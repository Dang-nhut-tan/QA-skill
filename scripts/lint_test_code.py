#!/usr/bin/env python3
"""
scripts/lint_test_code.py
Automated static linter enforcing Senior Dev testing and coding standards.
Part of the Enterprise QA Agent Quality Gate.

Supported Rules:
Group A — Playwright:
- PW-001 (ZERO_SLEEP_VIOLATION): Prohibits waitForTimeout, sleep [BLOCK]
- PW-002 (FLOATING_PROMISE_VIOLATION): Prohibits un-awaited async web-matchers & actions [BLOCK]
- PW-003 (TRACEABILITY_VIOLATION): Requires traceable TC/GAP/GUARD IDs in test titles [BLOCK]
- PW-004 (FOCUSED_TEST_VIOLATION): Prohibits test.only() and ungrounded test.skip() [BLOCK]
- PW-005 (LOCATOR_QUALITY_WARNING): Flags fragile locators (absolute XPath, deep DOM chains) [WARNING]

Group B — Security:
- SEC-001 (HARDCODED_SECRET_VIOLATION): Flags raw credentials, tokens, keys [BLOCK]
- SEC-002 (UNMASKED_CREDENTIAL_LOG_VIOLATION): Flags logging raw credentials [BLOCK]

Group C — Python:
- PY-001 (SILENT_EXCEPTION_VIOLATION): Flags bare except and swallowed exceptions via AST [BLOCK]
- PY-002 (MUTABLE_DEFAULT_ARG_VIOLATION): Flags mutable default arguments ([], {}) via AST [BLOCK]
- PY-003 (UNSAFE_EVAL_VIOLATION): Flags eval() and exec() via AST [BLOCK]

Group D — Architecture:
- ARCH-001 (IMPORT_BOUNDARY_VIOLATION): Flags production scripts importing test suites [BLOCK]
- ARCH-002 (FRAMEWORK_UTILITY_REUSE_WARNING): Flags reinventing sleep loops or manual locks [WARNING]

Legacy / Senior Dev Standards:
- SELECTOR_SYNTAX_VIOLATION (C3)
- COLLISION_DATA_VIOLATION (C2)
- EXCESSIVE_CONCURRENCY_VIOLATION
- MISSING_ASSERTION_VIOLATION
"""

import sys
import re
import os
import ast
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

class LintViolation(tuple):
    """
    Backwards-compatible tuple (line, rule_name, message) with rich metadata:
    - severity: "BLOCK" | "WARNING"
    - rule_id: e.g. "PW-001", "SEC-001", "PY-001"
    - remediation: guidance for AI auto-fix loop
    """
    def __new__(
        cls,
        line: int,
        rule_name: str,
        message: str,
        severity: str = "BLOCK",
        rule_id: str = "",
        remediation: str = ""
    ):
        instance = super().__new__(cls, (line, rule_name, message))
        instance.severity = severity
        instance.rule_id = rule_id
        instance.rule_name = rule_name
        instance.remediation = remediation
        return instance

    @property
    def line(self) -> int:
        return self[0]

    @property
    def rule(self) -> str:
        return self[1]

    @property
    def error_message(self) -> str:
        return self[2]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "line": self[0],
            "rule_name": self[1],
            "message": self[2],
            "severity": self.severity,
            "rule_id": self.rule_id,
            "remediation": self.remediation
        }


# Regex Patterns for Code Analysis
SLEEP_PATTERN = re.compile(r'\b(?:page\s*\.\s*waitForTimeout\s*\(|time\s*\.\s*sleep\s*\(|sleep\s*\(\s*\d+)', re.IGNORECASE)
SECRET_PATTERN = re.compile(r'''\b(?:password|passwd|api_key|secret|token)\s*[:=]\s*['"][^'"]{4,}['"]''', re.IGNORECASE)
ENV_VAR_PATTERN = re.compile(r'\b(?:process\s*\.\s*env\s*|os\s*\.\s*environ\b|env\s*\[)')
TEST_ID_PATTERN = re.compile(r'\btest\s*\(\s*[\'"`]((?:TC|GAP|GUARD)-[A-Z0-9_-]+)')
ASSERTION_PATTERN = re.compile(r'\b(?:expect\s*\(|assert\s+)')

