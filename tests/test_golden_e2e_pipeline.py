"""Golden-project integration test using real filesystem, discovery, Excel, and RTM engines."""

from pathlib import Path

from openpyxl import load_workbook

from scripts.codegraph_discovery import MethodDiscoveryEngine
from scripts.export_testcases import export_to_excel
from scripts.state_manager import WorkflowStateManager
from scripts.traceability_validator import validate_traceability


FIXTURE = Path(__file__).parent / "fixtures" / "golden-sample-project"


def test_golden_pipeline_without_mocks(tmp_path):
    spec = FIXTURE / "spec.md"
    assert "SPEC-AUTH-001" in spec.read_text(encoding="utf-8")

    state = WorkflowStateManager(tmp_path, module_name="golden-login")
    initialized = state.init_state(
        "golden-login",
        {"root": str(FIXTURE), "source": "golden-project"},
        [str(spec)],
    )
    assert initialized["current_state"] == "INITIALIZED"

    engine = MethodDiscoveryEngine(FIXTURE)
    discovery = engine.discover_and_evaluate("login")
    engine.close()
    assert discovery["status"] == "FOUND"
    assert discovery["candidate"]["name"] == "login"
    assert discovery["discovery_source"] == "fallback_ast_scan"

    payload = {
        "module": "Golden Login",
        "requirements": ["SPEC-AUTH-001"],
        "testcases": [{
            "id": "TC-AUTH-001",
            "name": "Đăng nhập bằng thông tin hợp lệ",
            "severity": "Chặn",
            "priority": "P0",
            "preconditions": "Tài khoản đang hoạt động",
            "test_data": "Tài khoản kiểm thử hợp lệ",
            "steps": "1. Mở màn hình đăng nhập\n2. Nhập thông tin hợp lệ\n3. Bấm Đăng nhập",
            "expected_result": "Màn hình bảng điều khiển được hiển thị",
            "requirement_ref": "SPEC-AUTH-001",
            "automation_ready": "Yes",
            "code_reference": f"{discovery['candidate']['file_path']}#{discovery['candidate']['name']}",
        }],
    }

    audit = validate_traceability(payload)
    assert audit["valid"] is True
    assert audit["metrics"]["coverage_percentage"] == 100.0

    workbook = tmp_path / "golden-login-testcases.xlsx"
    export_to_excel(payload, workbook)
    assert workbook.exists() and workbook.stat().st_size > 0
    loaded = load_workbook(workbook, read_only=True)
    assert "Test Cases" in loaded.sheetnames
    loaded.close()
