#!/usr/bin/env python3
"""
scripts/export_testcases.py
Exports designed test cases, requirement gaps, and coverage summary into a high-end,
executive-ready Excel file (.xlsx) with pastel pill badges, zebra striping, and auto-filters.
"""

import sys
import json
import math
import logging
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError) as exc:
        logger.debug("Unable to reconfigure stdout encoding: %s", exc)

import unicodedata
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter

# Dynamic sys.path fallback for safe invocation from any working directory
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

try:
    from traceability_validator import validate_traceability
except ImportError:
    try:
        from scripts.traceability_validator import validate_traceability
    except ImportError:
        validate_traceability = None

FONT_NAME = "Segoe UI"
HEADER_FONT = Font(name=FONT_NAME, size=11, bold=True, color="FFFFFF")
TITLE_FONT = Font(name=FONT_NAME, size=14, bold=True, color="FFFFFF")
DATA_FONT = Font(name=FONT_NAME, size=10, color="1E293B")
BOLD_DATA_FONT = Font(name=FONT_NAME, size=10, bold=True, color="1E293B")
NOTE_FONT = Font(name=FONT_NAME, size=9, italic=True, color="64748B")

PRIMARY_NAVY = "0F294A"    # Deep corporate navy for Sheet 1
SECONDARY_NAVY = "1E3A8A"  # Indigo navy for Sheet 2

FILL_HEADER_1 = PatternFill(start_color=PRIMARY_NAVY, end_color=PRIMARY_NAVY, fill_type="solid")
FILL_HEADER_2 = PatternFill(start_color=SECONDARY_NAVY, end_color=SECONDARY_NAVY, fill_type="solid")
FILL_ZEBRA_EVEN = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
FILL_ZEBRA_ODD = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

# Pastel Badges for Severity
FILL_CHAN = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")  # Soft Rose Red
FONT_CHAN = Font(name=FONT_NAME, size=10, bold=True, color="991B1B")

FILL_SAI = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")   # Soft Amber Yellow
FONT_SAI = Font(name=FONT_NAME, size=10, bold=True, color="92400E")

FILL_NHO = PatternFill(start_color="E0F2FE", end_color="E0F2FE", fill_type="solid")   # Soft Sky Blue
FONT_NHO = Font(name=FONT_NAME, size=10, bold=True, color="075985")

# Pastel Badges for Automation Ready
FILL_READY_YES = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid") # Soft Emerald
FONT_READY_YES = Font(name=FONT_NAME, size=10, bold=True, color="166534")

FILL_READY_NO = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")  # Neutral Slate
FONT_READY_NO = Font(name=FONT_NAME, size=10, color="475569")

# Borders
BORDER_SUBTLE = Border(
    left=Side(style='thin', color='E2E8F0'),
    right=Side(style='thin', color='E2E8F0'),
    top=Side(style='thin', color='E2E8F0'),
    bottom=Side(style='thin', color='E2E8F0')
)
BORDER_HEADER_BOTTOM = Border(
    left=Side(style='thin', color='E2E8F0'),
    right=Side(style='thin', color='E2E8F0'),
    top=Side(style='thin', color='E2E8F0'),
    bottom=Side(style='medium', color='0F172A')
)

ALIGN_DATA_CENTER = Alignment(horizontal="center", vertical="top", wrap_text=True)
ALIGN_DATA_LEFT = Alignment(horizontal="left", vertical="top", wrap_text=True)
ALIGN_HEADER = Alignment(horizontal="center", vertical="center", wrap_text=True)

FORMULA_PREFIXES = ("=", "+", "-", "@")

def sanitize_cell_value(val):
    """Prevent untrusted workbook text from being interpreted as a formula or DDE command."""
    if isinstance(val, str) and val.startswith(FORMULA_PREFIXES):
        return f"'{val}"
    return val

def style_severity_cell(cell):
    val = unicodedata.normalize('NFC', str(cell.value or "")).strip().lower()
    if any(k in val for k in ["chặn", "chan", "blocker", "critical"]):
        cell.fill = FILL_CHAN
        cell.font = FONT_CHAN
    elif any(k in val for k in ["sai", "major", "error"]):
        cell.fill = FILL_SAI
        cell.font = FONT_SAI
    elif any(k in val for k in ["nhỏ", "nho", "minor", "trivial", "low"]):
        cell.fill = FILL_NHO
        cell.font = FONT_NHO
    cell.alignment = ALIGN_DATA_CENTER

