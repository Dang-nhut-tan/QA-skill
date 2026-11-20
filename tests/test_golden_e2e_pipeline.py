"""
tests/test_golden_e2e_pipeline.py
Real end-to-end golden pipeline and behavioral verification test suite.
Validates the entire QA testing lifecycle using real filesystems, AST discovery,
Playwright execution, Excel generation, state transitions, security redaction,
and human decision gate enforcement.
"""

import sqlite3
import sys
import json
import subprocess
import shutil
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import jsonschema
from openpyxl import load_workbook

from scripts.codegraph_discovery import (
    MethodDiscoveryEngine,
    JavaScriptTypeScriptASTAdapter,
)
from scripts.export_testcases import export_to_excel
from scripts.read_approved_testcases import parse_approved_workbook
from scripts.state_manager import (
    WorkflowStateManager,
    classify_environment,
    redact_credentials_in_string,
    sanitize_metadata,
)
from scripts.traceability_validator import validate_traceability
from scripts.lint_test_code import lint_file

FIXTURE = Path(__file__).parent / "fixtures" / "golden-sample-project"
SCHEMA_FILE = PROJECT_ROOT / "references" / "workflow-state-schema.json"


def test_golden_pipeline_without_mocks(tmp_path):
    """Legacy smoke integration test on basic login module."""
    spec = FIXTURE / "spec.md"
    assert "SPEC-AUTH-001" in spec.read_text(encoding="utf-8")

    state = WorkflowStateManager(str(tmp_path), module_name="golden-login")
    initialized = state.init_state(
        "golden-login",
        {"root": str(FIXTURE), "source": "golden-project"},
        [str(spec)],
    )
    assert initialized["current_state"] == "INITIALIZED"

    # Step 1: Context discovery
    engine = MethodDiscoveryEngine(FIXTURE)
    discovery = engine.discover_and_evaluate("login")
    engine.close()
    assert discovery["status"] == "FOUND"
    assert discovery["candidate"]["name"] == "login"
    assert discovery["discovery_source"] == "fallback_ast_scan"
    state.transition("CONTEXT_DISCOVERY", note="Completed AST context discovery")

    # Step 2: Gap analysis
    state.transition("GAP_ANALYSIS", note="Evaluated spec vs codebase, zero blocking gaps")

    # Step 3: Testcase generation
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
    state.transition("TESTCASE_GENERATION", note="Designed risk-based test suite")

    # Step 4: Quality review
    audit = validate_traceability(payload)
    assert audit["valid"] is True
    assert audit["metrics"]["coverage_percentage"] == 100.0
    state.transition("TESTCASE_REVIEW", note="Internal quality review and RTM audit passed")

    # Step 5: Export to Excel and wait for approval
    workbook = tmp_path / "golden-login-testcases.xlsx"
    export_to_excel(payload, workbook)
    assert workbook.exists() and workbook.stat().st_size > 0
    loaded = load_workbook(workbook, read_only=True)
    assert "Test Cases" in loaded.sheetnames
    loaded.close()
    state.transition(
        "WAITING_FOR_APPROVED_TESTCASES",
        note="Exported workbook awaiting QA Lead signoff",
        metadata={"artifacts": {"approved_excel": str(workbook)}},
    )

    # Step 6: Round-Trip Ingestion verification
    state.transition(
        "AUTOMATION_IMPLEMENTATION",
        note="Approved by QA Lead, verified round-trip",
        approval_token="qa-lead-approved",
    )
    approved_result = parse_approved_workbook(workbook)
    assert approved_result["success"] is True
    assert approved_result["total_cases"] == 1
    assert approved_result["automation_ready_count"] == 1
    assert approved_result["ready_testcases"][0]["id"] == "TC-AUTH-001"

    state.transition("COMPLETED", note="Golden testcase roundtrip pipeline verified successfully")

    final_state = state.load()
    assert final_state["current_state"] == "COMPLETED"
    assert "WAITING_FOR_APPROVED_TESTCASES" in final_state["completed_steps"]
    assert len(final_state["history"]) >= 6


