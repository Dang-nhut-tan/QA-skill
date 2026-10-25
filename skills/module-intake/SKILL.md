---
name: module-intake
description: >-
  Receives the module testing request, detects available documentation and source code,
  identifies repository capabilities, collects staging and admin environment credentials beforehand,
  and initializes the persistent QA workflow state.
  Use when the user starts a new testing request or specifies a target module to test.
---

# Skill: Module Intake (Step 0)

## 1. Description & Trigger Conditions
* **Purpose:** Intake the user's testing request, assess repository context, inspect existing documentation, proactively collect staging and admin environment credentials if missing, and initialize workflow tracking in `.qa-state.json`.
* **Triggers:**
  * User requests testing for a feature or module (e.g., *"Test the Login module"*, *"Analyze and test Checkout"*, *"Tạo test case cho phân hệ Điểm danh"*).
  * Direct invocation by `workflow-orchestrator`.

## 2. Inputs
* **Required:**
  * Target module name or description.
* **Optional:**
  * Requirement documents (`.md`, `.pdf`, `.docx`, Swagger/OpenAPI specs).
  * Staging URL, test user email, and Admin page credentials (username & password).
  * Explicit test focus (e.g., negative tests, security edge cases).

## 3. Prerequisites
* Current workspace or repository is accessible.
* Python 3 and basic shell tools available.

## 4. Step-by-Step Execution Instructions
1. **Identify Module & Scope:**
   * Extract the exact target module name.
   * If the user's request is ambiguous, record initial assumptions without blocking execution.
2. **Scan & Convert Available Documentation (Microsoft MarkItDown):**
   * Check project directories (e.g., `docs/`, `specs/`, root files) or user-provided files for specifications.
   * **Mandatory Preprocessing with Microsoft MarkItDown:**
     * If the input file is a **PDF (`.pdf`), Excel (`.xlsx`, `.xls`), Word (`.docx`), or PPTX**:
       Execute MarkItDown to convert it into a clean Markdown (`.md`) file:
       `markitdown "<input_file>" -o "<output_file>.md"`
       (or invoke MCP tool `convert_to_markdown` from the `markitdown` server).
     * Use the converted `.md` file as the primary text specification for CodeGraph ingestion and Gap Analysis.
   * Record paths and compute SHA-256 hashes of input and converted documents for traceability.
3. **Inspect Repository Environment & CodeGraph Preflight:**
   * Determine project structure (root directory, language, package manager).
   * Check tool availability: `codegraph`, `python`, `node`, `playwright`.
   * **Mandatory CodeGraph Preflight Check (Auto-Recovery & Health Check):**
     * Execute preflight validation script:
       `python scripts/codegraph_preflight.py "<repo_path>"`
     * Script performs 5-point verification:
       1. CodeGraph CLI availability (`codegraph --version`).
       2. Target repository validity (detects markers `package.json`, `.git`, `pyproject.toml` and write permissions).
       3. Knowledge graph initialization (detects `.codegraph/codegraph.db`; auto-runs `codegraph init` if missing in valid repos).
       4. Database schema & SQLite integrity check (PRAGMA quick_check, validates `nodes`, `edges`, `files` tables).
       5. Index freshness check (compares git commit hash / file mtime; runs `codegraph sync` if stale).
     * If preflight reports `READY`: proceed to Step 4 and persist preflight metadata in `.qa-state.json`.
     * If preflight reports `BLOCKED` (e.g. invalid repo path, missing node/codegraph environment): log actionable remediation and alert the user.
4. **Proactive Staging & Admin Credentials Collection:**
   * Inspect existing project configuration (`.env`, `.env.local`, test fixtures, mock data) for:
     1. Staging Web URL (e.g., staging domain, local dev port).
     2. Staging test user email / phone / password.
     3. Admin Portal URL, Admin Username, and Admin Password.
   * **If Credentials Are Missing / Unknown:**
     - Proactively prompt the user in polite Vietnamese during the intake summary:
       ```text
       Để phục vụ việc kiểm chứng giao diện thực tế (Playwright MCP) và kiểm tra luồng phân quyền trang quản trị:
       Xin vui lòng cung cấp (nếu có):
       1. Đường dẫn Staging (URL web kiểm thử).
       2. Email / Tài khoản người dùng test.
       3. Đường dẫn trang Quản trị (Admin) cùng Username & Mật khẩu.
       (Nếu đang chạy môi trường demo/mock cục bộ, bạn có thể chỉ định: "dùng mock data").
       ```
     - Persist provided credentials securely in `.qa-state.json` under `environment.credentials` for subsequent Playwright UI verification in Step 3.
5. **Initialize Workflow State:**
   * Invoke `python scripts/state_manager.py init "<ModuleName>"` to create or reset `.qa-state.json`.
   * Record discovered document paths, repository metadata, and environment details.

## 5. Expected Outputs
* Initialized `.qa-state.json` with status `INITIALIZED`.
* Intake summary report presented in chat:
  * **Language Rule:** Chat communications and intake summary presented to the user must be in clear, polite Vietnamese.
  * Details: Target module name, discovered documentation, available testing tools, environment/credentials status, next action transition.

## 6. Failure Handling
* If repository root is invalid or inaccessible: halt and request the correct path.
* If documentation is missing: do NOT halt. Proceed using source code as the primary discovery source, but record that requirements are unverified.
* If user credentials are not provided: fall back to local mock data/test accounts (or unauthenticated flows) and note that external staging was unverified.

## 7. Human Approval Requirements
* None at Step 0. Automatically proceed to `codegraph-context-discovery`.
