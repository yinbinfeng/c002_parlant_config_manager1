#!/usr/bin/env python3
"""
step4_user_profiles.py
文件格式: Python 源码

Step 4（v2）: 用户画像生成（可与 Step3 并行）
- 基于 Step2 的宏观目标（global_objective / core_goal）与业务描述
- 强制使用 Deep Research（由 UserProfileAgent 提示词约束）
- 输出工程化格式：agent_user_profiles.json
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import os
import json
import re

from json_repair import repair_json

from ..utils.logger import logger


def _build_user_profiles_fallback(business_desc: str) -> Dict[str, Any]:
    """Fallback生成基础用户画像。
    
    根据业务场景生成更全面的用户分群和画像。
    """
    logger.warning("【FALLBACK】Step4使用fallback生成用户画像")
    
    scene_hint = "业务咨询"
    m = re.search(r"(保险|医疗|电商|客服|预约|理赔|投诉|退货|改签|营销|挽留)", business_desc or "")
    if m:
        scene_hint = m.group(1)
    
    is_insurance = "保险" in business_desc or "insurance" in business_desc.lower()
    is_retention = "挽留" in business_desc or "续保" in business_desc or "retention" in business_desc.lower()
    is_outbound = "外呼" in business_desc or "outbound" in business_desc.lower()
    
    if is_insurance and (is_retention or is_outbound):
        return {
            "agent_id": "insurance_outbound_agent_001",
            "remark": f"Step4 fallback用户画像（{scene_hint}场景），用于分支适配与个性化服务策略",
            "fallback_source": "template_fill_mode",
            "fallback_warning": "此用户画像由fallback模板生成，已根据业务特点定制基础分群",
            "user_segments": [
                {
                    "segment_id": "high_churn_risk",
                    "segment_name": "高流失风险用户",
                    "description": "出现明显拒绝/挂断倾向，需要快速合规挽留与简洁沟通",
                    "definition": {"tags": ["high_churn_risk"], "metadata_rules": {}},
                    "behavior_patterns": ["不耐烦", "对推销敏感", "倾向快速结束通话"],
                    "preferred_journeys": [],
                    "special_guidelines": [],
                    "custom_variables": {"patience_required": "high", "detail_level": "low"},
                },
                {
                    "segment_id": "needs_clarification",
                    "segment_name": "需求未明确用户",
                    "description": "对保险需求与顾虑点不清晰，需要结构化澄清后再推进",
                    "definition": {"tags": ["needs_clarification"], "metadata_rules": {}},
                    "behavior_patterns": ["问题多", "需要解释", "对条款敏感"],
                    "preferred_journeys": [],
                    "special_guidelines": [],
                    "custom_variables": {"detail_level": "medium"},
                },
                {
                    "segment_id": "value_seeker",
                    "segment_name": "价值导向用户",
                    "description": "愿意听取方案但关注价值与可信度，需要明确利益点与合规披露",
                    "definition": {"tags": ["value_seeker"], "metadata_rules": {}},
                    "behavior_patterns": ["会比较方案", "关注保障范围", "在意可信度与口碑"],
                    "preferred_journeys": [],
                    "special_guidelines": [],
                    "custom_variables": {"detail_level": "high"},
                },
                {
                    "segment_id": "ready_to_proceed",
                    "segment_name": "意向明确用户",
                    "description": "已有明确投保意向或续保意愿，需要快速推进流程",
                    "definition": {"tags": ["ready_to_proceed"], "metadata_rules": {}},
                    "behavior_patterns": ["主动询问", "确认细节", "准备签约"],
                    "preferred_journeys": [],
                    "special_guidelines": [],
                    "custom_variables": {"detail_level": "high", "urgency": "high"},
                },
            ],
            "personas": [
                {
                    "persona_id": "persona_001",
                    "persona_name": "时间紧张的上班族",
                    "segment_id": "high_churn_risk",
                    "demographics": "25-40 岁，上班族",
                    "goals": "尽快结束通话、不被打扰",
                    "pain_points": "对冗长推销反感、担心信息泄露",
                    "behavior_patterns": ["打断", "拒绝", "挂断倾向"],
                    "typical_dialogues": ["我现在很忙", "不用了谢谢", "别再打了"],
                    "parlant_mapping": {"tags": ["high_churn_risk"], "variables": [], "journeys": [], "guidelines": []},
                },
                {
                    "persona_id": "persona_002",
                    "persona_name": "谨慎比较的家庭责任人",
                    "segment_id": "value_seeker",
                    "demographics": "30-55 岁，家庭责任人",
                    "goals": "了解保障与费用，做出稳妥选择",
                    "pain_points": "担心误导、担心条款陷阱",
                    "behavior_patterns": ["反复确认", "询问条款与例外", "要求书面材料"],
                    "typical_dialogues": ["能把条款发我看吗？", "不赔的情况有哪些？", "有没有官方资料？"],
                    "parlant_mapping": {"tags": ["value_seeker"], "variables": [], "journeys": [], "guidelines": []},
                },
                {
                    "persona_id": "persona_003",
                    "persona_name": "需求模糊的新客户",
                    "segment_id": "needs_clarification",
                    "demographics": "20-35 岁，首次接触保险",
                    "goals": "了解保险能解决什么问题",
                    "pain_points": "不懂专业术语、不知道问什么",
                    "behavior_patterns": ["沉默", "简单回应", "需要引导提问"],
                    "typical_dialogues": ["我不太懂保险", "你们有什么产品？", "能简单说说吗？"],
                    "parlant_mapping": {"tags": ["needs_clarification"], "variables": [], "journeys": [], "guidelines": []},
                },
            ],
        }
    
    return {
        "agent_id": "fallback_agent_001",
        "remark": f"Step4 fallback用户画像（{scene_hint}场景），用于分支适配与个性化服务策略",
        "fallback_source": "template_fill_mode",
        "fallback_warning": "此用户画像由fallback模板生成，已根据业务特点定制基础分群",
        "user_segments": [
            {
                "segment_id": "high_churn_risk",
                "segment_name": "高流失风险用户",
                "description": f"出现明显拒绝/退出倾向，需要快速响应与简洁沟通",
                "definition": {"tags": ["high_churn_risk"], "metadata_rules": {}},
                "behavior_patterns": ["不耐烦", "倾向快速结束"],
                "preferred_journeys": [],
                "special_guidelines": [],
                "custom_variables": {"patience_required": "high"},
            },
            {
                "segment_id": "needs_clarification",
                "segment_name": "需求未明确用户",
                "description": f"对{scene_hint}需求不清晰，需要结构化澄清",
                "definition": {"tags": ["needs_clarification"], "metadata_rules": {}},
                "behavior_patterns": ["问题多", "需要解释"],
                "preferred_journeys": [],
                "special_guidelines": [],
                "custom_variables": {"detail_level": "medium"},
            },
            {
                "segment_id": "value_seeker",
                "segment_name": "价值导向用户",
                "description": f"关注价值与可信度，需要明确利益点",
                "definition": {"tags": ["value_seeker"], "metadata_rules": {}},
                "behavior_patterns": ["比较方案", "关注细节"],
                "preferred_journeys": [],
                "special_guidelines": [],
                "custom_variables": {"detail_level": "high"},
            },
        ],
        "personas": [
            {
                "persona_id": "persona_001",
                "persona_name": "时间紧张用户",
                "segment_id": "high_churn_risk",
                "demographics": "忙碌的用户群体",
                "goals": "尽快解决问题",
                "pain_points": "对冗长流程反感",
                "behavior_patterns": ["打断", "拒绝"],
                "typical_dialogues": ["我现在很忙", "不用了谢谢"],
                "parlant_mapping": {"tags": ["high_churn_risk"], "variables": [], "journeys": [], "guidelines": []},
            },
            {
                "persona_id": "persona_002",
                "persona_name": "谨慎决策用户",
                "segment_id": "value_seeker",
                "demographics": "注重细节的用户群体",
                "goals": "了解完整信息后做决定",
                "pain_points": "担心信息不透明",
                "behavior_patterns": ["反复确认", "询问细节"],
                "typical_dialogues": ["能详细说说吗？", "有没有书面材料？"],
                "parlant_mapping": {"tags": ["value_seeker"], "variables": [], "journeys": [], "guidelines": []},
            },
        ],
    }


async def step4_user_profiles_handler(context: Dict[str, Any], orchestrator) -> Dict[str, Any]:
    logger.info("Step 4(v2): generating user profiles (agent user segments + personas)")
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

    output_dir = Path(context.get("output_dir", "./output/step4_user_profile"))
    output_dir.mkdir(parents=True, exist_ok=True)

    # Deep Research（用于画像设计的依据；mock 模式下仍会返回 mock 报告文本）
    deep_research_tool = (
        orchestrator.get_tool("deep_research")
        if hasattr(orchestrator, "list_tools") and "deep_research" in (orchestrator.list_tools() or [])
        else None
    )
    if deep_research_tool:
        try:
            business_desc_for_query = " ".join(str(context.get("business_desc", "")).split())
            q = (
                "你是用户画像研究员。请围绕该业务场景产出“可落地分群+persona”研究资料，"
                "重点包括：分群维度、行为信号、可判定标签、常见异议/痛点、合规边界。"
                f" 行业={context.get('industry','通用')}；业务描述={business_desc_for_query}"
            )
            report = await deep_research_tool.search(
                q,
                audit_output_dir=str(output_dir),
                caller_agent="Step4_UserProfiles",
                query_tag="step4_profiles",
            )
            reports_dir = output_dir / "step4_research_reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            (reports_dir / "report_01.md").write_text(str(report), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Step4 deep research failed: {e}")

    # Mock 模式：生成最小可用的画像配置，避免模型不稳定导致产物为空
    if mock_mode:
        logger.warning("【FALLBACK】Step4 mock_mode使用预定义用户画像模板")
        agent_id = "insurance_outbound_agent_001"
        payload = {
            "agent_id": agent_id,
            "remark": "外呼营销挽留场景用户画像（MOCK），用于分支适配与个性化服务策略",
            "fallback_source": "mock_mode_template",
            "fallback_warning": "此用户画像由mock模式生成，未根据业务特点定制",
            "user_segments": [
                {
                    "segment_id": "high_churn_risk",
                    "segment_name": "高流失风险用户",
                    "description": "出现明显拒绝/挂断倾向，需要快速合规挽留与简洁沟通",
                    "definition": {"tags": ["high_churn_risk"], "metadata_rules": {}},
                    "behavior_patterns": ["不耐烦", "对推销敏感", "倾向快速结束通话"],
                    "preferred_journeys": [],
                    "special_guidelines": [],
                    "custom_variables": {"patience_required": "high", "detail_level": "low"},
                },
                {
                    "segment_id": "needs_clarification",
                    "segment_name": "需求未明确用户",
                    "description": "对保险需求与顾虑点不清晰，需要结构化澄清后再推进",
                    "definition": {"tags": ["needs_clarification"], "metadata_rules": {}},
                    "behavior_patterns": ["问题多", "需要解释", "对条款敏感"],
                    "preferred_journeys": [],
                    "special_guidelines": [],
                    "custom_variables": {"detail_level": "medium"},
                },
                {
                    "segment_id": "value_seeker",
                    "segment_name": "价值导向用户",
                    "description": "愿意听取方案但关注价值与可信度，需要明确利益点与合规披露",
                    "definition": {"tags": ["value_seeker"], "metadata_rules": {}},
                    "behavior_patterns": ["会比较方案", "关注保障范围", "在意可信度与口碑"],
                    "preferred_journeys": [],
                    "special_guidelines": [],
                    "custom_variables": {"detail_level": "high"},
                },
            ],
            "personas": [
                {
                    "persona_id": "persona_001",
                    "persona_name": "时间紧张的上班族",
                    "segment_id": "high_churn_risk",
                    "demographics": "25-40 岁，上班族",
                    "goals": "尽快结束通话、不被打扰",
                    "pain_points": "对冗长推销反感、担心信息泄露",
                    "behavior_patterns": ["打断", "拒绝", "挂断倾向"],
                    "typical_dialogues": ["我现在很忙", "不用了谢谢", "别再打了"],
                    "parlant_mapping": {"tags": ["high_churn_risk"], "variables": [], "journeys": [], "guidelines": []},
                },
                {
                    "persona_id": "persona_002",
                    "persona_name": "谨慎比较的家庭责任人",
                    "segment_id": "value_seeker",
                    "demographics": "30-55 岁，家庭责任人",
                    "goals": "了解保障与费用，做出稳妥选择",
                    "pain_points": "担心误导、担心条款陷阱",
                    "behavior_patterns": ["反复确认", "询问条款与例外", "要求书面材料"],
                    "typical_dialogues": ["能把条款发我看吗？", "不赔的情况有哪些？", "有没有官方资料？"],
                    "parlant_mapping": {"tags": ["value_seeker"], "variables": [], "journeys": [], "guidelines": []},
                },
            ],
        }

        profiles_file = output_dir / "agent_user_profiles.json"
        profiles_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "user_profiles": payload,
            "output_files": [str(profiles_file)],
            "metadata": {"segments_count": len(payload["user_segments"]), "personas_count": len(payload["personas"])},
        }

    await orchestrator.initialize_agent(agent_type="UserProfileAgent", agent_name="UserProfileAgent")

    agent_ctx = {
        "business_desc": context.get("business_desc", ""),
        "structured_requirements": context.get("structured_requirements", {}),
        "core_goal": context.get("core_goal", context.get("business_desc", "")[:200]),
        "industry": context.get("industry", "通用"),
        "global_objective": context.get("global_objective", ""),
        "main_sop_backbone": context.get("main_sop_backbone", {}),
        "mock_mode": context.get("mock_mode", True),
        "output_dir": str(output_dir),
        "step_num": context.get("step_num"),
    }

    fallback_used = False
    try:
        result = await orchestrator.execute_agent(
            agent_name="UserProfileAgent",
            task="基于宏观目标与业务描述生成用户分群与典型画像（Parlant工程化格式），数量适中、可用于分支适配",
            context=agent_ctx,
        )
    except Exception as e:
        logger.warning(f"Step4 Agent执行失败: {e}，使用fallback策略")
        result = None

    user_profiles = (result or {}).get("user_profiles", {})
    if not isinstance(user_profiles, dict) or not user_profiles.get("user_segments"):
        logger.warning("Step4用户画像生成失败，使用fallback模板")
        user_profiles = _build_user_profiles_fallback(context.get("business_desc", ""))
        fallback_used = True
    
    if fallback_used:
        logger.warning("【FALLBACK】Step4用户画像使用了fallback模板")

    profiles_file = output_dir / "agent_user_profiles.json"
    profiles_file.write_text(json.dumps(user_profiles, ensure_ascii=False, indent=2), encoding="utf-8")

    if not os.path.exists(profiles_file):
        raise FileNotFoundError(f"Step4 profiles file not written: {profiles_file}")

    # Step4 合规校验（v2 要求：输出后进入 ComplianceCheckAgent）
    await orchestrator.initialize_agent(agent_type="ComplianceCheckAgent", agent_name="ComplianceCheckAgent")
    compliance_ctx = {
        "stage": "step4_user_profiles",
        "output_dir": str(output_dir),
        "step_num": context.get("step_num"),
        "files": [str(profiles_file)],
    }
    compliance_res = await orchestrator.execute_agent(
        agent_name="ComplianceCheckAgent",
        task="对 Step4 用户画像产物做合规与结构校验，一票否决不合格产物",
        context=compliance_ctx,
    )
    if isinstance(compliance_res, dict) and compliance_res.get("passed") is False:
        raise ValueError(
            f"Step4 compliance check failed: {((compliance_res.get('compliance_report') or {}).get('issues') or [])[:5]}"
        )

    return {
        "user_profiles": user_profiles,
        "output_files": [
            str(profiles_file),
            *(((compliance_res or {}).get("output_files")) if isinstance(compliance_res, dict) else []),
        ],
        "metadata": {
            "segments_count": len((user_profiles or {}).get("user_segments", []) or []),
            "personas_count": len((user_profiles or {}).get("personas", []) or []),
            "fallback_info": {
                "fallback_used": fallback_used,
                "fallback_source": user_profiles.get("fallback_source") if fallback_used else None,
            },
        },
    }

