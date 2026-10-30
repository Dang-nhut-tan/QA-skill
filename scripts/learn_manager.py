#!/usr/bin/env python3
"""
scripts/learn_manager.py
Manages dynamic knowledge capture, continuous learning, and human-approved skill augmentation.
Detects recurring errors or framework quirks, formulates proposals,
and appends approved insights into target SKILL.md files within verified project roots.
Protects against path traversal and prohibits silent global plugin overwrites.
"""

import sys
import os
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

SYSTEM_ROOT = Path(__file__).resolve().parent.parent

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def resolve_skills_root(explicit_root: Optional[str] = None) -> Path:
    """
    Resolves the skills directory where project learnings should be saved.
    Priority order:
    1. Explicit root (--project-root or QA_PROJECT_ROOT env var).
    2. Candidate layout <root>/.agent/skills/ (embedded project mode).
    3. Candidate layout <root>/skills/ (verified QA Skill development repo mode).
    Never writes to global plugin directory unless explicitly verified.
    """
    root_str = explicit_root or os.environ.get("QA_PROJECT_ROOT")
    
    # Mode 1: Explicit root provided
    if root_str:
        p_root = Path(root_str).resolve()
        embedded_skills = p_root / ".agent" / "skills"
        if embedded_skills.is_dir():
            return embedded_skills
        
        # Check if verified QA skill repo
        repo_skills = p_root / "skills"
        is_verified_repo = (
            repo_skills.is_dir() and
            (p_root / "plugin.json").exists() and
            (p_root / "scripts" / "learn_manager.py").exists()
        )
        if is_verified_repo:
            return repo_skills
            
        raise RuntimeError(
            f"Explicit project root '{root_str}' does not have a valid skills layout "
            f"(.agent/skills/ or verified QA Skill repo with skills/). Aborting to prevent corrupting external files."
        )

    # Mode 2: Auto-detect upward from current working directory
    cur = Path.cwd().resolve()
    candidates = [cur, *cur.parents]
    
    for c in candidates:
        embedded = c / ".agent" / "skills"
        if embedded.is_dir():
            return embedded

    for c in candidates:
        repo_skills = c / "skills"
        if (
            repo_skills.is_dir() and
            (c / "plugin.json").exists() and
            (c / "scripts" / "learn_manager.py").exists()
        ):
            return repo_skills

    raise RuntimeError(
        "Could not detect a valid project root containing '.agent/skills' or a verified QA Skill repository. "
        "Please specify --project-root <path> or set the QA_PROJECT_ROOT environment variable."
    )

def get_learnings_file(skills_root: Optional[Path] = None) -> Path:
    if skills_root:
        # Determine parent references dir
        ref_dir = skills_root.parent / "references"
        ref_dir.mkdir(parents=True, exist_ok=True)
        return ref_dir / "project-learnings.json"
    return SYSTEM_ROOT / "references" / "project-learnings.json"

def load_learnings(learnings_file: Optional[Path] = None) -> Dict[str, Any]:
    l_file = learnings_file or get_learnings_file()
    if not l_file.exists():
        return {"proposals": [], "applied": []}
    try:
        with open(l_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"proposals": [], "applied": []}

def save_learnings(data: Dict[str, Any], learnings_file: Optional[Path] = None) -> None:
    l_file = learnings_file or get_learnings_file()
    l_file.parent.mkdir(parents=True, exist_ok=True)
    # Atomic write to prevent file corruption during parallel execution
    tmp_file = l_file.with_name(f"{l_file.name}.tmp")
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp_file, l_file)

