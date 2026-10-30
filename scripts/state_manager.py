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
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

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
    "TESTCASE_GENERATION": ["TESTCASE_REVIEW", "WAITING_FOR_APPROVED_TESTCASES", "BLOCKED"],
    "TESTCASE_REVIEW": ["WAITING_FOR_APPROVED_TESTCASES", "AUTOMATION_IMPLEMENTATION", "TESTCASE_GENERATION", "BLOCKED"],
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
        except Exception:
            key = str(item)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result

class WorkflowStateManager:
    def __init__(self, workspace_root: Optional[str] = None):
        self.workspace_root = Path(workspace_root or os.getcwd()).resolve()
        self.state_file = self.workspace_root / STATE_FILE_NAME

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
        with open(self.state_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, data: Dict[str, Any]) -> None:
        data["updated_at"] = self._now()
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def init_state(self, module_name: str, repo_info: Dict[str, Any], docs: Optional[List[str]] = None) -> Dict[str, Any]:
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

    def transition(self, target_state: str, note: str = "", metadata: Optional[Dict[str, Any]] = None, enforce_fsm: bool = True) -> Dict[str, Any]:
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
    if len(sys.argv) < 2:
        print("Usage: python state_manager.py [init|status|transition|validate] [args...]")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    mgr = WorkflowStateManager()

    if cmd == "init":
        mod_name = sys.argv[2] if len(sys.argv) > 2 else "UnknownModule"
        s = mgr.init_state(mod_name, {"cwd": str(Path.cwd())})
        print(f"[OK] Initialized workflow state for '{mod_name}'. Current state: {s['current_state']}")

    elif cmd == "status":
        if not mgr.exists():
            print(f"[ERROR] No {STATE_FILE_NAME} found in current directory.")
            sys.exit(1)
        s = mgr.load()
        if "--compact" in sys.argv or "-c" in sys.argv:
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
        if len(sys.argv) < 3:
            print("Usage: python state_manager.py get <field_path>")
            sys.exit(1)
        val = mgr.get_field(sys.argv[2])
        if val is None:
            print("null")
        elif isinstance(val, (dict, list)):
            print(json.dumps(val, ensure_ascii=False))
        else:
            print(val)

    elif cmd == "transition":
        if len(sys.argv) < 3:
            print(f"Usage: python state_manager.py transition <TARGET_STATE> [note]")
            sys.exit(1)
        tgt = sys.argv[2]
        note = sys.argv[3] if len(sys.argv) > 3 else ""
        s = mgr.transition(tgt, note=note)
        print(f"[OK] State transitioned to {s['current_state']}")

    elif cmd == "set-artifact":
        if len(sys.argv) < 4:
            print("Usage: python state_manager.py set-artifact <artifact_key> <file_path>")
            sys.exit(1)
        art_key = sys.argv[2]
        art_path = sys.argv[3]
        s = mgr.set_artifact(art_key, art_path)
        print(f"[OK] Artifact '{art_key}' set to: {art_path}")

    elif cmd == "validate":
        res = mgr.validate_integrity()
        if "--json" in sys.argv:
            print(json.dumps(res, indent=2))
        else:
            if res.get("valid"):
                print(f"[OK] State is valid & resumable at: {res.get('current_state')}")
            else:
                print(f"[FAIL] State invalid: {res.get('reason', 'Documents modified')}")
                for d in res.get("changed_documents", []):
                    print(f"  - Modified file: {d['path']}")
