---
name: requirement-gap-analysis
description: >-
  Audits inconsistencies, missing business rules, and contradictions between code and specifications.
  Analyzes dual-dimension impact: User Experience (UX) degradation and future technical bug prediction.
  Automatically authors executable Playwright bug reproduction scripts (tests/repro/<module>-gap-<id>.spec.ts),
  provides 1-click terminal reproduction commands (npm run <module>:gap:<id>), compiles <module>-gaps.md,
  and seamlessly progresses to testcase design.
---

# Skill: Requirement Gap Analysis (Step 2)

## 1. Description & Trigger Conditions
* **Purpose:** Audit the reconstructed context against available requirements, identify ambiguities and potential defects, assess dual-dimension impact (User Experience damage and future technical bug prediction), automatically author standalone executable Playwright bug reproduction scripts (`tests/repro/<module>-gap-<id>.spec.ts`), provide 1-click terminal reproduction commands (`npm run <module>:gap:<id>` and `npx playwright test ...`), compile `<module>-gaps.md`, and seamlessly progress to testcase design.
* **Triggers:**
  * Completed `codegraph-context-discovery` in full workflow orchestrator (`GAP_ANALYSIS`).
  * **Standalone Invocation:** Direct user request to investigate gaps for a module (e.g., *"Investigate gaps for Login module"*, *"Analyze requirement gaps for Checkout"*).

## 2. Inputs
* **Required:**
  * `module-context.md` (reused if cached, or generated on-demand).
  * Project documents or specifications (if available).
  * Target module name.
  * `.qa-state.json`.
* **Optional / Recommended:**
  * `system-architecture-flows.md` (generated in Step 0, mapping global system topology and cross-system interaction flows).

## 3. Prerequisites & Standalone Execution Architecture
* **Full Workflow Mode:** Expects `module-context.md` from Step 1 (`codegraph-context-discovery`).
* **Standalone Execution Mode (Single-Skill Trigger):**
  * When invoked directly with a module name:
    1. **Cache Check:** Check if `module-context.md` or existing CodeGraph dependency cache exists for the module.
    2. **Cache Hit:** Immediately reuses the AST context—zero token waste, skips re-parsing, and immediately jumps to discrepancy detection.
    3. **Cache Miss (Cold Start):** Automatically runs Step 1 (`codegraph-context-discovery`) in the background to discover unrestricted AST dependencies first, then continues seamlessly.
    4. **Focused Output:** Produces the dedicated visual report `<module-name>-gaps.md`, provides the clickable link, and stops at Gate 1. It does NOT force subsequent test case design or automation steps unless explicitly requested by the user.

## 4. Step-by-Step Execution Instructions
1. **Discrepancy & Ambiguity Audit:**
   * Compare documented rules against code AST implementations.
   * Categorize findings into 7 distinct categories:
     1. `Requirement Ambiguity`: Unspecified behavior (e.g., lockout duration not defined).
     2. `Potential Implementation Defect`: Code exhibits suspicious logic or unhandled edge cases.
     3. `Missing Documentation`: Feature exists in code but has zero written specification.
     4. `Environment / Test Data Limitation`: Feature requires external SMS/email gateway or hardware.
     5. `Confirmed Defect`: Clear breach of explicit documented business rule.
     6. `Architectural / Cross-System Inconsistency`: Contradictions or blindspots between local module logic and global system integration flows (from `system-architecture-flows.md`).
     7. `Industry Benchmark Discrepancy & Domain Blindspot`: Inadequacies (điểm bất cập), anti-patterns, or missing business rules (điểm mù) uncovered when cross-referencing our module against leading external systems with similar modules (from `industry-benchmark-flows.md`).