def propose_learning(title: str, issue: str, root_cause: str, solution: str, target_skill: str, module: Optional[str] = None, tags: Optional[List[str]] = None, project_root: Optional[str] = None) -> Dict[str, Any]:
    skills_root = resolve_skills_root(project_root)
    learnings_file = get_learnings_file(skills_root)
    
    data = load_learnings(learnings_file)
    proposal_id = f"LRN-{len(data.get('proposals', [])) + len(data.get('applied', [])) + 1:03d}"
    
    proposal = {
        "id": proposal_id,
        "title": title,
        "module": module or "General",
        "tags": tags or [],
        "issue": issue,
        "root_cause": root_cause,
        "solution": solution,
        "target_skill": target_skill,
        "status": "PENDING_APPROVAL",
        "active": True,
        "created_at": _now()
    }
    
    data.setdefault("proposals", []).append(proposal)
    save_learnings(data, learnings_file)
    print(f"[PROPOSED] Created proposal {proposal_id}: {title} (Saved in {learnings_file})")
    return proposal

def approve_learning(proposal_id: str, project_root: Optional[str] = None) -> Dict[str, Any]:
    skills_root = resolve_skills_root(project_root)
    learnings_file = get_learnings_file(skills_root)
    
    data = load_learnings(learnings_file)
    proposal = None
    for p in data.get("proposals", []):
        if p["id"] == proposal_id:
            proposal = p
            break
            
    if not proposal:
        raise ValueError(f"Proposal {proposal_id} not found in {learnings_file}.")
        
    target_skill_name = proposal["target_skill"].strip()
    
    # Path Traversal Guard: Skill name must be strictly alphanumeric with hyphens/underscores
    if not re.match(r'^[A-Za-z0-9_-]+$', target_skill_name):
        raise ValueError(f"Invalid target skill name '{target_skill_name}'. Path traversal rejected.")

    skill_file = (skills_root / target_skill_name / "SKILL.md").resolve()
    
    # Verify skill_file is strictly within skills_root
    try:
        skill_file.relative_to(skills_root)
    except ValueError:
        raise PermissionError(f"Path traversal detected: target '{skill_file}' escapes skills root '{skills_root}'.")

    if not skill_file.exists():
        raise FileNotFoundError(f"Target skill file '{skill_file}' does not exist.")

    # ARCHITECTURAL DECISION: Prevent Token Bloat in SKILL.md
    # Instead of unbounded append into SKILL.md system prompt, learnings are stored structured
    # in references/project-learnings.json and retrieved dynamically per module context.
    data["proposals"].remove(proposal)
    proposal["status"] = "APPLIED"
    proposal["active"] = True
    proposal["applied_at"] = _now()
    data.setdefault("applied", []).append(proposal)
    save_learnings(data, learnings_file)
    print(f"[OK] Learning {proposal_id} approved and persisted in {learnings_file} (SKILL.md kept clean).")
    
    return proposal

def reject_learning(proposal_id: str, reason: str = "", project_root: Optional[str] = None) -> Dict[str, Any]:
    skills_root = resolve_skills_root(project_root)
    learnings_file = get_learnings_file(skills_root)
    
    data = load_learnings(learnings_file)
    proposal = None
    for p in data.get("proposals", []):
        if p["id"] == proposal_id:
            proposal = p
            break
            
    if not proposal:
        raise ValueError(f"Proposal {proposal_id} not found in {learnings_file}.")

    data["proposals"].remove(proposal)
    proposal["status"] = "REJECTED"
    proposal["active"] = False
    proposal["rejected_at"] = _now()
    if reason:
        proposal["reject_reason"] = reason
    data.setdefault("rejected", []).append(proposal)
    save_learnings(data, learnings_file)
    print(f"[REJECTED] Learning proposal {proposal_id} marked as REJECTED in {learnings_file}.")
    return proposal