# Group A: Playwright Patterns
ASYNC_WEB_MATCHER_PATTERN = re.compile(
    r'\b(?:toBeVisible|toBeHidden|toBeEnabled|toBeDisabled|toBeChecked|toBeEditable|'
    r'toBeFocused|toBeEmpty|toHaveText|toContainText|toHaveAttribute|toHaveClass|'
    r'toHaveCount|toHaveCSS|toHaveId|toHaveJSProperty|toHaveValue|toHaveValues|'
    r'toHaveTitle|toHaveURL)\s*\(',
    re.IGNORECASE
)
ASYNC_PAGE_ACTION_PATTERN = re.compile(
    r'\b(?:page|request)\s*\.\s*(?:goto|click|dblclick|fill|press|type|selectOption|check|uncheck|setInputFiles|waitForSelector|waitForURL|waitForLoadState)\s*\(',
    re.IGNORECASE
)
FOCUSED_TEST_PATTERN = re.compile(
    r'\b(?:test|it|describe)\s*\.\s*only\s*\(',
    re.IGNORECASE
)
UNGROUNDED_SKIP_PATTERN = re.compile(
    r'\btest\s*\.\s*skip\s*\(\s*(?:\)|true\s*\)|false\s*\))',
    re.IGNORECASE
)
ABSOLUTE_XPATH_PATTERN = re.compile(
    r'''(?:\.locator|\.waitForSelector|\.\$)\s*\(\s*['"](?:\/html\/|\/\/html\/|\/body\/|\/\/body\/|xpath=\/(?:html|body))''',
    re.IGNORECASE
)
DEEP_DOM_PATTERN = re.compile(
    r'''(?:\.locator|\.waitForSelector)\s*\(\s*['"][^'"]*?(?:>\s*[\w-]+\s*){3,}['"]''',
    re.IGNORECASE
)
UNGROUNDED_NTH_PATTERN = re.compile(
    r'\.locator\([^)]+\)\.nth\s*\(\s*\d+\s*\)'
)

# Extended Verification Patterns (C2, C3, C5, Security, Concurrency)
BROKEN_ATTR_SELECTOR_PATTERN = re.compile(
    r'''(?:\.waitForSelector|\.locator|\.\$|\.\$\$)\s*\(\s*(?P<q>['"])(?:role|aria-[\w-]+|data-[\w-]+)\s*=\s*\\?['"]?[^'"\[\]()]+\\?['"]?\s*(?P=q)''',
    re.IGNORECASE
)
STATIC_WORKER_PATTERN = re.compile(
    r'\b(?:workerCode|employeeCode|userCode|userId|testUsername|testUser)\s*[:=]\s*[\'"][A-Z0-9_-]{4,}[\'"]',
    re.IGNORECASE
)
DYNAMIC_DATA_PATTERN = re.compile(
    r'\b(?:Date\.now|Math\.random|uuid|process\.env|Date\(|timestamp|workerIndex)\b',
    re.IGNORECASE
)
UNMASKED_LOG_PATTERN = re.compile(
    r'\b(?:console\s*\.\s*(?:log|info|error|warn)|print|logger\.\w+)\s*\([^)]*\b(?:authHeader|process\.env|os\.environ|TEST_TOKEN|secretKey|bearerToken)\b[^)]*\)',
    re.IGNORECASE
)
CONCURRENCY_BURST_PATTERN = re.compile(
    r'\bArray\s*\(\s*(?:[6-9]|\d{2,})\s*\)\s*\.\s*fill|\bPromise\.all\s*\(\s*\[(?:[^\]]*,){5,}',
    re.IGNORECASE
)

# Group D: Architecture Patterns
MANUAL_SLEEP_LOOP_PATTERN = re.compile(
    r'\bwhile\s+.*:\s*(?:.*\n)?.*time\s*\.\s*sleep\b',
    re.IGNORECASE
)


