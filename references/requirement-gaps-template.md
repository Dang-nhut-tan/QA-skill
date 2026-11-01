# BÁO CÁO ĐIỀU TRA ĐIỂM BẤT CẬP & XÁC MINH HÀNG RÀO AN TOÀN NGHIỆP VỤ
## Phân hệ: [Tên Phân Hệ] (Module: [ModuleName])

> **Thời điểm lập:** [YYYY-MM-DD HH:MM:SS]  
> **Trạng thái:** `WAITING_FOR_REQUIREMENT_CLARIFICATION`  
> **Công cụ xác minh:** CodeGraph AST (Mã nguồn) & Playwright MCP (Kiểm chứng UI thực tế)  
> **Tài liệu đối soát:** [Tên tài liệu đặc tả hoặc 'Không có tài liệu, đối soát trực tiếp từ code']

---

## 1. TỔNG QUAN KẾT QUẢ ĐIỀU TRA & XÁC MINH GIAO DIỆN

* **Tổng số bất cập/kẽ hở thực tế (True GAPs):** `[N]` điểm bất cập (Cần BA/PO làm rõ). Nếu hệ thống chạy chuẩn 100%, ghi `0` điểm bất cập.
* **Tổng số hàng rào an toàn đã kiểm chứng (Verified Guards):** `[M]` cơ chế bảo vệ phân quyền/nghiệp vụ hoạt động chuẩn xác (Đạt - PASS).
* **Tình trạng xác minh thực tế qua Playwright MCP:**
  - `[X]` kịch bản kiểm chứng có ảnh chụp minh chứng trực quan (Trước $\rightarrow$ Sau thao tác).
  - `[Y]` quy tắc backend ngầm đối soát qua AST mã nguồn.
* **Phân bổ rủi ro thực tế:**
  - Chỉ tính điểm bất cập thực sự (True GAPs) vào phân bổ rủi ro. Các hàng rào bảo vệ đã hoạt động chuẩn (Verified Guards) được tính là **ĐẠT (PASS)**, tuyệt đối không tính là Blocker hay Bug.

---

## 2. BẢNG TỔNG HỢP HÀNG RÀO AN TOÀN ĐÃ KIỂM CHỨNG (VERIFIED GUARDS - NẾU CÓ)
*(Dành cho các quy định phân quyền, chặn quyền trái thẩm quyền, tự duyệt đơn, giới hạn hạn mức... đã hoạt động chuẩn xác trên UI)*

| Mã Hàng Rào | Luồng Nghiệp Vụ Bảo Vệ | Bằng Chứng Mã Nguồn (AST) | Kết Quả UI Thực Tế (Playwright) | Đánh Giá An Toàn |
| :---: | :--- | :--- | :---: | :---: |
| **GUARD-001** | [Ví dụ: Phó quản lý không được duyệt đơn] | `Symbol: canApprove = false` | Nút Duyệt bị disabled, có thông báo phân quyền | **ĐẠT (PASS)** |
| **GUARD-002** | [Ví dụ: Chặn tự duyệt đơn cá nhân] | `Symbol: laDonCuaToi` | Ẩn hoàn toàn nút Duyệt ở tab Đơn cá nhân | **ĐẠT (PASS)** |

---

## 3. BẢNG PHÂN LOẠI ĐIỂM BẤT CẬP THỰC TẾ (TRUE GAPs - NẾU CÓ)
*(Chỉ ghi nhận khi có mâu thuẫn thực tế: tài liệu cấm nhưng UI cho làm, tài liệu thiếu gây mơ hồ, hoặc code bị crash/bug)*

| Mã Vấn Đề (Issue ID) | Phân Loại Kẽ Hở | Luồng Nghiệp Vụ Liên Quan | Bằng Chứng Mã Nguồn (AST) | Xác Minh Giao Diện (Playwright MCP) | Mức Độ Rủi Ro |
| :---: | :--- | :--- | :--- | :---: | :---: |
| **GAP-001** | Mơ hồ yêu cầu *(Requirement Ambiguity)* | [Luồng ảnh hưởng] | File: `path/to/file.ts#L45-L60` | Đã chụp ảnh minh chứng hành vi bất thường | Cao / Trung bình |
| **GAP-002** | Nghi ngờ lỗi code *(Potential Defect)* | [Luồng ảnh hưởng] | File: `path/to/service.ts#L102` | UI vi phạm quy định nghiệp vụ | Cao |

*(Nếu không phát hiện bất cập nào, ghi: `Không phát hiện điểm bất cập nào. Toàn bộ các luồng nghiệp vụ tuân thủ đúng quy định.`)*

---

## 4. CHI TIẾT TỪNG MỤC CẦN LÀM RÕ CHO BA / PO (KÈM BẰNG CHỨNG HÌNH ẢNH)

*(Trình bày chi tiết từng GAP-xxx nếu có, hoặc các khuyến nghị tối ưu hóa REC-xxx)*

---

## 5. HƯỚNG DẪN DÀNH CHO NGƯỜI DÙNG TẠI ĐIỂM DỪNG 1 (HUMAN GATE 1)

> [!IMPORTANT]
> **HỆ THỐNG ĐANG TẠM DỪNG TẠI ĐÂY.**  
> AI tuyệt đối không tự ý viết test case tiếp theo khi chưa có sự xác nhận của bạn.

* **Nếu đồng ý hoặc muốn tiếp tục:** Gửi tin nhắn: **`tiếp tục`** (hoặc **`proceed`**).
* **Nếu có câu trả lời từ BA/PO cho GAP:** Gửi tin nhắn: **`Trả lời GAP-xxx: Chọn Phương án A`**.
