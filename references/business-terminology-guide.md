# BUSINESS TERMINOLOGY STANDARDIZATION GUIDE
## Accessible, User-Centric Test Case Phrasing Standards for Non-Technical Stakeholders

> **Core Objective:**  
> Ensure that any stakeholder (Manual Tester, Business Analyst, Product Owner, or Executive) reading the test suite can **immediately understand the business objective** and **effortlessly reproduce every step on screen**, while **preserving 100% of risk coverage, boundary checks, and negative security testing**.

---

## 1. CORE PRINCIPLES

1. **User-Centric Visual Perspective:**
   * Every test case must start from the end user's action on the application interface (what to input, what button to click, what feedback appears).
   * Strictly avoid internal developer implementation phrasing (e.g., do not write *"trigger hook"*, *"intercept event"*, *"dispatch payload"*).

2. **Prohibition of Raw Developer Jargon:**
   * Prohibit awkward machine translations or cryptic internal terms.
   * Prohibit raw internal variable names or developer acronyms: `UI`, `DB`, `RPC`, `web_anon`, `DOM`, `insufficient_privilege`, `UUID`.

3. **Two-Tier Outcome Verification ("UI Presentation" & "Underlying Data State"):**
   * If a test case verifies both on-screen feedback and underlying data integrity, articulate both tiers clearly:
     - **Tier 1 (User Screen):** What message is displayed, how button states transition, modal visibility.
     - **Tier 2 (Underlying System Data - if applicable):** Whether a new persistence record is generated or rejected, explained in clean business terms.

4. **Preservation of Rigorous Risk Coverage:**
   * Never dumb down test cases to the point of omitting security boundaries, throttling limits, or race condition checks.
   * Maintain appropriate severity distributions across Critical, Major, and Minor tiers.

---

## 2. TERMINOLOGY MAPPING TABLE

| Technical Jargon / Cryptic Term | Business-Friendly Standard | Exemplary Phrasing |
| :--- | :--- | :--- |
| **Throttling / Rate limiting** | **Request limit exceeded / Rapid submission prevention** | *Verify rate limit: Prevent additional requests when an account submits more than 3 times within 24 hours* |
| **Silent drop** | **Security handling: Display generic confirmation without creating new record** | *Screen displays generic confirmation for security without creating duplicate background requests* |
| **UI returns error...** | **Screen displays notification / Alert banner appears...** | *Screen displays alert message: "Request has been recorded successfully"* |
| **No DB insert / DB row not inserted** | **System persistence layer creates no new records** | *The database records no duplicate transactions* |
| **RPC / Endpoint / API** | **Direct service endpoint / Functional URL** | *Directly access service URL without an active authenticated session* |
| **web_anon / Unauthenticated role** | **Unauthenticated guest / Anonymous visitor** | *An unauthenticated user attempts to perform restricted action* |
| **insufficient_privilege / 403 Forbidden** | **Access denied due to missing authorization** | *System denies access and displays message: "You do not have permission to perform this action"* |
| **useSubmitOnce / Double click prevention** | **Temporary button lockout during processing** | *Submit button transitions to loading state (disabled) to prevent accidental duplicate submissions* |
| **Payload / Request body** | **Form input parameters** | *Enter valid input data into the form fields* |
| **Preconditions: Un-auth** | **Preconditions: User is not logged into the system** | *User has browser open with no active login session* |
| **Password hashing / Bcrypt** | **Secure cryptographic password storage** | *Password data is stored cryptographically without exposing plaintext* |

---

## 3. CONTRASTIVE EXAMPLES: BEFORE VS. AFTER

### ❌ Example 1 (Developer Jargon):
* **Title:** `Throttling check 2: Silent drop when account exceeds 3 requests in 24h`
* **Steps:** `1. Shoot 4th request with employeeId`  
  `2. Check UI response and password_reset_request table`
* **Expected Result:** `UI returns generic success SEC-RL-03... DB does not insert row due to >3/24h limit.`

### ✅ Example 1 (Standard Business-Friendly Phrasing):
* **Title:** `Verify submission rate limiting: Prevent duplicate requests when account exceeds 3 attempts within 24 hours (security protection)`
* **Preconditions:** `User account has already submitted 3 password reset requests in the past 24 hours.`
* **Test Data:** `Account ID: USER-102 (reached 3 attempts/24h threshold)`
* **Steps (Actionable by Anyone):**  
  `1. Open the Password Reset screen.`  
  `2. Enter Account ID USER-102 into the identifier field.`  
  `3. Click the "Submit Request" button (this is the 4th attempt).`  
  `4. Observe the on-screen notification.`  
  `5. (System verification if applicable): Verify request history in admin records.`
* **Expected Result:**  
  `- On screen: Displays generic confirmation message to protect account security without revealing threshold status.`  
  `- In data records: System persistence creates no new reset requests since daily limit has been reached.`

---

## 4. STANDARDS FOR EXCEL TEST CASE COLUMNS

1. **Test Case Name:**  
   Begin with clear, action-oriented business phrasing:  
   * `Verify successful login when...`  
   * `Verify validation error display when...`  
   * `Verify rate limiting threshold when...`  
   * `Verify access restriction when...`

2. **Preconditions:**  
   Explicitly specify user role, device state, network state, and initial data prerequisites.

3. **Test Steps:**  
   Always numbered sequentially from the end-user perspective (`1. Open... 2. Enter... 3. Click... 4. Verify...`).

4. **Expected Result:**  
   State clear visual criteria (messages, modal popups, button states) followed by underlying persistence criteria where applicable.
