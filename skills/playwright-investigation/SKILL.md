---
name: playwright-investigation
description: >-
  Verifies discovered requirement gaps directly on the live UI using a Hybrid Architecture
  (Playwright CLI primary for white-box/codebase, Playwright MCP fallback for black-box/exploration).
  Authors executable Playwright bug reproduction scripts (tests/repro/<module>-gap-<id>.spec.ts),
  provides 1-click terminal reproduction commands (npm run <module>:gap:<id>), harvests DevTools
  runtime errors, and embeds reproducible code proof into <module-name>-gaps.md before testcase design.
---

# Skill: Playwright Live UI Verification & Reproduction (Step 3A)

## 1. Description & Trigger Conditions
* **Purpose:** Proactively verify on the actual web interface whether the requirement gaps and potential defects identified in Step 2 (`requirement-gap-analysis`) actually occur. Instead of relying on fragile, static screenshots that can capture loading screens or become obsolete, **author standalone executable Playwright bug reproduction scripts (`tests/repro/<module>-gap-<id>.spec.ts`)** for every observable gap using a Hybrid Investigation Architecture:
  * **Primary Engine (White-Box / Grey-Box): Playwright CLI Execution**
    When source code, fixtures, or Page Objects are accessible, author and execute quick repro specs (`tests/repro/` or `tests/guards/`) via Playwright CLI (`npx playwright test`). This provides ~1.5s execution speed, saves ~90% tokens by avoiding repetitive DOM snapshot round-trips, and directly produces version-controlled, CI-ready test artifacts.
  * **Secondary / Fallback Engine (Black-Box / Obfuscated DOM): Playwright MCP Interactive Tools**
    When no source code is accessible, dynamic selectors are obfuscated, or interactive step-by-step UI exploration is required: Use Playwright MCP interactive tools (`browser_navigate`, `browser_snapshot`, `browser_click`, `browser_console_messages`, `browser_network_requests`).
* **Triggers:**
  * Identified discrepancy points (gaps) from `requirement-gap-analysis`.
  * State transitions from `GAP_ANALYSIS` $\rightarrow$ `RUNTIME_INVESTIGATION` or direct progression to `TESTCASE_GENERATION`.

## 2. Inputs
* **Required:**
  * Target module URL / route and environment credentials.
  * List of identified `clarification_issues` (`GAP-xxx`) from Step 2.
  * `module-context.md` from Step 1.

## 3. Prerequisites & Tool Availability
* **Playwright Hybrid Engine:**
  * **Playwright CLI:** Installed globally or locally in repository (`npx playwright test`).
  * **Playwright MCP Server:** Configured and operational as an exploratory fallback.
* Target web application running and accessible (local dev server, staging environment, or local HTML fixtures).
* **Credentials Check:** Verify if Staging URL and test account metadata are configured in `.env.local` or environment variables (per `module-intake`). Never persist plaintext passwords or secrets in `.qa-state.json`. If required credentials are not yet set, proactively instruct the user to configure `.env.local`.

## 4. Step-by-Step Execution Instructions

### 4.0. Production Safety Gate (Pre-Execution Protection)
Prior to interacting with live forms or triggering actions on the web application:
1. **Target Environment Classification:**
   - Verify target URL against allowlisted environments (`localhost`, `127.0.0.1`, `*.test`, `*.local`, `dev.*`, `staging.*`, `uat.*`).
   - If target is **Production** or unverified: **HALT IMMEDIATELY**. Request explicit user confirmation before executing destructive UI actions (deleting records, user accounts, mass updates, or checkout payments).
2. **Deterministic Test Data Prefix:**
   - Any form inputs creating or updating records MUST use collision-resistant names prefixed with `[QA-TEST]` or `qa_<timestamp>_<uuid>`.
3. **Automated Teardown & Cleanup:**
   - Ensure created entities can be safely deleted or provide an explicit teardown script.
4. **Credential & Secret Protection:**
   - Never enter real production credentials or output unmasked tokens to console logs.

### 4.1. Identify Observable UI Gaps
* Filter the list of identified gap items from Step 2 to isolate issues that can be observed on the UI (e.g., form validation, error messages, disabled buttons, warning modals, tab transitions, redirects).
* For backend-only issues (e.g., database triggers without UI feedback, external gateway dependencies): Record `[Verified via AST - No UI Rendering]`.

### 4.2. Live UI Inspection & Verification (Hybrid Execution Protocol)
> [!IMPORTANT]
> **HYBRID ENGINE SELECTION POLICY:**
> 1. **Default (White-Box / Grey-Box with Codebase):**
>    - Author the isolated reproduction spec in `tests/repro/` and run directly via **Playwright CLI** (`npx playwright test tests/repro/<module>-gap-<id>.spec.ts`).
>    - Fast, deterministic (~1.5s), consumes minimal tokens, and instantly generates a persistent reproduction spec for CI and developers.
> 2. **Fallback (Black-Box / Obfuscated UI / Exploratory Debugging):**
>    - If selectors cannot be determined from code or an unexpected modal/interaction state occurs, activate **Playwright MCP** interactive tools (`browser_snapshot`, `browser_click`, `browser_console_messages`, `browser_network_requests`) to inspect live accessibility trees and real-time DevTools diagnostics.

