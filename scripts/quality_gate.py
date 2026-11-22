#!/usr/bin/env python3
"""
scripts/quality_gate.py
Unified AI Coding Quality Gate for Codex, Claude Code, and Antigravity Agents.

Provides static and runtime quality enforcement across:
- Group A: Playwright Testing Standards (PW-001 to PW-005)
- Group B: Security & Credential Protection (SEC-001, SEC-002)
- Group C: Python Engineering Quality (PY-001 to PY-003)
- Group D: Architectural Boundaries (ARCH-001, ARCH-002)
- Group E: QA Workflow Contracts (QA-001 to QA-005)

Usage:
  python scripts/quality_gate.py [files/dirs...]
  python scripts/quality_gate.py --staged
  python scripts/quality_gate.py --git-diff
  python scripts/quality_gate.py --check-state [.qa-state.json]
  python scripts/quality_gate.py --json
"""

import sys
import os
import json
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Ensure scripts directory is in sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lint_test_code import lint_file, LintViolation


def validate_qa_workflow_state(state_path: Path) -> List[LintViolation]:
    """
    Validates runtime QA workflow state JSON against Group E rules:
    - QA-001: No False PASS (BLOCK)
    - QA-002: Evidence-First Finding (BLOCK)
    - QA-003: GUARD Verification (BLOCK)
    - QA-004: Approval Gate Protection (BLOCK)
    - QA-005: Production Safety (BLOCK)
    """
    violations: List[LintViolation] = []
    if not state_path.exists():
        return [LintViolation(
            0,
            "STATE_FILE_NOT_FOUND",
            f"State file {state_path} does not exist.",
            severity="BLOCK",
            rule_id="QA-000",
            remediation="Initialize state file with WorkflowStateManager before audit."
        )]

    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [LintViolation(
            0,
            "STATE_JSON_CORRUPTION",
            f"Cannot parse state file JSON: {exc}",
            severity="BLOCK",
            rule_id="QA-000",
            remediation="Restore state from backup (.bak) or repair JSON syntax."
        )]

    current_state = data.get("current_state", "")
    history = data.get("history", [])
    artifacts = data.get("artifacts", {})
    completed_steps = data.get("completed_steps", [])

    # Rule QA-001: No False PASS
    if current_state == "COMPLETED":
        # 1. Any failed test run invalidates COMPLETED
        test_runs = data.get("test_runs", [])
        for run in test_runs:
            if run.get("status") == "FAILED" or run.get("exit_code", 0) != 0:
                violations.append(LintViolation(
                    1,
                    "NO_FALSE_PASS_VIOLATION",
                    f"State marked COMPLETED but test run '{run.get('test_id', 'unknown')}' failed with exit code {run.get('exit_code')}.",
                    severity="BLOCK",
                    rule_id="QA-001",
                    remediation="Resolve test failure or record state as BLOCKED/FAILED."
                ))
        # 2. Must possess valid execution evidence artifact
        has_evidence = any(
            k in artifacts and artifacts[k]
            for k in ["approved_excel", "test_summary", "quick_audit_report", "excel_testcases", "test_execution_report"]
        )
        if not has_evidence and not test_runs and "INITIALIZED" in completed_steps:
            violations.append(LintViolation(
                1,
                "NO_FALSE_PASS_VIOLATION",
                "State marked COMPLETED without valid test execution or audit evidence attached in artifacts.",
                severity="BLOCK",
                rule_id="QA-001",
                remediation="Execute verification and record artifact path in state before marking COMPLETED."
            ))

    # Rule QA-002: Evidence-First Finding
    gaps = data.get("gaps", [])
    for gap in gaps:
        if isinstance(gap, dict) and gap.get("status") in ["CONFIRMED", "CONFIRMED_BUG"]:
            repro = gap.get("repro_script") or gap.get("repro_cmd") or gap.get("evidence")
            if not repro:
                violations.append(LintViolation(
                    1,
                    "UNVERIFIED_BUG_VIOLATION",
                    f"Gap '{gap.get('id', 'unknown')}' marked CONFIRMED without reproduction script or execution proof.",
                    severity="BLOCK",
                    rule_id="QA-002",
                    remediation="Add verified repro_script in tests/repro/ or documented execution proof."
                ))

    # Rule QA-003: GUARD Verification
    guards = data.get("guards", [])
    for guard in guards:
        if isinstance(guard, dict):
            spec_path = guard.get("spec_path") or guard.get("guard_file")
            if not spec_path:
                violations.append(LintViolation(
                    1,
                    "UNVERIFIED_GUARD_VIOLATION",
                    f"Guard '{guard.get('id', 'unknown')}' registered without spec_path in tests/guards/.",
                    severity="BLOCK",
                    rule_id="QA-003",
                    remediation="Provide verified guard script path in tests/guards/."
                ))

    # Rule QA-004: Approval Gate Protection
    if current_state in ["AUTOMATION_IMPLEMENTATION", "AUTOMATION_EXECUTION"] or ("AUTOMATION_IMPLEMENTATION" in completed_steps):
        has_approval = False
        if data.get("approval_token"):
            has_approval = True
        else:
            for entry in history:
                if entry.get("to_state") == "AUTOMATION_IMPLEMENTATION":
                    if "approval" in entry.get("note", "").lower() or entry.get("approval_token"):
                        has_approval = True
                        break
        if not has_approval:
            violations.append(LintViolation(
                1,
                "APPROVAL_GATE_VIOLATION",
                "Automation implementation executed without required human approval token.",
                severity="BLOCK",
                rule_id="QA-004",
                remediation="Obtain explicit user approval at Step 5 Human Gate before automation."
            ))

    # Rule QA-005: Production Safety
    env = data.get("environment", {})
    if env.get("tier") == "production" and data.get("mutation_executed"):
        violations.append(LintViolation(
            1,
            "PRODUCTION_SAFETY_VIOLATION",
            f"Unauthorized automated mutation executed against production environment ({env.get('base_url')}).",
            severity="BLOCK",
            rule_id="QA-005",
            remediation="Strictly block automated mutations on production URLs."
        ))

    return violations


