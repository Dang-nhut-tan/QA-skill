# Defect Severity Classification Guidelines

In the QA Agent System, defect severity represents the **inherent business impact and user experience damage if a test case fails**.

Severity **does not reflect** whether a bug currently exists in production; rather, it reflects the **gravitational weight of the risk**.

---

## 1. Critical / Blocker
* **Definition:** A defect that causes the application or system to **completely fail, crash, or block essential business workflows** with no available workaround.
* **Key Characteristics:**
  * Application crashes, White Screen of Death (WSOD), unrecoverable HTTP 500 errors.
  * Complete blockage of prerequisite paths: Login failure, inability to process checkout/payments, unjustified account lockout, frozen transaction pipelines.
  * Critical security breaches: Leaked personally identifiable information (PII) over public channels, broken privilege boundaries, authentication bypasses.
* **Testing Priority:** Top priority (P0). Must be executed first in Smoke and Sanity suites.

---

## 2. Major
* **Definition:** The business workflow can proceed or complete, but **produces incorrect business results, inaccurate calculations, corrupted data, or invalid state transitions**.
* **Key Characteristics:**
  * Calculation errors: Payroll formula discrepancies, VAT tax errors, loyalty point mismatches, cart subtotal errors.
  * Database state corruption: Updating employee status displays wrong flags, erroneous activation emails sent.
  * Incorrect routing or branching: Successful login redirects to wrong destination ignoring `redirectUrl`.
  * Workaround exists but introduces significant user friction or risk of downstream data errors.
* **Testing Priority:** High priority (P1). Thoroughly tested in Functional and Integration test suites.

---

## 3. Minor
* **Definition:** A defect in UI formatting, presentation, cosmetic layout, or informational feedback that **does not disrupt core business flows and does not corrupt business data**.
* **Key Characteristics:**
  * Typos, imprecise i18n translations, or awkward copy where the user still understands intent.
  * Minor pixel alignment offsets, button color deviations from the Design System, slightly misaligned icons.
  * Missing supplemental tooltips or helper placeholders.
  * Slight animation stutter that does not cause application freeze or interaction lockout.
* **Testing Priority:** Normal / Low priority (P2). Executed after core functional flows are verified.
