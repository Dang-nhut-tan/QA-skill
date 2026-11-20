---
name: workflow-orchestrator
description: >-
  Coordinates the end-to-end AI QA testing lifecycle across all 11 skills.
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
    [*] --> INITIALIZED: Step 0 (module-intake: maps system-architecture-flows.md if missing)
    INITIALIZED --> CONTEXT_DISCOVERY: Step 1 (codegraph-context-discovery)
    CONTEXT_DISCOVERY --> GAP_ANALYSIS: Step 2 (requirement-gap-analysis: Pure Gap Analysis, Dual-Dimension Impact & Benchmark)
    CONTEXT_DISCOVERY --> DISCOVERY_INCOMPLETE: Technical Blocker / Parser Failure / Timeout
    DISCOVERY_INCOMPLETE --> CONTEXT_DISCOVERY: Retry / Resolve Technical Blocker
    
    GAP_ANALYSIS --> RUNTIME_INVESTIGATION: Step 2.5 (gap-reproduction / playwright-investigation: Live UI MCP & Repro Authoring)
    GAP_ANALYSIS --> API_INVESTIGATION: Step 2.5B (api-investigation: Verify direct backend contracts)
    
    RUNTIME_INVESTIGATION --> GAP_ANALYSIS: No bug found on UI -> Rollback & Delete Gap completely
    API_INVESTIGATION --> GAP_ANALYSIS: No bug found on API -> Rollback & Delete Gap completely
    
    RUNTIME_INVESTIGATION --> TESTCASE_GENERATION: Confirmed gaps verified with --debug -> Step 4 (testcase-design)
    API_INVESTIGATION --> TESTCASE_GENERATION: Confirmed API gaps verified -> Step 4 (testcase-design)
    
    TESTCASE_GENERATION --> TESTCASE_REVIEW: Step 4 (testcase-design: Dynamic RBC matrix)
    TESTCASE_REVIEW --> WAITING_FOR_APPROVED_TESTCASES: Step 5 [CORE HUMAN GATE: Deliver Excel & Ask Satisfaction]
    
    WAITING_FOR_APPROVED_TESTCASES --> TESTCASE_GENERATION: User not satisfied -> Revise per feedback
    WAITING_FOR_APPROVED_TESTCASES --> COMPLETED: User satisfied -> Stop & wait for manual testing
    WAITING_FOR_APPROVED_TESTCASES --> AUTOMATION_IMPLEMENTATION: User requests automation (Filter Automation Ready = Yes)
    
    AUTOMATION_IMPLEMENTATION --> AUTOMATION_EXECUTION: Phase 6.2 & 6.3 (automation-implementation)
    AUTOMATION_EXECUTION --> COMPLETED: Phase 6.4 (test-execution-debugging)
    AUTOMATION_EXECUTION --> BLOCKED: Unresolvable Environment Blocker
    COMPLETED --> [*]
```

## 4. Unrestricted Discovery & Incomplete Discovery Protocol
* **Core Rule:** **Optimize Context Consumption, NOT Discovery Coverage.**
* CodeGraph is permitted to traverse the entire dependency chain (direct, indirect, cross-module) without arbitrary hard limits on node count or depth.
* Analysis must never be truncated or culled purely to conserve token budgets.
* **Incomplete Discovery Protocol:** In the event of parser crashes, execution timeouts, or exhausted physical system resources, the system MUST transition to `DISCOVERY_INCOMPLETE` and report the exact technical bottleneck to the user. Reporting completion for incomplete analyses is strictly prohibited.
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
