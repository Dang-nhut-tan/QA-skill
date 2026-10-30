#!/usr/bin/env python3
"""
tests/test_adaptive_level4.py
Comprehensive unit test suite for Adaptive Level 4 JIT Engine and Multi-Module State Namespace.
"""

import os
import sys
import tempfile
import sqlite3
import pytest
from pathlib import Path

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from scripts.codegraph_discovery import (
    evaluate_spec_completeness,
    MethodDiscoveryEngine
)
from scripts.state_manager import (
    WorkflowStateManager,
    _resolve_state_file,
    STATE_FILE_NAME
)


class TestSpecificationCompletenessMatrix:
    """Tests for evaluate_spec_completeness heuristics."""

    def test_spec_completeness_matrix_detects_gherkin_en(self):
        gherkin_en = """
        Scenario: Block checkin outside corporate network
          Given employee is authenticated
          When employee checks in from IP "198.51.100.1"
          Then system rejects with error "INVALID_IP"
        """
        assert evaluate_spec_completeness(gherkin_en) is True

    def test_spec_completeness_matrix_detects_gherkin_vi(self):
        gherkin_vi = """
        Kịch bản: Chấm công nhân viên ca đêm
          Giả sử nhân viên đã đăng nhập thành công vào hệ thống
          Khi nhân viên quẹt thẻ vào lúc 23:55
          Thì hệ thống tự động ghi nhận công ca đêm và tính hệ số 1.5
        """
        assert evaluate_spec_completeness(gherkin_vi) is True

    def test_spec_completeness_matrix_detects_vague_greeting(self):
        greeting_65_words = """
        Chào đội dự án, tôi là An, BA mới phụ trách phân hệ Chấm công.
        Hôm nay tôi gửi tài liệu này để các bạn nắm được sơ bộ về màn hình quẹt thẻ.
        Mong các bạn hỗ trợ kiểm thử tính năng quẹt thẻ của nhân viên văn phòng trong sprint này.
        Nếu có gì chưa rõ xin liên hệ lại tôi qua Slack. Cảm ơn các bạn rất nhiều và chúc mọi người làm việc hiệu quả.
        """
        assert evaluate_spec_completeness(greeting_65_words) is False

    def test_spec_completeness_matrix_detects_empty_or_short(self):
        assert evaluate_spec_completeness("") is False
        assert evaluate_spec_completeness("Tính năng chấm công") is False

    def test_spec_completeness_matrix_detects_structured_ac_with_numbers(self):
        ac_spec = """
        Chức năng: Tính phạt đi muộn
        Tiêu chí nghiệm thu:
        - Đi muộn dưới hoặc bằng 15 phút (<= 15 phút): miễn phạt.
        - Đi muộn từ phút thứ 16 đến 60 phút: phạt 50.000 VNĐ.
        - Đi muộn trên 60 phút: tính nửa ngày công nghỉ không phép.
        """
        assert evaluate_spec_completeness(ac_spec) is True