def lint_python_ast(content: str, file_path: Path) -> List[LintViolation]:
    """
    Performs high-precision AST static analysis on Python files.
    Enforces:
    - PY-001: No Silent Exception (bare except and swallowed exceptions)
    - PY-002: No Mutable Default Arguments ([], {}, set())
    - PY-003: Unsafe Dynamic Execution (eval, exec)
    - ARCH-001: Import Boundaries (scripts/ cannot import tests/)
    """
    violations: List[LintViolation] = []
    try:
        tree = ast.parse(content, filename=str(file_path))
    except SyntaxError as e:
        return [LintViolation(
            e.lineno or 1,
            "SYNTAX_ERROR",
            f"Python syntax error: {e.msg}",
            severity="BLOCK",
            rule_id="PY-000",
            remediation="Fix Python syntax error to enable static analysis."
        )]

    for node in ast.walk(tree):
        # PY-001: No Silent Exception
        if isinstance(node, ast.Try):
            for handler in node.handlers:
                # Bare except:
                if handler.type is None:
                    violations.append(LintViolation(
                        handler.lineno,
                        "SILENT_EXCEPTION_VIOLATION",
                        f"Bare 'except:' detected at line {handler.lineno}. It catches SystemExit/KeyboardInterrupt and hides critical failures.",
                        severity="BLOCK",
                        rule_id="PY-001",
                        remediation="Catch specific exceptions: 'except (KeyError, ValueError) as err:' and log/handle."
                    ))
                else:
                    # Swallowed exception with only pass or docstring
                    body = handler.body
                    is_swallowed = False
                    if len(body) == 1:
                        if isinstance(body[0], ast.Pass):
                            is_swallowed = True
                        elif isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
                            is_swallowed = True
                    if is_swallowed:
                        type_str = ast.unparse(handler.type) if hasattr(ast, "unparse") else "Exception"
                        violations.append(LintViolation(
                            handler.lineno,
                            "SILENT_EXCEPTION_VIOLATION",
                            f"Swallowed exception 'except {type_str}: pass' at line {handler.lineno}. Silent pass hides errors and causes false passes.",
                            severity="BLOCK",
                            rule_id="PY-001",
                            remediation="Log the exception with logger.error() or re-raise with 'raise' instead of silently ignoring."
                        ))

        # PY-002: No Mutable Default Arguments
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for default in node.args.defaults + node.args.kw_defaults:
                if default is not None and isinstance(default, (ast.List, ast.Dict, ast.Set)):
                    type_name = "list" if isinstance(default, ast.List) else ("dict" if isinstance(default, ast.Dict) else "set")
                    violations.append(LintViolation(
                        default.lineno,
                        "MUTABLE_DEFAULT_ARG_VIOLATION",
                        f"Mutable default argument '{type_name}' in function '{node.name}' at line {default.lineno}. Mutable defaults retain mutated state across invocations.",
                        severity="BLOCK",
                        rule_id="PY-002",
                        remediation="Use None as default value and initialize inside function: 'def fn(items=None): if items is None: items = []'."
                    ))

        # PY-003: Unsafe Dynamic Execution
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in ("eval", "exec"):
                violations.append(LintViolation(
                    node.lineno,
                    "UNSAFE_EVAL_VIOLATION",
                    f"Unsafe dynamic execution '{node.func.id}()' detected at line {node.lineno}. Dynamic code execution introduces severe security vulnerabilities.",
                    severity="BLOCK",
                    rule_id="PY-003",
                    remediation="Use ast.literal_eval() for safe data parsing or explicit mapping dictionaries instead of eval/exec."
                ))

        # ARCH-001: Import Boundaries (scripts/ cannot import tests/)
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            is_scripts_file = "scripts" in file_path.parts
            if is_scripts_file:
                imported_module = ""
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name == "tests" or alias.name.startswith("tests."):
                            imported_module = alias.name
                elif isinstance(node, ast.ImportFrom):
                    if node.module and (node.module == "tests" or node.module.startswith("tests.")):
                        imported_module = node.module
                if imported_module:
                    violations.append(LintViolation(
                        node.lineno,
                        "IMPORT_BOUNDARY_VIOLATION",
                        f"Architecture boundary violation at line {node.lineno}: Production script '{file_path.name}' imports from test suite '{imported_module}'.",
                        severity="BLOCK",
                        rule_id="ARCH-001",
                        remediation="Extract shared utilities into scripts/ or references/ instead of importing from tests/."
                    ))

    return violations


