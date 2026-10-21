---
name: graphify-context-discovery
description: >-
  Reverse-engineers the codebase context for a module using Graphify Knowledge Graph.
  Extracts entry points, dependency call trees, data models, validation logic, upstream prerequisites,
  and downstream side-effects into module-context.md.
  Mandatory primary tool: Graphify.
---

# Skill: Graphify Context Discovery (Step 1)

## 1. Description & Trigger Conditions
* **Purpose:** Discover and map the full structural and dependency context of the target module using **Graphify**. Build a deterministic dependency-aware knowledge graph without relying on hallucinated assumptions.
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

## 4. Step-by-step Execution Instructions
1. **Graphify Environment Detection:**
   * Run `graphify --version` to verify CLI availability.
   * If `graphify` is not in PATH, check `~/.local/bin/graphify` or virtual environments.
   * *If Graphify is missing or fails:* Stop immediately. Explain what analysis cannot be performed, and request user permission before falling back to manual static search. Never fake Graphify results.
2. **Build / Refresh Knowledge Graph:**
   * Run `graphify update <repo-path>` to construct or refresh `graph.json`, `graph.html`, and `GRAPH_REPORT.md` in `graphify-out/`.
3. **Investigate Module Entry Points & Symbols:**
   * Identify core entry files (Routes, Controllers, Components).
   * Run `graphify explain "<KeySymbol>"` to inspect immediate neighbors and degree of coupling.
   * Identify "God Nodes" and high-centrality utilities connected to this module.
4. **Dependency-Aware Business Flow Analysis:**
   * Analyze interconnected upstream and downstream flows:
     * *Example (Authentication):* Account provisioning, activation, credential hashing, throttle/lockout (`useSubmitOnce`), session/token generation, device validation (`MayLaNotice`), logout, password reset.
   * Use `graphify path "<EntryNode>" "<ServiceNode>"` to trace call chains from UI to Data Layer.
5. **Context Classification:**
   * Classify every finding into:
     - `[CODE-CONFIRMED]`: Directly verified in source code AST.
     - `[DOC-CONFIRMED]`: Stated in project specification/document.
     - `[RUNTIME-CONFIRMED]`: Verified via observable runtime execution.
     - `[INFERRED]`: Deduce by pattern but lacking explicit assertion.
     - `[UNKNOWN]`: Missing or uncertain implementation.
6. **Generate Deliverable:**
   * Create `module-context.md` at the project artifact directory or workspace root.
   * Update workflow state: `python scripts/state_manager.py transition GAP_ANALYSIS "Completed Graphify context discovery"`.

## 5. Expected Outputs
* `module-context.md` containing:
  * Module Overview & Entry Points.
  * Dependency Call Tree (Upstream/Downstream).
  * Business Flow Reconstruction.
  * Data Models, Validations & SQL Schemas.
  * Error Handling & Throttle Mechanisms.
  * Evidence References (file paths and line numbers).
* Updated `.qa-state.json` transitioning to `GAP_ANALYSIS`.

## 6. Failure Handling
* **Graphify Extraction Timeout/Error:** Report exact error log. Check for unexcluded large binaries or deep folders.
* **Missing Symbols:** If a symbol yields no edges, run `graphify query "<feature-keyword>"` to search topological clusters.

## 7. Human Approval Requirements
* None if Graphify succeeds.
* Mandatory approval required ONLY if Graphify fails and an alternative fallback is proposed.

## 8. Completion Criteria
* `module-context.md` is generated with confirmed code references.
* Workflow state is successfully set to `GAP_ANALYSIS`.
