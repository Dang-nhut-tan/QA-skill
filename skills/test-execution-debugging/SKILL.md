---
name: test-execution-debugging
description: >-
  Executes automated test suites using the project CLI (e.g. Playwright CLI), diagnoses failures,
  performs controlled auto-repairs on script/locator defects, conducts up to two verification reruns,
  and compiles the final verifiable execution report.
---

# Skill: Test Execution, Diagnosis & Debugging (Phase 6.4)

## 1. Description & Trigger Conditions
* **Purpose:** Run the implemented automation test scripts, capture pass/fail telemetry, classify failure root causes, auto-repair script-level defects within strict boundaries, and produce the final evidence-backed execution report.
* **Triggers:**
  * Completed `automation-implementation`.
  * State is `AUTOMATION_EXECUTION`.

## 2. Inputs
* **Required:**
  * Implemented test files from Phase 6.3.
  * Target environment base URL and configuration.
  * `.qa-state.json`.

## 3. Prerequisites
* Project test runner CLI (e.g. `npx playwright test`, `pytest`) installed and operational.

## 4. Step-by-step Execution Instructions
1. **Verify CLI Runner & Command Syntax:**
   * Run runner help or version command (e.g. `npx playwright --version`).
   * Assemble targeted command targeting only the new spec file:
     `npx playwright test <spec-file> --reporter=list`.
2. **Execute Initial Run & Collect Logs:**
   * Run the test suite and capture stdout, stderr, and test traces.
   * Parse passed, failed, and skipped counts.
3. **Failure Root-Cause Classification:**
   * If any test fails, classify the cause into one of:
     * `[LOCATOR_DEFECT]`: Selector changed, not found, or ambiguous.
     * `[SYNCHRONIZATION_ISSUE]`: Action fired before element was actionable or network request finished.
     * `[TEST_DATA_ISSUE]`: Mock data expired or account already registered/locked.
     * `[ENVIRONMENT_ISSUE]`: Server returned 502/503 or network timed out.
     * `[SUSPECTED_APP_DEFECT]`: UI / API returned unexpected error despite correct inputs.
     * `[CONFIRMED_APP_DEFECT]`: Definite bug verified by logs and matching requirement contradiction.
4. **Controlled Automatic Repair Policy:**
   * **Allowed Auto-Repairs:**
     * Updating an outdated locator to a semantic accessible selector.
     * Adding proper web-first assertions or waiting for specific API response.
     * Adjusting collision-resistant data generator.
   * **Strictly Prohibited:**
     > [!CAUTION]
     > - NEVER alter user-approved Expected Results just to force a passing status.
     > - NEVER delete or comment out failing assertions.
     > - NEVER mark a test as Passed without an actual green verification rerun.
     > - NEVER modify application source code during test debugging without user consent.
5. **Rerun & Flakiness Verification Policy:**
   * Permit **up to TWO (2) verification reruns** for affected tests after a code fix.
   * If a test fails twice for the same underlying issue: STOP auto-repairing and document it as an unresolved defect.
   * Distinguish true fixes from flaky tests (intermittent passes).
6. **Generate Final Execution Deliverable:**
   * Produce `automation-summary.md` with:
     * Executive Summary Table (Total, Passed, Failed, Duration).
     * Traceability Matrix: Mapping Excel Test Case ID -> Automated Test Function -> Result.
     * Defect Log: Detail every failed test with error stack, screenshot link, and classified cause.
7. **Complete Workflow:**
   * Register execution deliverable and finalize workflow state:
     ```bash
     python scripts/state_manager.py set-artifact automation_summary automation-summary.md
     python scripts/state_manager.py transition COMPLETED "Workflow execution completed successfully"
     ```

## 5. Expected Outputs
* `automation-summary.md` detailing verifiable results and defect classifications.
* Updated test scripts (if repaired).
* Execution screenshots / trace files.
* `.qa-state.json` transitioning to `COMPLETED`.

## 6. Failure Handling
* If test execution is completely blocked by environment downtime: record state as `BLOCKED`, document the network/server blocker, and halt.

## 7. Human Approval Requirements
* If a confirmed application defect is discovered, immediately flag it for developer review.

## 8. Completion Criteria
* All tests executed with verified results.
* No unconfirmed claims of success.
* State is `COMPLETED`.
