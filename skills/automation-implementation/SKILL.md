---
name: automation-implementation
description: >-
  Inspects the existing project testing framework, reuses established Page Objects and fixtures,
  and writes clean, robust automation test scripts strictly mapped to approved Excel Test Case IDs.
  Non-destructive, zero arbitrary sleeps, collision-resistant data.
---

# Skill: Automation Implementation (Phases 6.2 & 6.3)

## 1. Description & Trigger Conditions
* **Purpose:** Inspect the host project's existing testing infrastructure (runner, POMs, fixtures, configs) and write production-grade automation scripts for the approved test cases without introducing unwanted boilerplate or incompatible frameworks.
* **Triggers:**
  * Completed `automation-readiness`.
  * State is `AUTOMATION_IMPLEMENTATION`.

## 2. Inputs
* **Required:**
  * List of approved automation-ready test cases from Phase 6.1.
  * Project source code and existing `tests/` directory.
  * `.qa-state.json`.

## 3. Prerequisites
* Project repository contains or supports a test framework (e.g. Playwright, Cypress, PyTest, Jest).

## 4. Step-by-step Execution Instructions

### Phase 6.2 — Inspect Existing Framework & Reusable Components:
1. **Analyze Framework Conventions:**
   * Scan project root for config files: `playwright.config.*`, `cypress.config.*`, `pytest.ini`, etc.
   * Determine test runner, language (TypeScript, JavaScript, Python), and directory conventions (`tests/specs/`, `e2e/`, etc.).
2. **Discover Reusable Assets:**
   * Search for existing Page Object Models (POM), custom fixtures, and API helpers.
   * *Rule:* Never introduce a new testing framework if the project already has one, unless the user explicitly approves.
   * *Rule:* Do not force complex POM structures if the repository follows a simpler functional test pattern. Respect the surrounding style.

### Phase 6.3 — Implement Test Automation:
1. **Script Construction Standards:**
   * **Stable Locators:** Prefer accessible roles and text (`getByRole`, `getByLabel`, `getByTestId`, or semantic `data-section`) over brittle CSS/XPath chains.
   * **No Arbitrary Sleeps:** Prohibit hardcoded `sleep(5000)` or `waitForTimeout`. Use web-first assertions and explicit auto-waiting (`toBeVisible()`, `toHaveURL()`).
   * **Test Independence:** Ensure each test can run in isolation without depending on execution side-effects of preceding tests.
   * **Collision-Resistant Test Data:** Use dynamic timestamps or random suffixes for unique fields (e.g. `testuser_${Date.now()}`).
   * **Zero Hardcoded Secrets:** Read credentials from environment variables (`process.env.TEST_USER`) or local `.env` files.
   * **Explicit ID Traceability:** Every test case must explicitly reference its Excel Test Case ID in its title and describe block (e.g., `test('TC-AUTH-001: ...')`).
2. **Review & Self-Correction:**
   * Check syntax using `node --check <file>` or language linter.
   * Ensure error messages on failed assertions provide actionable debugging clues.
3. **Transition Workflow State:**
   * Update workflow state:
     `python scripts/state_manager.py transition AUTOMATION_EXECUTION "Automation scripts generated; ready for execution"`.

## 5. Expected Outputs
* Automated test spec files adhering to the project's native style.
* Traceability mapping between spec functions and Excel Test Case IDs.
* Updated `.qa-state.json` transitioning to `AUTOMATION_EXECUTION`.

## 6. Failure Handling
* If target framework is completely missing: propose the simplest native setup (e.g. Playwright) and seek user approval before creating root configuration files.

## 7. Human Approval Requirements
* Required only if proposing a new test framework not currently in the repo.

## 8. Completion Criteria
* All approved test cases are coded into executable test files.
* State is `AUTOMATION_EXECUTION`.
