#!/usr/bin/env python3
"""
tests/test_qa_skills_regression.py
Comprehensive regression test suite for the QA Agent Testing System.
Validates the 5 critical bug fixes and architecture enhancements using standard `unittest`:
1. state_manager: Order-preserving deduplication for lists of scalars and non-hashable dicts.
2. read_approved_testcases: Bilingual normalization (Yes/No, Có/Không) and strict error reporting.
3. export_testcases: Bilingual severity styling (Chặn/Critical, Sai/Major, Nhỏ/Minor).
4. traceability_validator: Context-aware slash splitting (preserving code file paths vs splitting paired requirement IDs).
5. learn_manager: Multi-root skills resolution and path traversal security guards.
"""

import sys
import os
import unittest
import tempfile
import json
from pathlib import Path

# Add project root and scripts directory to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from scripts.state_manager import _dedup_list, WorkflowStateManager
from scripts.read_approved_testcases import parse_automation_ready_val
from scripts.export_testcases import (
    style_severity_cell,
    FILL_CHAN,
    FILL_SAI,
    FILL_NHO
)
from scripts.traceability_validator import split_requirement_references
from scripts.learn_manager import resolve_skills_root, propose_learning, approve_learning, query_learnings
from scripts.verify_and_embed_images import verify_and_fix_report_images

class MockCell:
    def __init__(self, value=None):
        self.value = value
        self.fill = None
        self.font = None
        self.alignment = None

