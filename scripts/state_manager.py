import re
#!/usr/bin/env python3
"""
scripts/state_manager.py
State management utility for the QA Agent System.
Provides deterministic workflow state transitions, checkpoint persistence,
and resumability without storing secrets or credentials.
"""

import sys
import os
import json
import time
import hashlib
import shutil
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError) as exc:
        logger.debug("Unable to reconfigure stdout encoding: %s", exc)

VALID_STATES = [
    "INITIALIZED",
    "CONTEXT_DISCOVERY",
    "DISCOVERY_INCOMPLETE",
    "GAP_ANALYSIS",
    "WAITING_FOR_REQUIREMENT_CLARIFICATION",
    "RUNTIME_INVESTIGATION",
    "TESTCASE_GENERATION",
    "TESTCASE_REVIEW",
    "WAITING_FOR_APPROVED_TESTCASES",
    "AUTOMATION_IMPLEMENTATION",
    "AUTOMATION_EXECUTION",
    "COMPLETED",
    "BLOCKED"
]

HUMAN_CHECKPOINT_STATES = {
    "WAITING_FOR_REQUIREMENT_CLARIFICATION",
    "WAITING_FOR_APPROVED_TESTCASES"
}

ALLOWED_TRANSITIONS = {
    "INITIALIZED": ["CONTEXT_DISCOVERY", "DISCOVERY_INCOMPLETE", "GAP_ANALYSIS", "WAITING_FOR_REQUIREMENT_CLARIFICATION", "BLOCKED"],
    "CONTEXT_DISCOVERY": ["GAP_ANALYSIS", "DISCOVERY_INCOMPLETE", "BLOCKED"],
    "DISCOVERY_INCOMPLETE": ["CONTEXT_DISCOVERY", "BLOCKED"],
    "GAP_ANALYSIS": ["WAITING_FOR_REQUIREMENT_CLARIFICATION", "RUNTIME_INVESTIGATION", "TESTCASE_GENERATION", "BLOCKED"],
    "WAITING_FOR_REQUIREMENT_CLARIFICATION": ["CONTEXT_DISCOVERY", "GAP_ANALYSIS", "RUNTIME_INVESTIGATION", "TESTCASE_GENERATION", "TESTCASE_REVIEW", "BLOCKED"],
    "RUNTIME_INVESTIGATION": ["TESTCASE_GENERATION", "WAITING_FOR_REQUIREMENT_CLARIFICATION", "BLOCKED"],
    "TESTCASE_GENERATION": ["TESTCASE_REVIEW", "WAITING_FOR_APPROVED_TESTCASES", "GAP_ANALYSIS", "BLOCKED"],
    "TESTCASE_REVIEW": ["WAITING_FOR_APPROVED_TESTCASES", "TESTCASE_GENERATION", "BLOCKED"],
    "WAITING_FOR_APPROVED_TESTCASES": ["AUTOMATION_IMPLEMENTATION", "TESTCASE_REVIEW", "BLOCKED"],
    "AUTOMATION_IMPLEMENTATION": ["AUTOMATION_EXECUTION", "COMPLETED", "BLOCKED"],
    "AUTOMATION_EXECUTION": ["COMPLETED", "AUTOMATION_IMPLEMENTATION", "GAP_ANALYSIS", "TESTCASE_GENERATION", "BLOCKED"],
    "COMPLETED": ["INITIALIZED", "CONTEXT_DISCOVERY", "AUTOMATION_EXECUTION"],
    "BLOCKED": VALID_STATES
}

FORBIDDEN_SECRET_KEYS = {
    "password", "passwd", "secret", "token", "credentials", "auth_key", 
    "api_key", "access_key", "private_key", "jwt", "bearer", "passphrase",
    "otp", "totp", "pin", "authorization", "session_id", "conn_str"
}

URI_CREDENTIAL_PATTERN = re.compile(r'([a-zA-Z0-9+.-]+://[^:\s@]+:)([^@\s]+)(@)')

def redact_credentials_in_string(val: str) -> str:
    """
    Scans a string value for URI credentials (e.g. postgres://user:password@host)
    and redacts the password portion to prevent secret leakage into state.
    """
    if "://" in val and "@" in val:
        return URI_CREDENTIAL_PATTERN.sub(r'\1***REDACTED***\3', val)
    return val

