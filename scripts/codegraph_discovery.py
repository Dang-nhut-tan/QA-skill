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

PAGE_OBJECT_DIRS = ["tests/pages", "e2e/pages", "page-objects", "04-src/tests/pages", "admin/tests/pages"]

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
                                        "end_line": min(start_line + 30, total_lines),
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
                        "SELECT kind, source, target FROM edges WHERE source = ? OR target = ? LIMIT 10",
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

        # Multi-candidate ranking: rank candidates by reusability relevance
        def score_candidate(cand: Dict[str, Any]) -> int:
            c_name = cand["name"].lower()
            score = 0
            if c_name == action_name.lower():
                score += 50
            elif c_name in self.synonyms.get(action_name.lower(), []):
                score += 35
            elif action_name.lower() in c_name:
                score += 20
            
            # Action component penalty: clickX without params scored slightly below full method X(params)
            sig_raw = cand.get("signature", "")
            if (c_name.startswith("click") or c_name.startswith("press")) and "()" in sig_raw:
                score -= 5
            elif "(" in sig_raw and ")" in sig_raw and not "()" in sig_raw:
                score += 15 # has parameters
            
            if cand.get("is_exported"):
                score += 10
            return score

        ranked_candidates = sorted(candidates, key=score_candidate, reverse=True)
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
