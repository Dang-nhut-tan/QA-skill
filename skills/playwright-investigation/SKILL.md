---
name: playwright-investigation
description: >-
  Verifies discovered requirement gaps and ambiguous behaviors directly on the live UI using Playwright MCP.
  Executes reproduction steps, captures screenshot evidence, and embeds visual proof into the BA clarification ticket
  before halting at Human Gate 1 for user confirmation to proceed.
---

# Skill: Playwright UI Verification & Gap Evidence Capture (Step 3)

## 1. Description & Trigger Conditions
* **Purpose:** Proactively verify on the actual web interface whether the requirement gaps and potential defects identified in Step 2 (`requirement-gap-analysis`) actually occur. Execute step-by-step reproduction, capture high-resolution screenshot evidence, and embed them into the BA Clarification Ticket (`<module-name>-gaps.md`) so that stakeholders can effortlessly understand and reproduce the issues.
* **Triggers:**
  * Discovered points of discrepancy (gaps) from `requirement-gap-analysis`.
  * State transitions from `GAP_ANALYSIS` $\rightarrow$ `RUNTIME_INVESTIGATION`.

## 2. Inputs
* **Required:**
  * Target module URL / route and environment credentials.
  * List of identified `clarification_issues` (`GAP-xxx`) from Step 2.
  * `module-context.md` from Step 1.

## 3. Prerequisites
* **Playwright MCP** server configured and operational.
* Target web application running and accessible (local dev server or staging).

## 4. Step-by-Step Execution Instructions

### 4.1. Identify Observable UI Gaps
* Lọc danh sách các điểm bất cập từ Step 2 để xác định các ca có thể kiểm chứng trên giao diện (ví dụ: validation form, thông báo lỗi, nút bấm bị khóa, modal cảnh báo, chuyển tab, redirect).
* Đối với các vấn đề backend thuần túy (không có giao diện): Ghi chú rõ `[Xác minh bằng AST - Không có giao diện trực quan]`.

### 4.2. Execute Live UI Reproduction & Capture Screenshots
* Với từng điểm bất cập có giao diện:
  1. **Điều hướng:** Dùng `browser_navigate` mở trang tương ứng.
  2. **Thao tác tái hiện:** Thực hiện các bước cụ thể để tái hiện tình huống bất cập (ví dụ: nhập sai 5 lần, để trống trường bắt buộc, bấm liên tiếp nhiều lần).
  3. **Chụp ảnh minh chứng:** Dùng `browser_take_screenshot` chụp lại màn hình ngay tại thời điểm xuất hiện lỗi hoặc trạng thái bất thường.
  4. **Lưu trữ:** Đặt tên tệp theo quy chuẩn: `screenshots/<IssueID>-evidence.png` (ví dụ: `screenshots/GAP-001-evidence.png`).
  5. **Ghi lại các bước tái hiện:** Mô tả chi tiết các bước từ góc nhìn người dùng:
     - `1. Mở trang...`
     - `2. Thao tác trên ô...`
     - `3. Quan sát kết quả...`

### 4.3. Epistemic Restriction (Cảnh báo nhận thức)
> [!WARNING]
> Playwright MCP chỉ ghi nhận **GIAO DIỆN HIỆN TẠI ĐANG CHẠY THẾ NÀO**, không tự động coi hành vi đó là **NGHIỆP VỤ ĐÚNG**. Mọi hành vi cần có sự đối soát và phê duyệt từ BA/PO hoặc người dùng.

### 4.4. Embed Visual Proof into BA Ticket (`<module-name>-gaps.md`)
* Nhúng trực tiếp đường dẫn ảnh chụp màn hình và các bước tái hiện vào từng thẻ `GAP-xxx` trong `<module-name>-gaps.md`.
* Xuất báo cáo chi tiết và đăng ký tệp artifact:
  `python scripts/state_manager.py set-artifact gap_analysis <module-name>-gaps.md`

### 4.5. Transition to Mandatory Human Gate 1 & HALT EXECUTION
* Cập nhật trạng thái workflow sang điểm dừng phê duyệt:
  `python scripts/state_manager.py transition WAITING_FOR_REQUIREMENT_CLARIFICATION "Verified gaps on UI with screenshots. Halting for user proceed command"`
* **DỪNG LẠI HOÀN TOÀN TẠI ĐÂY.**

### 4.6. Resumption Protocol (Khi người dùng phản hồi)
* **Trường hợp 1 — Người dùng bảo "tiếp tục":**
  - Khi người dùng nhắn `"tiếp tục"`, `"ok tiếp tục"`, hoặc `"proceed"`:
  - Hệ thống ghi nhận xác nhận, chuyển trạng thái sang `TESTCASE_GENERATION` và bắt đầu Bước 4 (Thiết kế Test Case).
* **Trường hợp 2 — Người dùng cung cấp câu trả lời từ BA/PO:**
  - Cập nhật quy tắc nghiệp vụ đã làm rõ vào `module-context.md`.
  - Đánh dấu `status: "Answered"` cho các mã GAP tương ứng.
  - Chuyển trạng thái sang `TESTCASE_GENERATION` để thiết kế test case chuẩn xác theo nghiệp vụ mới chốt.

## 5. Expected Outputs
* Thư mục `screenshots/` chứa các ảnh chụp minh chứng: `screenshots/<IssueID>-evidence.png`.
* Tệp phiếu làm rõ hoàn chỉnh `<module-name>-gaps.md` có đầy đủ:
  - Bằng chứng mã nguồn AST.
  - Các bước tái hiện chi tiết trên UI.
  - Ảnh chụp màn hình minh chứng thực tế từ Playwright MCP.
  - Câu hỏi và phương án đề xuất cho BA/PO.
* Trạng thái workflow được đặt thành `WAITING_FOR_REQUIREMENT_CLARIFICATION`.
* Đường link tệp báo cáo và bảng tóm tắt kèm ảnh minh chứng được hiển thị trực tiếp trong đoạn chat.

## 6. Failure Handling
* Nếu môi trường web không truy cập được hoặc Playwright MCP gặp lỗi: Báo cáo rõ trở ngại môi trường, đánh dấu `[UNABLE_TO_VERIFY_UI]` và giữ nguyên bằng chứng mã nguồn AST trong phiếu BA; không bịa đặt ảnh chụp.

## 7. Completion Criteria
* Toàn bộ điểm bất cập quan sát được trên UI đều đã được kiểm chứng và có ảnh chụp màn hình kèm các bước tái hiện.
* Phiếu làm rõ `<module-name>-gaps.md` đã hoàn tất và giao cho người dùng.
* **Hệ thống đã dừng lại và chỉ tiếp tục sang Bước 4 khi người dùng bảo "tiếp tục" hoặc cung cấp câu trả lời.**
