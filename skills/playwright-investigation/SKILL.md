---
name: playwright-investigation
description: >-
  Verifies discovered requirement gaps and ambiguous behaviors directly on the live UI using Playwright MCP.
  Executes reproduction steps, captures screenshot evidence, and embeds visual proof into the BA clarification ticket
  before halting at Human Gate 1 for user confirmation to proceed.
---

# Skill: Playwright UI Verification & Gap Evidence Capture (Step 3)

## 1. Description & Trigger Conditions
* **Purpose:** Proactively verify on the actual web interface whether the requirement gaps and potential defects identified in Step 2 (`requirement-gap-analysis`) actually occur. Execute step-by-step reproduction, capture high-resolution visual progression screenshots (2–3 milestone frames: Before/Input $\rightarrow$ After/Result), and embed them into the BA Clarification Ticket (`<module-name>-gaps.md`) so that stakeholders can effortlessly understand and reproduce the issues.
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

### 4.2. Execute Live UI Reproduction & Capture Visual Progression (2–3 Milestone Frames)
* To make bug reproduction effortless for BA, PO, and developers, capture **2 to 3 chronological milestone frames** for each observable UI gap:
  1. **Frame 1 (Input / Setup State):**
     - Navigate via `browser_navigate`. Fill in the test data or setup conditions via `browser_type` / `browser_fill_form`.
     - Capture the screen *before* clicking submit/trigger:
       `screenshots/<IssueID>-01-input.png` (e.g., `screenshots/GAP-001-01-input.png`).
  2. **Frame 2 (Error / Anomaly Moment):**
     - Execute the trigger action (click submit, trigger 5th failed attempt, submit empty field).
     - Capture the screen *at the exact moment* the error, missing validation, or abnormal behavior appears:
       `screenshots/<IssueID>-02-result.png` (e.g., `screenshots/GAP-001-02-result.png`).
  3. **Frame 3 (Optional — Intermediate Modal / Secondary State):**
     - If the issue triggers an unclosable dialog, broken redirect, or secondary side-effect:
       `screenshots/<IssueID>-03-modal.png`.
* **Single-Frame Fallback:** For simple static layout issues or page load anomalies (e.g., misaligned button, missing header), capturing a single frame `screenshots/<IssueID>-evidence.png` is fully acceptable.
* **Local Project Storage:** All screenshot files are saved directly inside the project's root `screenshots/` directory. Zero Base64 bytes are injected into LLM chat context. Users can freely view, share with BA, or delete them when done.
* **Record Reproduction Steps:** Detail sequential steps from the end-user perspective:
  - `1. Mở trang...`
  - `2. Nhập vào ô...`
  - `3. Bấm nút... và quan sát kết quả...`

### 4.3. Epistemic Restriction (Cảnh Báo Nhận Thức)
> [!WARNING]
> Playwright MCP observes **WHAT THE APPLICATION CURRENTLY DOES**, not whether that behavior is **CORRECT BUSINESS LOGIC**. All observed behaviors remain subject to BA/PO review and confirmation.

### 4.4. Embed Visual Proof into BA Ticket (`<module-name>-gaps.md`)
* Embed screenshot paths and reproduction steps directly into each `GAP-xxx` card within `<module-name>-gaps.md`.
* Export the completed report and register the state artifact:
  `python scripts/state_manager.py set-artifact gap_analysis <module-name>-gaps.md`

### 4.5. Transition to Mandatory Human Gate 1 & HALT EXECUTION
* Update workflow state to the approval gate:
  `python scripts/state_manager.py transition WAITING_FOR_REQUIREMENT_CLARIFICATION "Verified gaps on UI with visual progression screenshots. Halting for user proceed command"`
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
* Directory `screenshots/` containing visual evidence files:
  - `screenshots/<IssueID>-01-input.png` (Setup / Input state)
  - `screenshots/<IssueID>-02-result.png` (Observed anomaly state)
* Comprehensive clarification ticket `<module-name>-gaps.md` (in Vietnamese) containing:
  - AST code evidence.
  - Step-by-step reproduction instructions.
  - Embedded visual progression screenshots.
  - Targeted questions and options for BA/PO.
* Workflow state set to `WAITING_FOR_REQUIREMENT_CLARIFICATION`.
* Report link and summary presented to the user in chat.

## 6. Failure Handling
* If the web application is unreachable or Playwright MCP fails: Report the environment blocker clearly, tag issues as `[UNABLE_TO_VERIFY_UI]`, maintain AST code evidence in the BA ticket, and never fabricate fake screenshots.

## 7. Completion Criteria
* Observable UI gaps are verified with visual milestone screenshots.
* State is persisted as `WAITING_FOR_REQUIREMENT_CLARIFICATION`.
* Workflow is halted awaiting human instruction.
