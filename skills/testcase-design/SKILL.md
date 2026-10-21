---
name: testcase-design
description: >-
  Designs a prioritized, dynamic risk-based test suite (RBC) scaled to module complexity tiers
  (Tier S: 5–8, Tier M: 10–18, Tier L: 18–30+). Employs non-IT accessible business wording,
  100% bidirectional traceability, and separates defect Severity from test execution Priority.
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
  * `references/risk-based-coverage-matrix.md`
  * `references/testcase-quality-checklist.md`
  * `references/business-terminology-guide.md`

## 3. Prerequisites
* Module context and business flow are mapped without unresolved critical contradictions.

## 4. Step-by-step Execution Instructions
1. **Phân Bổ Test Case Theo Ma Trận Độ Phủ Rủi Ro Động (Dynamic Risk-Based Coverage - RBC):**
   * > [!IMPORTANT]
   * > **KHÔNG ÁP DỤNG QUOTA CỐ ĐỊNH:** Tuyệt đối không ép buộc số lượng test case cứng nhắc (như 15 hay 20 ca cố định).  
   * > Số lượng và cơ cấu test case được xác định linh hoạt dựa trên **Quy mô Phân hệ (Module Tier)** và **Điểm số Rủi ro (Risk = Impact × Probability)** theo `references/risk-based-coverage-matrix.md`:
   * **Nhận diện Cấp độ Phân hệ (Module Tier):**
     * **Tier S (Đơn giản — 5 đến 8 test cases):** Form 1 bước, đổi mật khẩu đơn giản, tra cứu danh mục, cập nhật thông tin cá nhân cơ bản. *Nghiêm cấm bịa thêm case thừa thãi để "đủ chỉ tiêu"*.
     * **Tier M (Tiêu chuẩn — 10 đến 18 test cases):** Đăng nhập/Đăng ký đa kênh, Quản lý đơn từ, Xếp ca làm việc, Đặt phòng họp, Throttling và chống spam.
     * **Tier L (Phức tạp / Trọng yếu — 18 đến 30+ test cases):** Cổng thanh toán, Bảng tính lương & thuế, Luồng duyệt đơn đa cấp, Bảo mật phiên làm việc & phân quyền dữ liệu nhạy cảm.
   * **Phân định rõ vai trò của Severity (Mức độ nghiêm trọng):**
     * `Severity` phản ánh **mức độ tác động tiêu cực của lỗi khi nó xảy ra** (`Chặn`: crash/mất dữ liệu/bế tắc luồng; `Sai`: sai tính toán/sai trạng thái/vi phạm validation; `Nhỏ`: giao diện/câu chữ), **KHÔNG PHẢI chỉ tiêu số lượng cần tạo**.
   * **Chấm điểm rủi ro & Ưu tiên thực thi (Risk Priority):**
     * **P0 (Critical Path / Rủi ro cao):** Happy Path sống còn, bảo mật, crash, mất dữ liệu, tính toán tài chính.
     * **P1 (High):** Luồng biên quan trọng, validation dữ liệu phức tạp, điều hướng màn hình.
     * **P2 (Normal / Low):** Lỗi giao diện, định dạng phụ, kịch bản hiếm gặp.

2. **Tiêu Chuẩn Soạn Thảo Nghiệp Vụ Dễ Hiểu Cho Người Non-IT (BẮT BUỘC):**
   > [!IMPORTANT]
   > **TUÂN THỦ CẨM NANG: `references/business-terminology-guide.md`**  
   > Người không chuyên IT (Tester thủ công, BA, PO, người dùng nghiệp vụ) đọc vào phải **hiểu ngay mục đích** và **tự thao tác làm theo được từng bước trên màn hình**, đồng thời bảo toàn độ sâu rủi ro kỹ thuật.
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
   * Document what is tested across the module risk tiers (Tier S, Tier M, or Tier L) and what remains outside the scope.

6. **Transition Workflow State:**
   * Invoke: `python scripts/state_manager.py transition TESTCASE_REVIEW "Generated dynamic risk-based test cases with 100% Traceability and Non-IT Friendly Wording"`.

## 5. Expected Outputs
* Structured test case dataset (JSON or Markdown) conforming to the 13-column schema tailored to the Module Tier (Tier S: 5–8, Tier M: 10–18, Tier L: 18–30+).
* Coverage summary metadata.
* Updated `.qa-state.json` transitioning to `TESTCASE_REVIEW`.

## 6. Failure Handling
* If test cases cannot be generated due to severe requirement uncertainty: return to Step 2 and formulate targeted gap questions.

## 7. Human Approval Requirements
* Handed off to `testcase-review-export` for formatting and human review checkpoint.

## 8. Completion Criteria
* Đạt tiêu chuẩn ma trận độ phủ rủi ro (RBC) tương ứng với quy mô phân hệ (Tier S: 5–8 ca, Tier M: 10–18 ca, Tier L: 18–30+ ca) và 100% Traceability.
* State is `TESTCASE_REVIEW`.
