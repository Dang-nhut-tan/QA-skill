# CẨM NANG CHUẨN HOÁ NGÔN NGỮ NGHIỆP VỤ CHO TEST CASE
## Hướng Dẫn Diễn Đạt Dễ Hiểu Dành Cho Người Không Chuyên IT (Non-IT Accessible Standard)

> **Mục tiêu cốt lõi:**  
> Đảm bảo bất kỳ ai (nhân viên nghiệp vụ, Tester thủ công, BA, Product Owner, hoặc người dùng mới) khi đọc vào bộ Test Case đều **hiểu ngay mục đích kiểm thử** và **tự thao tác làm theo được từng bước trên màn hình**, trong khi **giữ nguyên 100% số lượng, độ phủ rủi ro và các kịch bản kiểm thử chuyên sâu (7–10 ca Chặn, 5–7 ca Sai)**.

---

## 1. NGUYÊN TẮC CỐT LÕI (CORE PRINCIPLES)

1. **Góc nhìn Người Dùng Trực Quan (User-Centric Perspective):**
   * Mọi ca kiểm thử phải xuất phát từ hành động của người dùng trên giao diện ứng dụng (nhập gì, bấm nút gì, nhìn thấy thông báo gì).
   * Tuyệt đối không viết theo tư duy mã nguồn ngầm của lập trình viên (không viết kiểu *"chặn hook"*, *"bắt event"*, *"bắn payload"*).

2. **Cấm Tuyệt Đối Từ Dịch Máy Ngô Nghê & Biệt Ngữ IT:**
   * Nghiêm cấm các từ dịch máy quái đản như: *"Phanh chống ngập"* (dịch thô từ Rate limiting / Throttling).
   * Nghiêm cấm viết tắt cộc lốc hoặc dùng tên biến/mã code nội bộ: `UI`, `DB`, `RPC`, `web_anon`, `DOM`, `insufficient_privilege`, `UUID`.

3. **Cấu Trúc 2 Tầng: "Giao Diện Màn Hình" & "Hệ Thống Dữ Liệu":**
   * Nếu ca kiểm thử cần kiểm tra cả phản hồi trên màn hình lẫn tính toàn vẹn dữ liệu ngầm, phải diễn giải rõ ràng 2 vế:
     - **Vế 1 (Màn hình người dùng):** Giao diện hiển thị thông báo gì, nút bấm đổi trạng thái ra sao.
     - **Vế 2 (Hệ thống dữ liệu ngầm - nếu có):** Hệ thống có lưu bản ghi mới hay không, giải thích bằng ngôn ngữ nghiệp vụ trong sáng.

4. **Bảo Toàn 100% Định Mức Phân Bổ Rủi Ro:**
   * Không đơn giản hoá đến mức làm mất đi các ca kiểm thử bảo mật, biên giới hạn, hay spam click.
   * Vẫn giữ nguyên định mức: **7 – 10 ca kiểm thử mức Chặn (Nặng)** và **5 – 7 ca kiểm thử mức Sai**.

---

## 2. BẢNG TRA CỨU CHUYỂN ĐỔI THUẬT NGỮ (TERMINOLOGY MAPPING)

| Thuật ngữ kỹ thuật / Dịch máy sai lệch | Thuật ngữ chuẩn nghiệp vụ (Dễ hiểu cho Non-IT) | Ví dụ diễn đạt mẫu |
| :--- | :--- | :--- |
| **Phanh chống ngập / Throttling / Rate limiting** | **Giới hạn số lần gửi yêu cầu / Chặn spam liên tục** | *Kiểm tra giới hạn số lần yêu cầu: Chặn gửi thêm khi tài khoản gửi quá 3 lần trong 24 giờ* |
| **Chặn âm thầm (Silent drop)** | **Xử lý bảo mật: Báo thành công chung nhưng không tạo yêu cầu mới** | *Màn hình hiển thị thông báo thành công chung để tránh lộ thông tin tài khoản, nhưng hệ thống không tạo thêm yêu cầu xử lý mới* |
| **UI trả về...** | **Màn hình hiển thị thông báo... / Giao diện hiển thị...** | *Màn hình hiển thị thông báo: "Yêu cầu đã được ghi nhận"* |
| **DB không chèn dòng mới / No DB insert** | **Hệ thống dữ liệu không phát sinh bản ghi mới** | *Hệ thống không tạo mới bản ghi yêu cầu trong cơ sở dữ liệu* |
| **RPC / Endpoint / API** | **Đường dẫn chức năng / Cổng kết nối dữ liệu** | *Gửi yêu cầu trực tiếp qua đường dẫn chức năng khi chưa đăng nhập* |
| **Vai trò web_anon / Khách vãng lai** | **Người dùng chưa đăng nhập / Khách truy cập** | *Người dùng chưa đăng nhập thao tác yêu cầu gửi dữ liệu* |
| **insufficient_privilege / 403 Forbidden** | **Từ chối truy cập do không có quyền** | *Hệ thống từ chối xử lý và hiển thị thông báo: "Bạn không có quyền thực hiện hành động này"* |
| **Chống spam click / useSubmitOnce** | **Khoá nút bấm tạm thời khi đang xử lý** | *Nút "Xác nhận" chuyển sang trạng thái chờ (xoay vòng) và không cho bấm tiếp để tránh gửi trùng* |
| **Payload / Request body** | **Dữ liệu gửi vào biểu mẫu** | *Nhập thông tin hợp lệ vào các ô trong biểu mẫu* |
| **Preconditions: Chưa auth** | **Tiền điều kiện: Chưa đăng nhập vào hệ thống** | *Người dùng đang mở trình duyệt nhưng chưa đăng nhập tài khoản* |
| **Hash mật khẩu / Bcrypt** | **Mã hoá bảo mật thông tin mật khẩu** | *Thông tin mật khẩu được mã hoá an toàn, không hiển thị dạng chữ rõ* |

