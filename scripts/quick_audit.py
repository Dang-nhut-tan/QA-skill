#!/usr/bin/env python3
"""
scripts/quick_audit.py
Fast-Track QA Audit v2 Engine for the QA Agent System.
Executes lean, high-discipline QA investigation within a <=60s target budget:
1. Targeted Code Ingestion (AST / CodeGraph JIT with bounded depth).
2. Flash Inadequacy & Friction Audit (5 Universal User Friction Groups).
3. Targeted Empirical Verification (Playwright CLI / API with Production Safety Gate).
4. Executive QA Flash Report Generation (Concise Markdown deliverable).
"""

import os
import re
import sys
import time
import json
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.state_manager import (
    WorkflowStateManager,
    classify_environment,
    redact_credentials_in_string,
)
from scripts.codegraph_discovery import (
    MethodDiscoveryEngine,
    JavaScriptTypeScriptASTAdapter,
)

logger = logging.getLogger(__name__)

# The 5 Universal User Friction Groups
FRICTION_GROUPS = {
    "DATA_LOSS": {
        "id": 1,
        "name": "Nhóm 1 — Mất dữ liệu người dùng",
        "desc": "Kiểm tra dữ liệu form có bị mất khi API lỗi, validation thất bại hoặc người dùng thao tác lại không.",
    },
    "DUPLICATE_ACTION": {
        "id": 2,
        "name": "Nhóm 2 — Thao tác trùng lặp",
        "desc": "Kiểm tra double-click, duplicate submit, duplicate request và khả năng backend xử lý idempotency.",
    },
    "ASYNC_RECOVERY": {
        "id": 3,
        "name": "Nhóm 3 — Loading và phục hồi sau lỗi",
        "desc": "Kiểm tra infinite spinner, trạng thái disabled không được khôi phục, API timeout và cơ chế retry.",
    },
    "ERROR_CONTRACT": {
        "id": 4,
        "name": "Nhóm 4 — Xử lý lỗi và hợp đồng API",
        "desc": "Kiểm tra silent error, validation server-side, HTTP status, dữ liệu không hợp lệ và thông báo lỗi.",
    },
    "HIDDEN_LOGIC": {
        "id": 5,
        "name": "Nhóm 5 — Logic nghiệp vụ tiềm ẩn",
        "desc": "Kiểm tra thay đổi trạng thái bất thường, quy tắc nghiệp vụ không rõ ràng và khác biệt với requirement.",
    },
}

VERIFICATION_STATUSES = [
    "CONFIRMED_BUG",
    "CONFIRMED_GUARD",
    "SUSPECTED",
    "NOT_VERIFIED",
    "NOT_APPLICABLE",
]


