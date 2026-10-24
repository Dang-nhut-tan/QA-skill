# BÁO CÁO ĐIỀU TRA ĐIỂM BẤT CẬP & PHIẾU LÀM RÕ NGHIỆP VỤ (KÈM MINH CHỨNG MÃ NGUỒN)
## Phân hệ: Hệ Thống QA Agent Testing System (Module: `qa-agent-system`)

> **Thời điểm lập:** 2026-10-24 13:13:00  
> **Trạng thái:** `WAITING_FOR_REQUIREMENT_CLARIFICATION` (Dừng tại Cổng 1)  
> **Công cụ xác minh:** CodeGraph AST & Script Inspection (`scripts/`, `skills/`, `references/`)  
> **Tài liệu đối soát:** `README.md`, `AGENTS.md`, `references/workflow-state-schema.json`, `references/severity-guidelines.md`

---

## 1. TỔNG QUAN KẾT QUẢ ĐIỀU TRA HỆ THỐNG QA SKILL

Qua quá trình rà soát toàn diện giữa kiến trúc đặc tả (`README.md`, `AGENTS.md`) và các đoạn mã triển khai thực tế trong thư mục `scripts/`:
* **Tổng số vấn đề phát hiện:** **5 điểm bất cập & nguy cơ lỗi kỹ thuật**.
* **Phân loại theo mức độ rủi ro:**
  - **2 vấn đề rủi ro cao (Cao):** Có khả năng gây sập luồng chạy (Runtime Exception) hoặc lọc sai 100% dữ liệu người dùng duyệt.
  - **2 vấn đề rủi ro trung bình (Trung bình):** Làm sai lệch thuật toán truy vết ma trận yêu cầu (RTM) và định dạng hiển thị.
  - **1 vấn đề kiến trúc môi trường (Thấp):** Xử lý đường dẫn ghi bài học kinh nghiệm khi nhúng đa tầng.

---

## 2. BẢNG PHÂN LOẠI CHI TIẾT 5 ĐIỂM BẤT CẬP

| Mã Vấn Đề | Phân Loại Kẽ Hở | Luồng / Tệp Liên Quan | Bằng Chứng Mã Nguồn (AST) | Mức Độ Rủi Ro | Trạng Thái |
| :---: | :--- | :--- | :--- | :---: | :---: |
| **GAP-QA-001** | Nghi ngờ lỗi code *(Potential Defect)* | `scripts/state_manager.py` (Quản lý trạng thái) | Dòng 145–146 (`list(set(state[k] + v))`) | **Cao** | Chờ làm rõ |
| **GAP-QA-002** | Mơ hồ nghiệp vụ *(Requirement Ambiguity)* | `scripts/read_approved_testcases.py` (Đọc Excel) | Dòng 67 (`auto_ready_str.lower() == "yes"`) | **Cao** | Chờ làm rõ |
| **GAP-QA-003** | Thiếu hỗ trợ đặc tả *(Design Inconsistency)* | `scripts/export_testcases.py` (Tô màu Excel) | Dòng 76–85 (`style_severity_cell`) | **Trung bình** | Chờ làm rõ |
| **GAP-QA-004** | Sai lệch logic truy vết *(Logic Defect)* | `scripts/traceability_validator.py` (Ma trận RTM) | Dòng 75 (`re.split(r'[/;,|]', ref_raw)`) | **Trung bình** | Chờ làm rõ |
| **GAP-QA-005** | Giới hạn môi trường *(Environment Limitation)* | `scripts/learn_manager.py` (Tự học hỏi) | Dòng 74 (`SYSTEM_ROOT / "skills"`) | **Thấp** | Chờ làm rõ |

---

## 3. PHIẾU LÀM RÕ NGHIỆP VỤ & KỸ THUẬT (CHI TIẾT TỪNG VẤN ĐỀ)

---

### Điểm Bất Cập [GAP-QA-001]: Nguy cơ văng lỗi `TypeError` khi cập nhật danh sách Dict vào State
* **Luồng liên quan:** Quản lý vòng đời trạng thái (`state_manager.py` $\rightarrow$ `transition`)
* **Mức độ rủi ro:** **Cao** (Gây dừng đột ngột luồng tự động)
* **Bằng chứng mã nguồn (AST Evidence):**
  - *Tệp & Vị trí:* `scripts/state_manager.py#L145-L146`
  - *Đoạn code thực tế:*
    ```python
    elif k in state and isinstance(state[k], list) and isinstance(v, list):
        state[k] = list(set(state[k] + v))
    ```
  - *Hiện tượng kỹ thuật:* Hàm `set()` trong Python chỉ chấp nhận các phần tử hashable. Khi gọi `transition` với metadata chứa `clarification_issues` (danh sách các `dict`), Python sẽ văng lỗi ngay lập tức: `TypeError: unhashable type: 'dict'`.
