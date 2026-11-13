---
name: playwright-investigation
description: >-
  Verifies discovered requirement gaps and ambiguous behaviors directly on the live UI using Playwright MCP.
  Enforces a strict anti-loading-screen settle protocol, executes reproduction steps, captures verified visual evidence,
  and seamlessly feeds grounded UI proof into testcase design before the user review checkpoint.
---

# Skill: Playwright UI Verification & Gap Evidence Capture (Step 3)

## 1. Description & Trigger Conditions
* **Purpose:** Proactively verify on the actual web interface whether the requirement gaps and potential defects identified in Step 2 (`requirement-gap-analysis`) actually occur. Execute step-by-step reproduction, strictly ensure the page has completely settled (zero loading spinners/skeletons), capture high-resolution visual progression screenshots (2-3 milestone frames: Before/Input $\rightarrow$ After/Result), and embed them into the BA Clarification Ticket (`<module-name>-gaps.md`) so that stakeholders can effortlessly understand and reproduce the issues.
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

### 4.3. Execute Live UI Reproduction & Capture Visual Progression (2-3 Milestone Frames)
* To make bug reproduction effortless for BA, PO, and developers, capture **2 to 3 chronological milestone frames** for each observable UI gap:
  1. **Frame 1 (Input / Setup State):**
     - Navigate via `browser_navigate`. Fill in the test data or setup conditions via `browser_type` / `browser_fill_form`.
     - Verify DOM settlement, then capture the screen *before* clicking submit/trigger:
       `screenshots/<IssueID>-01-input.png` (e.g., `screenshots/GAP-001-01-input.png`).
  2. **Frame 2 (Settled Result / Error Moment):**
     - Execute the trigger action (click submit, trigger 5th failed attempt, submit empty field).
     - Wait for spinners to clear and response feedback to settle, then capture the screen *at the settled outcome moment*:
       `screenshots/<IssueID>-02-result.png` (e.g., `screenshots/GAP-001-02-result.png`).
  3. **Frame 3 (Optional — Secondary State / Modal):**
     - If the issue triggers a confirmation dialog, broken redirect, or secondary side-effect:
       `screenshots/<IssueID>-03-modal.png`.
* **Single-Frame Fallback:** For simple static layout issues or page load anomalies (e.g., misaligned button, missing header), capturing a single frame `screenshots/<IssueID>-evidence.png` is fully acceptable.
* **Local Project Storage:** All screenshot files are saved directly inside the project's root `screenshots/` directory. Zero Base64 bytes are injected into LLM chat context.
* **Record Reproduction Steps:** Detail sequential steps from the end-user perspective:
  - `1. Open page...`
  - `2. Enter into field...`
  - `3. Click button... and observe result...`

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

### 4.6. Embed Visual Proof & DevTools Diagnostics into `<module-name>-gaps.md`
* Embed screenshot paths, reproduction steps, and DevTools console/network snippets directly into each `GAP-xxx` card within `<module-name>-gaps.md`.
* **Mandatory Physical Verification & Dual-Mode Links:**
  Run the image validator to guarantee 100% of referenced screenshots physically exist on disk and inject clickable absolute fallback links:
  `python scripts/verify_and_embed_images.py <module-name>-gaps.md`
  If any screenshot is missing, the validator exits with an error and halts execution. You MUST capture the physical screenshot via Playwright before proceeding.
* Export the completed report and register the state artifact:
  `python scripts/state_manager.py set-artifact gap_analysis <module-name>-gaps.md`

### 4.7. Seamless Progression to Test Case Design
* To streamline the pipeline and eliminate redundant blocking gates, the workflow automatically transitions from UI investigation directly into Step 4 (`testcase-design`):
  `python scripts/state_manager.py transition TESTCASE_GENERATION "Verified gaps on live UI with settled screenshots and DevTools diagnostics. Proceeding directly to dynamic risk-based testcase design."`
* All discovered gaps, AST evidence, visual proofs, and DevTools logs are embedded into `<module-name>-gaps.md` and synthesized directly into the test suite design.
* The single mandatory human decision gate occurs at **Gate 2 (Test Case Satisfaction & Approval)**, where the user reviews the complete test suite and decides whether to test or request revisions.

## 5. Expected Outputs
* Directory `screenshots/` containing settled visual evidence files:
  - `screenshots/<IssueID>-01-input.png` (Setup / Input state)
  - `screenshots/<IssueID>-02-result.png` (Settled anomaly / outcome state)
* Comprehensive clarification ticket `<module-name>-gaps.md` containing:
  - AST code evidence.
  - Step-by-step reproduction instructions.
  - Dual-dimension impact analysis (UX degradation + future technical risks).
  - Embedded visual progression screenshots (verified free of loading spinners).
  - Harvested DevTools diagnostics (console errors & failed network API responses).
* Workflow state transitioned to `TESTCASE_GENERATION`.

## 6. Failure Handling
* If the web application is unreachable or Playwright MCP fails: Report the environment blocker clearly, tag issues as `[UNABLE_TO_VERIFY_UI]`, maintain AST code evidence in the BA ticket, and never fabricate fake screenshots.

## 7. Completion Criteria
* Observable UI gaps are verified with settled milestone screenshots (zero loading masks/spinners).
* Images are physically validated via `scripts/verify_and_embed_images.py`.
* Workflow transitions cleanly to `TESTCASE_GENERATION`.
