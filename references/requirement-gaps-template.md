# BÁO CÁO ĐIỀU TRA ĐIỂM BẤT CẬP & PHIẾU LÀM RÕ NGHIỆP VỤ (KÈM MINH CHỨNG GIAO DIỆN)
## Phân hệ: [Tên Phân Hệ] (Module: [ModuleName])

> **Thời điểm lập:** [YYYY-MM-DD HH:MM:SS]  
> **Trạng thái:** `WAITING_FOR_REQUIREMENT_CLARIFICATION`  
> **Công cụ xác minh:** Graphify AST (Mã nguồn) & Playwright MCP (Kiểm chứng UI thực tế)  
> **Tài liệu đối soát:** [Tên tài liệu đặc tả hoặc 'Không có tài liệu, đối soát trực tiếp từ code']

---

## 1. TỔNG QUAN KẾT QUẢ ĐIỀU TRA & XÁC MINH GIAO DIỆN

* **Tổng số vấn đề phát hiện:** `[N]` kẽ hở / điểm bất cập nghiệp vụ.
* **Tình trạng xác minh thực tế qua Playwright MCP:**
  - `[X]` vấn đề đã xác minh và chụp ảnh giao diện thực tế.
  - `[Y]` vấn đề thuộc tầng logic backend ngầm (đối soát qua mã nguồn AST).
* **Mức độ rủi ro:**
  - `[R1]` vấn đề rủi ro cao (ảnh hưởng đến luồng chính, bảo mật, hoặc toàn vẹn dữ liệu).
  - `[R2]` vấn đề mơ hồ nghiệp vụ cần BA/PO chốt phương án.
  - `[R3]` vấn đề nghi ngờ là lỗi triển khai (Potential Defect).

---

## 2. PHÂN LOẠI CHI TIẾT 5 NHÓM ĐIỂM BẤT CẬP

| Mã Vấn Đề (Issue ID) | Phân Loại Kẽ Hở | Luồng Nghiệp Vụ Liên Quan | Bằng Chứng Mã Nguồn (AST) | Xác Minh Giao Diện (Playwright MCP) | Mức Độ Rủi Ro |
| :---: | :--- | :--- | :--- | :---: | :---: |
| **GAP-001** | Mơ hồ yêu cầu *(Requirement Ambiguity)* | [Luồng ảnh hưởng] | File: `path/to/file.ts#L45-L60`<br>Symbol: `functionName` | Đã chụp ảnh minh chứng | Cao |
| **GAP-002** | Nghi ngờ lỗi code *(Potential Defect)* | [Luồng ảnh hưởng] | File: `path/to/service.ts#L102`<br>Symbol: `validator` | Đã chụp ảnh lỗi màn hình | Cao |
| **GAP-003** | Thiếu tài liệu *(Missing Documentation)* | [Luồng ảnh hưởng] | File: `path/to/hook.ts`<br>Symbol: `useSubmitOnce` | Logic ngầm client-side | Thấp |

---

## 3. PHIẾU LÀM RÕ NGHIỆP VỤ CHO BA / PO (KÈM BẰNG CHỨNG HÌNH ẢNH & BƯỚC TÁI HIỆN)

### Chi Tiết Từng Điểm Bất Cập:

#### Điểm Bất Cập [GAP-001]: [Tên ngắn gọn vấn đề]
* **Luồng liên quan:** [Tên luồng, ví dụ: Đăng nhập / Khóa tài khoản]
* **Mức độ rủi ro:** Cao / Trung bình / Thấp
* **Bằng chứng mã nguồn (AST Evidence):**
  - *Tệp & Vị trí:* `src/features/auth/useLogin.ts#L45`
  - *Cài đặt thực tế:* `LOGIN_THROTTLE.MAX_ATTEMPTS = 5` (Chưa có logic tự giải phóng phiên).
  - *Tài liệu đặc tả:* Tài liệu không ghi rõ thời gian khóa bao lâu hoặc do admin mở.
* **Các bước tái hiện trên giao diện (UI Reproduction Steps):**
  1. Mở trang `/dang-nhap?web=thu`.
  2. Chọn Tab 'Mã nhân viên', nhập mã `VG000101` và mật khẩu sai liên tục 5 lần.
  3. Bấm nút 'Đăng nhập' ở lần thứ 5.
* **Ảnh chụp minh chứng thực tế từ Playwright MCP:**
  > ![Ảnh chụp minh chứng GAP-001](./screenshots/GAP-001-evidence.png)
  > *(Đường dẫn: [GAP-001-evidence.png](./screenshots/GAP-001-evidence.png))*
* **Hành vi quan sát được trên màn hình (Observed UI Behavior):**
  - Màn hình hiển thị thông báo lỗi: `Tài khoản tạm thời bị khóa do nhập sai nhiều lần.`
  - Nút đăng nhập bị vô hiệu hóa nhưng không có đồng hồ đếm ngược hay hướng dẫn mở lại.
* **Tác động nghiệp vụ:** Người dùng thật bị khóa tài khoản sẽ không biết phải chờ bao lâu hay liên hệ ai để mở khóa.
* **Câu hỏi đối soát cho BA / PO:** **"[Tài khoản bị khóa sau 5 lần nhập sai sẽ tự mở sau bao lâu, hay cần quản trị viên mở thủ công]?"**
* **Các phương án đề xuất:**
  - **Phương án A:** Khóa tạm 15 phút, sau 15 phút tự mở khóa.
  - **Phương án B:** Khóa cứng, bắt buộc liên hệ HR/Admin để reset trạng thái.
* **Ý kiến phản hồi từ BA / Người dùng:** `[Chờ người dùng / BA giải đáp hoặc duyệt phương án]`

---

## 4. HƯỚNG DẪN DÀNH CHO NGƯỜI DÙNG TẠI ĐIỂM DỪNG 1 (HUMAN GATE 1)

> [!IMPORTANT]
> **HỆ THỐNG ĐANG TẠM DỪNG TẠI ĐÂY.**  
> AI tuyệt đối không tự ý viết test case tiếp theo khi chưa có sự xác nhận của bạn.

Vui lòng xem xét các điểm bất cập và ảnh chụp màn hình minh chứng ở trên:
* **Nếu bạn đồng ý với hiện trạng hoặc muốn tiếp tục thiết kế test case:**  
  > Hãy gửi tin nhắn: **`tiếp tục`** (hoặc **`proceed`**). Hệ thống sẽ chuyển sang Bước 4 (Thiết kế Test Case).
* **Nếu bạn có câu trả lời cụ thể từ BA / PO:**  
  > Hãy gửi tin nhắn theo cú pháp:  
  > **`Trả lời GAP-001: Chọn Phương án A`** (hoặc nội dung quy định thực tế). AI sẽ cập nhật quy tắc nghiệp vụ vào hệ thống rồi tiếp tục.
