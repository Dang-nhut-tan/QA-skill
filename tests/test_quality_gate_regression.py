#!/usr/bin/env python3
"""
tests/test_quality_gate_regression.py
Regression test suite for AI Coding Quality Gate and Lint Rules.
Covers all 15 mandatory verification requirements from Section 7:
1. Detect fixed wait (PW-001)
2. Detect floating promise (PW-002)
3. Detect test missing ID (PW-003)
4. Detect focused test (PW-004)
5. Detect hardcoded secret (SEC-001)
6. Detect silent exception (PY-001)
7. Clean valid code does not trigger false positives
8. Quality Gate returns exit code != 0 when BLOCK violation is present
9. WARNING does not fail Quality Gate (exit code 0)
10. Non-existent path or tool error reports error, never false PASS
11. Human Gate cannot be bypassed (QA-004)
12. Production Safety Gate cannot be bypassed (QA-005)
13. Standard and critical modes are unaffected
14. Auto-fix / linter does not touch or modify files out of scope
15. Never declare PASS when verification has not run (QA-001)
"""

import sys
import os
import unittest
import tempfile
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from scripts.lint_test_code import lint_file, lint_path, LintViolation
from scripts.quality_gate import run_quality_gate, validate_qa_workflow_state
from scripts.state_manager import WorkflowStateManager, classify_environment


