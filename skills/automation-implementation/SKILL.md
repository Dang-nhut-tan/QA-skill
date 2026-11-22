---
name: automation-implementation
description: >-
  Inspects the existing project testing framework, reuses established Page Objects and fixtures,
  and writes clean, robust automation test scripts strictly mapped to approved Excel Test Case IDs.
  Non-destructive, zero arbitrary sleeps, collision-resistant data, real DB mutations, multi-viewport, safe promises.
---

# Skill: Automation Implementation (Phases 6.2 & 6.3)

## 1. Description & Trigger Conditions
* **Purpose:** Inspect the host project's existing testing infrastructure (runner, Page Object Models, fixtures, configs) and write production-grade automation scripts for approved test cases without introducing unwanted boilerplate or incompatible frameworks.
* **Triggers:**
  * Completed `automation-readiness`.
  * State is `AUTOMATION_IMPLEMENTATION`.

## 2. Inputs
* **Required:**
  * List of approved automation-ready test cases from Phase 6.1.
  * Project source code and existing `tests/` directory.
  * `.qa-state.json`.

## 3. Prerequisites
* Project repository contains or supports a test framework (e.g., Playwright, Cypress, PyTest, Jest).

## 4. Step-by-step Execution Instructions

### Phase 6.2 — Inspect Existing Framework & Reusable Components:
1. **Analyze Framework Conventions:**
   * Scan project root for config files: `playwright.config.*`, `cypress.config.*`, `pytest.ini`, etc.
   * Determine test runner, language (TypeScript, JavaScript, Python), and directory conventions (`tests/specs/`, `e2e/`, etc.).
2. **Discover Reusable Assets & Prioritize Existing Methods:**
   * Query CodeGraph and fallback Page Object directories for reusable methods:
     `python scripts/codegraph_discovery.py "<action_name>" --repo "<repo_path>"`
   * **Mandatory Reuse Policy (Prevent Duplicate Code):**
     - **DIRECT_REUSE:** Call existing methods directly (e.g., `await loginPage.clickLogin()`). Do NOT write duplicate locators or inline actions.
     - **CONDITIONAL_REUSE:** Adapt call parameters or wrap the method (e.g., passing optional options). Do NOT re-implement from scratch.
     - **NOT_FOUND / NOT_REUSABLE:** Only implement a new POM method or step when confirmed missing from both CodeGraph and Page Object directories.
   * *Rule:* Never introduce a new testing framework if the project already has one, unless the user explicitly approves.
   * *Rule:* Do not force complex POM structures if the repository follows a simpler functional test pattern. Respect the surrounding style.

### Phase 6.3 — Implement Test Automation:

#### 1. [CRITICAL_FORBIDDEN - ZERO TOLERANCE]
Any AI agent implementing test automation MUST strictly adhere to the following 5 engineering constraints:
1. **C1 (Anti-Over-Mocking Guard):** STRICTLY PROHIBIT 100% network mocking (`page.route`) across the entire test suite. MUST include at least 1-2 real backend mutation tests (real DB / API mutation) to verify that frontend, backend services, and persistence layers interact correctly.
2. **C2 (Collision-Resistant Dynamic Isolation):** STRICTLY PROHIBIT hardcoding static entity/user identifiers (e.g., `'TEST_USER_STATIC'`, `'USER_01'`). MUST generate dynamic, collision-resistant identifiers for parallel execution:
   `const uniqueUserId = 'user_auto_' + Date.now() + '_' + (process.env.TEST_WORKER_INDEX || '0');`
3. **C3 (Multi-Viewport Matrix):** STRICTLY PROHIBIT testing exclusively on a single viewport (e.g., mobile-only). For administration panels, dashboards, and responsive web apps, MUST verify both Desktop (1920x1080) and Mobile responsive viewports.
4. **C4 (Process & State Concurrency):** Prevent race conditions and deadlocks when managing multi-process file locks. Utilize `StateFileLock` with automatic stale lock recovery (process liveness check + TTL timeout).
5. **C5 (Zero Floating Promises):** STRICTLY PROHIBIT un-awaited asynchronous assertions (web-first assertions such as `toBeVisible`, `toHaveText`, `toHaveURL`). Every async expectation must be preceded by `await` to prevent silent false positives.
6. **C6 (Production Safety Gate & Allowlist Verification):**
   - Verify target environment tier before executing any real state mutation (`POST`, `PUT`, `DELETE`).
   - Automatically execute ONLY on allowlisted environments (`localhost`, `127.0.0.1`, `*.test`, `dev.*`, `staging.*`). If the target is **Production** or unverified, HALT and require explicit human confirmation.
   - All mutation test data MUST carry the prefix `[QA-TEST]` or `qa_<timestamp>_<uuid>` for traceability and safe purging.
   - Mandatory teardown hook (`afterAll`) to delete or clean up created entities.
   - Prohibit unmasked token/credential logging; mask all authorization headers.
   - Concurrency bursts capped at a maximum of **5 concurrent requests**.

