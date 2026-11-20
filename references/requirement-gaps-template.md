# REQUIREMENT GAP INVESTIGATION & SECURITY GUARD VERIFICATION REPORT
## Module: [Module Name]

> **Generated At:** [YYYY-MM-DD HH:MM:SS]  
> **Status:** `WAITING_FOR_REQUIREMENT_CLARIFICATION`  
> **Verification Tools:** CodeGraph AST (Source Code) & Playwright MCP (Live UI Verification)  
> **Specification Reference:** [Document Name or 'Direct AST Source Code Audit']

---

## 1. EXECUTIVE SUMMARY & UI VERIFICATION OVERVIEW

* **Total True Gaps Identified:** `[N]` discrepancy items (Subject to BA/PO clarification). If the system is fully compliant, state `0`.
* **Total Verified Security Guards:** `[M]` security / RBAC permission constraints functioning correctly (PASS).
* **Live UI Verification Status (Playwright MCP):**
  - `[X]` scenarios physically verified with standalone Playwright reproduction scripts (`tests/repro/`).
  - `[Y]` backend-only rules audited via source code AST.
* **Risk Distribution:**
  - Only True GAPs contribute to risk assessment. Verified Security Guards are marked as **PASS** and must never be classified as defects or blockers.

---

## 2. VERIFIED SECURITY GUARDS & CONSTRAINTS (IF ANY)
*(Applicable for access restrictions, self-approval prevention, privilege boundary guards, rate limiters functioning correctly)*

| Guard ID | Protected Business Flow | Source Code Evidence (AST) | Live UI Verification (Playwright) | Safety Assessment |
| :---: | :--- | :--- | :--- | :---: |
| **GUARD-001** | [e.g., Deputy Manager cannot approve requests] | `Symbol: canApprove = false` | Button disabled with explanatory banner | **PASS** |
| **GUARD-002** | [e.g., Prevent self-approval of own requests] | `Symbol: isOwnRequest` | Action buttons completely hidden on personal tab | **PASS** |

---

## 3. CLASSIFICATION OF TRUE GAPs (IF ANY)
*(Recorded only when an actual contradiction occurs: spec forbids but UI allows, spec missing causing confusion, or runtime crash. External benchmark differences without empirical grounds are triaged as Advisory under Improvement Opportunity, BA Clarification, or Residual Risk, not active GAP defects.)*

| Issue ID | Gap Classification | Related Flow | Code Evidence (AST) & UI | UX Impact | Future Technical Risk | Risk Severity |
| :---: | :--- | :--- | :--- | :--- | :--- | :---: |
| **GAP-001** | Requirement Ambiguity | [Affected Flow] | File: `path/to/file.ts#L45-L60` | Operational confusion, missing feedback | Concurrency race condition, DB desync | High / Medium |
| **GAP-002** | Potential Implementation Defect | [Affected Flow] | File: `path/to/service.ts#L102` | Misleading submission status | Security vulnerability, data loss | High |
| **GAP-003** | Architectural / Cross-System Inconsistency | [Cross-Service Flow] | File: `system-architecture-flows.md` & `client.ts` | Missing remote timeout & webhook retry handling | Downstream split-brain, hung workers | High |
| **GAP-004** | Industry Benchmark Discrepancy & Domain Blindspot | [Resource Booking / Checkout Flow] | File: `industry-benchmark-flows.md` vs `orderService.ts` | Silent double-charge on double-click; missing reservation TTL | Race condition, inventory oversell, duplicate billing | Critical |

*(If zero gaps are found, state: `No requirement gaps or defects detected. All business flows comply with system specifications.`)*

---

## 3.5. SIDE-BY-SIDE BENCHMARK & USER FRICTION AUDIT
### (ĐỐI CHIẾU LUỒNG CHUẨN NGÀNH & ĐIỂM GÂY ỨC CHẾ NGƯỜI DÙNG)

*(Bắt buộc đối chiếu trực tiếp giữa luồng chuẩn mực ngành từ `industry-benchmark-flows.md` với luồng thực tế của phân hệ dự án công ty mình)*

