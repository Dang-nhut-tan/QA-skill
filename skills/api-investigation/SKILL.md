---
name: api-investigation
description: >-
  Verifies discovered requirement gaps, backend vulnerabilities, and data contract discrepancies directly
  at the API/RPC/REST level using Playwright APIRequestContext or HTTP clients. Authors standalone executable
  Playwright API bug reproduction scripts (tests/repro/<module>-api-gap-<id>.spec.ts), provides 1-click terminal
  reproduction commands, detects silent API failures, bypasses of UI validation, and enforces immediate gap elimination
  and rollback when the API operates safely according to business rules.
---

# Skill: API & Backend Service Verification & Reproduction (Step 3 - API Track)

## 1. Description & Trigger Conditions
* **Purpose:** Proactively verify requirement gaps, authorization boundaries, and data integrity constraints directly at the backend API, RPC, or REST endpoint level — bypassing the frontend UI entirely.
  * While `playwright-investigation` verifies what the user experiences on the screen (DOM state, visuals, click flows), `api-investigation` exposes whether the backend enforces true business security:
    1. **Bypass UI Validation (Vượt rào UI):** Giao diện disable nút hoặc validate form, nhưng khi gọi thẳng API thì server vẫn nhận dữ liệu bậy.
    2. **Silent API Failures (UI nuốt lỗi):** API trả về `400 / 422 / 500` hoặc crash nhưng UI không hề hiển thị thông báo lỗi cho người dùng.
    3. **Data Contract & Security Flaws:** Rò rỉ dữ liệu nhạy cảm, thiếu idempotency, hoặc vi phạm RBAC (Role-Based Access Control).
  * Authors standalone, deterministic, executable Playwright API reproduction scripts (`tests/repro/<module>-api-gap-<id>.spec.ts`) without browser launch overhead (< 500ms execution).
* **Triggers:**
  * Identified API/Backend gap items from Step 2 (`requirement-gap-analysis`).
  * Gaps tagged with `[Category: Backend / Security / Data Integrity]`.
  * State transitions from `GAP_ANALYSIS` $\rightarrow$ `API_INVESTIGATION`.

### 1.1. Ephemeral Subagent Delegation Architecture (Ủy quyền Subagent Chuyên Trách)
Để bảo tồn ngữ cảnh (context window) của Orchestrator và chạy song song, quy trình khuyến nghị ủy quyền việc điều tra API cho Subagent chuyên trách:
* **Subagent Name:** `api-investigator` (`agents/api-investigator.md`).
* **Spawn Invocation:**
  ```python
  invoke_subagent(
      TypeName="api-investigator",
      Role="API Investigation Specialist",
      Prompt="Verify identified backend/API gaps for module <ModuleName> directly at endpoint level. Author tests/repro/<module>-api-gap-<id>.spec.ts, run pre-delivery smoke check, and return verified defect proof or safe guard rollback recommendations."
  )
  ```
* **Isolation Boundary:** Subagent chỉ thao tác với HTTP network và file `tests/repro/`, không can thiệp vào các state khác. Sau khi hoàn thành và trả kết quả, Orchestrator thu nạp bằng chứng và đóng subagent.

---

## 2. Inputs & Prerequisites
* **Required Inputs:**
  * Target module API endpoints, RPC functions, or REST routes discovered in Step 1 (`module-context.md`).
  * List of identified `clarification_issues` (`GAP-xxx`) from Step 2.
  * Authentication headers / tokens (derived from `.env.local`, test fixtures, or login session).
* **Prerequisites:**
  * Staging / Dev server API reachable.
  * Node.js and `@playwright/test` installed.
  * Zero plaintext credentials in state files.

---

## 3. Core API Defect Taxonomy (Phân loại lỗi API)

| Mã danh mục | Loại lỗi | Dấu hiệu nhận biết & Hệ quả |
| :--- | :--- | :--- |
| **`API-DEF-01`** | **UI Bypass (Thiếu Server-side Validation)** | UI chặn (nút disabled, input regex), nhưng gọi thẳng API với payload sai lệch thì backend trả về `200 OK` và ghi dữ liệu rác vào CSDL. |
| **`API-DEF-02`** | **Silent API Failure (Nuốt lỗi backend)** | Backend trả về `400 / 422 / 500` hoặc Unhandled Exception, nhưng giao diện frontend không hiện Toast / Alert, người dùng tưởng thao tác thành công hoặc bị đơ. |
| **`API-DEF-03`** | **RBAC / Privilege Escalation** | Tài khoản vai trò thấp (ví dụ: Học sinh) gọi endpoint của vai trò cao (Giảng viên / Quản trị) mà không bị từ chối bằng `401 Unauthorized` hoặc `403 Forbidden`. |
| **`API-DEF-04`** | **Race Condition & Idempotency Failure** | Bắn 2-5 request đồng thời (Concurrent requests) với cùng 1 idempotency key hoặc transaction mà backend tạo trùng 2 bản ghi thanh toán / duyệt bài. |
| **`API-DEF-05`** | **Contract & Schema Inconsistency** | Endpoint trả về HTTP `200 OK` nhưng body chứa `{ "error": true, "message": "Failed" }` (Anti-pattern), hoặc trả về sai kiểu dữ liệu làm crash parser. |