1.5. **Adaptive Level 4 JIT Inspection for Underspecified Requirements:**
   * Evaluate the available specification text using `evaluate_spec_completeness(spec_text)`.
   * **If the specification is incomplete / underspecified (lacking BDD Gherkin or quantitative Acceptance Criteria):**
     - Run `discover_adaptive_core_snippets(spec_text, entry_actions)` via `scripts/codegraph_discovery.py` to selectively inspect the implementation bodies of core calculation methods or declarative rule matrices (Cyclomatic $M \ge 2$ or business rule dictionaries).
     - **Ephemeral Scoped Context Rule:** These code snippets are strictly temporary working context for Step 2 to detect hidden business logic and construct high-precision clarification questions. **DO NOT write raw implementation bodies into `module-context.md`**.
     - **Neutral Discrepancy Protocol:** At Human Gate 1, formulate questions neutrally with multiple options (Option A: standard industry practice, Option B: current code implementation, Option C: alternative policy, Option D: custom). Never anchor or lead the BA into codifying developer bugs.

1.6. **Strict Falsification & Negative Testing Rule (Anti-False-Alarm Protocol):**
   * **ANTI-FALSE-ALARM PROTOCOL:**
     When cross-referencing source code AST with live browser verification (Playwright MCP):
     - **CASE 1: VERIFIED SECURITY GUARDS / CONSTRAINTS:**
       + Example: Specification states *"Deputy manager cannot approve requests"*, and on the live UI the Approve button is properly disabled (`disabled`) with an explanatory role banner.
       + Or: Specification forbids *"Self-approving own requests"*, and on the personal request tab all Approve/Reject buttons are completely hidden.
       -> **THIS IS A SUCCESSFUL NEGATIVE TEST SCENARIO (PASS), SYSTEM IS 100% SECURE, STRICTLY NOT A BUG OR DEFECT!**
       + **STRICT PROHIBITION:** Do NOT tag as `GAP-xxx`. Do NOT assign severity as `Blocker` or `Major`. Never argue inversely: *"If the approve button were enabled, it would be a risk..."*.
       + **CLASSIFICATION RULE:** File separately under `## Verified Security Guards` with code `GUARD-xxx` and status `PASS`.
     - **CASE 2: WHEN IS AN ISSUE A GENUINE GAP (TRUE GAP)?**
       + Record as `GAP-xxx` ONLY when there is an **actual contradiction, loophole, or runtime defect**:
         * Spec prohibits but UI allows interaction (Confirmed Defect / Security Bypass).
         * Spec is missing, causing ambiguous UI states and workflow gridlock (Requirement Ambiguity).
         * UI interaction leads to unhandled crashes, 500 errors, or data loss (Implementation Bug).

1.7. **Mandatory Dual-Dimension Impact Assessment (UX Impact & Future Technical Risk):**
   * For every genuine ambiguity, discrepancy, or defect (`GAP-xxx`), the AI agent MUST conduct a rigorous dual-dimension impact analysis. Never settle for superficial or generic remarks (e.g. "may affect users"). Specifically evaluate:
     - **Dimension 1: User Experience (UX) Impact:**
       + **Operational Friction:** What does the user see, feel, or struggle with right now? Are error messages missing, misleading, or cryptic?
       + **Misleading Feedback:** Does the UI lead the user to believe an action succeeded (e.g. check-in recorded, order submitted, form saved) when it was silently dropped, queued, or rejected?
       + **Behavioral Traps:** Does the ambiguity cause accidental double submissions, incorrect data entry, confusion between tabs/roles, or abandonment of critical workflows?
       + **Trust Erosion:** How does this flaw degrade user confidence in the application's reliability?
     - **Dimension 2: Future Technical Risk & Potential Defect Prediction:**
       + **Data Inconsistency & Corruption:** Orphaned foreign keys, desynchronized records between database tables or distributed caches, partial state persistence.
       + **Concurrency & Race Conditions:** What happens when multiple users or parallel background workers execute this edge case simultaneously under peak traffic (`workers > 1`)?
       + **Cascading Downstream Failures:** How will future dependent modules (billing engines, financial ledger, month-end aggregation reports, analytics pipelines, third-party webhook integrations) crash or generate erroneous numbers due to dirty data?
       + **Compliance, Security & Audit Liabilities:** Risk of unauthorized actions, privilege escalation, lack of legally required audit trails, or performance bottlenecks as database volume scales.

