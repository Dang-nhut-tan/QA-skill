#!/usr/bin/env python3
"""
scripts/verify_and_embed_images.py
Ensures that all visual proof images referenced in BA clarification tickets (<module>-gaps.md)
physically exist on disk, are non-empty, and are formatted with a multi-viewer failsafe pattern
(Relative Markdown path + Clickable absolute file:// URI).
"""

import sys
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

IMAGE_REGEX = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')

def verify_and_fix_report_images(
    report_path: Path,
    project_root: Path,
    auto_fix_links: bool = True
) -> Dict[str, Any]:
    """
    Verifies that all images in report_path exist in project_root.
    Optionally updates the markdown file to include clickable absolute links
    as a fail-safe fallback for all IDEs and Markdown previewers.
    """
    if not report_path.exists():
        return {"success": False, "error": f"Report file not found: {report_path}"}

    content = report_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    
    missing_images: List[Dict[str, Any]] = []
    found_images: List[Dict[str, Any]] = []
    modified = False

    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        match = IMAGE_REGEX.search(line)
        if match:
            caption = match.group(1)
            raw_path = match.group(2).strip()
            
            # Clean possible query or fragments
            clean_rel = raw_path.split("?")[0].split("#")[0].strip()
            # Normalize path (convert forward/backslashes)
            normalized_rel = clean_rel.replace("\\", "/")
            if normalized_rel.startswith("./"):
                test_rel = normalized_rel[2:]
            elif normalized_rel.startswith("/"):
                test_rel = normalized_rel[1:]
            else:
                test_rel = normalized_rel

            # Resolve absolute path relative to project root or report dir
            candidate_p1 = (project_root / test_rel).resolve()
            candidate_p2 = (report_path.parent / test_rel).resolve()
            
            actual_file: Path = None
            if candidate_p1.is_file() and candidate_p1.stat().st_size > 0:
                actual_file = candidate_p1
            elif candidate_p2.is_file() and candidate_p2.stat().st_size > 0:
                actual_file = candidate_p2

            if not actual_file:
                missing_images.append({
                    "line": i + 1,
                    "caption": caption,
                    "referenced_path": raw_path,
                    "checked_paths": [str(candidate_p1), str(candidate_p2)]
                })
                new_lines.append(line)
            else:
                found_images.append({
                    "line": i + 1,
                    "caption": caption,
                    "file_path": str(actual_file),
                    "size_bytes": actual_file.stat().st_size
                })
                
                # Check if next line already has a clickable file URI
                posix_abs = actual_file.as_posix()
                file_uri = f"file:///{posix_abs}" if not posix_abs.startswith("/") else f"file://{posix_abs}"
                fallback_line = f"  *([Mở ảnh gốc: {test_rel}]({file_uri}))*"
                
                new_lines.append(line)
                
                # Check if next line is already our link
                has_link = False
                if i + 1 < len(lines) and "file:///" in lines[i + 1]:
                    has_link = True
                
                if auto_fix_links and not has_link:
                    new_lines.append(fallback_line)
                    modified = True
        else:
            new_lines.append(line)
        i += 1

    if auto_fix_links and modified:
        report_path.write_text("\n".join(new_lines), encoding="utf-8")

    return {
        "success": len(missing_images) == 0,
        "total_images": len(found_images) + len(missing_images),
        "found_images": found_images,
        "missing_images": missing_images,
        "report_modified": modified
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Verify and normalize image references in BA gap reports.")
    parser.add_argument("report", help="Path to <module>-gaps.md file")
    parser.add_argument("--root", help="Project root directory (defaults to report parent)")
    parser.add_argument("--no-fix", action="store_true", help="Do not inject fallback clickable links")

    args = parser.parse_args()
    rep_p = Path(args.report).resolve()
    root_p = Path(args.root).resolve() if args.root else rep_p.parent

    res = verify_and_fix_report_images(rep_p, root_p, auto_fix_links=not args.no_fix)
    
    if not res["success"]:
        print(f"[FAIL] Missing {len(res['missing_images'])} physical screenshot files in {rep_p.name}:", file=sys.stderr)
        for m in res["missing_images"]:
            print(f"  - Dòng {m['line']}: '{m['referenced_path']}' -> Không tìm thấy tệp trên ổ đĩa!", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"[OK] 100% Verified {res['total_images']} screenshots in {rep_p.name} exist on disk.")
        if res["report_modified"]:
            print(f"[UPDATED] Injected dual-mode clickable fallback links into {rep_p.name}")
        sys.exit(0)