def sanitize_metadata(data: Any) -> Any:
    """
    Recursively inspects metadata dictionaries, lists, and strings.
    - Normalizes hyphens to underscores to catch keys like 'x-api-key', 'auth-token'.
    - Raises ValueError if sensitive credential keys are found.
    - Redacts embedded credentials inside URI string values.
    """
    if isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            k_norm = str(k).lower().replace("-", "_")
            if any(forbidden in k_norm for forbidden in FORBIDDEN_SECRET_KEYS):
                raise ValueError(f"Security Alert: Attempted to persist sensitive credential key '{k}' into state.")
            sanitized[k] = sanitize_metadata(v)
        return sanitized
    elif isinstance(data, list):
        return [sanitize_metadata(x) for x in data]
    elif isinstance(data, str):
        return redact_credentials_in_string(data)
    return data

STATE_FILE_NAME = ".qa-state.json"

class ConcurrentStateUpdateError(RuntimeError):
    """Raised when a caller tries to overwrite a newer state revision."""


class StateFileLock:
    """Small cross-platform inter-process lock based on exclusive lock-file creation."""

    def __init__(self, lock_path: Path, timeout: float = 10.0, poll_interval: float = 0.05):
        self.lock_path = Path(lock_path)
        self.timeout = timeout
        self.poll_interval = poll_interval
        self._fd = None

    def __enter__(self):
        deadline = time.monotonic() + self.timeout
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        while True:
            try:
                self._fd = os.open(str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(self._fd, f"{os.getpid()}\n".encode("ascii"))
                return self
            except FileExistsError:
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"Timed out waiting for state lock: {self.lock_path}")
                time.sleep(self.poll_interval)

    def __exit__(self, exc_type, exc_value, traceback):
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
        try:
            self.lock_path.unlink()
        except FileNotFoundError:
            pass

def _resolve_state_file(workspace_root: Path, module_name: Optional[str] = None) -> Path:
    if module_name:
        slug = re.sub(r'[^a-zA-Z0-9_-]', '_', module_name.strip().lower())
        return workspace_root / f".qa-state-{slug}.json"
    
    # Smart auto-detection: if default .qa-state.json does not exist,
    # but there is exactly 1 .qa-state-*.json file, auto-select it.
    default_file = workspace_root / STATE_FILE_NAME
    if not default_file.exists():
        custom_files = [p for p in workspace_root.glob(".qa-state-*.json") if not p.name.endswith(".bak") and not p.name.endswith(".tmp")]
        if len(custom_files) == 1:
            return custom_files[0]
            
    return default_file

def _dedup_list(items: List[Any]) -> List[Any]:
    """
    Deduplicates a list while preserving original input order.
    Uses canonical JSON serialization with sort_keys=True as comparison key,
    safely handling primitives, lists, and unhashable dictionaries.
    """
    seen = set()
    result = []
    for item in items:
        try:
            key = json.dumps(item, sort_keys=True, ensure_ascii=False)
        except (TypeError, ValueError):
            key = str(item)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result

