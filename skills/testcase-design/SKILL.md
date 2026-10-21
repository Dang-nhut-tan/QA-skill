---
name: testcase-design
description: >-
  Designs a prioritized, risk-based test suite structured by severity quotas:
  7–10 test cases for Nặng (Chặn / Critical / Blocking) and 5–7 test cases for Sai (Incorrect / Functional).
  Covers critical paths, negative scenarios, validation boundaries, and data integrity.
---

# Skill: Risk-Based Test Case Design (Step 4)

## 1. Description & Trigger Conditions
* **Purpose:** Transform verified module context and requirement resolutions into a prioritized, high-leverage test suite with explicit severity quotas: **7–10 test cases cho mức độ Nặng (Chặn)** và **5–7 test cases cho mức độ Sai**.
* **Triggers:**
  * Completed `playwright-investigation` or clarification resolution.
  * State is `TESTCASE_GENERATION`.

## 2. Inputs
* **Required:**
  * Updated `module-context.md` (containing confirmed rules and unresolved gaps).
  * `.qa-state.json`.
* **References:**
  * `references/severity-guidelines.md`
  * `references/testcase-quality-checklist.md`

## 3. Prerequisites
* Module context and business flow are mapped without unresolved critical contradictions.

## 4. Step-by-step Execution Instructions
1. **Phân bổ Số lượng Test Case theo Ma trận Rủi ro (Target Quotas):**
   * **Nhóm Mức độ Nặng / Chặn (`Chặn` — 7 đến 10 test cases):**
     * Luồng chính (Happy Path) không thể thiếu.
     * Crash, White screen of death, lỗi 500 không phục hồi.
     * Kẹt luồng bắt buộc (không đăng nhập được, không thanh toán được, không lưu được dữ liệu).
     * Phá vỡ bảo mật, phân quyền, lộ dữ liệu nhạy cảm (PII), mất mát dữ liệu (data loss).
     * Throttling và khoá tài khoản oan khi mạng lag / spam click.
   * **Nhóm Mức độ Sai (`Sai` — 5 đến 7 test cases):**
     * Tính toán sai lệch công thức (tiền tệ, thuế, ngày phép, công làm việc).
     * Lưu trữ sai trạng thái CSDL hoặc hiển thị sai badge/nhãn.
     * Điều hướng sai màn hình (URL quay lại sau login không đúng).
     * Vi phạm quy tắc validation dữ liệu (chuỗi rỗng, vượt quá giới hạn ký tự, định dạng email/SĐT sai).
   * **Nhóm Mức độ Nhỏ (`Nhỏ`):**
     * Bổ sung thêm nếu phân hệ có các yêu cầu đặc thù về UI/UX, chính tả, hoặc i18n đa ngôn ngữ.

2. **Populate Required Columns for Each Case:**
   * **Test Case ID:** Unique, stable key (e.g. `TC-<MODULE>-001`).
   * **Module:** Module under test.
   * **Test Case Name:** Specific, actionable description.
   * **Preconditions:** Explicit initial state, auth status, DB record.
   * **Test Data:** Exact inputs or boundary payloads.
   * **Test Steps:** Numbered, reproducible actions (`1. ...\n2. ...`).
   * **Expected Result:** Clear, verifiable, measurable outcome.
   * **Severity:** Ghi chuẩn xác: `Chặn`, `Sai`, hoặc `Nhỏ`.
   * **Automation Ready:** `Yes` or `No`.
     * Strict Rule: Mark `Yes` ONLY if expected result is unambiguous, repeatable, test data is controllable, and objective assertion is possible.
   * **Automation Blocker:** Mandatory explanation if `Automation Ready = No`.
   * **Requirement Reference:** Code symbol or specification tag (e.g. `SPEC-AU-105`).
   * **Notes:** Assumptions, risks, or device dependencies.
   * **Status:** Trạng thái thực thi (`Pass`, `Fail`, `Pending`, `Skip`). Giá trị mặc định khi tạo mới luôn là `Pending`.

3. **Draft Coverage Summary & Uncovered Risks:**
   * Document what is tested across the Nặng (7-10) and Sai (5-7) tiers, and what remains outside the scope.

4. **Transition Workflow State:**
   * Invoke: `python scripts/state_manager.py transition TESTCASE_REVIEW "Generated risk-based test cases (7-10 Chặn, 5-7 Sai)"`.

## 5. Expected Outputs
* Structured test case dataset (JSON or Markdown) conforming to the 13-column schema with 7–10 Chặn and 5–7 Sai cases.
* Coverage summary metadata.
* Updated `.qa-state.json` transitioning to `TESTCASE_REVIEW`.

## 6. Failure Handling
* If test cases cannot be generated due to severe requirement uncertainty: return to Step 2 and formulate targeted gap questions.

## 7. Human Approval Requirements
* Handed off to `testcase-review-export` for formatting and human review checkpoint.

## 8. Completion Criteria
* Đạt chỉ tiêu phân bổ: 7–10 ca kiểm thử mức Chặn (Nặng) và 5–7 ca kiểm thử mức Sai.
* State is `TESTCASE_REVIEW`.
