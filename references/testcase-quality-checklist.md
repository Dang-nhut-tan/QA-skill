# Checklist Đánh giá Chất lượng Test Case (Test Case Quality Checklist)

Tất cả các ca kiểm thử do Agent thiết kế phải vượt qua bảng tiêu chí kiểm định chất lượng nội bộ trước khi xuất file Excel cho người dùng.

---

## 1. Tính Định danh và Rõ ràng (Identification & Clarity)
- [ ] **Mã Test Case (Test Case ID):** Có cấu trúc duy nhất, ổn định (Ví dụ: `TC-AUTH-001`), không trùng lặp.
- [ ] **Tên Test Case (Name):** Mô tả rõ ràng hành động và mục đích kiểm thử, không viết chung chung kiểu *"Kiểm tra màn hình"*.
- [ ] **Mục đích độc lập:** Mỗi ca kiểm thử chỉ tập trung vào đúng MỘT mục tiêu kiểm chứng chính, tránh dồn nhiều luồng phức tạp vào một ca.

## 2. Dữ liệu và Tiền điều kiện (Preconditions & Test Data)
- [ ] **Tiền điều kiện (Preconditions):** Ghi rõ trạng thái hệ thống cần có trước khi bắt đầu (tài khoản đã kích hoạt, quyền hạn role, cờ cấu hình...).
- [ ] **Dữ liệu kiểm thử (Test Data):** Định lượng rõ ràng các tham số đầu vào (chuỗi ký tự, độ dài, giá trị biên, tài khoản mẫu).

## 3. Các bước thực hiện (Test Steps)
- [ ] **Có đánh số thứ tự:** Từng bước được đánh số `1., 2., 3.` rõ ràng, tuần tự.
- [ ] **Có tính tái lập (Reproducible):** Bất kỳ người kiểm thử nào đọc vào cũng có thể thao tác lại chính xác mà không cần đoán mò.
- [ ] **Tách biệt hành động và kiểm chứng:** Bước thực hiện chỉ nêu hành động (gõ, bấm, chọn); phần kỳ vọng kết quả để riêng ở cột Expected Result.

## 4. Kết quả Kỳ vọng (Expected Result)
- [ ] **Khả kiểm và đo lường được (Verifiable & Measurable):** Không dùng các câu mơ hồ như *"hoạt động bình thường"*, *"chạy đúng"*. Phải nêu rõ thông điệp hiển thị, mã lỗi HTTP, URL đích, hoặc bản ghi được lưu.
- [ ] **Tách biệt Thực tế và Nghiệp vụ:** Phản ánh đúng nghiệp vụ đã được thống nhất, không nhầm lẫn giữa *"code đang chạy như thế này"* với *"nghiệp vụ mong muốn"*.

## 5. Mức độ Nghiêm trọng (Severity)
- [ ] **Phân loại chuẩn xác:** Chỉ sử dụng 3 mức độ: `Chặn`, `Sai`, `Nhỏ`.
- [ ] **Nhất quán:** Các kịch bản crash/bế tắc phải là `Chặn`; sai số liệu là `Sai`; lệch UI là `Nhỏ`.

## 6. Tính Sẵn sàng Tự động hoá (Automation Readiness)
- [ ] **Tiêu chí `Automation Ready = Yes`:**
  - Kết quả kỳ vọng đã sáng tỏ, không còn tranh chấp.
  - Có thể assert khách quan bằng code (DOM element, API status, URL, DB).
  - Không phụ thuộc vào các rào cản bất khả thi (CAPTCHA bên thứ 3, OTP SMS thật không mock được, thiết bị quét thẻ phần cứng).
  - Dữ liệu test có thể khởi tạo độc lập hoặc dọn dẹp sạch sẽ sau khi test.
- [ ] **Nếu `Automation Ready = No`:** Bắt buộc phải điền lý do cụ thể vào cột `Automation Blocker`.

## 7. Phân bổ Số lượng theo Chỉ tiêu Rủi ro (Severity Quotas)
- [ ] **Chỉ tiêu mức Chặn (Nặng):** Đạt từ **7 đến 10 test cases** bao quát toàn bộ các luồng bế tắc, crash, bảo mật, và happy path sinh tử.
- [ ] **Chỉ tiêu mức Sai:** Đạt từ **5 đến 7 test cases** bao quát các lỗi tính toán, sai trạng thái, validation và logic nghiệp vụ.

## 8. Cột Trạng thái Thực thi (Execution Status - Column M)
- [ ] **Vị trí & Giá trị hợp lệ:** Nằm ở cột ngoài cùng (Cột M / Cột 13) với dropdown gồm 4 giá trị: `Pass`, `Fail`, `Pending`, `Skip`.
- [ ] **Giá trị mặc định:** Khi mới xuất bản từ bước thiết kế test case, toàn bộ các ca kiểm thử đều phải có trạng thái mặc định là `Pending` (Pill badge màu hổ phách pastel).
- [ ] **Cập nhật kết quả:** Sau khi kiểm thử thủ công hoặc tự động hoá thực thi, trạng thái được cập nhật thành `Pass` (Xanh mint pastel), `Fail` (Hồng pastel), hoặc `Skip` (Xám nhạt). Nghiêm cấm đánh dấu `Pass` nếu chưa chạy kiểm thử thực tế.