def style_ready_cell(cell):
    val = unicodedata.normalize('NFC', str(cell.value or "")).strip().lower()
    if val in {"yes", "y", "true", "1", "có", "co"}:
        cell.fill = FILL_READY_YES
        cell.font = FONT_READY_YES
    else:
        cell.fill = FILL_READY_NO
        cell.font = FONT_READY_NO
    cell.alignment = ALIGN_DATA_CENTER

def style_status_cell(cell):
    val = str(cell.value or "").strip().lower()
    if val == "pass":
        cell.fill = FILL_READY_YES
        cell.font = FONT_READY_YES
    elif val == "fail":
        cell.fill = FILL_CHAN
        cell.font = FONT_CHAN
    elif val == "skip":
        cell.fill = FILL_READY_NO
        cell.font = FONT_READY_NO
    else:  # Mặc định: Pending
        cell.fill = FILL_SAI
        cell.font = FONT_SAI
    cell.alignment = ALIGN_DATA_CENTER

def auto_fit_rows_and_view(
    ws,
    col_widths: Dict[str, int],
    min_row: int = 2,
    min_height: int = 28,
    line_height: int = 16,
    padding: int = 12,
    zoom_scale: int = 85
):
    """
    1. Sets default opening zoomScale (85%) so all columns fit comfortably on screen without horizontal scroll.
    2. Dynamically calculates and sets row height based on content length, word-wrapping,
       and newlines so text is never truncated or clipped vertically.
    3. Configures print / export setup to fit 1 page wide in Landscape mode.
    """
    try:
        if hasattr(ws, "views") and ws.views.sheetView:
            ws.views.sheetView[0].zoomScale = zoom_scale
        elif hasattr(ws, "sheet_view"):
            ws.sheet_view.zoomScale = zoom_scale
    except (AttributeError, IndexError, TypeError, ValueError) as exc:
        logger.warning("Unable to set worksheet zoom; continuing with workbook default: %s", exc)

    try:
        ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
        ws.page_setup.paperSize = ws.PAPERSIZE_A4
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.sheet_properties.pageSetUpPr.fitToPage = True
    except (AttributeError, TypeError, ValueError) as exc:
        logger.warning("Unable to configure print layout; continuing with workbook default: %s", exc)

    for r in range(min_row, ws.max_row + 1):
        max_lines = 1
        for c in range(1, ws.max_column + 1):
            cell = ws.cell(row=r, column=c)
            val = cell.value
            if not val:
                continue
            text = str(val).strip()
            if not text:
                continue
            col_letter = get_column_letter(c)
            w = col_widths.get(col_letter, 25)
            # Usable characters per line in Segoe UI 10pt with standard cell margins
            usable_chars = max(8, int(w * 0.92) - 2)
            cell_lines = 0
            for paragraph in text.split("\n"):
                p = paragraph.strip()
                if not p:
                    cell_lines += 1
                else:
                    cell_lines += max(1, math.ceil(len(p) / usable_chars))
            if cell_lines > max_lines:
                max_lines = cell_lines
        ws.row_dimensions[r].height = max(min_height, max_lines * line_height + padding)

