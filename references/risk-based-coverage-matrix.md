# DYNAMIC RISK-BASED COVERAGE (RBC) MATRIX
## Test Suite Scaling Framework Based on Complexity Tiers & Business Risk

> **Architectural Objective:**  
> Eliminate rigid, arbitrary quotas (e.g. forcing 15 or 20 cases on every module).  
> Replace with a **Dynamic Risk-Based Coverage (RBC) Model**: Test suite volume and composition are determined dynamically by **Module Complexity Tier**, **Risk Score (Impact x Likelihood)**, and **Inherent Defect Severity**.

---

## 1. MODULE COMPLEXITY TIERS

Test suite scale is calibrated against codebase architectural complexity (number of routes, database entities, external dependencies) and business/security criticality:

| Module Complexity Tier | Structural & Business Characteristics | Recommended Test Case Volume | Inherent Severity Allocation Guideline |
| :--- | :--- | :---: | :--- |
| **Tier S — Simple** *(Cosmetic / 1-Step Form / Lookup)* | Static displays, simple password reset, basic profile edit, 1-step contact forms, read-only directory lookup. | **5 - 8 Test Cases** | • Critical: 2 - 3 cases (Happy path, crash, empty submit)<br>• Major: 2 - 4 cases (Validation, format error)<br>• Minor: 1 - 2 cases (UI, placeholder) |
| **Tier M — Standard** *(Standard Functional Module)* | Multi-channel Auth, Leave/Attendance requests, Shift scheduling, Meeting room reservation, Feedback forms. | **10 - 18 Test Cases** | • Critical: 5 - 8 cases (Core path, lockout, double click, RBAC)<br>• Major: 4 - 7 cases (Time calculation, overlap, validation)<br>• Minor: 2 - 3 cases |
| **Tier L — Complex / Core** *(Financial / Security / Data Engine)* | Payment gateways, Payroll & tax calculation, Multi-tier hierarchical approvals, Session security, Distributed database sync. | **18 - 30+ Test Cases** | • Critical: 10 - 16 cases (Financial loss, balance discrepancy, race condition, auth bypass, webhook retry)<br>• Major: 7 - 12 cases (Calculation formulas, status transitions)<br>• Minor: 2 - 4 cases |

---

## 2. RISK ASSESSMENT FORMULA

Every test scenario is evaluated using the standard quantitative risk formula:

$$\text{Risk Score} = \text{Impact (1-3)} \times \text{Likelihood (1-3)}$$

### 2.1. Impact Scale (1 to 3):
* **Level 3 (Critical Impact):** Financial loss, sensitive data leak (PII), application crash (HTTP 500), complete business process blockage, account takeover.
* **Level 2 (Moderate Impact):** Calculation discrepancies (leave days, allowances), incorrect redirection, invalid record state persistence, business constraint breach.
* **Level 1 (Minor Impact):** Cosmetic layout shift, minor typo, sub-optimal informational feedback without affecting data flow.

### 2.2. Likelihood / Probability Scale (1 to 3):
* **Level 3 (High Likelihood):** Complex asynchronous transitions, deeply nested conditionals, multi-party integrations (SMS, payment gateways, webhooks), high concurrent traffic.
* **Level 2 (Moderate Likelihood):** Multi-field forms with cross-field validation rules, multi-table JOIN queries.
* **Level 1 (Low Likelihood):** Static UI components, read-only data rendering, simple linear sequential flows.

---

## 3. STRICT SEPARATION: SEVERITY VS. RISK PRIORITY

* **Defect Severity (Column H in Workbook):**  
  Reflects the **technical and business damage if the scenario fails**:
  - `Critical` / `Blocker`: Paralyzes business workflow, crashes system, causes data loss or security breach.
  - `Major`: Produces incorrect calculations, saves invalid state, breaks validation rules.
  - `Minor`: Cosmetic, typographical, or pixel alignment flaws.
  *(Strictly prohibit using Severity as a production test quota!)*

* **Execution Priority (Risk Priority):**
  - **P0 (Critical / Blocker):** Risk Score = 6-9. Mandatory first-run in every CI/CD deployment and release gate.
  - **P1 (High):** Risk Score = 4-5. Must pass before feature release.
  - **P2 (Normal / Low):** Risk Score = 1-3. Executed during periodic regression cycles or when time permits.

---

## 4. AGENT DECISION WORKFLOW

1. **Step 1 (Tier Identification):** Analyze CodeGraph AST metrics (file count, endpoint count, database models) to classify the target module into Tier S, Tier M, or Tier L.
2. **Step 2 (Risk Enumeration):** Identify concrete threats (Security, Data Integrity, Concurrency, Throttling, Happy Path).
3. **Step 3 (Targeted Test Suite Design):**
   * If a Tier S module requires only 6 tests $\rightarrow$ generate exactly 6 high-value tests. **Padding with useless trivial tests is strictly prohibited**.
   * If a Tier L module has 24 high-risk branches $\rightarrow$ design all 24 comprehensive tests without artificial quota constraints.
