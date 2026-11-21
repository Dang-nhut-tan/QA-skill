"""
tests/test_human_gate_regression.py
Regression tests for Human Approval Gate (Gate 2), control field protection,
and recursive secret redaction in state files and backup (.bak) files.
"""

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
import pytest
from scripts.state_manager import WorkflowStateManager, STATE_FILE_NAME


def _sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


@pytest.fixture
def mock_workspace(tmp_path):
    ws = tmp_path / "workspace"
    ws.mkdir(parents=True, exist_ok=True)
    return ws


@pytest.fixture
def sample_workbook(mock_workspace):
    # Create a minimal mock xlsx file
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Test Cases"
    ws.append(["Test Case ID", "Module", "Name", "Severity", "Automation Ready", "Status"])
    ws.append(["TC-001", "Auth", "Login success", "Chặn", "Yes", "Pending"])
    wb_path = mock_workspace / "auth-testcases.xlsx"
    wb.save(wb_path)
    return wb_path


def _reach_waiting_for_approval(mgr, workbook_path):
    mgr.init_state("auth", {"cwd": str(mgr.workspace_root)})
    mgr.transition("GAP_ANALYSIS")
    mgr.transition("TESTCASE_GENERATION")
    mgr.transition("WAITING_FOR_APPROVED_TESTCASES", metadata={"artifacts": {"approved_excel": str(workbook_path)}})


def test_human_gate_missing_approval_blocks_transition(mock_workspace, sample_workbook):
    """Case 1: No approval object or approval token -> transition to AUTOMATION_IMPLEMENTATION blocked."""
    mgr = WorkflowStateManager(str(mock_workspace), module_name="auth")
    _reach_waiting_for_approval(mgr, sample_workbook)

    with pytest.raises((ValueError, PermissionError)) as excinfo:
        mgr.transition("AUTOMATION_IMPLEMENTATION")
    assert "Human Gate" in str(excinfo.value) or "approval" in str(excinfo.value).lower()


def test_human_gate_approved_false_blocks_transition(mock_workspace, sample_workbook):
    """Case 2: approved=false -> transition blocked."""
    mgr = WorkflowStateManager(str(mock_workspace), module_name="auth")
    _reach_waiting_for_approval(mgr, sample_workbook)
    
    mgr.record_human_approval(
        approved=False,
        approved_by="human",
        workbook_path=str(sample_workbook)
    )

    with pytest.raises((ValueError, PermissionError)) as excinfo:
        mgr.transition("AUTOMATION_IMPLEMENTATION")
    assert "approved" in str(excinfo.value).lower() or "gate" in str(excinfo.value).lower()


def test_human_gate_approved_by_agent_blocks_transition(mock_workspace, sample_workbook):
    """Case 3: approved_by='agent' -> transition blocked."""
    mgr = WorkflowStateManager(str(mock_workspace), module_name="auth")
    _reach_waiting_for_approval(mgr, sample_workbook)

    mgr.record_human_approval(
        approved=True,
        approved_by="agent",
        workbook_path=str(sample_workbook)
    )

    with pytest.raises((ValueError, PermissionError)) as excinfo:
        mgr.transition("AUTOMATION_IMPLEMENTATION")
    assert "human" in str(excinfo.value).lower() or "agent" in str(excinfo.value).lower()


def test_human_gate_workbook_missing_blocks_transition(mock_workspace):
    """Case 4: Workbook file does not exist on disk -> transition blocked."""
    non_existent = mock_workspace / "ghost-testcases.xlsx"
    mgr = WorkflowStateManager(str(mock_workspace), module_name="auth")
    _reach_waiting_for_approval(mgr, non_existent)

    with pytest.raises((ValueError, PermissionError, FileNotFoundError)) as excinfo:
        mgr.record_human_approval(
            approved=True,
            approved_by="human",
            workbook_path=str(non_existent)
        )
        mgr.transition("AUTOMATION_IMPLEMENTATION")
    assert "workbook" in str(excinfo.value).lower() or "exist" in str(excinfo.value).lower()


def test_human_gate_hash_mismatch_blocks_transition(mock_workspace, sample_workbook):
    """Case 5: Workbook hash mismatch -> transition blocked."""
    mgr = WorkflowStateManager(str(mock_workspace), module_name="auth")
    _reach_waiting_for_approval(mgr, sample_workbook)

    # Force a mismatched hash
    state = mgr.load()
    state["approval"] = {
        "approved": True,
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "approved_by": "human",
        "artifact_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" # empty string hash
    }
    state["_version"] = state.get("_version", 0)
    mgr.save(state)

    with pytest.raises((ValueError, PermissionError)) as excinfo:
        mgr.transition("AUTOMATION_IMPLEMENTATION")
    assert "hash" in str(excinfo.value).lower() or "mismatch" in str(excinfo.value).lower()


def test_human_gate_workbook_altered_after_approval_blocks_transition(mock_workspace, sample_workbook):
    """Case 6: Workbook modified after approval -> hash invalidation blocks transition."""
    mgr = WorkflowStateManager(str(mock_workspace), module_name="auth")
    _reach_waiting_for_approval(mgr, sample_workbook)

    mgr.record_human_approval(
        approved=True,
        approved_by="human",
        workbook_path=str(sample_workbook)
    )

    # Modify workbook content on disk after approval
    with open(sample_workbook, "ab") as f:
        f.write(b"\nTampered byte content")

    with pytest.raises((ValueError, PermissionError)) as excinfo:
        mgr.transition("AUTOMATION_IMPLEMENTATION")
    assert "hash" in str(excinfo.value).lower() or "tamper" in str(excinfo.value).lower() or "mismatch" in str(excinfo.value).lower()


