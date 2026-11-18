---
name: module-intake
description: >-
  Receives the module testing request, detects available documentation and source code,
  identifies repository capabilities, checks environment configuration safely without storing secrets,
  and initializes the persistent QA workflow state.
  Use when the user starts a new testing request or specifies a target module to test.
---

# Skill: Module Intake (Step 0)

## 1. Description & Trigger Conditions
* **Purpose:** Intake the user's testing request, assess repository context, inspect existing documentation, verify environment configuration safely without storing plaintext secrets, and initialize workflow tracking in `.qa-state.json`.
* **Triggers:**
  * User requests testing for a feature or module (e.g., *"Test the Login module"*, *"Analyze and test Checkout"*, *"Create test cases for User Settings"*).
  * Direct invocation by `workflow-orchestrator`.

## 2. Inputs
* **Required:**
  * Target module name or description.
* **Optional:**
  * Requirement documents (`.md`, `.pdf`, `.docx`, Swagger/OpenAPI specs).
  * Staging URL and test account metadata (via `.env.local` or runtime environment variables).
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
   * **On-Demand Preprocessing via Offline MarkItDown CLI & Section Chunking:**
     * If the input file is a binary format like **PDF (`.pdf`), Excel (`.xlsx`, `.xls`), Word (`.docx`), or PPTX**:
       Execute MarkItDown offline via CLI (0 token runtime, no MCP overhead):
       `markitdown "<input_file>" -o "<output_file>.md"`
     * **Graceful Fallback:** If `markitdown` CLI is missing or throws an error on the current environment, fallback to direct text/markdown reading or standard Python extraction (`python -c "import pypdf..."` / `docx2txt`) to ensure the intake flow never breaks.
     * **Section Chunking & Token Cap Rule:** If the converted document exceeds 2,000 tokens, apply section-level chunking to extract ONLY the specific module requirements relevant to the current test scope. Never inject raw monolithic multi-page documents into subsequent LLM prompts.
     * Use the extracted, scoped text specification for CodeGraph ingestion and Step 2 Gap Analysis.
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
4. **Proactive Staging & Environment Configuration Check:**
   * Inspect existing project configuration (`.env`, `.env.local`, test fixtures, mock data) for:
     1. Staging Web URL (e.g., staging domain, local dev port).
     2. Staging test user identifiers and Admin Portal URL.
   * **Security Rule (Zero Plaintext Secrets):**
     - Never persist plaintext passwords, tokens, or sensitive API keys into `.qa-state.json`.
     - Instruct the user to place test secrets in `.env.local` (already gitignored) or provide them as runtime environment variables for Playwright MCP:
       ```text
       To support live browser UI verification (Playwright MCP) and role-based access testing:
       Please configure test credentials in .env.local (or temporary environment variables):
       1. STAGING_URL=<Target Web Application URL>
       2. TEST_USER=<Test Username / Email>
       3. TEST_PASSWORD=<Test Password>
       (Security Note: The system will never store plaintext passwords in .qa-state.json).
       ```
     - Only record non-sensitive environment metadata (e.g., `environment.base_url`, `environment.auth_method`, `environment.has_admin_portal`) in `.qa-state.json`.
5. **Global System Landscape & Cross-System Flow Discovery (Run-Once Cache Protocol):**
   * **Purpose:** Prevent local module tunnel vision by mapping the global system architecture, inter-service dependencies, and cross-system interaction flows into a dedicated persistent document.
   * **Idempotent Cache Check (Run ONLY if not already present):**
     - Check if `system-architecture-flows.md` exists in the project root or workspace root.
     - **CACHE HIT:** If `system-architecture-flows.md` already exists: **SKIP execution completely** (0 token consumption, 0 execution latency). Reuse the existing global landscape.
     - **CACHE MISS:** If `system-architecture-flows.md` is missing:
       1. Inspect high-level project structure, inter-service routes, API gateway configs, and external 3rd-party dependencies (payment, auth, messaging queues, webhooks).
       2. Author a standalone deliverable `system-architecture-flows.md` in workspace root adhering to `references/system-architecture-flows-template.md`.
   * **Strict Isolation Rule:** Strictly do NOT place global system architecture into `module-context.md`. `system-architecture-flows.md` is a standalone project-wide artifact reused across all module testing cycles to expose cross-system blindspots and architectural inconsistencies.
6. **Initialize Workflow State:**
   * Invoke `python scripts/state_manager.py init "<ModuleName>"` to create or reset `.qa-state.json`.
   * Record discovered document paths, repository metadata, environment details, and `system-architecture-flows.md` path.

## 5. Expected Outputs
* Initialized `.qa-state.json` with status `INITIALIZED`.
* Standalone project-wide artifact `system-architecture-flows.md` (authored on first run, reused on subsequent runs).
* Intake summary report presented in chat:
  * **Language Rule:** Chat communications and intake summary presented to the user must be in clear, professional English.
  * Details: Target module name, discovered documentation, available testing tools, environment/credentials status, next action transition.

## 6. Failure Handling
* If repository root is invalid or inaccessible: halt and request the correct path.
* If documentation is missing: do NOT halt. Proceed using source code as the primary discovery source, but record that requirements are unverified.
* If user credentials are not provided: fall back to local mock data/test accounts (or unauthenticated flows) and note that external staging was unverified.

## 7. Human Approval Requirements
* None at Step 0. Automatically proceed to `codegraph-context-discovery`.