class TestQualityGateRegression(unittest.TestCase):

    # 1. Detect fixed wait (PW-001)
    def test_01_detect_fixed_wait(self):
        with tempfile.NamedTemporaryFile(suffix=".spec.js", mode="w", encoding="utf-8", delete=False) as f:
            f.write("test('TC-01: Login', async ({ page }) => {\n  await page.waitForTimeout(3000);\n  expect(true).toBe(true);\n});\n")
            p = Path(f.name)
        try:
            violations = lint_file(p)
            self.assertTrue(any(v.rule == "ZERO_SLEEP_VIOLATION" and v.severity == "BLOCK" for v in violations))
            self.assertTrue(any(v.rule_id == "PW-001" for v in violations))
        finally:
            p.unlink(missing_ok=True)

    # 2. Detect floating promise (PW-002)
    def test_02_detect_floating_promise(self):
        with tempfile.NamedTemporaryFile(suffix=".spec.js", mode="w", encoding="utf-8", delete=False) as f:
            f.write("test('TC-02: Missing Await', async ({ page }) => {\n  page.click('#btn-submit');\n  expect(page.locator('.msg')).toBeVisible();\n});\n")
            p = Path(f.name)
        try:
            violations = lint_file(p)
            self.assertTrue(any(v.rule == "FLOATING_PROMISE_VIOLATION" for v in violations))
            self.assertTrue(any(v.rule_id == "PW-002" for v in violations))
        finally:
            p.unlink(missing_ok=True)

    # 3. Detect test missing ID (PW-003)
    def test_03_detect_test_missing_id(self):
        with tempfile.NamedTemporaryFile(suffix=".spec.js", mode="w", encoding="utf-8", delete=False) as f:
            f.write("test('Untracked Random Test Without ID', async ({ page }) => {\n  await expect(page.locator('.msg')).toBeVisible();\n});\n")
            p = Path(f.name)
        try:
            violations = lint_file(p)
            self.assertTrue(any(v.rule == "TRACEABILITY_VIOLATION" for v in violations))
            self.assertTrue(any(v.rule_id == "PW-003" for v in violations))
        finally:
            p.unlink(missing_ok=True)

    # 4. Detect focused test (PW-004)
    def test_04_detect_focused_test(self):
        with tempfile.NamedTemporaryFile(suffix=".spec.js", mode="w", encoding="utf-8", delete=False) as f:
            f.write("test.only('TC-04: Focused test', async ({ page }) => {\n  await expect(page.locator('.msg')).toBeVisible();\n});\n")
            p = Path(f.name)
        try:
            violations = lint_file(p)
            self.assertTrue(any(v.rule == "FOCUSED_TEST_VIOLATION" for v in violations))
            self.assertTrue(any(v.rule_id == "PW-004" for v in violations))
        finally:
            p.unlink(missing_ok=True)

    # 5. Detect hardcoded secret (SEC-001)
    def test_05_detect_hardcoded_secret(self):
        with tempfile.NamedTemporaryFile(suffix=".spec.js", mode="w", encoding="utf-8", delete=False) as f:
            f.write("test('TC-05: Auth', async () => {\n  const api_key = 'sk_live_verysecret12345';\n  expect(true).toBe(true);\n});\n")
            p = Path(f.name)
        try:
            violations = lint_file(p)
            self.assertTrue(any(v.rule == "HARDCODED_SECRET_VIOLATION" for v in violations))
            self.assertTrue(any(v.rule_id == "SEC-001" for v in violations))
        finally:
            p.unlink(missing_ok=True)

    # 6. Detect silent exception (PY-001)
    def test_06_detect_silent_exception(self):
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", encoding="utf-8", delete=False) as f:
            f.write("def process_data():\n    try:\n        do_something()\n    except Exception:\n        pass\n")
            p = Path(f.name)
        try:
            violations = lint_file(p)
            self.assertTrue(any(v.rule == "SILENT_EXCEPTION_VIOLATION" for v in violations))
            self.assertTrue(any(v.rule_id == "PY-001" for v in violations))
        finally:
            p.unlink(missing_ok=True)

    # 7. Clean valid code does not trigger false positives
    def test_07_clean_valid_code_passes(self):
        with tempfile.NamedTemporaryFile(suffix=".spec.js", mode="w", encoding="utf-8", delete=False) as f:
            f.write(
                "import { test, expect } from '@playwright/test';\n\n"
                "test('TC-LOGIN-001: Valid spec', async ({ page }) => {\n"
                "  const pass = process.env.TEST_PASSWORD;\n"
                "  await page.goto('/login');\n"
                "  await expect(page.locator('.dashboard')).toBeVisible();\n"
                "});\n"
            )
            p = Path(f.name)
        try:
            violations = lint_file(p)
            self.assertEqual(len([v for v in violations if v.severity == "BLOCK"]), 0)
        finally:
            p.unlink(missing_ok=True)

    # 8. Quality Gate returns exit code != 0 when BLOCK violation is present
    def test_08_quality_gate_returns_exit_1_on_block(self):
        with tempfile.NamedTemporaryFile(suffix=".spec.js", mode="w", encoding="utf-8", delete=False) as f:
            f.write("test('TC-08: Sleep', async ({ page }) => {\n  await page.waitForTimeout(5000);\n  expect(true).toBe(true);\n});\n")
            p = Path(f.name)
        try:
            code, report = run_quality_gate(target_paths=[p])
            self.assertEqual(code, 1)
            self.assertEqual(report["status"], "FAIL")
            self.assertGreater(report["block_count"], 0)
        finally:
            p.unlink(missing_ok=True)

    # 9. WARNING does not fail Quality Gate (exit code 0)
    def test_09_warning_does_not_fail_quality_gate(self):
        with tempfile.NamedTemporaryFile(suffix=".spec.js", mode="w", encoding="utf-8", delete=False) as f:
            f.write(
                "import { test, expect } from '@playwright/test';\n\n"
                "test('TC-LOC-001: Absolute XPath Warning', async ({ page }) => {\n"
                "  await page.locator('//html/body/div[2]/button').click();\n"
                "  await expect(page.locator('.msg')).toBeVisible();\n"
                "});\n"
            )
            p = Path(f.name)
        try:
            code, report = run_quality_gate(target_paths=[p], strict=False)
            self.assertEqual(code, 0)
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["block_count"], 0)
            self.assertGreater(report["warning_count"], 0)
        finally:
            p.unlink(missing_ok=True)

    # 10. Non-existent path or tool error reports error, never false PASS
    def test_10_invalid_path_returns_error_exit_2(self):
        non_existent = Path(tempfile.gettempdir()) / "non_existent_file_xyz_123.js"
        code, report = run_quality_gate(target_paths=[non_existent])
        self.assertEqual(code, 2)
        self.assertEqual(report["status"], "ERROR")
        self.assertIn("does not exist", report["error"])

    # 11. Human Gate cannot be bypassed (QA-004)
    def test_11_human_gate_cannot_be_bypassed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = WorkflowStateManager(tmpdir)
            mgr.init_state("ModuleAuth", {"root": tmpdir})
            mgr.transition("CONTEXT_DISCOVERY")
            mgr.transition("GAP_ANALYSIS")
            mgr.transition("TESTCASE_GENERATION")
            mgr.transition("TESTCASE_REVIEW")
            mgr.transition("WAITING_FOR_APPROVED_TESTCASES", metadata={"artifacts": {"approved_excel": "test.xlsx"}})
            # Creating dummy test.xlsx so path check doesn't fail before approval token check
            (Path(tmpdir) / "test.xlsx").write_text("dummy")

            # Transitioning to AUTOMATION_IMPLEMENTATION without approval token must raise ValueError
            with self.assertRaises(ValueError) as ctx:
                mgr.transition("AUTOMATION_IMPLEMENTATION", approval_token=None)
            self.assertIn("Human Gate 2 requires a non-empty approval_token", str(ctx.exception))

    # 12. Production Safety Gate cannot be bypassed (QA-005)
    def test_12_production_safety_gate_cannot_be_bypassed(self):
        prod_classification = classify_environment("https://api.production-enterprise.com")
        self.assertEqual(prod_classification["tier"], "production")
        self.assertFalse(prod_classification["allowlist_verified"])

        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = WorkflowStateManager(tmpdir)
            mgr.init_state("Checkout", {"base_url": "https://api.production-enterprise.com"})
            allowed, msg = mgr.check_mutation_allowed()
            self.assertFalse(allowed)
            self.assertIn("Production Safety Gate", msg)

    # 13. Standard and critical modes are unaffected
    def test_13_standard_and_critical_modes_unaffected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = WorkflowStateManager(tmpdir)
            st = mgr.init_state("StdModule", {}, execution_mode="standard")
            self.assertEqual(st["execution_mode"], "standard")

            mgr_crit = WorkflowStateManager(tmpdir, module_name="CritModule")
            st_crit = mgr_crit.init_state("CritModule", {}, execution_mode="critical")
            self.assertEqual(st_crit["execution_mode"], "critical")

    # 14. Auto-fix / linter does not touch or modify files out of scope
    def test_14_quality_gate_is_strictly_read_only(self):
        with tempfile.NamedTemporaryFile(suffix=".spec.js", mode="w", encoding="utf-8", delete=False) as f:
            original_content = "test('TC-14: Read Only Check', async ({ page }) => {\n  await expect(page.locator('.item')).toBeVisible();\n});\n"
            f.write(original_content)
            p = Path(f.name)
        try:
            code, report = run_quality_gate(target_paths=[p])
            self.assertEqual(code, 0)
            # Verify file content is strictly unchanged
            self.assertEqual(p.read_text(encoding="utf-8"), original_content)
        finally:
            p.unlink(missing_ok=True)

    # 15. Never declare PASS when verification has not run (QA-001)
    def test_15_no_false_pass_when_verification_missing(self):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", encoding="utf-8", delete=False) as f:
            # Fake state marked COMPLETED but with no artifacts and no test runs
            fake_state = {
                "module_name": "TestFake",
                "current_state": "COMPLETED",
                "completed_steps": ["INITIALIZED", "CONTEXT_DISCOVERY"],
                "artifacts": {},
                "test_runs": []
            }
            json.dump(fake_state, f)
            state_path = Path(f.name)
        try:
            violations = validate_qa_workflow_state(state_path)
            self.assertTrue(any(v.rule == "NO_FALSE_PASS_VIOLATION" and v.severity == "BLOCK" for v in violations))
            self.assertTrue(any(v.rule_id == "QA-001" for v in violations))
        finally:
            state_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
