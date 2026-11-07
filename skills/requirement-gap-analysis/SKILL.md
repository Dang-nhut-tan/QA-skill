---
name: requirement-gap-analysis
description: >-
  Audits inconsistencies, missing business rules, and contradictions between code and specifications.
  Analyzes dual-dimension impact: User Experience (UX) degradation and future technical bug prediction.
  Collaborates with Playwright MCP to verify observable UI issues with screenshots, compiles the visual BA
  clarification ticket (<module>-gaps.md in Vietnamese), and halts at Human Gate 1 until the user commands to proceed.
---

# Skill: Requirement Gap Analysis (Step 2)

## 1. Description & Trigger Conditions
* **Purpose:** Audit the reconstructed context against available requirements, identify ambiguities and potential defects, assess dual-dimension impact (User Experience damage and future technical bug prediction), trigger live UI verification with screenshot capture via Playwright MCP, compile a visual BA/PO clarification report (`<module>-gaps.md`), and **halt execution for mandatory human confirmation**.
* **Triggers:**
  * Completed `codegraph-context-discovery` in full workflow orchestrator (`GAP_ANALYSIS`).
  * **Standalone Invocation:** Direct user request to investigate gaps for a module (e.g., *"Điều tra bất cập phân hệ Đăng Nhập"*, *"Phân tích gap module <Module>"*).

## 2. Inputs
* **Required:**
  * `module-context.md` (reused if cached, or generated on-demand).
  * Project documents or specifications (if available).
  * Target module name.
  * `.qa-state.json`.

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
   * Categorize findings into 5 distinct categories:
     1. `Requirement Ambiguity`: Unspecified behavior (e.g., lockout duration not defined).
     2. `Potential Implementation Defect`: Code exhibits suspicious logic or unhandled edge cases.
     3. `Missing Documentation`: Feature exists in code but has zero written specification.
     4. `Environment / Test Data Limitation`: Feature requires external SMS/email gateway or hardware.
     5. `Confirmed Defect`: Clear breach of explicit documented business rule.

1.5. **Adaptive Level 4 JIT Inspection for Underspecified Requirements:**
   * Evaluate the available specification text using `evaluate_spec_completeness(spec_text)`.
   * **If the specification is incomplete / underspecified (lacking BDD Gherkin or quantitative Acceptance Criteria):**
     - Run `discover_adaptive_core_snippets(spec_text, entry_actions)` via `scripts/codegraph_discovery.py` to selectively inspect the implementation bodies of core calculation methods or declarative rule matrices (Cyclomatic $M \ge 2$ or business rule dictionaries).
     - **Ephemeral Scoped Context Rule:** These code snippets are strictly temporary working context for Step 2 to detect hidden business logic and construct high-precision clarification questions. **DO NOT write raw implementation bodies into `module-context.md`**.
     - **Neutral Discrepancy Protocol:** At Human Gate 1, formulate questions neutrally with multiple options (Option A: standard industry practice, Option B: current code implementation, Option C: alternative policy, Option D: custom). Never anchor or lead the BA into codifying developer bugs.

