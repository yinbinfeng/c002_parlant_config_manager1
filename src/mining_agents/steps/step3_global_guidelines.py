#!/usr/bin/env python3
"""
step3_global_guidelines.py
文件格式: Python 源码

Step 3（v2）: 全局 guideline 生成（Agent 全局规则）
- 基于 Step2 的宏观目标（global_objective / core_goal）与业务描述
- 强制使用 Deep Research（由 GlobalRulesAgent 提示词约束）
- 输出 Parlant 工程化格式：agent_guidelines.json（仅全局 guideline，不生成 SOP/分支）
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict
import os
import re
import asyncio

from json_repair import repair_json

from ..utils.logger import logger


def _build_guidelines_fallback(business_desc: str) -> Dict[str, Any]:
    """Fallback生成基础guidelines。
    
    当Agent执行失败时，使用模板填空模式生成基础guidelines。
    """
    logger.warning("【FALLBACK】Step3使用fallback生成全局规则")
    
    scene_hint = "业务咨询"
    m = re.search(r"(保险|医疗|电商|客服|预约|理赔|投诉|退货|改签|营销)", business_desc or "")
    if m:
        scene_hint = m.group(1)
    
    return {
        "agent_id": "agent_001",
        "agent_name": "fallback_agent",
        "remark": f"Step3 fallback生成（{scene_hint}场景），未经过Agent定制化",
        "fallback_source": "template_fill_mode",
        "fallback_warning": "此全局规则由fallback模板生成，未根据业务特点深度定制",
        "agent_guidelines": [
            {
                "guideline_id": "global_greeting_001",
                "scope": "global",
                "condition": "会话开始，用户发起对话",
                "action": f"友好问候，确认{scene_hint}咨询意图，告知客服身份",
                "priority": 10,
                "composition_mode": "FLUID",
                "bind_canned_response_ids": [],
                "exclusions": [],
                "dependencies": [],
            },
            {
                "guideline_id": "global_clarification_002",
                "scope": "global",
                "condition": "用户意图不清晰或信息不足",
                "action": "使用开放式问题收集关键信息，避免预设答案引导",
                "priority": 8,
                "composition_mode": "FLUID",
                "bind_canned_response_ids": [],
                "exclusions": [],
                "dependencies": [],
            },
            {
                "guideline_id": "global_compliance_003",
                "scope": "global",
                "condition": "涉及敏感信息或合规要求",
                "action": "提供合规披露，说明信息用途，获取必要授权",
                "priority": 9,
                "composition_mode": "FLUID",
                "bind_canned_response_ids": [],
                "exclusions": [],
                "dependencies": [],
            },
            {
                "guideline_id": "global_closure_004",
                "scope": "global",
                "condition": "用户表示结束会话或问题已解决",
                "action": "总结关键结论，提供后续指引，礼貌结束",
                "priority": 7,
                "composition_mode": "FLUID",
                "bind_canned_response_ids": [],
                "exclusions": [],
                "dependencies": [],
            },
            {
                "guideline_id": "global_escalation_005",
                "scope": "global",
                "condition": "用户强烈投诉或要求人工服务",
                "action": "真诚道歉，提供升级渠道，确保用户知情",
                "priority": 10,
                "composition_mode": "FLUID",
                "bind_canned_response_ids": [],
                "exclusions": [],
                "dependencies": [],
            },
        ],
    }


def _build_glossary_fallback(business_desc: str) -> Dict[str, Any]:
    """Fallback生成基础术语库。"""
    import re
    logger.warning("【FALLBACK】Step3使用fallback生成术语库")
    
    scene_hint = "业务咨询"
    m = re.search(r"(保险|医疗|电商|客服|预约|理赔|投诉|退货|改签|营销)", business_desc or "")
    if m:
        scene_hint = m.group(1)
    
    return {
        "agent_id": "agent_001",
        "remark": f"Step3 fallback术语库（{scene_hint}场景）",
        "fallback_source": "template_fill_mode",
        "terms": [
            {
                "term_id": "term_001",
                "name": scene_hint,
                "description": f"本次对话涉及的{scene_hint}业务场景",
                "synonyms": [],
                "language": "zh-CN",
            },
        ],
    }


def _build_observations_fallback(business_desc: str) -> Dict[str, Any]:
    """Fallback生成全局observation。
    
    Observation是只有condition没有action的guideline，用于建立规则之间的依赖关系。
    """
    import re
    logger.warning("【FALLBACK】Step3使用fallback生成全局observation")
    
    scene_hint = "业务咨询"
    m = re.search(r"(保险|医疗|电商|客服|预约|理赔|投诉|退货|改签|营销)", business_desc or "")
    if m:
        scene_hint = m.group(1)
    
    prefix = "global"
    return {
        "agent_id": "agent_001",
        "remark": f"Step3 fallback全局观测（{scene_hint}场景），作为规则依赖的前置条件",
        "fallback_source": "template_fill_mode",
        "agent_observations": [
            {
                "observation_id": f"{prefix}_obs_user_angry_001",
                "condition": f"用户表达不满、愤怒、抱怨，使用负面情绪词汇（如投诉、没用、生气），在{scene_hint}场景中表现出不耐烦",
                "remark": "观测用户是否处于负面情绪状态，用于后续安抚规则的依赖",
            },
            {
                "observation_id": f"{prefix}_obs_user_requests_human_001",
                "condition": f"用户要求转人工、找客服、对自动回复不满意、要求真人对接，在{scene_hint}场景中明确要求人工服务",
                "remark": "观测用户是否有转人工需求，用于后续转人工规则的依赖",
            },
            {
                "observation_id": f"{prefix}_obs_user_intent_unclear_001",
                "condition": f"用户意图不清晰、需求模糊、无法确定具体目标，在{scene_hint}场景中表达不明确",
                "remark": "观测用户意图是否清晰。用于后续澄清规则的依赖",
            },
            {
                "observation_id": f"{prefix}_obs_user_refuse_001",
                "condition": f"用户明确拒绝、表示不需要、要求停止，在{scene_hint}场景中表达拒绝意向",
                "remark": "观测用户是否有拒绝意向。用于后续挽留或结束规则的依赖",
            },
        ],
    }


async def step3_global_guidelines_handler(context: Dict[str, Any], orchestrator) -> Dict[str, Any]:
    logger.info("Step 3(v2): generating global guidelines (agent-level)")
    mock_mode = bool(context.get("mock_mode", True))

    # 回填 Step2 产物
    output_base_dir = Path(context.get("output_base_dir", Path(context.get("output_dir", "./output")).parent))
    step2_dir = output_base_dir / "step2_objective_alignment_main_sop"
    step2_result_file = step2_dir / "result.json"
    if step2_result_file.exists():
        step2_result = repair_json(step2_result_file.read_text(encoding="utf-8"), return_objects=True)
        context.setdefault("global_objective", step2_result.get("global_objective", ""))
        context.setdefault("core_goal", (step2_result.get("business_objectives") or {}).get("core_goal", ""))
        context.setdefault("main_sop_backbone", step2_result.get("main_sop_backbone", {}))
        context.setdefault("structured_requirements", step2_result.get("structured_requirements", {}))
        context.setdefault("step2_canned_responses", step2_result.get("step2_canned_responses", {}))

    output_dir = Path(context.get("output_dir", "./output/step3_global_rules_and_glossary"))
    output_dir.mkdir(parents=True, exist_ok=True)

    # v2 Step3: GlobalRulesAgent + GlossaryAgent（可选并行）
    await orchestrator.initialize_agent(agent_type="GlobalRulesAgent", agent_name="GlobalRulesAgent")
    await orchestrator.initialize_agent(agent_type="GlossaryAgent", agent_name="GlossaryAgent")

    agent_ctx = {
        "business_desc": context.get("business_desc", ""),
        "structured_requirements": context.get("structured_requirements", {}),
        "step1_structured_requirements": context.get("structured_requirements", {}),
        "core_goal": context.get("core_goal", context.get("business_desc", "")[:200]),
        "industry": context.get("industry", "通用"),
        "global_objective": context.get("global_objective", ""),
        "main_sop_backbone": context.get("main_sop_backbone", {}),
        "mock_mode": context.get("mock_mode", True),
        "output_dir": str(output_dir),
        "step_num": context.get("step_num"),
        # 兼容旧字段：本步骤不再依赖 step3_guidelines/workflow_output_files
        "step3_guidelines": [],
        "workflow_output_files": [],
    }

    glossary_ctx = {
        "business_desc": context.get("business_desc", ""),
        "step2_atomic_tasks": context.get("atomic_tasks", context.get("step2_atomic_tasks", [])) or [],
        "atomic_tasks": context.get("atomic_tasks", []) or [],
        "step1_structured_requirements": context.get("structured_requirements", {}),
        "structured_requirements": context.get("structured_requirements", {}),
        "core_goal": context.get("core_goal", context.get("business_desc", "")[:200]),
        "industry": context.get("industry", "通用"),
        "mock_mode": context.get("mock_mode", True),
        "glossary_name": "master",
        "output_dir": str(output_dir),
        "step_num": context.get("step_num"),
    }

    # 可选并行：GlobalRulesAgent ‖ GlossaryAgent
    concurrency_cfg = ((context.get("config") or {}).get("concurrency") or getattr(orchestrator, "config", {}).get("system_config", {}).get("concurrency", {}) or {})
    enable_parallel = bool(concurrency_cfg.get("enable_step3_globalrules_glossary_parallel", False))
    
    business_desc = context.get("business_desc", "")
    guidelines_fallback_used = False
    glossary_fallback_used = False
    
    try:
        if enable_parallel:
            logger.info("Step3: running GlobalRulesAgent and GlossaryAgent in parallel (config enabled)")
            result, glossary_result = await asyncio.gather(
                orchestrator.execute_agent(
                    agent_name="GlobalRulesAgent",
                    task="基于宏观目标与业务描述生成精简的全局 Guideline（Parlant格式），并输出 Deep Research 依据",
                    context=agent_ctx,
                ),
                orchestrator.execute_agent(
                    agent_name="GlossaryAgent",
                    task="基于宏观目标与业务描述生成全局术语库（Parlant Glossary 格式），并输出 Deep Research 依据",
                    context=glossary_ctx,
                ),
            )
        else:
            result = await orchestrator.execute_agent(
                agent_name="GlobalRulesAgent",
                task="基于宏观目标与业务描述生成精简的全局 Guideline（Parlant格式），并输出 Deep Research 依据",
                context=agent_ctx,
            )
            glossary_result = await orchestrator.execute_agent(
                agent_name="GlossaryAgent",
                task="基于宏观目标与业务描述生成全局术语库（Parlant Glossary 格式），并输出 Deep Research 依据",
                context=glossary_ctx,
            )
    except Exception as e:
        logger.warning(f"Step3 Agent执行失败: {e}，使用fallback策略")
        result = None
        glossary_result = None

    global_rules = (result or {}).get("global_rules", {})
    # 兼容：agent 可能直接返回 dict（少一层包装）
    if isinstance(global_rules, dict) and ("agent_guidelines" in global_rules or "agent_id" in global_rules):
        guidelines_payload = global_rules
    else:
        guidelines_payload = result.get("global_rules", global_rules) if isinstance(result, dict) else {}
    
    # 检查guidelines是否有效，无效则使用fallback
    if not guidelines_payload or not isinstance(guidelines_payload, dict):
        logger.warning("Step3全局规则生成失败，使用fallback模板")
        guidelines_payload = _build_guidelines_fallback(business_desc)
        guidelines_fallback_used = True
    elif not guidelines_payload.get("agent_guidelines"):
        logger.warning("Step3全局规则缺少agent_guidelines，使用fallback模板")
        guidelines_payload = _build_guidelines_fallback(business_desc)
        guidelines_fallback_used = True
    
    if guidelines_fallback_used:
        logger.warning("【FALLBACK】Step3全局规则使用了fallback模板")

    guidelines_file = output_dir / "agent_guidelines.json"
    import json

    guidelines_file.write_text(json.dumps(guidelines_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # Step2 → Step3：可选的全局 canned responses（随全局 guideline 一并输出）
    canned_payload = context.get("step2_canned_responses") or {}
    canned_file = output_dir / "agent_canned_responses.json"
    if isinstance(canned_payload, dict) and (canned_payload.get("agent_canned_responses") or []):
        canned_file.write_text(json.dumps(canned_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # Glossary master（强制落盘为固定文件名，便于后续步骤引用）
    glossary_payload = (glossary_result or {}).get("glossary_terms", (glossary_result or {}).get("glossary", {}))
    if not isinstance(glossary_payload, dict):
        glossary_payload = {}
    
    # 检查glossary是否有效，无效则使用fallback
    if not glossary_payload or not glossary_payload.get("terms"):
        logger.warning("Step3术语库生成失败，使用fallback模板")
        glossary_payload = _build_glossary_fallback(business_desc)
        glossary_fallback_used = True
    
    if glossary_fallback_used:
        logger.warning("【FALLBACK】Step3术语库使用了fallback模板")
    
    glossary_master_file = output_dir / "step3_glossary_master.json"
    glossary_master_file.write_text(json.dumps(glossary_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # 生成全局 observation（用于建立规则依赖关系）
    observations_payload = None
    observations_fallback_used = False
    
    # 尝试从 agent 结果中提取 observations
    if result and isinstance(result, dict):
        observations_payload = result.get("agent_observations") or result.get("global_rules", {}).get("agent_observations")
    
    # 如果 agent 没有生成 observations，使用 fallback
    if not observations_payload or not isinstance(observations_payload, dict):
        logger.warning("Step3全局observation生成失败，使用fallback模板")
        observations_payload = _build_observations_fallback(business_desc)
        observations_fallback_used = True
    
    if observations_fallback_used:
        logger.warning("【FALLBACK】Step3全局observation使用了fallback模板")
    
    observations_file = output_dir / "agent_observations.json"
    observations_file.write_text(json.dumps(observations_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # 轻量存在性校验
    if not os.path.exists(guidelines_file):
        raise FileNotFoundError(f"Step3 guidelines file not written: {guidelines_file}")
    if not os.path.exists(glossary_master_file):
        raise FileNotFoundError(f"Step3 glossary master file not written: {glossary_master_file}")
    if not os.path.exists(observations_file):
        raise FileNotFoundError(f"Step3 observations file not written: {observations_file}")

    # Step3 合规校验（v2 要求：输出后进入 ComplianceCheckAgent）
    await orchestrator.initialize_agent(agent_type="ComplianceCheckAgent", agent_name="ComplianceCheckAgent")
    compliance_ctx = {
        "stage": "step3_global_guidelines",
        "output_dir": str(output_dir),
        "step_num": context.get("step_num"),
        "files": [
            str(guidelines_file),
            str(glossary_master_file),
            *( [str(canned_file)] if canned_file.exists() else [] ),
        ],
    }
    compliance_res = await orchestrator.execute_agent(
        agent_name="ComplianceCheckAgent",
        task="对 Step3 全局规则与术语库产物做合规与结构校验，一票否决不合格产物",
        context=compliance_ctx,
    )
    if isinstance(compliance_res, dict) and compliance_res.get("passed") is False:
        raise ValueError(f"Step3 compliance check failed: {((compliance_res.get('compliance_report') or {}).get('issues') or [])[:5]}")

    return {
        "agent_guidelines": guidelines_payload,
        "agent_observations": observations_payload,
        "glossary_master": glossary_payload,
        "output_files": [
            str(guidelines_file),
            str(glossary_master_file),
            str(observations_file),
            *( [str(canned_file)] if canned_file.exists() else [] ),
            *(((compliance_res or {}).get("output_files")) if isinstance(compliance_res, dict) else []),
        ],
        "metadata": {
            "guidelines_count": len((guidelines_payload or {}).get("agent_guidelines", []) or []),
            "observations_count": len((observations_payload or {}).get("agent_observations", []) or []),
            "glossary_terms_count": len((glossary_payload or {}).get("terms", []) or []),
            "fallback_info": {
                "guidelines_fallback_used": guidelines_fallback_used,
                "glossary_fallback_used": glossary_fallback_used,
                "observations_fallback_used": observations_fallback_used,
            },
        },
    }