---

## 4. Step-by-Step Execution Instructions

### 4.1. Author Standalone Playwright API Reproduction Script
* Every identified API gap MUST have an isolated, standalone executable script under `tests/repro/`:
  - Path format: `tests/repro/<module>-api-gap-<id>.spec.ts`
  - Structure:
    ```typescript
    import { test, expect } from '@playwright/test';

    /**
     * Bug Reproduction Script: GAP-API-<id>
     * Title: <Short Title>
     * Category: UI Bypass / Silent Failure / RBAC Flaw
     *
     * 1-Click Reproduction:
     *   npx playwright test tests/repro/<module>-api-gap-<id>.spec.ts --project=chromium-desktop
     */
    test.describe('GAP-API-<id>: <Description>', () => {
      test('reproduces backend vulnerability when calling endpoint directly with invalid payload', async ({ request }) => {
        // 1. Prepare Target Endpoint & Headers
        const endpoint = '/api/v1/target-endpoint';
        const authHeaders = {
          'Authorization': `Bearer ${process.env.TEST_TOKEN || ''}`,
          'Content-Type': 'application/json',
        };

        // 2. Dispatch Direct API Call (Bypassing UI)
        const response = await request.post(endpoint, {
          headers: authHeaders,
          data: {
            // Fault payload or unauthorized parameters
            invalid_field: -999,
          },
        });

        // 3. Assert Bug Reproduction:
        // A vulnerable backend accepts invalid payload (status 200/201),
        // whereas a secure backend MUST reject with 400/422/403.
        const status = response.status();
        const body = await response.json().catch(() => ({}));
        
        console.log(`[API PROOF] Status: ${status}`, body);

        // Expectation: If bug exists, server wrongly returns 200 OK
        expect(status, 'GAP Confirmed: Backend accepted invalid payload without validation!').toBe(200);
      });
    });
    ```

### 4.2. Mandatory Pre-Delivery Execution Gate (Chạy thực tế trước khi bàn giao)
> [!CRITICAL]
> **STRICT ZERO-BROKEN-CODE POLICY:**
> The AI agent MUST execute a live test run before presenting the script to the user:
> ```bash
> npx playwright test tests/repro/<module>-api-gap-<id>.spec.ts --project=chromium-desktop
> ```
> * Confirm: 0 syntax errors, 0 network host resolution crashes.
> * If the test script crashes due to harness defects, fix immediately before embedding into `<module>-gaps.md`.

---

### 4.3. Anti-Fabrication & Immediate Gap Elimination Protocol
> [!CAUTION]
> **XÁC NHẬN KHÔNG CÓ LỖI TẠI API -> LẬP TỨC QUAY VỀ BƯỚC GAPS VÀ XÓA BỎ NGAY:**
> Khi gọi API thực tế, nếu backend xử lý an toàn (ví dụ: trả về `400 Bad Request`, `403 Forbidden`, hoặc tuân thủ đúng business rules):
> 1. **LẬP TỨC QUAY VỀ BƯỚC GAPS (`<module>-gaps.md`):**
>    * **XÓA BỎ HOÀN TOÀN (Purge & Delete):** Gỡ bỏ bất cập đó khỏi danh mục `Identified Gaps (GAP-xxx)`. Tuyệt đối không giữ lại hay chuyển sang bước viết Testcase.
>    * **Phân loại vào Chốt chặn an toàn:** Ghi nhận vào mục `Verified Security Guards (GUARD-API-xxx, PASS)`.
>    * **Xóa script sai lệch:** Xóa bỏ file `tests/repro/<module>-api-gap-<id>.spec.ts` ngay lập tức để giữ kho mã sạch.
> 2. **Đồng bộ hóa State:** Cập nhật `.qa-state.json`, đảm bảo không tạo testcase cho lỗi không có thật.

---

## 5. Deliverables & State Transition
1. **Report Update:** Embed 1-click execution commands and API status proof into `<module-name>-gaps.md`.
2. **Terminal Reproduction Commands:**
   ```bash
   # 1-Click Playwright API test execution:
   npx playwright test tests/repro/<module>-api-gap-<id>.spec.ts --project=chromium-desktop
   ```
3. **State Transition:**
   ```bash
   python scripts/state_manager.py transition TESTCASE_GENERATION "API gaps verified with standalone reproduction specs. Advancing to testcase design."
   ```
