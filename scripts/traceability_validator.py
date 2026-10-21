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
        tokens = [t.strip() for t in re.split(r'[/;,|]', ref_raw) if t.strip()]
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
            matched = any(
                req_clean.lower() in token.lower() or token.lower() in req_clean.lower()
                for token in all_referenced_tokens
            )
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
    # 3. Deduplication Check (Detect Redundant / Overlapping Test Cases)
    # -------------------------------------------------------------
    duplicate_groups = []
    checked_pairs = set()
    
    for i in range(len(testcases)):
        for j in range(i + 1, len(testcases)):
            tc1 = testcases[i]
            tc2 = testcases[j]
            id1, id2 = tc1.get("id", f"Row{i}"), tc2.get("id", f"Row{j}")
            pair_key = tuple(sorted([id1, id2]))
            if pair_key in checked_pairs:
                continue
            checked_pairs.add(pair_key)
            
            # Compare key attributes
            name1, name2 = normalize_text(tc1.get("name", "")), normalize_text(tc2.get("name", ""))
            steps1, steps2 = normalize_text(tc1.get("steps", "")), normalize_text(tc2.get("steps", ""))
            exp1, exp2 = normalize_text(tc1.get("expected_result", "")), normalize_text(tc2.get("expected_result", ""))
            pre1, pre2 = normalize_text(tc1.get("preconditions", "")), normalize_text(tc2.get("preconditions", ""))
            data1, data2 = normalize_text(tc1.get("test_data", "")), normalize_text(tc2.get("test_data", ""))
            
            # Exact duplicates on Name or (Steps and Expected Result)
            is_exact_name = (name1 and name1 == name2)
            is_identical_behavior = (steps1 and exp1 and steps1 == steps2 and exp1 == exp2 and pre1 == pre2)
            
            if is_exact_name or is_identical_behavior:
                duplicate_groups.append({
                    "pair": [id1, id2],
                    "reason": "Exact duplicate name" if is_exact_name else "Identical steps and expected result",
                    "details": {
                        id1: tc1.get("name", ""),
                        id2: tc2.get("name", "")
                    }
                })

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
