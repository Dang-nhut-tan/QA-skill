# CODEX.md — BỐI CẢNH DỰ ÁN & QUY TẮC VẬN HÀNH DÀNH CHO CODEX / CODING AGENT

> **Dành cho:** Codex, Claude Code, Antigravity Subagents và các Coding Agents tham gia phát triển, bảo trì hoặc thực thi bộ kỹ năng `qa-agent-system`.
> **Mục tiêu:** Cung cấp đầy đủ bối cảnh kiến trúc, nguyên tắc thép, chuỗi trạng thái và các lệnh kiểm thử để bất kỳ agent nào khi đọc file này đều hiểu ngay hệ thống và làm việc chuẩn xác, không suy đoán.

---

## 1. TỔNG QUAN HỆ THỐNG (SYSTEM OVERVIEW)

- **Tên dự án:** `qa-agent-system`
- **Bản chất:** Hệ thống AI QA Copilot có kỷ luật cao, hoạt động theo nguyên tắc **"Bằng chứng trước, kết luận sau"**, chống báo lỗi ảo, tập trung tìm kiếm **Điểm Bất Cập Kỹ Thuật** và **Điểm Gây Ức Chế Người Dùng (User Friction)**, vận hành dưới sự kiểm soát an toàn của con người (Human Gate).
- **Ngôn ngữ & Nền tảng:** Python 3.12+ (`scripts/`, `tests/`), Node.js v24+ / Playwright CLI (`tests/`, `playwright.config.js`), OpenPyXL (Excel generation), SQLite (CodeGraph AST caching).
- **Vị trí gốc:** `C:\Users\TAN\.gemini\config\plugins\qa-agent-system`
- **Kho mã nguồn:** `https://github.com/Dang-nhut-tan/QA-skill.git` (nhánh `main`)

---

## 2. KIẾN TRÚC THƯ MỤC & TÀI NGUYÊN (REPOSITORY STRUCTURE)

```text
qa-agent-system/
├── skills/                            # 13 Kỹ năng chuyên biệt (mỗi thư mục chứa 1 SKILL.md)
│   ├── module-intake/                 # Step 0: Tiếp nhận module, quét môi trường, brief ngành
│   ├── codegraph-context-discovery/   # Step 1: Quét AST, trích xuất Page Object & vẽ sơ đồ Mermaid
│   ├── requirement-gap-analysis/      # Step 2: Đối chiếu luồng chuẩn ngành, tìm Điểm Bất Cập & Ức Chế
│   ├── playwright-investigation/      # Step 3A: Kiểm chứng giao diện sống qua kiến trúc Lai (CLI + MCP)
│   ├── api-investigation/             # Step 3B: Kiểm chứng API, phát hiện lọt validation, script repro
│   ├── gap-reproduction/              # Step 3 Shared: Quy chuẩn kỹ thuật viết script tái hiện lỗi
│   ├── testcase-design/               # Step 4: Thiết kế test case chuẩn doanh nghiệp (Tier S/M/L)
│   ├── testcase-review-export/        # Step 5: Đánh giá RTM & xuất file Excel 3-sheet 13 cột
│   ├── automation-readiness/          # Step 6.1: Bộ lọc chỉ nhận testcase "Automation Ready = Yes"
│   ├── automation-implementation/     # Step 6.2: Viết test automation Playwright chuẩn Senior Dev
│   ├── test-execution-debugging/      # Step 7: Chạy CLI, tự động sửa lỗi locator tối đa 2 lần
│   ├── continuous-learning/           # Step 7+: Đề xuất bài học kinh nghiệm, chờ Bi duyệt để nạp
│   └── workflow-orchestrator/         # Điều phối toàn bộ vòng đời, quản lý state machine
├── scripts/                           # Bộ công cụ thực thi cốt lõi (Core Python Engines)
│   ├── state_manager.py               # Quản lý file .qa-state.json, FSM 14 trạng thái, lock file, redaction
│   ├── codegraph_discovery.py         # Engine tìm kiếm Page Object, AST scanner, fallback đa ngôn ngữ
│   ├── export_testcases.py            # Xuất dữ liệu testcase thành file Excel 3-sheet có format Pastel Pill
│   ├── read_approved_testcases.py     # Đọc ngược file Excel sau khi người dùng duyệt và chỉnh sửa
│   ├── traceability_validator.py      # Kiểm toán ma trận truy vết hai chiều (Forward & Backward)
│   ├── lint_test_code.py              # Bộ linter quét mã test: cấm sleep, cấm lộ token, cấm floating promise
│   └── validate_system.py             # Script kiểm toán kiến trúc 9 bước (0 false PASS)
├── references/                        # Biểu mẫu, schema và tài liệu tham chiếu chuẩn
│   ├── workflow-state-schema.json     # JSON Schema chuẩn hóa cho .qa-state.json
│   ├── excel-testcases-template.xlsx  # File mẫu Excel chuẩn 3 sheets, 13 cột
│   ├── requirement-gaps-template.md   # Biểu mẫu báo cáo GAP, Điểm Bất Cập và Guard
│   └── risk-based-coverage-matrix.md  # Định nghĩa số lượng test case theo độ phức tạp (Tier S/M/L)
├── tests/                             # Bộ kiểm thử hồi quy & kịch bản thực nghiệm
│   ├── test_qa_skills_regression.py   # 112 bài unit test kiểm tra contract của toàn bộ skill
│   ├── test_golden_e2e_pipeline.py    # 5 bài kiểm thử hành vi end-to-end trên filesystem thật
│   ├── smoke.spec.js                  # Playwright smoke test khởi chạy trình duyệt thật
│   └── fixtures/                      # App mẫu đối chứng (order-app.html, order.ts, order.page.ts)
├── AGENTS.md                          # Hướng dẫn phân nhiệm agent toàn cục
├── CODEX.md                           # File này — cẩm nang bối cảnh toàn diện cho Codex
└── playwright.config.js               # Cấu hình Playwright CLI (testDir, reporter, parallel)
```

