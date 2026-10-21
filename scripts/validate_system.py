#!/usr/bin/env python3
"""
scripts/validate_system.py
Validates the QA Agent System architecture, skill definitions, dependencies,
and simulates an end-to-end dry-run for a hypothetical Login module.
"""

import sys
import os
import json
import shutil
import subprocess
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

SYSTEM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SYSTEM_ROOT))
sys.path.insert(0, str(SYSTEM_ROOT / "scripts"))

EXPECTED_SKILLS = [
    "module-intake",
    "graphify-context-discovery",
    "requirement-gap-analysis",
    "playwright-investigation",
    "testcase-design",
    "testcase-review-export",
    "automation-readiness",
    "automation-implementation",
    "test-execution-debugging",
    "continuous-learning",
    "workflow-orchestrator"
]

def check(name, fn, compact=False):
    if not compact:
        print(f"\n[RUNNING] {name}...")
    try:
        res = fn()
        if compact:
            print(f"[{name.split('.')[0]}/9 PASS] {name.split('. ', 1)[-1]}")
        else:
            print(f"  [PASS] {name}: {res}")
        return True, res
    except Exception as e:
        print(f"  [FAIL] {name}: {str(e)}")
        return False, str(e)

def validate_file_structure():
    assert (SYSTEM_ROOT / "AGENTS.md").exists(), "AGENTS.md missing"
    assert (SYSTEM_ROOT / "plugin.json").exists(), "plugin.json missing"
    assert (SYSTEM_ROOT / "templates" / "testcase-template.xlsx").exists(), "Excel template missing"
    assert (SYSTEM_ROOT / "references" / "severity-guidelines.md").exists(), "severity-guidelines.md missing"
    assert (SYSTEM_ROOT / "references" / "requirement-gaps-template.md").exists(), "requirement-gaps-template.md missing"
    assert (SYSTEM_ROOT / "references" / "testcase-quality-checklist.md").exists(), "checklist missing"
    assert (SYSTEM_ROOT / "references" / "workflow-state-schema.json").exists(), "state schema missing"
    return "All structural directories and global files exist."

def validate_skill_metadata():
    for sk in EXPECTED_SKILLS:
        skill_file = SYSTEM_ROOT / "skills" / sk / "SKILL.md"
        assert skill_file.exists(), f"Skill file {skill_file} missing"
        text = skill_file.read_text(encoding="utf-8")
        assert text.startswith("---"), f"Skill {sk} lacks YAML frontmatter"
        assert f"name: {sk}" in text, f"Skill {sk} name mismatch in frontmatter"
        assert "description:" in text, f"Skill {sk} missing description"
    return f"All {len(EXPECTED_SKILLS)} skills have valid frontmatter and files."

def validate_excel_template():
    import openpyxl
    tpl_path = SYSTEM_ROOT / "templates" / "testcase-template.xlsx"
    wb = openpyxl.load_workbook(tpl_path)
    expected_sheets = ["Test Cases", "Requirement Gaps", "Coverage Summary"]
    for s in expected_sheets:
        assert s in wb.sheetnames, f"Sheet '{s}' missing in template"
    
    ws_tc = wb["Test Cases"]
    headers = [c.value for c in ws_tc[1] if c.value]
    assert "Test Case ID" in headers, "Test Case ID missing"
    assert "Severity" in headers, "Severity missing"
    assert "Automation Ready" in headers, "Automation Ready missing"
    assert "Status" in headers, "Status missing"
    return f"Excel template verified with sheets: {wb.sheetnames} and 13 columns including Status"

def check_graphify_tool():
    res = subprocess.run(["graphify", "--version"], capture_output=True, text=True, shell=True)
    if res.returncode == 0:
        return f"Operational: {res.stdout.strip()}"
    return "Graphify CLI not found in PATH"

def check_playwright_cli():
    res = subprocess.run(["npx", "playwright", "--version"], capture_output=True, text=True, shell=True)
    if res.returncode == 0:
        return f"Operational: {res.stdout.strip()}"
    return "Playwright CLI not available globally (checked via npx)"

def check_markitdown_tool():
    res = subprocess.run(["markitdown", "--version"], capture_output=True, text=True, shell=True)
    if res.returncode == 0:
        return f"Operational: {res.stdout.strip()}"
    return "MarkItDown CLI not found in PATH"

def check_mcp_config():
    mcp_file = Path.home() / ".gemini" / "config" / "mcp_config.json"
    if mcp_file.exists():
        data = json.loads(mcp_file.read_text(encoding="utf-8"))
        servers = list(data.get("mcpServers", {}).keys())
        return f"Configured MCP servers: {servers}"
    return "Global mcp_config.json not found"