#### 2. Contrastive Code Patterns (DO vs. DON'T)

```javascript
// ============================================================================
// C1: Anti-Over-Mocking Guard (Real Mutation vs Network Mocking)
// ============================================================================
// ❌ WRONG (100% Mocking hides real DB and backend regressions):
await page.route('**/api/orders/**', route => route.fulfill({ status: 200, json: { id: 101, status: 'created' } }));

// ✅ CORRECT (Verify actual persistence and backend response for critical mutations):
const response = await request.post('/api/orders', { data: dynamicOrderPayload });
await expect(response.status()).toBe(201);

// ============================================================================
// C2: Dynamic Data Isolation (Prevents race conditions in parallel CI runs)
// ============================================================================
// ❌ WRONG (Static identifier causes collision when run in parallel workers):
const testUsername = 'testuser_qa_static';

// ✅ CORRECT (Unique, collision-resistant identifier per worker and timestamp):
const testUsername = `user_${Date.now()}_${process.env.TEST_WORKER_INDEX || '0'}`;

// ============================================================================
// C3: Selector Syntax Validity
// ============================================================================
// ❌ WRONG (Missing brackets causes selector parse failure or silent swallow):
await page.waitForSelector('role="progressbar"');

// ✅ CORRECT (Valid attribute selector syntax):
await page.waitForSelector('[role="progressbar"]', { state: 'hidden', timeout: 5000 });

// ============================================================================
// C5: Zero Floating Promises (Web-First Assertions)
// ============================================================================
// ❌ WRONG (Missing await -> Promise is dropped -> Silent false positive):
expect(page.locator('.alert-success')).toBeVisible();

// ✅ CORRECT (Awaited web-first assertion):
await expect(page.locator('.alert-success')).toBeVisible();
```

#### 3. Review, Self-Correction & Mandatory AI Coding Quality Gate:

1. **Syntax Check:**
   * Run syntax check: `node --check <file>` or language compiler.

2. **Automated AI Coding Quality Gate (`scripts/quality_gate.py`):**
   * The AI agent MUST execute the Quality Gate before completing the task:
     ```powershell
     python scripts/quality_gate.py <modified_files>
     ```
   * **Mandatory Lint Rules Matrix (17 Rules across 5 Groups):**
     | Rule ID | Rule Name | Severity | Scope | Violation Trigger & Remediation |
     | :--- | :--- | :---: | :--- | :--- |
     | **PW-001** | `ZERO_SLEEP_VIOLATION` | **BLOCK** | Test specs (`.js`, `.ts`, `.py`) | Prohibits `waitForTimeout()`, `time.sleep()`. Use web-first assertions (`await expect(locator).toBeVisible()`). |
     | **PW-002** | `FLOATING_PROMISE_VIOLATION` | **BLOCK** | Playwright specs (`.js`, `.ts`) | Prohibits un-awaited async web assertions and un-awaited Playwright page actions (`click`, `goto`, `fill`). Prefix with `await`. |
     | **PW-003** | `TRACEABILITY_VIOLATION` | **BLOCK** | Test specs | Every test title must contain an approved traceable ID: `TC-xxx`, `GAP-xxx`, or `GUARD-xxx`. |
     | **PW-004** | `FOCUSED_TEST_VIOLATION` | **BLOCK** | Playwright specs | Prohibits `test.only()`, `it.only()`, and ungrounded `test.skip()` without reason/ticket. Remove focus before handover. |
     | **PW-005** | `LOCATOR_QUALITY_WARNING` | **WARNING** | Playwright specs | Advises against absolute XPath (`//html/...`), deep DOM chains, or ungrounded `.nth()`. Use user-facing semantic locators (`getByRole`, `getByText`, `data-testid`). |
     | **SEC-001** | `HARDCODED_SECRET_VIOLATION` | **BLOCK** | All code (`.js`, `.ts`, `.py`) | Prohibits hardcoding passwords, API tokens, secret keys. Read from environment variables (`process.env.TEST_PASSWORD`). |
     | **SEC-002** | `UNMASKED_CREDENTIAL_LOG_VIOLATION` | **BLOCK** | All code | Prohibits printing or logging unmasked credentials/tokens to console or logger. Mask with `***REDACTED***`. |
     | **PY-001** | `SILENT_EXCEPTION_VIOLATION` | **BLOCK** | Python code (`.py`) | AST-level: Prohibits bare `except:` or swallowed exceptions (`except Exception: pass`). Catch specific errors and log or re-raise. |
     | **PY-002** | `MUTABLE_DEFAULT_ARG_VIOLATION` | **BLOCK** | Python code (`.py`) | AST-level: Prohibits mutable default parameters (`items=[]`, `data={}`). Default to `None` and initialize inside function. |
     | **PY-003** | `UNSAFE_EVAL_VIOLATION` | **BLOCK** | Python code (`.py`) | AST-level: Prohibits `eval()` and `exec()`. Use `ast.literal_eval()` or dictionary dispatch tables. |
     | **ARCH-001** | `IMPORT_BOUNDARY_VIOLATION` | **BLOCK** | All code | Prohibits production scripts (`scripts/`) from importing test code or test fixtures (`tests/`). |
     | **ARCH-002** | `FRAMEWORK_UTILITY_REUSE_WARNING` | **WARNING** | All code | Flags re-implementing manual sleep polling loops or file locking routines. Reuse `expect.poll` or `WorkflowStateManager`. |
     | **QA-001** | `NO_FALSE_PASS_VIOLATION` | **BLOCK** | State files & reports | Prohibits reporting COMPLETED when test execution failed or execution artifacts are missing. |
     | **QA-002** | `UNVERIFIED_BUG_VIOLATION` | **BLOCK** | State files & reports | Prohibits marking gaps CONFIRMED without reproducible script in `tests/repro/` and execution proof. |
     | **QA-003** | `UNVERIFIED_GUARD_VIOLATION` | **BLOCK** | State files & reports | Prohibits saving GUARD without verified negative execution proof in `tests/guards/`. |
     | **QA-004** | `APPROVAL_GATE_VIOLATION` | **BLOCK** | State files & runtime | Prohibits executing automation implementation without human approval token at Step 5. |
     | **QA-005** | `PRODUCTION_SAFETY_VIOLATION` | **BLOCK** | State files & runtime | Prohibits executing automated mutations against production environments. |