* **Tác động nghiệp vụ:** AI không thể lưu danh sách các câu hỏi BA vào tệp `.qa-state.json` khi hoàn tất bước Gap Analysis.
* **Câu hỏi đối soát cho Lead Architect / User:** **"Có nên sửa cơ chế gộp danh sách thành kiểm tra phần tử trùng lặp theo ID thay vì ép kiểu `set()` không?"**
* **Phương án đề xuất:**
  - **Phương án A (Khuyến nghị):** Duyệt danh sách và khử trùng lặp an toàn: nếu phần tử là `dict` có khóa `"id"`, lọc theo `id`; nếu là kiểu dữ liệu nguyên bản thì mới dùng `set()`.
  - **Phương án B:** Ghi đè trực tiếp `state[k] = v` khi `k == "clarification_issues"`.

---

### Điểm Bất Cập [GAP-QA-002]: Cột "Automation Ready" chỉ nhận chữ "Yes", bỏ qua tiếng Việt ("Có")
* **Luồng liên quan:** Đọc file Excel người dùng duyệt (`read_approved_testcases.py` $\rightarrow$ Pha 6.1)
* **Mức độ rủi ro:** **Cao** (Lọc thiếu 100% test case tự động hóa)
* **Bằng chứng mã nguồn (AST Evidence):**
  - *Tệp & Vị trí:* `scripts/read_approved_testcases.py#L66-L67`
  - *Đoạn code thực tế:*
    ```python
    auto_ready_str = str(auto_ready_val).strip() if auto_ready_val else "No"
    is_ready = auto_ready_str.lower() == "yes"
    ```
  - *Hiện tượng thực tế:* Tester hoặc người dùng doanh nghiệp tại Việt Nam khi mở file Excel thường gõ hoặc chọn dropdown tiếng Việt: `"Có"`, `"có"`, hoặc gõ tắt `"y"`, `"1"`, `"true"`.
* **Tác động nghiệp vụ:** Toàn bộ test case người dùng đánh dấu `"Có"` đều bị coi là `"No"`. Hệ thống báo: `automation_ready_count: 0` và dừng lại không viết code automation!
* **Câu hỏi đối soát cho BA / Lead:** **"Cần mở rộng bộ giá trị hợp lệ cho cột 'Automation Ready' như thế nào?"**
* **Phương án đề xuất:**
  - **Phương án A (Khuyến nghị):** Chấp nhận linh hoạt các giá trị: `{"yes", "y", "có", "co", "true", "1"}` (không phân biệt hoa thường).
  - **Phương án B:** Chỉ cho phép 2 giá trị duy nhất trong dropdown Excel là `"Yes"` và `"No"`, cảnh báo nếu người dùng nhập tiếng Việt.

---

### Điểm Bất Cập [GAP-QA-003]: Màu Pastel của cột Severity bị mất màu khi dùng thuật ngữ tiếng Anh
* **Luồng liên quan:** Xuất bản file Excel doanh nghiệp (`export_testcases.py` $\rightarrow$ `style_severity_cell`)
* **Mức độ rủi ro:** **Trung bình** (Suy giảm trải nghiệm trực quan)
* **Bằng chứng mã nguồn (AST Evidence):**
  - *Tệp & Vị trí:* `scripts/export_testcases.py#L76-L86`
  - *Đoạn code thực tế:*
    ```python
    def style_severity_cell(cell):
        val = str(cell.value or "").strip().lower()
        if "chặn" in val: ...
        elif "sai" in val: ...
        elif "nhỏ" in val: ...
    ```
* **Tác động nghiệp vụ:** Trong cẩm nang `references/severity-guidelines.md` và `AGENTS.md`, hệ thống hỗ trợ cả thuật ngữ quốc tế (`Critical`, `Blocker`, `Major`, `Minor`). Khi test case sinh ra mang nhãn tiếng Anh, ô Severity bị để màu nền trắng trơn, không có badge màu pastel chuẩn doanh nghiệp.
* **Câu hỏi đối soát:** **"Có nên bổ sung ánh xạ song ngữ (Bilingual Mapping) cho các mức độ nghiêm trọng không?"**
* **Phương án đề xuất:**
  - **Phương án A (Khuyến nghị):** Bổ sung: `"chặn"` $\leftrightarrow$ `{"blocker", "critical"}`, `"sai"` $\leftrightarrow$ `{"major", "error"}`, `"nhỏ"` $\leftrightarrow$ `{"minor", "trivial", "low"}`.

