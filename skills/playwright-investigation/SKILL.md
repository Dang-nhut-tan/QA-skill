---
name: playwright-investigation
description: >-
  Verifies discovered requirement gaps directly on the live UI using Playwright MCP.
  Authors executable Playwright bug reproduction scripts (tests/repro/<module>-gap-<id>.spec.ts),
  provides 1-click terminal reproduction commands (npm run <module>:gap:<id>), harvests DevTools
  runtime errors, and embeds reproducible code proof into <module-name>-gaps.md before testcase design.
---

# Skill: Playwright UI Verification & Gap Reproduction (Step 3)

## 1. Description & Trigger Conditions
* **Purpose:** Proactively verify on the actual web interface whether the requirement gaps and potential defects identified in Step 2 (`requirement-gap-analysis`) actually occur. Instead of relying on fragile, static screenshots that can capture loading screens or become obsolete, **author standalone executable Playwright bug reproduction scripts (`tests/repro/<module>-gap-<id>.spec.ts`)** for every observable gap. Provide 1-click terminal reproduction commands (`npm run <module>:gap:<id>` and `npx playwright test ...`), harvest DevTools runtime diagnostics, and embed the executable proof into the BA Clarification Ticket (`<module-name>-gaps.md`) so developers and QA engineers can effortlessly reproduce, debug, and verify the issues locally.
* **Triggers:**
  * Identified discrepancy points (gaps) from `requirement-gap-analysis`.
  * State transitions from `GAP_ANALYSIS` $\rightarrow$ `RUNTIME_INVESTIGATION` or direct progression to `TESTCASE_GENERATION`.

## 2. Inputs
* **Required:**
  * Target module URL / route and environment credentials.
  * List of identified `clarification_issues` (`GAP-xxx`) from Step 2.
  * `module-context.md` from Step 1.

## 3. Prerequisites
* **Playwright MCP** server configured and operational.
* Target web application running and accessible (local dev server or staging environment).
* **Credentials Check:** Verify if Staging URL and test account metadata are configured in `.env.local` or environment variables (per `module-intake`). Never persist plaintext passwords or secrets in `.qa-state.json`. If required credentials are not yet set, proactively instruct the user to configure `.env.local`.

## 4. Step-by-Step Execution Instructions

### 4.1. Identify Observable UI Gaps
* Filter the list of identified gap items from Step 2 to isolate issues that can be observed on the UI (e.g., form validation, error messages, disabled buttons, warning modals, tab transitions, redirects).
* For backend-only issues (e.g., database triggers without UI feedback, external gateway dependencies): Record `[Verified via AST - No UI Rendering]`.

### 4.2. Mandatory Page Settlement & Anti-Loading-Screen Clearance Protocol
> [!CAUTION]
> **STRICT PROHIBITION ON CAPTURING LOADING SCREENS / SKELETONS:**
> Capturing a screenshot while a page or component is still loading, spinning, or rendering skeleton placeholders produces **FALSE EVIDENCE** and makes it impossible to verify whether a defect is genuine. All screenshots MUST capture a fully settled, final rendered state.

Before executing ANY `browser_take_screenshot`:
1. **Network & DOM Completion Check:**
   - After `browser_navigate` or trigger actions, ensure navigation has reached `document.readyState === 'complete'`.
   - Wait for pending network requests to settle via `browser_wait_for` or appropriate selector checks.
2. **Loading Mask & Spinner Disappearance:**
   - The AI agent MUST verify that all loading overlays, progressbars, spinners, and skeleton screens are completely hidden or detached:
     - Check selectors: `[role="progressbar"]`, `.spinner`, `.loading`, `.ant-spin`, `.skeleton`, `[aria-busy="true"]`, `.shimmer-placeholder`, or application-specific loading overlays.
     - Wait for these selectors to have state `hidden` or `detached` before triggering screenshot capture.
3. **Target Element Settlement & Stability:**
   - Wait specifically for the target feedback element to be visible and stable:
     - For validation/error messages: Wait until the specific alert banner, inline error label, or toast container is attached and displays non-empty text.
     - For table/form results: Wait until the data rows or disabled submit buttons are rendered.
