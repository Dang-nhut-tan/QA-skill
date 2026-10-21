#!/usr/bin/env python3
"""
scripts/learn_manager.py
Manages dynamic knowledge capture, continuous learning, and human-approved skill augmentation.
Detects recurring errors or framework quirks, formulates proposals,
and appends approved insights into target SKILL.md files or project references.
"""

import sys
import os
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

SYSTEM_ROOT = Path(__file__).resolve().parent.parent
LEARNINGS_FILE = SYSTEM_ROOT / "references" / "project-learnings.json"

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def load_learnings() -> Dict[str, Any]:
    if not LEARNINGS_FILE.exists():
        return {"proposals": [], "applied": []}
    try:
        with open(LEARNINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"proposals": [], "applied": []}

def save_learnings(data: Dict[str, Any]) -> None:
    LEARNINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LEARNINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def propose_learning(title: str, issue: str, root_cause: str, solution: str, target_skill: str) -> Dict[str, Any]:
    data = load_learnings()
    proposal_id = f"LRN-{len(data.get('proposals', [])) + len(data.get('applied', [])) + 1:03d}"
    
    proposal = {
        "id": proposal_id,
        "title": title,
        "issue": issue,
        "root_cause": root_cause,
        "solution": solution,
        "target_skill": target_skill,
        "status": "PENDING_APPROVAL",
        "created_at": _now()
    }
    
    data.setdefault("proposals", []).append(proposal)
    save_learnings(data)
    print(f"[PROPOSED] Created proposal {proposal_id}: {title}")
    return proposal

def approve_learning(proposal_id: str) -> Dict[str, Any]:
    data = load_learnings()
    proposal = None
    for p in data.get("proposals", []):
        if p["id"] == proposal_id:
            proposal = p
            break
            
    if not proposal:
        raise ValueError(f"Proposal {proposal_id} not found or already processed.")
        
    target_skill_name = proposal["target_skill"]
    skill_file = SYSTEM_ROOT / "skills" / target_skill_name / "SKILL.md"
    
    # 1. Format the insight markdown block
    insight_block = f"""

## Project-Specific Learnings & Best Practices
> [!TIP]
> **{proposal['title']}** (Mã: {proposal['id']} - Đã duyệt: {_now()[:10]})
> - **Vấn đề / Điểm nghẽn lặp lại:** {proposal['issue']}
> - **Nguyên nhân gốc rễ:** {proposal['root_cause']}
> - **Giải pháp tối ưu đã kiểm chứng:** {proposal['solution']}
"""

    # 2. Append to target skill if it exists
    if skill_file.exists():
        content = skill_file.read_text(encoding="utf-8")
        if "## Project-Specific Learnings & Best Practices" in content:
            # Append inside existing section
            sub_block = f"""
> [!TIP]
> **{proposal['title']}** (Mã: {proposal['id']} - Đã duyệt: {_now()[:10]})
> - **Vấn đề / Điểm nghẽn lặp lại:** {proposal['issue']}
> - **Nguyên nhân gốc rễ:** {proposal['root_cause']}
> - **Giải pháp tối ưu đã kiểm chứng:** {proposal['solution']}
"""
            content += "\n" + sub_block
        else:
            content += "\n" + insight_block
        skill_file.write_text(content, encoding="utf-8")
        print(f"[OK] Knowledge injected into skill: {skill_file}")
    else:
        # Fallback to appending in references/project-learnings.md
        ref_doc = SYSTEM_ROOT / "references" / "project-learnings.md"
        with open(ref_doc, "a", encoding="utf-8") as f:
            f.write(insight_block + "\n")
        print(f"[OK] Target skill not found. Knowledge appended to: {ref_doc}")

    # 3. Update status in database
    data["proposals"].remove(proposal)
    proposal["status"] = "APPLIED"
    proposal["applied_at"] = _now()
    data.setdefault("applied", []).append(proposal)
    save_learnings(data)
    
    return proposal

def list_learnings() -> None:
    data = load_learnings()
    print("=== PENDING LEARNING PROPOSALS ===")
    if not data.get("proposals"):
        print("  (No pending proposals)")
    for p in data.get("proposals", []):
        print(f"[{p['id']}] {p['title']} -> Target: {p['target_skill']}")
        print(f"      Issue: {p['issue']}")
        print(f"      Solution: {p['solution']}")
    print("\n=== APPLIED LEARNINGS ===")
    if not data.get("applied"):
        print("  (No applied learnings)")
    for a in data.get("applied", []):
        print(f"[{a['id']}] {a['title']} -> Injected into: {a['target_skill']} on {a.get('applied_at')}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python learn_manager.py [propose|approve|list] [args...]")
        sys.exit(1)
        
    cmd = sys.argv[1].lower()
    if cmd == "propose":
        if len(sys.argv) < 7:
            print("Usage: python learn_manager.py propose <title> <issue> <root_cause> <solution> <target_skill>")
            sys.exit(1)
        p = propose_learning(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6])
    elif cmd == "approve":
        if len(sys.argv) < 3:
            print("Usage: python learn_manager.py approve <PROPOSAL_ID>")
            sys.exit(1)
        p = approve_learning(sys.argv[2])
        print(f"[SUCCESS] Approved and applied {p['id']}")
    elif cmd == "list":
        list_learnings()