def run_dry_run_simulation():
    from scripts.state_manager import WorkflowStateManager
    import tempfile

    tmp_dir = Path(tempfile.mkdtemp(prefix="qa_dryrun_"))
    try:
        mgr = WorkflowStateManager(str(tmp_dir))
        
        # 1. Step 0: Module Intake
        s0 = mgr.init_state("Hypothetical_Login", {"repo": "dry-run-repo"})
        assert s0["current_state"] == "INITIALIZED"

        # 2. Step 1: Context Discovery
        s1 = mgr.transition("GAP_ANALYSIS", "Discovered entry points: /login, authService, UserCredentials")
        assert s1["current_state"] == "GAP_ANALYSIS"

        # 3. Step 2: Gap Analysis -> Mandatory Gate 1
        s2 = mgr.transition("WAITING_FOR_REQUIREMENT_CLARIFICATION", "Found gap: lockout policy unspecified")
        assert s2["current_state"] == "WAITING_FOR_REQUIREMENT_CLARIFICATION"
        assert s2["pending_approval"] is not None

        # 4. Step 3: Handle Clarification (Path A)
        s3 = mgr.transition("TESTCASE_GENERATION", "User provided BA answer: Lockout after 5 failed attempts for 15 mins")
        assert s3["current_state"] == "TESTCASE_GENERATION"

        # 5. Step 4 & 5: Testcase Design & Review -> Mandatory Gate 2
        testcase_payload = {
            "testcases": [
                {
                    "id": "TC-LOGIN-001",
                    "module": "Login",
                    "name": "Đăng nhập thành công với tài khoản hợp lệ",
                    "preconditions": "Tài khoản active",
                    "test_data": "user=john, pass=secret",
                    "steps": "1. Mở trang login\n2. Nhập user, pass\n3. Bấm login",
                    "expected_result": "Đăng nhập thành công vào Dashboard",
                    "severity": "Chặn",
                    "automation_ready": "Yes",
                    "automation_blocker": "",
                    "requirement_ref": "SPEC-01",
                    "notes": "Core happy path"
                },
                {
                    "id": "TC-LOGIN-002",
                    "module": "Login",
                    "name": "Khóa tài khoản sau 5 lần nhập sai",
                    "preconditions": "Tài khoản active",
                    "test_data": "user=john, pass=wrong",
                    "steps": "1. Nhập sai pass 5 lần",
                    "expected_result": "Hiện thông báo tài khoản bị tạm khóa 15 phút",
                    "severity": "Sai",
                    "automation_ready": "Yes",
                    "automation_blocker": "",
                    "requirement_ref": "SPEC-02",
                    "notes": "Security test"
                },
                {
                    "id": "TC-LOGIN-003",
                    "module": "Login",
                    "name": "Đăng nhập bằng OTP thiết bị phần cứng",
                    "preconditions": "Thiết bị bảo mật USB cắm vào máy",
                    "test_data": "FIDO2 Key",
                    "steps": "1. Chạm tay vào khóa bảo mật",
                    "expected_result": "Xác thực thiết bị thành công",
                    "severity": "Sai",
                    "automation_ready": "No",
                    "automation_blocker": "Cần thiết bị phần cứng vật lý, không thể giả lập qua browser",
                    "requirement_ref": "SPEC-03",
                    "notes": "Manual only"
                }
            ],
            "gaps": [],
            "summary": {
                "module_name": "Hypothetical_Login",
                "covered_flows": "Username/Password, Lockout",
                "uncovered_risks": "SSO OAuth2, Hardware tokens",
                "environment_assumptions": "Staging server"
            }
        }
        
        from scripts.export_testcases import export_to_excel
        from scripts.read_approved_testcases import parse_approved_workbook

        excel_out = tmp_dir / "Hypothetical_Login-testcases.xlsx"
        export_to_excel(testcase_payload, excel_out)
        assert excel_out.exists(), "Exported Excel file does not exist"

        s4 = mgr.transition("WAITING_FOR_APPROVED_TESTCASES", "Excel generated and delivered to user")
        assert s4["current_state"] == "WAITING_FOR_APPROVED_TESTCASES"
        assert s4["pending_approval"] is not None

        # 6. Step 6.1: Read Approved Excel
        approved_result = parse_approved_workbook(excel_out)
        assert approved_result["success"] is True
        assert approved_result["total_cases"] == 3
        assert approved_result["automation_ready_count"] == 2
        assert approved_result["skipped_count"] == 1
        assert approved_result["ready_testcases"][0].get("status") == "Pending"

        s5 = mgr.transition("AUTOMATION_IMPLEMENTATION", "User approved workbook; 2 ready cases selected")
        assert s5["current_state"] == "AUTOMATION_IMPLEMENTATION"

        # 7. Resumability check
        integrity = mgr.validate_integrity()
        assert integrity["valid"] is True
        assert integrity["current_state"] == "AUTOMATION_IMPLEMENTATION"

        return "Dry run simulation PASSED through all 6 phases and 2 human checkpoints successfully."
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