class WorkflowStateManager:
    def __init__(self, workspace_root: Optional[str] = None, module_name: Optional[str] = None):
        self.workspace_root = Path(workspace_root or os.getcwd()).resolve()
        self.module_name = module_name
        self.state_file = _resolve_state_file(self.workspace_root, module_name)

    @property
    def lock_file(self) -> Path:
        return self.state_file.with_name(f"{self.state_file.name}.lock")

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _compute_hash(self, file_path: Path) -> Optional[str]:
        if not file_path.exists() or not file_path.is_file():
            return None
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def exists(self) -> bool:
        return self.state_file.exists()

    def load(self) -> Dict[str, Any]:
        if not self.exists():
            return {}
        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except (json.JSONDecodeError, UnicodeDecodeError, OSError) as ex:
            # Self-healing: attempt to restore from atomic backup snapshot if present
            bak_file = self.state_file.with_name(f"{self.state_file.name}.bak")
            if bak_file.exists():
                try:
                    with open(bak_file, "r", encoding="utf-8") as bf:
                        return json.load(bf)
                except (OSError, json.JSONDecodeError) as backup_exc:
                    logger.error("State and backup are both unreadable (%s): %s", bak_file, backup_exc)
            return {"current_state": "BLOCKED", "error": f"Corrupted state file: {str(ex)}"}

    def save(self, data: Dict[str, Any]) -> None:
        with StateFileLock(self.lock_file):
            disk_version = 0
            if self.state_file.exists():
                try:
                    with open(self.state_file, "r", encoding="utf-8") as current_file:
                        disk_version = int(json.load(current_file).get("_version", 0))
                except (OSError, ValueError, TypeError, json.JSONDecodeError):
                    disk_version = 0
            expected_version = int(data.get("_version", 0))
            if self.state_file.exists() and expected_version != disk_version:
                raise ConcurrentStateUpdateError(
                    f"State changed on disk (expected version {expected_version}, found {disk_version}); reload and retry."
                )
            data["_version"] = disk_version + 1
            data["updated_at"] = self._now()
            # Atomic file write with backup snapshot to prevent 0-byte state corruption
            tmp_file = self.state_file.with_name(f"{self.state_file.name}.{os.getpid()}.tmp")
            bak_file = self.state_file.with_name(f"{self.state_file.name}.bak")
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            if self.state_file.exists():
                try:
                    shutil.copy2(self.state_file, bak_file)
                except OSError as exc:
                    logger.warning("Unable to create state backup %s: %s", bak_file, exc)
            for attempt in range(5):
                try:
                    os.replace(tmp_file, self.state_file)
                    break
                except PermissionError:
                    if attempt == 4:
                        raise
                    time.sleep(0.02)

    def init_state(self, module_name: str, repo_info: Dict[str, Any], docs: Optional[List[str]] = None) -> Dict[str, Any]:
        if module_name:
            self.module_name = module_name
            self.state_file = _resolve_state_file(self.workspace_root, module_name)
        doc_hashes = {}
        if docs:
            for d in docs:
                p = Path(d)
                if not p.is_absolute():
                    p = self.workspace_root / p
                h = self._compute_hash(p)
                if h:
                    doc_hashes[str(p)] = h

        state = {
            "version": "1.0.0",
            "module_name": module_name,
            "current_state": "INITIALIZED",
            "repo_info": sanitize_metadata(repo_info),
            "created_at": self._now(),
            "updated_at": self._now(),
            "completed_steps": [],
            "pending_approval": None,
            "artifacts": {
                "module_context": None,
                "gap_analysis": None,
                "investigation_report": None,
                "excel_testcases": None,
                "approved_excel": None,
                "automation_summary": None
            },
            "document_hashes": doc_hashes,
            "testcase_ids": [],
            "clarification_issues": [],
            "history": [
                {
                    "state": "INITIALIZED",
                    "timestamp": self._now(),
                    "note": f"Workflow initialized for module '{module_name}'"
                }
            ]
        }
        self.save(state)
        return state

    def transition(self, target_state: str, note: str = "", metadata: Optional[Dict[str, Any]] = None, enforce_fsm: bool = True, approval_token: Optional[str] = None) -> Dict[str, Any]:
        if target_state not in VALID_STATES:
            raise ValueError(f"Invalid state '{target_state}'. Must be one of {VALID_STATES}")
        
        state = self.load()
        if not state:
            raise RuntimeError(f"Cannot transition: {STATE_FILE_NAME} does not exist. Run init first.")

        prev_state = state.get("current_state")

        if enforce_fsm and prev_state and prev_state != target_state:
            allowed = ALLOWED_TRANSITIONS.get(prev_state, [])
            if target_state not in allowed:
                raise ValueError(f"FSM Transition Violation: Cannot transition from '{prev_state}' to '{target_state}'. Allowed states: {allowed}")

        if prev_state == "WAITING_FOR_APPROVED_TESTCASES" and target_state == "AUTOMATION_IMPLEMENTATION":
            artifacts = state.get("artifacts", {})
            workbook_value = artifacts.get("approved_excel") or artifacts.get("excel_testcases")
            workbook_path = Path(workbook_value) if workbook_value else None
            if workbook_path and not workbook_path.is_absolute():
                workbook_path = self.workspace_root / workbook_path
            if not workbook_path or workbook_path.suffix.lower() != ".xlsx" or not workbook_path.is_file():
                raise ValueError("Human Gate 2 requires an existing approved .xlsx testcase workbook.")
            if not isinstance(approval_token, str) or not approval_token.strip():
                raise ValueError("Human Gate 2 requires a non-empty approval_token supplied by the approving user.")

        # Guard against infinite clarification loops
        if prev_state == "WAITING_FOR_REQUIREMENT_CLARIFICATION" and target_state in ["CONTEXT_DISCOVERY", "GAP_ANALYSIS"]:
            cycles = state.get("clarification_cycles", 0) + 1
            if cycles > 2:
                raise ValueError(
                    f"FSM Safety Guard: Exceeded maximum allowed clarification loops ({cycles}/2). "
                    "Manual review or human gate approval is required before re-triggering discovery."
                )
            state["clarification_cycles"] = cycles

        state["current_state"] = target_state
        if prev_state and prev_state not in state.get("completed_steps", []):
            state.setdefault("completed_steps", []).append(prev_state)

        if target_state in HUMAN_CHECKPOINT_STATES:
            state["pending_approval"] = {
                "checkpoint": target_state,
                "flagged_at": self._now(),
                "status": "AWAITING_USER_ACTION"
            }
        else:
            state["pending_approval"] = None

        if metadata:
            metadata = sanitize_metadata(metadata)
            for k, v in metadata.items():
                if k == "artifacts" and isinstance(v, dict):
                    state.setdefault("artifacts", {}).update(v)
                elif k in state and isinstance(state[k], list) and isinstance(v, list):
                    state[k] = _dedup_list(state[k] + v)
                else:
                    state[k] = v

        history = state.setdefault("history", [])
        history.append({
            "from_state": prev_state,
            "to_state": target_state,
            "timestamp": self._now(),
            "note": note
        })
        # Keep history capped to last 10 entries to prevent token bloat
        if len(history) > 12:
            state["history"] = history[-10:]

        self.save(state)
        return state

    def get_field(self, field_path: str) -> Any:
        state = self.load()
        if not state:
            return None
        parts = field_path.strip().split(".")
        curr = state
        for p in parts:
            if isinstance(curr, dict) and p in curr:
                curr = curr[p]
            else:
                return None
        return curr

    def set_artifact(self, artifact_key: str, file_path: str) -> Dict[str, Any]:
        state = self.load()
        if not state:
            raise RuntimeError(f"Cannot set artifact: {STATE_FILE_NAME} does not exist.")
        if "artifacts" not in state:
            state["artifacts"] = {}
        sanitized = sanitize_metadata({artifact_key: str(file_path)})
        state["artifacts"].update(sanitized)
        self.save(state)
        return state

    def set_field(self, field_path: str, value: Any) -> Dict[str, Any]:
        state = self.load()
        if not state:
            raise RuntimeError(f"Cannot set field: {STATE_FILE_NAME} does not exist.")
        
        value = sanitize_metadata(value) if isinstance(value, (dict, list, str)) else value
        parts = field_path.strip().split(".")
        curr = state
        for p in parts[:-1]:
            if p not in curr or not isinstance(curr[p], dict):
                curr[p] = {}
            curr = curr[p]
        curr[parts[-1]] = value
        state["updated_at"] = self._now()
        self.save(state)
        return state

    def validate_integrity(self) -> Dict[str, Any]:
        state = self.load()
        if not state:
            return {"valid": False, "reason": "No state file found"}

        changed_docs = []
        for doc_path, old_hash in state.get("document_hashes", {}).items():
            current_hash = self._compute_hash(Path(doc_path))
            if current_hash != old_hash:
                changed_docs.append({
                    "path": doc_path,
                    "old_hash": old_hash,
                    "current_hash": current_hash
                })

        return {
            "valid": len(changed_docs) == 0,
            "current_state": state.get("current_state"),
            "changed_documents": changed_docs,
            "resumable": True
        }

