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
  * `references/business-terminology-guide.md`

## 3. Prerequisites
* Module context and business flow are mapped without unresolved critical contradictions.

## 4. Step-by-step Execution Instructions
1. **Phân bổ Số lượng Test Case theo Ma trận Rủi ro (Target Quotas - Không Cắt Giảm):**
   * **Nhóm Mức độ Nặng / Chặn (`Chặn` — 7 đến 10 test cases):**
     * Luồng chính (Happy Path) không thể thiếu.
     * Crash, White screen of death, lỗi 500 không phục hồi.
     * Kẹt luồng bắt buộc (không đăng nhập được, không thanh toán được, không lưu được dữ liệu).
     * Phá vỡ bảo mật, phân quyền, lộ dữ liệu nhạy cảm (PII), mất mát dữ liệu (data loss).
     * Giới hạn tần suất và khoá tài khoản oan khi mạng lag / spam click.
   * **Nhóm Mức độ Sai (`Sai` — 5 đến 7 test cases):**
     * Tính toán sai lệch công thức (tiền tệ, thuế, ngày phép, công làm việc).
     * Lưu trữ sai trạng thái CSDL hoặc hiển thị sai badge/nhãn.
     * Điều hướng sai màn hình (URL quay lại sau login không đúng).
     * Vi phạm quy tắc validation dữ liệu (chuỗi rỗng, vượt quá giới hạn ký tự, định dạng email/SĐT sai).
   * **Nhóm Mức độ Nhỏ (`Nhỏ`):**
     * Bổ sung thêm nếu phân hệ có các yêu cầu đặc thù về UI/UX, chính tả, hoặc i18n đa ngôn ngữ.

2. **Tiêu Chuẩn Soạn Thảo Nghiệp Vụ Dễ Hiểu Cho Người Non-IT (BẮT BUỘC):**
   > [!IMPORTANT]
   > **TUÂN THỦ CẨM NANG: `references/business-terminology-guide.md`**  
   > Người không chuyên IT (Tester thủ công, BA, PO, người dùng nghiệp vụ) đọc vào phải **hiểu ngay mục đích** và **tự thao tác làm theo được từng bước trên màn hình**, trong khi **giữ nguyên 100% số lượng ca test (7-10 Chặn, 5-7 Sai)**.
   * **Nghiêm cấm từ dịch máy ngô nghê & biệt ngữ IT nội bộ:**
     * Tuyệt đối KHÔNG dùng các từ: *"Phanh chống ngập"*, *"Chặn âm thầm"*, *"Dùng vai trò web_anon"*, *"Gọi RPC"*, *"UI trả về"*, *"DB không chèn dòng"*, *"insufficient_privilege"*, *"bắn payload"*, *"bắt hook"*.
     * Thay thế bằng tiếng Việt nghiệp vụ chuẩn:
       - *"Phanh chống ngập / Rate limit"* $\rightarrow$ *"Giới hạn số lần gửi yêu cầu / Chặn spam liên tục"*.
       - *"Chặn âm thầm"* $\rightarrow$ *"Hiển thị thông báo thành công chung để bảo mật, nhưng không tạo yêu cầu mới"*.
       - *"UI trả về thông báo"* $\rightarrow$ *"Màn hình hiển thị thông báo: ..."*.
       - *"DB không chèn dòng"* $\rightarrow$ *"Hệ thống dữ liệu không tạo mới bản ghi"*.
       - *"Khách vãng lai web_anon gọi RPC"* $\rightarrow$ *"Người dùng chưa đăng nhập thực hiện thao tác"*.
       - *"insufficient_privilege"* $\rightarrow$ *"Hệ thống từ chối và báo lỗi không có quyền truy cập"*.
   * **Các bước thực hiện (Test Steps) phải làm theo được trên màn hình:**
     * Viết tuần tự: `1. Mở màn hình...`, `2. Nhập vào ô [Tên ô] giá trị...`, `3. Bấm nút [Tên nút]...`, `4. Quan sát...`.
     * Nếu có kiểm tra CSDL/API ngầm: tách riêng vế trên màn hình và vế hệ thống dữ liệu.
   * **Kết quả kỳ vọng (Expected Result) phân định 2 tầng:**
     * *Tầng 1 (Giao diện người dùng):* Người dùng nhìn thấy thông báo gì, nút bấm đổi màu/trạng thái ra sao.
     * *Tầng 2 (Hệ thống dữ liệu ngầm - nếu có):* Trạng thái bản ghi trong hệ thống quản trị.

3. **Populate Required Columns for Each Case:**
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

4. **Kiểm Soát Truy Vết Yêu Cầu 2 Chiều & Chống Trùng Lặp (Traceability & Deduplication):**
   * **Kiểm tra Bao phủ Chiều Xuôi (Forward Traceability):** Rà soát toàn bộ các yêu cầu trọng yếu, quy tắc xác thực và luồng nghiệp vụ đã trích xuất trong `module-context.md`. Đảm bảo mỗi yêu cầu quan trọng phải có ít nhất MỘT test case tương ứng. Tuyệt đối không để sót yêu cầu trọng yếu mà không có kiểm thử (Orphan Requirements = 0).
   * **Kiểm tra Căn cứ Chiều Ngược (Backward Grounding Traceability):** Mọi test case bắt buộc phải điền cột `Requirement Reference` cụ thể, trỏ chính xác về mã đặc tả (ví dụ: `SPEC-AU-01`, `BR§2.1`) hoặc hàm/symbol/endpoint từ source code phát hiện bởi Graphify (ví dụ: `useSubmitOnce`, `POST /api/login`). Nghiêm cấm các test case ảo tưởng (Hallucinated / Orphan Test Cases) không có căn cứ từ code hay tài liệu.
   * **Kiểm tra Chống Trùng Lặp Mục Tiêu (Deduplication Check):** Rà soát đối chiếu toàn bộ danh sách. Nghiêm cấm tạo ra các test case trùng lặp về mục tiêu kiểm thử, thao tác các bước giống hệt nhau trên cùng tiền điều kiện mà không bổ sung thêm giá trị rủi ro hay giá trị biên.

5. **Draft Coverage Summary & Uncovered Risks:**
   * Document what is tested across the Nặng (7-10) and Sai (5-7) tiers, and what remains outside the scope.

6. **Transition Workflow State:**
   * Invoke: `python scripts/state_manager.py transition TESTCASE_REVIEW "Generated risk-based test cases (7-10 Chặn, 5-7 Sai) with 100% Traceability and Non-IT Friendly Wording"`.

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
