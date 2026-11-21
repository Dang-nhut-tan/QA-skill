"""
tests/test_validate_system.py
Verifies exit codes and failure handling in scripts/validate_system.py:
1. Normal run with operational tools returns exit code 0.
2. Missing CodeGraph returns exit code 1.
3. Missing Playwright returns exit code 1.
4. Tool command returning non-zero returns exit code 1.
"""

import sys
import os
import subprocess
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VALIDATE_SCRIPT = PROJECT_ROOT / "scripts" / "validate_system.py"


def test_validator_normal_run_returns_zero():
    """Case 1: When all architectural checks pass or warn, exit code must be 0."""
    res = subprocess.run(
        [sys.executable, str(VALIDATE_SCRIPT), "--compact"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT)
    )
    assert res.returncode == 0, f"Expected 0, got {res.returncode}. Output:\n{res.stdout}\n{res.stderr}"
    assert "[SUCCESS]" in res.stdout


def test_validator_missing_codegraph_returns_nonzero(tmp_path):
    """Case 2: When CodeGraph CLI is missing, exit code must be non-zero (1)."""
    # Create empty directory for PATH without codegraph
    env = os.environ.copy()
    # Strip any directory that has codegraph from PATH
    paths = env.get("PATH", "").split(os.pathsep)
    filtered_paths = [p for p in paths if not (Path(p) / "codegraph").exists() and not (Path(p) / "codegraph.cmd").exists() and not (Path(p) / "codegraph.exe").exists()]
    env["PATH"] = os.pathsep.join(filtered_paths)

    res = subprocess.run(
        [sys.executable, str(VALIDATE_SCRIPT), "--compact"],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
        env=env
    )
    assert "[FAILURE]" in res.stdout or "[BLOCKED]" in res.stdout
    assert res.returncode != 0, f"Validator returned 0 despite BLOCKED/FAIL! Output:\n{res.stdout}"


def test_validator_missing_playwright_returns_nonzero(tmp_path):
    """Case 3: When Playwright Test Runner is missing, exit code must be non-zero (1)."""
    env = os.environ.copy()
    paths = env.get("PATH", "").split(os.pathsep)
    filtered_paths = [
        p for p in paths 
        if not (Path(p) / "playwright").exists() 
        and not (Path(p) / "playwright.cmd").exists() 
        and not (Path(p) / "npx").exists() 
        and not (Path(p) / "npx.cmd").exists()
    ]
    env["PATH"] = os.pathsep.join(filtered_paths)

    res = subprocess.run(
        [sys.executable, str(VALIDATE_SCRIPT), "--compact"],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
        env=env
    )
    assert "[FAILURE]" in res.stdout or "[BLOCKED]" in res.stdout
    assert res.returncode != 0, f"Validator returned 0 despite Playwright missing! Output:\n{res.stdout}"


def test_validator_tool_command_nonzero_returns_nonzero(tmp_path):
    """Case 4: When a tool command exits non-zero, exit code must be non-zero (1)."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a failing mock for codegraph
    if sys.platform == "win32":
        mock_codegraph = bin_dir / "codegraph.cmd"
        mock_codegraph.write_text("@echo off\nexit /b 1\n", encoding="utf-8")
    else:
        mock_codegraph = bin_dir / "codegraph"
        mock_codegraph.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        mock_codegraph.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}{os.pathsep}{env.get('PATH', '')}"

    res = subprocess.run(
        [sys.executable, str(VALIDATE_SCRIPT), "--compact"],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
        env=env
    )
    assert "[FAILURE]" in res.stdout or "FAIL" in res.stdout
    assert res.returncode != 0, f"Validator returned 0 despite tool failure! Output:\n{res.stdout}"


def test_validate_skills_missing_canonical_skill_fails(tmp_path):
    """Task 5: When any of the 13 canonical skills is missing, validate_skill_metadata must FAIL."""
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    from validate_system import validate_skill_metadata, REQUIRED_CANONICAL_SKILLS
    
    # Create incomplete skills directory (e.g. only 12 skills)
    fake_skills = tmp_path / "skills"
    fake_skills.mkdir(parents=True, exist_ok=True)
    for sk in REQUIRED_CANONICAL_SKILLS[:-1]:
        sdir = fake_skills / sk
        sdir.mkdir()
        (sdir / "SKILL.md").write_text(f"---\nname: {sk}\ndescription: Test description\n---\nContent", encoding="utf-8")
        
    status, msg = validate_skill_metadata(skills_root=fake_skills)
    assert status == "FAIL"
    assert "Missing required canonical skill" in msg
    assert REQUIRED_CANONICAL_SKILLS[-1] in msg


def test_validate_skills_name_mismatch_fails(tmp_path):
    """Task 5: When directory name does not match frontmatter name, validator must FAIL."""
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    from validate_system import validate_skill_metadata, REQUIRED_CANONICAL_SKILLS
    
    fake_skills = tmp_path / "skills"
    fake_skills.mkdir(parents=True, exist_ok=True)
    for sk in REQUIRED_CANONICAL_SKILLS:
        sdir = fake_skills / sk
        sdir.mkdir()
        mismatched_name = f"{sk}-mismatched" if sk == REQUIRED_CANONICAL_SKILLS[0] else sk
        (sdir / "SKILL.md").write_text(f"---\nname: {mismatched_name}\ndescription: Test description\n---\nContent", encoding="utf-8")
        
    status, msg = validate_skill_metadata(skills_root=fake_skills)
    assert status == "FAIL"
    assert "does not match frontmatter name" in msg


def test_validate_skills_missing_description_fails(tmp_path):
    """Task 5: When description is missing or empty in frontmatter, validator must FAIL."""
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    from validate_system import validate_skill_metadata, REQUIRED_CANONICAL_SKILLS
    
    fake_skills = tmp_path / "skills"
    fake_skills.mkdir(parents=True, exist_ok=True)
    for sk in REQUIRED_CANONICAL_SKILLS:
        sdir = fake_skills / sk
        sdir.mkdir()
        desc = "" if sk == REQUIRED_CANONICAL_SKILLS[0] else "Valid description"
        (sdir / "SKILL.md").write_text(f"---\nname: {sk}\ndescription: {desc}\n---\nContent", encoding="utf-8")
        
    status, msg = validate_skill_metadata(skills_root=fake_skills)
    assert status == "FAIL"
    assert "missing or empty 'description'" in msg

