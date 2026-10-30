#!/usr/bin/env python3
"""
scripts/traceability_validator.py
Requirement Traceability and Deduplication Validator for the QA Agent System.

Enforces three non-negotiable verification gates:
1. Coverage Check (Forward): Every critical requirement has at least one test case.
2. Grounding Check (Backward): No test case lacks requirement or source-code evidence.
3. Deduplication Check: No two test cases share identical or redundant test objectives.
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def normalize_text(text: str) -> str:
    """Normalize text for semantic comparison (lowercase, trimmed, collapsed whitespace)."""
    if not text:
        return ""
    t = text.lower().strip()
    return re.sub(r'\s+', ' ', t)


def split_requirement_references(ref_raw: str) -> List[str]:
    """
    Context-aware splitting of requirement references.
    Splits by ',', ';', '|', or ' / ' (slash with whitespace).
    Preserves file paths (e.g., 'src/features/auth.ts#L45') while safely
    splitting paired requirement IDs (e.g., 'REQ-01/REQ-02').
    """
    if not ref_raw:
        return []
    
    # 1. First split by clear delimiters: comma, semicolon, pipe, or slash surrounded by spaces
    primary_parts = re.split(r'[,;|]|\s+/\s+', ref_raw)
    
    final_tokens = []
    # Pattern indicating a code file path
    path_pattern = re.compile(r'(\.[a-zA-Z0-9]{1,5}(#L\d+)?$|#L\d+|^\.{1,2}[/\\]|[/\\][a-zA-Z0-9_-]+[/\\])')
    req_id_pattern = re.compile(r'^[A-Za-z0-9_\-\.]+$')

    for part in primary_parts:
        part = part.strip()
        if not part:
            continue
        
        # Check if part has internal slash without spaces (e.g. 'REQ-01/REQ-02' vs 'src/auth.ts')
        if '/' in part:
            # If it looks like a file path, preserve it intact
            if path_pattern.search(part) or part.count('/') > 2:
                final_tokens.append(part)
            else:
                sub_parts = [s.strip() for s in part.split('/') if s.strip()]
                # If all sub_parts look like requirement IDs, split them
                if all(req_id_pattern.match(s) for s in sub_parts):
                    final_tokens.extend(sub_parts)
                else:
                    final_tokens.append(part)
        else:
            final_tokens.append(part)
            
    return final_tokens

def validate_traceability(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates bidirectional requirement traceability and detects duplicate test cases.
    
    Expected data structure:
    {
        "requirements": ["SPEC-AU-01", "SPEC-HT-26", "SPEC-AU-49", ...],
        "testcases": [
            {
                "id": "TC-AUTH-001",
                "name": "...",
                "preconditions": "...",
                "test_data": "...",
                "steps": "...",
                "expected_result": "...",
                "requirement_ref": "SPEC-AU-01 / BR§2.1",
                ...
            }
        ]
    }
    """
    testcases: List[Dict[str, Any]] = data.get("testcases", [])
    declared_requirements: List[str] = data.get("requirements", [])
    
    # -------------------------------------------------------------
    # 1. Backward Traceability Check (Detect Orphan / Hallucinated Tests)
    # -------------------------------------------------------------
    orphan_testcases = []
    tc_references_map: Dict[str, Set[str]] = {}
    
    for tc in testcases:
        tc_id = tc.get("id", "UNKNOWN")
        ref_raw = str(tc.get("requirement_ref", "") or "").strip()
        
        # An orphan test case has no requirement reference or placeholder only
        if not ref_raw or ref_raw.lower() in ["n/a", "none", "null", "-", "chưa có", "unspecified"]:
            orphan_testcases.append({
                "id": tc_id,
                "name": tc.get("name", ""),
                "reason": "Missing Requirement Reference or ungrounded test case (no spec ID or code symbol provided)"
            })
            continue
            
        # Extract individual requirement tokens (split by /, ;, ,, |)
        tokens = split_requirement_references(ref_raw)
        tc_references_map[tc_id] = set(tokens)

    # -------------------------------------------------------------
    # 2. Forward Traceability Check (Detect Orphan Requirements)
    # -------------------------------------------------------------
    all_referenced_tokens = set()
    for tokens in tc_references_map.values():
        all_referenced_tokens.update(tokens)
        
    orphan_requirements = []
    covered_requirements = []
    
    # If explicit requirements list is provided, verify 100% coverage
    if declared_requirements:
        for req in declared_requirements:
            req_clean = req.strip()
            # Match if req is a token or part of any token
            # Exact token matching or word boundary regex (prevents 'REQ-1' from falsely matching 'REQ-10', 'REQ-100')
            matched = False
            for token in all_referenced_tokens:
                t_clean = token.strip().lower()
                r_clean = req_clean.lower()
                if t_clean == r_clean:
                    matched = True
                    break
                # Word-boundary check: ensures 'REQ-1' matches in 'REQ-1 / SPEC-01' but NOT in 'REQ-10'
                if re.search(rf'(?<![A-Za-z0-9_-]){re.escape(r_clean)}(?![A-Za-z0-9_-])', t_clean):
                    matched = True
                    break
                if re.search(rf'(?<![A-Za-z0-9_-]){re.escape(t_clean)}(?![A-Za-z0-9_-])', r_clean):
                    matched = True
                    break
            if matched:
                covered_requirements.append(req_clean)
            else:
                orphan_requirements.append({
                    "requirement": req_clean,
                    "reason": "Critical requirement has 0 mapped test cases"
                })
    else:
        # If not explicitly provided, use the set of extracted requirement tokens
        covered_requirements = sorted(list(all_referenced_tokens))

    # -------------------------------------------------------------
    # 3. Deduplication Check (Single-Pass O(N) Hash Map Lookup)
    # -------------------------------------------------------------
    duplicate_groups = []
    checked_pairs = set()
    seen_names = {}      # norm_name -> (tc_id, tc_dict)
    seen_behaviors = {}  # (norm_steps, norm_exp, norm_pre) -> (tc_id, tc_dict)
    
    for idx, tc in enumerate(testcases):
        tc_id = tc.get("id", f"Row{idx}")
        n_name = normalize_text(tc.get("name", ""))
        n_steps = normalize_text(tc.get("steps", ""))
        n_exp = normalize_text(tc.get("expected_result", ""))
        n_pre = normalize_text(tc.get("preconditions", ""))
        
        # Check exact duplicate name
        if n_name:
            if n_name in seen_names:
                prior_id, prior_tc = seen_names[n_name]
                pair_key = tuple(sorted([prior_id, tc_id]))
                if pair_key not in checked_pairs:
                    checked_pairs.add(pair_key)
                    duplicate_groups.append({
                        "pair": [prior_id, tc_id],
                        "reason": "Exact duplicate name",
                        "details": {
                            prior_id: prior_tc.get("name", ""),
                            tc_id: tc.get("name", "")
                        }
                    })
            else:
                seen_names[n_name] = (tc_id, tc)
                
        # Check identical behavior (steps, expected result, preconditions)
        if n_steps and n_exp:
            beh_key = (n_steps, n_exp, n_pre)
            if beh_key in seen_behaviors:
                prior_id, prior_tc = seen_behaviors[beh_key]
                pair_key = tuple(sorted([prior_id, tc_id]))
                if pair_key not in checked_pairs:
                    checked_pairs.add(pair_key)
                    duplicate_groups.append({
                        "pair": [prior_id, tc_id],
                        "reason": "Identical steps and expected result",
                        "details": {
                            prior_id: prior_tc.get("name", ""),
                            tc_id: tc.get("name", "")
                        }
                    })
            else:
                seen_behaviors[beh_key] = (tc_id, tc)

    # -------------------------------------------------------------
    # 4. Compile Final Audit Metrics
    # -------------------------------------------------------------
    total_req_count = len(declared_requirements) if declared_requirements else len(covered_requirements)
    coverage_rate = (len(covered_requirements) / total_req_count * 100) if total_req_count > 0 else 100.0
    
    is_valid = (len(orphan_requirements) == 0 and len(orphan_testcases) == 0 and len(duplicate_groups) == 0)
    
    return {
        "valid": is_valid,
        "metrics": {
            "total_testcases": len(testcases),
            "total_requirements": total_req_count,
            "covered_requirements_count": len(covered_requirements),
            "coverage_percentage": round(coverage_rate, 1),
            "orphan_requirements_count": len(orphan_requirements),
            "orphan_testcases_count": len(orphan_testcases),
            "duplicate_groups_count": len(duplicate_groups)
        },
        "orphan_requirements": orphan_requirements,
        "orphan_testcases": orphan_testcases,
        "duplicate_groups": duplicate_groups,
        "covered_requirements": covered_requirements
    }