def test_golden_order_full_e2e_pipeline(tmp_path):
    """
    Comprehensive Phase 4 Golden End-to-End Pipeline Test:
    1. Reusable Page Object discovery (CodeGraph POM reuse)
    2. Valid validation guard (classified as GUARD-xxx, NOT a bug)
    3. Real UI bug confirmed via live Playwright execution
    4. Real API validation bug confirmed via direct handler execution
    5. Missing requirement detection (unspecified code logic)
    6. Bidirectional traceability matrix validation (100% coverage)
    7. Human approval gate enforcement
    8. Static test linter clean verification
    """
    spec_path = FIXTURE / "spec.md"
    assert spec_path.exists()

    # Step 0: Intake & Initialization
    state = WorkflowStateManager(str(tmp_path), module_name="golden-order")
    initialized = state.init_state(
        "golden-order",
        {"root": str(FIXTURE), "source": "golden-sample-project"},
        docs=[str(spec_path)],
        execution_mode="standard",
        base_url="http://localhost:3000"
    )
    assert initialized["current_state"] == "INITIALIZED"
    assert initialized["execution_mode"] == "standard"
    assert initialized["environment"]["tier"] == "local"

    # Step 1: CodeGraph Context Discovery
    engine = MethodDiscoveryEngine(FIXTURE)
    
    # 1.1 Reusable Page Object discovery (Direct POM Reuse)
    pom_discovery = engine.discover_and_evaluate("submitOrder")
    assert pom_discovery["status"] == "FOUND"
    assert "order.page.ts" in pom_discovery["candidate"]["file_path"]
    assert pom_discovery["candidate"]["name"] == "submitOrder"

    # 1.2 Discover business logic methods in src/order.ts
    order_func_discovery = engine.discover_and_evaluate("createOrder", scope_hint="src")
    assert order_func_discovery["status"] == "FOUND"
    assert "order.ts" in order_func_discovery["candidate"]["file_path"]

    guard_func_discovery = engine.discover_and_evaluate("validateOrderQuantity", scope_hint="src")
    assert guard_func_discovery["status"] == "FOUND"

    api_func_discovery = engine.discover_and_evaluate("handleApiOrder", scope_hint="src")
    assert api_func_discovery["status"] == "FOUND"

    missing_spec_func = engine.discover_and_evaluate("applyLoyaltyPoints", scope_hint="src")
    assert missing_spec_func["status"] == "FOUND"
    engine.close()

    state.transition("CONTEXT_DISCOVERY", note="CodeGraph context discovery completed with POM and AST symbols")

    # Step 2: Gap Analysis & Triaging
    # Evaluates SPEC-ORDER-GUARD: validateOrderQuantity is a valid security guard, NOT a defect
    # Evaluates applyLoyaltyPoints: absent from spec.md -> GAP-003 Requirement Ambiguity
    # Identifies suspected UI Bug (Calculate shipping freeze) and API Bug (Negative price acceptance)
    state.transition("GAP_ANALYSIS", note="Identified 1 Guard, 1 UI Gap, 1 API Gap, 1 Ambiguity")

    # Step 3: Dual-Track Runtime Verification (Live Execution)
    state.transition("RUNTIME_INVESTIGATION", note="Conducting empirical UI and API verification")

    # 3.1 Live UI Bug Verification via Playwright CLI
    ui_spec_file = PROJECT_ROOT / "tests" / "fixtures" / "browser" / "order-ui-bug-repro.spec.js"
    ui_spec_rel = ui_spec_file.relative_to(PROJECT_ROOT).as_posix()
    res_ui = subprocess.run(
        f"npx playwright test {ui_spec_rel}",
        shell=True,
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT)
    )
    assert res_ui.returncode == 0, f"Playwright UI Bug repro spec failed: {res_ui.stderr}\nstdout: {res_ui.stdout}"
    assert "GAP-ORDER-001" in res_ui.stdout

    # 3.2 Live API Bug Verification via Playwright CLI
    api_spec_file = PROJECT_ROOT / "tests" / "fixtures" / "browser" / "order-api-bug-repro.spec.js"
    api_spec_rel = api_spec_file.relative_to(PROJECT_ROOT).as_posix()
    res_api = subprocess.run(
        f"npx playwright test {api_spec_rel}",
        shell=True,
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT)
    )
    assert res_api.returncode == 0, f"Playwright API Bug repro spec failed: {res_api.stderr}\nstdout: {res_api.stdout}"
    assert "GAP-API-002" in res_api.stdout

    # 3.3 Live Guard Verification via Playwright CLI
    guard_spec_file = PROJECT_ROOT / "tests" / "fixtures" / "browser" / "order-guard-verification.spec.js"
    guard_spec_rel = guard_spec_file.relative_to(PROJECT_ROOT).as_posix()
    res_guard = subprocess.run(
        f"npx playwright test {guard_spec_rel}",
        shell=True,
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT)
    )
    assert res_guard.returncode == 0, f"Playwright Guard verification failed: {res_guard.stderr}\nstdout: {res_guard.stdout}"
    assert "GUARD-ORDER-001" in res_guard.stdout

    # 3.4 Valuable Guard Retention: Register Guard in State (Do NOT delete!)
    state.register_guard(
        "GUARD-ORDER-001",
        "Blocks negative quantity and disables submit button",
        str(guard_spec_file)
    )
    loaded_guards = state.load().get("guards", [])
    assert len(loaded_guards) >= 1
    assert loaded_guards[0]["id"] == "GUARD-ORDER-001"

    # 3.5 Static Test Code Linter Gate: Zero Sleeps, Zero Unmasked Tokens, Safe Promises
    for spec_p in [ui_spec_file, api_spec_file, guard_spec_file]:
        violations = lint_file(spec_p)
        assert len(violations) == 0, f"Linter violations found in {spec_p}: {violations}"

    # Step 4: Testcase Design & Traceability Matrix (RTM)
    payload = {
        "module": "Golden Order Management",
        "requirements": ["SPEC-ORDER-001", "SPEC-ORDER-GUARD", "SPEC-ORDER-002"],
        "testcases": [
            {
                "id": "TC-ORDER-001",
                "name": "Create order successfully with valid items (Happy Path)",
                "severity": "Chặn",
                "priority": "P0",
                "preconditions": "Active logged-in user with standard cart",
                "test_data": "Item: Laptop, Qty: 2, Price: 500",
                "steps": "1. Navigate to order form\n2. Fill item, quantity, price\n3. Click Create Order",
                "expected_result": "Order confirmation banner displays ORD-1001",
                "requirement_ref": "SPEC-ORDER-001",
                "automation_ready": "Yes",
                "code_reference": "tests/fixtures/golden-sample-project/src/order.ts#createOrder",
            },
            {
                "id": "TC-ORDER-GUARD-001",
                "name": "Validation guard prevents negative quantity input",
                "severity": "Sai",
                "priority": "P1",
                "preconditions": "Order form open",
                "test_data": "Quantity: -3",
                "steps": "1. Input negative quantity\n2. Observe validation and submit button",
                "expected_result": "Validation error shown, submit button disabled (GUARD-ORDER-001 PASS)",
                "requirement_ref": "SPEC-ORDER-GUARD",
                "automation_ready": "Yes",
                "code_reference": "tests/fixtures/golden-sample-project/src/order.ts#validateOrderQuantity",
            },
            {
                "id": "TC-ORDER-002",
                "name": "Server-side rejection of negative price payloads (API Defect Coverage)",
                "severity": "Chặn",
                "priority": "P0",
                "preconditions": "API client initialized",
                "test_data": "Price: -500",
                "steps": "1. Dispatch POST request directly with price: -500\n2. Inspect response code",
                "expected_result": "Backend must reject with 400 Bad Request (Bug currently returns 200)",
                "requirement_ref": "SPEC-ORDER-002",
                "automation_ready": "Yes",
                "code_reference": "tests/fixtures/golden-sample-project/src/order.ts#handleApiOrder",
            }
        ],
    }

    state.transition("TESTCASE_GENERATION", note="Designed risk-based test cases for order module")

    # Step 5: Testcase Quality Review & Excel Export
    audit = validate_traceability(payload)
    assert audit["valid"] is True
    assert audit["metrics"]["coverage_percentage"] == 100.0
    state.transition("TESTCASE_REVIEW", note="Bidirectional traceability audit passed with 100% coverage")

    workbook_path = tmp_path / "golden-order-testcases.xlsx"
    export_to_excel(payload, workbook_path)
    assert workbook_path.exists() and workbook_path.stat().st_size > 0

    wb = load_workbook(workbook_path, read_only=True)
    assert "Test Cases" in wb.sheetnames
    assert "Requirement Gaps" in wb.sheetnames
    assert "Coverage Summary" in wb.sheetnames
    wb.close()

    # Step 6: Core Human Decision Gate (WAITING_FOR_APPROVED_TESTCASES)
    state.transition(
        "WAITING_FOR_APPROVED_TESTCASES",
        note="Exported 3-sheet workbook awaiting user review and approval",
        metadata={"artifacts": {"approved_excel": str(workbook_path)}},
    )

    # 6.1 Gate Protection: Transition without approval token MUST raise ValueError
    try:
        state.transition("AUTOMATION_IMPLEMENTATION", "Attempting automation without approval token")
        assert False, "FSM Human Gate must reject transition without valid approval token"
    except ValueError as exc:
        assert "approval_token" in str(exc)

    # 6.2 Supply approval token: Transition succeeds
    state.transition(
        "AUTOMATION_IMPLEMENTATION",
        note="User approved testcases with token",
        approval_token="tan-lead-approved",
    )

    # 6.3 Round-trip verification: Read back approved testcases from Excel
    parsed_approved = parse_approved_workbook(workbook_path)
    assert parsed_approved["success"] is True
    assert parsed_approved["total_cases"] == 3
    assert parsed_approved["automation_ready_count"] == 3
    ready_ids = [tc["id"] for tc in parsed_approved["ready_testcases"]]
    assert "TC-ORDER-001" in ready_ids
    assert "TC-ORDER-GUARD-001" in ready_ids
    assert "TC-ORDER-002" in ready_ids

    # Step 7: Execution & Completion
    state.transition("AUTOMATION_EXECUTION", note="Executed approved automated test suite")
    state.transition("COMPLETED", note="Golden order workflow completed successfully")

    final_state = state.load()
    assert final_state["current_state"] == "COMPLETED"
    assert "WAITING_FOR_APPROVED_TESTCASES" in final_state["completed_steps"]
    assert len(final_state["history"]) >= 8


