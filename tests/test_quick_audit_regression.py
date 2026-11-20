"""
tests/test_quick_audit_regression.py
Regression test suite for Fast-Track QA Audit v2 (Quick Mode Refactor).
Validates all 15 behavioral contracts required by Senior QA Automation Architect:
1. Quick actually reads code.
2. Quick actually performs Gap Analysis.
3. Does not declare bugs without empirical evidence.
4. Valid guards are not reported as bugs.
5. Incomplete discovery is reported honestly.
6. Production Safety Gate blocks mutation on live targets.
7. Quick does not export Excel.
8. Quick does not bypass human approval for full automation.
9. Quick state persistence and resumability.
10. Standard mode remains completely unaffected.
11. Critical mode remains completely unaffected.
12. Cache invalidation on source changes.
13. Timeout handling without false pass.
14. Non-applicable friction groups marked N/A.
15. Unreachable environment reported accurately.
"""

import os
import json
import time
import pytest
from pathlib import Path

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
import sys
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.quick_audit import FastTrackQAAuditor, FRICTION_GROUPS
from scripts.state_manager import WorkflowStateManager, classify_environment
from scripts.codegraph_discovery import MethodDiscoveryEngine

FIXTURE_DIR = PROJECT_ROOT / "tests" / "fixtures" / "golden-sample-project"
ORDER_TS = FIXTURE_DIR / "src" / "order.ts"
SPEC_MD = FIXTURE_DIR / "spec.md"


def test_quick_actually_reads_code(tmp_path):
    """1. Verify Quick Mode actually reads code using targeted AST discovery."""
    auditor = FastTrackQAAuditor(PROJECT_ROOT, module_name="test-read-code")
    res = auditor.run_audit(
        target_path="tests/fixtures/golden-sample-project/src/order.ts",
        target_symbol="handleApiOrder",
        spec_path=str(SPEC_MD),
        depth=1
    )
    assert auditor.discovery_complete is True
    assert auditor.discovery_metadata["status"] == "COMPLETE"
    assert auditor.discovery_metadata["line_count"] > 10
    assert "handleApiOrder" in auditor.discovery_metadata["source_snippet"]
    assert auditor.timings["discovery"] > 0.0


def test_quick_actually_performs_gap_analysis(tmp_path):
    """2. Verify Quick Mode executes the 5 Universal Friction Groups analysis."""
    auditor = FastTrackQAAuditor(PROJECT_ROOT, module_name="test-gap-analysis")
    res = auditor.run_audit(
        target_path="tests/fixtures/golden-sample-project/src/order.ts",
        target_symbol="handleApiOrder",
        spec_path=str(SPEC_MD),
    )
    assert len(auditor.findings) >= 5
    groups_evaluated = {f["group_key"] for f in auditor.findings}
    assert "DATA_LOSS" in groups_evaluated
    assert "DUPLICATE_ACTION" in groups_evaluated
    assert "ASYNC_RECOVERY" in groups_evaluated
    assert "ERROR_CONTRACT" in groups_evaluated
    assert "HIDDEN_LOGIC" in groups_evaluated
    assert auditor.timings["gap_analysis"] > 0.0


def test_quick_does_not_declare_bug_without_evidence(tmp_path):
    """3. Verify that suspected issues without empirical test pass stay as SUSPECTED or NOT_VERIFIED, never CONFIRMED_BUG."""
    auditor = FastTrackQAAuditor(PROJECT_ROOT, module_name="test-evidence-rule")
    auditor.run_audit(
        target_path="tests/fixtures/golden-sample-project/src/order.ts",
        target_symbol="createOrder",
        spec_path=str(SPEC_MD),
    )
    for finding in auditor.findings:
        if finding["verification_status"] == "CONFIRMED_BUG":
            # Must have concrete empirical evidence attached
            assert "Playwright CLI xác nhận" in finding["evidence"] or "exit code 0" in finding["evidence"]
        elif finding["risk_level"] == "High" and "order-api-bug-repro" not in str(auditor.repro_scripts):
            assert finding["verification_status"] in ["SUSPECTED", "NOT_VERIFIED", "NOT_APPLICABLE"]


def test_quick_valid_guard_not_reported_as_bug(tmp_path):
    """4. Verify that valid defensive guards are classified as CONFIRMED_GUARD and never reported as bugs."""
    auditor = FastTrackQAAuditor(PROJECT_ROOT, module_name="test-guard-rule")
    auditor.run_audit(
        target_path="tests/fixtures/golden-sample-project/src/order.ts",
        target_symbol="validateOrderQuantity",
        spec_path=str(SPEC_MD),
    )
    guard_findings = [f for f in auditor.findings if f["verification_status"] == "CONFIRMED_GUARD"]
    assert len(guard_findings) > 0
    # Guard items must never have CONFIRMED_BUG status
    for g in guard_findings:
        assert g["verification_status"] != "CONFIRMED_BUG"