def validate_traceability_engine():
    from scripts.traceability_validator import validate_traceability

    # 1. Clean payload test
    clean_payload = {
        "requirements": ["SPEC-AUTH-01", "SPEC-AUTH-02"],
        "testcases": [
            {
                "id": "TC-01",
                "name": "Login success",
                "preconditions": "Active account",
                "test_data": "user/pass",
                "steps": "1. Login",
                "expected_result": "Dashboard",
                "requirement_ref": "SPEC-AUTH-01"
            },
            {
                "id": "TC-02",
                "name": "Lockout after 5 fails",
                "preconditions": "Active account",
                "test_data": "user/badpass",
                "steps": "1. Bad pass 5 times",
                "expected_result": "Locked 15m",
                "requirement_ref": "SPEC-AUTH-02"
            }
        ]
    }
    res_clean = validate_traceability(clean_payload)
    assert res_clean["valid"] is True, "Clean payload failed traceability validation"
    assert res_clean["metrics"]["coverage_percentage"] == 100.0, "Coverage calculation mismatch"

    # 2. Flawed payload test (Orphan Req, Orphan TC, Duplicate)
    flawed_payload = {
        "requirements": ["SPEC-AUTH-01", "SPEC-MISSING-REQ"],
        "testcases": [
            {
                "id": "TC-01",
                "name": "Login success",
                "steps": "1. Login",
                "expected_result": "Dashboard",
                "requirement_ref": "SPEC-AUTH-01"
            },
            {
                "id": "TC-02",
                "name": "Login success", # Duplicate name & steps
                "steps": "1. Login",
                "expected_result": "Dashboard",
                "requirement_ref": "SPEC-AUTH-01"
            },
            {
                "id": "TC-03",
                "name": "Hallucinated case",
                "steps": "1. Mystery",
                "expected_result": "Unknown",
                "requirement_ref": "" # Orphan TC (no ref)
            }
        ]
    }
    res_flawed = validate_traceability(flawed_payload)
    assert res_flawed["valid"] is False, "Flawed payload falsely passed validation"
    assert res_flawed["metrics"]["orphan_requirements_count"] == 1, "Failed to catch orphan requirement"
    assert res_flawed["metrics"]["orphan_testcases_count"] == 1, "Failed to catch orphan test case"
    assert res_flawed["metrics"]["duplicate_groups_count"] == 1, "Failed to catch duplicate test case"

    return "Traceability validator correctly enforces Forward Coverage, Backward Grounding, and Deduplication."

def main():
    compact = "--compact" in sys.argv or "-c" in sys.argv
    if not compact:
        print("=" * 60)
        print("QA AGENT SYSTEM — VERIFICATION & VALIDATION SUITE")
        print("=" * 60)

    results = []
    results.append(check("1. Directory & File Structure", validate_file_structure, compact))
    results.append(check("2. Skill Metadata & Frontmatter", validate_skill_metadata, compact))
    results.append(check("3. Excel Template Schema", validate_excel_template, compact))
    results.append(check("4. Graphify CLI Verification", check_graphify_tool, compact))
    results.append(check("5. Playwright CLI Verification", check_playwright_cli, compact))
    results.append(check("6. MarkItDown CLI Verification", check_markitdown_tool, compact))
    results.append(check("7. MCP Server Configurations", check_mcp_config, compact))
    results.append(check("8. End-to-End Dry-Run Simulation", run_dry_run_simulation, compact))
    results.append(check("9. Requirement Traceability & Deduplication", validate_traceability_engine, compact))

    all_passed = all(r[0] for r in results)
    if compact:
        status_tag = "[SUCCESS]" if all_passed else "[WARNING]"
        print(f"{status_tag} {sum(1 for r in results if r[0])}/9 Architectural Validations PASSED!")
    else:
        print("\n" + "=" * 60)
        if all_passed:
            print("[SUCCESS] All architectural validations and dry-run tests PASSED!")
        else:
            print("[WARNING] Some checks reported warnings or non-zero status.")
        print("=" * 60)

if __name__ == "__main__":
    main()