if __name__ == "__main__":
    raw_args = sys.argv[1:]
    module_arg = None
    clean_args = []
    idx = 0
    while idx < len(raw_args):
        if raw_args[idx] in ("--module", "-m") and idx + 1 < len(raw_args):
            module_arg = raw_args[idx + 1]
            idx += 2
        else:
            clean_args.append(raw_args[idx])
            idx += 1

    if not clean_args:
        print("Usage: python state_manager.py [init|status|transition|validate] [args...] [--module <mod>]")
        sys.exit(1)

    cmd = clean_args[0].lower()
    mgr = WorkflowStateManager(module_name=module_arg)

    if cmd == "init":
        mod_name = clean_args[1] if len(clean_args) > 1 else (module_arg or "UnknownModule")
        s = mgr.init_state(mod_name, {"cwd": str(Path.cwd())})
        print(f"[OK] Initialized workflow state for '{mod_name}'. Current state: {s['current_state']}")

    elif cmd == "status":
        if not mgr.exists():
            print(f"[ERROR] No {mgr.state_file.name} found in current directory.")
            sys.exit(1)
        s = mgr.load()
        if "--compact" in clean_args or "-c" in clean_args:
            pa = s.get('pending_approval')
            pa_str = pa.get('checkpoint') if isinstance(pa, dict) else "None"
            print(f"Module: {s.get('module_name')} | State: {s.get('current_state')} | Pending: {pa_str}")
        else:
            pa = s.get('pending_approval')
            pa_desc = f"{pa.get('checkpoint')} ({pa.get('status')})" if isinstance(pa, dict) else "None"
            arts = [f"{k}={v}" for k, v in s.get("artifacts", {}).items() if v]
            print(f"Module: {s.get('module_name')}")
            print(f"Current State: {s.get('current_state')}")
            print(f"Pending Approval: {pa_desc}")
            print(f"Completed Steps: {', '.join(s.get('completed_steps', [])) or 'None'}")
            print(f"Artifacts: {', '.join(arts) if arts else 'None'}")

    elif cmd == "get":
        if len(clean_args) < 2:
            print("Usage: python state_manager.py get <field_path> [--module <mod>]")
            sys.exit(1)
        val = mgr.get_field(clean_args[1])
        if val is None:
            print("null")
        elif isinstance(val, (dict, list)):
            print(json.dumps(val, ensure_ascii=False))
        else:
            print(val)

    elif cmd == "transition":
        if len(clean_args) < 2:
            print(f"Usage: python state_manager.py transition <TARGET_STATE> [note] [--metadata '<json>'] [--approval-token <token>] [--module <mod>]")
            sys.exit(1)
        tgt = clean_args[1]
        note_parts = []
        meta = None
        approval_token = None
        args = clean_args[2:]
        i = 0
        while i < len(args):
            if args[i] == "--metadata" and i + 1 < len(args):
                try:
                    meta = json.loads(args[i+1])
                except json.JSONDecodeError as ex:
                    print(f"[ERROR] Failed to parse --metadata JSON: {ex}")
                    sys.exit(1)
                i += 2
            elif args[i] == "--approval-token" and i + 1 < len(args):
                approval_token = args[i+1]
                i += 2
            else:
                note_parts.append(args[i])
                i += 1
        note = " ".join(note_parts)
        s = mgr.transition(tgt, note=note, metadata=meta, approval_token=approval_token)
        print(f"[OK] State transitioned to {s['current_state']}")

    elif cmd == "set-field":
        if len(clean_args) < 3:
            print("Usage: python state_manager.py set-field <field_path> <value> [--module <mod>]")
            sys.exit(1)
        field_path = clean_args[1]
        raw_val = clean_args[2]
        try:
            val = json.loads(raw_val)
        except json.JSONDecodeError:
            val = raw_val
        s = mgr.set_field(field_path, val)
        print(f"[OK] Field '{field_path}' updated successfully.")

    elif cmd == "set-artifact":
        if len(clean_args) < 3:
            print("Usage: python state_manager.py set-artifact <artifact_key> <file_path> [--module <mod>]")
            sys.exit(1)
        art_key = clean_args[1]
        art_path = clean_args[2]
        s = mgr.set_artifact(art_key, art_path)
        print(f"[OK] Artifact '{art_key}' set to: {art_path}")

    elif cmd == "validate":
        res = mgr.validate_integrity()
        if "--json" in clean_args:
            print(json.dumps(res, indent=2))
        else:
            if res.get("valid"):
                print(f"[OK] State is valid & resumable at: {res.get('current_state')}")
            else:
                print(f"[FAIL] State invalid: {res.get('reason', 'Documents modified')}")
                for d in res.get("changed_documents", []):
                    print(f"  - Modified file: {d['path']}")
