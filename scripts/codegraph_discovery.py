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

PAGE_OBJECT_DIRS = ["tests/pages", "e2e/pages", "page-objects", "04-src/tests/pages", "admin/tests/pages"]

class MethodDiscoveryEngine:
    def __init__(self, repo_path: Path):
        self.repo_path = Path(repo_path).resolve()
        self.db_path = self.repo_path / ".codegraph" / "codegraph.db"
        self._conn = None

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
        """
        candidates = []
        action_clean = action_name.strip().lower()

        target_dirs = list(PAGE_OBJECT_DIRS)
        if scope_hint:
            target_dirs.insert(0, scope_hint)

        p_method = re.compile(rf'(?:async\s+)?([a-zA-Z0-9_$]*{re.escape(action_clean)}[a-zA-Z0-9_$]*)\s*\(([^)]*)\)\s*\{{', re.IGNORECASE)
        p_arrow = re.compile(rf'(?:export\s+)?(?:const|let|var)\s+([a-zA-Z0-9_$]*{re.escape(action_clean)}[a-zA-Z0-9_$]*)\s*=\s*(?:async\s*)?\(([^)]*)\)\s*(?::\s*[^=]+)?=>', re.IGNORECASE)
        p_obj_method = re.compile(rf'([a-zA-Z0-9_$]*{re.escape(action_clean)}[a-zA-Z0-9_$]*)\s*\(([^)]*)\)\s*(?::\s*([^{{]+))?\{{', re.IGNORECASE)

        for td in target_dirs:
            dir_p = self.repo_path / td
            if not dir_p.is_dir():
                continue
            for root, _, files in os.walk(dir_p):
                for f in files:
                    if f.endswith((".ts", ".tsx", ".js", ".mjs", ".jsx")):
                        f_path = Path(root) / f
                        try:
                            lines = f_path.read_text(encoding="utf-8").splitlines()
                            rel_p = f_path.relative_to(self.repo_path).as_posix()
                            for idx, line in enumerate(lines):
                                l_str = line.strip()
                                m1 = p_method.search(l_str) or p_arrow.search(l_str) or p_obj_method.search(l_str)
                                if m1:
                                    m_name = m1.group(1) if m1.group(1) else m1.group(2)
                                    m_name = m_name.replace("async", "").strip()
                                    if action_clean in m_name.lower():
                                        candidates.append({
                                            "id": f"fallback:{rel_p}:{idx+1}",
                                            "kind": "method/function",
                                            "name": m_name,
                                            "qualified_name": f"{rel_p}::{m_name}",
                                            "file_path": rel_p,
                                            "start_line": idx + 1,
                                            "end_line": min(idx + 30, len(lines)),
                                            "signature": l_str,
                                            "docstring": "",
                                            "is_exported": "export" in l_str,
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

    def classify_reuse(self, requirement_action: str, candidate: Dict[str, Any]) -> Tuple[str, str]:
        """
        Classifies candidate into DIRECT_REUSE, CONDITIONAL_REUSE, NOT_REUSABLE.
        """
        cand_name = candidate["name"]
        if cand_name.startswith("_"):
            return "NOT_REUSABLE", f"Method '{cand_name}' is private/internal and must not be reused directly in test automation."

        name = cand_name.lower()
        sig = candidate.get("signature", "").lower()
        req = requirement_action.lower().strip()

        # 1. Exact match
        if name == req:
            return "DIRECT_REUSE", f"Method '{candidate['name']}' matches required action directly with signature: {candidate.get('signature', '')}"

        # 2. Semantic equivalents
        direct_synonyms = {
            "login": ["login", "signin", "clicklogin", "authenticate"],
            "add": ["add", "additem", "insert"],
            "logout": ["logout", "signout"],
            "clear": ["clear", "reset", "empty"],
            "submit": ["submit", "send", "confirm"]
        }

        if req in direct_synonyms:
            syns = direct_synonyms[req]
            if name in syns:
                if "page" in sig or "context" in sig or "{" in sig:
                    return "CONDITIONAL_REUSE", f"Method '{candidate['name']}' matches action '{req}' but requires specific parameters or setup."
                return "DIRECT_REUSE", f"Method '{candidate['name']}' is a direct semantic match for action '{req}'."
            # If it contains the action name but has extra suffixes/prefixes (e.g. loginWithSso)
            if any(s in name for s in syns) and name not in syns:
                return "CONDITIONAL_REUSE", f"Method '{candidate['name']}' is a specialized variant for action '{req}' and may require specific options."

        if req in name:
            return "CONDITIONAL_REUSE", f"Method '{candidate['name']}' contains '{req}' but might require additional configuration."

        return "NOT_REUSABLE", f"Candidate '{candidate['name']}' does not fulfill the required action contract '{requirement_action}'."

    # Alias for flexibility
    classify_reusability = classify_reuse

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

        top_cand = candidates[0]
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
            "progressive_context": prog_ctx
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