---

## 3. MÁY TRẠNG THÁI & CHUỖI VẬN HÀNH (FSM & WORKFLOW)

Hệ thống lưu trạng thái liên tục trong file `.qa-state.json` (tự động khóa bằng `StateFileLock`, tự ghi nguyên tử qua `.tmp` + `os.replace`).

### 14 Trạng thái chuẩn tắc (Canonical States):
```mermaid
flowchart TD
    S0["INITIALIZED (Step 0)"] --> S1["CONTEXT_DISCOVERY (Step 1)"]
    S1 --> S1_INC["DISCOVERY_INCOMPLETE (Nếu chạm trần giới hạn)"]
    S1 --> S2["GAP_ANALYSIS (Step 2)"]
    S2 --> S3A["RUNTIME_INVESTIGATION (Step 3A - UI)"]
    S2 --> S3B["API_INVESTIGATION (Step 3B - API)"]
    S2 --> S2_WAIT["WAITING_FOR_REQUIREMENT_CLARIFICATION (Nếu spec mâu thuẫn)"]
    S3A --> S4["TESTCASE_GENERATION (Step 4)"]
    S3B --> S4
    S4 --> S5["TESTCASE_REVIEW (Step 5)"]
    S5 --> S5_GATE["🔴 WAITING_FOR_APPROVED_TESTCASES (Cổng duyệt con người)"]
    S5_GATE -->|"Người dùng duyệt"| S6["AUTOMATION_IMPLEMENTATION (Step 6)"]
    S5_GATE -->|"Người dùng yêu cầu sửa"| S4
    S6 --> S7["AUTOMATION_EXECUTION (Step 7)"]
    S7 -->|"Test xanh hoặc hoàn tất"| S_END["COMPLETED"]
    S7 -->|"Môi trường bị chặn"| S_BLOCKED["BLOCKED"]
```

---

## 4. BA CHẾ ĐỘ CHẠY (EXECUTION MODES)

