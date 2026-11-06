#!/usr/bin/env python3
"""
scripts/generate_template.py
Generates an executive-ready, beautifully styled Excel test case template for the QA Agent System.
Consolidated backward-compatible wrapper delegating to export_testcases.build_template.
"""

import sys
from pathlib import Path

# Dynamic sys.path fallback for safe invocation
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

try:
    from export_testcases import build_template
except ImportError:
    try:
        from scripts.export_testcases import build_template
    except ImportError:
        raise ImportError("Cannot import build_template from export_testcases")

if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "templates" / "testcase-template.xlsx"
    if len(sys.argv) > 1:
        out = Path(sys.argv[1])
    build_template(out)
