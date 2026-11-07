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
| :---: | :--- | :--- | :--- | :---: |
| **GUARD-001** | [Ví dụ: Phó quản lý không được duyệt đơn] | `Symbol: canApprove = false` | Nút Duyệt bị disabled, có thông báo phân quyền | **ĐẠT (PASS)** |
| **GUARD-002** | [Ví dụ: Chặn tự duyệt đơn cá nhân] | `Symbol: laDonCuaToi` | Ẩn hoàn toàn nút Duyệt ở tab Đơn cá nhân | **ĐẠT (PASS)** |

---

## 3. BẢNG PHÂN LOẠI ĐIỂM BẤT CẬP THỰC TẾ (TRUE GAPs - NẾU CÓ)
*(Chỉ ghi nhận khi có mâu thuẫn thực tế: tài liệu cấm nhưng UI cho làm, tài liệu thiếu gây mơ hồ, hoặc code bị crash/bug)*

| Mã Vấn Đề (Issue ID) | Phân Loại Kẽ Hở | Luồng Nghiệp Vụ | Bằng Chứng (AST) & UI | Ảnh Hưởng Trải Nghiệm (UX Impact) | Lỗi Tiềm Tàng / Rủi Ro Kỹ Thuật Tương Lai | Mức Độ Rủi Ro |
| :---: | :--- | :--- | :--- | :--- | :--- | :---: |
| **GAP-001** | Mơ hồ yêu cầu *(Requirement Ambiguity)* | [Luồng ảnh hưởng] | File: `path/to/file.ts#L45-L60` | [Mô tả cảm giác bối rối, nhầm lẫn, mất phản hồi của người dùng] | [Nguy cơ lỗi concurrency, sai lệch dữ liệu DB, vỡ báo cáo] | Cao / Trung bình |
| **GAP-002** | Nghi ngờ lỗi code *(Potential Defect)* | [Luồng ảnh hưởng] | File: `path/to/service.ts#L102` | [Thao tác bị chặn đứng hoặc hiển thị thông báo lỗi sai lệch] | [Lỗ hổng bảo mật, rò rỉ token, hoặc crash server khi tải cao] | Cao |

*(Nếu không phát hiện bất cập nào, ghi: `Không phát hiện điểm bất cập nào. Toàn bộ các luồng nghiệp vụ tuân thủ đúng quy định.`)*

---

## 4. CHI TIẾT TỪNG MỤC CẦN LÀM RÕ CHO BA / PO (KÈM BẰNG CHỨNG HÌNH ẢNH & ĐÁNH GIÁ TÁC ĐỘNG KÉP)

### [GAP-001]: [Tiêu Đề Điểm Bất Cập / Kẽ Hở]
* **Phân loại:** [Requirement Ambiguity / Potential Defect / Missing Documentation / Confirmed Defect]
* **Luồng nghiệp vụ liên quan:** [Tên chức năng / luồng người dùng]
* **Mức độ rủi ro:** [Chặn (Blocker) / Sai (Major) / Nhỏ (Minor)]

#### 1. Bằng chứng Mã nguồn (AST) & Đối soát Đặc tả
* **Vị trí code:** [`path/to/file.ts#L45-L60`](file:///path/to/file.ts#L45-L60)
* **Hiện trạng trong mã nguồn:** [Trích xuất đoạn code hoặc logic xử lý hiện tại]
* **Đặc tả nghiệp vụ:** [Trích dẫn tài liệu yêu cầu hoặc ghi nhận 'Tài liệu không đề cập']

#### 2. Ảnh hưởng Trải nghiệm Người dùng (UX Impact)
* **Trở ngại thao tác (Operational Friction):** [Mô tả cụ thể: Người dùng nhìn thấy gì, bối rối ở đâu? Thông báo trên màn hình có bị thiếu, khó hiểu hoặc gây hiểu lầm không?]
* **Bẫy hành vi (Behavioral Traps):** [Người dùng có tưởng rằng hành động đã hoàn tất (như đã duyệt, đã chấm công) trong khi hệ thống chưa lưu? Có nguy cơ bấm liên tiếp nhiều lần (double submit) hoặc nhập sai dữ liệu không?]
* **Tác động niềm tin:** [Giao diện có tạo cảm giác ứng dụng bị đơ, lag hoặc thiếu chuyên nghiệp không?]

#### 3. Lỗi Tiềm Tàng & Rủi Ro Kỹ Thuật Tương Lai (Future Technical Risks & Potential Defects)
* **Sai lệch & Xung đột Dữ liệu (Data Corruption / Inconsistency):** [Nếu bỏ qua không sửa, dữ liệu trong cơ sở dữ liệu sẽ bị sai lệch, mồ côi (orphaned records), hoặc mất đồng bộ giữa các bảng như thế nào?]
* **Rủi ro Đồng thời (Concurrency & Race Conditions):** [Khi nhiều người cùng thao tác lúc cao điểm (peak traffic) hoặc khi chạy đa worker song song, hệ thống có bị deadlock hay ghi đè dữ liệu không?]
* **Ảnh hưởng dây chuyền (Cascading Downstream Failures):** [Các module hạ tầng sau này (bảng lương, báo cáo tài chính/thống kê tháng, webhook đồng bộ bên thứ 3) sẽ bị tính toán sai hoặc crash ra sao?]
* **Rủi ro An toàn & Tuân thủ:** [Có nguy cơ bị vượt quyền, thiếu log kiểm toán (audit trail), hoặc vi phạm chính sách bảo mật không?]

#### 4. Kiểm chứng Giao diện Thực tế (Playwright MCP)
* **Các bước tái hiện (End-User Reproduction Steps):**
  1. *Bước 1:* Mở màn hình `[URL / Đường dẫn]`.
  2. *Bước 2:* Thao tác `[Hành động người dùng]`.
  3. *Bước 3:* Quan sát hiện tượng bất thường.
* **Hình ảnh minh chứng trực quan:**
  - *Trước thao tác (Input):* `![Trạng thái nhập liệu](screenshots/GAP-001-01-input.png)`
  - *Sau thao tác / Hiện tượng bất cập:* `![Kết quả bất thường](screenshots/GAP-001-02-result.png)`

#### 5. Câu hỏi Làm rõ dành cho BA / PO & Đề xuất Phương án
* **Câu hỏi cốt lõi:** *"[Câu hỏi rõ ràng, trung lập dành cho BA/PO]"*
* **Phương án A (Khuyến nghị):** [Giải pháp chuẩn ngành, an toàn dữ liệu và tối ưu UX]
* **Phương án B:** [Giải pháp giữ nguyên logic code hiện tại, bổ sung thông báo rõ ràng cho người dùng]
* **Phương án C:** [Giải pháp nghiệp vụ tùy chỉnh khác]

---

## 5. HƯỚNG DẪN DÀNH CHO NGƯỜI DÙNG TẠI ĐIỂM DỪNG 1 (HUMAN GATE 1)

> [!IMPORTANT]
> **HỆ THỐNG ĐANG TẠM DỪNG TẠI ĐÂY.**  
> AI tuyệt đối không tự ý viết test case tiếp theo khi chưa có sự xác nhận của bạn.

* **Nếu đồng ý hoặc muốn tiếp tục:** Gửi tin nhắn: **`tiếp tục`** (hoặc **`proceed`**).
* **Nếu có câu trả lời từ BA/PO cho GAP:** Gửi tin nhắn: **`Trả lời GAP-xxx: Chọn Phương án A`**.
