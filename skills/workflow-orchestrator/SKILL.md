---
name: workflow-orchestrator
description: >-
  Coordinates the end-to-end AI QA testing lifecycle across all 10 skills.
  Enforces mandatory human checkpoints, state transitions, evidence validation,
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
    [*] --> INITIALIZED: Step 0 (module-intake)
    INITIALIZED --> CONTEXT_DISCOVERY: Step 1 (graphify-context-discovery)
    CONTEXT_DISCOVERY --> GAP_ANALYSIS: Step 2 (requirement-gap-analysis)
    
    GAP_ANALYSIS --> WAITING_FOR_REQUIREMENT_CLARIFICATION: [MANDATORY STOP 1]
    
    WAITING_FOR_REQUIREMENT_CLARIFICATION --> TESTCASE_GENERATION: Path A (User Answers)
    WAITING_FOR_REQUIREMENT_CLARIFICATION --> RUNTIME_INVESTIGATION: Path B (Skip to Playwright MCP)
    RUNTIME_INVESTIGATION --> TESTCASE_GENERATION: Step 3 (playwright-investigation)
    
    TESTCASE_GENERATION --> TESTCASE_REVIEW: Step 4 (testcase-design)
    TESTCASE_REVIEW --> WAITING_FOR_APPROVED_TESTCASES: Step 5 [MANDATORY STOP 2]
    
    WAITING_FOR_APPROVED_TESTCASES --> AUTOMATION_IMPLEMENTATION: Phase 6.1 (automation-readiness)
    AUTOMATION_IMPLEMENTATION --> AUTOMATION_EXECUTION: Phase 6.2 & 6.3 (automation-implementation)
    AUTOMATION_EXECUTION --> COMPLETED: Phase 6.4 (test-execution-debugging)
    AUTOMATION_EXECUTION --> BLOCKED: Unresolvable Environment Blocker
    COMPLETED --> [*]
```

## 4. Mandatory Human Approval Gates (Non-Negotiable)

### Gate 1: Requirement Clarification Checkpoint
* **When:** Right after Step 2 (`requirement-gap-analysis`).
* **State:** `WAITING_FOR_REQUIREMENT_CLARIFICATION`.
* **Behavior:** The agent MUST PAUSE and ask the user to choose between supplying BA/PO answers (Path A) or verifying actual behavior with Playwright MCP (Path B). The agent must NEVER proceed to test case generation without this user decision.

### Gate 2: Approved Test Cases Workbook Checkpoint
* **When:** Right after Step 5 (`testcase-review-export`).
* **State:** `WAITING_FOR_APPROVED_TESTCASES`.
* **Behavior:** The agent MUST PAUSE and deliver `<module-name>-testcases.xlsx`. The agent must NEVER start writing automation test scripts until the user reviews, marks `Automation Ready = Yes`, and uploads/confirms the file.

## 5. Checkpoint Resumption Protocol
When starting a session or resuming:
1. Check if `.qa-state.json` exists in workspace root.
2. If it exists, run: `python scripts/state_manager.py validate`.
3. Check `changed_documents`:
   * If input documents or source files changed since last run, invalidate only the downstream affected analysis.
4. Read `current_state` and resume directly from the pending step.

## 6. Completion Criteria
* Workflow reaches `COMPLETED` state.
* All intermediate artifacts (`module-context.md`, `<module>-testcases.xlsx`, test spec files, `automation-summary.md`) are verified and recorded.