1.6. **Strict Falsification & Negative Testing Rule (Phân Biệt Lỗi/Bất Cập vs Hàng Rào An Toàn Đã Đạt):**
   * **CHỐNG BÁO ĐỘNG GIẢ & SUY DIỄN NGƯỢC (Anti-False-Alarm Protocol):**
     Khi đối chiếu mã nguồn (AST) và kiểm chứng giao diện thực tế (Playwright MCP):
     - **TRƯỜNG HỢP 1: HÀNG RÀO AN TOÀN ĐANG HOẠT ĐỘNG CHUẨN (Verified Security Guard / Constraint):**
       + Ví dụ: Đặc tả yêu cầu *"Phó quản lý không được duyệt đơn"*, và trên UI thực tế nút Duyệt đã bị khóa mờ (`disabled`), kèm khung cảnh báo màu vàng rõ ràng.
       + Hoặc: Đặc tả cấm *"Tự duyệt đơn của chính mình"*, và trên UI tab đơn cá nhân đã ẩn toàn bộ nút Duyệt/Từ chối.
       -> **ĐÂY LÀ KỊCH BẢN KIỂM THỬ TIÊU CỰC THÀNH CÔNG (PASS), HỆ THỐNG AN TOÀN 100%, TUYỆT ĐỐI KHÔNG PHẢI LỖ HỔNG HAY BẤT CẬP!**
       + **NGHIÊM CẤM:** Không được gắn mã `GAP-xxx`, không được đánh giá mức độ nghiêm trọng là `Chặn (Blocker)` hay `Sai (Major)`. Không được suy diễn ngược kiểu: *"Nếu bật nút duyệt lên thì sẽ có rủi ro..."*.
       + **QUY TẮC PHÂN LOẠI:** Xếp riêng vào mục `## Hàng Rào An Toàn Đã Kiểm Chứng (Verified Guards)` với mã `GUARD-xxx` và kết quả `ĐẠT (PASS)`.
     - **TRƯỜNG HỢP 2: KHI NÀO MỚI ĐƯỢC COI LÀ BẤT CẬP (TRUE GAP)?**
       + Chỉ ghi nhận là `GAP-xxx` khi có sự **mâu thuẫn, kẽ hở hoặc lỗi thực tế**:
         * Đặc tả cấm nhưng trên UI nút vẫn bấm được (Confirmed Defect / Security Bypass).
         * Đặc tả không quy định dẫn đến giao diện xử lý mơ hồ, gây nghẽn luồng người dùng (Requirement Ambiguity).
         * Thao tác trên UI dẫn đến crash, văng lỗi 500, mất dữ liệu (Implementation Bug).

1.7. **Mandatory Dual-Dimension Impact Assessment (Phân Tích Tác Động Kép: UX & Rủi Ro Kỹ Thuật Tương Lai):**
   * For every genuine ambiguity, discrepancy, or defect (`GAP-xxx`), the AI agent MUST conduct a rigorous dual-dimension impact analysis. Never settle for superficial or generic remarks (e.g. "may affect users"). Specifically evaluate:
     - **Dimension 1: User Experience (UX) Impact (Ảnh Hưởng Trải Nghiệm Người Dùng):**
       + **Operational Friction:** What does the user see, feel, or struggle with right now? Are error messages missing, misleading, or technical jargon?
       + **Misleading Feedback:** Does the UI lead the user to believe an action succeeded (e.g. check-in recorded, order submitted, form saved) when it was silently dropped, queued, or rejected?
       + **Behavioral Traps:** Does the ambiguity cause accidental double submissions, incorrect data entry, confusion between tabs/roles, or abandonment of critical workflows?
       + **Trust Erosion:** How does this flaw degrade user confidence in the application's reliability?
     - **Dimension 2: Future Technical Risk & Potential Bug Prediction (Lỗi Tiềm Tàng & Rủi Ro Kỹ Thuật Tương Lai):**
       + **Data Inconsistency & Corruption:** Orphaned foreign keys, desynchronized records between database tables or distributed caches, partial state persistence.
       + **Concurrency & Race Conditions:** What happens when multiple users or parallel background workers execute this edge case simultaneously under peak traffic (`workers > 1`)?
       + **Cascading Downstream Failures:** How will future dependent modules (payroll calculation, financial ledger, month-end aggregation reports, analytics pipelines, third-party webhook integrations) crash or generate erroneous numbers due to dirty data?
       + **Compliance, Security & Audit Liabilities:** Risk of unauthorized actions, privilege escalation, lack of legally required audit trails, or performance bottlenecks as database volume scales.

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

3. **Trigger Playwright MCP UI Verification & Screenshot Capture (Step 3 Collaboration):**
   * **Mandatory UI Verification Before BA Ticket Delivery:**
     - For every gap observable on the web UI:
     - Activate `playwright-investigation` (Step 3) to navigate to the live screen.
     - Execute concrete interaction steps to verify if the discrepancy occurs.
     - **Capture visual progression screenshots (.png)** saved into screenshots/<IssueID>-01-input.png and screenshots/<IssueID>-02-result.png for easy reproduction (stored in project root screenshots/).
     - Record step-by-step reproduction instructions from the end-user perspective (1. Mở... 2. Nhập... 3. Bấm... và quan sát...).
     - For backend-only logic lacking UI: explicitly tag `[Verified via AST - No UI Rendering]`.