4. **Anti-Premature Screenshot Self-Audit:**
   - If a captured screenshot reveals a loading indicator, spinner, or blank/skeleton canvas, the AI agent MUST deem that screenshot INVALID, wait for the DOM to settle, and re-capture.
   - If an asynchronous action hangs or times out (> 10s without completing), classify it explicitly as `[SYSTEM_TIMEOUT_OR_HANG]` with console logs and network failure evidence, rather than misrepresenting an incomplete loading state as a normal UI bug.

### 4.3. Author Playwright Bug Reproduction Script & Register Terminal Commands
* Instead of brittle, dead static screenshots, every observable UI gap MUST be accompanied by an executable Playwright reproduction spec:
  1. **Author Standalone Reproduction Script (`tests/repro/<module>-gap-<id>.spec.ts`):**
     - Create an isolated test file inside `tests/repro/` (e.g. `tests/repro/order-gap-001.spec.ts`).
     - Script structure:
       * **Setup / Navigation:** Open the target URL and initialize test conditions.
       * **Execution of Reproduction Steps:** Execute the exact user interactions (typing, clicking, toggling) in sequence.
       * **Assert Expected vs Bug Behavior:** Formulate a strict assertion expecting the correct business behavior (which will fail due to the bug, e.g. expecting feedback within 5000ms, or asserting error banner presence).
  2. **1-Click Terminal Reproduction Commands:**
     - Always provide two clear execution options in `<module-name>-gaps.md`:
       * **Direct Playwright CLI command (Universal / Zero-config):**
         # Primary QA Debug CLI (Interactive step-by-step inspector, zero timeout):
         `npx playwright test tests/repro/<module>-gap-<id>.spec.ts --project=chromium-desktop --debug`
         # Headed standard execution:
         `npx playwright test tests/repro/<module>-gap-<id>.spec.ts --project=chromium-desktop --headed`
         # Note: Ensure playwright.config.js sets `testDir: './tests'` to include tests/repro/
       * **Registered npm shortcut command:**
         `npm run <module>:gap:<id>`
  3. **Register Script in `package.json` (Optional / If Writable):**
     - If `package.json` exists in project root and is writable, register the reproduction shortcut under `scripts`:
       `"<module>:gap:<id>": "playwright test tests/repro/<module>-gap-<id>.spec.ts --headed"`
  4. **Capture Execution Failure Trace:**
     - Run the reproduction script to confirm failure and capture trace logs (`--trace on` / `test-results/`).
     - Note the exact error outcome (e.g. Timeout waiting for selector, unhandled 500 API response).


### 4.3.1. Hybrid Precondition Seeding (Direct API) & Fault Injection (page.route)
> [!TIP]
> **LESSON-LEARNED (LRN-005 / LRN-006): AVOID BRITTLE MULTI-STEP UI PRECONDITION SETUP**
> When reproducing complex bugs that depend on specific prerequisite data states (e.g., classes with 0 students, duplicate evidence hashes, rate limits, expired tokens):
> 1. **Direct API Seeding:** Use backend API/RPC calls (`request.post()`, Supabase client, or direct SQL seed) in `beforeAll` to create required prerequisite data in milliseconds, completely bypassing slow and flaky UI navigation.
> 2. **Fault Injection via `page.route()`:** When live backend data cannot be easily altered or to simulate rare edge cases (429 Rate Limit, 500 Server Crash, Network Timeouts, Fraud/Duplicate Detection Flags):
>    - Intercept network requests directly via Playwright:
>      ```typescript
>      await page.route('**/rest/v1/endpoint*', async (route) => {
>        await route.fulfill({
>          status: 200,
>          contentType: 'application/json',
>          body: JSON.stringify(mockEdgeCaseData),
>        });
>      });
>      ```
>    - This guarantees 100% deterministic, instant bug reproduction (< 2s) without polluting the staging database or depending on fragile third-party states.