1.8. **Cross-System Architectural & Industry Benchmark Synthesis (Uncovering Inadequacies, Domain Blindspots & User Friction):**
   * **Mandatory Core Directive:** The primary objective of benchmarking against external systems with similar modules is to contrast our company project's module flow against mature industry leaders, systematically surfacing **Điểm bất cập (Inadequacies)**, **Điểm gây khó chịu / ức chế cho người dùng (User Friction & Frustration Points)**, and **Điểm mù (Domain Blindspots)**:
     1. **Điểm bất cập kiến trúc & luồng (Architectural Inadequacies & Anti-Patterns):**
        - Fragile or substandard technical flows compared to mature industry implementations.
        - *Examples:* Synchronous blocking operations without timeout/circuit breaker, premature state mutation (marking 'Paid' before verified webhook), unhandled Promise rejections, lack of automated Saga compensation/rollback on downstream failures.
     2. **Điểm gây khó chịu / ức chế cho người dùng (User Friction & Operational Frustration):**
        - Flaws that inflict direct operational friction, confusion, or wasted effort on real users.
        - *Lost Effort / State Loss:* Clearing all form fields when 1 validation fails, forcing user to type from scratch.
        - *Double-Submission Pitfalls:* Keeping submit buttons clickable during transit, inducing users to click 2-3 times and triggering duplicate charges or duplicate records.
        - *UI Freezes & Infinite Spinners:* Lack of progress indicators or timeout ceilings, leaving users stranded on loading spinners indefinitely without knowing whether the transaction completed.
        - *Cryptic / Silent Feedback:* Generic banners like "Có lỗi xảy ra" or silent drops without clear actionable guidance on what to fix.
        - *Lack of Reversibility & Control:* No confirmation prompt before irreversible actions, no Undo/Edit grace window.
     3. **Điểm mù (Domain Blindspots & Missing Business Rules):**
        - Critical industry edge cases or policies standard in mature platforms that local documentation and code completely omitted.
        - *Examples:* Missing idempotency keys on double submissions, absence of temporary resource reservation TTL (e.g. cart/seat hold countdown), lack of rate limiting / exponential backoff on brute-force attempts, failure to distinguish user-actionable errors from transient infrastructure errors.
     4. **Cross-System & Distributed Liabilities:**
        - Unbounded remote timeouts, webhook retry storms, distributed state desynchronization (split-brain), and orphaned side-effects on database rollback.

2. **Formulate BA/PO Clarification Table:**
   * Create prioritized table with columns:
     * `Issue ID` (e.g., `GAP-001`)
     * `Related Flow`
     * `Current Evidence` (Code references & lines)
     * `Uncertainty`
     * `UX Impact` (Direct consequences on end-user experience and behavior)
     * `Future Technical Risk` (Downstream bugs, data corruption, concurrency failures, or scaling liabilities)
     * `Question for BA/PO`
     * `Suggested Options` (Hypotheses A, B, C)
     * `Status` (`Pending`)

3. **Trigger Playwright MCP UI Verification & Reproduction Script Generation (Step 3 Collaboration):**
   * **Mandatory UI Verification & Script Authoring:**
     - For every gap observable on the web UI:
     - Activate `playwright-investigation` (Step 3) to navigate to the live screen.
     - Execute concrete interaction steps to verify if the discrepancy occurs.
     - **Author a standalone Playwright bug reproduction script (`tests/repro/<module>-gap-<id>.spec.ts`)** with explicit assertions reproducing the failure, and provide 1-click terminal commands:
       * `npm run <module>:gap:<id>`
       * `npx playwright test tests/repro/<module>-gap-<id>.spec.ts --headed`
     - Record step-by-step reproduction instructions from the end-user perspective (1. Open... 2. Enter... 3. Click... and observe...).
     - For backend-only logic lacking UI: explicitly tag `[Verified via AST - No UI Rendering]`.

