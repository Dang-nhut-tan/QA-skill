# Checklist Đánh giá Chất lượng Test Case (Test Case Quality Checklist)

Tất cả các ca kiểm thử do Agent thiết kế phải vượt qua bảng tiêu chí kiểm định chất lượng nội bộ trước khi xuất file Excel cho người dùng.

---

## 1. Tính Định danh và Rõ ràng (Identification & Clarity)
- [ ] **Mã Test Case (Test Case ID):** Có cấu trúc duy nhất, ổn định (Ví dụ: `TC-AUTH-001`), không trùng lặp.
- [ ] **Tên Test Case (Name):** Mô tả rõ ràng hành động và mục đích kiểm thử từ góc độ người dùng, không viết chung chung kiểu *"Kiểm tra màn hình"*.
- [ ] **Ngôn ngữ nghiệp vụ trong sáng (Non-IT Accessible):** Tuyệt đối KHÔNG dùng từ dịch máy thô thiển ("phanh chống ngập", "chặn âm thầm") hoặc biệt ngữ IT nội bộ ("web_anon", "gọi RPC", "UI trả về", "DB chèn dòng").
- [ ] **Mục đích độc lập:** Mỗi ca kiểm thử chỉ tập trung vào đúng MỘT mục tiêu kiểm chứng chính, tránh dồn nhiều luồng phức tạp vào một ca.

## 2. Dữ liệu và Tiền điều kiện (Preconditions & Test Data)
- [ ] **Tiền điều kiện (Preconditions):** Ghi rõ trạng thái hệ thống cần có trước khi bắt đầu (tài khoản đã kích hoạt, quyền hạn role, cờ cấu hình...).
- [ ] **Dữ liệu kiểm thử (Test Data):** Định lượng rõ ràng các tham số đầu vào (chuỗi ký tự, độ dài, giá trị biên, tài khoản mẫu).

## 3. Các bước thực hiện (Test Steps)
- [ ] **Có đánh số thứ tự:** Từng bước được đánh số `1., 2., 3.` rõ ràng, tuần tự.
- [ ] **Có tính làm theo được (Actionable for Non-IT):** Người không chuyên IT đọc vào có thể tự thao tác được trên màn hình (Ví dụ: `1. Mở màn hình...`, `2. Nhập vào ô [Tên ô]...`, `3. Bấm nút [Tên nút]...`).
- [ ] **Tách biệt hành động và kiểm chứng:** Bước thực hiện chỉ nêu hành động (gõ, bấm, chọn); phần kỳ vọng kết quả để riêng ở cột Expected Result.

## 4. Kết quả Kỳ vọng (Expected Result)
- [ ] **Khả kiểm và đo lường được (Verifiable & Measurable):** Không dùng các câu mơ hồ như *"hoạt động bình thường"*, *"chạy đúng"*. Phải nêu rõ thông điệp hiển thị, mã lỗi HTTP, URL đích, hoặc bản ghi được lưu.
- [ ] **Cấu trúc 2 tầng (Giao diện & Dữ liệu):** Nêu rõ người dùng nhìn thấy gì trên màn hình (thông báo gì, nút đổi trạng thái gì) và hệ thống xử lý thế nào ở phía sau (không phát sinh bản ghi mới, lưu thành công với trạng thái gì).
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

## 7. Độ Phủ Theo Ma Trận Rủi Ro Động (Dynamic Risk-Based Coverage)
- [ ] **Định lượng theo Cấp độ Phân hệ (Module Tier):** Phân hệ đơn giản (Tier S) đạt 5–8 ca; tiêu chuẩn (Tier M) đạt 10–18 ca; phức tạp/tài chính/bảo mật (Tier L) đạt 18–30+ ca theo `references/risk-based-coverage-matrix.md`. Tuyệt đối không sinh test case rác/thừa chỉ để đạt quota.
- [ ] **Phân định rạch ròi Severity vs Priority:** Mức độ nghiêm trọng (`Chặn`, `Sai`, `Nhỏ`) phản ánh đúng tác động kỹ thuật/nghiệp vụ của lỗi khi xảy ra, không dùng để ép số lượng test case.
- [ ] **Ưu tiên rủi ro (Risk Priority):** Các ca P0 (Critical Path / Happy path / Bảo mật / Tính toàn vẹn dữ liệu) được bao phủ đầy đủ.