Execution sequence:
1. **Navigate to Route (`browser_navigate` or spec `page.goto`):**
   - Navigate directly to target route (e.g. `https://talent.io.vn/auth/login`).
   - Await page load completion (`document.readyState === 'complete'`).
   - **Anti-Loading-Screen Clearance Protocol:** Never capture screenshots or snapshots while spinners, skeleton placeholders, or loading bars are active. Await full DOM settlement and `networkidle`.
2. **Inspect Accessibility Snapshot & DOM (`browser_snapshot` / Page Object Inspection):**
   - Inspect live accessibility tree or Page Object methods to determine real active button roles, inputs, tabs, and placeholders.
3. **Execute Interactive Verification Steps (`browser_click`, `browser_type`, `browser_fill_form` or CLI test run):**
   - Faithfully execute the user interaction sequence documented in `<module>-gaps.md`.
4. **Mandatory DevTools Diagnostics Protocol (Console & Network Logs):**
   - Harvest uncaught exceptions and 4xx/5xx token refresh failures using `browser_console_messages` or Playwright `page.on('pageerror', ...)` / `page.on('console', ...)`.
   - Harvest failed API calls or background network drops using `browser_network_requests` or Playwright `page.on('response', ...)`.
5. **Anti-False-Alarm & Valuable Guard Retention Protocol:**
   - If live interaction proves the app functions safely, displays clear validation banners, or disallows unauthorized actions:
     * **IMMEDIATELY ROLL BACK TO `<module>-gaps.md`:** Remove the suspected gap from the active defect list.
     * Reclassify under `## 2. Verified Security Guards (GUARD-xxx, PASS)`.
     * **Valuable Guard Migration:** If a reproduction spec proved the defensive validation holds, migrate it to `tests/guards/<module>-guard-<id>.spec.ts` with ID `GUARD-xxx` for permanent regression protection. If the script was defective or broken, delete it immediately.
     * **STOP:** Do NOT retain false alarms in the active gap defect list.
6. **Confirmed Gap Handling:**
   - Only when live verification proves an actual defect exists (infinite spinner, unhandled 500, silent data loss, validation bypass), author or keep `tests/repro/<module>-gap-<id>.spec.ts`.

### 4.3. Author Playwright Bug Reproduction Script & Register Terminal Commands (Confirmed Gaps Only)
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


### 4.3.3. Valuable Repro Guard Retention & Anti-Fabrication Protocol
> [!CAUTION]
> **STRICT ANTI-FABRICATION CONTRACT & GUARD RETENTION:**
> 1. **Zero Fake Assertions:** The AI agent is STRICTLY FORBIDDEN from inventing artificial test assertions, fake mocks, or inverted logic to claim a bug is confirmed when live execution proves otherwise.
> 2. **Differentiate Script Quality on Proven System Defense:**
>    When empirical verification proves the application functions safely (e.g. form validation alert displays, unauthorized action is blocked):
>    - **Defective / Broken Script:** If the script failed due to wrong selectors, outdated DOM assumptions, or test harness crashes $\rightarrow$ **DELETE immediately**.
>    - **Valuable Defensive Guard:** If the script correctly modeled the negative scenario and verified that the UI defense works $\rightarrow$ **DO NOT DELETE!**
>      * Migrate script to `tests/guards/<module>-guard-<id>.spec.ts`.
>      * Rebrand issue ID from `GAP-xxx` to `GUARD-xxx`.
>      * Retain as an automated regression guard.
> 3. **Roll Back from Active Gap List:**
>    - In `<module>-gaps.md`, purge the item from `Identified Gaps (GAP-xxx)` and record under `## 2. Verified Security Guards (GUARD-xxx, PASS)`.
>    - Synchronize `.qa-state.json`.

### 4.3.4. Zero Hardcoded Timeout Rule
> [!WARNING]
> **LESSON-LEARNED (LRN-015): STRICT PROHIBITION ON `waitForTimeout()` AND ARBITRARY SLEEPS**
> Hardcoded sleeps cause flakiness and artificial slowdowns. Use web-first asynchronous assertions:
> 1. **Verify Zero Request Triggered (Safe Silent Drop / Form Validation Guard):**
>    - Wrap `page.waitForRequest(...)` in a short timeout Promise with catch fallback:
>      ```typescript
>      const requestPromise = page.waitForRequest(
>        (req) => req.url().includes('/rest/v1/') || req.url().includes('target-api'),
>        { timeout: 1500 }
>      ).then(() => true).catch(() => false);
>
>      await triggerButton.click();
>      const wasDispatched = await requestPromise;
>      expect(wasDispatched).toBe(false);
>      ```
> 2. **Network / Navigation Settlement:**
>    - Use `await page.waitForLoadState('networkidle')` or `await page.waitForResponse(...)`.
> 3. **Locator / Visual State Settlement:**
>    - Use web-first auto-retrying assertions: `await expect(locator).toBeVisible({ timeout: 5000 })`, `toBeEnabled()`, `toHaveText()`.
> 4. **URL Transition Settlement:**
>    - Use `await page.waitForURL('**/expected/path**', { timeout: 10000 })`.

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
