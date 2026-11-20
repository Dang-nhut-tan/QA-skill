---
name: gap-reproduction
description: >-
  Transforms identified requirement gaps from Step 2 into verified, executable Playwright bug reproduction
  scripts (tests/repro/<module>-gap-<id>.spec.ts) with zero hardcoded timeouts, registers 1-click terminal
  commands (npm run <module>:gap:<id> & npx playwright test ... --debug), runs pre-delivery test clearance,
  and embeds verified command blocks directly under each numbered gap item in <module>-gaps.md.
---

# Skill: Gap Reproduction Engineering Standards (Step 3 Shared Capability)

## 1. Description & Trigger Conditions
* **Purpose:** Serves as the dedicated runtime engineering bridge between **Step 2 (Requirement Gap Analysis)** and **Step 4 (Test Case Design)**. Takes suspected discrepancy items (`GAP-xxx`), physically tests them on live web UI and API endpoints using Playwright MCP, eliminates false alarms (Anti-False-Alarm Protocol), authors clean standalone Playwright bug reproduction specs (`tests/repro/<module>-gap-<id>.spec.ts`) without hardcoded sleeps, executes a live `--debug` pre-delivery verification run, and embeds dedicated 1-click terminal commands under each numbered gap item in `<module>-gaps.md`.
* **Triggers:**
  * Completed Step 2 (`requirement-gap-analysis`) with identified gaps.
  * Workflow state is `RUNTIME_INVESTIGATION` or `API_INVESTIGATION`.
  * Direct user request to reproduce or verify reported requirement gaps.

## 2. Inputs
* `<module>-gaps.md` containing the numbered list of suspected gaps (`### 1. GAP-001`, `### 2. GAP-002`...).
* `module-context.md` from Step 1.
* Staging or local dev application URL (e.g. `baseURL: 'https://talent.io.vn'`).
* Test credentials from `.env.local` or `qa/demo-login.private.local`.

## 3. Step-by-Step Execution Sequence

### Phase 1: Live Verification via Playwright MCP (Empirical Verification)
1. **Navigate to Target Route (`browser_navigate`):**
   - Open target page on dev/staging environment.
   - Verify page ready state (`document.readyState === 'complete'`).
2. **Inspect Accessibility Snapshot & DOM (`browser_snapshot`):**
   - Capture live DOM tree, extract real buttons, inputs, placeholders, and container refs.
3. **Execute Suspected Failure Scenario (`browser_click`, `browser_type`):**
   - Reproduce exact user interactions.
4. **Harvest Runtime Diagnostics:**
   - Call `browser_console_messages` to capture uncaught JS exceptions and 4xx/5xx network responses.
   - Call `browser_network_requests` to catch silent backend drops.
5. **Anti-False-Alarm & Valuable Guard Retention Protocol:**
   - If live interaction proves the app functions safely, displays a clear validation message, or does not crash:
     * **IMMEDIATELY ROLL BACK TO `<module>-gaps.md`:** Remove the suspected gap from the active defect list.
     * Reclassify as `Verified Security Guards (GUARD-xxx, PASS)`.
     * **Valuable Guard Migration:** If a reproduction spec proved the defensive validation holds, migrate it to `tests/guards/<module>-guard-<id>.spec.ts` with ID `GUARD-xxx` for permanent regression protection. If the script was defective or broken, delete it immediately.
     * **STOP:** Do NOT author or retain reproduction scripts for non-existent bugs in the active gap defect list.

---

### Phase 2: Authoring Standalone Playwright Bug Reproduction Spec
For every confirmed genuine gap:
1. **Create Isolated Spec File (`tests/repro/<module>-gap-<id>.spec.ts`):**
   - Self-contained, zero-dependency on external fixtures.
   - Explicit Setup, Reproduction Steps, and Assertion proving the bug.
2. **Strict Zero Hardcoded Timeout Rule (LRN-015):**
   > [!WARNING]
   > **STRICT PROHIBITION: NEVER USE ARBITRARY SLEEPS OR `waitForTimeout()`.**
   > Hardcoded sleeps cause test flakiness and artificial slowdowns. Use web-first asynchronous assertions:
   > - **Verify Zero Request Triggered (Safe Silent Drop / Form Validation Guard):**
   >   ```typescript
   >   const requestPromise = page.waitForRequest(
   >     (req) => req.url().includes('/target-api/'),
   >     { timeout: 1500 }
   >   ).then(() => true).catch(() => false);
   >   await triggerButton.click();
   >   const wasDispatched = await requestPromise;
   >   expect(wasDispatched).toBe(false);
   >   ```
   > - **Network / Navigation Settlement:** Use `await page.waitForLoadState('networkidle')`.
   > - **Locator / Visual State Settlement:** Use `await expect(locator).toBeVisible({ timeout: 5000 })`, `toBeEnabled()`.
   > - **URL Transition Settlement:** Use `await page.waitForURL('**/expected/path**')`.

---

### Phase 3: Registration & Pre-Delivery Verification Run Gate
1. **Register Shortcut in `package.json` (under `scripts`):**
   ```json
   "<module>:gap:<id>": "playwright test tests/repro/<module>-gap-<id>.spec.ts --project=chromium-desktop --debug"
   ```
2. **Mandatory Pre-Delivery Execution Gate:**
   - Execute test locally via CLI before handing over:
     `npx playwright test tests/repro/<module>-gap-<id>.spec.ts --project=chromium-desktop`
   - Auto-repair locator drift or syntax defects if any.
   - Verify exit code is 0 and assertions cleanly reproduce target gap behavior.

---

### Phase 4: Embed Commands under Numbered Gap Items in `<module>-gaps.md`
Under each numbered gap item in `<module>-gaps.md` (`### 1. GAP-001`, `### 2. GAP-002`...):
Embed the verified 1-click execution block:
```bash
# 1. Interactive step-by-step debug inspector (Recommended for QA/Devs):
npx playwright test tests/repro/<module>-gap-<id>.spec.ts --project=chromium-desktop --debug

# 2. Headed browser execution:
npx playwright test tests/repro/<module>-gap-<id>.spec.ts --project=chromium-desktop --headed

# 3. Registered npm shortcut command:
npm run <module>:gap:<id>
```

## 4. Expected Outputs
* Verified reproduction specs in `tests/repro/<module>-gap-<id>.spec.ts`.
* Registered shortcut commands in `package.json`.
* Pre-delivery execution logs proving clean reproduction.
* Updated `<module>-gaps.md` with dedicated 1-click command blocks under each numbered gap item.