| Giai Đoạn Thao Tác (Operational Phase) | Chuẩn Mực Hệ Thống Dẫn Đầu (Industry Leader Flow) | Luồng Thực Tế Dự Án Công Ty Mình (Our Company Project Flow) | Điểm Bất Cập Kỹ Thuật (Technical / Logic Inadequacy) | Điểm Gây Khó Chịu / Ức Chế Cho Người Dùng (User Friction & Frustration Point) |
| :--- | :--- | :--- | :--- | :--- |
| **1. Nhập liệu & Khởi tạo (Data Entry & Initiation)** | Xác thực ngay tại ô (inline validation), tự động lưu nháp (auto-save draft), gợi ý dữ liệu thông minh. | [Mô tả luồng khởi tạo thực tế của dự án] | [Ví dụ: Không validate phía client, reload trang toàn phần] | **Ức chế 1: Mất dữ liệu vừa điền.** Báo lỗi 1 ô là xóa sạch cả form, bắt người dùng nhập lại từ đầu. |
| **2. Gửi yêu cầu & Chuyển trạng thái (Submission & Transit)** | Disable nút submit ngay khi click, gửi kèm Idempotency Key, hiển thị icon loading mượt mà tại nút. | [Mô tả cách xử lý khi bấm nút gửi] | [Ví dụ: Nút vẫn click được bình thường, không debounce] | **Ức chế 2: Bẫy bấm đúp (Double-Click Trap).** Người dùng tưởng nút chưa ăn nên click nhiều lần, sinh đơn trùng lặp hoặc trừ tiền nhiều lần. |
| **3. Chờ xử lý bất đồng bộ (Async Processing / Wait)** | Có thanh tiến trình / bộ đếm thời gian rõ ràng, có timeout tối đa (ví dụ 10s) và nút hủy/thử lại. | [Mô tả cách hệ thống phản hồi khi xử lý lâu] | [Ví dụ: Không bắt Promise reject, không đặt timeout trần] | **Ức chế 3: Treo màn hình / Spinner vô tận.** Màn hình đơ, spinner quay mãi không dừng, không dám F5 vì sợ mất đơn. |
| **4. Thông báo lỗi & Khắc phục (Error Feedback & Recovery)** | Thông báo rõ ràng lý do lỗi và chỉ đích danh thao tác cần sửa để tiếp tục (actionable guidance). | [Mô tả cách ứng dụng hiển thị lỗi] | [Ví dụ: Banner thông báo chung chung 'Có lỗi xảy ra' hoặc văng mã lỗi kỹ thuật 500] | **Ức chế 4: Thông báo mơ hồ hoặc im lặng.** Người dùng không biết tại sao lỗi (do thẻ, do mạng, hay do máy chủ) và không biết phải làm gì tiếp theo. |
| **5. Kết thúc & Hoàn tất (Completion & Control)** | Hiển thị mã biên nhận rõ ràng, có thời gian ân hạn (grace period) cho phép Hủy / Sửa (Undo). | [Mô tả màn hình hoàn tất giao dịch] | [Ví dụ: Điều hướng thẳng về trang chủ mà không có mã xác nhận] | **Ức chế 5: Mất dấu vết & Thiếu quyền kiểm soát.** Không biết đơn đã lưu ở đâu, lỡ bấm nhầm không có nút Undo hoặc hủy. |

---

## 4. DETAILED CLARIFICATION CARDS FOR BA / PO (WITH SCREENSHOT PROOF & DUAL IMPACT)

### [GAP-001]: [Concise Issue Title]
* **Category:** [Requirement Ambiguity / Potential Defect / Missing Documentation / Confirmed Defect / Architectural Cross-System Inconsistency / Industry Benchmark Discrepancy & Domain Blindspot]
* **Related Business Flow:** [Flow Name]
* **Severity:** [Critical/Blocker / Major / Minor]

