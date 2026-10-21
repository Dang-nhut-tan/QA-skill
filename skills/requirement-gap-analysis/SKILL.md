---
name: requirement-gap-analysis
description: >-
  Analyzes inconsistencies, missing business rules, and contradictions between code and specifications.
  Produces a structured BA/PO clarification question report and enforces a mandatory workflow STOP
  for human direction (Provide answers vs. Investigate via Playwright MCP).
---

# Skill: Requirement Gap Analysis (Step 2)

## 1. Description & Trigger Conditions
* **Purpose:** Audit the reconstructed context against available requirements, identify ambiguities and potential defects, formulate high-impact BA/PO questions, and **halt execution for human decision**.
* **Triggers:**
  * Completed `graphify-context-discovery`.
  * State is `GAP_ANALYSIS`.

## 2. Inputs
* **Required:**
  * `module-context.md` from Step 1.
  * Project documents or specifications (if available).
  * `.qa-state.json`.

## 3. Prerequisites
* Source code context and dependencies have been mapped.

## 4. Step-by-step Execution Instructions
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
     * `Issue ID` (e.g. `GAP-001`)
     * `Related Flow`
     * `Current Evidence` (Code references & lines)
     * `Uncertainty`
     * `Business Impact`
     * `Question for BA/PO`
     * `Suggested Options` (Hypotheses A, B, C)
     * `Status` (`Pending`)
3. **Generate Standalone Markdown Deliverable (`<module-name>-gaps.md`):**
   * **MANDATORY:** Generate a standalone Markdown report file (e.g. `<module-name>-gaps.md` or `requirement-gaps.md`) based on `references/requirement-gaps-template.md`.
   * Structure:
     - Section 1: Executive investigation overview and risk breakdown.
     - Section 2: 5-category discrepancy table with exact source code references and AST line numbers.
     - Section 3: Detailed BA/PO question cards with code evidence, business impact, and concrete hypotheses (Option A, Option B).
     - Section 4: Reserved placeholder for runtime investigation logs (Playwright MCP observations if Path B is selected).
     - Section 5: Checkpoint 1 instructions for user response.
4. **Persist State Checkpoint & Register Artifact:**
   * Save questions into `.qa-state.json` under `clarification_issues`.
   * Register the generated report artifact:
     `python scripts/state_manager.py set-artifact gap_analysis <module-name>-gaps.md`
   * Update workflow state:
     `python scripts/state_manager.py transition WAITING_FOR_REQUIREMENT_CLARIFICATION "Awaiting user choice: BA answers or Playwright runtime investigation"`

## 5. Mandatory Human Checkpoint (CRITICAL)
> [!IMPORTANT]
> **YOU MUST STOP THE WORKFLOW HERE.**
> Before awaiting user input, the agent MUST:
> 1. Deliver the clickable markdown link to the generated report file: `[<module-name>-gaps.md](file:///path/to/<module-name>-gaps.md)`.
> 2. Present an executive summary table directly in chat showing Issue ID, Category, Flow, Risk Level, and Question.
> 3. Prompt the user with two clear choices:
>    - **Lựa chọn 1 (Path A):** Cung cấp câu trả lời từ BA / Product Owner (theo cú pháp: `Trả lời GAP-001: [Phương án / Quy định]`).
>    - **Lựa chọn 2 (Path B):** Bỏ qua làm rõ và dùng Playwright MCP để kiểm chứng hành vi thực tế của ứng dụng (Observable Runtime Investigation).
>
> **DO NOT PROCEED TO STEP 3 OR STEP 4 WITHOUT EXPLICIT USER INPUT.**

## 6. Expected Outputs
* Dedicated Markdown file: `<module-name>-gaps.md` (or `requirement-gaps.md`) exported into workspace root following `references/requirement-gaps-template.md`.
* State file updated to `WAITING_FOR_REQUIREMENT_CLARIFICATION` with `artifacts.gap_analysis` pointing to the generated file.
* Executive table and clickable file link presented directly to the user in chat.

## 7. Failure Handling
* If zero gaps are found: double-check edge cases (boundary values, throttling, role permissions). If truly clean, document the verification criteria in `<module-name>-gaps.md` and request confirmation before proceeding.

## 8. Completion Criteria
* Standalone `<module-name>-gaps.md` report is created and registered in state.
* State is persisted as `WAITING_FOR_REQUIREMENT_CLARIFICATION`.
* Report link, executive summary table, and choices are displayed in chat.
* Execution is paused waiting for user input.
