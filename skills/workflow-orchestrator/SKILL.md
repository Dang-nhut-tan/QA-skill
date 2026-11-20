---
name: workflow-orchestrator
description: >-
  Coordinates the end-to-end AI QA testing lifecycle across all 13 skills.
  Enforces mandatory human checkpoints, dual-track investigation (UI & API), state transitions, evidence validation,
  and checkpoint resumption.
---

# Skill: QA Workflow Orchestrator

## 1. Description & Trigger Conditions
* **Purpose:** Serves as the central governor of the QA Agent System. Manages sequential lifecycle transitions, monitors checkpoint persistence in `.qa-state.json`, halts execution at mandatory human gates, and resumes interrupted sessions seamlessly.
* **Triggers:**
  * Invocation of master QA commands (e.g., *"Run full QA workflow on <Module>"*).
  * Session resumption after a user checkpoint response.
  * Direct invocation by `AGENTS.md`.

## 2. Inputs
* Target module name, user requirements, and repository context.
* Existing `.qa-state.json` (if resuming).

## 3. Workflow State Machine & Lifecycle Graph

```mermaid
stateDiagram-v2
    [*] --> INITIALIZED: Step 0 (module-intake: repo context & benchmark flows)
    INITIALIZED --> CONTEXT_DISCOVERY: Step 1 (codegraph-context-discovery: AST call tree)
    CONTEXT_DISCOVERY --> GAP_ANALYSIS: Step 2 (requirement-gap-analysis: gaps & UX impact)
    CONTEXT_DISCOVERY --> DISCOVERY_INCOMPLETE: Ceiling Reached / Technical Blocker
    DISCOVERY_INCOMPLETE --> CONTEXT_DISCOVERY: Retry / Adjust Ceilings
    
    GAP_ANALYSIS --> RUNTIME_INVESTIGATION: Step 3A (playwright-investigation: live UI verification)
    GAP_ANALYSIS --> API_INVESTIGATION: Step 3B (api-investigation: direct API/RPC verification)
    GAP_ANALYSIS --> TESTCASE_GENERATION: Logical Gaps (no UI/API rendering)
    GAP_ANALYSIS --> WAITING_FOR_REQUIREMENT_CLARIFICATION: Spec Ambiguity Gate (optional)
    
    RUNTIME_INVESTIGATION --> GAP_ANALYSIS: No bug found on UI -> Rollback & Delete Gap
    API_INVESTIGATION --> GAP_ANALYSIS: No bug found on API -> Rollback & Delete Gap
    
    RUNTIME_INVESTIGATION --> TESTCASE_GENERATION: Confirmed UI gaps verified -> Step 4 (testcase-design)
    API_INVESTIGATION --> TESTCASE_GENERATION: Confirmed API gaps verified -> Step 4 (testcase-design)
    WAITING_FOR_REQUIREMENT_CLARIFICATION --> TESTCASE_GENERATION: User resolved ambiguities
    
    TESTCASE_GENERATION --> TESTCASE_REVIEW: Step 4 -> Step 5 (testcase-design to export)
    TESTCASE_REVIEW --> WAITING_FOR_APPROVED_TESTCASES: Step 5 [CORE HUMAN GATE: Deliver Excel]
    
    WAITING_FOR_APPROVED_TESTCASES --> COMPLETED: User approves manual testing
    WAITING_FOR_APPROVED_TESTCASES --> TESTCASE_GENERATION: User requests revisions (feedback loop)
    WAITING_FOR_APPROVED_TESTCASES --> AUTOMATION_IMPLEMENTATION: User approves automation implementation
    
    AUTOMATION_IMPLEMENTATION --> AUTOMATION_EXECUTION: Step 6 -> Step 7 (CLI Run & Repair)
    AUTOMATION_EXECUTION --> COMPLETED: Green tests & evidence registered
    AUTOMATION_EXECUTION --> AUTOMATION_IMPLEMENTATION: Auto-repair loop (max 2 retries)
    AUTOMATION_EXECUTION --> BLOCKED: Unresolvable Environment Blocker
    COMPLETED --> [*]
```

## 4. Controlled Discovery & DISCOVERY_INCOMPLETE Protocol
* **Core Rule:** **Optimize Context Consumption, NOT Discovery Coverage.**
* CodeGraph is authorized to traverse the full dependency tree (direct, indirect, cross-module) bounded by configurable operational ceilings (`max_depth`, `max_nodes`, execution timeout) to safeguard host memory and runtime.
* **Incomplete Discovery Protocol:** In the event of reaching operational ceilings, parser crashes, SQLite locks, or execution timeouts, the system MUST transition to `DISCOVERY_INCOMPLETE` and report the exact technical bottleneck and untraversed node identifiers. Falsely declaring completion when traversal was truncated or partial is strictly prohibited.
* **Mandatory Step 3 Gate (Zero-Bypass Enforcement - LRN-014):**
  - The orchestrator is STRICTLY PROHIBITED from skipping or bypassing Step 3 (`playwright-investigation` / `api-investigation`).
  - When transitioning out of `GAP_ANALYSIS`, if any observable UI or API gaps are identified, the workflow MUST execute live inspection (Playwright MCP or direct API request dispatch) and author verified `--debug` reproduction specs for confirmed defects BEFORE advancing to `TESTCASE_GENERATION`. Jumping directly from static AST gap analysis to testcase generation is a critical compliance violation.

## 5. Core Human Review Gate (Test Case Satisfaction & Approval)

### Core Checkpoint: Test Case Satisfaction Review
* **When:** Right after Step 5 (`testcase-review-export` generates and audits `<module-name>-testcases.xlsx`).
* **State:** `WAITING_FOR_APPROVED_TESTCASES`.
* **Behavior:**
  1. Deliver `<module-name>-testcases.xlsx` and the executive test summary table in chat.
  2. Ask the user the central review question:
     **"Bạn có hài lòng với bộ testcase hiện tại không?"** *(Are you satisfied with the current test cases?)*
  3. **Handle User Responses:**
     * **If Satisfied ("Có" / "Hài lòng" / "OK"):**
       - **Stop and wait for manual testing:** The workflow halts and remains ready for manual QA execution.
       - **(Optional Automation):** If the user instructs to automate (or sets `Automation Ready = Yes`), transition to `AUTOMATION_IMPLEMENTATION`.
     * **If Not Satisfied / Revisions Requested ("Không" / "Chưa hài lòng" / "Cần sửa"):**
       - Gather user feedback and transition state back to `TESTCASE_GENERATION`.
       - Update, add, or refine test cases until the user is 100% satisfied.

## 6. Checkpoint Resumption Protocol
When starting a session or resuming:
1. Check if `.qa-state.json` exists in workspace root.
2. If it exists, run: `python scripts/state_manager.py validate`.
3. Check `changed_documents`:
   * If input documents or source files changed since last run, invalidate only the downstream affected analysis.
4. Read `current_state` and resume directly from the pending step.

## 7. Completion Criteria
* Workflow reaches `COMPLETED` state.
* All intermediate artifacts (`module-context.md`, `<module>-gaps.md`, optional `<module>-runtime-investigation.md`, `<module>-testcases.xlsx`, test spec files, `automation-summary.md`) are verified and recorded.