def print_report(audit_result: Dict[str, Any], compact: bool = False):
    m = audit_result["metrics"]
    if audit_result["valid"]:
        if compact:
            print(f"[PASS] Traceability: 100% valid (TCs: {m['total_testcases']}, Reqs: {m['total_requirements']})")
        else:
            print(f"[PASS] Traceability & Deduplication Audit: 100% Valid")
            print(f"Metrics: Total TCs: {m['total_testcases']} | Reqs: {m['covered_requirements_count']}/{m['total_requirements']} ({m['coverage_percentage']}%) | Orphans: 0 | Duplicates: 0")
        return

    print("[FAIL] Traceability & Deduplication Violations Found:")
    print(f"Metrics: TCs: {m['total_testcases']} | Reqs: {m['covered_requirements_count']}/{m['total_requirements']} | Orphan Reqs: {m['orphan_requirements_count']} | Orphan TCs: {m['orphan_testcases_count']} | Duplicates: {m['duplicate_groups_count']}")
    
    if audit_result["orphan_requirements"]:
        print("\nOrphan Requirements (0 TCs mapped):")
        for o in audit_result["orphan_requirements"]:
            print(f"  - {o['requirement']}: {o['reason']}")
            
    if audit_result["orphan_testcases"]:
        print("\nOrphan Test Cases (No code/spec reference):")
        for o in audit_result["orphan_testcases"]:
            print(f"  - [{o['id']}] {o['name']}")
            
    if audit_result["duplicate_groups"]:
        print("\nDuplicate / Redundant Test Pairs:")
        for d in audit_result["duplicate_groups"]:
            print(f"  - Pair {d['pair']}: {d['reason']}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python traceability_validator.py <payload.json> [--compact|--json]")
        sys.exit(1)
        
    p = Path(sys.argv[1])
    if not p.exists():
        print(f"File not found: {p}")
        sys.exit(1)
        
    with open(p, "r", encoding="utf-8") as f:
        payload = json.load(f)
        
    res = validate_traceability(payload)
    if "--json" in sys.argv:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        is_compact = "--compact" in sys.argv or "-c" in sys.argv
        print_report(res, compact=is_compact)
    sys.exit(0 if res["valid"] else 1)
