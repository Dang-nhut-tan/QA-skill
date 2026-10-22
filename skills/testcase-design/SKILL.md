---
name: testcase-design
description: >-
  Designs a prioritized, dynamic risk-based test suite (RBC) scaled to module complexity tiers
  (Tier S: 5–8, Tier M: 10–18, Tier L: 18–30+). Employs non-IT accessible business wording in Vietnamese,
  100% bidirectional traceability, and separates defect Severity from test execution Priority.
---

# Skill: Risk-Based Test Case Design (Step 4)

## 1. Description & Trigger Conditions
* **Purpose:** Transform verified module context, gap resolutions, and UI findings into a prioritized, high-leverage test suite scaled dynamically by module risk tiers (Tier S: 5–8, Tier M: 10–18, Tier L: 18–30+). Employs user-centric Vietnamese business terminology so non-IT stakeholders can immediately understand and execute all steps.
* **Triggers:**
  * Completed `playwright-investigation` and user approved proceeding from Gate 1 (`"tiếp tục"` or BA answers).
  * State is `TESTCASE_GENERATION`.

## 2. Inputs
* **Required:**
  * Updated `module-context.md` (containing confirmed rules and resolved gaps).
  * `.qa-state.json`.
* **References:**
  * `references/severity-guidelines.md`
  * `references/risk-based-coverage-matrix.md`
  * `references/testcase-quality-checklist.md`
  * `references/business-terminology-guide.md`

## 3. Prerequisites
* Module context and business flows are mapped without unresolved critical contradictions.
* User has explicitly confirmed proceeding from Checkpoint 1.

## 4. Step-by-Step Execution Instructions

### 4.1. Dynamic Risk-Based Coverage Allocation (RBC)
* > [!IMPORTANT]
* > **DO NOT USE RIGID QUOTAS:** Strictly avoid hardcoded test counts (e.g., forcing 15 or 20 cases on every module).
* > Determine test suite scale and composition based on **Module Complexity Tier** and **Risk Score (Risk = Impact x Probability)** following `references/risk-based-coverage-matrix.md`:
* **Identify Module Complexity Tier:**
  * **Tier S (Simple — 5 to 8 test cases):** 1-step forms, simple password changes, read-only directory lookup, basic profile edits. *Strictly prohibit padding with useless tests.*
  * **Tier M (Standard — 10 to 18 test cases):** Multi-channel Auth, Leave/Attendance requests, Shift scheduling, Meeting room booking, Form throttling and anti-spam.
  * **Tier L (Complex / Core — 18 to 30+ test cases):** Payment gateways, Payroll and tax engines, Multi-tier approvals, Session security, Concurrency, and distributed sync.
* **Strict Role of Defect Severity (Column H):**
  * `Severity` reflects the **inherent damage of a bug if it occurs** (`Chặn` = Blocking/Crash/Data Loss; `Sai` = Calculation/State Error/Validation Breach; `Nhỏ` = Cosmetic/Typo), **NOT a production quota**.
* **Risk Priority (Execution Order):**
  * **P0 (Critical / Blocker):** Happy path core flows, security boundaries, financial accuracy, crash prevention.
  * **P1 (High):** Major boundary conditions, complex validation rules, state transitions.
  * **P2 (Normal / Low):** Minor cosmetic edge cases, rare alternate paths.

