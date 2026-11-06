#!/usr/bin/env python3
"""
scripts/lint_test_code.py
Automated static linter enforcing Ponytail Senior Dev standards for generated test scripts.
Checks:
1. Zero arbitrary sleeps (prohibits waitForTimeout, sleep).
2. Zero hardcoded secrets (flags hardcoded passwords, tokens, API keys).
3. Explicit ID traceability (ensures test cases have approved TC IDs).
4. Web-first assertion presence.
"""

import sys
import re
import os
from pathlib import Path
from typing import List, Tuple

# Patterns that violate Ponytail Senior Dev standards
SLEEP_PATTERN = re.compile(r'\b(?:page\s*\.\s*waitForTimeout\s*\(|time\s*\.\s*sleep\s*\(|sleep\s*\(\s*\d+)', re.IGNORECASE)
SECRET_PATTERN = re.compile(r'\b(?:password|passwd|api_key|secret|token)\s*[:=]\s*[\'"][^\'"]{4,}[\'"]', re.IGNORECASE)
ENV_VAR_PATTERN = re.compile(r'\b(?:process\s*\.\s*env\s*|os\s*\.\s*environ\b|env\s*\[)')
TEST_ID_PATTERN = re.compile(r'\btest\s*\(\s*[\'"`](TC-[A-Z0-9_-]+)')
ASSERTION_PATTERN = re.compile(r'\b(?:expect\s*\(|assert\s+)')

def lint_file(file_path: Path) -> List[Tuple[int, str, str]]:
    """
    Lints a single test script file.
    Returns a list of (line_number, rule_name, error_message).
    """
    violations = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as exc:
        return [(0, "FILE_READ_ERROR", f"Cannot read file: {exc}")]

    lines = content.splitlines()
    has_test_block = False
    has_test_id = False
    has_assertion = bool(ASSERTION_PATTERN.search(content))

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        # Skip comment lines
        if stripped.startswith("//") or stripped.startswith("#") or stripped.startswith("/*") or stripped.startswith("*"):
            continue

        # Rule 1: Zero Arbitrary Sleeps
        if SLEEP_PATTERN.search(line):
            violations.append((
                idx,
                "ZERO_SLEEP_VIOLATION",
                f"Prohibited arbitrary sleep detected: '{stripped}'. Use web-first assertions or waitForUIStable instead."
            ))

        # Rule 2: Zero Hardcoded Secrets
        secret_match = SECRET_PATTERN.search(line)
        if secret_match and not ENV_VAR_PATTERN.search(line):
            # Avoid flagging test fixture dummy data like 'testuser' or variable names
            val = secret_match.group(0)
            if not any(safe in val.lower() for safe in ["process.env", "dummy", "placeholder", "xxx"]):
                violations.append((
                    idx,
                    "HARDCODED_SECRET_VIOLATION",
                    f"Possible hardcoded secret: '{val}'. Read credentials from environment variables (process.env.TEST_PASSWORD)."
                ))

        # Check for test blocks and test IDs
        if re.search(r'\btest\s*\(', line):
            has_test_block = True
            if TEST_ID_PATTERN.search(line):
                has_test_id = True

    # Rule 3: Explicit ID Traceability
    if has_test_block and not has_test_id:
        violations.append((
            1,
            "TRACEABILITY_VIOLATION",
            "Test cases must explicitly reference approved Excel Test Case IDs in titles (e.g., test('TC-AUTH-001: ...'))."
        ))

    # Rule 4: Assertion Presence
    if has_test_block and not has_assertion:
        violations.append((
            1,
            "MISSING_ASSERTION_VIOLATION",
            "Test script contains test blocks without assertions. Add web-first assertions (expect(locator).toBeVisible())."
        ))

    return violations

def lint_path(target_path: Path) -> int:
    """Lints a file or directory of test files. Returns exit code 0 if clean, 1 if violations found."""
    if target_path.is_file():
        files = [target_path]
    elif target_path.is_dir():
        files = [
            p for p in target_path.rglob("*")
            if p.suffix in [".js", ".mjs", ".ts", ".tsx", ".py"] and not any(part.startswith(".") or part in ["node_modules", "__pycache__"] for part in p.parts)
        ]
    else:
        print(f"[ERROR] Path does not exist: {target_path}")
        return 1

    total_violations = 0
    for f in sorted(files):
        violations = lint_file(f)
        if violations:
            total_violations += len(violations)
            print(f"\n[FAIL] {f}:")
            for line_no, rule, msg in violations:
                print(f"  Line {line_no} [{rule}]: {msg}")

    if total_violations == 0:
        print(f"[PASS] All {len(files)} file(s) meet Ponytail Senior Dev testing standards (0 sleeps, 0 hardcoded secrets, verified traceability).")
        return 0
    else:
        print(f"\n[TOTAL] Found {total_violations} violation(s) across {len(files)} file(s).")
        return 1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python lint_test_code.py <file_or_dir_to_lint>")
        sys.exit(1)

    target = Path(sys.argv[1])
    sys.exit(lint_path(target))
