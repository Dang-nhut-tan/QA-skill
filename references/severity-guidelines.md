# Tiêu chí phân loại Mức độ Nghiêm trọng (Severity Guidelines)

Trong hệ thống QA Agent System, mức độ nghiêm trọng đại diện cho **tác động tiềm tàng đến nghiệp vụ và trải nghiệm người dùng nếu ca kiểm thử thất bại**.

Mức độ nghiêm trọng **không phản ánh** trạng thái lỗi đã xảy ra hay chưa, mà phản ánh **sức nặng của rủi ro**.

---

## 1. Chặn (Blocking)
* **Định nghĩa:** Lỗi khiến người dùng hoặc hệ thống **hoàn toàn không thể tiếp tục** thực hiện luồng nghiệp vụ bắt buộc, không có phương án thay thế (workaround) tạm thời.
* **Đặc điểm nhận diện:**
  * Sập ứng dụng, White screen of death (WSOD), Crash hệ thống, mã lỗi 500 không thể phục hồi.
  * Tắc nghẽn hoàn toàn ở các bước tiên quyết: Đăng nhập thất bại, không thể thanh toán đơn hàng, khoá oan tài khoản người dùng, treo tiến trình xử lý giao dịch.
  * Vi phạm bảo mật nghiêm trọng: Lộ thông tin định danh (PII) trên đường truyền công khai, phá vỡ ranh giới phân quyền truy cập.
* **Mức độ ưu tiên kiểm thử:** Tối cao. Phải kiểm thử đầu tiên trong Smoke / Sanity test.

---

## 2. Sai (Incorrect)
* **Định nghĩa:** Luồng nghiệp vụ vẫn có thể tiếp tục thực hiện hoặc hoàn tất, nhưng **tạo ra dữ liệu, tính toán, kết quả kinh doanh hoặc trạng thái hệ thống không chính xác**.
* **Đặc điểm nhận diện:**
  * Sai lệch công thức tính toán: Tiền lương, thuế VAT, điểm tích luỹ, tổng tiền giỏ hàng bị lệch số liệu.
  * Lưu trữ sai trạng thái vào CSDL: Cập nhật thông tin nhân viên nhưng trạng thái hiển thị sai, gửi sai email kích hoạt.
  * Luồng rẽ nhánh điều hướng sai: Đăng nhập thành công nhưng văng ra màn hình không đúng với `dichQuayLai`.
  * Có phương án thay thế (workaround) nhưng gây phiền hà hoặc rủi ro sai lệch dữ liệu.
* **Mức độ ưu tiên kiểm thử:** Cao. Phải được kiểm tra kỹ trong Functional / Integration test.

---

## 3. Nhỏ (Minor)
* **Định nghĩa:** Lỗi giao diện, định dạng trình bày, thông điệp phản hồi hoặc trải nghiệm người dùng (UI/UX) ở mức độ nhẹ, **không làm gián đoạn luồng nghiệp vụ và không làm sai lệch dữ liệu kinh doanh**.
* **Đặc điểm nhận diện:**
  * Lỗi chính tả, dịch thuật i18n không sát nghĩa, câu từ chưa mượt mà nhưng người dùng vẫn hiểu được.
  * Lệch khoảng cách pixel, màu sắc nút bấm chưa chuẩn theo Design System, icon bị căn lệch nhẹ.
  * Thiếu placeholder hoặc tooltip hướng dẫn bổ trợ.
  * Tốc độ phản hồi UI hơi chậm ở một animation chuyển cảnh nhưng không gây đơ ứng dụng.
* **Mức độ ưu tiên kiểm thử:** Trung bình / Thấp. Kiểm tra sau khi các luồng cốt lõi đã hoàn tất.