### 4.3.2. Mandatory Pre-Delivery Execution & Self-Verification Gate (CHẠY THỰC TẾ TRƯỚC KHI BÀN GIAO)
> [!CRITICAL]
> **STRICT ZERO-BROKEN-CODE POLICY (KHÔNG BÀN GIAO CODE KHI CHƯA CHẠY THỬ):**
> The AI agent is STRICTLY PROHIBITED from delivering any generated code (reproduction spec, test script, helper) to the user without executing a live pre-delivery verification run first.
> 
> **Execution Protocol:**
> 1. **Immediate Execution:** Immediately after generating/editing any `.spec.ts` file, the agent MUST run:
>    `npx playwright test <path_to_spec> --project=chromium-desktop`
> 2. **Pre-flight Error Triaging:**
>    - Check for syntax errors, missing imports, unresolvable modules.
>    - Check for locator mismatches (e.g. heading vs span, outdated placeholder, missing input name, button text changes).
>    - Check for premature timeouts.
> 3. **Auto-Repair Loop:** If execution fails due to script defects or locator drift:
>    - Inspect failure screenshot and trace in `test-results/`.
>    - Refactor locator or apply `page.route()` fault injection.
>    - Re-run verification until the script executes cleanly without harness errors.
> 4. **Delivery Clearance:** ONLY when the script executes successfully and accurately asserts the target scenario (without harness/locator crashes) is the agent permitted to present the code and terminal command to the user.


### 4.3.3. Anti-Fabrication & Immediate Gap Elimination Protocol (XÁC NHẬN KHÔNG CÓ LỖI -> LẬP TỨC QUAY VỀ BƯỚC GAPS VÀ XÓA BỎ)
> [!CAUTION]
> **STRICT ANTI-FABRICATION CONTRACT (XÓA BỎ BẤT CẬP NẾU XÁC NHẬN KHÔNG CÓ LỖI TRÊN GIAO DIỆN):**
> 1. **Zero Fake Assertions:** The AI agent is STRICTLY FORBIDDEN from inventing artificial test assertions, fake mocks, or inverted logic to claim a bug is confirmed when the live execution proves otherwise.
> 2. **Immediate Rollback & Gap Elimination (Xác nhận không lỗi -> Quay về bước Gaps xóa bỏ ngay):**
>    Khi kiểm chứng trên giao diện thực tế (qua Playwright hoặc trình duyệt), nếu xác nhận hệ thống hoạt động bình thường, không có lỗi như phỏng đoán:
>    - **LẬP TỨC QUAY VỀ BƯỚC GAPS (`<module>-gaps.md`):**
>      * **XÓA BỎ HOÀN TOÀN (Purge & Delete):** Loại bỏ hoàn toàn bất cập đó khỏi danh mục `Identified Gaps (GAP-xxx)`. Tuyệt đối không để sót lại hay chuyển tiếp sang bước thiết kế Testcase!
>      * **Nếu là cơ chế an toàn hoặc luồng nghiệp vụ có chủ đích (Intended Behavior):** Ghi nhận vào mục `Verified Security Guards (GUARD-xxx, PASS)`.
>      * **Xóa bỏ Script Repro sai lệch:** Xóa bỏ file kịch bản trong `tests/repro/` ngay lập tức để tránh nhầm lẫn hoặc chạy lại dữ liệu rác.
>    - **Đồng bộ hóa State:** Cập nhật `.qa-state.json`, đảm bảo bộ testcase chỉ kiểm chứng tính năng/bảo vệ thực tế, không kiểm chứng bug ảo.

### 4.4. Mandatory DevTools Diagnostics Protocol (Console & Network Error Harvesting)
> [!IMPORTANT]
> **TRI-LAYER DEFECT GROUNDING (Visual UI + DevTools Runtime + AST Code):**
> A UI screenshot proves what the user sees, but DevTools diagnostics prove WHY it happened. Every investigated UI gap MUST harvest browser console messages and network failure logs to eliminate guesswork.

1. **Harvest Console Messages (`browser_console_messages`):**
   - After executing reproduction actions on the page, invoke `browser_console_messages` to extract browser logs.
   - **Filter specifically for:**
     * `level: "error"` messages.
     * Uncaught runtime exceptions (`TypeError`, `ReferenceError`, `SyntaxError`).
     * Unhandled Promise rejections.
     * React/Vue/framework component error boundaries or hydration mismatches.
   - If errors exist: Extract the top 1-3 distinct error messages and stack traces.
   - If clean: Explicitly record `[CLEAN - Zero Console Errors]`.

