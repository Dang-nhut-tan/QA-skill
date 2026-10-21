---
name: testcase-review-export
description: >-
  Executes an internal quality review on designed test cases, generates a styled professional
  Excel workbook (<module>-testcases.xlsx), and enforces a mandatory workflow STOP
  for user review, editing, and approval before any automation begins.
---

# Skill: Test Case Review & Excel Export (Step 5)

## 1. Description & Trigger Conditions
* **Purpose:** Audit the designed test suite against the quality checklist, generate a professional multi-sheet Excel file (`.xlsx`), deliver it to the user, and **halt execution until the user reviews and re-submits the approved workbook**.
* **Triggers:**
  * Completed `testcase-design`.
  * State is `TESTCASE_REVIEW`.

## 2. Inputs
* **Required:**
  * Designed test cases and gap items from Step 4.
  * `.qa-state.json`.
* **References:**
  * `references/testcase-quality-checklist.md`
  * `scripts/export_testcases.py`

## 3. Prerequisites
* Python 3 with `openpyxl` available.

## 4. Step-by-step Execution Instructions
1. **Internal Quality Review (Self-Audit):**
   * Check each test case against the 6 pillars in `references/testcase-quality-checklist.md`:
     1. Unique, stable IDs.
     2. Reproducible, numbered steps.
     3. Measurable expected results (no vague phrases).
     4. Accurate `Chặn / Sai / Nhỏ` severity.
     5. Justified `Automation Ready` flags and blockers.
     6. No duplicate or overlapping test coverage.
   * Auto-correct formatting discrepancies before export.
2. **Export to Standardized Excel Workbook:**
   * Prepare JSON payload containing: `testcases`, `gaps`, and `summary`.
   * Run: `python scripts/export_testcases.py <payload.json> <module-name>-testcases.xlsx`.
   * Verify workbook contains 3 sheets:
     * `Sheet 1 — Test Cases`: 13 columns (bao gồm cột ngoài cùng `Status` với dropdown `Pass, Fail, Pending, Skip`, mặc định là `Pending`), dropdown validations, frozen header, autofilter, badges màu pastel.
     * `Sheet 2 — Requirement Gaps`: Open and resolved issues.
     * `Sheet 3 — Coverage Summary`: High-level metrics, covered flows, and uncovered risks.
3. **Persist State Checkpoint:**
   * Record exported file path in `.qa-state.json` under `artifacts.excel_testcases`.
   * Update workflow state:
     `python scripts/state_manager.py transition WAITING_FOR_APPROVED_TESTCASES "Delivered Excel file to user. Waiting for review and approval"`

## 5. Mandatory Human Checkpoint (CRITICAL)
> [!IMPORTANT]
> **YOU MUST STOP THE WORKFLOW HERE.**
> Present the generated Excel file link to the user and state clearly:
> *"File test case đã được tạo tại `<module-name>-testcases.xlsx`. Xin vui lòng mở file, kiểm tra, chỉnh sửa (nếu cần), đánh dấu các ca muốn tự động hoá (`Automation Ready = Yes`), và phản hồi lại để tiếp tục bước Automation."*
>
> **DO NOT PROCEED TO STEP 6 (AUTOMATION) UNTIL THE USER SUBMITS / CONFIRMS THE EXCEL FILE.**

## 6. Expected Outputs
* Real `.xlsx` workbook: `<module-name>-testcases.xlsx`.
* State file updated to `WAITING_FOR_APPROVED_TESTCASES`.
* Execution paused awaiting user approval.

## 7. Failure Handling
* If `openpyxl` fails to write: inspect permissions and disk space; ensure no running Excel process has locked the file.

## 8. Human Approval Requirements
* Mandatory user review and approval of the Excel file.

## 9. Completion Criteria
* Excel file successfully generated and verified.
* State is `WAITING_FOR_APPROVED_TESTCASES`.
* Workflow is paused.
