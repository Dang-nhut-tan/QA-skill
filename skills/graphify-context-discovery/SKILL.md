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
1. **Incremental Cache & Hash Verification (Token Saving Guardrail 1):**
   * Inspect `.qa-state.json` for current git commit hash (`git rev-parse HEAD`) or file content SHA-256 hashes.
   * If the target module source files have NOT changed since last run and `module-context.md` exists:
     - Reuse cached AST context directly; do NOT rerun full graph extraction.
     - *Token savings:* Bypasses AST re-reading entirely (0 token consumed for unchanged modules).
   * If changes exist: perform **Incremental Diff-Only Analysis** (`git diff --name-only <last-hash>`) and analyze only modified files and their immediate neighbors.

2. **Graphify Environment Detection:**
   * Run `graphify --version` to verify CLI availability.
   * If `graphify` is not in PATH, check `~/.local/bin/graphify` or virtual environments.
   * *If Graphify is missing or fails:* Stop immediately. Explain what analysis cannot be performed, and request user permission before falling back to manual static search. Never fake Graphify results.

3. **Build / Refresh Knowledge Graph with Strict Output Bounds:**
   * Run `graphify update <repo-path>` to construct or refresh knowledge graph in `graphify-out/`.
   * > [!CAUTION]
   * > **TOKEN BLOWOUT PREVENTION (CRITICAL):**
   * > NEVER read the raw `graphify-out/graph.json` or full `GRAPH_REPORT.md` into LLM context (these files often exceed 100,000 tokens!).
   * > Always query targeted subgraphs using CLI commands with bounded limits.

4. **Signature-First Progressive Disclosure (Token Saving Guardrail 2):**
   * **Boundary Limits:** Enforce maximum dependency depth: `max_depth = 2` and maximum neighborhood nodes: `max_nodes = 30` per symbol query.
   * **Signature-First Protocol:**
     - Step 4.1: Query TypeScript interfaces, function contracts, export signatures, and Zod/Yup schemas first.
     - Step 4.2: Read full function implementation bodies ONLY on-demand if the contract reveals suspicious edge cases, custom regex, or unhandled errors.
     - *Token impact:* Cuts 70%–80% of unnecessary source code ingestion.

5. **Investigate Module Entry Points & Symbols:**
   * Identify core entry files (Routes, Controllers, Components).
   * Run `graphify explain "<KeySymbol>"` with depth $\le 2$ to inspect immediate neighbors.
   * Identify "God Nodes" and high-centrality utilities connected to this module.

6. **Dependency-Aware Business Flow Analysis:**
   * Analyze interconnected upstream and downstream flows:
     * *Example (Authentication):* Account provisioning, activation, credential hashing, throttle/lockout (`useSubmitOnce`), session/token generation, device validation (`MayLaNotice`), logout, password reset.
   * Use `graphify path "<EntryNode>" "<ServiceNode>"` to trace call chains from UI to Data Layer.

7. **Context Classification:**
   * Classify every finding into:
     - `[CODE-CONFIRMED]`: Directly verified in source code AST.
     - `[DOC-CONFIRMED]`: Stated in project specification/document.
     - `[RUNTIME-CONFIRMED]`: Verified via observable runtime execution.
     - `[INFERRED]`: Deduce by pattern but lacking explicit assertion.
     - `[UNKNOWN]`: Missing or uncertain implementation.

8. **Generate Deliverable Within Step Token Budget:**
   * **Step 1 Token Budget:** Target $\le$ 4,000 tokens for the entire context discovery phase.
   * Create `module-context.md` at workspace root with concise, high-signal structural mapping.
   * Update workflow state: `python scripts/state_manager.py transition GAP_ANALYSIS "Completed Graphify context discovery"`.

## 5. Expected Outputs
* `module-context.md` containing:
  * Module Overview & Entry Points.
  * Dependency Call Tree (Upstream/Downstream, bounded depth $\le 2$).
  * Business Flow Reconstruction.
  * Data Models, Validations & SQL Schemas (Signature-first).
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