1. **`standard` (Mặc định cốt lõi):**
   - Áp dụng cho mọi module nghiệp vụ thông thường.
   - Bắt buộc đi qua đủ 8 bước.
   - **Giá trị tối thượng:** Đối chiếu chuẩn mực ngành để vạch trần **Điểm Bất Cập Kỹ Thuật** (Inadequacies) và **Điểm Gây Ức Chế Người Dùng** (User Friction) qua 5 giai đoạn: Nhập liệu $\rightarrow$ Gửi yêu cầu $\rightarrow$ Chờ xử lý $\rightarrow$ Báo lỗi $\rightarrow$ Hoàn tất.
   - Xuất file Excel 3-sheet 13 cột và **bắt buộc dừng lại xin duyệt**.

2. **`critical` (Trọng yếu cao cấp):**
   - Dành cho phân hệ Tài chính, Tiền bạc, Thanh toán (Payment/Checkout), Phân quyền tối cao (RBAC), Dữ liệu nhạy cảm.
   - Giống `standard` nhưng kích hoạt thêm:
     * **Production Safety Gate:** Chặn đứng mutation nếu chạy trên URL production.
     * **Giới hạn tương tranh (Concurrency Burst Cap):** Tối đa 5 requests đồng thời để chống DoS và kiểm tra race condition/idempotency.
     * **Dual-Track bắt buộc:** Kiểm tra song song cả giao diện UI (3A) và backend API (3B).

3. **`quick` (Rút gọn / Hotfix):**
   - Dùng khi người dùng yêu cầu smoke test hoặc tái hiện gấp 1 con bug cụ thể.
   - Đi đường tắt: Intake $\rightarrow$ Runtime/API verify $\rightarrow$ Báo cáo log chat.
   - **LƯU Ý DÀNH CHO CODEX:** Không được lạm dụng `quick` mode cho các yêu cầu QA thông thường, vì `quick` mode bỏ qua bước phân tích luồng và không tìm ra điểm bất cập.

---

## 5. CHÍNH SÁCH CÔNG CỤ & KIẾN TRÚC LAI (HYBRID ARCHITECTURE)

### 1. Khám phá mã nguồn bằng CodeGraph (JIT Discovery):
- Được phép duyệt toàn bộ cây dependency nhưng **bắt buộc áp trần an toàn**: `max_depth = 3`, `max_nodes = 50`, timeout tiến trình 60s.
- Nếu chạm trần hoặc parser lỗi, trạng thái ghi nhận là `DISCOVERY_INCOMPLETE` kèm cảnh báo minh bạch; **tuyệt đối không được báo hoàn tất dối**.

### 2. Kiến trúc Lai cho Kiểm chứng Giao diện (Playwright Hybrid):
- **Động cơ chính (Primary Engine) — Playwright CLI:** Dành cho các dự án có mã nguồn, Page Objects, hoặc fixtures. Agent viết script tái hiện ngắn trong `tests/repro/` và chạy lệnh terminal `npx playwright test`. Tốc độ cực nhanh (~1.5s), tiết kiệm ~90% token, sinh file `.spec.ts` sẵn sàng bàn giao cho Dev và CI.
- **Động cơ dự phòng (Fallback Engine) — Playwright MCP:** Chỉ kích hoạt khi kiểm thử hộp đen (black-box), web ngoài không có mã nguồn, hoặc khi selector trên DOM bị dynamic/obfuscate cần mò mẫm qua cây Accessibility Tree (`browser_snapshot`, `browser_click`).

---

## 6. CÁC NGUYÊN TẮC THÉP BẮT BUỘC (NON-NEGOTIABLE GUARDRAILS)

Khi Codex thực thi mã nguồn hoặc kịch bản kiểm thử, **BẮT BUỘC TUÂN THỦ 100% CÁC NGUYÊN TẮC SAU**:

1. **Nguyên tắc Chứng cứ (Zero Hallucination / Evidence-First):**
   - Tuyệt đối CẤM báo test "PASS" nếu chưa chạy CLI và nhận exit code 0.
   - Phân biệt rõ: Điều xác nhận từ code, điều thấy khi chạy thật, và điều chỉ là suy đoán.