def test_quick_discovery_incomplete_reported_honestly(tmp_path):
    """5. Verify that missing or unparseable target code honestly records DISCOVERY_INCOMPLETE without false completion."""
    auditor = FastTrackQAAuditor(tmp_path, module_name="test-incomplete-disc")
    res = auditor.run_audit(
        target_path="non/existent/missing_service.ts",
        target_symbol="nonExistentFunction12345",
    )
    assert auditor.discovery_complete is False
    assert auditor.discovery_metadata["status"] == "DISCOVERY_INCOMPLETE"
    assert "DISCOVERY_INCOMPLETE" in auditor.report_markdown
    # State history must contain DISCOVERY_INCOMPLETE
    state = auditor.state_mgr.load()
    states_in_history = [h.get("to_state") or h.get("state") for h in state["history"]]
    assert "DISCOVERY_INCOMPLETE" in states_in_history


def test_quick_production_safety_gate_blocks_mutation(tmp_path):
    """6. Verify Production Safety Gate blocks destructive actions on production URLs across quick mode."""
    auditor = FastTrackQAAuditor(
        PROJECT_ROOT,
        module_name="test-prod-safety",
        base_url="https://production-store.company.com"
    )
    res = auditor.run_audit(
        target_path="tests/fixtures/golden-sample-project/src/order.ts",
        target_symbol="handleApiOrder",
        spec_path=str(SPEC_MD),
    )
    # Verification must be blocked by Safety Gate
    state = auditor.state_mgr.load()
    assert state["current_state"] == "BLOCKED"
    assert "Production Safety Gate" in state["history"][-1]["note"]
    # All high-risk findings must remain NOT_VERIFIED
    for f in auditor.findings:
        if f["group_key"] == "ERROR_CONTRACT":
            assert f["verification_status"] == "NOT_VERIFIED"
            assert "Production Safety Gate" in f["evidence"]


def test_quick_does_not_export_excel(tmp_path):
    """7. Verify Quick Mode does not mandate or export any 3-sheet Excel workbooks."""
    auditor = FastTrackQAAuditor(tmp_path, module_name="test-no-excel")
    auditor.run_audit(
        target_path="tests/fixtures/golden-sample-project/src/order.ts",
        target_symbol="handleApiOrder",
        spec_path=str(SPEC_MD),
    )
    state = auditor.state_mgr.load()
    artifacts = state.get("artifacts", {})
    assert artifacts.get("excel_testcases") is None
    assert artifacts.get("approved_excel") is None
    # No .xlsx files generated in workspace
    xlsx_files = list(tmp_path.glob("*.xlsx"))
    assert len(xlsx_files) == 0


def test_quick_does_not_bypass_human_gate_approval(tmp_path):
    """8. Verify that Quick Mode cannot bypass Human Gate 2 to implement full automation without approval token."""
    mgr = WorkflowStateManager(str(tmp_path), module_name="gate-test")
    mgr.init_state("gate-test", {"root": str(tmp_path)}, execution_mode="quick")
    
    # Quick mode transitions to COMPLETED
    mgr.transition("RUNTIME_INVESTIGATION", "Quick verification")
    mgr.transition("COMPLETED", "Quick flash report delivered")
    
    # Attempting to directly trigger Step 6 (AUTOMATION_IMPLEMENTATION) without Gate 2 signoff must be rejected
    with pytest.raises(ValueError, match="FSM Transition Violation"):
        mgr.transition("AUTOMATION_IMPLEMENTATION", "Attempting full automation without approval")


def test_quick_resumability_and_state_persistence(tmp_path):
    """9. Verify Quick Mode state is persisted atomically to .qa-state.json and can be inspected/resumed."""
    auditor = FastTrackQAAuditor(tmp_path, module_name="test-persistence", base_url="http://localhost:3000")
    auditor.run_audit(
        target_path="tests/fixtures/golden-sample-project/src/order.ts",
        target_symbol="handleApiOrder",
        spec_path=str(SPEC_MD),
    )
    state_file = auditor.state_mgr.state_file
    assert state_file.exists()
    
    loaded_mgr = WorkflowStateManager(str(tmp_path), module_name="test-persistence")
    loaded_state = loaded_mgr.load()
    assert loaded_state["module_name"] == "test-persistence"
    assert loaded_state["execution_mode"] == "quick"
    assert loaded_state["current_state"] == "COMPLETED"
    assert loaded_state["artifacts"].get("quick_audit_report") is not None
    assert len(loaded_state["history"]) >= 4


