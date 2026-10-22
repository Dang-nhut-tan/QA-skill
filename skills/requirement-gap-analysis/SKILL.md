---
name: requirement-gap-analysis
description: >-
  Analyzes inconsistencies, missing business rules, and contradictions between code and specifications.
  Produces a structured BA/PO clarification question report and enforces a mandatory workflow STOP
  for human direction (Provide answers vs. Investigate via Playwright MCP).
---

# Skill: Requirement Gap Analysis (Step 2)

## 1. Description & Trigger Conditions
* **Purpose:** Audit the reconstructed context against available requirements, identify ambiguities and potential defects, formulate high-impact BA/PO questions, and **halt execution for human decision**.
* **Triggers:**
  * Completed `graphify-context-discovery`.
  * State is `GAP_ANALYSIS`.

## 2. Inputs
* **Required:**
  * `module-context.md` from Step 1.
  * Project documents or specifications (if available).
  * `.qa-state.json`.

## 3. Prerequisites
* Source code context and dependencies have been mapped.

## 4. Step-by-step Execution Instructions
1. **Discrepancy & Ambiguity Audit:**
   * Compare documented rules against code AST implementations.
   * Categorize findings into 5 distinct categories:
     1. `Requirement Ambiguity`: Unspecified behavior (e.g., lockout duration not defined).
     2. `Potential Implementation Defect`: Code exhibits suspicious logic or unhandled edge cases.
     3. `Missing Documentation`: Feature exists in code but has zero written specification.
     4. `Environment / Test Data Limitation`: Feature requires external SMS/email gateway or hardware.
     5. `Confirmed Defect`: Clear breach of explicit documented business rule.
2. **Formulate BA/PO Clarification Table:**
   * Create prioritized table with columns:
     * `Issue ID` (e.g. `GAP-001`)
     * `Related Flow`
     * `Current Evidence` (Code references & lines)
     * `Uncertainty`
     * `Business Impact`
     * `Question for BA/PO`
     * `Suggested Options` (Hypotheses A, B, C)
     * `Status` (`Pending`)
3. **Trigger Playwright MCP UI Verification & Screenshot Capture (Step 3 Integration):**
   * **Bắt buộc kiểm chứng giao diện trước khi gửi phiếu BA:**
     - Đối với mọi điểm bất cập có thể kiểm chứng được qua giao diện web:
     - Kích hoạt kỹ năng `playwright-investigation` để điều hướng đến màn hình thực tế.
     - Thực hiện các bước thao tác để kiểm tra xem vấn đề có xuất hiện trên màn hình hay không.
     - **Chụp ảnh màn hình minh chứng (`.png`)** lưu vào thư mục `screenshots/` (ví dụ: `GAP-001-evidence.png`).
     - Ghi chép chi tiết các bước tái hiện (Reproduction Steps: 1. Mở... 2. Nhập... 3. Quan sát...).
     - Nếu là logic ngầm backend không có UI: ghi rõ `[Xác minh qua mã nguồn AST - Không có giao diện trực quan]`.
4. **Generate Standalone Deliverable (`<module-name>-gaps.md`):**
   * Tạo tệp báo cáo hoàn chỉnh dựa trên `references/requirement-gaps-template.md`:
     - Tóm tắt tổng quan và phân loại 5 nhóm bất cập.
     - Từng phiếu câu hỏi cho BA được **đính kèm trực tiếp ảnh chụp màn hình minh chứng từ Playwright MCP** và các bước tái hiện rõ ràng.
     - Câu hỏi trực diện cho BA/PO và các phương án đề xuất (Phương án A, Phương án B).
5. **Persist State Checkpoint & Register Artifact:**
   * Lưu các vấn đề vào `.qa-state.json` dưới `clarification_issues`.
   * Đăng ký tệp báo cáo đã tạo:
     `python scripts/state_manager.py set-artifact gap_analysis <module-name>-gaps.md`
   * Cập nhật trạng thái workflow sang điểm dừng chờ người dùng:
     `python scripts/state_manager.py transition WAITING_FOR_REQUIREMENT_CLARIFICATION "Gaps verified via Playwright MCP with screenshots. Awaiting user confirmation to proceed"`

## 5. Mandatory Human Checkpoint 1 (DỪNG LẠI BẮT BUỘC)
> [!IMPORTANT]
> **AI PHẢI DỪNG LẠI HOÀN TOÀN TẠI ĐÂY.**
> Trước khi dừng lại, AI phải:
> 1. Gửi đường link tệp báo cáo phiếu BA kèm ảnh minh chứng: `[<module-name>-gaps.md](file:///path/to/<module-name>-gaps.md)`.
> 2. Hiển thị bảng tóm tắt trực tiếp trong chat gồm: Mã GAP, Phân loại, Luồng, Ảnh minh chứng, và Câu hỏi cho BA/PO.
> 3. **DỪNG LẠI CHỜ PHẢN HỒI:**
>    - **Khi người dùng nhắn "tiếp tục" (hoặc "proceed"):** AI mới được phép tiếp tục bước tiếp theo (`testcase-design`).
>    - **Nếu người dùng cung cấp câu trả lời giải đáp từ BA:** AI cập nhật quy tắc nghiệp vụ vào `module-context.md`, ghi nhận `Answered` và chuyển sang bước tiếp theo.
>
> **TUYỆT ĐỐI KHÔNG TỰ ĐỘNG CHUYỂN BƯỚC NẾU NGƯỜI DÙNG CHƯA BẢO "TIẾP TỤC" HOẶC CHƯA DUYỆT.**

## 6. Expected Outputs
* Dedicated Markdown file: `<module-name>-gaps.md` (or `requirement-gaps.md`) exported into workspace root following `references/requirement-gaps-template.md`.
* State file updated to `WAITING_FOR_REQUIREMENT_CLARIFICATION` with `artifacts.gap_analysis` pointing to the generated file.
* Executive table and clickable file link presented directly to the user in chat.

## 7. Failure Handling
* If zero gaps are found: double-check edge cases (boundary values, throttling, role permissions). If truly clean, document the verification criteria in `<module-name>-gaps.md` and request confirmation before proceeding.

## 8. Completion Criteria
* Standalone `<module-name>-gaps.md` report is created and registered in state.
* State is persisted as `WAITING_FOR_REQUIREMENT_CLARIFICATION`.
* Report link, executive summary table, and choices are displayed in chat.
* Execution is paused waiting for user input.