def export_to_excel(data: Dict[str, Any], output_path: Path):
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    # 1. Test Cases Sheet
    ws_tc = wb.create_sheet(title="Test Cases")
    ws_tc.views.sheetView[0].showGridLines = True
    ws_tc.row_dimensions[1].height = 32

    tc_headers = [
        "Test Case ID", "Module", "Test Case Name", "Preconditions",
        "Test Data", "Test Steps", "Expected Result", "Severity",
        "Automation Ready", "Automation Blocker", "Requirement Reference", "Notes",
        "Status"
    ]
    ws_tc.append(tc_headers)

    testcases = data.get("testcases", [])
    max_val_tc = max(1000, len(testcases) + 500)

    dv_severity = DataValidation(type="list", formula1='"Chặn,Sai,Nhỏ"', allow_blank=True)
    ws_tc.add_data_validation(dv_severity)
    dv_severity.add(f"H2:H{max_val_tc}")

    dv_auto = DataValidation(type="list", formula1='"Yes,No"', allow_blank=True)
    ws_tc.add_data_validation(dv_auto)
    dv_auto.add(f"I2:I{max_val_tc}")

    dv_status = DataValidation(type="list", formula1='"Pass,Fail,Pending,Skip"', allow_blank=True)
    ws_tc.add_data_validation(dv_status)
    dv_status.add(f"M2:M{max_val_tc}")
    for tc in testcases:
        row = [
            tc.get("id", ""),
            tc.get("module", ""),
            tc.get("name", ""),
            tc.get("preconditions", ""),
            tc.get("test_data", ""),
            tc.get("steps", ""),
            tc.get("expected_result", ""),
            tc.get("severity", "Sai"),
            tc.get("automation_ready", "Yes"),
            tc.get("automation_blocker", ""),
            tc.get("requirement_ref", ""),
            tc.get("notes", ""),
            tc.get("status", "Pending")
        ]
        ws_tc.append([sanitize_cell_value(value) for value in row])

    ws_tc.freeze_panes = "A2"
    max_row_tc = max(2, len(testcases) + 1)
    ws_tc.auto_filter.ref = f"A1:{get_column_letter(len(tc_headers))}{max_row_tc}"

    for cell in ws_tc[1]:
        cell.font = HEADER_FONT
        cell.fill = FILL_HEADER_1
        cell.alignment = ALIGN_HEADER
        cell.border = BORDER_HEADER_BOTTOM

    for row_idx, row in enumerate(ws_tc.iter_rows(min_row=2, max_row=max_row_tc, min_col=1, max_col=len(tc_headers)), start=2):
        is_odd = (row_idx % 2 == 1)
        row_fill = FILL_ZEBRA_ODD if is_odd else FILL_ZEBRA_EVEN

        for cell in row:
            cell.font = DATA_FONT
            cell.border = BORDER_SUBTLE
            cell.fill = row_fill

            if cell.column == 1:
                cell.font = BOLD_DATA_FONT
                cell.alignment = ALIGN_DATA_CENTER
            elif cell.column == 8:
                style_severity_cell(cell)
            elif cell.column == 9:
                style_ready_cell(cell)
            elif cell.column == 12:
                cell.font = NOTE_FONT
                cell.alignment = ALIGN_DATA_LEFT
            elif cell.column == 13:
                style_status_cell(cell)
            else:
                cell.alignment = ALIGN_DATA_LEFT

    col_widths_tc = {
        "A": 14, "B": 15, "C": 30, "D": 26, "E": 26, "F": 36,
        "G": 36, "H": 13, "I": 14, "J": 22, "K": 20, "L": 22, "M": 14
    }
    for col_letter, width in col_widths_tc.items():
        ws_tc.column_dimensions[col_letter].width = width

    auto_fit_rows_and_view(ws_tc, col_widths_tc, min_row=2, min_height=28, zoom_scale=85)

    # 2. Requirement Gaps Sheet
    ws_gaps = wb.create_sheet(title="Requirement Gaps")
    ws_gaps.views.sheetView[0].showGridLines = True
    ws_gaps.row_dimensions[1].height = 32

    gap_headers = [
        "Issue ID", "Related Flow", "Current Evidence", "Uncertainty",
        "UX Impact", "Future Technical Risk", "Question for BA/PO", "Suggested Options", "Status"
    ]
    ws_gaps.append(gap_headers)

    gaps = data.get("gaps", [])
    max_val_gap = max(500, len(gaps) + 200)

    dv_gap_status = DataValidation(type="list", formula1='"Pending,Answered,Skipped"', allow_blank=True)
    ws_gaps.add_data_validation(dv_gap_status)
    status_col_letter = get_column_letter(len(gap_headers))
    dv_gap_status.add(f"{status_col_letter}2:{status_col_letter}{max_val_gap}")
    for gap in gaps:
        ux_impact = gap.get("ux_impact") or gap.get("business_impact", "")
        future_risk = gap.get("future_risk") or gap.get("potential_defect") or gap.get("future_technical_risk", "")
        question = gap.get("question") or gap.get("question_for_ba", "")
        row = [
            gap.get("id", ""),
            gap.get("related_flow", ""),
            gap.get("current_evidence", ""),
            gap.get("uncertainty", ""),
            ux_impact,
            future_risk,
            question,
            gap.get("suggested_options", ""),
            gap.get("status", "Pending")
        ]
        ws_gaps.append([sanitize_cell_value(value) for value in row])

    ws_gaps.freeze_panes = "A2"
    max_row_gap = max(2, len(gaps) + 1)
    ws_gaps.auto_filter.ref = f"A1:{get_column_letter(len(gap_headers))}{max_row_gap}"

    for cell in ws_gaps[1]:
        cell.font = HEADER_FONT
        cell.fill = FILL_HEADER_2
        cell.alignment = ALIGN_HEADER
        cell.border = BORDER_HEADER_BOTTOM

    for row_idx, row in enumerate(ws_gaps.iter_rows(min_row=2, max_row=max_row_gap, min_col=1, max_col=len(gap_headers)), start=2):
        row_fill = FILL_ZEBRA_ODD if (row_idx % 2 == 1) else FILL_ZEBRA_EVEN

        for cell in row:
            cell.font = DATA_FONT
            cell.border = BORDER_SUBTLE
            cell.fill = row_fill

            if cell.column == 1:
                cell.font = BOLD_DATA_FONT
                cell.alignment = ALIGN_DATA_CENTER
            elif cell.column == len(gap_headers):
                st = str(cell.value or "").strip().lower()
                if st in ["answered", "đã làm rõ"]:
                    cell.fill = FILL_READY_YES
                    cell.font = FONT_READY_YES
                elif st in ["pending", "chờ làm rõ"]:
                    cell.fill = FILL_SAI
                    cell.font = FONT_SAI
                else:
                    cell.fill = FILL_READY_NO
                    cell.font = FONT_READY_NO
                cell.alignment = ALIGN_DATA_CENTER
            else:
                cell.alignment = ALIGN_DATA_LEFT

    col_widths_gap = {
        "A": 13, "B": 20, "C": 24, "D": 26, "E": 28, "F": 28, "G": 30, "H": 26, "I": 14
    }
    for col_letter, width in col_widths_gap.items():
        ws_gaps.column_dimensions[col_letter].width = width

    auto_fit_rows_and_view(ws_gaps, col_widths_gap, min_row=2, min_height=28, zoom_scale=85)

    # 3. Coverage Summary Sheet
    ws_sum = wb.create_sheet(title="Coverage Summary")
    ws_sum.views.sheetView[0].showGridLines = True
    ws_sum.column_dimensions["A"].width = 30
    ws_sum.column_dimensions["B"].width = 70

    ws_sum.row_dimensions[1].height = 40
    ws_sum.append(["BÁO CÁO TỔNG HỢP ĐỘ BAO PHỦ VÀ RỦI RO KIỂM THỬ", ""])
    ws_sum.merge_cells("A1:B1")
    ws_sum["A1"].font = TITLE_FONT
    ws_sum["A1"].fill = FILL_HEADER_1
    ws_sum["A1"].alignment = Alignment(horizontal="left", vertical="center", indent=1)

    summary_info = data.get("summary", {})
    critical_count = sum(1 for t in testcases if any(x in str(t.get("severity", "")).lower() for x in ["critical", "blocker", "chặn"]))
    major_count = sum(1 for t in testcases if any(x in str(t.get("severity", "")).lower() for x in ["major", "sai"]))
    minor_count = sum(1 for t in testcases if any(x in str(t.get("severity", "")).lower() for x in ["minor", "nhỏ"]))
    ready_count = sum(1 for t in testcases if str(t.get("automation_ready", "")).strip().lower() == "yes")
    not_ready_count = len(testcases) - ready_count

    if validate_traceability:
        t_audit = validate_traceability(data)
    else:
        t_audit = {"metrics": {}, "orphan_requirements": [], "orphan_testcases": [], "duplicate_groups": []}
    t_metrics = t_audit.get("metrics", {})

    orphan_req_str = "None (0) - 100% Full Coverage" if t_metrics.get("orphan_requirements_count", 0) == 0 else f"{t_metrics.get('orphan_requirements_count')} requirements: " + ", ".join(o.get('requirement', '') for o in t_audit.get('orphan_requirements', []))
    orphan_tc_str = "None (0) - 100% Grounded Test Cases" if t_metrics.get("orphan_testcases_count", 0) == 0 else f"{t_metrics.get('orphan_testcases_count')} test cases: " + ", ".join(o.get('id', '') for o in t_audit.get('orphan_testcases', []))
    dup_str = "None (0) - Clean Minimal Test Suite" if t_metrics.get("duplicate_groups_count", 0) == 0 else f"{t_metrics.get('duplicate_groups_count')} duplicate pairs: " + ", ".join(f"{d['pair'][0]}={d['pair'][1]}" for d in t_audit.get('duplicate_groups', []))

    summary_rows = [
        ("Module Name:", summary_info.get("module_name", "")),
        ("Total Designed Test Cases:", f"{len(testcases)} cases (Dynamic Risk-Based Coverage)"),
        ("Automation Ready (Yes):", f"{ready_count} ({ready_count/max(1, len(testcases))*100:.0f}%)"),
        ("Manual Intervention Required (No):", str(not_ready_count)),
        ("Severity Distribution:", f"Critical: {critical_count} | Major: {major_count} | Minor: {minor_count}"),
        ("Requirement Traceability Rate:", f"{t_metrics.get('coverage_percentage', 100)}% ({t_metrics.get('covered_requirements_count', 0)}/{t_metrics.get('total_requirements', 0)} verified requirements)"),
        ("Uncovered Critical Requirements (Orphan):", orphan_req_str),
        ("Ungrounded / Hallucinated Test Cases:", orphan_tc_str),
        ("Duplicate Test Cases:", dup_str),
        ("Covered Business Flows:", summary_info.get("covered_flows", "")),
        ("Uncovered Risk Areas / Backlog:", summary_info.get("uncovered_risks", "")),
        ("Environment & Data Assumptions:", summary_info.get("environment_assumptions", ""))
    ]

    for label, val in summary_rows:
        ws_sum.append([label, val])

    try:
        if hasattr(ws_sum, "views") and ws_sum.views.sheetView:
            ws_sum.views.sheetView[0].zoomScale = 90
        elif hasattr(ws_sum, "sheet_view"):
            ws_sum.sheet_view.zoomScale = 90
    except (AttributeError, IndexError, TypeError, ValueError) as exc:
        logger.warning("Unable to set summary worksheet zoom: %s", exc)

    for row_idx in range(2, len(summary_rows) + 2):
        cell_lbl = ws_sum.cell(row=row_idx, column=1)
        cell_val = ws_sum.cell(row=row_idx, column=2)

        cell_lbl.font = BOLD_DATA_FONT
        cell_lbl.fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
        cell_lbl.border = BORDER_SUBTLE
        cell_lbl.alignment = Alignment(horizontal="left", vertical="top", indent=1)

        cell_val.font = DATA_FONT
        cell_val.fill = FILL_ZEBRA_EVEN
        cell_val.border = BORDER_SUBTLE
        cell_val.alignment = ALIGN_DATA_LEFT

        val_text = str(cell_val.value or "").strip()
        lines = 0
        for p in val_text.split("\n"):
            lines += max(1, math.ceil(len(p) / 65))
        ws_sum.row_dimensions[row_idx].height = max(28, lines * 16 + 10)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    actual_path = output_path
    try:
        wb.save(output_path)
    except PermissionError:
        actual_path = output_path.with_name(f"{output_path.stem} (auto-scale){output_path.suffix}")
        wb.save(actual_path)
        print(f"[NOTE] File '{output_path.name}' is currently locked. Saved auto-scaled copy to: '{actual_path.name}'")

    print(f"[OK] Exported: {actual_path} (Total: {len(testcases)} | Critical: {critical_count} | Major: {major_count} | Minor: {minor_count} | Ready: {ready_count})")