4. **Generate Standalone Deliverable (`<module-name>-gaps.md`):**
   * **Deliverable Language Rule:** The generated deliverable `<module-name>-gaps.md` MUST be produced in **Vietnamese** following `references/requirement-gaps-template.md` so that local BA, PO, and business users can understand and act on it immediately.
   * Structure:
     - Investigation overview and 5-category summary table.
     - Table of Verified Security Guards (`GUARD-xxx`, PASS).
     - Prioritized table of True GAPs with dedicated `UX Impact` and `Future Technical Risk` columns.
     - Detailed issue cards for each `GAP-xxx` containing:
       1. AST code evidence and specification discrepancy.
       2. **Ảnh hưởng Trải nghiệm Người dùng (UX Impact):** Bối rối, thông báo sai lệch, tắc nghẽn thao tác.
       3. **Lỗi Tiềm tàng & Rủi ro Kỹ thuật Tương lai (Future Technical Risks):** Sai lệch dữ liệu, concurrency race conditions, vỡ logic báo cáo sau này.
       4. UI reproduction steps and **embedded Playwright MCP screenshots**.
       5. Direct questions for BA/PO and concrete options (Option A, Option B).

5. **Persist State Checkpoint & Register Artifact:**
   * Save questions into `.qa-state.json` under `clarification_issues`.
   * Register the generated report artifact:
     `python scripts/state_manager.py set-artifact gap_analysis <module-name>-gaps.md`
   * Update workflow state:
     `python scripts/state_manager.py transition WAITING_FOR_REQUIREMENT_CLARIFICATION "Gaps verified via Playwright MCP with screenshots and dual-dimension impact analysis. Awaiting user confirmation to proceed"`

## 5. Mandatory Human Checkpoint 1 (CRITICAL STOP)
> [!IMPORTANT]
> **THE AGENT MUST HALT EXECUTION COMPLETELY HERE.**
> Before pausing, the agent MUST:
> 1. Deliver the clickable markdown link to the generated report file: `[<module-name>-gaps.md](file:///path/to/<module-name>-gaps.md)`.
> 2. Present an executive summary table directly in chat showing Issue ID, Category, Flow, Screenshot Evidence, UX Impact, Future Risk, and BA Question (in polite Vietnamese).
> 3. **WAIT FOR EXPLICIT USER INSTRUCTION:**
>    - **User commands "tiếp tục" (or "proceed"):** Advance to Step 4 (`testcase-design`) if running full workflow.
>    - **User provides answers from BA/PO:** Update `module-context.md` with resolved business rules, mark issues as `Answered`.
>    - **In Standalone Mode:** User can review the gaps ticket, forward it to BA, or request next steps when ready.
>
> **STRICT PROHIBITION: DO NOT PROCEED TO STEP 4 WITHOUT USER COMMAND "TIẾP TỤC" OR BA ANSWERS.**

## 6. Expected Outputs
* Dedicated Markdown report: `<module-name>-gaps.md` (in Vietnamese) exported into workspace root with embedded screenshot links and dual-dimension impact analysis (UX + Future Risk).
* State file updated to `WAITING_FOR_REQUIREMENT_CLARIFICATION` with `artifacts.gap_analysis` registered.
* Executive table and clickable file link presented directly to the user in chat.

## 7. Failure Handling
* If zero gaps are found: double-check edge cases (boundary values, throttling, role permissions). If genuinely clean, document verification criteria in `<module-name>-gaps.md` and request confirmation to proceed.

## 8. Completion Criteria
* Standalone `<module-name>-gaps.md` report is created with visual screenshots, reproduction steps, and dual-dimension impact analysis (UX Impact + Future Technical Risk) for every identified gap.
* State is persisted as `WAITING_FOR_REQUIREMENT_CLARIFICATION`.
* Workflow is paused waiting for user input.
