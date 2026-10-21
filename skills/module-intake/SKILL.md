---
name: module-intake
description: >-
  Receives the module testing request, detects available documentation and source code,
  identifies repository capabilities, and initializes the persistent QA workflow state.
  Use when the user starts a new testing request or specifies a target module to test.
---

# Skill: Module Intake (Step 0)

## 1. Description & Trigger Conditions
* **Purpose:** Intake the user's testing request, assess repository context, inspect existing documentation, and initialize workflow tracking in `.qa-state.json`.
* **Triggers:**
  * User requests testing for a feature or module (e.g., *"Test the Login module"*, *"Analyze and test Checkout"*, *"Tạo test case cho phân hệ Điểm danh"*).
  * Direct invocation by `workflow-orchestrator`.

## 2. Inputs
* **Required:**
  * Target module name or description.
* **Optional:**
  * Requirement documents (`.md`, `.pdf`, `.docx`, Swagger/OpenAPI specs).
  * User stories, acceptance criteria, or screenshots.
  * Explicit test focus (e.g., negative tests, security edge cases).

## 3. Prerequisites
* Current workspace or repository is accessible.
* Python 3 and basic shell tools available.

## 4. Step-by-step Execution Instructions
1. **Identify Module & Scope:**
   * Extract the exact target module name.
   * If the user's request is ambiguous, note initial assumptions without blocking.
2. **Scan & Convert Available Documentation (Microsoft MarkItDown):**
   * Check project directories (e.g., `docs/`, `specs/`, root files) or user-provided files for specifications.
   * **Mandatory Preprocessing with Microsoft MarkItDown:**
     * If the input file is a **PDF (`.pdf`), Excel (`.xlsx`, `.xls`), Word (`.docx`), or PPTX**:
       Execute MarkItDown to convert it into a clean Markdown (`.md`) file:
       `markitdown "<input_file>" -o "<output_file>.md"`
       (hoặc gọi tool MCP `convert_to_markdown` từ server `markitdown`).
     * Use the converted `.md` file as the primary text specification for Graphify ingestion and Gap Analysis.
   * Record paths and compute SHA-256 hashes of input and converted documents for traceability.
3. **Inspect Repository Environment:**
   * Determine project structure (root directory, language, package manager).
   * Check tool availability: `graphify`, `python`, `node`, `playwright`.
4. **Initialize Workflow State:**
   * Invoke `python scripts/state_manager.py init "<ModuleName>"` to create or reset `.qa-state.json`.
   * Record discovered document paths and repository metadata.

## 5. Expected Outputs
* Initialized `.qa-state.json` with status `INITIALIZED`.
* Intake summary report detailing:
  * Module name.
  * Discovered documentation.
  * Available testing tools.
  * Next action transition.

## 6. Failure Handling
* If repository root is invalid or inaccessible: halt and request the correct path.
* If documentation is missing: do NOT halt. Proceed using source code as the primary discovery source, but record that requirements are unverified.

## 7. Human Approval Requirements
* None at Step 0. Automatically proceed to `graphify-context-discovery`.

## 8. Completion Criteria
* State file `.qa-state.json` created with state `INITIALIZED`.
* Ready to transition to `graphify-context-discovery`.