3. **AI Auto-Fix Feedback Loop Protocol:**
   - **Vòng lặp:** `Tạo code -> Chạy Quality Gate -> Đọc lỗi -> Sửa đúng nguyên nhân -> Chạy lại Quality Gate -> Chạy test`.
   - **Quy tắc trần:** Tối đa 2 lần tự sửa cho cùng một nhóm lỗi. Nếu không sửa được, báo cáo lỗi còn tồn tại kèm bằng chứng và dừng lại.
   - **Hành vi nghiêm cấm:** CẤM thêm suppression comment (`/* eslint-disable */`, `# noqa`, `// @ts-ignore`), CẤM xóa hoặc làm yếu assertion, CẤM sửa linter rule để ép test xanh, CẤM sửa logic ngoài phạm vi nhiệm vụ.

4. **Technical Self-Audit Verification Card:**
   * At the conclusion of the code generation output, the AI agent MUST output the following audit card:
     ```markdown
     ### Technical Self-Audit Verification Card
     | # | Engineering Standard (C1-C5) | Status | Code Evidence / Verification Proof |
     |:--|:---|:---:|:---|
     | 1 | C1: Real Backend Mutation Test | PASS | Test ID: TC-XXX executes real mutation without route mocking |
     | 2 | C2: Dynamic Data Isolation | PASS | Line XX: Isolated via Date.now() / worker index |
     | 3 | C3: Multi-Viewport Matrix | PASS | Tested across Desktop (1920x1080) and Mobile viewports |
     | 4 | C4: State Concurrency Safe | PASS | StateFileLock with PID check & TTL recovery applied |
     | 5 | C5: 100% Awaited Assertions | PASS | Linter verified 0 floating promises |
     | 6 | Quality Gate (17 Rules) | PASS | python scripts/quality_gate.py: 0 BLOCK violations |
     ```

5. **Mandatory Pre-Delivery Smoke Execution Gate (Chạy thực tế trước khi bàn giao):**
   * The AI agent MUST execute a live dry-run of the authored test spec:
     `npx playwright test <spec_file> --project=chromium-desktop`
   * Confirm 0 syntax errors, 0 locator timeouts, and 0 harness crashes.
   * If any step fails due to locator changes or timing, auto-repair the script immediately and re-run.
   * STRICTLY PROHIBITED from handing over untested or broken test files to the user.

6. **Transition Workflow State:**
   * Update workflow state:
     `python scripts/state_manager.py transition AUTOMATION_EXECUTION "Automation scripts generated and verified via Quality Gate"`.

## 5. Expected Outputs
* Automated test spec files adhering to the project's native style and Senior Dev standards.
* Traceability mapping between spec functions and Excel Test Case IDs.
* Verified Technical Self-Audit Verification Card confirming C1-C5 and Quality Gate compliance.
* Updated `.qa-state.json` transitioning to `AUTOMATION_EXECUTION`.

## 6. Failure Handling
* If target framework is completely missing: propose the simplest native setup (e.g. Playwright) and seek user approval before creating root configuration files.

## 7. Human Approval Requirements
* Required only if proposing a new test framework not currently in the repo.

## 8. Completion Criteria
* All approved test cases are coded into executable test files.
* `python scripts/quality_gate.py` passes with 0 BLOCK violations.
* Technical Self-Audit Verification Card is provided in the final output.
* State is `AUTOMATION_EXECUTION`.