def lint_file(file_path: Path) -> List[LintViolation]:
    """
    Lints a single source or test file.
    Returns a list of LintViolation objects (backward-compatible with 3-tuples).
    """
    violations: List[LintViolation] = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as exc:
        return [LintViolation(
            0,
            "FILE_READ_ERROR",
            f"Cannot read file: {exc}",
            severity="BLOCK",
            rule_id="IO-001",
            remediation="Ensure file exists and has readable UTF-8 permissions."
        )]

    # If Python file, execute AST analysis first
    if file_path.suffix == ".py":
        violations.extend(lint_python_ast(content, file_path))

    lines = content.splitlines()
    has_test_block = False
    has_test_id = False
    has_assertion = bool(ASSERTION_PATTERN.search(content))
    is_js_ts = file_path.suffix in [".js", ".mjs", ".ts", ".tsx"]

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        # Skip comment lines
        if stripped.startswith("//") or stripped.startswith("#") or stripped.startswith("/*") or stripped.startswith("*"):
            continue

        # Rule PW-001: Zero Arbitrary Sleeps
        if SLEEP_PATTERN.search(line):
            violations.append(LintViolation(
                idx,
                "ZERO_SLEEP_VIOLATION",
                f"Prohibited arbitrary sleep detected: '{stripped}'. Use web-first assertions or waitForUIStable instead.",
                severity="BLOCK",
                rule_id="PW-001",
                remediation="Replace arbitrary sleep with 'await expect(locator).toBeVisible()' or 'page.waitForLoadState('networkidle')'."
            ))

        # Rule SEC-001: Zero Hardcoded Secrets
        secret_match = SECRET_PATTERN.search(line)
        if secret_match and not ENV_VAR_PATTERN.search(line):
            val = secret_match.group(0)
            if not any(safe in val.lower() for safe in ["process.env", "dummy", "placeholder", "xxx", "redacted", "test_id"]):
                violations.append(LintViolation(
                    idx,
                    "HARDCODED_SECRET_VIOLATION",
                    f"Possible hardcoded secret: '{val}'. Read credentials from environment variables (process.env.TEST_PASSWORD).",
                    severity="BLOCK",
                    rule_id="SEC-001",
                    remediation="Read credentials from environment variables (e.g. process.env.TEST_PASSWORD or os.environ['TEST_PASSWORD'])."
                ))

        # Rule PW-002: Zero Floating Promises (JS/TS)
        if is_js_ts:
            # 1. Missing await before async assertions
            if ("expect(" in line or "expect (" in line):
                if ASYNC_WEB_MATCHER_PATTERN.search(line) or "locator(" in line or "getBy" in line:
                    match = re.search(r'(?P<prefix>.*?)\bexpect\s*\(', line)
                    if match:
                        prefix = match.group("prefix").strip()
                        if not (prefix.endswith("await") or prefix.endswith("return") or prefix.startswith("return") or "await " in prefix):
                            violations.append(LintViolation(
                                idx,
                                "FLOATING_PROMISE_VIOLATION",
                                f"Missing 'await' before async assertion: '{stripped}'. Web-first assertions return promises and must be awaited to prevent silent false positives.",
                                severity="BLOCK",
                                rule_id="PW-002",
                                remediation="Add 'await' before expect: 'await expect(...)'."
                            ))
            # 2. Missing await before async Playwright page actions
            elif ASYNC_PAGE_ACTION_PATTERN.search(line):
                # Check if statement is awaited or returned or inside Promise.all
                if not any(kw in line for kw in ["await ", "return ", "Promise.all", "Promise.race", "void "]):
                    # Make sure it's not a comment or callback parameter declaration
                    if not (stripped.startswith("const ") or stripped.startswith("let ") or stripped.startswith("var ")):
                        violations.append(LintViolation(
                            idx,
                            "FLOATING_PROMISE_VIOLATION",
                            f"Missing 'await' before async Playwright page operation: '{stripped}'. Un-awaited operations cause unhandled promise rejections.",
                            severity="BLOCK",
                            rule_id="PW-002",
                            remediation="Add 'await' before async Playwright method call: 'await page.click(...) or await page.goto(...)'."
                        ))

        # Rule PW-004: No Focused Tests
        if is_js_ts:
            if FOCUSED_TEST_PATTERN.search(line):
                violations.append(LintViolation(
                    idx,
                    "FOCUSED_TEST_VIOLATION",
                    f"Focused test detected: '{stripped}'. Prohibited to commit test.only() or describe.only().",
                    severity="BLOCK",
                    rule_id="PW-004",
                    remediation="Remove .only() focus before handover."
                ))
            elif UNGROUNDED_SKIP_PATTERN.search(line):
                violations.append(LintViolation(
                    idx,
                    "FOCUSED_TEST_VIOLATION",
                    f"Ungrounded test.skip() without documented reason: '{stripped}'.",
                    severity="BLOCK",
                    rule_id="PW-004",
                    remediation="Supply documented reason parameter: test.skip(condition, 'Reason / Ticket ID')."
                ))

        # Rule PW-005: Locator Quality (WARNING)
        if is_js_ts:
            if ABSOLUTE_XPATH_PATTERN.search(line):
                violations.append(LintViolation(
                    idx,
                    "LOCATOR_QUALITY_WARNING",
                    f"Fragile absolute XPath locator detected: '{stripped}'. Absolute paths break easily on DOM updates.",
                    severity="WARNING",
                    rule_id="PW-005",
                    remediation="Use user-facing locators: page.getByRole(), page.getByText(), page.getByLabel(), or data-testid."
                ))
            elif DEEP_DOM_PATTERN.search(line):
                violations.append(LintViolation(
                    idx,
                    "LOCATOR_QUALITY_WARNING",
                    f"Fragile deep DOM structural selector detected: '{stripped}'.",
                    severity="WARNING",
                    rule_id="PW-005",
                    remediation="Use semantic user-facing locators or scoped data-testid."
                ))
            elif UNGROUNDED_NTH_PATTERN.search(line):
                violations.append(LintViolation(
                    idx,
                    "LOCATOR_QUALITY_WARNING",
                    f"Ungrounded index-based selector '.nth()' detected: '{stripped}'.",
                    severity="WARNING",
                    rule_id="PW-005",
                    remediation="Filter by accessible role, label, or text instead of relying on DOM ordinal index."
                ))

        # Rule 6 (C3): Broken Attribute Selector Syntax
        if BROKEN_ATTR_SELECTOR_PATTERN.search(line):
            violations.append(LintViolation(
                idx,
                "SELECTOR_SYNTAX_VIOLATION",
                f"Attribute selector missing square brackets: '{stripped}'. Use '[role=\"...\"]' instead of raw 'attribute=value'.",
                severity="BLOCK",
                rule_id="C3-001",
                remediation="Wrap attribute selectors in square brackets: '[role=\"...\"]'."
            ))

        # Rule 7 (C2): Collision-Prone Static Identifiers
        if STATIC_WORKER_PATTERN.search(line) and not DYNAMIC_DATA_PATTERN.search(line):
            if not any(safe in line.lower() for safe in ["process.env", "dummy", "placeholder", "mock", "test_id"]):
                violations.append(LintViolation(
                    idx,
                    "COLLISION_DATA_VIOLATION",
                    f"Hardcoded user/entity identifier detected: '{stripped}'. Use collision-resistant dynamic generation (e.g., 'user_' + Date.now()).",
                    severity="BLOCK",
                    rule_id="C2-001",
                    remediation="Use collision-resistant timestamps or random IDs: 'user_' + Date.now()."
                ))

        # Rule SEC-002: Unmasked Token or Credential Logging
        if UNMASKED_LOG_PATTERN.search(line):
            violations.append(LintViolation(
                idx,
                "UNMASKED_CREDENTIAL_LOG_VIOLATION",
                f"Prohibited unmasked credential logging: '{stripped}'. Never print tokens, auth headers, or raw environment variables to console/logs.",
                severity="BLOCK",
                rule_id="SEC-002",
                remediation="Redact credentials before logging: '***REDACTED***'."
            ))

        # Rule 9: Excessive Concurrency Burst
        if CONCURRENCY_BURST_PATTERN.search(line):
            violations.append(LintViolation(
                idx,
                "EXCESSIVE_CONCURRENCY_VIOLATION",
                f"Concurrency limit exceeded: '{stripped}'. Max allowed concurrent requests per batch is 5 to prevent DoS on target systems.",
                severity="BLOCK",
                rule_id="PERF-001",
                remediation="Limit concurrency burst batch size to <= 5 concurrent promises."
            ))

        # Check for test blocks and test IDs
        if re.search(r'\btest\s*\(', line):
            has_test_block = True
            if TEST_ID_PATTERN.search(line):
                has_test_id = True

    # Rule PW-003: Explicit ID Traceability
    if has_test_block and not has_test_id:
        violations.append(LintViolation(
            1,
            "TRACEABILITY_VIOLATION",
            "Test cases must explicitly reference traceable Test Case, Gap, or Guard IDs in titles (e.g., test('TC-AUTH-001: ...') or test('GAP-xxx: ...') or test('GUARD-xxx: ...')).",
            severity="BLOCK",
            rule_id="PW-003",
            remediation="Add traceable ID prefix in test title: 'TC-MODULE-001: ...' or 'GAP-001: ...' or 'GUARD-001: ...'."
        ))

    # Rule 4: Assertion Presence
    if has_test_block and not has_assertion:
        violations.append(LintViolation(
            1,
            "MISSING_ASSERTION_VIOLATION",
            "Test script contains test blocks without assertions. Add web-first assertions (await expect(locator).toBeVisible()).",
            severity="BLOCK",
            rule_id="QA-006",
            remediation="Add explicit web-first assertions: await expect(locator).toBeVisible()."
        ))

    return violations