## 8. Cột Trạng thái Thực thi (Execution Status - Column M)
- [ ] **Vị trí & Giá trị hợp lệ:** Nằm ở cột ngoài cùng (Cột M / Cột 13) với dropdown gồm 4 giá trị: `Pass`, `Fail`, `Pending`, `Skip`.
- [ ] **Giá trị mặc định:** Khi mới xuất bản từ bước thiết kế test case, toàn bộ các ca kiểm thử đều phải có trạng thái mặc định là `Pending` (Pill badge màu hổ phách pastel).
- [ ] **Cập nhật kết quả:** Sau khi kiểm thử thủ công hoặc tự động hoá thực thi, trạng thái được cập nhật thành `Pass` (Xanh mint pastel), `Fail` (Hồng pastel), hoặc `Skip` (Xám nhạt). Nghiêm cấm đánh dấu `Pass` nếu chưa chạy kiểm thử thực tế.

## 9. Kiểm Soát Truy Vết Yêu Cầu 2 Chiều & Chống Trùng Lặp (Traceability & Deduplication)
- [ ] **Bao phủ Yêu cầu Trọng yếu (Forward Coverage):** 100% các quy tắc nghiệp vụ, validation rules, và flow trọng yếu trong `module-context.md` đều có ít nhất một test case tương ứng. Số lượng yêu cầu mồ côi (Orphan Requirements) = 0.
- [ ] **Căn cứ Thực tế Không Ảo tưởng (Backward Grounding):** 100% test case đều có giá trị cột `Requirement Reference` chỉ rõ mã đặc tả spec (ví dụ: `SPEC-AU-01`) hoặc symbol/hàm/endpoint cụ thể từ mã nguồn do CodeGraph phát hiện (ví dụ: `useSubmitOnce`, `POST /api/login`). Nghiêm cấm hoàn toàn test case mồ côi (Orphan Test Cases) không có cơ sở thực tế.
- [ ] **Chống Trùng lặp Mục tiêu (Deduplication):** Không có 2 test case nào trùng lặp về mục tiêu kiểm thử, thao tác giống nhau trên cùng tập tiền điều kiện và kỳ vọng cùng kết quả. Mỗi ca kiểm thử phải đại diện cho một rủi ro hoặc một kịch bản biên riêng biệt.

## 10. Tiếp Cận Cho Người Non-IT Không Giảm Thiểu Định Mức (Non-IT Friendly Without Reducing Depth)
- [ ] **Người Non-IT có thể hiểu & thực hiện được:** Bất kỳ nhân viên nghiệp vụ, BA, PO, hoặc Tester mới vào nghề nào khi đọc test case cũng hiểu ngay mục đích và tự thao tác làm theo được từng bước trên màn hình.
- [ ] **Bảo toàn 100% độ sâu kiểm thử:** Không cắt giảm độ sâu phân tích hay độ phức tạp của kịch bản kiểm thử (đáp ứng định mức theo Risk-Based Coverage Tier S/M/L, đầy đủ các kịch bản spam, rate limiting, bảo mật phân quyền, kiểm tra dữ liệu ngầm, concurrency và state transition).
- [ ] **Tuân thủ Cẩm nang thuật ngữ nghiệp vụ:** Áp dụng đầy đủ quy chuẩn chuyển đổi thuật ngữ theo `references/business-terminology-guide.md`, loại bỏ hoàn toàn các từ dịch thô ("phanh chống ngập", "chặn âm thầm", "DB chèn dòng", "web_anon").