#### 1. Technical Evidence & Specification Discrepancy
* **Code Location:** [`path/to/file.ts#L45-L60`](file:///path/to/file.ts#L45-L60)
* **Observed Implementation:** [Code snippet or logic summary]
* **Documented Specification:** [Requirement text citation or 'Unspecified in documentation']

#### 2. User Experience (UX) Impact
* **Operational Friction:** [Detailed description: What does the user see or struggle with? Are error messages missing, generic, or misleading?]
* **Behavioral Traps:** [Does the user assume an action succeeded when it silently failed? Risk of accidental duplicate submissions or wrong inputs?]
* **Trust Degradation:** [Does the interface appear unresponsive, broken, or unpolished?]

#### 3. Future Technical Risks & Potential Defects
* **Data Inconsistency & Corruption:** [How will database records become corrupted, orphaned, or desynchronized across tables?]
* **Concurrency & Race Conditions:** [How will this edge case behave under peak concurrent traffic or parallel background workers?]
* **Cascading Downstream Failures:** [How will future reporting, billing, financial ledger, or third-party webhooks break due to dirty data?]
* **Compliance & Security Liabilities:** [Risk of privilege escalation, unauthorized operations, or missing audit trails?]

#### 4. Playwright Bug Reproduction Script & CLI Execution
* **Reproduction Script Path:** [`tests/repro/GAP-001.spec.ts`](file:///tests/repro/GAP-001.spec.ts)
* **1-Click Terminal Reproduction Commands:**
  ```bash
  # Execute via registered npm shortcut:
  npm run module:gap:1

  # Or execute directly via Playwright CLI (headed with interactive debug):
  npx playwright test tests/repro/GAP-001.spec.ts --headed
  ```
* **Executable Reproduction Code (`tests/repro/GAP-001.spec.ts`):**
  ```typescript
  import { test, expect } from '@playwright/test';

  test('GAP-001: Reproduce [concise issue summary]', async ({ page }) => {
    // 1. Navigate to target screen
    await page.goto('/target-route');

    // 2. Perform reproduction interactions
    await page.fill('#field-id', 'test-input');
    await page.click('button#action-id');

    // 3. Assert expected state vs observed failure
    // EXPECTED: Feedback message or state transition appears within timeout
    // OBSERVED BUG: Action hangs silently or unhandled exception occurs
    await expect(page.locator('.expected-feedback-selector')).toBeVisible({ timeout: 5000 });
  });
  ```
* **Observed Execution Failure / Trace:**
  - *Outcome:* `FAILED` — Timeout 5000ms exceeded waiting for locator `.expected-feedback-selector`.
  - *Trace File:* `test-results/GAP-001/trace.zip` (Inspect with `npx playwright show-trace`).

#### 5. DevTools Diagnostics (Console & Network Logs)
* **Console Messages & Runtime Exceptions (`browser_console_messages`):**
  - *Status:* `[ERRORS_DETECTED]` or `[CLEAN - Zero Console Errors]`
  - *Log Trace:*
    ```text
    [error] Uncaught TypeError: Cannot read properties of undefined (reading 'status') at actionHandler.ts:54
    ```
* **Network Traffic & API Diagnostics (`browser_network_requests`):**
  - *Status:* `[FAILED_REQUESTS_DETECTED]` or `[CLEAN - All Requests 2xx/3xx]`
  - *Failed Endpoints:*
    ```text
    POST /api/v1/module/action -> 500 Internal Server Error (Duration: 320ms)
    Response: {"error": "Internal Server Error", "code": "ERR_DB_LOCK_TIMEOUT"}
    ```

#### 6. Targeted Clarification Questions & Suggested Options
* **Core Question:** *"[Clear, neutral clarification question for BA/PO]"*
* **Option A (Recommended):** [Industry-standard, safe, and UX-friendly approach]
* **Option B:** [Keep existing code behavior and add clear user messaging]
* **Option C:** [Custom business policy]

---

## 5. USER INSTRUCTIONS AT HUMAN GATE 1

> [!IMPORTANT]
> **WORKFLOW IS CURRENTLY HALTED HERE.**  
> The agent will not generate subsequent test cases until you provide explicit instruction.

* **To approve and continue:** Send message: **`proceed`** (or **`continue`**).
* **To provide BA/PO answers:** Send message: **`Answer GAP-xxx: Option A`**.