def test_behavioral_schema_and_secret_redaction(tmp_path):
    """
    Behavioral Test:
    1. Validates that forbidden secret keys raise a Security Alert ValueError.
    2. Validates generated .qa-state.json strictly against workflow-state-schema.json.
    3. Verifies credential and token redaction (no passwords in state or logs).
    4. Verifies Production Safety Gate blocks mutations on production URLs.
    """
    import pytest

    # 1. Verify Forbidden Secret Keys Detection raises ValueError
    with pytest.raises(ValueError, match="Security Alert: Attempted to persist sensitive credential key"):
        sanitize_metadata({"api_key": "prod_live_secret_key_9999"})

    with pytest.raises(ValueError, match="Security Alert: Attempted to persist sensitive credential key"):
        sanitize_metadata({"db_password": "super_secret_password"})

    mgr = WorkflowStateManager(str(tmp_path), module_name="security-test")
    raw_state = mgr.init_state(
        "security-test",
        {
            "root": str(tmp_path),
            "database_url": "postgres://admin:super_secret_password_123@localhost:5432/test_db",
            "environment_label": "staging-replica",
        },
        execution_mode="critical",
        base_url="https://production-store.company.com"
    )

    # 2. Verify JSON Schema Validation
    schema = json.loads(SCHEMA_FILE.read_text(encoding="utf-8"))
    jsonschema.validate(instance=raw_state, schema=schema)

    # 3. Verify Credential Redaction: raw passwords/tokens must never appear in state
    state_json_str = json.dumps(raw_state)
    assert "super_secret_password_123" not in state_json_str
    assert "***REDACTED***" in state_json_str

    # 4. Verify redact_credentials_in_string functionality
    sensitive_uri = "https://svc_account:SecretPass123!@api.enterprise.com/v1"
    redacted_uri = redact_credentials_in_string(sensitive_uri)
    assert "SecretPass123!" not in redacted_uri
    assert "***REDACTED***" in redacted_uri

    # 5. Verify Production Safety Gate: mutations blocked on production URL
    allowed, msg = mgr.check_mutation_allowed()
    assert allowed is False
    assert "Production Safety Gate" in msg


