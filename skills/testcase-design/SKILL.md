---
name: testcase-design
description: >-
  Designs a prioritized, dynamic risk-based test suite (RBC) scaled to module complexity tiers
  (Tier S: 5-8, Tier M: 10-18, Tier L: 18-30+). Employs accessible business wording in English,
  100% bidirectional traceability, and separates defect Severity from test execution Priority.
---

# Skill: Risk-Based Test Case Design (Step 4)

## 1. Description & Trigger Conditions
* **Purpose:** Transform verified module context, gap resolutions, and UI findings into a prioritized, high-leverage test suite scaled dynamically by module risk tiers (Tier S: 5-8, Tier M: 10-18, Tier L: 18-30+). Employs user-centric business terminology so non-technical stakeholders can immediately understand and execute all steps.
* **Triggers:**
  * Completed `playwright-investigation` and user approved proceeding from Gate 1 (`"proceed"` or BA answers).
  * State is `TESTCASE_GENERATION`.

## 2. Inputs
* **Required:**
  * Updated `module-context.md` (containing confirmed rules and resolved gaps).
  * `.qa-state.json`.
* **References:**
  * `references/severity-guidelines.md`
  * `references/risk-based-coverage-matrix.md`
  * `references/testcase-quality-checklist.md`
  * `references/business-terminology-guide.md`

## 3. Prerequisites
* Module context and business flows are mapped without unresolved critical contradictions.
* User has explicitly confirmed proceeding from Checkpoint 1.

## 4. Step-by-Step Execution Instructions

### 4.1. Dynamic Risk-Based Coverage Allocation (RBC)
* > [!IMPORTANT]
* > **DO NOT USE RIGID QUOTAS:** Strictly avoid hardcoded test counts (e.g., forcing 15 or 20 cases on every module).
* > Determine test suite scale and composition based on **Module Complexity Tier** and **Risk Score (Risk = Impact x Probability)** following `references/risk-based-coverage-matrix.md`:
* **Identify Module Complexity Tier:**
  * **Tier S (Simple — 5 to 8 test cases):** 1-step forms, simple password changes, read-only directory lookup, basic profile edits. *Strictly prohibit padding with useless tests.*
  * **Tier M (Standard — 10 to 18 test cases):** Multi-channel Auth, Multi-step Checkout, Profile & Security settings, Search & filtering, Resource booking, Form throttling and rate-limiting.
  * **Tier L (Complex / Core — 18 to 30+ test cases):** Payment gateways, Billing & invoice engines, Multi-tier hierarchical approvals, Session security, Concurrency, and distributed sync.
* **Strict Role of Defect Severity (Column H):**
  * `Severity` reflects the **inherent damage of a bug if it occurs** (`Critical/Blocker` = Crash/Data Loss/Total Blockage; `Major` = Calculation/State Error/Validation Breach; `Minor` = Cosmetic/Typo/Minor UI Flaw), **NOT a production quota**.
* **Risk Priority (Execution Order):**
  * **P0 (Critical / Blocker):** Happy path core flows, security boundaries, financial accuracy, crash prevention.
  * **P1 (High):** Major boundary conditions, complex validation rules, state transitions.
  * **P2 (Normal / Low):** Minor cosmetic edge cases, rare alternate paths.

### 4.2. Business-Friendly Phrasing Standard (MANDATORY)
> [!IMPORTANT]
> **COMPLIANCE REQUIRED: `references/business-terminology-guide.md`**  
> Test cases must be drafted in clear, professional **English** so that non-IT stakeholders (Manual Testers, BAs, Product Owners, Business Users) immediately understand the purpose and can follow each step on screen without technical friction.
* **Strict Prohibition of Raw Developer Jargon:**
  * Prohibit: *"flood brake"*, *"silent drop"*, *"web_anon"*, *"RPC"*, *"UI returns"*, *"DB row not inserted"*, *"insufficient_privilege"*, *"shoot payload"*.
  * Standard business replacements:
    - *"Rate limiting"* $\rightarrow$ *"Request limit exceeded / Prevent rapid continuous submissions"*
    - *"Silent drop"* $\rightarrow$ *"Display generic confirmation for security without creating duplicate records"*
    - *"UI returns error"* $\rightarrow$ *"Screen displays message: ..."*
    - *"DB row not inserted"* $\rightarrow$ *"System does not create a new persistence record"*
    - *"web_anon RPC call"* $\rightarrow$ *"Unauthenticated user performs action"*
    - *"insufficient_privilege"* $\rightarrow$ *"System denies access and displays authorization required notice"*
* **Actionable On-Screen Test Steps (Numbered):**
  * Write user-centric sequential steps: `1. Open screen...`, `2. Enter into [Field Name] value...`, `3. Click [Button Name]...`, `4. Observe...`.
* **Two-Tier Expected Results:**
  * *Tier 1 (UI Presentation):* What the user sees on screen (messages, button disabled state, modal).
  * *Tier 2 (Underlying Data State - if applicable):* Record status in management system.

### 4.3. Populate Required 13 Columns for Each Test Case:
* **Test Case ID:** Unique key (`TC-<MODULE>-001`).
* **Module:** Target module name (e.g., `Authentication`, `Shift Management`, `Orders`).
* **Test Case Name:** Clear, actionable description in business English.
* **Preconditions:** Explicit starting state, auth status, test account.
* **Test Data:** Exact inputs or boundary values.
* **Test Steps:** Numbered reproduction steps (`1. ...\n2. ...`).
* **Expected Result:** Clear, verifiable outcome in business English.
* **Severity:** Standardized label: `Critical` (or `Blocker`), `Major`, or `Minor`.
* **Automation Ready:** `Yes` or `No` (Mark `Yes` only if repeatable and objectively assertable).
* **Automation Blocker:** Reason if `Automation Ready = No`.
* **Requirement Reference:** Code symbol or spec ID (e.g., `SPEC-AU-01`, `useSubmitOnce`).
* **Notes:** Context notes or device assumptions.
* **Status:** Initial execution status (`Pass`, `Fail`, `Pending`, `Skip`). Default is always `Pending`.

### 4.4. Bidirectional Requirement Traceability & Deduplication
* **Forward Traceability:** 100% of critical requirements in `module-context.md` must have $\ge 1$ test case (`orphan_requirements_count == 0`).
* **Backward Grounding:** 100% of test cases must cite verified spec tags or AST code symbols in `Requirement Reference` (`orphan_testcases_count == 0`). Zero fabricated/hallucinated tests.
* **Deduplication:** Zero duplicate test cases with identical objectives and actions (`duplicate_groups_count == 0`).

### 4.5. Transition Workflow State
* Invoke: `python scripts/state_manager.py transition TESTCASE_REVIEW "Generated dynamic risk-based test cases with 100% Traceability and Business-Friendly Wording"`.

## 5. Expected Outputs
* Structured dataset conforming to the 13-column schema tailored to the Module Tier (Tier S: 5-8, Tier M: 10-18, Tier L: 18-30+).
* Coverage summary metadata.
* Updated `.qa-state.json` transitioning to `TESTCASE_REVIEW`.

## 6. Failure Handling
* If test cases cannot be generated due to severe requirement uncertainty: return to Step 2 and formulate targeted gap questions.

## 7. Completion Criteria
* Full test case suite designed adhering to the 13-column schema, Risk-Based Coverage, and clear English business terminology.
* State transitioned to `TESTCASE_REVIEW`.
