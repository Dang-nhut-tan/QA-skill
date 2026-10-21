# BÁO CÁO ĐIỀU TRA ĐIỂM BẤT CẬP & KẼ HỞ NGHIỆP VỤ
## Phân hệ: [Tên Phân Hệ] (Module: [ModuleName])

> **Thời điểm lập:** [YYYY-MM-DD HH:MM:SS]  
> **Trạng thái:** `WAITING_FOR_REQUIREMENT_CLARIFICATION`  
> **Nguồn bằng chứng mã nguồn (AST):** Graphify AST Analysis  
> **Tài liệu đối soát:** [Tên tài liệu đặc tả hoặc 'Không có tài liệu, đối soát trực tiếp từ code']

---

## 1. TỔNG QUAN KẾT QUẢ ĐIỀU TRA

* **Tổng số vấn đề phát hiện:** `[N]` kẽ hở / điểm bất cập.
* **Mức độ rủi ro:**
  - `[X]` vấn đề có rủi ro cao (ảnh hưởng đến luồng chính, bảo mật hoặc tính toàn vẹn dữ liệu).
  - `[Y]` vấn đề mơ hồ nghiệp vụ cần xác nhận từ BA/PO.
  - `[Z]` vấn đề nghi ngờ là lỗi triển khai (Potential Defect).

---

## 2. PHÂN LOẠI CHI TIẾT 5 NHÓM ĐIỂM BẤT CẬP

| Mã Vấn Đề (Issue ID) | Phân Loại Kẽ Hở | Luồng Nghiệp Vụ Liên Quan | Bằng Chứng Thực Tế (Source Code / Spec) | Mức Độ Rủi Ro |
| :---: | :--- | :--- | :--- | :---: |
| **GAP-001** | Mơ hồ yêu cầu *(Requirement Ambiguity)* | [Luồng ảnh hưởng] | File: `path/to/file.ts#L45-L60`<br>Symbol: `functionName` | Cao / Trung bình |
| **GAP-002** | Nghi ngờ lỗi code *(Potential Defect)* | [Luồng ảnh hưởng] | File: `path/to/service.ts#L102`<br>Symbol: `validator` | Cao |
| **GAP-003** | Thiếu tài liệu *(Missing Documentation)* | [Luồng ảnh hưởng] | File: `path/to/hook.ts`<br>Symbol: `useSubmitOnce` | Thấp |

---

## 3. BẢNG CÂU HỎI ĐỐI SOÁT CHUYÊN SÂU DÀNH CHO BA / PRODUCT OWNER

### Chi Tiết Từng Điểm Bất Cập:

#### 🔹 Vấn đề [GAP-001]: [Tên ngắn gọn vấn đề]
* **Luồng liên quan:** [Tên luồng]
* **Bằng chứng hiện tại:**
  - *Mã nguồn:* Code triển khai logic tại `file.ts`: `const TIMEOUT = 5;`
  - *Tài liệu:* Tài liệu không đề cập thời gian timeout.
* **Điểm bất cập / Điều chưa rõ:** [Mô tả chi tiết sự mâu thuẫn hoặc thiếu sót]
* **Tác động nghiệp vụ:** [Tại sao điểm này quan trọng? Nếu hiểu sai sẽ dẫn đến hậu quả gì?]
* **Câu hỏi cho BA/PO:** **"[Nêu câu hỏi trực diện, rõ ràng]?"**
* **Các phương án đề xuất giả thuyết:**
  - **Phương án A:** [Mô tả hướng xử lý A]
  - **Phương án B:** [Mô tả hướng xử lý B]
* **Trạng thái:** `Pending`

---

## 4. KẾT QUẢ THÁM THÍNH RUNTIME (NẾU CHẠY PLAYWRIGHT MCP)

*(Mục này được bổ sung khi người dùng chọn Path B hoặc khi AI cần kiểm chứng hành vi DOM thực tế)*

* **URL kiểm tra:** `http://...`
* **Nhật ký thao tác từng bước & Ảnh chụp màn hình:**
  1. *Bước 1:* Truy cập trang `...` $\rightarrow$ DOM phản hồi bình thường.
  2. *Bước 2:* Thao tác click submit $\rightarrow$ Chụp ảnh màn hình: `[ISSUE-GAP-001-step-01.png](./screenshots/ISSUE-GAP-001-step-01.png)`.
  3. *Bước 3:* Quan sát thấy UI trả về thông báo lỗi: `...`.
* **Phân định nhận thức (Epistemic Classification):**
  - `Hành vi quan sát được ở runtime:` [Mô tả code đang chạy thế nào]
  - `Lưu ý nghiệp vụ:` [Hành vi quan sát được chỉ phản ánh code hiện tại, KHÔNG tự động biến thành nghiệp vụ đúng nếu chưa có BA phê duyệt].

---

## 5. HƯỚNG DẪN DÀNH CHO NGƯỜI DÙNG TẠI ĐIỂM DỪNG 1

Vui lòng xem xét các điểm bất cập trong tài liệu này và phản hồi lại bằng 1 trong 2 lựa chọn:

* **LỰA CHỌN 1 (Path A — Cung cấp câu trả lời BA/PO):**
  > Phản hồi theo cú pháp:  
  > *"Trả lời GAP-001: [Chọn Phương án A hoặc đưa quy định cụ thể]"*
* **LỰA CHỌN 2 (Path B — Thám thính runtime thực tế):**
  > Phản hồi theo cú pháp:  
  > *"Bỏ qua câu hỏi, hãy bật Playwright MCP thám thính runtime thực tế trên môi trường."*