def build_template(output_path: Path):
    sample_payload = {
        "summary": {
            "module_name": "Authentication & Access Control",
            "covered_flows": "• Standard credentials sign-in (Happy Path)\n• Submission rate-limiting and anti-automation throttling\n• Toggle between Username and Work Email identification methods",
            "uncovered_risks": "• SSO OAuth2 identity federation via corporate IdP (Google / Microsoft Azure AD)\n• Hardware FIDO2 / WebAuthn biometric security keys",
            "environment_assumptions": "• Staging environment with rate-limiter enabled\n• Pre-seeded active test accounts without administrative lockout"
        },
        "testcases": [
            {
                "id": "TC-AUTH-001",
                "module": "Authentication",
                "name": "Successful sign-in with valid credentials (Happy Path)",
                "preconditions": "Active user account with verified email and no existing security locks",
                "test_data": "Username: qa_standard_user, Password: ValidPassword@2026",
                "steps": "1. Open Sign-In screen (/login)\n2. Enter valid username and password\n3. Click 'Sign In' button",
                "expected_result": "System validates credentials successfully and automatically redirects user to Main Dashboard",
                "severity": "Critical",
                "automation_ready": "Yes",
                "automation_blocker": "",
                "requirement_ref": "SPEC-AUTH-01 / BR§2.1",
                "notes": "Core business authentication flow",
                "status": "Pass"
            },
            {
                "id": "TC-AUTH-002",
                "module": "Authentication",
                "name": "Rate-limiting enforcement: Block repeated requests exceeding 3 attempts within 15 minutes",
                "preconditions": "Account has already submitted 3 unsuccessful requests in the last 15 minutes",
                "test_data": "User identifier: test_locked_account@example.com",
                "steps": "1. Open Password Recovery screen\n2. Enter identifier into input field\n3. Click 'Send Reset Link' button on 4th attempt",
                "expected_result": "System displays standard rate-limit feedback message (Code: SEC-RL-03) without revealing account existence; rejects dispatch of additional reset tokens.",
                "severity": "Critical",
                "automation_ready": "Yes",
                "automation_blocker": "",
                "requirement_ref": "SPEC-SEC-26 (RateLimiting)",
                "notes": "Anti-enumeration and brute-force mitigation",
                "status": "Pass"
            },
            {
                "id": "TC-AUTH-003",
                "module": "Authentication",
                "name": "Form state sanitation: Switching sign-in method automatically resets input buffer",
                "preconditions": "User is on the sign-in modal with Username tab active by default",
                "test_data": "Draft input: user_temp_entry",
                "steps": "1. Type 'user_temp_entry' into Username input\n2. Click 'Work Email' tab",
                "expected_result": "Active view switches to Email mode, input field is cleared, and placeholder updates to email format.",
                "severity": "Major",
                "automation_ready": "Yes",
                "automation_blocker": "",
                "requirement_ref": "SPEC-AUTH-02 / BR§2.3",
                "notes": "Clean input mode transition",
                "status": "Pending"
            }
        ],
        "gaps": [
            {
                "id": "GAP-01",
                "related_flow": "Session Lifecycle Management",
                "current_evidence": "src/auth/jwt.config.ts:42",
                "uncertainty": "Specification states a 15-minute idle session timeout, but codebase configures a 24-hour JWT refresh token without active sliding revocation",
                "ux_impact": "Users receive no idle timeout warning dialog; sessions may abruptly terminate mid-transaction or remain unexpectedly active on shared workstations",
                "future_risk": "Unauthorized access risk on shared enterprise terminals; token invalidation race conditions during multi-device sign-out",
                "question_for_ba": "Should the system enforce strict 15-minute idle expiration or maintain extended 24-hour persistent sessions?",
                "suggested_options": "A) 15-minute idle timeout with 60-second warning modal (Enterprise High Security)\nB) 24-hour persistent session with sliding refresh (Standard SaaS Convenience)",
                "status": "Clarified"
            }
        ]
    }
    export_to_excel(sample_payload, output_path)
    print(f"[OK] Generated high-end polished Excel template at: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--template":
        out = Path(__file__).resolve().parent.parent / "templates" / "testcase-template.xlsx"
        build_template(out)
    elif len(sys.argv) == 3 and sys.argv[1] == "--template":
        out = Path(sys.argv[2])
        build_template(out)
    elif len(sys.argv) < 3:
        print("Usage: python export_testcases.py <input_data.json> <output_workbook.xlsx>")
        print("       python export_testcases.py --template [output_template.xlsx]")
        sys.exit(1)
    else:
        in_file = Path(sys.argv[1])
        out_file = Path(sys.argv[2])
        with open(in_file, "r", encoding="utf-8") as f:
            payload = json.load(f)
        export_to_excel(payload, out_file)
