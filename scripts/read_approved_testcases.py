#!/usr/bin/env python3
"""
scripts/read_approved_testcases.py
Reads an approved Excel test case file, validates its schema,
and selects strictly rows where `Automation Ready = Yes`.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List
import openpyxl

REQUIRED_COLUMNS = [
    "Test Case ID", "Module", "Test Case Name", "Preconditions",
    "Test Data", "Test Steps", "Expected Result", "Severity", "Automation Ready"
]

def parse_approved_workbook(excel_path: Path) -> Dict[str, Any]:
    if not excel_path.exists():
        return {"success": False, "error": f"File not found: {excel_path}"}

    try:
        wb = openpyxl.load_workbook(excel_path, data_only=True)
    except Exception as e:
        return {"success": False, "error": f"Failed to open workbook: {str(e)}"}

    if "Test Cases" not in wb.sheetnames:
        return {
            "success": False,
            "error": f"Missing required sheet 'Test Cases'. Available sheets: {wb.sheetnames}"
        }

    ws = wb["Test Cases"]
    header_row = [cell.value for cell in ws[1]]
    col_map = {}
    for idx, name in enumerate(header_row):
        if name:
            col_map[str(name).strip()] = idx + 1

    missing = [c for c in REQUIRED_COLUMNS if c not in col_map]
    if missing:
        return {
            "success": False,
            "error": f"Missing required columns in 'Test Cases' sheet: {missing}"
        }

    all_cases = []
    automation_ready_cases = []
    skipped_cases = []

    for row_idx in range(2, ws.max_row + 1):
        tc_id = ws.cell(row=row_idx, column=col_map["Test Case ID"]).value
        if not tc_id:
            continue

        tc_id_str = str(tc_id).strip()
        auto_ready_val = ws.cell(row=row_idx, column=col_map["Automation Ready"]).value
        auto_ready_str = str(auto_ready_val).strip() if auto_ready_val else "No"
        is_ready = auto_ready_str.lower() == "yes"

        tc_item = {
            "row_number": row_idx,
            "id": tc_id_str,
            "module": str(ws.cell(row=row_idx, column=col_map["Module"]).value or "").strip(),
            "name": str(ws.cell(row=row_idx, column=col_map["Test Case Name"]).value or "").strip(),
            "preconditions": str(ws.cell(row=row_idx, column=col_map["Preconditions"]).value or "").strip(),
            "test_data": str(ws.cell(row=row_idx, column=col_map["Test Data"]).value or "").strip(),
            "steps": str(ws.cell(row=row_idx, column=col_map["Test Steps"]).value or "").strip(),
            "expected_result": str(ws.cell(row=row_idx, column=col_map["Expected Result"]).value or "").strip(),
            "severity": str(ws.cell(row=row_idx, column=col_map["Severity"]).value or "").strip(),
            "automation_ready": "Yes" if is_ready else "No",
            "automation_blocker": str(ws.cell(row=row_idx, column=col_map.get("Automation Blocker", 10)).value or "").strip() if "Automation Blocker" in col_map else "",
            "requirement_ref": str(ws.cell(row=row_idx, column=col_map.get("Requirement Reference", 11)).value or "").strip() if "Requirement Reference" in col_map else "",
            "notes": str(ws.cell(row=row_idx, column=col_map.get("Notes", 12)).value or "").strip() if "Notes" in col_map else "",
            "status": str(ws.cell(row=row_idx, column=col_map.get("Status", 13)).value or "Pending").strip() if "Status" in col_map else "Pending"
        }

        all_cases.append(tc_item)
        if is_ready:
            automation_ready_cases.append(tc_item)
        else:
            skipped_cases.append(tc_item)

    return {
        "success": True,
        "excel_path": str(excel_path.resolve()),
        "total_cases": len(all_cases),
        "automation_ready_count": len(automation_ready_cases),
        "skipped_count": len(skipped_cases),
        "ready_testcases": automation_ready_cases,
        "skipped_testcases": skipped_cases
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python read_approved_testcases.py <approved_workbook.xlsx>")
        sys.exit(1)

    file_p = Path(sys.argv[1])
    res = parse_approved_workbook(file_p)
    print(json.dumps(res, indent=2, ensure_ascii=False))