def get_git_files(mode: str) -> List[Path]:
    """Retrieves changed files via git command."""
    cmd = ["git", "diff", "--name-only"]
    if mode == "staged":
        cmd.append("--cached")
    elif mode == "diff":
        cmd.append("HEAD")

    try:
        res = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, check=True)
        paths = []
        for line in res.stdout.splitlines():
            line = line.strip()
            if line:
                p = PROJECT_ROOT / line
                if p.is_file():
                    paths.append(p)
        return paths
    except Exception as exc:
        print(f"[WARN] Git diff retrieval failed: {exc}")
        return []


def run_quality_gate(
    target_paths: Optional[List[Path]] = None,
    check_state: bool = False,
    strict: bool = False
) -> Tuple[int, Dict[str, Any]]:
    """
    Executes Quality Gate over target files.
    Returns:
    - (exit_code, report_dict)
    - exit_code 0: PASS (0 BLOCK violations)
    - exit_code 1: FAIL (1+ BLOCK violations, or warnings in strict mode)
    - exit_code 2: ERROR (System / IO / Dependency failure)
    """
    report: Dict[str, Any] = {
        "status": "PASS",
        "total_files": 0,
        "block_count": 0,
        "warning_count": 0,
        "files_with_violations": 0,
        "results": {}
    }

    files_to_check: List[Path] = []
    if target_paths:
        for p in target_paths:
            if p.is_file():
                files_to_check.append(p)
            elif p.is_dir():
                for sub in p.rglob("*"):
                    if sub.is_file() and sub.suffix in [".js", ".mjs", ".ts", ".tsx", ".py", ".json"]:
                        if not any(part in ["node_modules", "__pycache__", ".git", ".venv"] for part in sub.parts):
                            files_to_check.append(sub)
            else:
                report["status"] = "ERROR"
                report["error"] = f"Target path does not exist: {p}"
                return (2, report)
    else:
        # Default: check project scripts, skills, and tests
        for sub_dir in ["scripts", "tests", "skills"]:
            d = PROJECT_ROOT / sub_dir
            if d.exists():
                for sub in d.rglob("*"):
                    if sub.is_file() and sub.suffix in [".js", ".mjs", ".ts", ".tsx", ".py"]:
                        if not any(part in ["node_modules", "__pycache__", ".git", ".venv"] for part in sub.parts):
                            files_to_check.append(sub)

    if check_state:
        for st_file in PROJECT_ROOT.glob(".qa-state*.json"):
            if st_file.is_file():
                files_to_check.append(st_file)

    files_to_check = sorted(list(set(files_to_check)))
    report["total_files"] = len(files_to_check)

    total_blocks = 0
    total_warnings = 0

    for file_path in files_to_check:
        try:
            if file_path.suffix == ".json" and ".qa-state" in file_path.name:
                violations = validate_qa_workflow_state(file_path)
            elif file_path.suffix in [".js", ".mjs", ".ts", ".tsx", ".py"]:
                violations = lint_file(file_path)
            else:
                continue
        except Exception as exc:
            report["status"] = "ERROR"
            report["error"] = f"Linter crashed while processing {file_path}: {exc}"
            return (2, report)

        if violations:
            file_key = str(file_path.relative_to(PROJECT_ROOT) if file_path.is_relative_to(PROJECT_ROOT) else file_path)
            report["results"][file_key] = [v.to_dict() for v in violations]
            blocks = [v for v in violations if getattr(v, "severity", "BLOCK") == "BLOCK"]
            warns = [v for v in violations if getattr(v, "severity", "BLOCK") == "WARNING"]
            total_blocks += len(blocks)
            total_warnings += len(warns)

    report["block_count"] = total_blocks
    report["warning_count"] = total_warnings
    report["files_with_violations"] = len(report["results"])

    if total_blocks > 0 or (strict and total_warnings > 0):
        report["status"] = "FAIL"
        exit_code = 1
    else:
        report["status"] = "PASS"
        exit_code = 0

    return (exit_code, report)