2. **Cổng kiểm soát của Con người (Human Gate):**
   - Sau khi xuất file Excel tại Step 5, hệ thống **bắt buộc dừng lại** ở trạng thái `WAITING_FOR_APPROVED_TESTCASES` và hỏi Bi (Tân): *"Bạn có hài lòng với bộ testcase hiện tại không?"*.
   - CẤM tự ý viết mã Playwright automation (Step 6) khi người dùng chưa phê duyệt và cung cấp `approval_token`.
3. **Cơ chế giữ lại Guard (Valuable Guard Retention):**
   - Nếu kịch bản kiểm thử chứng minh hệ thống đã có phòng thủ hợp lệ (ví dụ: server chặn đúng giá âm trả về 400 Bad Request, hoặc nút bị disable khi số lượng $\le 0$):
   - **TUYỆT ĐỐI CẤM BÁO THÀNH BUG.**
   - Di chuyển script vào `tests/guards/<module>-guard-<id>.spec.ts`, đổi ID thành `GUARD-xxx`, ghi nhận vào `.qa-state.json` và giữ làm regression protection vĩnh viễn.
4. **Tiêu chuẩn mã kiểm thử Senior Dev (`scripts/lint_test_code.py`):**
   - ❌ **CẤM arbitrary sleep:** Không dùng `waitForTimeout()`, `time.sleep()`. Bắt buộc dùng web-first assertions (`await expect(locator).toBeVisible()`).
   - ❌ **CẤM floating promises:** Bắt buộc có `await` trước mọi async expect.
   - ❌ **CẤM in lộ token:** Không dùng `console.log(token)` hoặc echo biến môi trường thô.
   - ✅ **Định danh chuẩn mực:** Tiêu đề test phải chứa ID truy vết rõ ràng: `test('TC-xxx: ...')`, `test('GAP-xxx: ...')`, hoặc `test('GUARD-xxx: ...')`.
5. **Bảo mật & Làm sạch Dữ liệu (Secret Redaction):**
   - State manager tự động chặn các key nhạy cảm (`api_key`, `password`, `token`) nếu truyền trực tiếp vào state metadata (ném `ValueError: Security Alert`).
   - Mọi URI connection string có mật khẩu đều tự động được chuyển đổi thành `***REDACTED***`.
6. **Chuẩn hóa Ngôn ngữ:**
   - Schema nội bộ, tài liệu kỹ thuật, test script, tên hàm, enum: **100% English**.
   - Báo cáo, trao đổi, hỏi ý kiến người dùng Bi (Tân): **Tiếng Việt**.
   - File Excel bàn giao: Ngôn ngữ nghiệp vụ dễ hiểu (Non-IT Business Phrasing), tách bạch `Severity` (Mức độ nghiêm trọng) khỏi `Priority` (Thứ tự ưu tiên chạy).

---

## 7. CÁC LỆNH KIỂM CHỨNG BẮT BUỘC (VERIFICATION COMMANDS)

Trước khi hoàn tất bất kỳ thay đổi code nào trong repo này, Codex bắt buộc phải chạy và bảo đảm các lệnh sau đạt kết quả xanh 100%:

```powershell
# 1. Chạy toàn bộ 112 bài unit test hồi quy
cd "C:\Users\TAN\.gemini\config\plugins\qa-agent-system"
python -m pytest tests -q
# Kỳ vọng: 112 passed, 0 failed

# 2. Chạy kiểm thử trình duyệt thực tế qua Playwright CLI
npx playwright test
# Kỳ vọng: 5 passed (trên Chromium thật)

# 3. Kiểm toán toàn vẹn kiến trúc hệ thống
python scripts/validate_system.py
# Kỳ vọng: [SUCCESS] All 9 architectural validations and dry-run tests PASSED! (0 false PASS)

# 4. Kiểm tra quy chuẩn linter mã test
python scripts/lint_test_code.py tests/fixtures/browser/order-ui-bug-repro.spec.js
# Kỳ vọng: Trả về mã thoát 0, không có vi phạm
```