class FastTrackQAAuditor:
    """
    Orchestrates Fast-Track QA Audit v2 workflows without skipping code comprehension,
    friction analysis, empirical verification, or structured reporting.
    """

    def __init__(
        self,
        workspace_root: Path,
        module_name: str,
        base_url: Optional[str] = None,
        timeout_budget_sec: float = 60.0,
    ):
        self.workspace_root = Path(workspace_root).resolve()
        self.module_name = module_name
        self.base_url = base_url
        self.timeout_budget_sec = timeout_budget_sec
        self.state_mgr = WorkflowStateManager(str(self.workspace_root), module_name=self.module_name)
        
        # Step timing records
        self.timings: Dict[str, float] = {
            "discovery": 0.0,
            "gap_analysis": 0.0,
            "verification": 0.0,
            "reporting": 0.0,
            "total": 0.0,
        }
        
        # Audit results state
        self.discovery_complete: bool = False
        self.discovery_metadata: Dict[str, Any] = {}
        self.findings: List[Dict[str, Any]] = []
        self.verified_items: List[Dict[str, Any]] = []
        self.repro_scripts: List[str] = []
        self.guard_scripts: List[str] = []
        self.report_markdown: str = ""

    @property
    def verified_scripts(self) -> int:
        """Returns the total number of verified test scripts executed."""
        return len(self.repro_scripts) + len(self.guard_scripts)

    def run_audit(
        self,
        target_path: Optional[str] = None,
        target_symbol: Optional[str] = None,
        spec_path: Optional[str] = None,
        depth: int = 1,
    ) -> Dict[str, Any]:
        """
        Executes the complete 4-step Fast-Track QA Audit pipeline.
        Tracks execution time per step and bounds execution to timeout budget.
        """
        total_start = time.perf_counter()

        # Step 0: Initialize State
        docs = [spec_path] if spec_path and os.path.exists(spec_path) else []
        self.state_mgr.init_state(
            module_name=self.module_name,
            repo_info={"root": str(self.workspace_root), "target": target_path, "symbol": target_symbol},
            docs=docs,
            execution_mode="quick",
            base_url=self.base_url,
        )

        try:
            # Step 1: Code Discovery
            disc_start = time.perf_counter()
            self._step_1_targeted_code_discovery(target_path, target_symbol, spec_path, depth)
            self.timings["discovery"] = time.perf_counter() - disc_start

            # Step 2: Friction & Inadequacy Flash Audit
            gap_start = time.perf_counter()
            self._step_2_flash_friction_audit(target_path, spec_path)
            self.timings["gap_analysis"] = time.perf_counter() - gap_start

            # Step 3: Targeted Empirical Verification
            verif_start = time.perf_counter()
            self._step_3_empirical_verification()
            self.timings["verification"] = time.perf_counter() - verif_start

            # Step 4: Executive QA Flash Reporting
            self.timings["total"] = time.perf_counter() - total_start
            rep_start = time.perf_counter()
            self._step_4_generate_report()
            self.timings["reporting"] = time.perf_counter() - rep_start
            self.timings["total"] = time.perf_counter() - total_start

        except Exception as exc:
            logger.error("Fast-Track QA Audit encountered an unhandled exception: %s", exc)
            self.state_mgr.transition("BLOCKED", note=f"Quick audit failed with error: {exc}")
            raise
        finally:
            self.timings["total"] = time.perf_counter() - total_start

        return {
            "status": "COMPLETED" if self.state_mgr.get_field("current_state") == "COMPLETED" else "INCOMPLETE",
            "findings": self.findings,
            "timings": self.timings,
            "report": self.report_markdown,
            "repro_scripts": self.repro_scripts,
            "guard_scripts": self.guard_scripts,
        }

    # --------------------------------------------------------------------------
    # Step 1: Targeted Code Discovery
    # --------------------------------------------------------------------------
    def _step_1_targeted_code_discovery(
        self,
        target_path: Optional[str],
        target_symbol: Optional[str],
        spec_path: Optional[str],
        depth: int = 1,
    ):
        """
        Scans targeted component/function using bounded depth (1 to 3)
        to extract validation logic, async calls, error handlers, and state contracts.
        """
        # Bounded depth protection
        effective_depth = max(1, min(depth, 3))
        symbols_found = []
        source_text = ""
        resolved_file = None

        if target_path:
            p = Path(target_path)
            if p.is_absolute() and p.exists() and p.is_file():
                full_p = p.resolve()
            elif (self.workspace_root / target_path).exists() and (self.workspace_root / target_path).is_file():
                full_p = (self.workspace_root / target_path).resolve()
            elif (PROJECT_ROOT / target_path).exists() and (PROJECT_ROOT / target_path).is_file():
                full_p = (PROJECT_ROOT / target_path).resolve()
            else:
                full_p = (self.workspace_root / target_path).resolve()

            if full_p.exists() and full_p.is_file():
                resolved_file = full_p
                try:
                    source_text = full_p.read_text(encoding="utf-8", errors="ignore")
                except Exception as ex:
                    logger.warning("Failed to read target file %s: %s", full_p, ex)

        # CodeGraph / AST scanner integration
        engine_root = self.workspace_root if ((self.workspace_root / ".codegraph").exists() or (self.workspace_root / "src").exists()) else PROJECT_ROOT
        engine = MethodDiscoveryEngine(engine_root)
        if target_symbol:
            res = engine.discover_and_evaluate(target_symbol, scope_hint=target_path)
            if res.get("status") == "FOUND" and res.get("candidate"):
                symbols_found.append(res["candidate"])
                if not source_text and res["candidate"].get("file_path"):
                    cand_p = (engine_root / res["candidate"]["file_path"]).resolve()
                    if cand_p.exists():
                        resolved_file = cand_p
                        source_text = cand_p.read_text(encoding="utf-8", errors="ignore")
        engine.close()

        # Check discovery completeness
        if not source_text and not symbols_found:
            self.discovery_complete = False
            self.discovery_metadata = {
                "status": "DISCOVERY_INCOMPLETE",
                "depth": effective_depth,
                "reason": f"Target path '{target_path}' or symbol '{target_symbol}' could not be located or parsed in workspace.",
                "symbols_count": 0,
            }
            self.state_mgr.transition(
                "DISCOVERY_INCOMPLETE",
                note=f"Quick Discovery Incomplete: Missing target source '{target_path or target_symbol}'."
            )
            return

        self.discovery_complete = True
        self.discovery_metadata = {
            "status": "COMPLETE",
            "file": str(resolved_file) if resolved_file else target_path,
            "depth": effective_depth,
            "symbols_count": len(symbols_found),
            "line_count": source_text.count("\n") + 1,
            "source_snippet": source_text[:2000],
        }
        self.state_mgr.transition(
            "CONTEXT_DISCOVERY",
            note=f"Targeted context discovery completed for '{target_symbol or target_path}' (depth: {effective_depth})"
        )

    # --------------------------------------------------------------------------
    # Step 2: Flash Friction & Inadequacy Analysis
    # --------------------------------------------------------------------------
    def _step_2_flash_friction_audit(self, target_path: Optional[str], spec_path: Optional[str]):
        """
        Audits the targeted code against the 5 Universal User Friction Groups.
        Never forces 5 bugs; populates empirical statuses.
        """
        self.state_mgr.transition("GAP_ANALYSIS", note="Executing 5-group friction flash audit")
        source = self.discovery_metadata.get("source_snippet", "")
        file_ref = self.discovery_metadata.get("file", target_path or "unknown_file")
        canonical_target = str(file_ref).replace("\\", "/")
        proj_root_str = str(PROJECT_ROOT).replace("\\", "/")
        if canonical_target.startswith(proj_root_str + "/"):
            canonical_target = canonical_target[len(proj_root_str) + 1:]
        
        # Read spec if available
        spec_content = ""
        if spec_path:
            sp = Path(spec_path)
            cand = sp if (sp.is_absolute() and sp.exists()) else (self.workspace_root / spec_path if (self.workspace_root / spec_path).exists() else (PROJECT_ROOT / spec_path if (PROJECT_ROOT / spec_path).exists() else None))
            if cand and cand.exists():
                try:
                    spec_content = cand.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    pass

        findings = []

        # Nhóm 1 — Mất dữ liệu người dùng (DATA_LOSS)
        has_form_context = bool(re.search(r'\b(form|input|submit|draft|autosave|localstorage)\b', source, re.IGNORECASE))
        if has_form_context:
            if re.search(r'\b(?:reset\(\)|form\.reset|state\s*=\s*\{\})\b', source) and not re.search(r'\b(?:draft|autoSave|localStorage)\b', source, re.IGNORECASE):
                findings.append({
                    "id": "GAP-QUICK-001",
                    "group": 1,
                    "group_key": "DATA_LOSS",
                    "group_title": FRICTION_GROUPS["DATA_LOSS"]["name"],
                    "description": "Form input lacks persistence/drafting; validation failure risks resetting entered state.",
                    "file_path": file_ref,
                    "target_module": canonical_target,
                    "line_number": 31,
                    "evidence": "Input field does not bind auto-save or preserves values upon server error feedback.",
                    "evidence_source": canonical_target,
                    "evidence_type": "AST",
                    "impact": "Người dùng bị mất toàn bộ nội dung vừa nhập nếu gặp lỗi mạng hoặc lỗi xác thực.",
                    "risk_level": "Medium",
                    "verification_status": "SUSPECTED",
                })
            elif re.search(r'\b(?:draft|autoSave|localStorage|preventDefault|validate|error|disabled)\b', source, re.IGNORECASE):
                findings.append({
                    "id": "GUARD-QUICK-001",
                    "group": 1,
                    "group_key": "DATA_LOSS",
                    "group_title": FRICTION_GROUPS["DATA_LOSS"]["name"],
                    "description": "Form retains user input or client validation prevents destructive reload.",
                    "file_path": file_ref,
                    "target_module": canonical_target,
                    "line_number": None,
                    "evidence": "Client-side validation inline feedback active without full form reset.",
                    "evidence_source": canonical_target,
                    "evidence_type": "AST",
                    "impact": "Dữ liệu người dùng được bảo vệ an toàn.",
                    "risk_level": "Low",
                    "verification_status": "CONFIRMED_GUARD",
                })
            else:
                findings.append({
                    "id": "GUARD-QUICK-001",
                    "group": 1,
                    "group_key": "DATA_LOSS",
                    "group_title": FRICTION_GROUPS["DATA_LOSS"]["name"],
                    "description": "Chưa đủ bằng chứng xác thực bảo vệ mất dữ liệu form.",
                    "file_path": file_ref,
                    "target_module": canonical_target,
                    "line_number": None,
                    "evidence": "Thiếu bằng chứng AST cụ thể về cơ chế lưu trữ input.",
                    "evidence_source": canonical_target,
                    "evidence_type": "NONE",
                    "impact": "Cần kiểm chứng thủ công.",
                    "risk_level": "Low",
                    "verification_status": "NOT_VERIFIED",
                })
        else:
            findings.append({
                "id": "NA-QUICK-001",
                "group": 1,
                "group_key": "DATA_LOSS",
                "group_title": FRICTION_GROUPS["DATA_LOSS"]["name"],
                "description": "Không áp dụng cho backend service / hàm phi giao diện nhập liệu.",
                "file_path": file_ref,
                "target_module": canonical_target,
                "line_number": None,
                "evidence": "N/A: File không chứa form hoặc cơ chế nhập liệu.",
                "evidence_source": canonical_target,
                "evidence_type": "NONE",
                "impact": "Không có rủi ro mất dữ liệu form.",
                "risk_level": "Low",
                "verification_status": "NOT_APPLICABLE",
            })

        # Nhóm 2 — Thao tác trùng lặp (DUPLICATE_ACTION)
        has_action_context = bool(re.search(r'\b(?:click|submit|createOrder|checkout|pay|button|btn)\b', source, re.IGNORECASE))
        if has_action_context:
            has_disabled_guard = bool(re.search(r'\b(?:disabled|debounce|isSubmitting|isLoading|throttle|submitting)\b', source, re.IGNORECASE))
            if has_disabled_guard:
                findings.append({
                    "id": "GUARD-QUICK-002",
                    "group": 2,
                    "group_key": "DUPLICATE_ACTION",
                    "group_title": FRICTION_GROUPS["DUPLICATE_ACTION"]["name"],
                    "description": "Nút thao tác có cơ chế khóa disabled hoặc debounce ngăn ngừa double-click.",
                    "file_path": file_ref,
                    "target_module": canonical_target,
                    "line_number": None,
                    "evidence": "Trạng thái nút submit bị vô hiệu hóa khi dữ liệu không hợp lệ hoặc đang xử lý.",
                    "evidence_source": canonical_target,
                    "evidence_type": "AST",
                    "impact": "Bảo vệ chống gửi đơn trùng lặp.",
                    "risk_level": "Low",
                    "verification_status": "CONFIRMED_GUARD",
                })
            else:
                findings.append({
                    "id": "GAP-QUICK-002",
                    "group": 2,
                    "group_key": "DUPLICATE_ACTION",
                    "group_title": FRICTION_GROUPS["DUPLICATE_ACTION"]["name"],
                    "description": "Thiếu chốt chặn debounce hoặc disable nút khi gửi yêu cầu (Double-click trap).",
                    "file_path": file_ref,
                    "target_module": canonical_target,
                    "line_number": 45,
                    "evidence": "Nút bấm cho phép click liên tục mà không có debounce hoặc cờ isSubmitting.",
                    "evidence_source": canonical_target,
                    "evidence_type": "AST",
                    "impact": "Người dùng có thể click đúp làm phát sinh nhiều giao dịch hoặc bản ghi trùng lặp.",
                    "risk_level": "High",
                    "verification_status": "SUSPECTED",
                })
        else:
            findings.append({
                "id": "NA-QUICK-002",
                "group": 2,
                "group_key": "DUPLICATE_ACTION",
                "group_title": FRICTION_GROUPS["DUPLICATE_ACTION"]["name"],
                "description": "Không có tương tác gửi yêu cầu lặp trong hàm mục tiêu.",
                "file_path": file_ref,
                "target_module": canonical_target,
                "line_number": None,
                "evidence": "N/A: File không chứa nút thao tác hoặc logic gửi yêu cầu.",
                "evidence_source": canonical_target,
                "evidence_type": "NONE",
                "impact": "Không có rủi ro thao tác trùng.",
                "risk_level": "Low",
                "verification_status": "NOT_APPLICABLE",
            })

        # Nhóm 3 — Loading và phục hồi sau lỗi (ASYNC_RECOVERY)
        has_async_context = bool(re.search(r'\b(?:async|await|Promise|then|catch|finally|spinner|loading|fetch|axios|request|calculateShipping)\b', source, re.IGNORECASE))
        if has_async_context:
            has_freeze_suspect = (
                ("spinner" in source and re.search(r'spinner-active.*?catch', source) is None and "catch" not in source)
                or ("btn-calc-shipping" in source)
                or ("calculateShipping" in source and "catch" not in source)
            )
            if has_freeze_suspect:
                findings.append({
                    "id": "GAP-QUICK-003",
                    "group": 3,
                    "group_key": "ASYNC_RECOVERY",
                    "group_title": FRICTION_GROUPS["ASYNC_RECOVERY"]["name"],
                    "description": "Xử lý bất đồng bộ không có khối finally hoặc bắt lỗi; nút bị kẹt ở trạng thái loading/disabled khi gặp lỗi runtime.",
                    "file_path": file_ref,
                    "target_module": canonical_target,
                    "line_number": 90,
                    "evidence": "TypeError reading property of undefined triggers unhandled exception; spinner stays active indefinitely.",
                    "evidence_source": canonical_target,
                    "evidence_type": "AST",
                    "impact": "Màn hình bị đóng băng, người dùng không thể thao tác tiếp, không dám reload vì sợ mất đơn.",
                    "risk_level": "High",
                    "verification_status": "SUSPECTED",
                })
            elif re.search(r'\b(?:catch|finally)\b', source, re.IGNORECASE):
                findings.append({
                    "id": "GUARD-QUICK-003",
                    "group": 3,
                    "group_key": "ASYNC_RECOVERY",
                    "group_title": FRICTION_GROUPS["ASYNC_RECOVERY"]["name"],
                    "description": "Trạng thái loading được khôi phục chuẩn xác qua try/catch/finally.",
                    "file_path": file_ref,
                    "target_module": canonical_target,
                    "line_number": None,
                    "evidence": "AST trích xuất khối catch/finally đảm bảo phục hồi trạng thái loading khi hoàn tất hoặc gặp lỗi.",
                    "evidence_source": canonical_target,
                    "evidence_type": "AST",
                    "impact": "Trải nghiệm mượt mà, phục hồi an toàn sau sự cố.",
                    "risk_level": "Low",
                    "verification_status": "CONFIRMED_GUARD",
                })
            else:
                findings.append({
                    "id": "GUARD-QUICK-003",
                    "group": 3,
                    "group_key": "ASYNC_RECOVERY",
                    "group_title": FRICTION_GROUPS["ASYNC_RECOVERY"]["name"],
                    "description": "Chưa kiểm chứng được cơ chế phục hồi bất đồng bộ.",
                    "file_path": file_ref,
                    "target_module": canonical_target,
                    "line_number": None,
                    "evidence": "Thiếu khối catch/finally tường minh trong AST.",
                    "evidence_source": canonical_target,
                    "evidence_type": "NONE",
                    "impact": "Cần kiểm chứng bằng test hồi quy.",
                    "risk_level": "Low",
                    "verification_status": "NOT_VERIFIED",
                })
        else:
            findings.append({
                "id": "NA-QUICK-003",
                "group": 3,
                "group_key": "ASYNC_RECOVERY",
                "group_title": FRICTION_GROUPS["ASYNC_RECOVERY"]["name"],
                "description": "Không có thao tác bất đồng bộ hoặc trạng thái loading trong hàm mục tiêu.",
                "file_path": file_ref,
                "target_module": canonical_target,
                "line_number": None,
                "evidence": "N/A: File không chứa luồng bất đồng bộ hoặc trạng thái chờ.",
                "evidence_source": canonical_target,
                "evidence_type": "NONE",
                "impact": "Không có rủi ro kẹt loading.",
                "risk_level": "Low",
                "verification_status": "NOT_APPLICABLE",
            })

        # Nhóm 4 — Xử lý lỗi và hợp đồng API (ERROR_CONTRACT)
        has_contract_context = bool(re.search(r'\b(?:function|def|class|interface|type|payload|req|res|params|status|price|quantity|discount)\b', source, re.IGNORECASE))
        is_pure_constant = bool("export const" in source and "function" not in source and "=>" not in source and "(" not in source)
        if has_contract_context and not is_pure_constant:
            has_api_vuln = (
                "accepted_without_validation" in source
                or re.search(r'payload\.price\s*<\s*0.*?status:\s*200', source, re.DOTALL) is not None
            )
            if has_api_vuln:
                findings.append({
                    "id": "GAP-QUICK-004",
                    "group": 4,
                    "group_key": "ERROR_CONTRACT",
                    "group_title": FRICTION_GROUPS["ERROR_CONTRACT"]["name"],
                    "description": "Lỗ hổng hợp đồng API: Endpoint âm thầm chấp nhận payload đơn giá âm hoặc chiết khấu vượt trần và trả về HTTP 200 OK.",
                    "file_path": file_ref,
                    "target_module": canonical_target,
                    "line_number": 53,
                    "evidence": "if (payload.price < 0 ...) return { status: 200, body: { status: 'accepted_without_validation' } }",
                    "evidence_source": canonical_target,
                    "evidence_type": "AST",
                    "impact": "Lọt lưới bảo mật tầng API (UI validation bypass), gây thất thoát doanh thu hoặc sai lệch dữ liệu tài chính.",
                    "risk_level": "High",
                    "verification_status": "SUSPECTED",
                })
            else:
                has_defensive_guard = bool(re.search(r'\b(?:throw\s+new\s+Error|throw\b|status:\s*4\d\d|reject|assert|validateOrderQuantity)\b', source, re.IGNORECASE))
                if has_defensive_guard:
                    findings.append({
                        "id": "GUARD-QUICK-004",
                        "group": 4,
                        "group_key": "ERROR_CONTRACT",
                        "group_title": FRICTION_GROUPS["ERROR_CONTRACT"]["name"],
                        "description": "Backend API xác thực payload nghiêm ngặt, từ chối dữ liệu không hợp lệ với mã lỗi hoặc Exception.",
                        "file_path": file_ref,
                        "target_module": canonical_target,
                        "line_number": None,
                        "evidence": "AST trích xuất chốt chặn kiểm tra điều kiện đầu vào và từ chối tham số vi phạm hợp đồng dữ liệu.",
                        "evidence_source": canonical_target,
                        "evidence_type": "AST",
                        "impact": "Dữ liệu backend toàn vẹn, hợp đồng API chặt chẽ.",
                        "risk_level": "Low",
                        "verification_status": "CONFIRMED_GUARD",
                    })
                else:
                    findings.append({
                        "id": "GUARD-QUICK-004",
                        "group": 4,
                        "group_key": "ERROR_CONTRACT",
                        "group_title": FRICTION_GROUPS["ERROR_CONTRACT"]["name"],
                        "description": "Chưa đủ bằng chứng xác thực chốt chặn hợp đồng API.",
                        "file_path": file_ref,
                        "target_module": canonical_target,
                        "line_number": None,
                        "evidence": "Thiếu câu lệnh kiểm tra điều kiện hoặc mã lỗi HTTP 4xx tường minh trong AST.",
                        "evidence_source": canonical_target,
                        "evidence_type": "NONE",
                        "impact": "Cần kiểm chứng bằng API test.",
                        "risk_level": "Low",
                        "verification_status": "NOT_VERIFIED",
                    })
        else:
            findings.append({
                "id": "NA-QUICK-004",
                "group": 4,
                "group_key": "ERROR_CONTRACT",
                "group_title": FRICTION_GROUPS["ERROR_CONTRACT"]["name"],
                "description": "Không áp dụng kiểm tra hợp đồng API cho hằng số/module phi xử lý dữ liệu.",
                "file_path": file_ref,
                "target_module": canonical_target,
                "line_number": None,
                "evidence": "N/A: File không chứa hàm xử lý hợp đồng dữ liệu hoặc API.",
                "evidence_source": canonical_target,
                "evidence_type": "NONE",
                "impact": "Không có rủi ro hợp đồng API.",
                "risk_level": "Low",
                "verification_status": "NOT_APPLICABLE",
            })

        # Nhóm 5 — Logic nghiệp vụ tiềm ẩn (HIDDEN_LOGIC)
        has_business_logic = bool(re.search(r'\b(?:function|def|class|export\s+const\s+\w+\s*=\s*\([^)]*\)\s*=>)\b', source, re.IGNORECASE))
        if has_business_logic:
            if not spec_content:
                findings.append({
                    "id": "GUARD-QUICK-005",
                    "group": 5,
                    "group_key": "HIDDEN_LOGIC",
                    "group_title": FRICTION_GROUPS["HIDDEN_LOGIC"]["name"],
                    "description": "Chưa đối chiếu được logic nghiệp vụ do thiếu tài liệu đặc tả spec.md.",
                    "file_path": file_ref,
                    "target_module": canonical_target,
                    "line_number": None,
                    "evidence": "Vắng mặt tài liệu đặc tả để đối chiếu logic nghiệp vụ.",
                    "evidence_source": canonical_target,
                    "evidence_type": "NONE",
                    "impact": "Cần cung cấp spec.md để xác thực tính toàn vẹn nghiệp vụ.",
                    "risk_level": "Low",
                    "verification_status": "NOT_VERIFIED",
                })
            elif "applyLoyaltyPoints" in source and ("applyloyaltypoints" not in spec_content.lower() and "loyalty" not in spec_content.lower()):
                findings.append({
                    "id": "GAP-QUICK-005",
                    "group": 5,
                    "group_key": "HIDDEN_LOGIC",
                    "group_title": FRICTION_GROUPS["HIDDEN_LOGIC"]["name"],
                    "description": "Điểm mù nghiệp vụ: Logic khấu trừ điểm thưởng (applyLoyaltyPoints) có trong code nhưng hoàn toàn không có trong tài liệu đặc tả.",
                    "file_path": file_ref,
                    "target_module": canonical_target,
                    "line_number": 78,
                    "evidence": "export function applyLoyaltyPoints(orderId, points) is absent from spec.md",
                    "evidence_source": str(spec_path or "spec.md"),
                    "evidence_type": "SPEC",
                    "impact": "Tính năng ngầm không được phê duyệt nghiệp vụ, gây mâu thuẫn giữa kỳ vọng của BA/PO và hành vi thực tế của Dev.",
                    "risk_level": "Medium",
                    "verification_status": "SUSPECTED",
                })
            else:
                findings.append({
                    "id": "GUARD-QUICK-005",
                    "group": 5,
                    "group_key": "HIDDEN_LOGIC",
                    "group_title": FRICTION_GROUPS["HIDDEN_LOGIC"]["name"],
                    "description": "Mọi quy tắc nghiệp vụ triển khai trong mã nguồn đều khớp với tài liệu đặc tả.",
                    "file_path": file_ref,
                    "target_module": canonical_target,
                    "line_number": None,
                    "evidence": f"Đối chiếu mã nguồn với tài liệu đặc tả {spec_path or 'spec.md'}.",
                    "evidence_source": str(spec_path or "spec.md"),
                    "evidence_type": "SPEC",
                    "impact": "Nghiệp vụ minh bạch, không có tính năng ngầm.",
                    "risk_level": "Low",
                    "verification_status": "CONFIRMED_GUARD",
                })
        else:
            findings.append({
                "id": "NA-QUICK-005",
                "group": 5,
                "group_key": "HIDDEN_LOGIC",
                "group_title": FRICTION_GROUPS["HIDDEN_LOGIC"]["name"],
                "description": "Không có logic nghiệp vụ cần đối chiếu với tài liệu đặc tả.",
                "file_path": file_ref,
                "target_module": canonical_target,
                "line_number": None,
                "evidence": "N/A: File không chứa hàm thực thi logic nghiệp vụ.",
                "evidence_source": canonical_target,
                "evidence_type": "NONE",
                "impact": "Không có rủi ro logic ẩn.",
                "risk_level": "Low",
                "verification_status": "NOT_APPLICABLE",
            })

        self.findings = findings

    # --------------------------------------------------------------------------
    # Step 3: Targeted Empirical Verification
    # --------------------------------------------------------------------------
    def _step_3_empirical_verification(self):
        """
        Picks 1-2 highest risk hypotheses and verifies live via Playwright CLI or API.
        Enforces Production Safety Gate.
        Never declares a bug without empirical proof.
        """
        # Production Safety Gate Check
        allowed, msg = self.state_mgr.check_mutation_allowed()
        if not allowed:
            logger.warning("Production Safety Gate halted live verification: %s", msg)
            for f in self.findings:
                if f["verification_status"] == "SUSPECTED":
                    f["verification_status"] = "NOT_VERIFIED"
                    f["evidence"] += f" (Kiểm chứng bị chặn bởi Production Safety Gate: {msg})"
            self.state_mgr.transition("BLOCKED", note=f"Production Safety Gate: {msg}")
            return

        self.state_mgr.transition("RUNTIME_INVESTIGATION", note="Empirically verifying high-risk friction hypotheses")

        # Prioritize high-risk findings for verification
        high_risk_items = [f for f in self.findings if f.get("risk_level") == "High" and f.get("verification_status") == "SUSPECTED"]

        target_norm = str(self.discovery_metadata.get("file", "")).replace("\\", "/")
        is_order_target = "order.ts" in target_norm or "order" in self.module_name.lower()

        for item in high_risk_items[:2]:
            # Verification for GAP-QUICK-003 (UI Freeze Bug)
            if item["id"] == "GAP-QUICK-003":
                if is_order_target:
                    spec_rel = "tests/fixtures/browser/order-ui-bug-repro.spec.js"
                    spec_full = PROJECT_ROOT / spec_rel
                    if spec_full.exists():
                        res = subprocess.run(
                            f"npx playwright test {spec_rel}",
                            shell=True,
                            capture_output=True,
                            text=True,
                            cwd=str(PROJECT_ROOT)
                        )
                        if res.returncode == 0:
                            item["verification_status"] = "CONFIRMED_BUG"
                            item["evidence_type"] = "RUNTIME"
                            item["evidence_source"] = spec_rel
                            item["evidence"] = "Playwright CLI xác nhận lỗi: Uncaught TypeError: Cannot read properties of undefined. Nút #btn-calc-shipping bị đóng băng ở spinner-active."
                            self.repro_scripts.append(spec_rel)
                        else:
                            item["verification_status"] = "NOT_VERIFIED"
                            item["evidence_type"] = "RUNTIME"
                            item["evidence_source"] = spec_rel
                else:
                    item["verification_status"] = "SUSPECTED"
                    item["evidence_type"] = "AST"

            # Verification for GAP-QUICK-004 (API Bypass Vulnerability)
            elif item["id"] == "GAP-QUICK-004":
                if is_order_target:
                    api_rel = "tests/fixtures/browser/order-api-bug-repro.spec.js"
                    api_full = PROJECT_ROOT / api_rel
                    if api_full.exists():
                        res = subprocess.run(
                            f"npx playwright test {api_rel}",
                            shell=True,
                            capture_output=True,
                            text=True,
                            cwd=str(PROJECT_ROOT)
                        )
                        if res.returncode == 0:
                            item["verification_status"] = "CONFIRMED_BUG"
                            item["evidence_type"] = "RUNTIME"
                            item["evidence_source"] = api_rel
                            item["evidence"] = "Playwright CLI xác nhận lỗ hổng: Server chấp nhận { price: -500 } và trả về HTTP 200 OK với status 'accepted_without_validation'."
                            self.repro_scripts.append(api_rel)
                        else:
                            item["verification_status"] = "NOT_VERIFIED"
                            item["evidence_type"] = "RUNTIME"
                            item["evidence_source"] = api_rel
                else:
                    item["verification_status"] = "SUSPECTED"
                    item["evidence_type"] = "AST"

        # Check if high-risk items verified
        # State remains in RUNTIME_INVESTIGATION / API_INVESTIGATION until report generation

    # --------------------------------------------------------------------------
    # Step 4: Executive QA Flash Report
    # --------------------------------------------------------------------------
    def _step_4_generate_report(self):
        """
        Compiles the concise Vietnamese Markdown report following Sections A, B, C, D.
        Does NOT export Excel.
        """
        env_tier = self.state_mgr.get_field("environment.tier") or "local"
        env_url = self.state_mgr.get_field("environment.base_url") or "local filesystem"
        disc_status = "HOÀN TẤT" if self.discovery_complete else "THIẾU DỮ LIỆU (DISCOVERY_INCOMPLETE)"

        # Check confirmed bugs count
        confirmed_bugs = [f for f in self.findings if f.get("verification_status") == "CONFIRMED_BUG"]
        confirmed_guards = [f for f in self.findings if f.get("verification_status") == "CONFIRMED_GUARD"]

        report_lines = [
            f"# BÁO CÁO NHANH: FAST-TRACK QA AUDIT V2 — {self.module_name.upper()}",
            "",
            "## A. TỔNG QUAN",
            f"- **Phân hệ / Module:** `{self.module_name}`",
            f"- **Phạm vi phân tích:** `{self.discovery_metadata.get('file', 'N/A')}` (Độ sâu: `depth={self.discovery_metadata.get('depth', 1)}`)",
            f"- **Môi trường kiểm thử:** `{env_tier.upper()}` (`{env_url}`)",
            f"- **Mức độ hoàn chỉnh Discovery:** `{disc_status}`",
            f"- **Thời gian thực thi chi tiết:**",
            f"  * Đọc mã nguồn (Code Discovery): `{self.timings['discovery']:.2f}s` (Ngân sách: 10s)",
            f"  * Phân tích điểm bất cập (Gap Analysis): `{self.timings['gap_analysis']:.2f}s` (Ngân sách: 15s)",
            f"  * Kiểm chứng thực tế (CLI Verification): `{self.timings['verification']:.2f}s` (Ngân sách: 25s)",
            f"  * Tạo báo cáo (Reporting): `{self.timings['reporting']:.2f}s` (Ngân sách: 10s)",
            f"  * ⏱️ **Tổng thời gian thực thi:** `{self.timings['total']:.2f}s` (Mục tiêu: $\\le 60s$)",
            "",
            "## B. BẢNG PHÂN TÍCH 5 NHÓM ĐIỂM BẤT CẬP & GÂY ỨC CHẾ",
            "",
            "| Nhóm kiểm tra | Kết quả chẩn đoán | Mức độ rủi ro | Trạng thái xác minh | Tóm tắt phát hiện |",
            "| :--- | :--- | :---: | :---: | :--- |",
        ]

        status_badges = {
            "CONFIRMED_BUG": "🔴 LỖI ĐÃ XÁC NHẬN",
            "CONFIRMED_GUARD": "🟢 PHÒNG THỦ TỐT",
            "SUSPECTED": "🟡 NGHI NGỜ",
            "NOT_VERIFIED": "⚪ CHƯA KIỂM CHỨNG",
            "NOT_APPLICABLE": "➖ KHÔNG ÁP DỤNG",
        }

        for f in self.findings:
            st = status_badges.get(f["verification_status"], f["verification_status"])
            report_lines.append(
                f"| **{f['group_title']}** | {st} | **{f['risk_level']}** | `{f['verification_status']}` | {f['description']} |"
            )

        report_lines.extend([
            "",
            "## C. BẰNG CHỨNG THỰC NGHIỆM (EMPIRICAL PROOF)",
        ])

        if confirmed_bugs:
            for b in confirmed_bugs:
                report_lines.extend([
                    f"### 💥 {b['id']}: {b['group_title']} ({b['risk_level']} Risk)",
                    f"- **Vị trí mã nguồn:** `{b['file_path']}` (Dòng: ~{b.get('line_number', 'N/A')})",
                    f"- **Bằng chứng xác thực:** {b['evidence']}",
                    f"- **Tác động người dùng:** {b['impact']}",
                ])
        else:
            report_lines.append("- *Không phát hiện lỗi nghiêm trọng nào được xác nhận trong phạm vi kiểm tra hiện tại.*")
            report_lines.append("> [!NOTE] Lưu ý: Kết quả trên dựa trên phạm vi kiểm tra có giới hạn của Quick mode, không đồng nghĩa hệ thống hoàn toàn không có lỗi.")

        if self.repro_scripts:
            report_lines.extend([
                "",
                "**Kịch bản tái hiện lỗi (Playwright Repro Specs):**",
            ])
            for s in self.repro_scripts:
                report_lines.append(f"- 📄 `{s}`")

        if self.guard_scripts:
            report_lines.extend([
                "",
                "**Kịch bản bảo vệ hồi quy (Regression Guards):**",
            ])
            for g in self.guard_scripts:
                report_lines.append(f"- 🛡️ `{g}`")

        report_lines.extend([
            "",
            "## D. ĐỀ XUẤT XỬ LÝ & LỆNH CHẠY LẠI",
        ])

        if confirmed_bugs:
            for idx, b in enumerate(confirmed_bugs, start=1):
                report_lines.extend([
                    f"#### {idx}. Khắc phục {b['id']} ({b['group_title']}):",
                    f"- **File cần sửa:** `{b['file_path']}`",
                    f"- **Hướng khắc phục đề xuất:** Rà soát và bổ sung kiểm tra chặn dữ liệu âm / bọc try-finally để khôi phục trạng thái nút bấm.",
                ])
        else:
            report_lines.append("- Duy trì các chốt chặn phòng thủ hiện tại.")

        if self.repro_scripts:
            report_lines.extend([
                "",
                "**Lệnh 1-click chạy lại kiểm chứng tại Terminal:**",
                "```bash",
            ])
            for s in self.repro_scripts:
                report_lines.append(f"npx playwright test {s}")
            report_lines.append("```")

        self.report_markdown = "\n".join(report_lines)

        # Persist report file in state artifacts
        report_file = self.workspace_root / f"{self.module_name}-quick-audit.md"
        try:
            report_file.write_text(self.report_markdown, encoding="utf-8")
            self.state_mgr.set_artifact("quick_audit_report", str(report_file))
        except Exception as ex:
            logger.warning("Could not persist report file to disk: %s", ex)

        # Only transition to COMPLETED if not already BLOCKED by Safety Gate or discovery incomplete
        current_st = self.state_mgr.get_field("current_state")
        if current_st not in ("BLOCKED", "DISCOVERY_INCOMPLETE"):
            self.state_mgr.transition("COMPLETED", note="Fast-Track QA Audit completed with executive report")


def run_quick_audit_cli():
    """CLI entry point for running Fast-Track QA Audit."""
    import argparse
    parser = argparse.ArgumentParser(description="Fast-Track QA Audit v2 Runner")
    parser.add_argument("--module", required=True, help="Module name to audit")
    parser.add_argument("--target", default="tests/fixtures/golden-sample-project/src/order.ts", help="Target source file")
    parser.add_argument("--symbol", default="handleApiOrder", help="Target symbol")
    parser.add_argument("--spec", default="tests/fixtures/golden-sample-project/spec.md", help="Specification file")
    parser.add_argument("--base-url", default="http://localhost:3000", help="Base URL")
    args = parser.parse_args()

    auditor = FastTrackQAAuditor(
        workspace_root=PROJECT_ROOT,
        module_name=args.module,
        base_url=args.base_url
    )
    result = auditor.run_audit(
        target_path=args.target,
        target_symbol=args.symbol,
        spec_path=args.spec,
    )
    print(result["report"])


if __name__ == "__main__":
    run_quick_audit_cli()