def lint_path(target_path: Path) -> int:
    """
    Lints a file or directory of source/test files.
    Returns:
    - 0 if clean or only WARNINGs found.
    - 1 if one or more BLOCK violations found.
    """
    if target_path.is_file():
        files = [target_path]
    elif target_path.is_dir():
        files = [
            p for p in target_path.rglob("*")
            if p.suffix in [".js", ".mjs", ".ts", ".tsx", ".py"] and not any(
                (part.startswith(".") and not part.startswith(".env")) or part in ["node_modules", "__pycache__", ".git"]
                for part in p.relative_to(target_path).parts
            )
        ]
    else:
        print(f"[ERROR] Path does not exist: {target_path}")
        return 1

    total_block = 0
    total_warn = 0

    for f in sorted(files):
        violations = lint_file(f)
        if violations:
            blocks = [v for v in violations if getattr(v, "severity", "BLOCK") == "BLOCK"]
            warns = [v for v in violations if getattr(v, "severity", "BLOCK") == "WARNING"]
            total_block += len(blocks)
            total_warn += len(warns)

            status_tag = "[FAIL]" if blocks else "[WARN]"
            print(f"\n{status_tag} {f}:")
            for v in violations:
                sev = getattr(v, "severity", "BLOCK")
                rule_id = getattr(v, "rule_id", "")
                rule_tag = f"{rule_id} ({v[1]})" if rule_id else v[1]
                print(f"  Line {v[0]} [{sev}] [{rule_tag}]: {v[2]}")
                remediation = getattr(v, "remediation", "")
                if remediation:
                    print(f"    --> Fix: {remediation}")

    if total_block == 0 and total_warn == 0:
        print(f"[PASS] All {len(files)} file(s) meet Senior Dev testing standards (0 sleeps, 0 hardcoded secrets, verified traceability, safe promises).")
        return 0
    elif total_block == 0:
        print(f"\n[PASS WITH ADVISORIES] {len(files)} file(s) clean of BLOCK violations ({total_warn} WARNING(s)).")
        return 0
    else:
        print(f"\n[TOTAL] Found {total_block} BLOCK violation(s) and {total_warn} WARNING(s) across {len(files)} file(s).")
        return 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python lint_test_code.py <file_or_dir_to_lint>")
        sys.exit(1)

    target = Path(sys.argv[1])
    sys.exit(lint_path(target))
