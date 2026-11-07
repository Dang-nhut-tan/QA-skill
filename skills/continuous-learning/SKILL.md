---
name: continuous-learning
description: >-
  Detects recurring errors, framework quirks, and complex project obstacles.
  Synthesizes actionable lesson-learned proposals and presents them to the user.
  Upon user approval, automatically injects the verified knowledge into target skills.
---

# Skill: Continuous Learning & Dynamic Skill Evolution

## 1. Description & Trigger Conditions
* **Purpose:** Monitor the QA lifecycle for repetitive errors, synchronization bottlenecks, or project-specific quirks. Synthesize hard-won lessons into actionable rules. Present proposals to the user, and **upon user approval, automatically inject the knowledge into the appropriate Skill file** to permanently avoid making the same mistakes.
* **Triggers:**
  * An automation test fails $\ge 2$ times with the same root cause (e.g., locator instability, animation delay).
  * A complex authentication/mocking quirk is successfully diagnosed and resolved.
  * User gives feedback or requests learning (e.g., *"Save this troubleshooting lesson"*, `/learn`).
  * Concluding Phase 6.4 (`test-execution-debugging`) with notable fixes.

## 2. Inputs
* **Required:**
  * Error stack trace, debug history, and verified fix.
  * Target skill name to be augmented (e.g., `automation-implementation`, `playwright-investigation`).
* **References:**
  * `scripts/learn_manager.py`
  * `references/project-learnings.json`

## 3. Step-by-step Execution Instructions

1. **Pattern & Obstacle Detection:**
   * Scan execution logs and debugging history for:
     * *Flaky Locators:* Elements requiring special attributes (`data-section`, accessibility labels).
     * *Timing/Race Conditions:* Complex transitions needing specific web-first waiting instead of blind retries.
     * *Domain Quirks:* Special headers, auth token caching, or device state traps.
2. **Synthesize Proposal:**
   * Invoke `scripts/learn_manager.py`:
     `python scripts/learn_manager.py propose "<Short Title>" "<Recurring Error / Obstacle>" "<Root Cause>" "<Optimal Fix>" "<target_skill>"`
   * Proposal is assigned a unique ID (e.g., `LRN-001`) with status `PENDING_APPROVAL`.
3. **Present Proposal to User for Explicit Approval:**
   * Display a clean, actionable prompt to the user:
     ```text
     [AI PROJECT LESSON-LEARNED PROPOSAL DETECTED]
     - Proposal ID: LRN-001
     - Issue Encountered: Submit button double-clicked due to network lag causing account lock
     - Root Cause: Project implements asynchronous useSubmitOnce hook
     - Optimal Fix: Assert disabled state or await response before secondary click
     - Target Skill: automation-implementation

     Do you approve injecting this lesson into the target skill? (Approve / Reject / Edit)
     ```
4. **Execute Structured Learning Upon Approval:**
   * When user confirms *"Approve"* or confirms proposal:
     Run: `python scripts/learn_manager.py approve <PROPOSAL_ID>`
   * The script activates and stores the verified learning in `references/project-learnings.json` (STATUS: APPROVED).
   * **Zero Token Bloat Guarantee:** `SKILL.md` core files remain immutable and clean. Instead, active skills dynamically retrieve relevant learnings at runtime using:
     `python scripts/learn_manager.py query --skill <target_skill> --module <module_name>`
5. **Rejection or Discard:**
   * If user rejects: `python scripts/learn_manager.py reject <PROPOSAL_ID>` to mark it REJECTED without modifying state or reference files.

## 4. Expected Outputs
* Proposal recorded and updated in `references/project-learnings.json` (Structured JSON storage).
* Dynamic runtime query availability via `learn_manager.py query`.
* Zero unbounded token inflation in static `SKILL.md` files.
* Trace recorded in `.qa-state.json`.

## 5. Human Approval Requirements
* **MANDATORY:** AI must NEVER silently edit a skill's permanent instructions without explicit user approval.

## 6. Completion Criteria
* Proposal either approved and injected into skill, or discarded per user directive.
