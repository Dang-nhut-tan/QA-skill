#!/usr/bin/env python3
"""
scripts/codegraph_discovery.py
Intelligent method discovery, framework reuse validator, and progressive context
retrieval engine for the QA Agent System using CodeGraph.

Supports:
- Multi-declaration patterns (classes, functions, arrow functions, nested object methods).
- Method reuse classification: DIRECT_REUSE, CONDITIONAL_REUSE, NOT_REUSABLE, NOT_FOUND.
- 5-Level progressive context retrieval.
- Fallback search across Page Objects, exported object literals, and helpers.
- Prevention of duplicate automation methods.
"""

import sys
import os
import re
import json
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

SYSTEM_ROOT = Path(__file__).resolve().parent.parent

def find_block_end(content: str, start_pos: int) -> int:
    """
    Finds the line number where the code block starting at start_pos closes its matching curly brace.
    Handles nested braces, single-line/multi-line comments, and string literals.
    Falls back gracefully if braces are unbalanced.
    """
    brace_open_idx = content.find('{', start_pos)
    if brace_open_idx == -1:
        return content[:start_pos].count('\n') + 30
    
    depth = 0
    in_string = False
    string_char = None
    in_comment = False
    in_block_comment = False
    i = brace_open_idx
    length = len(content)
    
    while i < length:
        ch = content[i]
        if in_block_comment:
            if ch == '*' and i + 1 < length and content[i + 1] == '/':
                in_block_comment = False
                i += 1
        elif in_comment:
            if ch == '\n':
                in_comment = False
        elif in_string:
            if ch == '\\':
                i += 1
            elif ch == string_char:
                in_string = False
        else:
            if ch in ('"', "'", '`'):
                in_string = True
                string_char = ch
            elif ch == '/' and i + 1 < length:
                if content[i + 1] == '/':
                    in_comment = True
                    i += 1
                elif content[i + 1] == '*':
                    in_block_comment = True
                    i += 1
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return content[:i].count('\n') + 1
        i += 1
    return content[:start_pos].count('\n') + 30

def evaluate_spec_completeness(spec_text: str) -> bool:
    """
    Evaluates whether the requirement specification contains structured acceptance criteria
    or is an informal, underspecified summary requiring adaptive inspection.
    Returns True if the spec is complete (keeps Level 2), False if underspecified (triggers Adaptive Level 4).
    Supports bilingual English & Vietnamese markers.
    """
    if not spec_text or len(spec_text.strip().split()) < 10:
        return False
    text_lower = spec_text.lower()
    gherkin_markers = ["given", "when", "then", "scenario", "kịch bản", "giả sử", "khi", "thì", "quy tắc"]
    if sum(1 for m in gherkin_markers if m in text_lower) >= 3:
        return True
    ac_markers = [
        "acceptance criteria", "tiêu chí nghiệm thu", "điều kiện chấp nhận", 
        "preconditions", "tiền điều kiện", "kỳ vọng", "expected result"
    ]
    has_ac = any(m in text_lower for m in ac_markers)
    has_quantitative = bool(re.search(r'(\d+\s*(phút|giờ|ngày|tháng|năm|vnđ|%|\$|ms|s|items|lần))|[><=!]=?', text_lower))
    return has_ac and has_quantitative

PAGE_OBJECT_DIRS = ["tests/pages", "e2e/pages", "page-objects", "src/pages", "playwright/pages", "cypress/pages", "04-src/tests/pages", "admin/tests/pages"]