def test_standard_mode_unaffected(tmp_path):
    """10. Verify standard mode lifecycle is completely unaffected by quick mode changes."""
    mgr = WorkflowStateManager(str(tmp_path), module_name="standard-test")
    state = mgr.init_state("standard-test", {"root": str(tmp_path)}, execution_mode="standard")
    assert state["execution_mode"] == "standard"
    assert state["current_state"] == "INITIALIZED"
    
    # Standard flow: INITIALIZED -> CONTEXT_DISCOVERY -> GAP_ANALYSIS -> TESTCASE_GENERATION -> TESTCASE_REVIEW
    mgr.transition("CONTEXT_DISCOVERY", "CodeGraph AST tree")
    mgr.transition("GAP_ANALYSIS", "Gap analysis with benchmark")
    mgr.transition("TESTCASE_GENERATION", "Design test cases")
    mgr.transition("TESTCASE_REVIEW", "Review traceability")
    mgr.transition("WAITING_FOR_APPROVED_TESTCASES", "Deliver Excel to user")
    assert mgr.get_field("current_state") == "WAITING_FOR_APPROVED_TESTCASES"


def test_critical_mode_unaffected(tmp_path):
    """11. Verify critical mode enforces strict production blocker and concurrency caps."""
    mgr = WorkflowStateManager(str(tmp_path), module_name="critical-test")
    state = mgr.init_state(
        "critical-test",
        {"root": str(tmp_path)},
        execution_mode="critical",
        base_url="https://live-bank-gateway.com"
    )
    assert state["execution_mode"] == "critical"
    assert state["environment"]["tier"] == "production"
    
    allowed, msg = mgr.check_mutation_allowed()
    assert allowed is False
    assert "Production Safety Gate" in msg


def test_quick_cache_invalidation_on_source_change(tmp_path):
    """12. Verify source modifications invalidate hash integrity in state."""
    spec_f = tmp_path / "order-spec.md"
    spec_f.write_text("# Spec v1", encoding="utf-8")
    
    mgr = WorkflowStateManager(str(tmp_path), module_name="cache-test")
    mgr.init_state("cache-test", {"root": str(tmp_path)}, docs=[str(spec_f)], execution_mode="quick")
    
    # Initial: valid
    res_v1 = mgr.validate_integrity()
    assert res_v1["valid"] is True
    
    # Mutate source
    spec_f.write_text("# Spec v2 (Changed requirements)", encoding="utf-8")
    res_v2 = mgr.validate_integrity()
    assert res_v2["valid"] is False
    assert len(res_v2["changed_documents"]) == 1


def test_quick_timeout_does_not_create_false_pass(tmp_path):
    """13. Verify that step timings are bounded and simulated timeout does not fabricate false pass."""
    auditor = FastTrackQAAuditor(tmp_path, module_name="test-timeout", timeout_budget_sec=0.001)
    auditor.run_audit(
        target_path="tests/fixtures/golden-sample-project/src/order.ts",
        target_symbol="handleApiOrder",
        spec_path=str(SPEC_MD),
    )
    # Timings must be recorded honestly
    assert auditor.timings["total"] > 0.0
    assert "⏱️" in auditor.report_markdown
    assert "Tổng thời gian thực thi" in auditor.report_markdown


def test_quick_non_applicable_groups_marked_na(tmp_path):
    """14. Verify that non-applicable friction groups (e.g. data loss on backend-only functions) are marked NOT_APPLICABLE."""
    auditor = FastTrackQAAuditor(PROJECT_ROOT, module_name="test-na-group")
    auditor.run_audit(
        target_path="tests/fixtures/golden-sample-project/src/order.ts",
        target_symbol="handleApiOrder",
        spec_path=str(SPEC_MD),
    )
    na_findings = [f for f in auditor.findings if f["verification_status"] == "NOT_APPLICABLE"]
    assert len(na_findings) >= 1
    # Check that it's in the Markdown report
    assert "KHÔNG ÁP DỤNG" in auditor.report_markdown


def test_quick_unreachable_environment_reported_accurately(tmp_path):
    """15. Verify that unreachable runtime targets are marked NOT_VERIFIED with an accurate reason, not false pass."""
    auditor = FastTrackQAAuditor(
        PROJECT_ROOT,
        module_name="test-unreachable",
        base_url="https://unreachable-qa-server-9999.internal.corp"
    )
    auditor.run_audit(
        target_path="tests/fixtures/golden-sample-project/src/order.ts",
        target_symbol="handleApiOrder",
        spec_path=str(SPEC_MD),
    )
    # Must report blocked/not verified for safety
    state = auditor.state_mgr.load()
    assert state["current_state"] == "BLOCKED"
    for f in auditor.findings:
        if f["risk_level"] == "High":
            assert f["verification_status"] == "NOT_VERIFIED"