def format_report_console(report: Dict[str, Any], strict: bool = False) -> None:
    """Prints a beautiful console summary of Quality Gate results."""
    print("=" * 64)
    print("AI CODING QUALITY GATE — AUDIT REPORT")
    print("=" * 64)
    print(f"Total files audited     : {report['total_files']}")
    print(f"BLOCK violations        : {report['block_count']}")
    print(f"WARNING advisories      : {report['warning_count']}")
    print(f"Files with violations   : {report['files_with_violations']}")
    print("-" * 64)

    for file_key, violations in report.get("results", {}).items():
        has_block = any(v.get("severity") == "BLOCK" for v in violations)
        status_tag = "[BLOCK]" if has_block else "[WARN]"
        print(f"\n{status_tag} {file_key}:")
        for v in violations:
            sev = v.get("severity", "BLOCK")
            rule_id = v.get("rule_id", "GENERAL")
            rule_name = v.get("rule_name", "VIOLATION")
            print(f"  Line {v.get('line', 0)} [{sev}] [{rule_id}: {rule_name}]: {v.get('message')}")
            if v.get("remediation"):
                print(f"    --> Fix: {v.get('remediation')}")

    print("\n" + "=" * 64)
    if report["status"] == "PASS":
        if report["warning_count"] > 0:
            print(f"[PASS WITH ADVISORIES] Quality Gate APPROVED with {report['warning_count']} non-blocking warning(s).")
        else:
            print("[SUCCESS] Quality Gate APPROVED: 0 BLOCK violations. Code meets Senior QA standards.")
    else:
        print(f"[FAIL] Quality Gate BLOCKED: {report['block_count']} BLOCK violation(s) must be resolved before handover.")
    print("=" * 64)


def main() -> int:
    parser = argparse.ArgumentParser(description="AI Coding Quality Gate for QA Agent System")
    parser.add_argument("targets", nargs="*", help="File or directory paths to audit")
    parser.add_argument("--staged", action="store_true", help="Audit git staged files")
    parser.add_argument("--git-diff", action="store_true", help="Audit git changed files (HEAD)")
    parser.add_argument("--check-state", action="store_true", help="Audit .qa-state*.json state files against Group E contracts")
    parser.add_argument("--strict", action="store_true", help="Treat WARNINGs as failures (exit 1)")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON format for AI agents")
    args = parser.parse_args()

    targets: List[Path] = []
    if args.staged:
        targets.extend(get_git_files("staged"))
    elif args.git_diff:
        targets.extend(get_git_files("diff"))
    elif args.targets:
        targets.extend([Path(t).resolve() for t in args.targets])

    exit_code, report = run_quality_gate(
        target_paths=targets if targets else None,
        check_state=args.check_state,
        strict=args.strict
    )

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        format_report_console(report, strict=args.strict)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
