#!/usr/bin/env python3
"""
step8_validation.py
文件格式: Python 源码

Step 9（v2）: 最终校验与输出
- 对最终配置包执行 JSON 解析校验（json_repair）
- 校验关键目录/文件存在性
- 生成验证报告与合规证书
- 产出 final_parlant_config
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
import shutil
import json
import traceback
from collections import defaultdict, deque

from json_repair import repair_json
from jsonschema import validate as jsonschema_validate

from ..utils.file_utils import write_json, write_markdown
from ..utils.logger import logger


def _collect_json_files(root: Path) -> List[Path]:
    return [p for p in root.rglob("*.json") if p.is_file()]


def _detect_cycle_in_graph(edges: Dict[str, List[str]]) -> bool:
    """检测有向图是否存在环（Kahn 拓扑排序）。"""
    indegree: Dict[str, int] = defaultdict(int)
    nodes = set(edges.keys())
    for src, dsts in edges.items():
        nodes.add(src)
        for d in dsts:
            nodes.add(d)
            indegree[d] += 1
    for n in nodes:
        indegree.setdefault(n, 0)

    q = deque([n for n in nodes if indegree[n] == 0])
    visited = 0
    while q:
        n = q.popleft()
        visited += 1
        for d in edges.get(n, []):
            indegree[d] -= 1
            if indegree[d] == 0:
                q.append(d)
    return visited != len(nodes)


def _check_journey_state_machine(journey_data: Dict[str, Any]) -> List[str]:
    """状态机检查：死胡同、不可达状态、无结束态。"""
    issues: List[str] = []
    states = journey_data.get("sop_states", []) or []
    if not states:
        return ["journey has no sop_states"]

    state_ids = [s.get("state_id") for s in states if isinstance(s, dict) and s.get("state_id")]
    if not state_ids:
        return ["journey has no valid state_id"]
    state_set = set(state_ids)

    # 构图
    edges: Dict[str, List[str]] = defaultdict(list)
    end_states = set()
    for s in states:
        if not isinstance(s, dict):
            continue
        sid = s.get("state_id")
        if not sid:
            continue
        if s.get("is_end_state") is True:
            end_states.add(sid)
        for t in s.get("transitions", []) or []:
            if isinstance(t, dict):
                tid = t.get("target_state_id")
                if tid:
                    edges[sid].append(tid)
                    if tid not in state_set:
                        issues.append(f"transition target not found: {sid} -> {tid}")

    # 无结束态
    if not end_states:
        issues.append("journey has no end state")

    # 不可达状态（以第一个状态为起点）
    start = state_ids[0]
    reachable = set()
    dq = deque([start])
    while dq:
        cur = dq.popleft()
        if cur in reachable:
            continue
        reachable.add(cur)
        for nxt in edges.get(cur, []):
            if nxt in state_set and nxt not in reachable:
                dq.append(nxt)
    unreachable = sorted(list(state_set - reachable))
    if unreachable:
        issues.append(f"unreachable states: {unreachable}")

    # 死胡同状态（非结束态且无出边）
    for sid in state_set:
        if sid not in end_states and len(edges.get(sid, [])) == 0:
            issues.append(f"dead-end state: {sid}")

    return issues


def _compute_quality_score(
    *,
    json_parse_errors: int,
    missing_required_paths: int,
    schema_errors: int,
    journey_schema_errors: int,
    state_machine_issues: int,
    conflict_issues: int,
    backbone_issues: int,
) -> int:
    """简单可解释的质量分（0-100）。

    用于 Step8 可选返工门控：分数低于阈值则建议回跳返工。
    """
    score = 100
    # 解析/结构错误权重大
    score -= min(40, json_parse_errors * 8)
    score -= min(30, missing_required_paths * 10)
    score -= min(30, schema_errors * 6)
    score -= min(30, journey_schema_errors * 3)
    score -= min(20, state_machine_issues * 3)
    score -= min(20, conflict_issues * 3)
    score -= min(20, backbone_issues * 10)
    if score < 0:
        score = 0
    if score > 100:
        score = 100
    return int(score)


async def step8_validation_handler(context: Dict[str, Any], orchestrator) -> Dict[str, Any]:
    logger.info("Step 9(v2): final validation started")
    output_dir = Path(context.get("output_dir", "./output/step8_validation"))
    output_dir.mkdir(parents=True, exist_ok=True)
    log_dir = Path(context.get("step_log_dir", output_dir / "logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    msg_dir = Path(context.get("step_message_archive_dir", output_dir / "message_archive"))
    msg_dir.mkdir(parents=True, exist_ok=True)
    step_log_file = log_dir / "step9_validation.log"
    archive_file = msg_dir / "step9_validation_messages.jsonl"

    def _append_log(msg: str):
        with open(step_log_file, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] {msg}\n")

    def _append_archive(event: str, payload: dict):
        with open(archive_file, "a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {"ts": datetime.now().isoformat(), "event": event, "payload": payload},
                    ensure_ascii=False,
                )
                + "\n"
            )

    _append_log("Step9 started")

    try:
        output_base = Path(context.get("output_base_dir", output_dir.parent))
        package_dir = output_base / "parlant_agent_config"
        if not package_dir.exists():
            # 兼容 Step7 目录内副本
            alt = output_base / "step7_config_assembly" / "parlant_agent_config"
            if alt.exists():
                package_dir = alt
            else:
                raise ValueError("Step8 requires parlant_agent_config generated by Step7")
        _append_archive("input_loaded", {"package_dir": str(package_dir)})

        # 1) JSON 可解析性（json_repair）
        sys_cfg = (context.get("config") or {}) or getattr(orchestrator, "config", {}).get("system_config", {}) or {}
        auto_fix_cfg = (sys_cfg.get("step8_auto_fix_json", {}) or {})
        enable_auto_fix = bool(auto_fix_cfg.get("enabled", False))

        json_files = _collect_json_files(package_dir)
        json_parse_errors: List[str] = []
        json_auto_fixed: List[str] = []
        for f in json_files:
            try:
                _ = repair_json(f.read_text(encoding="utf-8"), return_objects=True)
            except Exception as e:
                # 解析失败：尝试修复并（可选）回写
                try:
                    raw = f.read_text(encoding="utf-8")
                    repaired = repair_json(raw)  # 返回修复后的 JSON 字符串
                    # 二次确认可解析
                    _ = json.loads(repaired)
                    if enable_auto_fix:
                        f.write_text(repaired, encoding="utf-8")
                        json_auto_fixed.append(str(f))
                    else:
                        json_parse_errors.append(f"{f}: repaired_ok_but_not_written (enable step8_auto_fix_json to write back)")
                except Exception as e2:
                    json_parse_errors.append(f"{f}: {type(e).__name__}: {e} | repair_failed: {type(e2).__name__}: {e2}")

        # 2) 关键结构校验
        required_dirs = [
            package_dir / "agents",
        ]
        missing_paths = [str(p) for p in required_dirs if not p.exists()]

        # 3) JSON Schema 校验（关键文件）
        schema_errors: List[str] = []
        journey_schema_errors: List[str] = []
        state_machine_issues: List[str] = []
        conflict_issues: List[str] = []
        agent_dirs = [p for p in (package_dir / "agents").glob("*") if p.is_dir()] if (package_dir / "agents").exists() else []
        metadata_schema = {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string"},
                "agent_name": {"type": "string"},
            },
            "required": ["agent_id", "agent_name"],
        }
        guidelines_schema = {
            "type": "object",
            "properties": {
                "agent_guidelines": {"type": "array"},
            },
            "required": ["agent_guidelines"],
        }
        for ad in agent_dirs:
            metadata_file = ad / "00_agent_base" / "agent_metadata.json"
            if metadata_file.exists():
                try:
                    data = repair_json(metadata_file.read_text(encoding="utf-8"), return_objects=True)
                    jsonschema_validate(instance=data, schema=metadata_schema)
                except Exception as e:
                    schema_errors.append(f"{metadata_file}: {type(e).__name__}: {e}")

            guidelines_file = ad / "01_agent_rules" / "agent_guidelines.json"
            if guidelines_file.exists():
                try:
                    data = repair_json(guidelines_file.read_text(encoding="utf-8"), return_objects=True)
                    jsonschema_validate(instance=data, schema=guidelines_schema)
                except Exception as e:
                    schema_errors.append(f"{guidelines_file}: {type(e).__name__}: {e}")

            # journey 级 schema/一致性检查
            journeys_dir = ad / "02_journeys"
            if journeys_dir.exists():
                sop_schema = {
                    "type": "object",
                    "properties": {
                        "sop_id": {"type": "string"},
                        "sop_title": {"type": "string"},
                        "sop_states": {"type": "array"},
                    },
                    "required": ["sop_id", "sop_states"],
                }
                sop_guidelines_schema = {
                    "type": "object",
                    "properties": {
                        "sop_id": {"type": "string"},
                        "sop_scoped_guidelines": {"type": "array"},
                    },
                    "required": ["sop_id"],
                }
                sop_observations_schema = {
                    "type": "object",
                    "properties": {
                        "sop_id": {"type": "string"},
                        "sop_observations": {"type": "array"},
                    },
                    "required": ["sop_id"],
                }

                for journey_folder in [p for p in journeys_dir.glob("*") if p.is_dir()]:
                    sop_file = journey_folder / "sop.json"
                    sop_guidelines_file = journey_folder / "sop_guidelines.json"
                    sop_observations_file = journey_folder / "sop_observations.json"

                    # sop.json
                    if sop_file.exists():
                        try:
                            sop_data = repair_json(sop_file.read_text(encoding="utf-8"), return_objects=True)
                            jsonschema_validate(instance=sop_data, schema=sop_schema)
                            sm_issues = _check_journey_state_machine(sop_data)
                            for issue in sm_issues:
                                state_machine_issues.append(f"{sop_file}: {issue}")
                        except Exception as e:
                            journey_schema_errors.append(f"{sop_file}: {type(e).__name__}: {e}")
                    else:
                        journey_schema_errors.append(f"{journey_folder}: missing sop.json")

                    # sop_guidelines.json
                    if sop_guidelines_file.exists():
                        try:
                            gdata = repair_json(sop_guidelines_file.read_text(encoding="utf-8"), return_objects=True)
                            jsonschema_validate(instance=gdata, schema=sop_guidelines_schema)

                            # exclusions/dependencies 环路与自依赖检查
                            guidelines = gdata.get("sop_scoped_guidelines", []) or []
                            dep_edges: Dict[str, List[str]] = defaultdict(list)
                            ex_edges: Dict[str, List[str]] = defaultdict(list)
                            for g in guidelines:
                                if not isinstance(g, dict):
                                    continue
                                gid = g.get("guideline_id")
                                if not gid:
                                    continue
                                for dep in g.get("dependencies", []) or []:
                                    if dep == gid:
                                        conflict_issues.append(f"{sop_guidelines_file}: self dependency `{gid}`")
                                    dep_edges[gid].append(dep)
                                for ex in g.get("exclusions", []) or []:
                                    if ex == gid:
                                        conflict_issues.append(f"{sop_guidelines_file}: self exclusion `{gid}`")
                                    ex_edges[gid].append(ex)

                            if _detect_cycle_in_graph(dep_edges):
                                conflict_issues.append(f"{sop_guidelines_file}: dependency cycle detected")
                            if _detect_cycle_in_graph(ex_edges):
                                conflict_issues.append(f"{sop_guidelines_file}: exclusion cycle detected")
                        except Exception as e:
                            journey_schema_errors.append(f"{sop_guidelines_file}: {type(e).__name__}: {e}")

                    # sop_observations.json
                    if sop_observations_file.exists():
                        try:
                            odata = repair_json(sop_observations_file.read_text(encoding="utf-8"), return_objects=True)
                            jsonschema_validate(instance=odata, schema=sop_observations_schema)
                        except Exception as e:
                            journey_schema_errors.append(f"{sop_observations_file}: {type(e).__name__}: {e}")

        # 主干约束校验（来自 Step2）
        main_backbone = context.get("main_sop_backbone", {}) or {}
        if not main_backbone:
            output_base_dir = output_dir.parent
            candidate_files = [
                output_base_dir / "step2_objective_alignment_main_sop" / "step2_main_sop_backbone.json",
                output_base_dir / "step2_objective_alignment_main_sop" / "result.json",
                output_base_dir / "dimension_analysis" / "main_sop_backbone.json",
            ]
            for p in candidate_files:
                if not p.exists():
                    continue
                try:
                    loaded = repair_json(p.read_text(encoding="utf-8"), return_objects=True)
                    if isinstance(loaded, dict) and loaded.get("main_sop_nodes"):
                        main_backbone = loaded
                        context["main_sop_backbone"] = main_backbone
                        break
                    if isinstance(loaded, dict):
                        nested = loaded.get("main_sop_backbone")
                        if isinstance(nested, dict) and nested.get("main_sop_nodes"):
                            main_backbone = nested
                            context["main_sop_backbone"] = main_backbone
                            break
                except Exception:
                    # 忽略回退加载异常，继续按已有 context 校验并在报告中暴露问题
                    pass
        nodes = main_backbone.get("main_sop_nodes", []) or []
        backbone_issues: List[str] = []
        if nodes:
            if not (5 <= len(nodes) <= 9):
                backbone_issues.append(f"main_sop_nodes count out of range: {len(nodes)}")
        else:
            backbone_issues.append("main_sop_backbone missing in context")

        # 质量分与可选返工门控
        quality_score = _compute_quality_score(
            json_parse_errors=len(json_parse_errors),
            missing_required_paths=len(missing_paths),
            schema_errors=len(schema_errors),
            journey_schema_errors=len(journey_schema_errors),
            state_machine_issues=len(state_machine_issues),
            conflict_issues=len(conflict_issues),
            backbone_issues=len(backbone_issues),
        )
        gate_cfg = (sys_cfg.get("step8_quality_gate", {}) or {})
        gate_enabled = bool(gate_cfg.get("enabled", False))
        threshold = int(gate_cfg.get("rework_trigger_threshold", 80))
        rework_restart_step = int(gate_cfg.get("rework_restart_step", 5))
        max_rework_rounds = int(gate_cfg.get("max_rework_rounds", 1))
        rework_required = bool(gate_enabled and quality_score < threshold)

        passed = (
            (len(json_parse_errors) == 0)
            and (len(missing_paths) == 0)
            and (len(backbone_issues) == 0)
            and (len(schema_errors) == 0)
            and (len(journey_schema_errors) == 0)
            and (len(state_machine_issues) == 0)
            and (len(conflict_issues) == 0)
        )

        validation_report_lines = [
            "# Step 9 Validation Report",
            "",
            f"- generated_at: {datetime.now().isoformat()}",
            f"- package_dir: `{package_dir}`",
            f"- json_files_checked: {len(json_files)}",
            f"- passed: {passed}",
            "",
            "## JSON Parse Errors",
        ] + ([f"- {x}" for x in json_parse_errors] if json_parse_errors else ["- 无"]) + [
            "",
            "## JSON Schema Errors",
        ] + ([f"- {x}" for x in schema_errors] if schema_errors else ["- 无"]) + [
            "",
            "## Journey Schema Errors",
        ] + ([f"- {x}" for x in journey_schema_errors] if journey_schema_errors else ["- 无"]) + [
            "",
            "## State Machine Issues",
        ] + ([f"- {x}" for x in state_machine_issues] if state_machine_issues else ["- 无"]) + [
            "",
            "## Guideline Conflict Issues",
        ] + ([f"- {x}" for x in conflict_issues] if conflict_issues else ["- 无"]) + [
            "",
            "## Missing Required Paths",
        ] + ([f"- {x}" for x in missing_paths] if missing_paths else ["- 无"]) + [
            "",
            "## Main Backbone Checks",
        ] + ([f"- {x}" for x in backbone_issues] if backbone_issues else ["- 无"]) + [
            "",
        ]

        write_markdown("\n".join(validation_report_lines), str(output_dir / "step9_validation_report.md"))

        compliance_certificate = {
            "generated_at": datetime.now().isoformat(),
            "passed": passed,
            "quality_score": quality_score,
            "checks": {
                "json_parse_errors": len(json_parse_errors),
                "json_auto_fixed": len(json_auto_fixed),
                "schema_errors": len(schema_errors),
                "journey_schema_errors": len(journey_schema_errors),
                "state_machine_issues": len(state_machine_issues),
                "conflict_issues": len(conflict_issues),
                "missing_required_paths": len(missing_paths),
                "main_backbone_issues": len(backbone_issues),
            },
        }
        write_json(compliance_certificate, str(output_dir / "step9_compliance_certificate.json"))

        # 4) 产出正式目录（校验后的最终版本）
        final_dir = output_base / "final_parlant_config"
        if final_dir.exists():
            shutil.rmtree(final_dir, ignore_errors=True)
        shutil.copytree(package_dir, final_dir)
        _append_archive(
            "output_written",
            {
                "passed": passed,
                "json_files_checked": len(json_files),
                "schema_errors": len(schema_errors),
                "journey_schema_errors": len(journey_schema_errors),
                "state_machine_issues": len(state_machine_issues),
                "conflict_issues": len(conflict_issues),
                "final_dir": str(final_dir),
            },
        )
        _append_log("Step9 completed")

        return {
            "passed": passed,
            "output_files": [
                "step9_validation_report.md",
                "step9_compliance_certificate.json",
                str(final_dir),
            ],
            "metadata": {
                "json_files_checked": len(json_files),
                "json_parse_errors": len(json_parse_errors),
                "json_auto_fixed": len(json_auto_fixed),
                "schema_errors": len(schema_errors),
                "journey_schema_errors": len(journey_schema_errors),
                "state_machine_issues": len(state_machine_issues),
                "conflict_issues": len(conflict_issues),
                "missing_required_paths": len(missing_paths),
                "main_backbone_issues": len(backbone_issues),
                "quality_score": quality_score,
                "rework_required": rework_required,
                "rework_restart_step": rework_restart_step,
                "max_rework_rounds": max_rework_rounds,
            },
        }
    except Exception as e:
        _append_log(f"Step9 failed: {type(e).__name__}: {e}")
        _append_archive(
            "error",
            {"error": f"{type(e).__name__}: {e}", "traceback": traceback.format_exc()},
        )
        raise