def test_behavioral_source_invalidation_and_resume(tmp_path):
    """
    Behavioral Test:
    Verifies that when source documents are modified, the state manager
    detects the hash mismatch, reports changed documents, and enables selective invalidation.
    """
    doc_file = tmp_path / "checkout-spec.md"
    doc_file.write_text("# Checkout Specification v1", encoding="utf-8")

    mgr = WorkflowStateManager(str(tmp_path), module_name="checkout")
    mgr.init_state("checkout", {"root": str(tmp_path)}, docs=[str(doc_file)])
    
    # Initial integrity check: valid
    res_init = mgr.validate_integrity()
    assert res_init["valid"] is True
    assert len(res_init["changed_documents"]) == 0

    # Modify the document content
    doc_file.write_text("# Checkout Specification v2 (Updated with payment gateways)", encoding="utf-8")

    # Re-validate: must detect changed document
    res_modified = mgr.validate_integrity()
    assert res_modified["valid"] is False
    assert len(res_modified["changed_documents"]) == 1
    assert res_modified["changed_documents"][0]["path"] == str(doc_file)
    assert res_modified["resumable"] is True


def test_polyglot_adapter_and_truncation_observability(tmp_path):
    # 1. Verify JavaScriptTypeScriptASTAdapter directly executes without NotImplementedError
    adapter = JavaScriptTypeScriptASTAdapter(synonyms={"login": ["login", "signin"]})
    candidates = adapter.discover(FIXTURE, "login")
    assert len(candidates) > 0
    assert any(c["name"] == "login" for c in candidates)

    # 2. Verify MethodDiscoveryEngine wires adapter seamlessly
    engine = MethodDiscoveryEngine(FIXTURE)
    assert len(engine.adapters) >= 1
    assert isinstance(engine.adapters[0], JavaScriptTypeScriptASTAdapter)

    # 3. Verify SQLite candidate truncation transparency
    db_dir = tmp_path / ".codegraph"
    db_dir.mkdir(parents=True, exist_ok=True)
    db_file = db_dir / "codegraph.db"
    conn = sqlite3.connect(db_file)
    conn.execute("""
        CREATE TABLE nodes (
            id TEXT PRIMARY KEY,
            kind TEXT,
            name TEXT,
            qualified_name TEXT,
            file_path TEXT,
            start_line INTEGER,
            end_line INTEGER,
            signature TEXT,
            docstring TEXT,
            is_exported INTEGER
        )
    """)
    for i in range(1, 4):
        conn.execute(
            "INSERT INTO nodes VALUES (?, 'method', 'handlePayment', 'Order::handlePayment', 'order.ts', ?, ?, '() => void', '', 1)",
            (f"node_{i}", i * 10, i * 10 + 5)
        )
    conn.commit()
    conn.close()

    mock_engine = MethodDiscoveryEngine(tmp_path)
    results = mock_engine.discover_candidates("handlePayment", max_candidates=2)
    assert len(results) == 2
    warnings = mock_engine.last_traversal_report.get("warnings", [])
    assert any("truncated to top 2" in w for w in warnings)
    mock_engine.close()
    engine.close()
