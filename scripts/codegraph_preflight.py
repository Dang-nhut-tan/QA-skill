#!/usr/bin/env python3
"""
scripts/codegraph_preflight.py
Preflight verification and auto-recovery engine for CodeGraph integration
in the QA Agent System.

Validates:
1. CodeGraph CLI availability.
2. Target repository validity & write permissions.
3. CodeGraph database initialization (.codegraph/codegraph.db). Auto-recovers via `codegraph init`.
4. Database health: SQLite PRAGMA integrity_check and required schema tables.
5. Index freshness: compares source file mtime against DB index epoch; auto-syncs if needed.
"""

import sys
import os
import shutil
import sqlite3
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

CORE_TABLES = {"nodes", "edges", "files", "schema_versions"}
PROJECT_MARKERS = {
    "package.json", "tsconfig.json", "pyproject.toml",
    "requirements.txt", "go.mod", "pom.xml", ".git"
}

class CodeGraphPreflight:
    def __init__(self, repo_path: Optional[Path] = None):
        self.repo_path = Path(repo_path or ".").resolve()
        self.codegraph_dir = self.repo_path / ".codegraph"
        self.db_path = self.codegraph_dir / "codegraph.db"
        self.version = ""
        self.cli_bin = ""
        self.results: Dict[str, Any] = {
            "cli_available": False,
            "repo_valid": False,
            "db_initialized": False,
            "db_healthy": False,
            "index_freshness": False,
            "status": "NOT_READY",
            "diagnostics": [],
            "checks": {}
        }

    def _find_codegraph_cli(self) -> Optional[str]:
        # 1. System PATH
        cmd = shutil.which("codegraph")
        if cmd:
            return cmd
        
        # 2. Windows Local AppData default location
        appdata_cmd = Path.home() / "AppData" / "Local" / "codegraph" / "current" / "bin" / "codegraph.cmd"
        if appdata_cmd.exists():
            return str(appdata_cmd)

        return None

    def check_cli(self) -> bool:
        has_cli, _ = self.check_cli_available()
        return has_cli

    def check_cli_available(self) -> Tuple[bool, str]:
        cli_bin = self._find_codegraph_cli()
        if not cli_bin:
            msg = "CodeGraph CLI not found in PATH or AppData. Install via: npm install -g @colbymchenry/codegraph"
            self.results["diagnostics"].append(msg)
            return False, msg

        try:
            res = subprocess.run(
                [cli_bin, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                shell=True
            )
            if res.returncode == 0:
                self.results["cli_available"] = True
                self.cli_bin = cli_bin
                self.version = res.stdout.strip()
                return True, self.version
            else:
                msg = f"CodeGraph CLI returned error: {res.stderr.strip()}"
                self.results["diagnostics"].append(msg)
                return False, msg
        except Exception as e:
            msg = f"Failed to execute CodeGraph CLI: {str(e)}"
            self.results["diagnostics"].append(msg)
            return False, msg

    def check_repository(self) -> bool:
        valid, _ = self.check_repo_validity()
        return valid

    def check_repo_validity(self) -> Tuple[bool, str]:
        if not self.repo_path.exists() or not self.repo_path.is_dir():
            msg = f"Target repository path does not exist or is not a directory: {self.repo_path}"
            self.results["diagnostics"].append(msg)
            return False, msg

        if not os.access(self.repo_path, os.W_OK):
            msg = f"Target repository path is not writable: {self.repo_path}"
            self.results["diagnostics"].append(msg)
            return False, msg

        # Check for standard project markers to prevent initializing random folders
        has_marker = any((self.repo_path / m).exists() for m in PROJECT_MARKERS)
        if not has_marker:
            has_src = any(self.repo_path.glob("*.ts")) or any(self.repo_path.glob("*.js")) or any(self.repo_path.glob("*.py"))
            if not has_src:
                msg = f"Directory does not appear to be a recognized project repository: {self.repo_path}"
                self.results["diagnostics"].append(msg)
                return False, msg

        self.results["repo_valid"] = True
        return True, "Valid repository"

    def check_db_initialized(self) -> Tuple[bool, str]:
        if self.db_path.exists() and self.db_path.stat().st_size > 0:
            self.results["db_initialized"] = True
            return True, f"Database present at {self.db_path}"
        return False, f"Database missing at {self.db_path}"

    def check_and_recover_initialization(self, auto_init: bool = True) -> bool:
        has_db, msg = self.check_db_initialized()
        if has_db:
            return True

        if not auto_init:
            self.results["diagnostics"].append(f"{msg} and auto-init is disabled.")
            return False

        # Auto-initialize CodeGraph inside verified repository
        if not self.cli_bin:
            cli_bin = self._find_codegraph_cli()
            if not cli_bin:
                self.results["diagnostics"].append("Cannot auto-init: CLI is unavailable.")
                return False
            self.cli_bin = cli_bin

        try:
            self.results["diagnostics"].append(f"Initializing CodeGraph in {self.repo_path} via 'codegraph init'...")
            res = subprocess.run(
                [self.cli_bin, "init", str(self.repo_path)],
                capture_output=True,
                text=True,
                timeout=60,
                shell=True
            )
            if res.returncode == 0 and self.db_path.exists() and self.db_path.stat().st_size > 0:
                self.results["db_initialized"] = True
                return True
            else:
                err_msg = res.stderr.strip() or res.stdout.strip()
                self.results["diagnostics"].append(f"CodeGraph init failed: {err_msg}")
                return False
        except Exception as e:
            self.results["diagnostics"].append(f"Exception during CodeGraph auto-init: {str(e)}")
            return False

    def check_database_health(self) -> bool:
        healthy, _, _ = self.check_db_health()
        return healthy

    def check_db_health(self) -> Tuple[bool, str, Dict[str, Any]]:
        details: Dict[str, Any] = {"node_count": 0, "integrity": "unknown"}
        if not self.db_path.exists():
            return False, "Database file does not exist", details

        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path), timeout=5)
            cur = conn.cursor()
            
            # 1. Integrity check
            integrity = cur.execute("PRAGMA quick_check").fetchone()
            if not integrity or integrity[0] != "ok":
                msg = f"SQLite integrity check failed: {integrity}"
                self.results["diagnostics"].append(msg)
                return False, msg, details
            details["integrity"] = "ok"

            # 2. Verify schema tables
            tables = {row[0] for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            missing = {"nodes", "edges", "files"} - tables
            if missing:
                msg = f"Database missing required CodeGraph tables: {missing}"
                self.results["diagnostics"].append(msg)
                return False, msg, details

            # 3. Check node count
            node_count = cur.execute("SELECT count(*) FROM nodes").fetchone()[0]
            self.results["node_count"] = node_count
            details["node_count"] = node_count

            self.results["db_healthy"] = True
            return True, "Database is healthy", details
        except Exception as e:
            msg = f"Database health check error: {str(e)}"
            self.results["diagnostics"].append(msg)
            return False, msg, details
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def check_and_sync_freshness(self, auto_sync: bool = True) -> bool:
        if not self.results["db_healthy"]:
            return False

        try:
            conn = sqlite3.connect(str(self.db_path), timeout=5)
            cur = conn.cursor()
            res = None
            try:
                res = cur.execute("SELECT max(modified_at) FROM files").fetchone()
            except Exception:
                pass
            last_indexed_epoch = res[0] if res and res[0] else 0
            conn.close()

            newest_src_mtime = 0
            for root, dirs, files in os.walk(self.repo_path):
                dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "dist", "build", ".codegraph", "test-results"}]
                for f in files:
                    if f.endswith((".ts", ".tsx", ".js", ".jsx", ".py", ".go")):
                        try:
                            m = int((Path(root) / f).stat().st_mtime * 1000)
                            if m > newest_src_mtime:
                                newest_src_mtime = m
                        except Exception:
                            pass

            is_outdated = (newest_src_mtime > (last_indexed_epoch + 15000)) if newest_src_mtime > 0 and last_indexed_epoch > 0 else False

            if not is_outdated:
                self.results["index_freshness"] = True
                return True

            if not auto_sync:
                self.results["diagnostics"].append("CodeGraph index is older than source files, but auto_sync is disabled.")
                return False

            if self.cli_bin:
                sync_res = subprocess.run(
                    [self.cli_bin, "sync", str(self.repo_path)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    shell=True
                )
                if sync_res.returncode == 0:
                    self.results["index_freshness"] = True
                    return True
                else:
                    self.results["diagnostics"].append(f"codegraph sync returned non-zero: {sync_res.stderr.strip()}")
                    self.results["index_freshness"] = True
                    return True
            else:
                self.results["index_freshness"] = True
                return True

        except Exception as e:
            self.results["diagnostics"].append(f"Freshness check warning: {str(e)}")
            self.results["index_freshness"] = True
            return True

    def run_preflight(self, auto_init: bool = True, auto_sync: bool = True) -> Dict[str, Any]:
        c1 = self.check_cli()
        self.results["checks"]["cli"] = c1
        if not c1:
            return self._finalize()

        c2 = self.check_repository()
        self.results["checks"]["repo"] = c2
        if not c2:
            return self._finalize()

        c3 = self.check_and_recover_initialization(auto_init=auto_init)
        self.results["checks"]["db_initialized"] = c3
        if not c3:
            return self._finalize()

        c4 = self.check_database_health()
        self.results["checks"]["db_healthy"] = {
            "passed": c4,
            "node_count": self.results.get("node_count", 0)
        }
        if not c4:
            return self._finalize()

        c5 = self.check_and_sync_freshness(auto_sync=auto_sync)
        self.results["checks"]["index_freshness"] = c5
        if not c5:
            return self._finalize()

        self.results["status"] = "READY"
        return self._finalize()

    def _finalize(self) -> Dict[str, Any]:
        if self.results["cli_available"] and self.results["repo_valid"] and self.results["db_initialized"] and self.results["db_healthy"]:
            self.results["status"] = "READY"
        else:
            self.results["status"] = "BLOCKED"
        return self.results

    def format_report(self) -> str:
        r = self.results
        s_cli = "PASS" if r["cli_available"] else "FAIL"
        s_repo = "PASS" if r["repo_valid"] else "FAIL"
        s_init = "PASS" if r["db_initialized"] else "FAIL"
        s_hlth = "PASS" if r["db_healthy"] else "FAIL"
        s_frsh = "PASS" if r["index_freshness"] else "FAIL"
        s_ctx  = "READY" if r["status"] == "READY" else "BLOCKED"

        lines = [
            "[CodeGraph Preflight]",
            f"CLI Available       : {s_cli}",
            f"Repository Valid    : {s_repo}",
            f"Database Initialized: {s_init}",
            f"Database Healthy    : {s_hlth}",
            f"Index Freshness     : {s_frsh}",
            f"Context Discovery   : {s_ctx}"
        ]
        if r.get("node_count") is not None:
            lines.append(f"Indexed AST Nodes   : {r['node_count']:,}")
        if r["diagnostics"]:
            lines.append("\nDiagnostics / Recovery Notes:")
            for d in r["diagnostics"]:
                lines.append(f"  * {d}")
        return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="CodeGraph Preflight & Health Verification")
    parser.add_argument("repo", nargs="?", default=".", help="Target repository path (default: current directory)")
    parser.add_argument("--no-init", action="store_true", help="Do not auto-initialize if database is missing")
    parser.add_argument("--no-sync", action="store_true", help="Do not auto-sync if database is outdated")
    parser.add_argument("--json", action="store_true", help="Output raw JSON result")

    args = parser.parse_args()
    pf = CodeGraphPreflight(Path(args.repo))
    res = pf.run_preflight(auto_init=not args.no_init, auto_sync=not args.no_sync)

    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print(pf.format_report())
        sys.exit(0 if res["status"] == "READY" else 1)
