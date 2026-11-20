---
name: requirement-gap-analysis
description: >-
  Audits inconsistencies, missing business rules, and contradictions between code and specifications.
  Analyzes dual-dimension impact: User Experience (UX) degradation and future technical bug prediction.
  Synthesizes industry benchmark discrepancies from industry-benchmark-flows.md and compiles <module>-gaps.md
  with a clean numbered format (1, 2, 3...) before handing over to Step 2.5 (gap-reproduction).
---

# Skill: Requirement Gap Analysis (Step 2)

## 1. Description & Trigger Conditions
* **Purpose:** Audit the reconstructed codebase context against available requirements and industry benchmarks, uncover discrepancies, ambiguities, and potential defects, assess dual-dimension impact (User Experience degradation and future technical risk), compile the numbered gap catalogue (`<module>-gaps.md`), and hand over suspected items to **Step 2.5 (`gap-reproduction`)** for live verification and Playwright reproduction script authoring.
* **Triggers:**
  * Completed `codegraph-context-discovery` in full workflow orchestrator (`GAP_ANALYSIS`).
  * Direct user request to analyze requirement gaps for a module.

## 2. Inputs
* `module-context.md` from Step 1 (`codegraph-context-discovery`).
* `industry-benchmark-flows.md` (or `system-architecture-flows.md`) from Step 0 (`module-intake`).
* Project documentation or business rules (if available).
* Initialized `.qa-state.json`.

## 3. Step-by-Step Execution Sequence

### 3.1. Discrepancy & Ambiguity Audit (Code AST vs Specification)
* Cross-reference documented business rules against CodeGraph AST implementation facts.
* Categorize findings into 6 core analytical categories:
  1. `Requirement Ambiguity`: Unspecified or conflicting behavior.
  2. `Potential Implementation Defect`: Suspicious branch logic or unhandled edge cases.
  3. `Missing Documentation`: Feature exists in code but has zero written specification.
  4. `Environment / Test Data Limitation`: Feature requires external SMS/email gateway or mock provider.
  5. `Architectural / Cross-System Inconsistency (Cross-System Architectural Synthesis)`: Inconsistencies, contract drifts, or blindspots between local module logic and global integration flows (from `system-architecture-flows.md`).
  6. `Industry Benchmark Discrepancy & Domain Blindspot`: Inadequacies (Điểm bất cập), anti-patterns, user friction points, or missing business rules (Điểm mù) uncovered when cross-referencing against mature industry leaders (`industry-benchmark-flows.md`).

### 3.2. Strict Falsification & Negative Testing Rule (ANTI-FALSE-ALARM PROTOCOL)
* **CASE 1: VERIFIED SECURITY GUARDS / CONSTRAINTS (GUARD-xxx, PASS):**
  - If specification or business logic restricts an action (e.g., student blocked from accepting without guardian consent, button disabled for unauthorized role), and source code AST enforces this:
  - Record under `## 2. Verified Security Guards` with status `PASS`. Strictly NEVER label intended constraints as bugs or gaps.
* **CASE 2: GENUINE SUSPECTED GAPS (GAP-xxx):**
  - Record as `GAP-xxx` ONLY when there is an actual contradiction, missing validation, data loss vulnerability, or unhandled crash.

### 3.3. Mandatory Dual-Dimension Impact Assessment
For every suspected gap (`GAP-xxx`), conduct a rigorous dual-dimension evaluation:
* **Dimension 1: User Experience (UX) Impact:**
  - Operational friction, confusing / misleading error messages.
  - Behavioral traps (user assumes submission succeeded when dropped, accidental double submissions).
  - Trust degradation (frozen UI, dead buttons, unresponsiveness).
* **Dimension 2: Future Technical Risk & Potential Defect Prediction:**
  - Data corruption, orphaned records, or desynchronized cache/DB state.
  - Concurrency & race conditions under peak traffic (`workers > 1`).
  - Cascading downstream failures in billing, reporting, or scoring engines.

### 3.4. Compile Numbered Gap Catalogue in `<module>-gaps.md` (Structured Item Format)
* **Numbered Gap Catalogue Format (No Wide Horizontal Tables):** Structure suspected gaps as clear numbered items (`### 1. GAP-001`, `### 2. GAP-002`, `### 3. GAP-003`...):
  - `Issue ID` & Concise Title
  - `Category` & `Related Business Flow`
  - `Severity`: `Critical`, `Major`, `Minor`
  - `Source Code Evidence (Code AST)`: Exact file path and line range
  - `User Experience Impact (UX Impact)`: Operational friction, lost effort, confusing feedback
  - `Future Technical Risk`: Concurrency race condition, data corruption, downstream cascading failure
  - `Clarification Questions for BA/PO & Proposed Options`

### 3.5. Seamless Handover to Step 3 (Step 3A UI & Step 3B API Verification)
* Upon completing the numbered gap catalogue in `<module>-gaps.md`:
  - Update workflow state:
    `python scripts/state_manager.py transition RUNTIME_INVESTIGATION "Gap analysis completed. Handing over to Step 3 verification tracks for live verification and repro spec authoring."`
  - Hand over `<module>-gaps.md` to:
    * **Step 3A (`playwright-investigation`):** For UI-observable gaps, conduct live browser verification and author standalone `tests/repro/<module>-gap-<id>.spec.ts` specs.
    * **Step 3B (`api-investigation`):** For backend/RPC/data gaps, conduct direct endpoint verification and author standalone `tests/repro/<module>-api-gap-<id>.spec.ts` specs.
    * Both tracks strictly adhere to **Step 3 Shared Gap Reproduction Engineering standards (`gap-reproduction`)**, ensuring zero hardcoded timeouts and embedding 1-click terminal commands (`npm run <module>:gap:<id>` and `npx playwright test ...`).

## 4. Expected Outputs
* `<module>-gaps.md` containing Verified Security Guards (`GUARD-xxx`, PASS) and the numbered list of suspected gaps (`### 1. GAP-001`, `### 2. GAP-002`...).
* State transitioned to `RUNTIME_INVESTIGATION` for Step 2.5 processing.
