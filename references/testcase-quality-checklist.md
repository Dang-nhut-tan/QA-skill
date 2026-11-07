# Test Case Quality Checklist

All test cases designed by the agent must pass this internal quality checklist before being exported into the user-facing Excel workbook.

---

## 1. Identification & Clarity
- [ ] **Test Case ID:** Unique, stable identifier (e.g. `TC-AUTH-001`), zero collisions.
- [ ] **Test Case Name:** Clear, action-oriented description from the end-user perspective, avoiding generic titles like *"Check screen"*.
- [ ] **Accessible Business Phrasing:** Strictly avoid raw internal technical jargon (`web_anon`, `call RPC`, `UI returns`, `DB row inserted`).
- [ ] **Single Test Objective:** Each test case focuses on exactly ONE primary verification objective, avoiding bloated multi-flow scenarios.

## 2. Preconditions & Test Data
- [ ] **Preconditions:** Clearly specifies required starting state (activated account, role privileges, feature flags).
- [ ] **Test Data:** Explicitly quantifies inputs (character length, boundary values, mock account IDs).

## 3. Test Steps
- [ ] **Sequentially Numbered:** Numbered `1., 2., 3.` in clear chronological order.
- [ ] **Actionable for Non-Technical Users:** Followable directly on screen (e.g. `1. Open screen...`, `2. Enter into [Field Name]...`, `3. Click [Button Name]...`).
- [ ] **Separation of Action and Assertion:** Steps contain only actions (type, click, select); expected outcomes belong strictly in Expected Result.

## 4. Expected Result
- [ ] **Verifiable & Measurable:** Avoid ambiguous terms like *"works normally"*, *"runs fine"*. Must specify on-screen messages, HTTP status, redirect URL, or state changes.
- [ ] **Two-Tier Outcome Verification:** State what the user observes on screen (Tier 1) and what the system updates in persistence/state (Tier 2).
- [ ] **Separation of Observed vs. Desired:** Accurately reflects agreed business specifications, not confusing *"what code currently does"* with *"correct business logic"*.

## 5. Defect Severity
- [ ] **Standard Classification:** Uses standard tiers: `Critical` (or `Blocker`), `Major`, `Minor`.
- [ ] **Consistency:** Crash and blockage scenarios must be `Critical`; calculation and state errors must be `Major`; cosmetic UI flaws must be `Minor`.

## 6. Automation Readiness
- [ ] **Criteria for `Automation Ready = Yes`:**
  - Expected results are unambiguous and finalized.
  - Can be objectively asserted via code (DOM locators, API status, URL, DB state).
  - Free from insurmountable automation blockers (third-party CAPTCHA, unmockable physical SMS OTP, biometric hardware).
  - Test data can be independently set up and cleaned up.
- [ ] **If `Automation Ready = No`:** Mandatory explicit explanation in the `Automation Blocker` column.

## 7. Dynamic Risk-Based Coverage (RBC)
- [ ] **Scaled by Complexity Tier:** Simple (Tier S: 5-8 cases), Standard (Tier M: 10-18 cases), Complex (Tier L: 18-30+ cases) per `references/risk-based-coverage-matrix.md`. Prohibits padding with useless tests.
- [ ] **Strict Separation of Severity vs. Priority:** Severity reflects defect damage, not a quota.
- [ ] **Risk Priority:** P0 (Critical path, security, data integrity) cases are thoroughly covered.

## 8. Execution Status (Column M)
- [ ] **Location & Valid Values:** Column M (Column 13) dropdown with 4 values: `Pass`, `Fail`, `Pending`, `Skip`.
- [ ] **Default State:** Newly exported test cases must always default to `Pending` (amber pastel badge).
- [ ] **Result Updates:** Updated to `Pass` (mint green), `Fail` (rose pink), or `Skip` (gray) only after real execution. Marking `Pass` without live execution is strictly prohibited.

## 9. Bidirectional Traceability & Deduplication
- [ ] **Forward Coverage:** 100% of critical requirements in `module-context.md` have $\ge 1$ covering test case (`orphan_requirements_count == 0`).
- [ ] **Backward Grounding:** 100% of test cases cite explicit spec tags or AST code symbols in `Requirement Reference` (`orphan_testcases_count == 0`). Zero fabricated tests.
- [ ] **Deduplication:** Zero duplicate test cases with identical objectives and actions (`duplicate_groups_count == 0`).

## 10. Non-Technical Accessibility Without Compromising Depth
- [ ] **Accessible to Non-Technical Stakeholders:** Clear business wording allows BAs, POs, and manual testers to understand and verify.
- [ ] **Preserves 100% Analytical Depth:** Retains boundary testing, security permissions, rate limiting, and concurrency checks.
- [ ] **Terminology Compliance:** Complies with `references/business-terminology-guide.md`.
