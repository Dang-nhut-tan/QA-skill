---
name: graphify-context-discovery
description: >-
  Reverse-engineers the codebase context for a module using Graphify Knowledge Graph.
  Extracts entry points, unrestricted dependency call trees, data models, validation logic,
  upstream prerequisites, and downstream side-effects into module-context.md.
  Mandatory primary tool: Graphify.
---

# Skill: Graphify Context Discovery (Step 1)

## 1. Description & Trigger Conditions
* **Purpose:** Discover and map the complete, unrestricted structural and dependency context of the target module using **Graphify**. Build a deterministic dependency-aware knowledge graph without relying on hallucinated assumptions or artificial depth cutoffs.
* **Core Philosophy:** **Optimize Context Consumption, NOT Discovery Coverage.**
  * Graph Discovery is exhaustive and unrestricted.
  * LLM Context Loading is selective, on-demand, and progressive.
* **Triggers:**
  * Completed `module-intake`.
  * Invoked by `workflow-orchestrator` when entering `CONTEXT_DISCOVERY`.

## 2. Inputs
* **Required:**
  * Target module name and repository path.
  * Initialized `.qa-state.json`.
* **Optional:**
  * Specific entry file paths or suspected symbols.

## 3. Prerequisites
* **Graphify CLI** (`graphify`) or **Graphify MCP** (`graphify-mcp`) installed and operational.
* Target repository source code available locally.

## 4. Architectural Principles: Discovery vs. Context Loading

### 4.1. Unrestricted Dependency Discovery (No Artificial Caps)
* **NO Node Limits:** Strictly PROHIBIT artificial caps on the number of nodes Graphify is permitted to explore.
* **NO Depth Limits:** Strictly PROHIBIT artificial dependency depth cutoffs (e.g., depth = 2, 3, or 5). Traverse the complete chain of direct, indirect, and cross-module dependencies relevant to the module under test.
* **NO Budget-Based Truncation:** Strictly PROHIBIT cutting short or pruning the dependency graph merely because a token budget was reached.
* **NO Arbitrary Stopping:** Strictly PROHIBIT halting exploration upon finding an arbitrary threshold of functions, classes, or modules.
* **NO Top-K Pruning:** Strictly PROHIBIT Top-K filtering that discards business-logic or testing-risk dependencies.
* **Technical Safety Guards Only:** Maintain robust safeguards against real technical obstacles:
  * Maintain `visited_set` tracking and cycle detection to prevent infinite loops in cyclic dependencies.
  * Exclude binary, vendor, and build artifact folders (`node_modules/`, `dist/`, `.git/`, test fixtures).
  * Enforce process timeout guards to safely terminate hanging commands on corrupted syntax or file locks.
* **Persistence:** Save the exhaustive knowledge graph locally to disk (`graphify-out/`) for reuse across the entire QA lifecycle.

### 4.2. High-Efficiency LLM Context Loading (On-Demand Progressive Disclosure)
* **Never Dump Full Graph:** Strictly PROHIBIT ingesting raw `graphify-out/graph.json` or massive hundred-thousand-token monolithic graph reports into prompt context.
* **On-Demand Subgraph Queries:** Retrieve only the specific subgraphs or call chains required for the current reasoning step via targeted Graphify CLI queries.
* **Signature-First Protocol:**
  * Query TypeScript interfaces, function contracts, export signatures, and Zod/Yup validation schemas first.
  * Read full implementation bodies ONLY on-demand when inspecting complex branching, custom regex, or exception handling.
* **Incremental Cache:** Validate git commit hashes (`git rev-parse HEAD`) or file content SHA-256 hashes. If source code is unchanged, reuse cached AST context; if modified, re-analyze only changed files and their dependent subgraphs.

## 5. Step-by-Step Execution Instructions

1. **Incremental Cache & Hash Verification:**
   * Inspect `.qa-state.json` against the current git commit hash.
   * If module source files have NOT changed and `module-context.md` exists:
     - Reuse cached AST context directly without re-running extraction (0 token consumption).
   * If changes exist: Analyze modified files and their extended dependency network.

