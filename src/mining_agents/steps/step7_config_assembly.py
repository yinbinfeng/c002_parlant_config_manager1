#!/usr/bin/env python3
"""
step7_config_assembly.py
文件格式: Python 源码

Step 7（v2）: Parlant 配置组装
- 整合step3-step6的文件，按parlant目录结构重组
- 生成主journey的sop.json和sop_guidelines.json
- 建立父子journey链接关系
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import shutil
import traceback
import json
import re
from datetime import datetime
from json_repair import repair_json

from ..utils.file_utils import write_markdown, write_json
from ..utils.logger import logger


def _derive_agent_id(text: str) -> str:
    """生成简短英文 agent_id"""
    raw = (text or "").strip()
    low = raw.lower()
    tokens: list[str] = []
    
    if "日本共荣" in raw or "共荣" in raw:
        tokens.append("kyoroei")
    elif "日本" in raw:
        tokens.append("japan")
    
    if "保险" in raw or "insurance" in low:
        tokens.append("insurance")
    
    if "挽留" in raw or "续保" in raw or "retention" in low:
        tokens.append("retention")
    
    import hashlib
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:8] if raw else "unknown"
    base = "_".join([t for t in tokens if t]) or "parlant_agent"
    agent_id = f"{base}_{digest}" if base == "parlant_agent" else base
    
    agent_id = re.sub(r"[^a-z0-9_]+", "_", agent_id.lower()).strip("_")
    return (agent_id[:32] or "parlant_agent")


def _derive_main_journey_name(text: str) -> str:
    """生成主journey名称"""
    raw = (text or "").strip()
    low = raw.lower()
    tokens: list[str] = []
    
    if "日本共荣" in raw or "共荣" in raw:
        tokens.append("kyoroei")
    elif "日本" in raw:
        tokens.append("japan")
    
    if "保险" in raw or "insurance" in low:
        tokens.append("insurance")
    
    if "挽留" in raw or "续保" in raw or "retention" in low:
        tokens.append("retention")
    
    base = "_".join([t for t in tokens if t]) or "main"
    main_name = f"{base}_main"
    main_name = re.sub(r"[^a-z0-9_]+", "_", main_name.lower()).strip("_")
    return (main_name[:48] or "main_journey")


def _load_json_file(path: Path) -> tuple[dict | None, str | None]:
    """加载JSON文件"""
    try:
        raw = path.read_text(encoding="utf-8")
        return repair_json(raw, return_objects=True), None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def _ensure_list(x):
    """确保返回列表"""
    if isinstance(x, list):
        return x
    if x is None:
        return []
    return [x]


def _build_main_journey_sop(
    main_backbone: dict,
    main_journey_name: str,
    branch_journey_map: Dict[str, List[str]],
    edge_journey_map: Dict[str, List[str]],
) -> dict:
    """
    构建主journey的sop.json
    
    Args:
        main_backbone: Step2生成的主SOP主干
        main_journey_name: 主journey名称
        branch_journey_map: node_id -> list of branch journey names
        edge_journey_map: node_id -> list of edge journey names
    
    Returns:
        主journey的sop.json内容
    """
    sop_id = main_backbone.get("sop_id", f"{main_journey_name}_sop")
    nodes = main_backbone.get("main_sop_nodes", [])
    
    sop_states = []
    for idx, node in enumerate(nodes):
        node_id = node.get("node_id", f"node_{idx:03d}")
        node_name = node.get("node_name", node_id)
        instruction = node.get("instruction", "")
        exit_condition = node.get("exit_condition", "")
        
        branch_names = branch_journey_map.get(node_id, [])
        edge_names = edge_journey_map.get(node_id, [])
        
        child_journeys = []
        for bn in branch_names:
            child_journeys.append({
                "journey_type": "branch",
                "journey_name": bn,
                "trigger": f"在[{node_name}]节点触发分支场景",
            })
        for en in edge_names:
            child_journeys.append({
                "journey_type": "edge",
                "journey_name": en,
                "trigger": f"在[{node_name}]节点触发边缘场景",
            })
        
        next_idx = idx + 1
        transitions = []
        if next_idx < len(nodes):
            next_node_id = nodes[next_idx].get("node_id", f"node_{next_idx:03d}")
            transitions.append({
                "target_state_id": next_node_id,
                "condition": "正常流程推进",
            })
        
        state = {
            "state_id": node_id,
            "state_name": node_name,
            "state_type": "chat",
            "instruction": instruction,
            "exit_condition": exit_condition,
            "transitions": transitions,
            "child_journeys": child_journeys,
        }
        
        if idx == len(nodes) - 1:
            state["is_end_state"] = True
            state["transitions"] = []
        
        sop_states.append(state)
    
    return {
        "sop_id": sop_id,
        "sop_type": "main",
        "sop_title": f"{main_journey_name} 主流程",
        "sop_description": "主SOP主干流程，包含分支和边缘场景链接",
        "sop_states": sop_states,
        "frozen": main_backbone.get("frozen", True),
        "frozen_at": main_backbone.get("frozen_at", datetime.now().isoformat()),
    }


def _build_main_journey_guidelines(
    main_journey_name: str,
    global_guidelines: Optional[dict],
) -> dict:
    """
    构建主journey的sop_guidelines.json
    主journey引用全局规则，不生成专属规则
    """
    return {
        "sop_id": f"{main_journey_name}_sop",
        "sop_title": f"{main_journey_name} 主流程规则",
        "remark": "主Journey引用全局规则，不生成专属规则",
        "sop_canned_responses": [],
        "sop_scoped_guidelines": [],
        "global_guideline_reference": "01_agent_rules/agent_guidelines.json",
    }


def _add_parent_link_to_journey(
    sop_data: dict,
    parent_sop_id: str,
    parent_node_id: str,
    is_edge_case: bool = False,
) -> dict:
    """
    为子journey添加父journey链接
    """
    sop_data["parent_sop_id"] = parent_sop_id
    sop_data["parent_node_id"] = parent_node_id
    if is_edge_case:
        sop_data["is_edge_case"] = True
    return sop_data


def _fix_branch_sop_transitions(sop_data: dict) -> dict:
    """
    修复分支SOP的transitions字段
    确保每个state都有正确的transitions字段
    """
    sop_states = sop_data.get("sop_states", [])
    if not sop_states:
        return sop_data
    
    fixed_states = []
    for idx, state in enumerate(sop_states):
        if not isinstance(state, dict):
            fixed_states.append(state)
            continue
        
        state_id = state.get("state_id", f"state_{idx}")
        
        if "transitions" not in state or not state.get("transitions"):
            transitions = []
            next_idx = idx + 1
            if next_idx < len(sop_states):
                next_state = sop_states[next_idx]
                if isinstance(next_state, dict):
                    next_state_id = next_state.get("state_id", f"state_{next_idx}")
                    condition = state.get("condition", "正常流程推进")
                    transitions.append({
                        "target_state_id": next_state_id,
                        "condition": condition,
                    })
            
            if state.get("is_end_state") is True:
                transitions = []
            
            state["transitions"] = transitions
        
        fixed_states.append(state)
    
    sop_data["sop_states"] = fixed_states
    return sop_data


async def step7_config_assembly_handler(context: Dict[str, Any], orchestrator) -> Dict[str, Any]:
    logger.info("Step 7(v2): config assembly started - integrating previous step outputs")
    output_dir = Path(context.get("output_dir", "./output/step7_config_assembly"))
    output_dir.mkdir(parents=True, exist_ok=True)
    log_dir = Path(context.get("step_log_dir", output_dir / "logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    msg_dir = Path(context.get("step_message_archive_dir", output_dir / "message_archive"))
    msg_dir.mkdir(parents=True, exist_ok=True)
    step_log_file = log_dir / "step7_config_assembly.log"
    archive_file = msg_dir / "step7_config_assembly_messages.jsonl"

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

    _append_log("Step7 started")
    _append_archive("input_loaded", {"output_dir": str(output_dir)})

    try:
        output_base = Path(context.get("output_base_dir", output_dir.parent))
        
        step2_dir = output_base / "step2_objective_alignment_main_sop"
        step3_dir = output_base / "step3_global_rules_and_glossary"
        step4_dir = output_base / "step4_user_profile"
        step5_dir = output_base / "step5_branch_sop_parallel"
        step6_dir = output_base / "step6_edge_cases"
        step_extract_dir = output_base / "step_extract_canned_obs"
        
        if not step3_dir.exists():
            raise ValueError(f"Step3输出目录不存在: {step3_dir}")
        if not step4_dir.exists():
            raise ValueError(f"Step4输出目录不存在: {step4_dir}")
        
        agent_name = _derive_agent_id(context.get("business_desc", ""))
        main_journey_name = _derive_main_journey_name(context.get("business_desc", ""))
        
        parlant_root = output_base / "parlant_agent_config"
        if parlant_root.exists():
            shutil.rmtree(parlant_root)
        agent_root = parlant_root / "agents" / agent_name
        (agent_root / "00_agent_base").mkdir(parents=True, exist_ok=True)
        (agent_root / "01_agent_rules").mkdir(parents=True, exist_ok=True)
        (agent_root / "02_journeys").mkdir(parents=True, exist_ok=True)
        (agent_root / "03_tools").mkdir(parents=True, exist_ok=True)
        
        assembled_files: List[str] = []
        integration_issues: List[str] = []
        
        global_guidelines_data = None
        step3_global_guidelines = step3_dir / "agent_guidelines.json"
        if step3_global_guidelines.exists():
            data, err = _load_json_file(step3_global_guidelines)
            if err:
                integration_issues.append(f"Step3全局规则加载失败: {err}")
            else:
                global_guidelines_data = data
                rules_out = agent_root / "01_agent_rules" / "agent_guidelines.json"
                rules_out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                assembled_files.append(str(rules_out))
        else:
            integration_issues.append(f"Step3全局规则文件不存在: {step3_global_guidelines}")

        all_canned_responses: List[dict] = []
        
        global_canned_file = step_extract_dir / "global_canned_responses.json"
        if global_canned_file.exists():
            data, err = _load_json_file(global_canned_file)
            if err:
                integration_issues.append(f"提取步骤全局canned responses加载失败: {err}")
            else:
                cr_list = data.get("agent_canned_responses", [])
                if isinstance(cr_list, list):
                    all_canned_responses.extend(cr_list)
                target = agent_root / "01_agent_rules" / "agent_canned_responses.json"
                target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                assembled_files.append(str(target))
                _append_log(f"Loaded global canned responses from extraction step: {len(cr_list)} items")
        else:
            step3_canned = step3_dir / "agent_canned_responses.json"
            if step3_canned.exists():
                data, err = _load_json_file(step3_canned)
                if err:
                    integration_issues.append(f"Step3全局话术加载失败: {err}")
                else:
                    cr_list = data.get("agent_canned_responses", [])
                    if isinstance(cr_list, list):
                        all_canned_responses.extend(cr_list)
                    target = agent_root / "01_agent_rules" / "agent_canned_responses.json"
                    target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                    assembled_files.append(str(target))
                    _append_log(f"Loaded global canned responses from step3: {len(cr_list)} items")

        global_obs_file = step_extract_dir / "global_observations.json"
        if global_obs_file.exists():
            data, err = _load_json_file(global_obs_file)
            if err:
                integration_issues.append(f"提取步骤全局observations加载失败: {err}")
            else:
                target = agent_root / "01_agent_rules" / "agent_observations.json"
                target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                assembled_files.append(str(target))
                _append_log(f"Loaded global observations from extraction step")
        else:
            step3_observations = step3_dir / "agent_observations.json"
            if step3_observations.exists():
                data, err = _load_json_file(step3_observations)
                if err:
                    integration_issues.append(f"Step3全局observation加载失败: {err}")
                else:
                    target = agent_root / "01_agent_rules" / "agent_observations.json"
                    target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                    assembled_files.append(str(target))
                    _append_log(f"Loaded global observations from step3")

        step4_profiles = step4_dir / "agent_user_profiles.json"
        if step4_profiles.exists():
            data, err = _load_json_file(step4_profiles)
            if err:
                integration_issues.append(f"Step4用户画像加载失败: {err}")
            else:
                target = agent_root / "00_agent_base" / "agent_user_profiles.json"
                target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                assembled_files.append(str(target))
        else:
            integration_issues.append(f"Step4用户画像文件不存在: {step4_profiles}")

        # 加载并合并glossary（Step3主术语库 + Step5子分支术语库）
        step3_glossary_master = step3_dir / "step3_glossary_master.json"
        all_glossary_terms = []
        glossary_agent_id = "japan_kyoei_insurance_outbound_retention_agent"
        glossary_remark = "支撑日本共荣保险外呼营销场景中挂断挽留、产品转化及合规管控的核心术语体系"
        
        if step3_glossary_master.exists():
            data, err = _load_json_file(step3_glossary_master)
            if err:
                integration_issues.append(f"Step3术语库加载失败: {err}")
            else:
                if isinstance(data, dict):
                    glossary_agent_id = data.get("agent_id", glossary_agent_id)
                    glossary_remark = data.get("remark", glossary_remark)
                    step3_terms = _ensure_list(data.get("terms", []))
                    all_glossary_terms.extend(step3_terms)
                    _append_log(f"Loaded {len(step3_terms)} terms from Step3 glossary")
        else:
            integration_issues.append(f"Step3术语库文件不存在: {step3_glossary_master}")
        
        # 收集Step5子分支的glossary术语
        step5_glossary_terms = []
        if step5_dir.exists():
            for glossary_file in step5_dir.rglob("step5_glossary_*.json"):
                data, err = _load_json_file(glossary_file)
                if err:
                    continue
                if isinstance(data, dict) and not data.get("skipped"):
                    terms = _ensure_list(data.get("terms", []))
                    if terms:
                        step5_glossary_terms.extend(terms)
                        _append_log(f"Loaded {len(terms)} terms from {glossary_file.name}")
        
        # 合并术语并去重（基于term_id）
        seen_term_ids = set()
        merged_terms = []
        for term in all_glossary_terms + step5_glossary_terms:
            if isinstance(term, dict):
                term_id = term.get("term_id", "")
                if term_id and term_id not in seen_term_ids:
                    seen_term_ids.add(term_id)
                    merged_terms.append(term)
                elif not term_id:
                    # 为没有term_id的术语生成一个
                    term["term_id"] = f"kyoei_term_{len(merged_terms) + 1:03d}"
                    merged_terms.append(term)
        
        # 重新编号所有术语
        for i, term in enumerate(merged_terms, start=1):
            term["term_id"] = f"kyoei_term_{i:03d}"
        
        # 写入合并后的glossary
        merged_glossary = {
            "agent_id": glossary_agent_id,
            "remark": glossary_remark,
            "terms": merged_terms,
        }
        (agent_root / "00_agent_base" / "glossary").mkdir(parents=True, exist_ok=True)
        glossary_target = agent_root / "00_agent_base" / "glossary" / "glossary_master.json"
        glossary_target.write_text(json.dumps(merged_glossary, ensure_ascii=False, indent=2), encoding="utf-8")
        assembled_files.append(str(glossary_target))
        _append_log(f"Merged glossary written with {len(merged_terms)} total terms")
        
        branch_journey_map: Dict[str, List[str]] = {}
        edge_journey_map: Dict[str, List[str]] = {}
        
        main_backbone = None
        main_backbone_file = step2_dir / "main_sop_backbone.json"
        if main_backbone_file.exists():
            main_backbone, err = _load_json_file(main_backbone_file)
            if err:
                integration_issues.append(f"Step2主SOP主干加载失败: {err}")
                main_backbone = None
        
        if step5_dir.exists():
            step5_json_files = sorted([p for p in step5_dir.rglob("*.json") if p.is_file()])
            for src in step5_json_files:
                data, err = _load_json_file(src)
                if err:
                    integration_issues.append(f"{src}: JSON无效: {err}")
                    continue
                name = src.stem
                if name.startswith("step5_journeys_"):
                    key = name.removeprefix("step5_journeys_") or "branch"
                    
                    # 检查是否被模型跳过，如果跳过则不创建分支目录
                    if data.get("skipped_by_model") is True or data.get("skipped") is True:
                        skip_reason = data.get("skip_reason", data.get("reason", "模型判断该节点不需要二级分支"))
                        _append_log(f"Skipping branch directory for {key}: {skip_reason}")
                        continue
                    
                    # 使用有意义的命名：节点名称+序号
                    node_name_for_dir = key
                    # 尝试从step5结果中获取节点名称
                    if main_backbone and main_backbone.get("main_sop_nodes"):
                        for node in _ensure_list(main_backbone.get("main_sop_nodes", [])):
                            if isinstance(node, dict) and node.get("node_id") == key:
                                node_name = node.get("node_name", "")
                                if node_name:
                                    # 将节点名称转换为安全的目录名
                                    node_name_for_dir = re.sub(r"[^\w\u4e00-\u9fa5]+", "_", node_name).strip("_")
                                    node_name_for_dir = f"{node_name_for_dir}_{key}"
                                break
                    
                    journey_name = f"branch_{node_name_for_dir}"
                    
                    if main_backbone and main_backbone.get("sop_id"):
                        data = _add_parent_link_to_journey(
                            data,
                            parent_sop_id=main_backbone.get("sop_id", f"{main_journey_name}_sop"),
                            parent_node_id=key,
                            is_edge_case=False,
                        )
                    
                    data = _fix_branch_sop_transitions(data)
                    
                    target = agent_root / "02_journeys" / journey_name / "sop.json"
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                    assembled_files.append(str(target))
                    
                    node_id = key
                    if node_id not in branch_journey_map:
                        branch_journey_map[node_id] = []
                    branch_journey_map[node_id].append(journey_name)
                    
                elif name.startswith("step5_guidelines_"):
                    key = name.removeprefix("step5_guidelines_") or "branch"
                    
                    # 检查是否被模型跳过，如果跳过则跳过处理
                    if data.get("skipped") is True:
                        _append_log(f"Skipping guidelines file for {key}: marked as skipped by model")
                        continue
                    
                    # 使用有意义的命名：节点名称+序号
                    node_name_for_dir = key
                    if main_backbone and main_backbone.get("main_sop_nodes"):
                        for node in _ensure_list(main_backbone.get("main_sop_nodes", [])):
                            if isinstance(node, dict) and node.get("node_id") == key:
                                node_name = node.get("node_name", "")
                                if node_name:
                                    node_name_for_dir = re.sub(r"[^\w\u4e00-\u9fa5]+", "_", node_name).strip("_")
                                    node_name_for_dir = f"{node_name_for_dir}_{key}"
                                break
                    
                    journey_name = f"branch_{node_name_for_dir}"
                    journey_dir = agent_root / "02_journeys" / journey_name
                    journey_dir.mkdir(parents=True, exist_ok=True)
                    
                    sop_crs = data.get("sop_canned_responses", [])
                    sop_gl = data.get("sop_scoped_guidelines", [])
                    
                    guidelines_payload = {
                        "sop_id": data.get("sop_id", f"{journey_name}_sop"),
                        "sop_title": data.get("sop_title", f"{journey_name} 二级分支 Journey"),
                        "remark": data.get("remark", "Step5 生成：二级分支局部 guidelines（sop_only）"),
                        "sop_scoped_guidelines": sop_gl,
                    }
                    target = journey_dir / "sop_guidelines.json"
                    target.write_text(json.dumps(guidelines_payload, ensure_ascii=False, indent=2), encoding="utf-8")
                    assembled_files.append(str(target))
                    
                    extracted_canned_file = step_extract_dir / "local_canned_responses" / f"sop_canned_responses_{key}.json"
                    if extracted_canned_file.exists():
                        ext_data, ext_err = _load_json_file(extracted_canned_file)
                        if not ext_err and isinstance(ext_data, dict):
                            ext_crs = ext_data.get("sop_canned_responses", [])
                            if isinstance(ext_crs, list) and len(ext_crs) > 0:
                                cr_target = journey_dir / "sop_canned_responses.json"
                                cr_target.write_text(json.dumps(ext_data, ensure_ascii=False, indent=2), encoding="utf-8")
                                assembled_files.append(str(cr_target))
                                _append_log(f"Loaded sop_canned_responses from extraction step: {cr_target} ({len(ext_crs)} items)")
                    elif isinstance(sop_crs, list) and len(sop_crs) > 0:
                        cr_payload = {
                            "sop_id": data.get("sop_id", f"{journey_name}_sop"),
                            "sop_title": data.get("sop_title", f"{journey_name} 二级分支 Journey"),
                            "remark": f"{journey_name} SOP专属模板话术",
                            "sop_canned_responses": sop_crs,
                        }
                        cr_target = journey_dir / "sop_canned_responses.json"
                        cr_target.write_text(json.dumps(cr_payload, ensure_ascii=False, indent=2), encoding="utf-8")
                        assembled_files.append(str(cr_target))
                        _append_log(f"Generated sop_canned_responses from step5: {cr_target} ({len(sop_crs)} items)")
                elif name.startswith("sop_observations_"):
                    key = name.removeprefix("sop_observations_") or "branch"
                    
                    # 检查是否被模型跳过，如果跳过则跳过处理
                    if isinstance(data, dict) and data.get("skipped") is True:
                        _append_log(f"Skipping observations file for {key}: marked as skipped by model")
                        continue
                    
                    # 使用有意义的命名：节点名称+序号
                    node_name_for_dir = key
                    if main_backbone and main_backbone.get("main_sop_nodes"):
                        for node in _ensure_list(main_backbone.get("main_sop_nodes", [])):
                            if isinstance(node, dict) and node.get("node_id") == key:
                                node_name = node.get("node_name", "")
                                if node_name:
                                    node_name_for_dir = re.sub(r"[^\w\u4e00-\u9fa5]+", "_", node_name).strip("_")
                                    node_name_for_dir = f"{node_name_for_dir}_{key}"
                                break
                    
                    journey_name = f"branch_{node_name_for_dir}"
                    
                    extracted_obs_file = step_extract_dir / "local_observations" / f"sop_observations_{key}.json"
                    if extracted_obs_file.exists():
                        ext_data, ext_err = _load_json_file(extracted_obs_file)
                        if not ext_err and isinstance(ext_data, dict):
                            if "sop_id" not in ext_data:
                                ext_data["sop_id"] = ext_data.get("sop_id", f"{journey_name}_sop")
                            target = agent_root / "02_journeys" / journey_name / "sop_observations.json"
                            target.parent.mkdir(parents=True, exist_ok=True)
                            target.write_text(json.dumps(ext_data, ensure_ascii=False, indent=2), encoding="utf-8")
                            assembled_files.append(str(target))
                            _append_log(f"Loaded sop_observations from extraction step: {target}")
                    else:
                        obs_payload = data
                        if isinstance(data, dict):
                            if "sop_id" not in data:
                                obs_payload = {
                                    "sop_id": data.get("sop_id", f"{journey_name}_sop"),
                                    "sop_title": data.get("sop_title", f"{journey_name} 二级分支 Journey"),
                                    "sop_observations": data.get("sop_observations", []),
                                }
                        target = agent_root / "02_journeys" / journey_name / "sop_observations.json"
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_text(json.dumps(obs_payload, ensure_ascii=False, indent=2), encoding="utf-8")
                        assembled_files.append(str(target))
                elif name.startswith("step5_tools_"):
                    if data.get("skipped") is True:
                        _append_log(f"Skipping tools file {name}: marked as skipped")
                        continue
                    key = name.removeprefix("step5_tools_") or "tool"
                    
                    # 使用有意义的命名：节点名称+序号
                    node_name_for_dir = key
                    if main_backbone and main_backbone.get("main_sop_nodes"):
                        for node in _ensure_list(main_backbone.get("main_sop_nodes", [])):
                            if isinstance(node, dict) and node.get("node_id") == key:
                                node_name = node.get("node_name", "")
                                if node_name:
                                    node_name_for_dir = re.sub(r"[^\w\u4e00-\u9fa5]+", "_", node_name).strip("_")
                                    node_name_for_dir = f"{node_name_for_dir}_{key}"
                                break
                    
                    target = agent_root / "03_tools" / f"step5_{node_name_for_dir}" / "tool_meta.json"
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                    assembled_files.append(str(target))
                elif name.startswith("step5_glossary_"):
                    if data.get("skipped") is True:
                        _append_log(f"Skipping glossary file {name}: marked as skipped")
                        continue
                    (agent_root / "00_agent_base" / "glossary").mkdir(parents=True, exist_ok=True)
                    key = name.removeprefix("step5_glossary_") or "branch"
                    
                    # 使用有意义的命名：节点名称+序号
                    node_name_for_dir = key
                    if main_backbone and main_backbone.get("main_sop_nodes"):
                        for node in _ensure_list(main_backbone.get("main_sop_nodes", [])):
                            if isinstance(node, dict) and node.get("node_id") == key:
                                node_name = node.get("node_name", "")
                                if node_name:
                                    node_name_for_dir = re.sub(r"[^\w\u4e00-\u9fa5]+", "_", node_name).strip("_")
                                    node_name_for_dir = f"{node_name_for_dir}_{key}"
                                break
                    
                    target = agent_root / "00_agent_base" / "glossary" / f"step5_{node_name_for_dir}.json"
                    target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                    assembled_files.append(str(target))
        else:
            integration_issues.append(f"Step5输出目录不存在: {step5_dir}")

        step3_json_files = sorted([p for p in step3_dir.rglob("*.json") if p.is_file()])
        
        for src in step3_json_files:
            data, err = _load_json_file(src)
            if err:
                integration_issues.append(f"{src}: JSON无效: {err}")
                continue
            
            name = src.stem
            if name in ("agent_guidelines", "step3_glossary_master"):
                continue
            if name.startswith("step3_journeys_"):
                journey_name = name.removeprefix("step3_journeys_") or "journey"
                target = agent_root / "02_journeys" / journey_name / "sop.json"
                target.parent.mkdir(parents=True, exist_ok=True)
                if isinstance(data, dict) and "journeys" in data:
                    journeys = _ensure_list(data.get("journeys"))
                    data = journeys[0] if journeys else {}
                target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                assembled_files.append(str(target))
            elif name.startswith("step3_guidelines_"):
                journey_name = name.removeprefix("step3_guidelines_") or "journey"
                target = agent_root / "02_journeys" / journey_name / "sop_guidelines.json"
                target.parent.mkdir(parents=True, exist_ok=True)
                if isinstance(data, dict) and "sop_scoped_guidelines" not in data:
                    if "guidelines" in data:
                        data = {
                            "sop_id": f"{journey_name}_sop_001",
                            "sop_scoped_guidelines": _ensure_list(data.get("guidelines")),
                        }
                elif isinstance(data, list):
                    data = {
                        "sop_id": f"{journey_name}_sop_001",
                        "sop_scoped_guidelines": _ensure_list(data),
                    }
                target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                assembled_files.append(str(target))
            elif name.startswith("step3_tools_"):
                tool_name = name.removeprefix("step3_tools_") or "tool"
                target = agent_root / "03_tools" / tool_name / "tool_meta.json"
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                assembled_files.append(str(target))
            elif name.startswith("step3_glossary_"):
                (agent_root / "00_agent_base" / "glossary").mkdir(parents=True, exist_ok=True)
                glossary_name = name.removeprefix("step3_glossary_") or "glossary"
                target = agent_root / "00_agent_base" / "glossary" / f"{glossary_name}.json"
                target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                assembled_files.append(str(target))
        
        if step6_dir.exists():
            step6_sops_file = step6_dir / "step6_edge_case_sops.json"
            if step6_sops_file.exists():
                edge_sops, err = _load_json_file(step6_sops_file)
                if err:
                    integration_issues.append(f"Step6边缘场景加载失败: {err}")
                elif isinstance(edge_sops, list):
                    for idx, sop in enumerate(edge_sops):
                        if not isinstance(sop, dict):
                            continue
                        sop_id = str(sop.get("sop_id") or f"edge_journey_{idx + 1}")
                        journey_name = re.sub(r"[^a-zA-Z0-9_\-]+", "_", sop_id).strip("_") or "edge_journey"
                        
                        parent_node_id = sop.get("parent_node_id", "")
                        if main_backbone and main_backbone.get("sop_id"):
                            sop = _add_parent_link_to_journey(
                                sop,
                                parent_sop_id=main_backbone.get("sop_id", f"{main_journey_name}_sop"),
                                parent_node_id=parent_node_id,
                                is_edge_case=True,
                            )
                        
                        sop = _fix_branch_sop_transitions(sop)
                        
                        target = agent_root / "02_journeys" / journey_name / "sop.json"
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_text(json.dumps(sop, ensure_ascii=False, indent=2), encoding="utf-8")
                        assembled_files.append(str(target))
                        
                        if parent_node_id:
                            if parent_node_id not in edge_journey_map:
                                edge_journey_map[parent_node_id] = []
                            edge_journey_map[parent_node_id].append(journey_name)
        
        if main_backbone:
            main_journey_sop = _build_main_journey_sop(
                main_backbone,
                main_journey_name,
                branch_journey_map,
                edge_journey_map,
            )
            main_journey_dir = agent_root / "02_journeys" / main_journey_name
            main_journey_dir.mkdir(parents=True, exist_ok=True)
            
            main_sop_file = main_journey_dir / "sop.json"
            main_sop_file.write_text(json.dumps(main_journey_sop, ensure_ascii=False, indent=2), encoding="utf-8")
            assembled_files.append(str(main_sop_file))
            _append_log(f"Generated main journey sop: {main_sop_file}")
            
            main_guidelines = _build_main_journey_guidelines(main_journey_name, global_guidelines_data)
            main_guidelines_file = main_journey_dir / "sop_guidelines.json"
            main_guidelines_file.write_text(json.dumps(main_guidelines, ensure_ascii=False, indent=2), encoding="utf-8")
            assembled_files.append(str(main_guidelines_file))
            _append_log(f"Generated main journey guidelines: {main_guidelines_file}")
        else:
            integration_issues.append("Step2主SOP主干不存在，跳过主Journey生成")
        
        metadata_out = agent_root / "00_agent_base" / "agent_metadata.json"
        metadata_payload = {
            "agent_id": f"{agent_name}_001",
            "agent_name": agent_name,
            "agent_description": (context.get("business_desc") or "")[:300],
            "default_language": "zh-CN",
            "default_priority": 5,
            "conversation_timeout": 3600,
            "playground_port": 8801,
            "remark": "Generated by mining_agents step7 config_assembly",
        }
        metadata_out.write_text(json.dumps(metadata_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        assembled_files.append(str(metadata_out))
        
        observability_out = agent_root / "00_agent_base" / "agent_observability.json"
        observability_payload = {
            "agent_id": f"{agent_name}_001",
            "observability": {
                "enabled": True,
                "track_metrics": ["response_time", "resolution_rate", "fallback_rate"],
                "log_level": "INFO",
            },
        }
        observability_out.write_text(json.dumps(observability_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        assembled_files.append(str(observability_out))
        
        if all_canned_responses:
            seen_ids = set()
            unique_canned_responses = []
            for cr in all_canned_responses:
                cr_id = cr.get("canned_response_id", "")
                if cr_id and cr_id not in seen_ids:
                    seen_ids.add(cr_id)
                    unique_canned_responses.append(cr)
            
            canned_responses_out = agent_root / "01_agent_rules" / "agent_canned_responses.json"
            canned_responses_payload = {
                "agent_id": f"{agent_name}_001",
                "remark": f"{agent_name} Agent专属全局模板话术，跨所有SOP生效",
                "agent_canned_responses": unique_canned_responses,
            }
            canned_responses_out.write_text(json.dumps(canned_responses_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            assembled_files.append(str(canned_responses_out))
            _append_log(f"Generated agent canned responses: {canned_responses_out} ({len(unique_canned_responses)} items)")
        
        assembly_report_lines = [
            "# Step 7: 配置组装报告",
            "",
            f"- 时间: {datetime.now().isoformat()}",
            f"- 输出目录: `{parlant_root}`",
            f"- Agent: `{agent_name}`",
            f"- 主Journey: `{main_journey_name}`",
            f"- 整合文件数: {len(assembled_files)}",
            f"- 问题数: {len(integration_issues)}",
            "",
            "## 整合来源",
            "",
            f"- Step2目录: `{step2_dir}`",
            f"- Step3目录: `{step3_dir}`",
            f"- Step4目录: `{step4_dir}`",
            f"- Step5目录: `{step5_dir if step5_dir.exists() else '不存在'}`",
            f"- Step6目录: `{step6_dir if step6_dir.exists() else '不存在'}`",
            "",
            "## Journey链接关系",
            "",
            f"- 主Journey: `{main_journey_name}`",
            f"- 分支Journey数: {sum(len(v) for v in branch_journey_map.values())}",
            f"- 边缘Journey数: {sum(len(v) for v in edge_journey_map.values())}",
            "",
            "## 整合产物",
            "",
        ] + [f"- `{p}`" for p in assembled_files]
        
        if integration_issues:
            assembly_report_lines.extend([
                "",
                "## 整合问题",
                "",
            ] + [f"- {x}" for x in integration_issues])
        
        step7_report = output_dir / "step7_assembly_report.md"
        write_markdown("\n".join(assembly_report_lines) + "\n", str(step7_report))
        
        _append_archive(
            "output_written",
            {
                "assembled_files_count": len(assembled_files),
                "integration_issues_count": len(integration_issues),
                "parlant_root": str(parlant_root),
                "main_journey_name": main_journey_name,
                "branch_journey_count": sum(len(v) for v in branch_journey_map.values()),
                "edge_journey_count": sum(len(v) for v in edge_journey_map.values()),
            },
        )
        _append_log("Step7 completed")
        
        return {
            "output_files": [str(step7_report), str(parlant_root)] + assembled_files,
            "parlant_config_package": str(parlant_root),
            "metadata": {
                "step": 8,
                "agent_name": agent_name,
                "main_journey_name": main_journey_name,
                "assembled_files_count": len(assembled_files),
                "integration_issues_count": len(integration_issues),
            },
        }
    except Exception as e:
        _append_log(f"Step7 failed: {type(e).__name__}: {e}")
        _append_archive(
            "error",
            {"error": f"{type(e).__name__}: {e}", "traceback": traceback.format_exc()},
        )
        raise