def test_human_gate_valid_approval_and_matching_hash_allows_transition(mock_workspace, sample_workbook):
    """Case 7: Valid approval object with matching hash -> transition permitted."""
    mgr = WorkflowStateManager(str(mock_workspace), module_name="auth")
    _reach_waiting_for_approval(mgr, sample_workbook)

    mgr.record_human_approval(
        approved=True,
        approved_by="human",
        workbook_path=str(sample_workbook)
    )

    s = mgr.transition("AUTOMATION_IMPLEMENTATION")
    assert s["current_state"] == "AUTOMATION_IMPLEMENTATION"
    assert s["approval"]["approved"] is True
    assert s["approval"]["approved_by"] == "human"
    assert s["approval"]["artifact_hash"] == _sha256(sample_workbook)


def test_control_field_current_state_mutation_blocked(mock_workspace):
    """Case 8: set_field('current_state') must be blocked with PermissionError."""
    mgr = WorkflowStateManager(str(mock_workspace), module_name="auth")
    mgr.init_state("auth", {"cwd": str(mock_workspace)})

    with pytest.raises(PermissionError) as excinfo:
        mgr.set_field("current_state", "AUTOMATION_IMPLEMENTATION")
    assert "current_state" in str(excinfo.value) or "protected" in str(excinfo.value).lower()


def test_control_field_approval_mutation_blocked(mock_workspace):
    """Case 9: set_field('approval') must be blocked with PermissionError."""
    mgr = WorkflowStateManager(str(mock_workspace), module_name="auth")
    mgr.init_state("auth", {"cwd": str(mock_workspace)})

    with pytest.raises(PermissionError) as excinfo:
        mgr.set_field("approval", {"approved": True})
    assert "approval" in str(excinfo.value) or "protected" in str(excinfo.value).lower()


def test_control_field_other_protected_fields_mutation_blocked(mock_workspace):
    """Case 10: set_field on quality_gates, environment.tier, environment.allowlist_verified, history blocked."""
    mgr = WorkflowStateManager(str(mock_workspace), module_name="auth")
    mgr.init_state("auth", {"cwd": str(mock_workspace)})

    protected_targets = [
        ("quality_gates", {}),
        ("environment.tier", "local"),
        ("environment.allowlist_verified", True),
        ("history", []),
    ]

    for field, val in protected_targets:
        with pytest.raises(PermissionError):
            mgr.set_field(field, val)


def test_metadata_update_cannot_bypass_human_gate(mock_workspace, sample_workbook):
    """Case 10b: Metadata update inside transition cannot bypass Human Gate."""
    mgr = WorkflowStateManager(str(mock_workspace), module_name="auth")
    _reach_waiting_for_approval(mgr, sample_workbook)

    # Attempt to bypass via transition metadata
    fake_approval = {
        "approved": True,
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "approved_by": "human",
        "artifact_hash": "fake_hash"
    }

    with pytest.raises((ValueError, PermissionError)):
        mgr.transition(
            "AUTOMATION_IMPLEMENTATION",
            metadata={"approval": fake_approval}
        )


def test_recursive_redaction_in_state_and_backup(mock_workspace):
    """Task 4: State and .bak file must recursively redact secrets before persisting to disk."""
    mgr = WorkflowStateManager(str(mock_workspace), module_name="secret_test")
    mgr.init_state("secret_test", {
        "cwd": str(mock_workspace),
        "base_url": "http://user_admin:dummy_pass_999@test.company.internal/api"
    })

    # Directly attach sensitive structures to state tree as requested by Task 4:
    # 1. Bearer token in header
    # 2. Password in basic auth / URL / query
    # 3. API key in metadata
    # 4. Secret in note of history
    state = mgr.load()
    state["headers"] = {
        "Authorization": "Bearer dummy_bearer_token_abc123"
    }
    state["metadata"] = {
        "api_key": "dummy_api_key_xyz987"
    }
    state["credentials"] = {
        "db_secret": "dummy_db_password_456",
        "session": "dummy_session_id_789"
    }
    state["callback_url"] = "https://auth.internal/callback?code=dummy_oauth_code_000&state=normal"
    state["history"].append({
        "state": "CONTEXT_DISCOVERY",
        "note": "Initial discovery with ghp_dummy_github_token_12345"
    })

    mgr.save(state)

    state_file = mgr.state_file
    bak_file = state_file.with_name(f"{state_file.name}.bak")

    assert state_file.exists(), "State file must exist"
    assert bak_file.exists(), "Backup (.bak) file must exist"

    state_raw = state_file.read_text(encoding="utf-8")
    bak_raw = bak_file.read_text(encoding="utf-8")

    forbidden_literals = [
        "dummy_pass_999",
        "dummy_bearer_token_abc123",
        "dummy_api_key_xyz987",
        "dummy_db_password_456",
        "dummy_session_id_789",
        "dummy_github_token_12345",
        "dummy_oauth_code_000"
    ]

    for secret in forbidden_literals:
        assert secret not in state_raw, f"Secret '{secret}' leaked in raw state file!"
        assert secret not in bak_raw, f"Secret '{secret}' leaked in backup (.bak) file!"

    assert "***REDACTED***" in state_raw
    assert "***REDACTED***" in bak_raw

    # Verify that loading state succeeds and returns sanitized dictionary
    loaded = mgr.load()
    assert loaded["current_state"] == "INITIALIZED"
    assert loaded["headers"]["Authorization"] == "Bearer ***REDACTED***"
    assert loaded["metadata"]["api_key"] == "***REDACTED***"
