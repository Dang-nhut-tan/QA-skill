---
name: api-investigation
description: >-
  Verifies discovered requirement gaps, backend vulnerabilities, and data contract discrepancies directly
  at the API/RPC/REST level using Playwright APIRequestContext or HTTP clients. Authors standalone executable
  Playwright API bug reproduction scripts (tests/repro/<module>-api-gap-<id>.spec.ts), provides 1-click terminal
  reproduction commands, detects silent API failures, bypasses of UI validation, and enforces immediate gap elimination
  and rollback when the API operates safely according to business rules.
---

# Skill: Direct API & Backend Service Verification & Reproduction (Step 3B)

## 1. Description & Trigger Conditions
* **Purpose:** Proactively verify requirement gaps, authorization boundaries, and data integrity constraints directly at the backend API, RPC, or REST endpoint level — completely bypassing the browser UI.
  * While `playwright-investigation` (Step 3A) verifies screen interactions and visual flows, `api-investigation` (Step 3B) exposes server-side defensive robustness:
    1. **Bypass of UI Validation:** Frontend disables submit button or enforces regex validation, but calling the raw API endpoint allows invalid, out-of-range, or malicious payloads to persist.
    2. **Silent API Failures:** Backend endpoint returns `400 / 422 / 500` or crashes with an unhandled exception, but frontend UI swallows the failure without displaying user feedback.
    3. **Data Contract & Security Flaws:** Leakage of sensitive PII fields, absence of idempotency keys causing duplicate records, or broken Role-Based Access Control (RBAC).
  * Authors standalone, deterministic, executable Playwright API reproduction specs (`tests/repro/<module>-api-gap-<id>.spec.ts`) without browser launch overhead (< 500ms execution).
* **Triggers:**
  * Identified API/Backend gap items from Step 2 (`requirement-gap-analysis`).
  * Gaps tagged with `[Category: Backend / Security / Data Integrity]`.
  * State transitions from `GAP_ANALYSIS` $\rightarrow$ `API_INVESTIGATION`.

### 1.1. Capability-Aware Dispatch & Execution Mode (Multi-Agent vs Sequential Fallback)
* The agent detects available host platform capabilities:
  - **Branch A: Dedicated Subagent Delegation (`api-investigator`):**
    When running in an environment supporting native subagent spawning (`invoke_subagent`):
    * Dispatch investigation task to subagent `api-investigator` (`agents/api-investigator.md`):
      ```json
      {
        "TypeName": "api-investigator",
        "Role": "API Investigation Specialist",
        "Prompt": "Verify identified backend/API gaps for module <ModuleName> directly at endpoint level. Author tests/repro/<module>-api-gap-<id>.spec.ts, run pre-delivery smoke check, and return verified defect proof or safe guard rollback recommendations."
      }
      ```
    * Subagent operates strictly within HTTP network calls and `tests/repro/` spec authoring.
    * Upon completion, parent collects verified reproduction specs and terminates subagent session via `manage_subagents(Action="kill")`.
  - **Branch B: Sequential Main Thread Execution (Single-Agent Fallback):**
    When running in a standard single-agent environment (Claude Code, Cursor, standalone Playwright CLI):
    * The primary agent executes the API dispatch sequentially using Playwright `request` fixture or Node.js `fetch`.
    * Directly authors `tests/repro/<module>-api-gap-<id>.spec.ts` with explicit assertions replicating the bug.
    * Embeds 1-click execution commands into `<module>-gaps.md`.
* **Universal Evidence Guarantee:** Both branches produce the identical verified artifact `tests/repro/<module>-api-gap-<id>.spec.ts` and update `.qa-state.json`. Never claim a subagent was dispatched without verified tool call execution.

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

## 3. Core API Defect Taxonomy

| Defect Code | Category | Root Cause & Failure Signature |
| :--- | :--- | :--- |
| **`API-DEF-01`** | **UI Bypass (Missing Server-side Validation)** | UI blocks input (disabled button, client regex), but direct API call accepts malformed payload, returning `200 OK` and persisting dirty data. |
| **`API-DEF-02`** | **Silent API Failure (Swallowed Backend Error)** | Backend returns `400 / 422 / 500` or uncaught exception, but frontend displays no error toast or alert, leaving users stranded or assuming success. |
| **`API-DEF-03`** | **RBAC / Privilege Escalation** | Low-privilege role calls high-privilege administrative endpoint without receiving HTTP `401 Unauthorized` or `403 Forbidden`. |
| **`API-DEF-04`** | **Race Condition & Idempotency Failure** | 2-5 concurrent requests sent with identical idempotency token produce duplicate database records or double-billing mutations. |
| **`API-DEF-05`** | **Contract & Schema Inconsistency** | Endpoint returns HTTP `200 OK` but body contains `{ "error": true, "message": "Failed" }` (anti-pattern), or returns unexpected types causing frontend parser crash. |

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

### 4.2. Mandatory Pre-Delivery Execution Gate
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
> **PROVEN BACKEND SAFETY -> IMMEDIATE GAP PURGE & ROLLBACK:**
> When calling the live API, if the backend operates securely (e.g. returns `400 Bad Request`, `403 Forbidden`, `422 Unprocessable Entity`, or strictly enforces business constraints):
> 1. **IMMEDIATELY ROLL BACK TO `<module>-gaps.md`:**
>    * **Purge & Delete:** Remove that suspected gap completely from `Identified Gaps (GAP-xxx)`. Strictly prohibit transferring false alarms to testcase design.
>    * **Reclassify as Verified Guard:** Record under `Verified Security Guards (GUARD-API-xxx, PASS)`.
>    * **Delete Faulty Script:** Delete `tests/repro/<module>-api-gap-<id>.spec.ts` immediately to keep the test suite clean.
> 2. **Synchronize Workflow State:** Update `.qa-state.json`, ensuring zero testcase generation for fabricated or non-existent bugs.

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
