---
name: playwright-investigation
description: >-
  Investigates observable runtime application behavior using Playwright MCP or incorporates
  BA/PO clarification answers to resolve requirement gaps before test design.
  Captures step-by-step evidence and screenshots without making unverified assumptions.
---

# Skill: Playwright Runtime Investigation & Clarification Handling (Step 3)

## 1. Description & Trigger Conditions
* **Purpose:** Process the human checkpoint from Step 2:
  * **Path A:** Integrate BA/PO answers into the system context.
  * **Path B:** Launch Playwright MCP to execute observable UI interactions, capture screenshots, and document empirical application behavior.
* **Triggers:**
  * User provides answers to BA/PO questions, OR
  * User selects to skip clarification and investigate runtime behavior.
  * Workflow state was `WAITING_FOR_REQUIREMENT_CLARIFICATION`.

## 2. Inputs
* **Required:**
  * User decision (Path A answers or Path B directive).
  * `module-context.md` with pending `clarification_issues`.
  * Application base URL and valid credentials/environment (if Path B).

## 3. Prerequisites
* For Path B: **Playwright MCP** server configured and active, target application running/accessible.

## 4. Step-by-step Execution Instructions

### Path A — User Provides BA/PO Answers:
1. Parse user answers against each `Issue ID` in `.qa-state.json`.
2. Check for contradictions with existing source code AST evidence. If a serious discrepancy exists, flag it explicitly to the user.
3. Update `module-context.md` with newly confirmed business rules, referencing the user/BA as the source.
4. Mark issue statuses as `Answered` in `.qa-state.json`.
5. Transition state to `TESTCASE_GENERATION`.

### Path B — Playwright MCP Runtime Investigation:
1. **Accessibility Check:** Verify the application endpoint is reachable using `browser_navigate`.
2. **Execute Exploration Steps:**
   * Navigate through the disputed workflow.
   * Observe actual UI rendering, field behaviors, and error messages.
3. **Capture Evidence & Screenshots:**
   * Take screenshot at each meaningful state.
   * Use descriptive naming convention: `<IssueID>-step-<NN>-<description>.png`.
   * Store screenshots in project artifacts directory.
4. **Enforce Critical Epistemic Restriction:**
   > [!WARNING]
   > Playwright MCP observes **WHAT the application currently does**, not whether that behavior is **CORRECT according to business intent**.
   * Classify findings as:
     - `Observed Behavior Confirmed`: Matches consistent pattern.
     - `Suspected Defect`: Behavior violates general logic or safety.
     - `Requirement Still Unresolved`: Ambiguity persists despite observation.
     - `Unable to Verify`: Blocked by environment/data limits.
5. **Generate Standalone Investigation Report (`<module-name>-runtime-investigation.md`):**
   * Document step-by-step reproducible exploration, observed DOM states, network payloads, and relative markdown screenshot links (`<IssueID>-step-<NN>-<description>.png`).
   * Export standalone deliverable `<module-name>-runtime-investigation.md` (and update Section 4 of `<module-name>-gaps.md`).
   * Register artifact in state:
     `python scripts/state_manager.py set-artifact investigation_report <module-name>-runtime-investigation.md`
   * Present clickable link in chat: `[<module-name>-runtime-investigation.md](file:///path/to/<module-name>-runtime-investigation.md)` so user can review the empirical investigation findings.
   * Update `module-context.md` with runtime findings.
   * Transition state:
     `python scripts/state_manager.py transition TESTCASE_GENERATION "Completed runtime investigation"`

## 5. Expected Outputs
* Standalone `<module-name>-runtime-investigation.md` report with screenshot evidence attachments.
* Updated `<module-name>-gaps.md` (Section 4 populated with runtime logs).
* State file updated to `TESTCASE_GENERATION` with `artifacts.investigation_report` recorded.
* Clickable report link presented directly to the user in chat.

## 6. Failure Handling
* If application is down or unreachable via Playwright MCP: report blocker immediately, mark status as `BLOCKED`, and do not fabricate fake screenshots or logs.

## 7. Human Approval Requirements
* If Path A reveals direct conflict between BA answer and source code, confirm with user before writing test cases.

## 8. Completion Criteria
* Sufficient clarity exists to design deterministic test cases.
* Standalone investigation report `.md` is exported and linked.
* Workflow state is `TESTCASE_GENERATION`.