---

## 3. SO SÁNH TRỰC DIỆN: TRƯỚC VÀ SAU KHI CHUẨN HOÁ

### ❌ Ví dụ 1 (Lỗi thực tế từ phản hồi người dùng):
* **Tên Test Case cũ:**  
  `Phanh chống ngập 2: Chặn âm thầm khi một tài khoản vượt ngưỡng 3 yêu cầu trong 24 giờ`
* **Các bước thực hiện cũ:**  
  `1. Gửi tiếp yêu cầu lần thứ 4 bằng mã nhân viên này`  
  `2. Kiểm tra phản hồi UI và bảng password_reset_request`
* **Kết quả kỳ vọng cũ:**  
  `UI trả về thông báo chung thành công VBO-QM-03... DB không chèn dòng mới do đã vượt quá 3 lần/24h.`

### ✅ Ví dụ 1 (Đã chuẩn hoá nghiệp vụ dễ hiểu cho Non-IT):
* **Tên Test Case mới:**  
  `Kiểm tra giới hạn số lần yêu cầu: Chặn gửi thêm khi tài khoản đã yêu cầu quá 3 lần trong 24 giờ (bảo vệ an toàn thông tin)`
* **Tiền điều kiện:**  
  `Tài khoản nhân viên đã gửi 3 yêu cầu lấy lại mật khẩu trong vòng 24 giờ qua.`
* **Dữ liệu kiểm thử:**  
  `Mã nhân viên: NV-102 (đã đạt giới hạn 3 lần/24 giờ)`
* **Các bước thực hiện mới (Ai cũng làm theo được):**  
  `1. Mở màn hình Quên Mật Khẩu.`  
  `2. Nhập Mã nhân viên NV-102 vào ô nhập liệu.`  
  `3. Bấm nút "Gửi Yêu Cầu" (đây là lần gửi thứ 4).`  
  `4. Quan sát thông báo xuất hiện trên màn hình.`  
  `5. (Dành cho kiểm tra hệ thống nếu cần): Kiểm tra danh sách yêu cầu trong hệ thống quản trị.`
* **Kết quả kỳ vọng mới:**  
  `- Trên màn hình: Hiển thị thông báo thành công chung (Mã: VBO-QM-03) nhằm bảo mật thông tin, không để lộ việc tài khoản đã bị chặn.`  
  `- Trong hệ thống dữ liệu: Không phát sinh thêm bản ghi yêu cầu mới do đã vượt quá hạn mức 3 lần trong ngày.`

---

### ❌ Ví dụ 2:
* **Tên cũ:** `Kiểm soát phân quyền RPC: Khách vãng lai gọi RPC reset password bị từ chối với insufficient_privilege`
* **Các bước cũ:** `1. Dùng vai trò web_anon gọi trực tiếp RPC`
* **Kết quả kỳ vọng cũ:** `Máy chủ từ chối với lỗi insufficient_privilege`

### ✅ Ví dụ 2 (Đã chuẩn hoá):
* **Tên mới:** `Kiểm tra bảo mật phân quyền: Người dùng chưa đăng nhập không thể gọi trực tiếp chức năng cấp lại mật khẩu`
* **Tiền điều kiện:** `Trình duyệt chưa đăng nhập bất kỳ tài khoản nào (phiên khách vãng lai).`
* **Các bước thực hiện mới:**  
  `1. Truy cập trực tiếp vào đường dẫn chức năng cấp lại mật khẩu mà không thông qua giao diện đăng nhập thông thường.`  
  `2. Gửi thông tin yêu cầu thực hiện chức năng.`
* **Kết quả kỳ vọng mới:**  
  `Hệ thống từ chối xử lý, chặn truy cập và hiển thị thông báo lỗi: "Bạn không có quyền thực hiện hành động này hoặc phiên làm việc không hợp lệ."`

---

## 4. QUY CHUẨN SOẠN THẢO CHO TỪNG CỘT TRONG FILE EXCEL

1. **Cột Test Case Name:**  
   Bắt đầu bằng cụm từ hành động nghiệp vụ rõ ràng:  
   * `Kiểm tra đăng nhập thành công khi...`  
   * `Kiểm tra hiển thị thông báo lỗi khi...`  
   * `Kiểm tra giới hạn số lần gửi khi...`  
   * `Kiểm tra bảo mật phân quyền khi...`  
   * `Kiểm tra tính toán ngày công / số tiền khi...`

2. **Cột Preconditions (Tiền điều kiện):**  
   Mô tả trạng thái sẵn có của môi trường/người dùng:  
   * Ví dụ: *"Tài khoản nhân viên đang hoạt động, chưa bị khoá."*  
   * Ví dụ: *"Đã điền đầy đủ thông tin nhưng chưa bấm nút Lưu."*

3. **Cột Test Steps (Các bước thực hiện):**  
   Bắt buộc đánh số thứ tự `1., 2., 3.` với các hành động người dùng thao tác thực tế:  
   * `1. Mở trang...`  
   * `2. Nhập vào ô [Tên ô] giá trị...`  
   * `3. Chọn mục [Tên mục] từ danh sách xổ xuống...`  
   * `4. Bấm nút [Tên nút]...`

4. **Cột Expected Result (Kết quả kỳ vọng):**  
   Nêu rõ những gì người dùng nhìn thấy và hệ thống thực hiện:  
   * Giao diện: Hiển thị thông báo gì (trích dẫn nội dung cụ thể nếu có), ô nhập liệu đổi màu gì, chuyển hướng đến trang nào.  
   * Dữ liệu: Bản ghi được lưu thành công với trạng thái gì.