2. **Harvest Network Request Failures (`browser_network_requests`):**
   - Invoke `browser_network_requests` to inspect HTTP interactions triggered by the reproduction flow.
   - **Filter specifically for:**
     * HTTP Status `>= 400` (e.g. 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 422 Unprocessable Entity, 500 Internal Server Error, 502/504 Bad Gateway).
     * Network aborts, connection timeouts, or CORS policy blocks.
   - If failed requests exist: Record Method, Endpoint URL, Status Code, Duration, and Error Response Body.
   - If clean: Explicitly record `[CLEAN - All Network Requests 2xx/3xx]`.

3. **Diagnose Silent Failures (Crucial QA Capability):**
   - If user interaction produces NO visible UI change (button appears dead, click is ignored), but DevTools reveals an unhandled console error or a 500 API response:
     * Flag as **CRITICAL SILENT FAILURE (Unhandled Exception)** in `<module-name>-gaps.md`.
     * Explain clearly: *"UI remains static and gives no user feedback, but DevTools captures fatal runtime error: `<error>`"*.

### 4.5. Epistemic Restriction
> [!WARNING]
> Playwright MCP observes **WHAT THE APPLICATION CURRENTLY DOES**, not whether that behavior is **CORRECT BUSINESS LOGIC**. All observed behaviors remain subject to BA/PO review and confirmation.

> [!IMPORTANT]
> **Negative Testing & Security Guard Verification:**
> When verifying restricted access scenarios (e.g., Standard user cannot approve administrative orders, Non-owner cannot modify finalized records, Unauthorized role cannot export sensitive financial reports):
> - If the UI correctly displays the disabled state (`disabled`) with appropriate explanatory warning banner -> Record result: `[PASS - GUARD ACTIVE: Security guard functioning correctly]`.
> - Strictly prohibit reporting disabled or restricted buttons as a system defect (Defect/Blocker).

### 4.6. Embed Playwright Reproduction Scripts & DevTools Diagnostics into `<module-name>-gaps.md`
* Embed reproduction script paths, 1-click terminal commands (`npm run <module>:gap:<id>` and `npx playwright test ...`), executable `.spec.ts` code snippets, and DevTools console/network snippets directly into each `GAP-xxx` card within `<module-name>-gaps.md`.
* Ensure every referenced reproduction file physically exists in `tests/repro/`.
* Export the completed report and register the state artifact:
  `python scripts/state_manager.py set-artifact gap_analysis <module-name>-gaps.md`

### 4.7. Seamless Progression to Test Case Design
* To streamline the pipeline and eliminate redundant blocking gates, the workflow automatically transitions from UI investigation directly into Step 4 (`testcase-design`):
  `python scripts/state_manager.py transition TESTCASE_GENERATION "Verified gaps on live UI with Playwright reproduction scripts and DevTools diagnostics. Proceeding directly to dynamic risk-based testcase design."`
* All discovered gaps, AST evidence, reproduction scripts, and DevTools logs are embedded into `<module-name>-gaps.md` and synthesized directly into the test suite design.
* The single mandatory human decision gate occurs at **Gate 2 (Test Case Satisfaction & Approval)**, where the user reviews the complete test suite and decides whether to test or request revisions.

## 5. Expected Outputs
* Directory `tests/repro/` containing executable Playwright reproduction test files:
  - `tests/repro/<module>-gap-<id>.spec.ts` (Isolated, runnable reproduction script)
* Comprehensive clarification ticket `<module-name>-gaps.md` containing:
  - AST code evidence.
  - Step-by-step reproduction instructions.
  - Dual-dimension impact analysis (UX degradation + future technical risks).
  - Standalone Playwright reproduction script and 1-click terminal command (`npm run <module>:gap:<id>`).
  - Harvested DevTools diagnostics (console errors & failed network API responses).
* Workflow state transitioned to `TESTCASE_GENERATION`.

## 6. Failure Handling
* If the web application is unreachable or Playwright MCP fails: Report the environment blocker clearly, tag issues as `[UNABLE_TO_VERIFY_UI]`, maintain AST code evidence in the BA ticket, and provide the authored reproduction script for future execution.

## 7. Completion Criteria
* Observable UI gaps have verified, standalone Playwright reproduction scripts authored in `tests/repro/`.
* 1-click terminal reproduction commands (`npm run <module>:gap:<id>` and `npx playwright test ...`) are embedded in `<module-name>-gaps.md`.
* Workflow transitions cleanly to `TESTCASE_GENERATION`.