4. **Generate Standalone Deliverable (`<module-name>-gaps.md`):**
   * **Deliverable Format:** The generated deliverable `<module-name>-gaps.md` must follow `references/requirement-gaps-template.md` so that stakeholders can understand and act on it immediately.
   * Structure:
     - Investigation overview and 5-category summary table.
     - Table of Verified Security Guards (`GUARD-xxx`, PASS).
     - Prioritized table of True GAPs with dedicated `UX Impact` and `Future Technical Risk` columns.
     - **Mandatory Side-by-Side Benchmark & User Friction Audit Table:** Direct comparison between Industry Leader Flow vs Our Company Project Flow across 5 operational phases, highlighting Điểm bất cập and Điểm gây ức chế cho người dùng.
     - Detailed issue cards for each `GAP-xxx` containing:
       1. AST code evidence and specification discrepancy.
       2. **User Experience Impact (UX Impact):** User confusion, misleading feedback, workflow interruption.
       3. **Future Technical Risks & Potential Defects:** Data corruption, concurrency race conditions, broken reports.
       4. Standalone Playwright reproduction script (`tests/repro/`) and 1-click terminal command (`npm run <module>:gap:<id>`).
       5. DevTools runtime diagnostics (console errors and network API failures).
       6. Direct questions for BA/PO and concrete options (Option A, Option B).

5. **Direct Authoring of Playwright Reproduction Scripts (`tests/repro/`):**
   * For every observable UI gap identified, the agent MUST immediately invoke `write_file` to author a standalone reproduction spec:
     - Target path: `tests/repro/<module>-gap-<id>.spec.ts` (e.g. `tests/repro/order-gap-001.spec.ts`).
     - Content: Navigation, user interactions replicating the issue, and an assertion proving the bug.
   * Format the 1-click terminal commands into `<module-name>-gaps.md`:
     - Registered script: `npm run <module>:gap:<id>`
     - Direct CLI: `npx playwright test tests/repro/<module>-gap-<id>.spec.ts --headed`

6. **Persist State Checkpoint & Register Artifact:**
   * Save questions into `.qa-state.json` under `clarification_issues`.
   * Register the generated report artifact:
     `python scripts/state_manager.py set-artifact gap_analysis <module-name>-gaps.md`
   * Update workflow state to advance seamlessly:
     `python scripts/state_manager.py transition TESTCASE_GENERATION "Gaps identified with executable Playwright reproduction scripts and DevTools diagnostics. Seamlessly advancing to risk-based testcase design."`

## 5. Artifact Delivery & Review Integration
* **Deliverable Link:** Deliver the clickable markdown link to the generated report file: `[<module-name>-gaps.md](file:///path/to/<module-name>-gaps.md)`.
* **In Standalone Mode:** Deliver the report link and executive summary table directly in chat, ready for developer review.
* **In Full Workflow Mode:** To ensure continuous execution without unnecessary blocking stops, the workflow advances seamlessly into Step 4 (`testcase-design`). The single mandatory human gate is at Step 5 (`WAITING_FOR_APPROVED_TESTCASES`), where the user reviews the complete test suite and decides whether to test or request revisions.

## 6. Expected Outputs
* Dedicated Markdown report: `<module-name>-gaps.md` exported into workspace root with standalone Playwright reproduction scripts and dual-dimension impact analysis (UX + Future Risk).
* Directory `tests/repro/` containing executable Playwright test specs (`tests/repro/<module>-gap-<id>.spec.ts`).
* State file updated to `TESTCASE_GENERATION` (or `WAITING_FOR_REQUIREMENT_CLARIFICATION` if explicitly requested in standalone mode).

## 7. Failure Handling
* If zero gaps are found: double-check edge cases (boundary values, throttling, role permissions). If genuinely clean, document verification criteria in `<module-name>-gaps.md` and advance to testcase design.

## 8. Completion Criteria
* Standalone `<module-name>-gaps.md` report is created with Playwright reproduction scripts (`tests/repro/`), terminal commands (`npm run`), and dual-dimension impact analysis (UX Impact + Future Technical Risk) for every identified gap.
* Artifact is registered and workflow transitions to `TESTCASE_GENERATION`.
