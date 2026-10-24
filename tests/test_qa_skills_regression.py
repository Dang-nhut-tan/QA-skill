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
from scripts.learn_manager import resolve_skills_root

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

if __name__ == "__main__":
    unittest.main(verbosity=2)