---

### Điểm Bất Cập [GAP-QA-004]: Phân rã dấu gạch chéo `/` làm hỏng đường dẫn tệp trong Traceability Matrix
* **Luồng liên quan:** Kiểm tra ma trận truy vết yêu cầu (`traceability_validator.py` $\rightarrow$ `validate_traceability`)
* **Mức độ rủi ro:** **Trung bình** (Báo động giả lỗi mồ côi - False Positive Orphan)
* **Bằng chứng mã nguồn (AST Evidence):**
  - *Tệp & Vị trí:* `scripts/traceability_validator.py#L75`
  - *Đoạn code thực tế:*
    ```python
    tokens = [t.strip() for t in re.split(r'[/;,|]', ref_raw) if t.strip()]
    ```
* **Tác động nghiệp vụ:** Khi test case tham chiếu đến mã nguồn thực tế (ví dụ: `Requirement Reference: src/scripts/state_manager.py#L50`), biểu thức chính quy tách dấu `/` sẽ băm đường dẫn thành 4 token con: `['src', 'scripts', 'state_manager.py#L50']`. Điều này làm thuật toán đối soát 2 chiều bị sai lệch, có nguy cơ đánh rớt bài kiểm tra tự động.
* **Câu hỏi đối soát:** **"Nên quy định dấu phân tách mã yêu cầu (Spec Delimiter) là gì để không xung đột với đường dẫn file?"**
* **Phương án đề xuất:**
  - **Phương án A (Khuyến nghị):** Chỉ tách theo `;`, `,`, `|` hoặc ` / ` (có khoảng trắng hai bên), không tách dấu `/` nằm liền trong đường dẫn tệp.

---

### Điểm Bất Cập [GAP-QA-005]: Đường dẫn ghi bài học `learn_manager.py` chưa linh hoạt khi nhúng đa tầng
* **Luồng liên quan:** Tự học hỏi và tiến hóa kỹ năng (`learn_manager.py` $\rightarrow$ `approve_learning`)
* **Mức độ rủi ro:** **Thấp**
* **Bằng chứng mã nguồn (AST Evidence):**
  - *Tệp & Vị trí:* `scripts/learn_manager.py#L22, L74`
  - *Đoạn code thực tế:*
    ```python
    SYSTEM_ROOT = Path(__file__).resolve().parent.parent
    skill_file = SYSTEM_ROOT / "skills" / target_skill_name / "SKILL.md"
    ```
* **Tác động nghiệp vụ:** Khi chạy thông qua Plugin toàn cục Antigravity, script sẽ nạp bài học vào thư mục plugin mẫu thay vì thư mục `.agent` của dự án đang mở.
* **Phương án đề xuất:**
  - **Phương án A (Khuyến nghị):** Kiểm tra ưu tiên thư mục `.agent/skills/` trong workspace hiện tại trước, nếu không có mới ghi vào `SYSTEM_ROOT`.

---

## 4. HƯỚNG DẪN TẠI ĐIỂM DỪNG 1 (HUMAN GATE 1)

> [!IMPORTANT]
> **HỆ THỐNG ĐANG DỪNG LẠI TẠI ĐÂY THEO ĐÚNG NGUYÊN TẮC CỔNG 1.**  
> AI tuyệt đối không tự ý sửa code hoặc sinh test case khi bạn chưa phê duyệt phương án.

Bạn có thể đưa ra chỉ đạo bằng cách chọn một trong các hướng sau:
1. **Lệnh "tiến hành sửa":** Yêu cầu AI áp dụng ngay các **Phương án A (Khuyến nghị)** để vá 5 điểm bất cập trên vào toàn bộ script của QA skill.
2. **Lệnh "tiếp tục":** Bỏ qua các điểm trên và tiếp tục sang bước tiếp theo (Thiết kế Test Case cho hệ thống QA).
3. **Chỉ đạo riêng:** Đưa ra phương án điều chỉnh cụ thể cho từng mã `GAP-QA-xxx`.
