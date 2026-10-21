# MA TRẬN ĐỘ PHỦ THEO RỦI RO ĐỘNG (DYNAMIC RISK-BASED COVERAGE MATRIX)
## Tiêu Chuẩn Phân Bổ Test Case Theo Mức Độ Trọng Yếu & Độ Phức Tạp Thay Thế Quota Cứng

> **Mục tiêu kiến trúc:**  
> Xoá bỏ hoàn toàn quota số lượng cứng nhắc (trước đây là 7–10 Chặn, 5–7 Sai).  
> Thay thế bằng **Mô hình Độ phủ Theo Rủi ro Thực tế (Risk-Based Coverage - RBC)**: Số lượng và cơ cấu test case được xác định linh hoạt dựa trên **Quy mô Phân hệ (Module Tier)**, **Điểm số Rủi ro (Risk Score)** và **Mức độ Tác động (Severity)**.

---

## 1. PHÂN CẤP QUY MÔ PHÂN HỆ (MODULE COMPLEXITY TIERS)

Số lượng test case được điều chỉnh theo độ phức tạp cấu trúc mã nguồn (số lượng route, bảng CSDL, API liên quan) và tác động tài chính/bảo mật của phân hệ:

| Cấp Độ Phân Hệ (Tier) | Đặc Điểm Cấu Trúc & Nghiệp Vụ | Định Lượng Test Case Hợp Lý | Phân Bổ Mức Độ Nghiêm Trọng (Severity) Dự Kiến |
| :--- | :--- | :---: | :--- |
| **Tier S — Đơn Giản** *(Simple / Cosmetic / Form đơn)* | Màn hình tĩnh, đổi mật khẩu đơn giản, cập nhật hồ sơ cơ bản, form liên hệ 1 bước, tra cứu danh mục. | **5 – 8 Test Cases** | • Chặn: 2 – 3 ca (Happy path, crash, rỗng)<br>• Sai: 2 – 4 ca (Validation, sai định dạng)<br>• Nhỏ: 1 – 2 ca (UI, placeholder) |
| **Tier M — Tiêu Chuẩn** *(Standard Functional Module)* | Đăng nhập/Đăng ký đa kênh, Đơn từ chấm công, Xếp ca làm việc, Quản lý phòng họp, Phản ánh khiếu nại. | **10 – 18 Test Cases** | • Chặn: 5 – 8 ca (Luồng chính, khoá TK, spam click, phân quyền)<br>• Sai: 4 – 7 ca (Tính toán thời gian, trùng ca, validation)<br>• Nhỏ: 2 – 3 ca |
| **Tier L — Phức Tạp / Trọng Yếu** *(Complex / Financial / Security Core)* | Cổng thanh toán, Quyết toán lương & thuế, Luồng duyệt đơn đa cấp, Mã hoá & Bảo mật phiên làm việc, Đồng bộ CSDL phân tán. | **18 – 30+ Test Cases** | • Chặn: 10 – 16 ca (Mất tiền, sai lệch số dư, race condition, thủng quyền, retry webhook)<br>• Sai: 7 – 12 ca (Công thức tính toán, trạng thái giao dịch)<br>• Nhỏ: 2 – 4 ca |

---

## 2. MA TRẬN ĐÁNH GIÁ RỦI RO (RISK ASSESSMENT FORMULA)

Mỗi kịch bản kiểm thử được chấm điểm theo công thức:

$$\text{Điểm Rủi Ro (Risk Score)} = \text{Mức Độ Tác Động (Impact: 1–3)} \times \text{Xác Suất Lỗi (Probability: 1–3)}$$

### 2.1. Thang Đo Mức Độ Tác Động (Impact):
* **Mức 3 (Cao - Critical):** Mất tiền, rò rỉ dữ liệu nhạy cảm (PII), sập hệ thống (500), gián đoạn hoàn toàn luồng nghiệp vụ chính, tài khoản bị chiếm đoạt.
* **Mức 2 (Trung bình - Moderate):** Sai lệch số liệu tính toán (ngày phép, công), điều hướng nhầm trang, lưu sai trạng thái bản ghi, vi phạm quy tắc ràng buộc dữ liệu.
* **Mức 1 (Thấp - Minor):** Lệch giao diện, lỗi chính tả, thông báo chưa tối ưu, không ảnh hưởng đến luồng dữ liệu.

### 2.2. Thang Đo Xác Suất Lỗi (Probability / Likelihood):
* **Mức 3 (Dễ xảy ra):** Luồng xử lý bất đồng bộ phức tạp, nhiều điều kiện rẽ nhánh (nested if), nhiều bên thứ 3 (SMS, cổng thanh toán, webhook), xử lý đồng thời (concurrency).
* **Mức 2 (Trung bình):** Form nhập liệu nhiều trường có ràng buộc chéo (cross-field validation), truy vấn CSDL có JOIN phức tạp.
* **Mức 1 (Hiếm gặp):** Thành phần UI tĩnh, dữ liệu chỉ đọc (read-only), logic tuần tự đơn giản.

---

## 3. PHÂN ĐỊNH RẠCH RÒI: SEVERITY VS RISK PRIORITY

* **Mức Độ Nghiêm Trọng (Severity - Cột H):**  
  Phản ánh **tác động kỹ thuật / nghiệp vụ khi lỗi xảy ra**:
  - `Chặn`: Lỗi làm tê liệt luồng, crash, mất dữ liệu, thủng bảo mật.
  - `Sai`: Lỗi làm sai kết quả tính toán, hiển thị sai trạng thái, vi phạm validation.
  - `Nhỏ`: Lỗi giao diện, câu chữ, pixel.
  *(Tuyệt đối không dùng Severity để ép số lượng test case!)*

* **Độ Ưu Tiên Thực Thi (Risk Priority):**
  - **P0 (Critical / Blocker):** Điểm rủi ro = 6–9. Bắt buộc kiểm thử đầu tiên, bao phủ 100% trong mọi đợt phát hành.
  - **P1 (High):** Điểm rủi ro = 4–5. Phải kiểm thử trước khi release tính năng.
  - **P2 (Normal / Low):** Điểm rủi ro = 1–3. Kiểm thử khi có đủ thời gian hoặc kiểm thử hồi quy định kỳ.

---

## 4. QUY TRÌNH QUYẾT ĐỊNH ĐỘ PHỦ TỰ ĐỘNG CỦA AGENT

1. **Bước 1 (Nhận diện Tier):** Dựa vào kết quả bóc tách AST của Graphify (số lượng files, số endpoints, cấu trúc DB) để xác định phân hệ thuộc Tier S, Tier M hay Tier L.
2. **Bước 2 (Lập danh mục rủi ro):** Liệt kê các mối đe doạ thực tế (Security, Data Integrity, Concurrency, Throttling, Happy Path).
3. **Bước 3 (Thiết kế test case tương ứng với rủi ro thực):**
   * Nếu phân hệ Tier S chỉ có 6 luồng thực sự cần kiểm thử $\rightarrow$ Tạo đúng 6 test cases sắc bén, **nghiêm cấm bịa thêm case rác chỉ để đạt số lượng**.
   * Nếu phân hệ Tier L có 24 trường hợp rủi ro cao $\rightarrow$ Thiết kế đủ 24 test cases chuyên sâu, **không bị giới hạn bởi quota cũ**.
