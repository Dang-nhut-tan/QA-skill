---
name: requirement-gap-analysis
description: >-
  Audits inconsistencies, missing business rules, and contradictions between code and specifications.
  Collaborates with Playwright MCP to verify observable UI issues with screenshots, compiles the BA
  clarification ticket (<module>-gaps.md in Vietnamese), and halts at Human Gate 1 until the user commands to proceed.
---

# Skill: Requirement Gap Analysis (Step 2)

## 1. Description & Trigger Conditions
* **Purpose:** Audit the reconstructed context against available requirements, identify ambiguities and potential defects, trigger live UI verification with screenshot capture via Playwright MCP, compile a visual BA/PO clarification report (`<module>-gaps.md`), and **halt execution for mandatory human confirmation**.
* **Triggers:**
  * Completed `graphify-context-discovery` in full workflow orchestrator (`GAP_ANALYSIS`).
  * **Standalone Invocation:** Direct user request to investigate gaps for a module (e.g., *"Điều tra bất cập phân hệ Đăng Nhập"*, *"Phân tích gap module <Module>"*).

## 2. Inputs
* **Required:**
  * `module-context.md` (reused if cached, or generated on-demand).
  * Project documents or specifications (if available).
  * Target module name.
  * `.qa-state.json`.

## 3. Prerequisites & Standalone Execution Architecture
* **Full Workflow Mode:** Expects `module-context.md` from Step 1 (`graphify-context-discovery`).
* **Standalone Execution Mode (Single-Skill Trigger):**
  * When invoked directly with a module name:
    1. **Cache Check:** Check if `module-context.md` or existing Graphify dependency cache exists for the module.
    2. **Cache Hit:** Immediately reuses the AST context—zero token waste, skips re-parsing, and immediately jumps to discrepancy detection.
    3. **Cache Miss (Cold Start):** Automatically runs Step 1 (`graphify-context-discovery`) in the background to discover unrestricted AST dependencies first, then continues seamlessly.
    4. **Focused Output:** Produces the dedicated visual report `<module-name>-gaps.md`, provides the clickable link, and stops at Gate 1. It does NOT force subsequent test case design or automation steps unless explicitly requested by the user.

## 4. Step-by-Step Execution Instructions
1. **Discrepancy & Ambiguity Audit:**
   * Compare documented rules against code AST implementations.
   * Categorize findings into 5 distinct categories:
     1. `Requirement Ambiguity`: Unspecified behavior (e.g., lockout duration not defined).
     2. `Potential Implementation Defect`: Code exhibits suspicious logic or unhandled edge cases.
     3. `Missing Documentation`: Feature exists in code but has zero written specification.
     4. `Environment / Test Data Limitation`: Feature requires external SMS/email gateway or hardware.
     5. `Confirmed Defect`: Clear breach of explicit documented business rule.
2. **Formulate BA/PO Clarification Table:**
   * Create prioritized table with columns:
     * `Issue ID` (e.g., `GAP-001`)
     * `Related Flow`
     * `Current Evidence` (Code references & lines)
     * `Uncertainty`
     * `Business Impact`
     * `Question for BA/PO`
     * `Suggested Options` (Hypotheses A, B, C)
     * `Status` (`Pending`)
3. **Trigger Playwright MCP UI Verification & Screenshot Capture (Step 3 Collaboration):**
   * **Mandatory UI Verification Before BA Ticket Delivery:**
     - For every gap observable on the web UI:
     - Activate `playwright-investigation` (Step 3) to navigate to the live screen.
     - Execute concrete interaction steps to verify if the discrepancy occurs.
     - **Capture screenshot evidence (`.png`)** saved into `screenshots/<IssueID>-evidence.png` (e.g., `screenshots/GAP-001-evidence.png`).
     - Record step-by-step reproduction instructions from the end-user perspective (`1. Mở... 2. Nhập... 3. Quan sát...`).
     - For backend-only logic lacking UI: explicitly tag `[Verified via AST - No UI Rendering]`.
4. **Generate Standalone Deliverable (`<module-name>-gaps.md`):**
   * **Deliverable Language Rule:** The generated deliverable `<module-name>-gaps.md` MUST be produced in **Vietnamese** following `references/requirement-gaps-template.md` so that local BA, PO, and business users can understand and act on it immediately.
   * Structure:
     - Investigation overview and 5-category summary table.
     - Detailed issue cards for each `GAP-xxx` with AST code evidence, UI reproduction steps, and **embedded Playwright MCP screenshots**.
     - Direct questions for BA/PO and concrete options (Option A, Option B).
5. **Persist State Checkpoint & Register Artifact:**
   * Save questions into `.qa-state.json` under `clarification_issues`.
   * Register the generated report artifact:
     `python scripts/state_manager.py set-artifact gap_analysis <module-name>-gaps.md`
   * Update workflow state:
     `python scripts/state_manager.py transition WAITING_FOR_REQUIREMENT_CLARIFICATION "Gaps verified via Playwright MCP with screenshots. Awaiting user confirmation to proceed"`

## 5. Mandatory Human Checkpoint 1 (CRITICAL STOP)
> [!IMPORTANT]
> **THE AGENT MUST HALT EXECUTION COMPLETELY HERE.**
> Before pausing, the agent MUST:
> 1. Deliver the clickable markdown link to the generated report file: `[<module-name>-gaps.md](file:///path/to/<module-name>-gaps.md)`.
> 2. Present an executive summary table directly in chat showing Issue ID, Category, Flow, Screenshot Evidence, and BA Question (in polite Vietnamese).
> 3. **WAIT FOR EXPLICIT USER INSTRUCTION:**
>    - **User commands "tiếp tục" (or "proceed"):** Advance to Step 4 (`testcase-design`) if running full workflow.
>    - **User provides answers from BA/PO:** Update `module-context.md` with resolved business rules, mark issues as `Answered`.
>    - **In Standalone Mode:** User can review the gaps ticket, forward it to BA, or request next steps when ready.
>
> **STRICT PROHIBITION: DO NOT PROCEED TO STEP 4 WITHOUT USER COMMAND "TIẾP TỤC" OR BA ANSWERS.**

## 6. Expected Outputs
* Dedicated Markdown report: `<module-name>-gaps.md` (in Vietnamese) exported into workspace root with embedded screenshot links.
* State file updated to `WAITING_FOR_REQUIREMENT_CLARIFICATION` with `artifacts.gap_analysis` registered.
* Executive table and clickable file link presented directly to the user in chat.

## 7. Failure Handling
* If zero gaps are found: double-check edge cases (boundary values, throttling, role permissions). If genuinely clean, document verification criteria in `<module-name>-gaps.md` and request confirmation to proceed.

## 8. Completion Criteria
* Standalone `<module-name>-gaps.md` report is created with visual screenshots and reproduction steps.
* State is persisted as `WAITING_FOR_REQUIREMENT_CLARIFICATION`.
* Workflow is paused waiting for user input.
