---
name: playwright-investigation
description: >-
  Verifies discovered requirement gaps and ambiguous behaviors directly on the live UI using Playwright MCP.
  Executes reproduction steps, captures screenshot evidence, and embeds visual proof into the BA clarification ticket
  before halting at Human Gate 1 for user confirmation to proceed.
---

# Skill: Playwright UI Verification & Gap Evidence Capture (Step 3)

## 1. Description & Trigger Conditions
* **Purpose:** Proactively verify on the actual web interface whether the requirement gaps and potential defects identified in Step 2 (`requirement-gap-analysis`) actually occur. Execute step-by-step reproduction, capture high-resolution screenshot evidence, and embed them into the BA Clarification Ticket (`<module-name>-gaps.md`) so that stakeholders can effortlessly understand and reproduce the issues.
* **Triggers:**
  * Identified discrepancy points (gaps) from `requirement-gap-analysis`.
  * State transitions from `GAP_ANALYSIS` $\rightarrow$ `RUNTIME_INVESTIGATION`.

## 2. Inputs
* **Required:**
  * Target module URL / route and environment credentials.
  * List of identified `clarification_issues` (`GAP-xxx`) from Step 2.
  * `module-context.md` from Step 1.

## 3. Prerequisites
* **Playwright MCP** server configured and operational.
* Target web application running and accessible (local dev server or staging).

## 4. Step-by-Step Execution Instructions

### 4.1. Identify Observable UI Gaps
* Filter the list of identified gap items from Step 2 to isolate issues that can be observed on the UI (e.g., form validation, error messages, disabled buttons, warning modals, tab transitions, redirects).
* For backend-only issues (e.g., database triggers without UI feedback, external gateway dependencies): Record `[Verified via AST - No UI Rendering]`.

### 4.2. Execute Live UI Reproduction & Capture Screenshots
* For each observable UI gap:
  1. **Navigate:** Use `browser_navigate` to open the target route.
  2. **Execute Reproduction:** Perform the exact sequence of actions to trigger the gap (e.g., 5 consecutive invalid login attempts, submitting empty required fields, rapid double-clicks).
  3. **Capture Evidence:** Use `browser_take_screenshot` to capture the screen at the exact moment the error or abnormal state appears.
  4. **File Storage:** Save screenshots under the standardized path: `screenshots/<IssueID>-evidence.png` (e.g., `screenshots/GAP-001-evidence.png`).
  5. **Record Reproduction Steps:** Detail sequential steps from the end-user perspective:
     - `1. Mở trang...`
     - `2. Thao tác trên ô...`
     - `3. Quan sát kết quả...`

### 4.3. Epistemic Restriction (Cảnh Báo Nhận Thức)
> [!WARNING]
> Playwright MCP observes **WHAT THE APPLICATION CURRENTLY DOES**, not whether that behavior is **CORRECT BUSINESS LOGIC**. All observed behaviors remain subject to BA/PO review and confirmation.

### 4.4. Embed Visual Proof into BA Ticket (`<module-name>-gaps.md`)
* Embed screenshot paths and reproduction steps directly into each `GAP-xxx` card within `<module-name>-gaps.md`.
* Export the completed report and register the state artifact:
  `python scripts/state_manager.py set-artifact gap_analysis <module-name>-gaps.md`

### 4.5. Transition to Mandatory Human Gate 1 & HALT EXECUTION
* Update workflow state to the approval gate:
  `python scripts/state_manager.py transition WAITING_FOR_REQUIREMENT_CLARIFICATION "Verified gaps on UI with screenshots. Halting for user proceed command"`
* **HALT EXECUTION COMPLETELY HERE.**

### 4.6. Resumption Protocol (When User Responds)
* **Scenario 1 — User Commands "tiếp tục":**
  - When the user sends `"tiếp tục"`, `"proceed"`, or `"ok tiếp tục"`:
  - Record approval, transition state to `TESTCASE_GENERATION`, and initiate Step 4 (`testcase-design`).
* **Scenario 2 — User Provides BA/PO Answers:**
  - Incorporate clarified business rules into `module-context.md`.
  - Mark corresponding gap items as `Answered` in `.qa-state.json`.
  - Transition state to `TESTCASE_GENERATION` to design test cases reflecting the approved rules.

## 5. Expected Outputs
* Directory `screenshots/` containing visual evidence files: `screenshots/<IssueID>-evidence.png`.
* Comprehensive clarification ticket `<module-name>-gaps.md` (in Vietnamese) containing:
  - AST code evidence.
  - Step-by-step reproduction instructions.
  - Playwright MCP screenshots.
  - Targeted questions and options for BA/PO.
* Workflow state set to `WAITING_FOR_REQUIREMENT_CLARIFICATION`.
* Report link and summary presented to the user in chat.

## 6. Failure Handling
* If the web application is unreachable or Playwright MCP fails: Report the environment blocker clearly, tag issues as `[UNABLE_TO_VERIFY_UI]`, maintain AST code evidence in the BA ticket, and never fabricate fake screenshots.

## 7. Completion Criteria
* All observable UI gaps are verified with screenshots and reproduction steps.
* Clarification ticket `<module-name>-gaps.md` is delivered to the user.
* Execution is paused waiting for user instruction ("tiếp tục" or BA answers).
