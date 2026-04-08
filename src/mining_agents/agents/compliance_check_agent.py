#!/usr/bin/env python3
"""
compliance_check_agent.py
文件格式: Python 源码

ComplianceCheckAgent:
- 对 Step3/Step4 的关键产物进行轻量结构校验与合规门控（最小实现）
- 不依赖异步并发；仅在需要时由 Step handler 调用
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json

from .base_agent import BaseAgent


def _as_list(x: Any) -> List[Any]:
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]


def _load_json(path: Path) -> Tuple[Optional[Any], Optional[str]]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


class ComplianceCheckAgent(BaseAgent):
    """最小合规模块：对关键字段与 JSON 结构做门控校验。"""

    async def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        # 这里不走 LLM，直接做结构化校验
        return await self.run(task, context)

    async def run(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        stage = str(context.get("stage", "unknown"))
        output_dir = Path(str(context.get("output_dir", "./output")))
        output_dir.mkdir(parents=True, exist_ok=True)

        files = [Path(p) for p in _as_list(context.get("files")) if p]
        issues: List[str] = []
        checked: List[str] = []

        for p in files:
            checked.append(str(p))
            if not p.exists():
                issues.append(f"missing_file: {p}")
                continue

            data, err = _load_json(p)
            if err:
                issues.append(f"invalid_json: {p} -> {err}")
                continue

            # 仅做最小契约校验（对齐 v2 关键产物）
            if stage == "step3_global_guidelines":
                # agent_guidelines.json
                if p.name == "agent_guidelines.json":
                    if not isinstance(data, dict):
                        issues.append(f"agent_guidelines_not_object: {p}")
                    else:
                        if not data.get("agent_id"):
                            issues.append(f"agent_guidelines_missing_agent_id: {p}")
                        gl = data.get("agent_guidelines")
                        if not isinstance(gl, list) or len(gl) == 0:
                            issues.append(f"agent_guidelines_empty: {p}")
                # step3_glossary_master.json
                if p.name == "step3_glossary_master.json":
                    if not isinstance(data, dict):
                        issues.append(f"glossary_master_not_object: {p}")
                    else:
                        if not data.get("agent_id"):
                            issues.append(f"glossary_master_missing_agent_id: {p}")
                        terms = data.get("terms")
                        if not isinstance(terms, list) or len(terms) == 0:
                            issues.append(f"glossary_master_terms_empty: {p}")
                # agent_canned_responses.json（可选）
                if p.name == "agent_canned_responses.json":
                    if not isinstance(data, dict):
                        issues.append(f"agent_canned_responses_not_object: {p}")
                    else:
                        if not data.get("agent_id"):
                            issues.append(f"agent_canned_responses_missing_agent_id: {p}")
                        cr = data.get("agent_canned_responses")
                        if not isinstance(cr, list) or len(cr) == 0:
                            issues.append(f"agent_canned_responses_empty: {p}")

            if stage == "step4_user_profiles":
                if p.name == "agent_user_profiles.json":
                    if not isinstance(data, dict):
                        issues.append(f"user_profiles_not_object: {p}")
                    else:
                        if not data.get("agent_id"):
                            issues.append(f"user_profiles_missing_agent_id: {p}")
                        seg = data.get("user_segments")
                        per = data.get("personas")
                        if not isinstance(seg, list) or len(seg) == 0:
                            issues.append(f"user_segments_empty: {p}")
                        if not isinstance(per, list) or len(per) == 0:
                            issues.append(f"personas_empty: {p}")

            if stage == "step5_branch_sop_parallel":
                # Step5 per-node产物：journey/guidelines/glossary/tools
                if p.name.startswith("step5_journeys_"):
                    if not isinstance(data, dict) or not data.get("sop_id") or not data.get("sop_states"):
                        issues.append(f"step5_journey_invalid: {p}")
                    else:
                        states = data.get("sop_states") or []
                        if not (5 <= len(states) <= 10):
                            issues.append(f"step5_journey_state_count_out_of_range({len(states)}): {p}")
                if p.name.startswith("step5_guidelines_"):
                    if not isinstance(data, dict):
                        issues.append(f"step5_guidelines_not_object: {p}")
                    else:
                        gl = data.get("sop_scoped_guidelines")
                        if not isinstance(gl, list) or len(gl) == 0:
                            issues.append(f"step5_guidelines_empty: {p}")
                        cr = data.get("sop_canned_responses")
                        if cr is not None and not isinstance(cr, list):
                            issues.append(f"step5_canned_responses_not_list: {p}")
                if p.name.startswith("step5_glossary_"):
                    if not isinstance(data, dict):
                        issues.append(f"step5_glossary_not_object: {p}")
                    else:
                        # 如果模型决策跳过，则不检查terms是否为空
                        if data.get("skipped_by_model") is True:
                            pass  # 模型决策跳过，不检查
                        else:
                            terms = data.get("terms")
                            if not isinstance(terms, list) or len(terms) == 0:
                                issues.append(f"step5_glossary_terms_empty: {p}")
                if p.name.startswith("step5_tools_"):
                    if not isinstance(data, dict):
                        issues.append(f"step5_tools_not_object: {p}")
                    else:
                        tools = data.get("tools")
                        if not isinstance(tools, list) or len(tools) == 0:
                            issues.append(f"step5_tools_empty: {p}")

            if stage == "step6_edge_cases":
                # edge case list
                if p.name == "step6_edge_case_sops.json":
                    if not isinstance(data, list) or len(data) == 0:
                        issues.append(f"step6_edge_case_sops_empty: {p}")
                    else:
                        # 单节点 edge：每个 sop_states 必须只有1个 state
                        for item in data:
                            if not isinstance(item, dict):
                                continue
                            states = item.get("sop_states") or []
                            if not isinstance(states, list) or len(states) != 1:
                                issues.append(f"step6_edge_sop_not_single_state({len(states) if isinstance(states,list) else 'na'}): {p}")
                                break
                # 注入后的 step5 guidelines 仍应为合法 JSON 且 sop_scoped_guidelines 非空
                if p.name.startswith("step5_guidelines_"):
                    if not isinstance(data, dict):
                        issues.append(f"step6_injected_guidelines_not_object: {p}")
                    elif data.get("skipped") is True:
                        pass
                    else:
                        gl = data.get("sop_scoped_guidelines")
                        if not isinstance(gl, list) or len(gl) == 0:
                            issues.append(f"step6_injected_guidelines_empty: {p}")

        passed = len(issues) == 0
        report = {
            "stage": stage,
            "passed": passed,
            "checked_files": checked,
            "issues": issues,
        }

        report_file = output_dir / f"{stage}_compliance_report.json"
        report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        return {
            "passed": passed,
            "compliance_report": report,
            "output_files": [str(report_file)],
            "metadata": {"issues_count": len(issues)},
        }