def query_learnings(module_name: Optional[str] = None, target_skill: Optional[str] = None, limit: int = 3, project_root: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Dynamic Context Injection: Retrieves top active learnings relevant to the target module and skill.
    Injected on-demand into prompt context without polluting static SKILL.md files.
    """
    try:
        skills_root = resolve_skills_root(project_root)
        learnings_file = get_learnings_file(skills_root)
    except Exception:
        learnings_file = get_learnings_file()

    data = load_learnings(learnings_file)
    applied = data.get("applied", [])

    matching = []
    mod_clean = (module_name or "").strip().lower()
    skill_clean = (target_skill or "").strip().lower()

    for item in applied:
        if not item.get("active", True):
            continue
        # Filter by target_skill if specified
        if skill_clean:
            item_skill = str(item.get("target_skill", "")).strip().lower()
            if item_skill != skill_clean:
                continue
        # Filter by module_name if specified
        item_mod = str(item.get("module", "")).lower()
        if mod_clean and (item_mod == mod_clean or mod_clean in item_mod):
            matching.append(item)
        elif not mod_clean or item_mod == "general":
            matching.append(item)

    # Return top 'limit' matches
    return matching[:limit]

def list_learnings(as_json: bool = False, project_root: Optional[str] = None) -> None:
    try:
        skills_root = resolve_skills_root(project_root)
        learnings_file = get_learnings_file(skills_root)
    except Exception:
        learnings_file = get_learnings_file()

    data = load_learnings(learnings_file)
    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    props = data.get("proposals", [])
    apps = data.get("applied", [])
    print(f"[LEARNINGS from {learnings_file}] Pending: {len(props)} | Applied: {len(apps)}")
    if props:
        print("\nPending Proposals:")
        for p in props:
            print(f"  - [{p['id']}] {p['title']} (Target: {p['target_skill']})")
    if apps:
        print("\nApplied Learnings:")
        for a in apps:
            print(f"  - [{a['id']}] {a['title']} -> {a['target_skill']}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Continuous Learning Manager for QA Agent System")
    parser.add_argument("action", choices=["propose", "approve", "reject", "list", "query"], help="Action to execute")
    parser.add_argument("--module", dest="module", default=None, help="Target module name for propose or query")
    parser.add_argument("--skill", dest="skill", default=None, help="Target skill name to filter learnings")
    parser.add_argument("--limit", dest="limit", type=int, default=3, help="Max results for query action")
    parser.add_argument("args", nargs="*", help="Arguments for the selected action")
    parser.add_argument("--project-root", dest="project_root", default=None, help="Explicit target project root path")
    parser.add_argument("--json", action="store_true", help="Output in JSON format (for list action)")
    
    parsed = parser.parse_args()
    
    if parsed.action == "propose":
        if len(parsed.args) < 5:
            print("Usage: python learn_manager.py propose <title> <issue> <root_cause> <solution> <target_skill> [--project-root <path>]")
            sys.exit(1)
        p = propose_learning(parsed.args[0], parsed.args[1], parsed.args[2], parsed.args[3], parsed.args[4], module=parsed.module, project_root=parsed.project_root)
    elif parsed.action == "approve":
        if len(parsed.args) < 1:
            print("Usage: python learn_manager.py approve <PROPOSAL_ID> [--project-root <path>]")
            sys.exit(1)
        p = approve_learning(parsed.args[0], project_root=parsed.project_root)
        print(f"[SUCCESS] Approved and applied {p['id']}")
    elif parsed.action == "reject":
        if len(parsed.args) < 1:
            print("Usage: python learn_manager.py reject <PROPOSAL_ID> [reason] [--project-root <path>]")
            sys.exit(1)
        reason = parsed.args[1] if len(parsed.args) > 1 else ""
        p = reject_learning(parsed.args[0], reason=reason, project_root=parsed.project_root)
        print(f"[SUCCESS] Rejected {p['id']}")
    elif parsed.action == "list":
        list_learnings(as_json=parsed.json, project_root=parsed.project_root)
    elif parsed.action == "query":
        res = query_learnings(module_name=parsed.module, target_skill=parsed.skill, limit=parsed.limit, project_root=parsed.project_root)
        if parsed.json:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            print(f"[RELEVANT LEARNINGS for module '{parsed.module or 'All'}']: {len(res)} items")
            for r in res:
                print(f"  - [{r['id']}] {r['title']}: {r['solution']}")