class MethodDiscoveryEngine:
    def __init__(self, repo_path: Path):
        self.repo_path = Path(repo_path).resolve()
        self.db_path = self.repo_path / ".codegraph" / "codegraph.db"
        self._conn = None
        self.synonyms = self._load_synonyms()

    def _load_synonyms(self) -> Dict[str, List[str]]:
        """
        Loads domain action synonyms from system reference or built-in dictionary,
        and merges with repository custom config overrides.
        """
        base_synonyms = {}

        # 1. Load base synonyms from system reference
        sys_ref = SYSTEM_ROOT / "references" / "domain-action-synonyms.json"
        if sys_ref.exists():
            try:
                with open(sys_ref, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    actions = data.get("actions", data)
                    if isinstance(actions, dict):
                        base_synonyms = dict(actions)
            except Exception:
                pass

        if not base_synonyms:
            base_synonyms = {
                "login": ["login", "signin", "authenticate", "clicklogin", "log_in", "sign_in"],
                "logout": ["logout", "signout", "log_out", "sign_out"],
                "order": ["order", "placeorder", "createorder", "submitorder", "trackorder"],
                "checkout": ["checkout", "processcheckout", "gotocheckout", "submitorder"],
                "pay": ["pay", "makepayment", "processpayment", "charge"],
                "add": ["add", "additem", "insert", "append", "createitem"],
                "remove": ["remove", "removeitem", "deleteitem", "dropitem"],
                "clear": ["clear", "reset", "empty", "clearcart"],
                "submit": ["submit", "send", "confirm", "postform"],
                "cancel": ["cancel", "abort", "dismiss", "closemodal"],
                "search": ["search", "find", "query", "lookup"],
                "filter": ["filter", "applyfilter", "refineresults"],
                "select": ["select", "choose", "pickoption"],
                "export": ["export", "exportexcel", "exportcsv"],
                "approve": ["approve", "confirmrequest", "acceptrequest"],
                "reject": ["reject", "declinerequest", "denyapproval"]
            }

        # 2. Check and merge custom repo overrides
        custom_paths = [
            self.repo_path / ".codegraph" / "synonyms.json",
            self.repo_path / "domain-action-synonyms.json",
            self.repo_path / "qa-synonyms.json",
            self.repo_path / "references" / "domain-action-synonyms.json"
        ]
        for cp in custom_paths:
            if cp.exists():
                try:
                    with open(cp, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        custom_actions = data.get("actions", data)
                        if isinstance(custom_actions, dict):
                            base_synonyms.update(custom_actions)
                except Exception:
                    pass

        return base_synonyms
    def _get_db(self) -> Optional[sqlite3.Connection]:
        if not self.db_path.exists():
            return None
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path), timeout=5)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def _get_search_terms(self, action_name: str) -> List[str]:
        """
        Expands an action name into search variants including category name and synonyms.
        Enables multi-language and variant search (e.g. 'dang_nhap' -> ['dang_nhap', 'dangnhap', 'login', 'signin']).
        """
        action_clean = action_name.strip().lower()
        terms = {action_clean, action_clean.replace("_", ""), action_clean.replace("-", "")}
        
        for cat, syns in self.synonyms.items():
            cat_lower = cat.lower()
            syns_lower = [s.lower() for s in syns]
            if action_clean == cat_lower or action_clean in syns_lower or cat_lower in action_clean:
                terms.add(cat_lower)
                for s in syns_lower:
                    if len(s) >= 3:
                        terms.add(s)
                        terms.add(s.replace("_", ""))
        return [t for t in terms if len(t) >= 2]

    def discover_candidates(self, action_name: str, scope_hint: Optional[str] = None, fallback: bool = True) -> List[Dict[str, Any]]:
        """
        Queries CodeGraph SQLite nodes for matching methods, functions, and object properties.
        Falls back to Page Object / helper file scanning if CodeGraph has no matches or DB is absent.
        """
        candidates = []
        action_clean = action_name.strip().lower()

        conn = self._get_db()
        if conn:
            cur = conn.cursor()
            query_sql = """
            SELECT id, kind, name, qualified_name, file_path, start_line, end_line, signature, docstring, is_exported
            FROM nodes
            WHERE (
                lower(name) = ?
                OR lower(name) LIKE ?
                OR lower(qualified_name) LIKE ?
            )
            AND kind IN ('function', 'method', 'arrow_function', 'constant', 'property', 'class')
            """
            params = [action_clean, f"%{action_clean}%", f"%{action_clean}%"]

            if scope_hint:
                query_sql += " AND lower(file_path) LIKE ?"
                params.append(f"%{scope_hint.strip().lower()}%")

            query_sql += " ORDER BY CASE WHEN lower(name) = ? THEN 0 ELSE 1 END, start_line LIMIT 30"
            params.append(action_clean)

            try:
                rows = cur.execute(query_sql, params).fetchall()
                for r in rows:
                    candidates.append({
                        "id": r["id"],
                        "kind": r["kind"],
                        "name": r["name"],
                        "qualified_name": r["qualified_name"],
                        "file_path": r["file_path"],
                        "start_line": r["start_line"],
                        "end_line": r["end_line"],
                        "signature": r["signature"] or "",
                        "docstring": r["docstring"] or "",
                        "is_exported": bool(r["is_exported"]),
                        "source": "codegraph_index"
                    })
            except Exception:
                pass

        if not candidates and fallback:
            candidates = self.fallback_search(action_name, scope_hint)

        return candidates

    def fallback_search(self, action_name: str, scope_hint: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Deterministic regex fallback scanner for repositories without CodeGraph DB
        or for dynamic objects not captured in the AST index.
        Scans Page Object directories and helper folders.
        Supports single-line and multi-line method signatures (e.g. formatted by Prettier),
        and expands domain synonyms (e.g. Vietnamese 'dang_nhap' -> finds 'login').
        """
        candidates = []
        search_terms = self._get_search_terms(action_name)
        action_pattern = "|".join(re.escape(t) for t in sorted(search_terms, key=len, reverse=True))

        target_dirs = list(PAGE_OBJECT_DIRS)
        if scope_hint:
            target_dirs.insert(0, scope_hint)

        p_patterns = [
            # standard / async method: async methodName(...) { or methodName(...) {
            re.compile(rf'(?:async\s+)?([a-zA-Z0-9_$]*(?:{action_pattern})[a-zA-Z0-9_$]*)\s*\((.*?)\)\s*(?::\s*[^{{]+)?\{{', re.IGNORECASE | re.DOTALL),
            # arrow function: const methodName = async (...) =>
            re.compile(rf'(?:export\s+)?(?:const|let|var)\s+([a-zA-Z0-9_$]*(?:{action_pattern})[a-zA-Z0-9_$]*)\s*=\s*(?:async\s*)?\((.*?)\)\s*(?::\s*[^=]+)?=>', re.IGNORECASE | re.DOTALL),
            # object method: methodName(...) : Type {
            re.compile(rf'([a-zA-Z0-9_$]*(?:{action_pattern})[a-zA-Z0-9_$]*)\s*\((.*?)\)\s*(?::\s*([^{{]+))?\{{', re.IGNORECASE | re.DOTALL)
        ]

        seen_candidates = set()

        for td in target_dirs:
            dir_p = self.repo_path / td
            if not dir_p.is_dir():
                continue
            for root, _, files in os.walk(dir_p):
                for f in files:
                    if f.endswith((".ts", ".tsx", ".js", ".mjs", ".jsx")):
                        f_path = Path(root) / f
                        try:
                            content = f_path.read_text(encoding="utf-8", errors="ignore")
                            rel_p = f_path.relative_to(self.repo_path).as_posix()
                            total_lines = content.count("\n") + 1

                            for p_regex in p_patterns:
                                for match in p_regex.finditer(content):
                                    m_name = match.group(1).replace("async", "").strip()
                                    if not m_name or not any(t in m_name.lower() for t in search_terms):
                                        continue

                                    start_pos = match.start()
                                    start_line = content[:start_pos].count("\n") + 1
                                    cand_key = f"{rel_p}:{m_name}:{start_line}"
                                    if cand_key in seen_candidates:
                                        continue
                                    seen_candidates.add(cand_key)

                                    # Extract matched signature snippet (compacted to single line)
                                    sig_raw = match.group(0).rstrip("{").strip()
                                    sig_compact = " ".join(line.strip() for line in sig_raw.splitlines())

                                    candidates.append({
                                        "id": f"fallback:{rel_p}:{start_line}",
                                        "kind": "method/function",
                                        "name": m_name,
                                        "qualified_name": f"{rel_p}::{m_name}",
                                        "file_path": rel_p,
                                        "start_line": start_line,
                                        "end_line": min(find_block_end(content, start_pos), total_lines),
                                        "signature": sig_compact,
                                        "docstring": "",
                                        "is_exported": "export" in sig_compact,
                                        "source": "fallback_ast_scan"
                                    })
                        except Exception:
                            pass

        return candidates
    def get_progressive_context(self, candidate: Dict[str, Any], level: int = 2, target_level: Optional[int] = None) -> Dict[str, Any]:
        """
        Progressive Context Retrieval (Levels 1 to 5):
        Level 1: Symbol Name & Location.
        Level 2: Signature & Return Type.
        Level 3: Dependency / Caller-Callee Relationships.
        Level 4: Implementation Snippet (bounded lines).
        Level 5: Full Source File.
        """
        if target_level is not None:
            level = target_level

        result = {
            "name": candidate["name"],
            "file": candidate["file_path"],
            "lines": f"L{candidate['start_line']}-L{candidate['end_line']}",
            "level_achieved": level
        }

        if level >= 2:
            result["signature"] = candidate.get("signature", "")
            result["kind"] = candidate.get("kind", "")
            result["is_exported"] = candidate.get("is_exported", False)

        if level >= 3:
            conn = self._get_db()
            relationships = {"callers": [], "callees": [], "imports": []}
            if conn and candidate.get("id"):
                cur = conn.cursor()
                try:
                    edges = cur.execute(
                        "SELECT kind, source, target FROM edges WHERE source = ? OR target = ?",
                        [candidate["id"], candidate["id"]]
                    ).fetchall()
                    for e in edges:
                        if e["source"] == candidate["id"]:
                            relationships["callees"].append(f"{e['kind']} -> {e['target']}")
                        else:
                            relationships["callers"].append(f"{e['source']} -> {e['kind']}")
                except Exception:
                    pass
            result["relationships"] = relationships

        if level >= 4:
            full_p = self.repo_path / candidate["file_path"]
            if full_p.exists():
                try:
                    all_lines = full_p.read_text(encoding="utf-8").splitlines()
                    s_idx = max(0, candidate["start_line"] - 1)
                    e_idx = min(len(all_lines), candidate["end_line"])
                    snippet = "\n".join(all_lines[s_idx:e_idx])
                    result["implementation"] = snippet
                except Exception as ex:
                    result["implementation_error"] = str(ex)

        if level >= 5:
            full_p = self.repo_path / candidate["file_path"]
            if full_p.exists():
                try:
                    result["full_source"] = full_p.read_text(encoding="utf-8")
                except Exception as ex:
                    result["full_source_error"] = str(ex)

        return result

    def _parse_params(self, sig: str) -> Dict[str, Any]:
        """
        Extracts and analyzes parameter signature.
        Handles destructured objects ({ user, pass }), regular parameters, and paramless calls.
        """
        m = re.search(r'\((.*?)\)', sig, re.DOTALL)
        if not m:
            return {"param_count": 0, "is_empty": True, "has_destructured": False, "raw": ""}
        raw = m.group(1).strip()
        if not raw:
            return {"param_count": 0, "is_empty": True, "has_destructured": False, "raw": ""}
        
        has_destructured = "{" in raw and "}" in raw
        # Remove destructured contents temporarily to count outer parameters accurately
        normalized = re.sub(r'\{.*?\}', 'DESTRUCTURED_OBJ', raw)
        parts = [p.strip() for p in normalized.split(',') if p.strip()]
        return {
            "param_count": len(parts),
            "is_empty": False,
            "has_destructured": has_destructured,
            "raw": raw
        }

    def classify_reuse(self, requirement_action: str, candidate: Dict[str, Any]) -> Tuple[str, str]:
        """
        Parameter-aware and AST-informed reuse classification.
        Classifies candidate into: DIRECT_REUSE, CONDITIONAL_REUSE, NOT_REUSABLE.
        """
        cand_name = candidate["name"]
        if cand_name.startswith("_"):
            return "NOT_REUSABLE", f"Method '{cand_name}' is private/internal and must not be reused directly in test automation."

        name = cand_name.lower()
        sig = candidate.get("signature", "")
        req = requirement_action.lower().strip()
        params_info = self._parse_params(sig)

        # Action component helpers (e.g. clickLogin() with 0 params) vs full action (e.g. login(u, p))
        is_click_button_only = (name.startswith("click") or name.startswith("press")) and params_info["is_empty"]

        # Check in synonyms dictionary
        syns = self.synonyms.get(req, [req])
        is_synonym_match = (name == req) or (name in syns)

        if is_synonym_match:
            # If it's a 0-parameter click button helper when requirement expects action (e.g. login)
            if is_click_button_only and req in ["login", "checkout", "pay", "submit", "register"]:
                return "CONDITIONAL_REUSE", f"Action component helper '{candidate['name']}' performs button interaction only; requires preceding form input actions."

            # Structured parameters or destructured options (e.g., login({ username, password }))
            if params_info["has_destructured"] or params_info["param_count"] >= 1:
                return "DIRECT_REUSE", f"Method '{candidate['name']}' directly matches required action '{req}' with contract parameters: ({params_info['raw']})"

            # If page fixture or browser context parameter is needed
            if "page:" in sig.lower() or "context:" in sig.lower():
                return "CONDITIONAL_REUSE", f"Method '{candidate['name']}' matches action '{req}' but requires injecting test fixture or page context."

            return "DIRECT_REUSE", f"Method '{candidate['name']}' is a direct match for action '{req}' with signature: {sig}"

        # Specialized variants (e.g. loginWithSso for login)
        if any(s in name for s in syns) and name not in syns:
            return "CONDITIONAL_REUSE", f"Method '{candidate['name']}' is a specialized variant for action '{req}' and may require specific options or credentials."

        if req in name:
            return "CONDITIONAL_REUSE", f"Method '{candidate['name']}' contains '{req}' but may require additional configuration."

        return "NOT_REUSABLE", f"Candidate '{candidate['name']}' does not fulfill the required action contract '{requirement_action}'."

    # Alias for flexibility
    classify_reusability = classify_reuse

    def score_candidate(self, action_name: str, cand: Dict[str, Any]) -> int:
        """
        Ranks candidate relevance for an action based on name match, parameters, and location.
        """
        score = 0
        name_lower = cand.get("name", "").lower()
        norm_action = action_name.lower().replace(" ", "").replace("_", "")

        # Exact match
        if name_lower == norm_action:
            score += 50
        elif norm_action in name_lower:
            score += 35
        elif any(syn in name_lower or name_lower in syn for syn in self.synonyms.get(norm_action, [])):
            score += 20

        # Location heuristic
        fpath = cand.get("file_path", "").lower()
        if any(k in fpath for k in ["page", "service", "action", "helper"]):
            score += 15
        if norm_action in fpath:
            score += 10

        # Parameter awareness
        sig = cand.get("signature", "")
        params = self._parse_params(sig)
        if params.get("param_count", 0) > 0:
            score += 15
        elif (name_lower.startswith("click") or name_lower.startswith("press")) and norm_action not in ["click", "press"]:
            # Action component penalty: click/press helper without params scored below direct action
            score -= 5

        if cand.get("is_exported"):
            score += 10

        return score
    def discover_and_evaluate(self, action_name: str, scope_hint: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes end-to-end discovery: CodeGraph -> Fallback -> Classification -> Progressive Context.
        """
        candidates = self.discover_candidates(action_name, scope_hint, fallback=True)
        discovery_source = "codegraph" if (candidates and candidates[0].get("source") == "codegraph_index") else "fallback_ast_scan"

        if not candidates:
            return {
                "action": action_name,
                "status": "NOT_FOUND",
                "classification": "NOT_FOUND",
                "reason": f"No existing method or function found for action '{action_name}' after querying CodeGraph and scanning fallback directories.",
                "candidate": None,
                "progressive_context": None
            }

        # Candidate ranking utilizing unified parameter-aware heuristics & domain synonyms
        ranked_candidates = sorted(candidates, key=lambda c: self.score_candidate(action_name, c), reverse=True)
        top_cand = ranked_candidates[0]
        classification, reason = self.classify_reuse(action_name, top_cand)
        prog_ctx = self.get_progressive_context(top_cand, level=4)

        return {
            "action": action_name,
            "status": "FOUND",
            "classification": classification,
            "reason": reason,
            "discovery_source": discovery_source,
            "total_candidates": len(candidates),
            "candidate": top_cand,
            "progressive_context": prog_ctx,
            "ranked_candidates_count": len(ranked_candidates)
        }

    def walk_call_tree(self, start_node_id: str, max_depth: int = 3) -> List[str]:
        """
        Performs bounded downstream BFS call-tree traversal starting from start_node_id.
        Cycle-safe using visited set. Traverses downstream calls: source = curr_id.
        """
        conn = self._get_db()
        if not conn:
            return []
        cur = conn.cursor()
        visited = set()
        traversal_order = []
        queue = [(start_node_id, 0)]
        while queue:
            curr_id, depth = queue.pop(0)
            if curr_id in visited or depth > max_depth:
                continue
            visited.add(curr_id)
            if depth > 0:
                traversal_order.append(curr_id)
            try:
                rows = cur.execute(
                    "SELECT target FROM edges WHERE source = ? AND kind IN ('call', 'reference')",
                    [curr_id]
                ).fetchall()
                for r in rows:
                    target_id = r["target"]
                    if target_id not in visited:
                        queue.append((target_id, depth + 1))
            except Exception:
                break
        return traversal_order

    def discover_adaptive_core_snippets(
        self, 
        spec_text: str, 
        entry_actions: Optional[List[str]] = None, 
        max_snippets: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Adaptive Level 4 JIT Engine:
        When specification is incomplete, selectively extracts implementation bodies of core calculation
        methods or declarative rule matrices without token bloat (capped at max_snippets).
        """
        if evaluate_spec_completeness(spec_text):
            return []
            
        conn = self._get_db()
        if not conn:
            return []
        cur = conn.cursor()
        
        # Step 1: Find entry candidate node IDs
        candidate_ids = []
        if entry_actions:
            for act in entry_actions:
                cands = self.discover_candidates(act, fallback=True)
                for c in cands:
                    if c.get("id"):
                        candidate_ids.append(c["id"])
        
        # If no explicit entry actions, locate exported functions/methods in relevant module files
        if not candidate_ids:
            try:
                rows = cur.execute(
                    "SELECT id FROM nodes WHERE is_exported = 1 AND kind IN ('function', 'method', 'class', 'variable', 'constant', 'enum') LIMIT 30"
                ).fetchall()
                candidate_ids = [r["id"] for r in rows]
            except Exception:
                pass
                
        # Step 2: Traverse call tree downstream (BFS)
        target_node_ids = []
        seen_targets = set()
        for cid in candidate_ids:
            downstream = self.walk_call_tree(cid, max_depth=3)
            for d in downstream:
                if d not in seen_targets:
                    seen_targets.add(d)
                    target_node_ids.append(d)
            if cid not in seen_targets:
                seen_targets.add(cid)
                target_node_ids.append(cid)
            
        adaptive_snippets = []
        rule_matrix_pattern = re.compile(
            r'\b(penalty|grace|fee|rate|tax|discount|threshold|limit|multiplier|tier|rule|config)\w*\b\s*[:=]\s*(\d+|\{|\[)',
            re.IGNORECASE
        )
        branch_pattern = re.compile(r'\b(if|else|switch|case|catch|\?)\b')
        
        for nid in target_node_ids:
            if len(adaptive_snippets) >= max_snippets:
                break
            try:
                node = cur.execute(
                    "SELECT id, name, file_path, start_line, end_line, signature FROM nodes WHERE id = ?",
                    [nid]
                ).fetchone()
                if not node or not node["file_path"]:
                    continue
                fpath = self.repo_path / node["file_path"]
                if not fpath.exists():
                    continue
                lines = fpath.read_text(encoding="utf-8", errors="ignore").splitlines()
                s_line = max(0, node["start_line"] - 1)
                e_line = min(len(lines), node["end_line"])
                body = "\n".join(lines[s_line:e_line])
                
                branches = len(branch_pattern.findall(body))
                is_rule_matrix = bool(rule_matrix_pattern.search(body))
                
                # Dual-Factor Heuristic: Cyclomatic Complexity M >= 2 OR Declarative Rule Matrix
                if branches >= 2 or is_rule_matrix:
                    reason = f"Cyclomatic Complexity M={branches + 1}" if branches >= 2 else "Declarative Rule Matrix"
                    adaptive_snippets.append({
                        "id": node["id"],
                        "name": node["name"],
                        "file_path": str(node["file_path"]),
                        "start_line": node["start_line"],
                        "end_line": node["end_line"],
                        "signature": node["signature"],
                        "body": body,
                        "reason": reason
                    })
            except Exception:
                continue
                
        return adaptive_snippets


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="CodeGraph Method Discovery & Reuse Engine")
    parser.add_argument("action", help="Action or method name to search (e.g. 'login', 'add', 'submitInquiry')")
    parser.add_argument("--repo", default=".", help="Repository root path (default: current directory)")
    parser.add_argument("--scope", help="Optional file or module scope hint")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("-o", "--output", help="Write full JSON to file and print compact summary")

    args = parser.parse_args()
    engine = MethodDiscoveryEngine(Path(args.repo))
    res = engine.discover_and_evaluate(args.action, args.scope)
    engine.close()

    if args.output:
        out_p = Path(args.output)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=2, ensure_ascii=False)
        print(f"[DISCOVERY] Action: '{res['action']}' | Result: {res['classification']} | Source: {res.get('discovery_source', 'N/A')}")
        print(f"Saved full discovery context to: {out_p}")
    elif args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print(f"=== METHOD DISCOVERY: '{res['action']}' ===")
        print(f"Classification : {res['classification']}")
        print(f"Reason         : {res['reason']}")
        if res.get("candidate"):
            c = res["candidate"]
            print(f"Candidate      : [{c['kind']}] {c['name']} ({c['file_path']}#L{c['start_line']}-L{c['end_line']})")
            if res.get("progressive_context", {}).get("signature"):
                print(f"Signature      : {res['progressive_context']['signature']}")
        sys.exit(0 if res["status"] == "FOUND" else 1)
