#!/usr/bin/env python3
"""
tests/test_codegraph_upgrades.py
Regression & Unit Test Suite for CodeGraph Upgrades in the QA Agent System:
- Group A: CodeGraph Preflight & Auto-Recovery
- Group B: Intelligent Method Discovery & Fallback
- Group C: Method Reusability Classification (DIRECT_REUSE, CONDITIONAL_REUSE, NOT_REUSABLE, NOT_FOUND)
- Group D: Progressive Context & Token Efficiency
"""

import os
import sys
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from scripts.codegraph_preflight import CodeGraphPreflight
from scripts.codegraph_discovery import MethodDiscoveryEngine

class TestCodeGraphUpgrades(unittest.TestCase):

    # =========================================================================
    # Group A: CodeGraph Preflight & Auto-Recovery
    # =========================================================================

    def test_preflight_cli_available(self):
        preflight = CodeGraphPreflight()
        has_cli, version = preflight.check_cli_available()
        self.assertTrue(has_cli, "codegraph CLI should be detected in the system")
        self.assertTrue(len(version) > 0, "CLI version string should not be empty")

    def test_preflight_invalid_repo(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            preflight = CodeGraphPreflight(Path(tmp_dir))
            is_valid, msg = preflight.check_repo_validity()
            self.assertFalse(is_valid, "Empty temp directory without project markers should be invalid")

    def test_preflight_valid_repo_markers(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            p = Path(tmp_dir)
            (p / "package.json").write_text("{}", encoding="utf-8")
            preflight = CodeGraphPreflight(p)
            is_valid, msg = preflight.check_repo_validity()
            self.assertTrue(is_valid, "Directory with package.json should be recognized as valid repository")

    def test_preflight_uninitialized_detection(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            p = Path(tmp_dir)
            (p / "package.json").write_text("{}", encoding="utf-8")
            preflight = CodeGraphPreflight(p)
            has_db, msg = preflight.check_db_initialized()
            self.assertFalse(has_db, "Uninitialized directory should report missing db")

    def test_preflight_db_corrupted_detection(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            p = Path(tmp_dir)
            (p / "package.json").write_text("{}", encoding="utf-8")
            cg_dir = p / ".codegraph"
            cg_dir.mkdir(parents=True, exist_ok=True)
            db_file = cg_dir / "codegraph.db"
            db_file.write_text("GARBAGE NOT A VALID SQLITE DB", encoding="utf-8")

            preflight = CodeGraphPreflight(p)
            is_healthy, msg, details = preflight.check_db_health()
            self.assertFalse(is_healthy, "Corrupted SQLite file must be reported as unhealthy")

    def test_preflight_healthy_db(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            p = Path(tmp_dir)
            (p / "package.json").write_text("{}", encoding="utf-8")
            cg_dir = p / ".codegraph"
            cg_dir.mkdir(parents=True, exist_ok=True)
            db_file = cg_dir / "codegraph.db"
            
            # Create minimal valid schema
            conn = sqlite3.connect(str(db_file))
            conn.execute("CREATE TABLE nodes (id TEXT PRIMARY KEY, name TEXT, kind TEXT, file_path TEXT, start_line INT, end_line INT, signature TEXT, docstring TEXT, is_exported INT)")
            conn.execute("CREATE TABLE edges (source_id TEXT, target_id TEXT, type TEXT)")
            conn.execute("CREATE TABLE files (path TEXT PRIMARY KEY, mtime REAL, hash TEXT)")
            conn.commit()
            conn.close()

            preflight = CodeGraphPreflight(p)
            is_healthy, msg, details = preflight.check_db_health()
            self.assertTrue(is_healthy, f"Valid SQLite schema should pass health check: {msg}")

    def test_preflight_real_thaihao(self):
        thaihao_path = Path("C:/intern/thaihao")
        if thaihao_path.exists():
            preflight = CodeGraphPreflight(thaihao_path)
            res = preflight.run_preflight(auto_init=False)
            self.assertEqual(res["status"], "READY", "Thaihao repository must pass all preflight checks")
            self.assertGreater(res["checks"]["db_healthy"]["node_count"], 1000)

    # =========================================================================
    # Group B: Intelligent Method Discovery & Fallback
    # =========================================================================

    def test_discovery_class_method_fallback(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            p = Path(tmp_dir)
            pages_dir = p / "tests" / "pages"
            pages_dir.mkdir(parents=True, exist_ok=True)
            
            sample_page = pages_dir / "SamplePage.mjs"
            sample_page.write_text("""
export class SamplePage {
    async submitOrder(orderId) {
        await this.page.click('#submit-btn');
    }
}
""", encoding="utf-8")

            engine = MethodDiscoveryEngine(p)
            cands = engine.discover_candidates("submitOrder")
            engine.close()
            
            self.assertEqual(len(cands), 1)
            self.assertEqual(cands[0]["name"], "submitOrder")
            self.assertEqual(cands[0]["kind"], "method/function")

    def test_discovery_arrow_function_fallback(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            p = Path(tmp_dir)
            pages_dir = p / "04-src" / "tests" / "pages"
            pages_dir.mkdir(parents=True, exist_ok=True)
            
            sample_file = pages_dir / "authHelper.js"
            sample_file.write_text("""
export const loginWithToken = async (token) => {
    return true;
};
""", encoding="utf-8")

            engine = MethodDiscoveryEngine(p)
            cands = engine.discover_candidates("loginWithToken")
            engine.close()

            self.assertEqual(len(cands), 1)
            self.assertEqual(cands[0]["name"], "loginWithToken")

    def test_discovery_nested_object_methods(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            p = Path(tmp_dir)
            pages_dir = p / "page-objects"
            pages_dir.mkdir(parents=True, exist_ok=True)
            
            sample_file = pages_dir / "basketService.ts"
            sample_file.write_text("""
export const basket = {
    add(item: any): boolean {
        return true;
    },
    remove(id: string): void {
        return;
    }
};
""", encoding="utf-8")

            engine = MethodDiscoveryEngine(p)
            cands = engine.discover_candidates("add")
            engine.close()

            self.assertEqual(len(cands), 1)
            self.assertEqual(cands[0]["name"], "add")

    # =========================================================================
    # Group C: Method Reusability Classification
    # =========================================================================

    def test_classification_direct_reuse(self):
        engine = MethodDiscoveryEngine(Path("."))
        cand = {
            "name": "login",
            "file_path": "tests/pages/LoginPage.js",
            "start_line": 10,
            "end_line": 20,
            "signature": "(username, password)",
            "kind": "method"
        }
        res, reason = engine.classify_reusability("login", cand)
        self.assertEqual(res, "DIRECT_REUSE")

    def test_classification_conditional_reuse(self):
        engine = MethodDiscoveryEngine(Path("."))
        cand = {
            "name": "loginWithSso",
            "file_path": "tests/pages/LoginPage.js",
            "start_line": 25,
            "end_line": 35,
            "signature": "(provider, options)",
            "kind": "method"
        }
        res, reason = engine.classify_reusability("login", cand)
        self.assertEqual(res, "CONDITIONAL_REUSE")

    def test_classification_not_reusable_internal(self):
        engine = MethodDiscoveryEngine(Path("."))
        cand = {
            "name": "_internalInitSession",
            "file_path": "tests/pages/LoginPage.js",
            "start_line": 5,
            "end_line": 8,
            "signature": "()",
            "kind": "method"
        }
        res, reason = engine.classify_reusability("InitSession", cand)
        self.assertEqual(res, "NOT_REUSABLE")

    def test_classification_not_found(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            p = Path(tmp_dir)
            engine = MethodDiscoveryEngine(p)
            res = engine.discover_and_evaluate("completelyNonExistentMethod12345")
            engine.close()
            self.assertEqual(res["classification"], "NOT_FOUND")

    # =========================================================================
    # Group D: Progressive Context & Token Efficiency
    # =========================================================================

    def test_progressive_context_hierarchy(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            p = Path(tmp_dir)
            src_dir = p / "src"
            src_dir.mkdir(parents=True, exist_ok=True)
            code_file = src_dir / "calculator.ts"
            code_file.write_text("""
// Complex implementation
export function calculateTax(amount: number, rate: number): number {
    if (amount <= 0) return 0;
    const base = amount * rate;
    const surcharge = base > 1000 ? base * 0.05 : 0;
    return base + surcharge;
}
""", encoding="utf-8")

            cand = {
                "name": "calculateTax",
                "file_path": "src/calculator.ts",
                "start_line": 3,
                "end_line": 8,
                "signature": "(amount: number, rate: number): number",
                "kind": "function"
            }

            engine = MethodDiscoveryEngine(p)
            ctx = engine.get_progressive_context(cand, target_level=4)
            engine.close()

            # Level 1-4 hierarchy verification
            self.assertEqual(ctx["name"], "calculateTax")
            self.assertIn("amount", ctx["signature"])
            self.assertIn("surcharge", ctx["implementation"])
            
            # Token/character count efficiency check: Signature vs Full Implementation
            sig_len = len(ctx["signature"])
            impl_len = len(ctx["implementation"])
            self.assertLess(sig_len, impl_len, "Signature (L2) must be significantly smaller than implementation (L4)")

    def test_token_reduction_comparison(self):
        thaihao_path = Path("C:/intern/thaihao")
        if thaihao_path.exists():
            engine = MethodDiscoveryEngine(thaihao_path)
            res = engine.discover_and_evaluate("basket", scope_hint="quote-basket")
            engine.close()
            
            ctx = res["progressive_context"]
            cand = res["candidate"]
            
            full_file_path = thaihao_path / cand["file_path"]
            full_file_text = full_file_path.read_text(encoding="utf-8")
            
            sig_text = ctx["signature"]
            
            full_tokens_est = len(full_file_text) // 4
            sig_tokens_est = len(sig_text) // 4
            savings_pct = (full_tokens_est - sig_tokens_est) / full_tokens_est * 100
            
            self.assertGreater(savings_pct, 60.0, "Progressive signature retrieval must achieve > 60% token reduction over full file")

if __name__ == "__main__":
    unittest.main()
