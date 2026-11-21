---
name: automation-readiness
description: >-
  Ingests the user-approved Excel test case workbook, validates structural schema,
  and filters strictly for test cases marked 'Automation Ready = Yes'.
  Enforces zero-tampering with user-approved expected results.
---

# Skill: Automation Readiness Assessment (Phase 6.1)

## 1. Description & Trigger Conditions
* **Purpose:** Process the human checkpoint from Step 5 by reading the user's approved `.xlsx` file, validating table columns, filtering strictly for rows where `Automation Ready = Yes`, and preparing execution scope.
* **Triggers:**
  * User uploads or points to an approved Excel file and requests automation.
  * State was `WAITING_FOR_APPROVED_TESTCASES`.

## 2. Inputs
* **Required:**
  * Path to approved Excel workbook (e.g. `<module-name>-testcases.xlsx`).
  * `.qa-state.json`.
* **References:**
  * `scripts/read_approved_testcases.py`

## 3. Prerequisites
* Valid `.xlsx` file available locally.

## 4. Step-by-step Execution Instructions
1. **Workbook Inspection & Column Validation:**
   * Run: `python scripts/read_approved_testcases.py <approved_workbook.xlsx>`.
   * *Token Optimization Tip:* To avoid dumping thousands of JSON tokens into the LLM context, use:
     - `python scripts/read_approved_testcases.py <file.xlsx>` for a clean 10-line executive summary.
     - `python scripts/read_approved_testcases.py <file.xlsx> -o approved-cases.json` to persist the full payload to disk without flooding the chat.
     - `python scripts/read_approved_testcases.py <file.xlsx> --ready-only` to retrieve only cases ready for automation.
     - `python scripts/read_approved_testcases.py <file.xlsx> --id <TC_ID>` to retrieve only the single test case needed for coding a specific test file.
   * Verify sheet `Test Cases` contains all required columns: `Test Case ID`, `Module`, `Test Case Name`, `Preconditions`, `Test Data`, `Test Steps`, `Expected Result`, `Severity`, `Automation Ready`.
2. **Filter Automation-Ready Test Cases:**
   * Extract ONLY rows where `Automation Ready` column equals `Yes` (case-insensitive).
   * Strictly do NOT convert `No` or empty values to `Yes`.
   * Strictly do NOT alter or overwrite user-approved `Expected Result` text.
3. **Assess Framework Reusability for Ready Test Cases:**
   * For each test case marked `Automation Ready = Yes`, identify primary UI actions and domain methods.
   * Cross-reference methods against discovered framework assets via:
     `python scripts/codegraph_discovery.py "<action_name>" --repo "<repo_path>"`
   * Group test cases into:
     - **Direct Reuse:** Existing POM methods/helpers exist and can be called immediately.
     - **Conditional Reuse:** Existing POM methods exist but require parameter extension or wrapper adjustments.
     - **New Implementation Needed:** No matching methods exist (`NOT_FOUND`), requiring new automation methods.
4. **Report Intake Breakdown:**
   * Display summary:
     * Total test cases in workbook.
     * Count of `Automation Ready = Yes` selected for implementation (broken down by Direct Reuse vs New Implementation).
     * Count of skipped cases (`No` or missing) with their listed blockers.
5. **Transition Workflow State:**
   * Record approved Excel path in `.qa-state.json` under `artifacts.approved_excel`.
   * Record ready test case IDs in `testcase_ids`.
   * Update workflow state:
     `python scripts/state_manager.py transition AUTOMATION_IMPLEMENTATION "Approved Excel loaded; proceeding to implementation"`.

## 5. Expected Outputs
* Structured JSON list of approved automation-ready test cases.
* Updated `.qa-state.json` transitioning to `AUTOMATION_IMPLEMENTATION`.

## 6. Failure Handling
* If file is unreadable, corrupted, or missing required columns: report exact column error and request user to upload a compliant file.
* If 0 test cases are marked `Automation Ready = Yes`: halt and notify the user that no cases were selected for automation.

## 7. Human Approval Requirements
* **Mandatory Gate 2 Enforcement:**
  * Bắt buộc có đối tượng `approval` hợp lệ gắn trực tiếp với SHA-256 hash của workbook đã duyệt:
    ```json
    {
      "approval": {
        "approved": true,
        "approved_at": "<ISO-8601>",
        "approved_by": "human",
        "artifact_hash": "<SHA-256 workbook>"
      }
    }
    ```
  * Lệnh ghi nhận phê duyệt: `python scripts/state_manager.py approve --workbook <path_to_excel> --by human`
  * Chuyển trạng thái: `python scripts/state_manager.py transition AUTOMATION_IMPLEMENTATION --approval-token <user_token>`
  * **Cơ chế khóa an toàn:** Hệ thống kiểm tra hash SHA-256 thực tế của file `.xlsx` trên đĩa. Không chấp nhận approval thiếu hash hoặc hash không khớp. Nếu workbook bị chỉnh sửa sau approval, hash mismatch sẽ ngay lập tức chặn transition sang `AUTOMATION_IMPLEMENTATION`.

## 8. Completion Criteria
* At least one validated test case marked `Automation Ready = Yes`.
* State is `AUTOMATION_IMPLEMENTATION`.