### 4.2. Non-IT Business Phrasing Standard (MANDATORY)
> [!IMPORTANT]
> **COMPLIANCE REQUIRED: `references/business-terminology-guide.md`**  
> Test cases must be drafted in natural, professional **Vietnamese** so that non-IT stakeholders (Manual Testers, BAs, Product Owners, Business Users) immediately understand the purpose and can follow each step on screen without technical friction.
* **Strict Prohibition of Raw Dev Jargon & Literal Translations:**
  * Prohibit: *"Phanh chống ngập"*, *"Chặn âm thầm"*, *"web_anon"*, *"RPC"*, *"UI trả về"*, *"DB không chèn dòng"*, *"insufficient_privilege"*, *"bắn payload"*.
  * Standard Vietnamese business replacements:
    - *"Rate limiting"* $\rightarrow$ *"Giới hạn số lần gửi yêu cầu / Chặn gửi liên tục"*
    - *"Silent drop"* $\rightarrow$ *"Hiển thị thông báo thành công chung để bảo mật, không tạo yêu cầu mới"*
    - *"UI returns error"* $\rightarrow$ *"Màn hình hiển thị thông báo: ..."*
    - *"DB row not inserted"* $\rightarrow$ *"Hệ thống dữ liệu không tạo mới bản ghi"*
    - *"web_anon RPC call"* $\rightarrow$ *"Người dùng chưa đăng nhập thực hiện thao tác"*
    - *"insufficient_privilege"* $\rightarrow$ *"Hệ thống từ chối và báo lỗi không có quyền truy cập"*
* **Actionable On-Screen Test Steps (Numbered):**
  * Write user-centric sequential steps: `1. Mở màn hình...`, `2. Nhập vào ô [Tên ô] giá trị...`, `3. Bấm nút [Tên nút]...`, `4. Quan sát...`.
* **Two-Tier Expected Results:**
  * *Tier 1 (UI Presentation):* What the user sees on screen (messages, button disabled state, modal).
  * *Tier 2 (Underlying Data State - if applicable):* Record status in management system.

### 4.3. Populate Required 13 Columns for Each Test Case:
* **Test Case ID:** Unique key (`TC-<MODULE>-001`).
* **Module:** Target module name in Vietnamese (e.g., `Đăng Nhập`, `Quản Lý Ca`).
* **Test Case Name:** Clear, actionable description in Vietnamese.
* **Preconditions:** Explicit starting state, auth status, test account.
* **Test Data:** Exact inputs or boundary values.
* **Test Steps:** Numbered reproduction steps (`1. ...\n2. ...`).
* **Expected Result:** Clear, verifiable outcome in Vietnamese.
* **Severity:** Standardized Vietnamese label: `Chặn`, `Sai`, or `Nhỏ`.
* **Automation Ready:** `Yes` or `No` (Mark `Yes` only if repeatable and objectively assertable).
* **Automation Blocker:** Reason if `Automation Ready = No`.
* **Requirement Reference:** Code symbol or spec ID (e.g., `SPEC-AU-01`, `useSubmitOnce`).
* **Notes:** Context notes or device assumptions.
* **Status:** Initial execution status (`Pass`, `Fail`, `Pending`, `Skip`). Default is always `Pending`.

### 4.4. Bidirectional Requirement Traceability & Deduplication
* **Forward Traceability:** 100% of critical requirements in `module-context.md` must have $\ge 1$ test case (`orphan_requirements_count == 0`).
* **Backward Grounding:** 100% of test cases must cite verified spec tags or AST code symbols in `Requirement Reference` (`orphan_testcases_count == 0`). Zero fabricated/hallucinated tests.
* **Deduplication:** Zero duplicate test cases with identical objectives and actions (`duplicate_groups_count == 0`).

### 4.5. Transition Workflow State
* Invoke: `python scripts/state_manager.py transition TESTCASE_REVIEW "Generated dynamic risk-based test cases with 100% Traceability and Non-IT Friendly Wording"`.

## 5. Expected Outputs
* Structured dataset conforming to the 13-column schema tailored to the Module Tier (Tier S: 5–8, Tier M: 10–18, Tier L: 18–30+).
* Coverage summary metadata.
* Updated `.qa-state.json` transitioning to `TESTCASE_REVIEW`.

## 6. Failure Handling
* If test cases cannot be generated due to severe requirement uncertainty: return to Step 2 and formulate targeted gap questions.

## 7. Completion Criteria
* Full test case suite designed adhering to the 13-column schema, Risk-Based Coverage, and non-IT Vietnamese terminology.
* State transitioned to `TESTCASE_REVIEW`.