class TestQASkillsRegression(unittest.TestCase):

    # =========================================================================
    # Test 1: state_manager list deduplication
    # =========================================================================
    def test_dedup_list_scalars_preserves_order(self):
        input_list = ["Step 1", "Step 2", "Step 1", "Step 3", "Step 2"]
        expected = ["Step 1", "Step 2", "Step 3"]
        self.assertEqual(_dedup_list(input_list), expected)

    def test_dedup_list_dicts_no_type_error(self):
        # Dicts are unhashable in standard set()
        d1 = {"id": "GAP-001", "name": "Auth Issue"}
        d2 = {"name": "Auth Issue", "id": "GAP-001"} # Same content, different key order
        d3 = {"id": "GAP-002", "name": "Timeout Issue"}
        
        merged = _dedup_list([d1, d2, d3])
        self.assertEqual(len(merged), 2)
        self.assertEqual(merged[0]["id"], "GAP-001")
        self.assertEqual(merged[1]["id"], "GAP-002")

    def test_workflow_state_manager_transition_with_dict_metadata(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            mgr = WorkflowStateManager(tmp_dir)
            mgr.init_state("TestModule", {"repo": "test"})
            
            # Transition with clarification_issues list of dicts
            issues = [{"id": "GAP-001", "title": "Issue 1"}]
            state = mgr.transition(
                "WAITING_FOR_REQUIREMENT_CLARIFICATION",
                "Found gaps",
                metadata={"clarification_issues": issues}
            )
            self.assertEqual(len(state["clarification_issues"]), 1)
            
            # Transition again appending another dict and a duplicate dict
            issues_next = [
                {"title": "Issue 1", "id": "GAP-001"}, # duplicate
                {"id": "GAP-002", "title": "Issue 2"}
            ]
            state2 = mgr.transition(
                "WAITING_FOR_REQUIREMENT_CLARIFICATION",
                "Appended gaps",
                metadata={"clarification_issues": issues_next}
            )
            self.assertEqual(len(state2["clarification_issues"]), 2)

    # =========================================================================
    # Test 2: read_approved_testcases bilingual normalization
    # =========================================================================
    def test_automation_ready_truthy_values(self):
        truthy_inputs = ["Yes", "yes", "Y", "y", "True", "true", "1", "Có", "có", "Co", "co"]
        for val in truthy_inputs:
            with self.subTest(val=val):
                self.assertTrue(parse_automation_ready_val(val, row_idx=2))

    def test_automation_ready_falsy_values(self):
        falsy_inputs = ["No", "no", "N", "n", "False", "false", "0", "Không", "không", "Khong", "", None]
        for val in falsy_inputs:
            with self.subTest(val=val):
                self.assertFalse(parse_automation_ready_val(val, row_idx=2))

    def test_automation_ready_invalid_values_raise_error_with_row(self):
        invalid_inputs = ["Yess", "Oki", "Được", "Chắc chắn", "abc", 123]
        for val in invalid_inputs:
            with self.subTest(val=val):
                with self.assertRaises(ValueError) as ctx:
                    parse_automation_ready_val(val, row_idx=15)
                self.assertIn("row 15", str(ctx.exception))

    # =========================================================================
    # Test 3: export_testcases bilingual severity styling
    # =========================================================================
    def test_severity_styling_vietnamese(self):
        c1 = MockCell("Chặn")
        style_severity_cell(c1)
        self.assertEqual(c1.fill, FILL_CHAN)

        c2 = MockCell("Sai")
        style_severity_cell(c2)
        self.assertEqual(c2.fill, FILL_SAI)

        c3 = MockCell("Nhỏ")
        style_severity_cell(c3)
        self.assertEqual(c3.fill, FILL_NHO)

    def test_severity_styling_english(self):
        for val in ["Critical", "critical", "Blocker", "blocker"]:
            with self.subTest(val=val):
                cell = MockCell(val)
                style_severity_cell(cell)
                self.assertEqual(cell.fill, FILL_CHAN)

        for val in ["Major", "major"]:
            with self.subTest(val=val):
                cell = MockCell(val)
                style_severity_cell(cell)
                self.assertEqual(cell.fill, FILL_SAI)

        for val in ["Minor", "minor", "Trivial", "low"]:
            with self.subTest(val=val):
                cell = MockCell(val)
                style_severity_cell(cell)
                self.assertEqual(cell.fill, FILL_NHO)

    # =========================================================================
    # Test 4: traceability_validator context-aware slash splitting
    # =========================================================================
    def test_traceability_paired_requirement_ids_are_split(self):
        res = split_requirement_references("REQ-01/REQ-02")
        self.assertEqual(res, ["REQ-01", "REQ-02"])

        res2 = split_requirement_references("SPEC-AU-01/SPEC-AU-02")
        self.assertEqual(res2, ["SPEC-AU-01", "SPEC-AU-02"])

    def test_traceability_file_paths_are_preserved(self):
        # File paths with slash and extension or line number must NOT be chopped into pieces
        cases = [
            "src/features/auth/useLogin.ts#L45",
            "./scripts/state_manager.py",
            "C:/projects/myapp/index.ts#L10",
            "auth/login.py"
        ]
        for p in cases:
            with self.subTest(path=p):
                res = split_requirement_references(p)
                self.assertEqual(res, [p])

    def test_traceability_mixed_file_path_and_spec_are_split_properly(self):
        mixed = "src/features/auth/useLogin.ts#L45 / SPEC-01"
        res = split_requirement_references(mixed)
        self.assertEqual(res, ["src/features/auth/useLogin.ts#L45", "SPEC-01"])

    def test_traceability_standard_delimiters(self):
        standard = "REQ-A, REQ-B; REQ-C | REQ-D"
        res = split_requirement_references(standard)
        self.assertEqual(res, ["REQ-A", "REQ-B", "REQ-C", "REQ-D"])

    # =========================================================================
    # Test 5: learn_manager multi-root skills resolution & security
    # =========================================================================
    def test_learn_manager_resolves_embedded_agent_skills(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            embedded_dir = tmp_root / ".agent" / "skills"
            embedded_dir.mkdir(parents=True)
            
            resolved = resolve_skills_root(explicit_root=str(tmp_root))
            self.assertEqual(resolved, embedded_dir.resolve())

    def test_learn_manager_resolves_verified_repo_skills(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            skills_dir = tmp_root / "skills"
            skills_dir.mkdir(parents=True)
            (tmp_root / "scripts").mkdir(parents=True)
            (tmp_root / "plugin.json").write_text("{}", encoding="utf-8")
            (tmp_root / "scripts" / "learn_manager.py").write_text("# marker", encoding="utf-8")
            
            resolved = resolve_skills_root(explicit_root=str(tmp_root))
            self.assertEqual(resolved, skills_dir.resolve())

    def test_learn_manager_rejects_unverified_explicit_root(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            # Empty folder without .agent/skills or verified markers
            with self.assertRaises(RuntimeError) as ctx:
                resolve_skills_root(explicit_root=str(tmp_root))
            self.assertIn("does not have a valid skills layout", str(ctx.exception))

    # =========================================================================
    # Test 6: verify_and_embed_images for visual proof reliability
    # =========================================================================
    def test_verify_report_images_detects_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            report = tmp_root / "test-gaps.md"
            report.write_text("![Missing](./screenshots/non_existent.png)\n", encoding="utf-8")
            res = verify_and_fix_report_images(report, tmp_root)
            self.assertFalse(res["success"])
            self.assertEqual(len(res["missing_images"]), 1)
            self.assertEqual(res["missing_images"][0]["line"], 1)

    def test_verify_report_images_passes_and_injects_fallback_for_existing_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            screenshots_dir = tmp_root / "screenshots"
            screenshots_dir.mkdir(parents=True)
            img = screenshots_dir / "valid.png"
            img.write_bytes(b"\x89PNG\r\n\x1a\nfakeimage")
            
            report = tmp_root / "test-gaps.md"
            report.write_text("![Valid](./screenshots/valid.png)\n", encoding="utf-8")
            
            res = verify_and_fix_report_images(report, tmp_root, auto_fix_links=True)
            self.assertTrue(res["success"])
            self.assertEqual(len(res["found_images"]), 1)
            self.assertTrue(res["report_modified"])
            
            updated_content = report.read_text(encoding="utf-8")
            self.assertIn("file:///", updated_content)
            self.assertIn("Mở ảnh gốc", updated_content)


    # =========================================================================
    # Test 7: Security Sanitizer - Secret keys rejected from state metadata
    # =========================================================================
    def test_state_manager_rejects_plaintext_secrets_in_init(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            mgr = WorkflowStateManager(tmp_dir)
            forbidden_keys = [
                {"db_password": "supersecretpassword"},
                {"auth_token": "bearer xyz123"},
                {"client_secret": "my-secret-key"},
                {"api_key": "AIzaSy..."}
            ]
            for bad_meta in forbidden_keys:
                with self.subTest(meta=bad_meta):
                    with self.assertRaises(ValueError) as ctx:
                        mgr.init_state("AuthModule", bad_meta)
                    self.assertIn("Security Alert", str(ctx.exception))

    def test_state_manager_rejects_plaintext_secrets_in_transition(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            mgr = WorkflowStateManager(tmp_dir)
            mgr.init_state("AuthModule", {"repo": "myapp"})
            with self.assertRaises(ValueError) as ctx:
                mgr.transition(
                    "WAITING_FOR_REQUIREMENT_CLARIFICATION",
                    "Attempting to log secret",
                    metadata={"user_password": "PlainPassword123"}
                )
            self.assertIn("Security Alert", str(ctx.exception))

    def test_state_manager_accepts_clean_metadata(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            mgr = WorkflowStateManager(tmp_dir)
            state = mgr.init_state("AuthModule", {"repo_name": "clean-repo", "module_version": "1.2.0"})
            self.assertEqual(state["repo_info"]["module_version"], "1.2.0")

    # =========================================================================
    # Test 8: FSM State Transition Matrix Validation
    # =========================================================================
    def test_fsm_rejects_invalid_state_jumps(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            mgr = WorkflowStateManager(tmp_dir)
            mgr.init_state("TestModule", {"repo": "test"})
            
            # INITIALIZED directly to COMPLETED is forbidden
            with self.assertRaises(ValueError) as ctx:
                mgr.transition("COMPLETED", "Illegal jump directly to completed")
            self.assertIn("FSM Transition Violation", str(ctx.exception))

            # INITIALIZED directly to AUTOMATION_IMPLEMENTATION is forbidden
            with self.assertRaises(ValueError) as ctx:
                mgr.transition("AUTOMATION_IMPLEMENTATION", "Illegal jump skipping gates")
            self.assertIn("FSM Transition Violation", str(ctx.exception))

    def test_fsm_allows_valid_linear_transitions(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            mgr = WorkflowStateManager(tmp_dir)
            mgr.init_state("TestModule", {"repo": "test"})
            
            # Step 1 -> GAP_ANALYSIS
            s1 = mgr.transition("GAP_ANALYSIS", "Starting gap analysis")
            self.assertEqual(s1["current_state"], "GAP_ANALYSIS")

            # Step 2 -> WAITING_FOR_REQUIREMENT_CLARIFICATION
            s2 = mgr.transition("WAITING_FOR_REQUIREMENT_CLARIFICATION", "Human Gate 1")
            self.assertEqual(s2["current_state"], "WAITING_FOR_REQUIREMENT_CLARIFICATION")

            # Step 3 -> TESTCASE_GENERATION
            s3 = mgr.transition("TESTCASE_GENERATION", "User approved, designing test cases")
            self.assertEqual(s3["current_state"], "TESTCASE_GENERATION")

    # =========================================================================
    # Test 9: Zero Token Bloat Continuous Learning (Skill Immutability)
    # =========================================================================
    def test_learn_manager_does_not_mutate_skill_md_on_approval(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            skills_dir = tmp_root / "skills" / "automation-implementation"
            skills_dir.mkdir(parents=True)
            (tmp_root / "scripts").mkdir(parents=True)
            (tmp_root / "plugin.json").write_text("{}", encoding="utf-8")
            (tmp_root / "scripts" / "learn_manager.py").write_text("# marker", encoding="utf-8")
            
            skill_md = skills_dir / "SKILL.md"
            initial_content = "---\nname: automation-implementation\n---\n# Original Skill Instructions\nStrictly immutable.\n"
            skill_md.write_text(initial_content, encoding="utf-8")

            # Propose learning
            proposal = propose_learning(
                title="Flaky Submit Button Wait",
                issue="Button click race condition in slow 3G",
                root_cause="useSubmitOnce hook async transition",
                solution="Use waitForResponse instead of arbitrary delay",
                target_skill="automation-implementation",
                tags=["flaky", "submit"],
                project_root=str(tmp_root)
            )
            self.assertEqual(proposal["status"], "PENDING_APPROVAL")

            # Approve learning
            approved = approve_learning(proposal["id"], project_root=str(tmp_root))
            self.assertEqual(approved["status"], "APPLIED")

            # CRITICAL ASSERTION: SKILL.md must remain COMPLETELY UNCHANGED
            current_content = skill_md.read_text(encoding="utf-8")
            self.assertEqual(current_content, initial_content, "SKILL.md must NEVER be modified to avoid token bloat!")

            # Verify structured JSON contains the approved learning
            learnings_file = tmp_root / "references" / "project-learnings.json"
            self.assertTrue(learnings_file.exists())
            with open(learnings_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertTrue(any(item["id"] == proposal["id"] and item["status"] == "APPLIED" for item in data.get("applied", [])))

            # Verify dynamic query retrieves the learning
            queried = query_learnings(project_root=str(tmp_root))
            self.assertEqual(len(queried), 1)
            self.assertEqual(queried[0]["id"], proposal["id"])


    # =========================================================================
    # Test 10: Enterprise Hardening V2 (Hyphenated keys, URI redaction, FSM Rollback)
    # =========================================================================
    def test_state_manager_rejects_hyphenated_and_advanced_secret_keys(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            mgr = WorkflowStateManager(tmp_dir)
            hyphen_cases = [
                {"x-api-key": "secret_key_1"},
                {"auth-token": "jwt.abc.xyz"},
                {"access-key-id": "AKIA123"},
                {"jwt": "header.payload.sig"},
                {"bearer": "token123"},
                {"passphrase": "my long pass phrase"},
                {"otp": "123456"}
            ]
            for case in hyphen_cases:
                with self.subTest(case=case):
                    with self.assertRaises(ValueError) as ctx:
                        mgr.init_state("AuthModule", case)
                    self.assertIn("Security Alert", str(ctx.exception))

    def test_state_manager_redacts_credentials_in_uri(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            mgr = WorkflowStateManager(tmp_dir)
            clean_meta = {
                "db_uri": "postgres://admin:SuperSecretPass123@staging-db:5432/main",
                "api_endpoint": "https://service_user:Token999@api.example.com/v1"
            }
            state = mgr.init_state("DataModule", clean_meta)
            db_res = state["repo_info"]["db_uri"]
            api_res = state["repo_info"]["api_endpoint"]
            self.assertNotIn("SuperSecretPass123", db_res)
            self.assertIn("***REDACTED***", db_res)
            self.assertNotIn("Token999", api_res)
            self.assertIn("***REDACTED***", api_res)

    def test_fsm_allows_clarification_and_execution_rollback(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            mgr = WorkflowStateManager(tmp_dir)
            mgr.init_state("AuthModule", {"repo": "app"})
            
            # 1. INITIALIZED -> GAP_ANALYSIS -> WAITING_FOR_REQUIREMENT_CLARIFICATION
            mgr.transition("GAP_ANALYSIS", "Found gaps")
            mgr.transition("WAITING_FOR_REQUIREMENT_CLARIFICATION", "Human Gate 1")

            # 2. Rollback to CONTEXT_DISCOVERY when BA updates spec scope
            s_disc = mgr.transition("CONTEXT_DISCOVERY", "BA updated spec, re-scanning context")
            self.assertEqual(s_disc["current_state"], "CONTEXT_DISCOVERY")

            # 3. Advance to AUTOMATION_EXECUTION
            mgr.transition("GAP_ANALYSIS", "Analysis 2")
            mgr.transition("TESTCASE_GENERATION", "Gen testcases")
            mgr.transition("TESTCASE_REVIEW", "Review")
            mgr.transition("WAITING_FOR_APPROVED_TESTCASES", "Gate 2")
            mgr.transition("AUTOMATION_IMPLEMENTATION", "Writing tests")
            mgr.transition("AUTOMATION_EXECUTION", "Running suite")

            # 4. Rollback from AUTOMATION_EXECUTION to GAP_ANALYSIS when test exposes spec defect
            s_back = mgr.transition("GAP_ANALYSIS", "Spec bug discovered during test execution")
            self.assertEqual(s_back["current_state"], "GAP_ANALYSIS")

    def test_fsm_blocks_excessive_clarification_loops(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            mgr = WorkflowStateManager(tmp_dir)
            mgr.init_state("AuthModule", {"repo": "app"})
            mgr.transition("GAP_ANALYSIS", "1")
            mgr.transition("WAITING_FOR_REQUIREMENT_CLARIFICATION", "Gate")

            # Loop 1
            mgr.transition("GAP_ANALYSIS", "Back 1")
            mgr.transition("WAITING_FOR_REQUIREMENT_CLARIFICATION", "Gate")

            # Loop 2
            mgr.transition("GAP_ANALYSIS", "Back 2")
            mgr.transition("WAITING_FOR_REQUIREMENT_CLARIFICATION", "Gate")

            # Loop 3 must be blocked by safety guard
            with self.assertRaises(ValueError) as ctx:
                mgr.transition("GAP_ANALYSIS", "Back 3")
            self.assertIn("FSM Safety Guard: Exceeded maximum allowed clarification loops", str(ctx.exception))

    def test_learn_manager_query_filters_by_target_skill(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            (tmp_root / "skills" / "skill-a").mkdir(parents=True)
            (tmp_root / "skills" / "skill-b").mkdir(parents=True)
            (tmp_root / "scripts").mkdir(parents=True)
            (tmp_root / "plugin.json").write_text("{}", encoding="utf-8")
            (tmp_root / "scripts" / "learn_manager.py").write_text("# marker", encoding="utf-8")
            (tmp_root / "skills" / "skill-a" / "SKILL.md").write_text("# A", encoding="utf-8")
            (tmp_root / "skills" / "skill-b" / "SKILL.md").write_text("# B", encoding="utf-8")

            p1 = propose_learning("Fix A", "Issue A", "Root A", "Sol A", "skill-a", module="Orders", project_root=str(tmp_root))
            approve_learning(p1["id"], project_root=str(tmp_root))

            p2 = propose_learning("Fix B", "Issue B", "Root B", "Sol B", "skill-b", module="Orders", project_root=str(tmp_root))
            approve_learning(p2["id"], project_root=str(tmp_root))

            # Query with target_skill isolates correctly
            res_a = query_learnings(module_name="Orders", target_skill="skill-a", project_root=str(tmp_root))
            self.assertEqual(len(res_a), 1)
            self.assertEqual(res_a[0]["id"], p1["id"])

            res_b = query_learnings(module_name="Orders", target_skill="skill-b", project_root=str(tmp_root))
            self.assertEqual(len(res_b), 1)
            self.assertEqual(res_b[0]["id"], p2["id"])

# =========================================================================
    # Group 11: Enterprise Hardening V3 (Root Import, Exact Traceability & Atomic Recovery)
    # =========================================================================
    def test_export_to_excel_callable_from_root(self):
        from scripts.export_testcases import export_to_excel
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_xlsx = Path(tmp_dir) / "test_v3_export.xlsx"
            payload = {
                "testcases": [
                    {"id": "TC-01", "module": "Auth", "name": "Login", "severity": "Chặn", "automation_ready": "Yes", "requirement_ref": "REQ-1"}
                ],
                "gaps": [],
                "summary": {"module_name": "Auth"}
            }
            export_to_excel(payload, tmp_xlsx)
            self.assertTrue(tmp_xlsx.exists())
            self.assertGreater(tmp_xlsx.stat().st_size, 1000)

    def test_traceability_exact_matching_avoids_false_positives(self):
        from scripts.traceability_validator import validate_traceability
        payload = {
            "requirements": ["REQ-1", "REQ-10", "REQ-100", "REQ-123"],
            "testcases": [
                {"id": "TC-01", "name": "Only for REQ-1", "requirement_ref": "REQ-1"}
            ]
        }
        res = validate_traceability(payload)
        m = res["metrics"]
        self.assertEqual(m["covered_requirements_count"], 1, "Only REQ-1 should be covered")
        self.assertEqual(m["orphan_requirements_count"], 3, "REQ-10, REQ-100, REQ-123 must be orphans")
        self.assertEqual(m["coverage_percentage"], 25.0, "Coverage must be 25%, NOT 100% false positive!")

    def test_state_manager_atomic_and_corrupted_recovery(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            mgr = WorkflowStateManager(tmp_dir)
            mgr.init_state("ModuleA", {"repo": "app"})
            self.assertTrue(mgr.exists())

            mgr.transition("CONTEXT_DISCOVERY", "test transition")
            bak_file = Path(tmp_dir) / ".qa-state.json.bak"
            self.assertTrue(bak_file.exists(), "Backup snapshot must exist after save")

            state_file = Path(tmp_dir) / ".qa-state.json"
            state_file.write_text("CORRUPTED INVALID JSON {", encoding="utf-8")

            loaded = mgr.load()
            self.assertEqual(loaded.get("module_name"), "ModuleA", "Must self-heal from backup snapshot")

    def test_fsm_closes_human_gate_2_backdoor(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            mgr = WorkflowStateManager(tmp_dir)
            mgr.init_state("ModuleA", {"repo": "app"})
            mgr.transition("GAP_ANALYSIS", "1")
            mgr.transition("TESTCASE_GENERATION", "2")
            mgr.transition("TESTCASE_REVIEW", "3")

            with self.assertRaises(ValueError) as ctx:
                mgr.transition("AUTOMATION_IMPLEMENTATION", "Attempting to bypass Gate 2")
            self.assertIn("FSM Transition Violation", str(ctx.exception))

            s_gate2 = mgr.transition("WAITING_FOR_APPROVED_TESTCASES", "Delivered Excel")
            self.assertEqual(s_gate2["current_state"], "WAITING_FOR_APPROVED_TESTCASES")

    def test_verify_images_markdown_table_preservation(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            screenshots_dir = tmp_root / "screenshots"
            screenshots_dir.mkdir(parents=True)
            (screenshots_dir / "img1.png").write_bytes(b"\x89PNGfake1")
            (screenshots_dir / "img2.png").write_bytes(b"\x89PNGfake2")

            report = tmp_root / "test-gaps.md"
            table_line = "| Bước | ![Img1](./screenshots/img1.png) | ![Img2](./screenshots/img2.png) |\n"
            report.write_text(table_line, encoding="utf-8")

            res = verify_and_fix_report_images(report, tmp_root, auto_fix_links=True)
            self.assertTrue(res["success"])
            self.assertEqual(len(res["found_images"]), 2)

            content = report.read_text(encoding="utf-8").strip()
            self.assertEqual(content.count("\n"), 0, "Table row must remain a single row with inline links!")
            self.assertIn("<br>*([Mở ảnh gốc", content)

if __name__ == "__main__":
    unittest.main(verbosity=2)