class TestBfsCallTreeWalkerAndCycleSafety:
    """Tests for walk_call_tree BFS algorithm and cycle safety."""

    @pytest.fixture
    def mock_codegraph_db(self, tmp_path):
        cg_dir = tmp_path / ".codegraph"
        cg_dir.mkdir(parents=True, exist_ok=True)
        db_path = cg_dir / "codegraph.db"
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE nodes (
                id TEXT PRIMARY KEY,
                name TEXT,
                kind TEXT,
                file_path TEXT,
                start_line INTEGER,
                end_line INTEGER,
                signature TEXT,
                is_exported INTEGER DEFAULT 1
            )
        """)
        cur.execute("""
            CREATE TABLE edges (
                source TEXT,
                target TEXT,
                kind TEXT
            )
        """)
        # Create a cyclic graph: A -> B -> C -> A (cycle) and C -> D (leaf)
        nodes = [
            ("node_a", "handleCheckin", "method", "src/controller.ts", 1, 10, "handleCheckin()", 1),
            ("node_b", "recordCheckin", "method", "src/service.ts", 1, 15, "recordCheckin()", 1),
            ("node_c", "calculatePenalty", "method", "src/engine.ts", 1, 40, "calculatePenalty()", 1),
            ("node_d", "saveLog", "method", "src/logger.ts", 1, 5, "saveLog()", 1),
        ]
        cur.executemany("INSERT INTO nodes (id, name, kind, file_path, start_line, end_line, signature, is_exported) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", nodes)
        
        edges = [
            ("node_a", "node_b", "call"),
            ("node_b", "node_c", "call"),
            ("node_c", "node_a", "call"), # cycle
            ("node_c", "node_d", "call"),
        ]
        cur.executemany("INSERT INTO edges (source, target, kind) VALUES (?, ?, ?)", edges)
        conn.commit()
        conn.close()
        return tmp_path

    def test_bfs_walker_cycle_safety_and_downstream(self, mock_codegraph_db):
        engine = MethodDiscoveryEngine(mock_codegraph_db)
        traversal = engine.walk_call_tree("node_a", max_depth=3)
        # Must visit node_b, node_c, node_d without getting stuck in infinite loop
        assert "node_b" in traversal
        assert "node_c" in traversal
        assert "node_d" in traversal
        # Verify no duplicate entries
        assert len(traversal) == len(set(traversal))
        engine.close()


class TestAdaptiveCoreSnippetsExtraction:
    """Tests for discover_adaptive_core_snippets with Dual-Factor Heuristic."""

    @pytest.fixture
    def mock_repo_with_code(self, tmp_path):
        src_dir = tmp_path / "src"
        src_dir.mkdir(parents=True, exist_ok=True)
        cg_dir = tmp_path / ".codegraph"
        cg_dir.mkdir(parents=True, exist_ok=True)

        # File 1: Complex calculation engine (M >= 2)
        engine_file = src_dir / "AttendanceEngine.ts"
        engine_file.write_text("""
        export function calculateLatePenalty(minutesLate: number, shift: string): number {
            if (minutesLate <= 15) {
                return 0;
            } else if (minutesLate <= 60) {
                return 50000;
            } else {
                return 100000;
            }
        }
        """, encoding="utf-8")

        # File 2: Declarative rule matrix (M = 1, but rule dictionary)
        rule_file = src_dir / "PenaltyConfig.ts"
        rule_file.write_text("""
        export const PENALTY_POLICY: Record<string, any> = {
            MORNING: { graceMinutes: 15, feeAmount: 50000 },
            NIGHT: { graceMinutes: 0, feeAmount: 100000 }
        };
        """, encoding="utf-8")

        # File 3: Simple 1-line facade/logger (M = 1, not a rule matrix)
        logger_file = src_dir / "SimpleLogger.ts"
        logger_file.write_text("""
        export function logEvent(msg: string): void {
            console.log(msg);
        }
        """, encoding="utf-8")

        # DB Setup
        db_path = cg_dir / "codegraph.db"
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE nodes (
                id TEXT PRIMARY KEY,
                name TEXT,
                kind TEXT,
                file_path TEXT,
                start_line INTEGER,
                end_line INTEGER,
                signature TEXT,
                is_exported INTEGER DEFAULT 1
            )
        """)
        cur.execute("CREATE TABLE edges (source TEXT, target TEXT, kind TEXT)")

        nodes = [
            ("n_calc", "calculateLatePenalty", "function", "src/AttendanceEngine.ts", 2, 10, "calculateLatePenalty(m, s)", 1),
            ("n_rule", "PENALTY_POLICY", "variable", "src/PenaltyConfig.ts", 2, 5, "const PENALTY_POLICY", 1),
            ("n_log", "logEvent", "function", "src/SimpleLogger.ts", 2, 4, "logEvent(msg)", 1),
        ]
        cur.executemany("INSERT INTO nodes (id, name, kind, file_path, start_line, end_line, signature, is_exported) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", nodes)
        conn.commit()
        conn.close()

        return tmp_path

    def test_discover_adaptive_core_snippets_extracts_complex_and_rule_matrix(self, mock_repo_with_code):
        engine = MethodDiscoveryEngine(mock_repo_with_code)
        # Incomplete spec triggers adaptive expansion
        vague_spec = "Chào team, kiểm thử phần chấm công nhé."
        snippets = engine.discover_adaptive_core_snippets(vague_spec)

        extracted_names = [s["name"] for s in snippets]
        # Should include calculateLatePenalty (M >= 2)
        assert "calculateLatePenalty" in extracted_names
        # Should include PENALTY_POLICY (declarative rule dictionary)
        assert "PENALTY_POLICY" in extracted_names
        # Should NOT include logEvent (M = 1 and no rule keywords)
        assert "logEvent" not in extracted_names

        engine.close()

    def test_discover_adaptive_core_snippets_skips_when_spec_is_complete(self, mock_repo_with_code):
        engine = MethodDiscoveryEngine(mock_repo_with_code)
        complete_spec = """
        Scenario: Checkin late
          Given employee is on morning shift
          When employee clocks in at 08:16
          Then system penalizes 50000 VNĐ
        """
        snippets = engine.discover_adaptive_core_snippets(complete_spec)
        assert len(snippets) == 0
        engine.close()


class TestMultiModuleStateIsolation:
    """Tests for multi-module state file isolation and smart auto-detection."""

    def test_multi_module_creates_isolated_state_files(self, tmp_path):
        mgr_chamcong = WorkflowStateManager(workspace_root=str(tmp_path), module_name="cham-cong")
        mgr_dangnhap = WorkflowStateManager(workspace_root=str(tmp_path), module_name="dang-nhap")

        assert mgr_chamcong.state_file.name == ".qa-state-cham-cong.json"
        assert mgr_dangnhap.state_file.name == ".qa-state-dang-nhap.json"

        # Initialize both modules
        mgr_chamcong.init_state("cham-cong", {"repo": "viva"})
        mgr_dangnhap.init_state("dang-nhap", {"repo": "viva"})

        # Verify both files co-exist without clobbering
        assert (tmp_path / ".qa-state-cham-cong.json").exists()
        assert (tmp_path / ".qa-state-dang-nhap.json").exists()

        state_cc = mgr_chamcong.load()
        state_dn = mgr_dangnhap.load()

        assert state_cc["module_name"] == "cham-cong"
        assert state_dn["module_name"] == "dang-nhap"

    def test_smart_autodetect_when_single_custom_state_file_exists(self, tmp_path):
        # Create a single custom state file
        custom_file = tmp_path / ".qa-state-auth_service.json"
        custom_file.write_text('{"module_name": "auth_service", "current_state": "DISCOVERY"}', encoding="utf-8")

        # When initializing without module_name, auto-detect should resolve to auth_service
        mgr = WorkflowStateManager(workspace_root=str(tmp_path))
        assert mgr.state_file.name == ".qa-state-auth_service.json"
        state = mgr.load()
        assert state.get("module_name") == "auth_service"

    def test_default_fallback_to_qa_state_json_when_no_custom_file(self, tmp_path):
        mgr = WorkflowStateManager(workspace_root=str(tmp_path))
        assert mgr.state_file.name == STATE_FILE_NAME