2. **Graphify Environment Detection:**
   * Run `graphify --version` to verify tool availability.
   * *If Graphify is missing or fails:* Stop immediately. Explain the technical limitation and obtain user permission before attempting static search fallbacks. Never fabricate Graphify outputs.

3. **Build / Refresh Exhaustive Knowledge Graph:**
   * Run `graphify update <repo-path>` to build or refresh the complete knowledge graph in `graphify-out/`.
   * Persist all graph analysis locally.

4. **Trace Full Dependency Chains & Cross-Module Flows:**
   * Start from main entry points (Routes, Pages, Controllers, Event Handlers).
   * Traverse complete call flows: UI $\rightarrow$ Custom Hooks $\rightarrow$ Domain Services $\rightarrow$ API Clients/RPC $\rightarrow$ Data Models / Database Tables.
   * Map cross-module dependencies (e.g., Authentication invoking User Management, Notifications, Rate Limiters, Audit Logs).
   * Use `graphify path "<EntryNode>" "<TargetNode>"` to trace call chains end-to-end without depth bounds.

5. **Signature-First Extraction & Targeted Ingestion:**
   * Ingest data contracts, types, and schema validations for all involved symbols.
   * Selectively inspect implementation bodies for high-risk zones (concurrency, account lockout, session token creation, error handling).

6. **Context Classification:**
   * Explicitly tag every piece of evidence:
     - `[CODE-CONFIRMED]`: Verified directly in source code AST.
     - `[DOC-CONFIRMED]`: Specified in written documentation.
     - `[RUNTIME-CONFIRMED]`: Verified through live runtime execution (Playwright MCP).
     - `[INFERRED]`: Deduced by pattern but lacking direct assertion.
     - `[UNKNOWN]`: Missing, contradictory, or unverified implementation.

7. **Generate Deliverable & State Transition:**
   * Export `module-context.md` at workspace root detailing entry points, dependency trees, validation rules, and identified risks.
   * **State Transition:**
     - If discovery completes without blockers: Transition state to `GAP_ANALYSIS` via `python scripts/state_manager.py transition GAP_ANALYSIS "Completed full Graphify context discovery"`.
     - If discovery cannot complete due to real technical obstacles (parser crash, timeout, resource exhaustion): Transition state to `DISCOVERY_INCOMPLETE` with detailed notes on untraversed files and technical causes. Never falsely report completion.

## 6. Expected Outputs
* `module-context.md` containing:
  * Module Overview & Entry Points.
  * Comprehensive Dependency Call Tree (Upstream / Downstream & Cross-Module, unrestricted depth).
  * Business Flow Reconstruction & State Transitions.
  * Data Models, Validations & Database Schemas.
  * Security, Concurrency, Error Handling & Throttling Mechanisms.
  * Evidence References (File paths, symbol names, exact line numbers).
* Updated `.qa-state.json` (`GAP_ANALYSIS` or `DISCOVERY_INCOMPLETE`).

## 7. Failure Handling & Incomplete Discovery Protocol
* **Parser / Syntax Errors:** Log exact file and syntax error; mark `DISCOVERY_INCOMPLETE` for that branch and continue exploring independent branches.
* **Process Timeout:** Safely kill hanging processes, log timeout error, and mark `DISCOVERY_INCOMPLETE`.
* **Missing Symbols:** Execute `graphify query "<feature-keyword>"` to search topological clusters.
* **Zero False Completion:** Never claim discovery is complete if files were skipped due to token budgets. All incomplete traversals must be marked `DISCOVERY_INCOMPLETE`.

## 8. Human Approval Requirements
* None if Graphify discovery succeeds.
* Mandatory user confirmation required if `DISCOVERY_INCOMPLETE` is flagged or before switching to a static search fallback.

## 9. Completion Criteria
* `module-context.md` is generated with confirmed code references.
* All relevant dependencies are fully mapped, or any unreached branches are explicitly logged under `DISCOVERY_INCOMPLETE`.
