#!/usr/bin/env python3
"""
step5_branch_sop_parallel.py
文件格式: Python 源码

Step 5（v2）: 二级分支 SOP 挖掘（核心优化点）
- 基于 Step2 的主干 SOP 节点，为每个节点派生“二级 Journey 子任务”（可选并发）
- 产出：二级 branch journey（5-10 个节点）、局部 guidelines、术语、工具、总结
- 规则要求：局部 guidelines 不应与 Step3 全局 guidelines 重复（做启发式剔除）
- 工程化：每个 node 独立目录，避免并发写冲突
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import asyncio
import json
import re

from json_repair import repair_json

from ..utils.logger import logger


def _norm_text(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def _ensure_list(x: Any) -> List[Any]:
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]


def _safe_id(text: str) -> str:
    t = re.sub(r"[^a-z0-9_]+", "_", (text or "").lower()).strip("_")
    return t or "id"


def _load_step2_result(context: Dict[str, Any]) -> Dict[str, Any]:
    output_base_dir = Path(context.get("output_base_dir", Path(context.get("output_dir", "./output")).parent))
    step2_dir = output_base_dir / "step2_objective_alignment_main_sop"
    step2_result_file = step2_dir / "result.json"
    if step2_result_file.exists():
        try:
            return repair_json(step2_result_file.read_text(encoding="utf-8"), return_objects=True) or {}
        except Exception:
            return {}
    return {}


def _load_global_guidelines(step3_dir: Path) -> Tuple[List[dict], List[str]]:
    """读取 Step3 agent_guidelines.json，返回 guidelines 列表与 action/condition 文本集合。"""
    file = step3_dir / "agent_guidelines.json"
    if not file.exists():
        return [], []
    try:
        data = repair_json(file.read_text(encoding="utf-8"), return_objects=True) or {}
    except Exception:
        return [], []
    gl = _ensure_list(data.get("agent_guidelines"))
    texts: List[str] = []
    for g in gl:
        if not isinstance(g, dict):
            continue
        texts.append(_norm_text(str(g.get("condition", ""))))
        texts.append(_norm_text(str(g.get("action", ""))))
    # 去空
    texts = [t for t in texts if t]
    return [g for g in gl if isinstance(g, dict)], texts


def _heuristic_dedupe_local_guidelines(local: List[dict], global_texts: List[str]) -> List[dict]:
    """启发式去重：若 local 的 condition 或 action 与全局完全相同（规范化后），则剔除。"""
    if not global_texts:
        return local
    global_set = set(global_texts)
    kept: List[dict] = []
    for g in local:
        if not isinstance(g, dict):
            continue
        c = _norm_text(str(g.get("condition", "")))
        a = _norm_text(str(g.get("action", "")))
        if c and c in global_set:
            continue
        if a and a in global_set:
            continue
        kept.append(g)
    return kept


@dataclass
class NodeTaskOutput:
    node_id: str
    node_name: str
    journey_file: Path
    guidelines_file: Path
    glossary_file: Path
    tools_file: Path
    summary_file: Path
    observations_file: Path
    skipped_by_model: bool = False
    skip_reason: str = ""


def _build_branch_journey_fallback(
    *,
    main_journey_name: str,
    node_id: str,
    node_name: str,
    business_desc: str,
) -> dict:
    """Fallback模板：当Agent动态生成失败时使用。
    
    注意：这是固化模板，输出中会标记fallback_source。
    """
    sop_id = f"{main_journey_name}__branch_{node_id}_{_safe_id(node_name)}_sop_001"
    states: List[dict] = [
        {
            "state_id": "branch_state_000",
            "state_name": "分支接管",
            "state_type": "chat",
            "instruction": f"当主干节点[{node_name}]出现偏离/阻塞/特殊需求时，接管并明确分支目的，保持合规与简洁。",
            "bind_guideline_ids": [],
            "transitions": [
                {
                    "target_state_id": "branch_state_001",
                    "condition": "用户已明确说出分支处理的具体原因（如：我想了解XX/我对XX有疑问/我需要XX帮助）",
                    "condition_examples": ["用户说：我想了解一下这个产品的细节", "用户说：我有个问题想问", "用户明确表达特定需求"],
                }
            ],
        },
        {
            "state_id": "branch_state_001",
            "state_name": "信息澄清",
            "state_type": "chat",
            "instruction": "补齐必要信息与约束条件，避免误导与过度承诺。",
            "bind_guideline_ids": [],
            "transitions": [
                {
                    "target_state_id": "branch_state_002",
                    "condition": "已获取用户的关键信息（至少包含：具体问题、期望结果、相关背景），且用户确认信息无误",
                    "condition_examples": ["用户回答了至少2个关键问题", "用户说：就这些了", "用户确认信息正确"],
                }
            ],
        },
        {
            "state_id": "branch_state_002",
            "state_name": "给出可执行方案",
            "state_type": "chat",
            "instruction": f"围绕业务场景给出 1 个优先方案 + 1 个备选方案（如适用），与[{business_desc[:40]}]一致。",
            "bind_guideline_ids": [],
            "transitions": [
                {
                    "target_state_id": "branch_state_003",
                    "condition": "用户已理解方案内容并表示倾向（接受/拒绝/需要更多时间考虑）",
                    "condition_examples": ["用户说：我选第一个方案", "用户说：我再考虑一下", "用户询问方案细节"],
                }
            ],
        },
        {
            "state_id": "branch_state_003",
            "state_name": "确认与风险提示",
            "state_type": "chat",
            "instruction": "再次确认关键点，给出必要的合规披露与风险提示，避免争议。",
            "bind_guideline_ids": [],
            "transitions": [
                {
                    "target_state_id": "branch_state_004",
                    "condition": "用户已确认理解风险提示，且分支问题已得到解决或用户明确表示可以继续主流程",
                    "condition_examples": ["用户说：好的我明白了", "用户说：没问题了，继续吧", "用户确认风险提示内容"],
                }
            ],
        },
        {
            "state_id": "branch_state_004",
            "state_name": "回归主干",
            "state_type": "chat",
            "instruction": "总结分支结论并回归主流程继续执行。",
            "is_end_state": True,
            "return_to_parent": True,
        },
    ]

    return {
        "sop_id": sop_id,
        "sop_type": "branch",
        "parent_sop_id": f"{main_journey_name}_sop_001",
        "parent_state_id": node_id,
        "sop_title": f"{node_name} 二级分支 Journey",
        "sop_description": f"挂载于主干节点[{node_name}]的二级分支流程（Step5 生成）",
        "trigger_conditions": [
            {
                "trigger": f"用户在[{node_name}]节点提出特定需求或问题，需要分支处理",
                "trigger_examples": [
                    "用户说：我想了解一下XX的细节",
                    "用户说：我有个问题想问",
                    "用户表达与当前节点相关的特殊需求",
                ],
            }
        ],
        "timeout": 900,
        "sop_states": states,
        "fallback_source": "hardcoded_template",  # 标识：完全固化模板
        "fallback_warning": "此分支SOP由固化模板生成，未根据业务特点定制",
    }


_BRANCH_SOP_FEW_SHOT_EXAMPLE = '''
【Few-Shot 示例：保险外呼营销挽留场景的分支SOP】

主节点：node_002 挂断风险监测与决策
分支SOP节点（5个）：
1. branch_state_000 分支接管：识别用户拒绝信号，启动挽留流程
   - transition condition: 用户明确表示拒绝或挂断倾向
   - condition_examples: ["用户说：不需要了", "用户说：没时间", "用户语速加快"]

2. branch_state_001 挽留话术执行：执行合规挽留话术
   - transition condition: 用户表示愿意继续倾听或明确拒绝
   - condition_examples: ["用户说：好吧你继续说", "用户说：真的不需要"]

3. branch_state_002 价值重申：强调服务价值与信息知情权
   - transition condition: 用户表示理解或继续询问
   - condition_examples: ["用户说：那你说说看", "用户询问具体内容"]

4. branch_state_003 异议处理：处理用户顾虑
   - transition condition: 用户异议得到解决或表示愿意继续
   - condition_examples: ["用户说：这个可以考虑", "用户说：还是算了"]

5. branch_state_004 回归主干：总结并回归主流程
   - is_end_state: true
   - return_to_parent: true

【节点抽象度原则】
- 每个分支节点代表一个"处理步骤"，不是"具体话术"
- 节点数量控制在5-10个
- transition condition必须可判定
'''


async def _generate_branch_journey_via_agent(
    *,
    main_journey_name: str,
    node_id: str,
    node_name: str,
    business_desc: str,
    orchestrator,
) -> dict:
    """通过Agent动态生成分支SOP。
    
    策略：
    1. 先让模型判断该主节点是否需要二级分支
    2. 如果需要，让模型生成完整JSON
    3. 如果不需要，返回空标记，跳过该节点
    4. 失败时使用模板填空模式
    5. 所有fallback输出都会标记fallback_source字段
    """
    
    prompt = f'''
请根据以下信息，判断是否需要为该主节点生成二级分支SOP。

## 业务描述
{business_desc}

## 主节点信息
- node_id: {node_id}
- node_name: {node_name}

## 判断标准
请根据以下标准判断是否需要生成二级分支：
1. 该主节点是否有复杂的子流程需要展开？（例如：需要多步骤处理、需要收集多个信息、需要多次确认）
2. 该主节点是否可能触发用户特殊需求或问题？（例如：用户可能需要详细解释、可能有异议需要处理）
3. 该主节点是否有明显的分支场景？（例如：成功/失败分支、同意/拒绝分支、不同选项分支）

如果以上条件都不满足，说明该主节点足够简单，不需要二级分支，请返回 need_branch: false。

## Few-Shot 示例
{_BRANCH_SOP_FEW_SHOT_EXAMPLE}

## 输出格式（JSON）
如果需要生成二级分支：
{{
  "need_branch": true,
  "reason": "需要二级分支的原因",
  "sop_title": "分支SOP标题",
  "sop_states": [
    {{
      "state_name": "节点名称",
      "instruction": "节点指令",
      "condition": "转换到下一节点的条件",
      "condition_examples": ["示例1", "示例2"]
    }}
  ]
}}

如果不需要生成二级分支：
{{
  "need_branch": false,
  "reason": "不需要二级分支的原因（例如：该节点流程简单，无需展开；该节点是终点节点，无需分支等）"
}}

## 重要提示
1. 节点数量：5-8个（严格控制）
2. 每个节点包含：state_name, instruction, condition, condition_examples
3. 最后一个节点不需要condition
4. 节点必须与主节点[{node_name}]的业务场景相关
5. condition必须可判定
6. 如果确实没有需要展开的内容，请诚实返回 need_branch: false，不要强行生成无意义的内容

请只输出JSON，不要输出其他内容。
'''

    try:
        await orchestrator.initialize_agent(agent_type="CoordinatorAgent", agent_name="BranchSOPGenerator")
        agent = orchestrator.agents.get("BranchSOPGenerator")
        if not agent:
            logger.warning("无法获取BranchSOPGenerator agent实例，使用fallback模板填空模式")
            return await _generate_branch_journey_via_fallback(
                main_journey_name=main_journey_name,
                node_id=node_id,
                node_name=node_name,
                business_desc=business_desc,
                agent=None,
            )
        
        response = await agent.call_llm(
            prompt=prompt,
            context={
                "business_desc": business_desc,
                "node_id": node_id,
                "node_name": node_name,
            },
        )
        
        if not response:
            logger.warning("Agent call_llm返回空响应，使用fallback模板填空模式")
            return await _generate_branch_journey_via_fallback(
                main_journey_name=main_journey_name,
                node_id=node_id,
                node_name=node_name,
                business_desc=business_desc,
                agent=agent,
            )
        
        sop_data = repair_json(response.strip(), return_objects=True)
        
        if not isinstance(sop_data, dict):
            logger.warning("Agent返回的结果不是有效JSON对象，使用fallback模板填空模式")
            return await _generate_branch_journey_via_fallback(
                main_journey_name=main_journey_name,
                node_id=node_id,
                node_name=node_name,
                business_desc=business_desc,
                agent=agent,
            )
        
        need_branch = sop_data.get("need_branch", True)
        if need_branch is False:
            reason = sop_data.get("reason", "模型判断不需要二级分支")
            logger.info(f"【模型决策】主节点[{node_name}]不需要二级分支，原因: {reason}")
            return {
                "sop_id": f"{main_journey_name}__branch_{node_id}_skipped",
                "sop_type": "branch",
                "parent_sop_id": f"{main_journey_name}_sop_001",
                "parent_state_id": node_id,
                "sop_title": f"{node_name} - 无需二级分支",
                "sop_description": f"模型判断该节点不需要二级分支: {reason}",
                "sop_states": [],
                "skipped_by_model": True,
                "skip_reason": reason,
            }
        
        if "sop_states" not in sop_data:
            logger.warning("Agent返回的结果不包含sop_states，使用fallback模板填空模式")
            return await _generate_branch_journey_via_fallback(
                main_journey_name=main_journey_name,
                node_id=node_id,
                node_name=node_name,
                business_desc=business_desc,
                agent=agent,
            )
        
        states = sop_data.get("sop_states", [])
        if not (5 <= len(states) <= 10):
            logger.warning(f"Agent生成的节点数量{len(states)}不在5-10范围内，使用fallback模板填空模式")
            return await _generate_branch_journey_via_fallback(
                main_journey_name=main_journey_name,
                node_id=node_id,
                node_name=node_name,
                business_desc=business_desc,
                agent=agent,
            )
        
        for i, state in enumerate(states):
            state["state_id"] = f"branch_state_{i:03d}"
            state["state_type"] = "chat"
            state["bind_guideline_ids"] = []
            if i == len(states) - 1:
                state["is_end_state"] = True
                state["return_to_parent"] = True
        
        sop_id = f"{main_journey_name}__branch_{node_id}_{_safe_id(node_name)}_sop_001"
        journey = {
            "sop_id": sop_id,
            "sop_type": "branch",
            "parent_sop_id": f"{main_journey_name}_sop_001",
            "parent_state_id": node_id,
            "sop_title": sop_data.get("sop_title", f"{node_name} 二级分支 Journey"),
            "sop_description": f"挂载于主干节点[{node_name}]的二级分支流程（Step5 Agent动态生成）",
            "trigger_conditions": [
                {
                    "trigger": f"用户在[{node_name}]节点提出特定需求或问题，需要分支处理",
                    "trigger_examples": ["用户表达特殊需求", "用户提出问题", "用户需要额外帮助"],
                }
            ],
            "timeout": 900,
            "sop_states": states,
            "fallback_source": None,  # 标识：非fallback生成
        }
        
        logger.info(f"Agent动态生成分支SOP成功，节点数: {len(states)}")
        return journey
        
    except Exception as e:
        logger.warning(f"Agent动态生成分支SOP失败: {e}，使用fallback模板填空模式")
        return await _generate_branch_journey_via_fallback(
            main_journey_name=main_journey_name,
            node_id=node_id,
            node_name=node_name,
            business_desc=business_desc,
            agent=orchestrator.agents.get("CoordinatorAgent") if orchestrator.agents else None,
        )


async def _generate_branch_journey_via_fallback(
    *,
    main_journey_name: str,
    node_id: str,
    node_name: str,
    business_desc: str,
    agent: Any = None,
) -> dict:
    """Fallback模板填空模式：让模型只填写关键字段。"""
    logger.warning("=" * 60)
    logger.warning(f"【FALLBACK模式】使用模板填空模式生成分支SOP - {node_name}")
    logger.warning("=" * 60)
    
    fallback_prompt = f'''
请根据以下信息，生成分支SOP的关键字段。

## 业务描述
{business_desc}

## 主节点
- node_name: {node_name}

## 任务
请生成5-6个分支SOP节点，每个节点只需要提供：
1. state_name: 节点名称（简洁，4-8个字）
2. instruction: 节点指令（一句话描述）
3. condition: 转换到下一节点的条件
4. condition_examples: 判定示例（1-2个）

## 输出格式（JSON数组）
[
  {{
    "state_name": "节点名称",
    "instruction": "节点指令",
    "condition": "转换条件",
    "condition_examples": ["示例1"]
  }}
]

注意：
- 节点数量控制在5-6个
- 最后一个节点不需要condition
- 只输出JSON数组
'''
    
    states_data = None
    
    if agent:
        try:
            response = await agent.call_llm(
                prompt=fallback_prompt,
                context={"business_desc": business_desc, "node_name": node_name},
            )
            if response:
                states_data = repair_json(response.strip(), return_objects=True)
        except Exception as e:
            logger.warning(f"Fallback模式LLM调用失败: {e}")
    
    if not states_data or not isinstance(states_data, list):
        logger.warning("Fallback模式LLM未返回有效数据，使用完全固化模板")
        return _build_branch_journey_fallback(
            main_journey_name=main_journey_name,
            node_id=node_id,
            node_name=node_name,
            business_desc=business_desc,
        )
    
    if not (5 <= len(states_data) <= 10):
        logger.warning(f"Fallback模式节点数量{len(states_data)}不在范围内，使用完全固化模板")
        return _build_branch_journey_fallback(
            main_journey_name=main_journey_name,
            node_id=node_id,
            node_name=node_name,
            business_desc=business_desc,
        )
    
    states = []
    for i, state_data in enumerate(states_data):
        if not isinstance(state_data, dict):
            continue
        state = {
            "state_id": f"branch_state_{i:03d}",
            "state_name": state_data.get("state_name", f"节点{i+1}"),
            "state_type": "chat",
            "instruction": state_data.get("instruction", ""),
            "bind_guideline_ids": [],
        }
        
        if i < len(states_data) - 1:
            state["transitions"] = [
                {
                    "target_state_id": f"branch_state_{i+1:03d}",
                    "condition": state_data.get("condition", ""),
                    "condition_examples": state_data.get("condition_examples", []),
                }
            ]
        else:
            state["is_end_state"] = True
            state["return_to_parent"] = True
        
        states.append(state)
    
    if len(states) < 5:
        logger.warning(f"Fallback模式有效节点不足5个，使用完全固化模板")
        return _build_branch_journey_fallback(
            main_journey_name=main_journey_name,
            node_id=node_id,
            node_name=node_name,
            business_desc=business_desc,
        )
    
    sop_id = f"{main_journey_name}__branch_{node_id}_{_safe_id(node_name)}_sop_001"
    journey = {
        "sop_id": sop_id,
        "sop_type": "branch",
        "parent_sop_id": f"{main_journey_name}_sop_001",
        "parent_state_id": node_id,
        "sop_title": f"{node_name} 二级分支 Journey",
        "sop_description": f"挂载于主干节点[{node_name}]的二级分支流程（Step5 Fallback模板填空模式）",
        "trigger_conditions": [
            {
                "trigger": f"用户在[{node_name}]节点提出特定需求或问题，需要分支处理",
                "trigger_examples": ["用户表达特殊需求", "用户提出问题"],
            }
        ],
        "timeout": 900,
        "sop_states": states,
        "fallback_source": "template_fill_mode",  # 标识：fallback模板填空模式
        "fallback_warning": "此分支SOP由fallback模板填空模式生成",
    }
    
    logger.warning(f"【FALLBACK模式】分支SOP生成完成，节点数: {len(states)}")
    
    return journey


def _build_local_guidelines(*, main_journey_name: str, node_id: str, node_name: str) -> dict:
    prefix = f"{_safe_id(main_journey_name)}_{_safe_id(node_id)}"
    cr_takeover = f"{prefix}_cr_takeover_001"
    cr_no_overpromise = f"{prefix}_cr_no_overpromise_002"
    cr_return_main = f"{prefix}_cr_return_main_003"
    cr_clarify_evidence = f"{prefix}_cr_clarify_evidence_004"
    cr_privacy_min = f"{prefix}_cr_privacy_min_005"
    
    sop_canned_responses: List[dict] = [
        {
            "canned_response_id": cr_takeover,
            "content": f"我先确认一下：您现在在「{node_name}」这个环节，主要希望我优先帮您处理哪一点？我可以用 1-2 个问题快速确认。",
            "language": "zh-CN",
        },
        {
            "canned_response_id": cr_no_overpromise,
            "content": "我会尽力为您说明，但涉及具体结果/最终解释仍需以正式条款、系统记录或人工核验为准，避免造成误解。",
            "language": "zh-CN",
        },
        {
            "canned_response_id": cr_return_main,
            "content": f"好的，关于「{node_name}」的问题已经处理完毕。我们继续主流程吧。",
            "language": "zh-CN",
        },
        {
            "canned_response_id": cr_clarify_evidence,
            "content": "您提到的信息可以在我们的官方网站或正式条款中查到，我可以为您提供具体的查询方式或发送相关材料给您。",
            "language": "zh-CN",
        },
        {
            "canned_response_id": cr_privacy_min,
            "content": "为了继续处理您的请求，我需要确认几个必要信息。这些信息仅用于本次服务，我们会严格保密。请问您方便提供吗？",
            "language": "zh-CN",
        },
    ]
    
    gl: List[dict] = [
        {
            "guideline_id": f"{prefix}_branch_takeover_001",
            "scope": "sop_only",
            "condition": f"进入[{node_name}]二级分支且用户意图不清晰",
            "action": f"使用分支接管模板话术，确认分支处理目标并提出关键澄清问题，引导用户明确需求。",
            "priority": 4,
            "composition_mode": "FLUID",
            "bind_canned_response_ids": [cr_takeover],
            "exclusions": [],
            "dependencies": [],
        },
        {
            "guideline_id": f"{prefix}_branch_no_overpromise_002",
            "scope": "sop_only",
            "condition": "用户要求明确承诺、赔付或结果保证",
            "action": "使用合规免责模板话术，避免绝对化承诺，说明需要以正式条款/系统记录/人工核验为准，并引导获取权威信息。",
            "priority": 3,
            "composition_mode": "FLUID",
            "bind_canned_response_ids": [cr_no_overpromise],
            "exclusions": [],
            "dependencies": [],
        },
        {
            "guideline_id": f"{prefix}_branch_return_main_003",
            "scope": "sop_only",
            "condition": "分支场景已处理完成或用户拒绝继续分支",
            "action": "使用回归主流程模板话术，总结分支结论并引导用户返回主干节点继续流程。",
            "priority": 6,
            "composition_mode": "FLUID",
            "bind_canned_response_ids": [cr_return_main],
            "exclusions": [],
            "dependencies": [],
        },
        {
            "guideline_id": f"{prefix}_branch_clarify_evidence_004",
            "scope": "sop_only",
            "condition": "用户对信息来源/合规性/可信度提出质疑",
            "action": "使用证据澄清模板话术，提供可核验来源（官方材料/条款/联系方式），避免编造法规或机构背书。",
            "priority": 5,
            "composition_mode": "FLUID",
            "bind_canned_response_ids": [cr_clarify_evidence],
            "exclusions": [],
            "dependencies": [],
        },
        {
            "guideline_id": f"{prefix}_branch_privacy_min_005",
            "scope": "sop_only",
            "condition": "需要收集用户信息以继续分支处理",
            "action": "使用隐私保护模板话术，最小化收集必要字段，告知用途与保留方式，避免索取无关敏感信息。",
            "priority": 4,
            "composition_mode": "FLUID",
            "bind_canned_response_ids": [cr_privacy_min],
            "exclusions": [],
            "dependencies": [],
        },
    ]
    return {
        "sop_id": f"{main_journey_name}__branch_{node_id}",
        "sop_title": f"{node_name} 二级分支 Journey",
        "remark": "Step5 生成：二级分支局部 guidelines（sop_only）",
        "sop_canned_responses": sop_canned_responses,
        "sop_scoped_guidelines": gl,
    }


_GLOSSARY_FEW_SHOT_EXAMPLE = '''
【Few-Shot 示例：保险外呼营销场景的术语表】

业务描述：日本共荣保险的外呼营销客服，目标是在用户有挂断或拒绝倾向时进行合规挽留。

生成的术语（15-20个，必须覆盖以下类别）：

【产品术语 - 4-6个】
1. 终身寿险：保障期限为被保险人终身的寿险产品，包含身故保障和现金价值累积
   - 同义词：终身保险、终身保障计划、Whole Life

2. 定期寿险：在约定保障期限内提供身故保障，期满无返还的纯保障型产品
   - 同义词：定期保险、Term Insurance、纯保障险

3. 重大疾病险：确诊约定重大疾病后一次性给付保险金的保障产品
   - 同义词：重疾险、Critical Illness、疾病保险

4. 医疗保险：报销因疾病或意外产生的医疗费用的补偿型保险产品
   - 同义词：医疗险、健康险、Medical Insurance

5. 年金保险：按约定定期给付保险金，用于养老或长期现金流规划的产品
   - 同义词：年金险、养老金保险、Annuity

6. 万能险：兼具保障和投资功能，保费灵活可调的寿险产品
   - 同义词：万能寿险、Universal Life、灵活型保险

【业务/流程术语 - 5-7个】
7. 冷静期：保险法规定的契约解除权行使期间（通常8-15日），客户可无条件退保
   - 同义词：犹豫期、冷却期、无理由退保期

8. 等待期：保险合同生效后，特定疾病或事故需经过的免赔期间
   - 同义词：免责期、观察期、Waiting Period

9. 免责条款：保险合同中约定保险公司不承担赔付责任的情形条款
   - 同义词：除外责任、免赔条款、Exclusions

10. 保额：保险合同约定的最高赔付金额，即保险保障额度
    - 同义词：保险金额、Coverage Amount、Sum Assured

11. 保费：投保人为获得保险保障需定期支付的保险费用
    - 同义词：保险费、Premium、保险成本

12. 现金价值：具有储蓄性质的保险产品在退保时可获得的金额
    - 同义词：退保金、保单价值、Cash Value

【合规/法规术语 - 4-6个】
13. 说明义务：保险销售中必须向客户说明的重要事项，包括条款、风险、费用等
    - 同义词：信息披露义务、重要事项说明、风险告知义务

14. 适合性确认：根据金融商品交易法要求的投保人需求匹配度验证流程
    - 同义词：需求匹配、适配性验证、Suitability Assessment

15. 明示同意：电子渠道营销所需的客户明确授权机制，含录音保存与内容确认
    - 同义词：书面同意、录音授权、Explicit Consent

16. 保险营销合规：保险销售过程中必须遵守的法律法规和行业规范
    - 同义词：合规要求、监管规定、Regulatory Compliance

17. 反洗钱：金融机构识别和防范洗钱活动的合规要求与流程
    - 同义词：AML、洗钱防范、Anti-Money Laundering

【服务/沟通术语 - 2-4个】
18. 挽留话术：针对用户挂断/拒绝倾向时采用的标准化合规沟通策略
    - 同义词：继续提案话术、异议处理话术、Retention Script

19. 需求分析：通过提问了解客户保障缺口和风险偏好的专业评估过程
    - 同义词：需求评估、保障规划、Needs Analysis

20. 方案定制：根据客户需求和预算量身设计保险组合方案的服务
    - 同义词：个性化方案、定制保障、Tailored Solution

【术语定义原则】
- 术语必须是专业名词或概念，不能是句子或短语
- 术语长度通常在2-8个字（中文）或2-15个字符（英文）
- 每个术语必须有明确的定义，说明其在业务场景中的含义
- 同义词应该是该术语的其他表达方式，不是解释
- 术语必须与业务场景直接相关，有实际参考价值
- 输出语言必须与业务描述的语言保持一致
- 术语数量要求：主术语库必须包含15-20个术语，覆盖产品、业务、合规、服务四大类别
'''


async def _generate_glossary_via_agent(
    *,
    main_journey_name: str,
    node_id: str,
    node_name: str,
    business_desc: str,
    orchestrator,
) -> dict:
    """通过Agent动态生成分支术语表。
    
    策略：
    1. 让模型判断该分支是否需要专属术语
    2. 如果需要，生成2-5个专业术语
    3. 如果不需要，返回空术语表
    """
    
    prompt = f'''
请根据以下信息，判断该分支是否需要专属术语，并生成术语表。

## 业务描述
{business_desc}

## 分支节点
- node_id: {node_id}
- node_name: {node_name}

## 判断标准
请判断该分支是否需要专属术语：
1. 该分支是否涉及专业概念或行业术语？（例如：保险条款、合规要求、业务流程）
2. 该分支是否有特定的业务实体需要定义？（例如：产品名称、服务类型、客户分类）
3. 该分支是否有需要统一理解的专有名词？

如果以上条件都不满足，说明该分支不需要专属术语，请返回空术语表。

## Few-Shot 示例
{_GLOSSARY_FEW_SHOT_EXAMPLE}

## 输出格式（JSON）
如果需要生成术语：
{{
  "need_glossary": true,
  "reason": "需要术语的原因",
  "terms": [
    {{
      "name": "术语名称",
      "description": "术语在业务场景中的定义和含义",
      "synonyms": ["同义词1", "同义词2"]
    }}
  ]
}}

如果不需要生成术语：
{{
  "need_glossary": false,
  "reason": "不需要术语的原因"
}}

## 重要提示
1. 术语数量：主术语库必须包含15-20个术语，覆盖产品、业务、合规、服务四大类别
2. 术语必须是专业名词或概念，不能是句子或短语
3. 术语长度通常在2-8个字（中文）或2-15个字符（日文/英文）
4. 每个术语必须有明确的定义
5. 同义词应该是该术语的其他表达方式
6. 如果确实没有需要定义的术语，请诚实返回 need_glossary: false
7. **输出语言必须与业务描述的语言保持一致**：如果业务描述是中文，术语名称、描述、同义词都必须是中文；如果是日文，则全部使用日文；如果是英文，则全部使用英文
8. **术语覆盖要求**：必须覆盖产品术语（4-6个）、业务/流程术语（5-7个）、合规/法规术语（4-6个）、服务/沟通术语（2-4个）

请只输出JSON，不要输出其他内容。
'''

    try:
        await orchestrator.initialize_agent(agent_type="CoordinatorAgent", agent_name="GlossaryGenerator")
        agent = orchestrator.agents.get("GlossaryGenerator")
        if not agent:
            logger.warning("无法获取GlossaryGenerator agent实例，使用空术语表")
            return _build_empty_glossary(main_journey_name=main_journey_name, node_id=node_id, node_name=node_name)
        
        response = await agent.call_llm(
            prompt=prompt,
            context={
                "business_desc": business_desc,
                "node_id": node_id,
                "node_name": node_name,
            },
        )
        
        if not response:
            logger.warning("Agent call_llm返回空响应，使用空术语表")
            return _build_empty_glossary(main_journey_name=main_journey_name, node_id=node_id, node_name=node_name)
        
        result = repair_json(response.strip(), return_objects=True)
        
        if not isinstance(result, dict):
            logger.warning("Agent返回的结果不是有效JSON对象，使用空术语表")
            return _build_empty_glossary(main_journey_name=main_journey_name, node_id=node_id, node_name=node_name)
        
        need_glossary = result.get("need_glossary", True)
        if need_glossary is False:
            reason = result.get("reason", "模型判断不需要专属术语")
            logger.info(f"【模型决策】分支[{node_name}]不需要专属术语，原因: {reason}")
            return _build_empty_glossary(main_journey_name=main_journey_name, node_id=node_id, node_name=node_name)
        
        terms_data = result.get("terms", [])
        if not terms_data or not isinstance(terms_data, list):
            logger.info(f"【模型决策】分支[{node_name}]没有有效的术语")
            return _build_empty_glossary(main_journey_name=main_journey_name, node_id=node_id, node_name=node_name)
        
        # 构建术语表
        prefix = _safe_id(main_journey_name)
        terms = []
        for i, term_data in enumerate(terms_data, start=1):
            if not isinstance(term_data, dict):
                continue
            name = term_data.get("name", "")
            if not name or len(name) > 20:  # 术语名称不能为空或过长
                continue
            terms.append({
                "term_id": f"{prefix}_{_safe_id(node_id)}_term_{i:03d}",
                "name": name,
                "description": term_data.get("description", f"在[{node_name}]分支场景中的术语：{name}"),
                "synonyms": term_data.get("synonyms", []),
                "language": "zh-CN" if re.match(r"[\u4e00-\u9fff]", name) else "ja-JP",
            })
        
        if len(terms) == 0:
            logger.info(f"【模型决策】分支[{node_name}]没有有效的术语")
            return _build_empty_glossary(main_journey_name=main_journey_name, node_id=node_id, node_name=node_name)
        
        logger.info(f"Agent动态生成分支术语成功，术语数: {len(terms)}")
        return {
            "agent_id": f"{main_journey_name}_agent_001",
            "remark": f"Step5 节点[{node_name}]分支术语（Agent动态生成）",
            "terms": terms,
        }
        
    except Exception as e:
        logger.warning(f"Agent动态生成分支术语失败: {e}，使用空术语表")
        return _build_empty_glossary(main_journey_name=main_journey_name, node_id=node_id, node_name=node_name)


def _build_empty_glossary(*, main_journey_name: str, node_id: str, node_name: str) -> dict:
    """构建空术语表。"""
    return {
        "agent_id": f"{main_journey_name}_agent_001",
        "remark": f"Step5 节点[{node_name}]分支术语（模型判断无需专属术语）",
        "terms": [],
        "skipped_by_model": True,
    }


def _build_node_glossary(*, main_journey_name: str, node_id: str, node_name: str, business_desc: str) -> dict:
    """已废弃：保留此函数签名以兼容旧代码，实际调用 _generate_glossary_via_agent。"""
    return _build_empty_glossary(main_journey_name=main_journey_name, node_id=node_id, node_name=node_name)


def _build_node_tools(*, main_journey_name: str, node_id: str, node_name: str) -> dict:
    tool_id = f"{_safe_id(main_journey_name)}_{_safe_id(node_id)}_tool_send_material_001"
    return {
        "tools": [
            {
                "tool_id": tool_id,
                "tool_name": "send_official_material",
                "description": f"向用户发送与[{node_name}]相关的官方材料/条款链接（若系统支持）。",
                "inputs_schema": {"type": "object", "properties": {"topic": {"type": "string"}}, "required": ["topic"]},
                "outputs_schema": {"type": "object", "properties": {"sent": {"type": "boolean"}}, "required": ["sent"]},
            }
        ]
    }


def _build_sop_observations(*, main_journey_name: str, node_id: str, node_name: str, business_desc: str) -> dict:
    """生成SOP专属observation。
    
    Observation是只有condition没有action的guideline，用于建立规则之间的依赖关系。
    SOP专属observation用于检测该分支场景下的特定状态，供后续规则依赖。
    """
    prefix = f"{_safe_id(main_journey_name)}_{_safe_id(node_id)}"
    
    scene_hint = "业务场景"
    m = re.search(r"(保险|医疗|电商|客服|预约|理赔|投诉|退货|改签|营销|挽留|异议)", business_desc or "")
    if m:
        scene_hint = m.group(1)
    
    return {
        "sop_id": f"{main_journey_name}__branch_{node_id}",
        "sop_title": f"{node_name} 二级分支 Journey",
        "remark": f"Step5 生成：[{node_name}]分支专属observation，用于建立规则依赖关系",
        "sop_observations": [
            {
                "observation_id": f"{prefix}_obs_user_needs_detail_001",
                "condition": f"用户在[{node_name}]节点询问具体细节、要求解释、需要更多信息，在{scene_hint}场景中表现出深入了解的意愿",
                "remark": f"观测用户是否需要[{node_name}]相关的详细信息，用于后续信息提供规则的依赖",
            },
            {
                "observation_id": f"{prefix}_obs_user_hesitant_001",
                "condition": f"用户在[{node_name}]节点犹豫不决、反复询问、表达顾虑，在{scene_hint}场景中表现出决策困难",
                "remark": f"观测用户是否在[{node_name}]节点有犹豫，用于后续引导或澄清规则的依赖",
            },
            {
                "observation_id": f"{prefix}_obs_user_ready_proceed_001",
                "condition": f"用户在[{node_name}]节点表示理解、确认信息、准备继续，在{scene_hint}场景中表现出推进意愿",
                "remark": f"观测用户是否准备好继续[{node_name}]流程，用于后续推进规则的依赖",
            },
            {
                "observation_id": f"{prefix}_obs_branch_completed_001",
                "condition": f"用户在[{node_name}]节点问题已解决、表示满意、准备回归主流程，在{scene_hint}场景中分支处理完成",
                "remark": f"观测[{node_name}]分支是否已完成，用于后续回归主流程规则的依赖",
            },
        ],
    }


def _build_summary(*, node_id: str, node_name: str) -> str:
    return "\n".join(
        [
            f"# Step 5 Summary - {node_id}",
            "",
            f"- node_id: {node_id}",
            f"- node_name: {node_name}",
            f"- generated_at: {datetime.now().isoformat()}",
            "",
            "## 摘要",
            f"本节点分支 SOP 用于在主干节点「{node_name}」出现偏离/阻塞/特殊需求时接管处理，并在完成后回归主干。",
            "",
        ]
    )


async def _run_node_task(
    *,
    output_dir: Path,
    main_journey_name: str,
    node: dict,
    business_desc: str,
    global_texts: List[str],
    orchestrator,
) -> NodeTaskOutput:
    node_id = str(node.get("node_id") or "node_unknown")
    node_name = str(node.get("node_name") or node_id)
    node_dir = output_dir / f"node_{node_id}"
    node_dir.mkdir(parents=True, exist_ok=True)

    # 1) branch journey - 使用Agent动态生成
    journey = await _generate_branch_journey_via_agent(
        main_journey_name=main_journey_name,
        node_id=node_id,
        node_name=node_name,
        business_desc=business_desc,
        orchestrator=orchestrator,
    )
    
    # 检查是否被模型跳过
    skipped_by_model = journey.get("skipped_by_model", False)
    skip_reason = journey.get("skip_reason", "")
    
    if skipped_by_model:
        logger.info(f"【模型决策】节点[{node_name}]被跳过: {skip_reason}")
        # 仍然写入journey文件，标记为跳过
        journey_file = node_dir / f"step5_journeys_{node_id}.json"
        journey_file.write_text(json.dumps(journey, ensure_ascii=False, indent=2), encoding="utf-8")
        
        # 创建空的占位文件
        guidelines_file = node_dir / f"step5_guidelines_{node_id}.json"
        guidelines_file.write_text(json.dumps({"skipped": True, "reason": skip_reason}, ensure_ascii=False, indent=2), encoding="utf-8")
        
        glossary_file = node_dir / f"step5_glossary_{node_id}.json"
        glossary_file.write_text(json.dumps({"skipped": True, "reason": skip_reason}, ensure_ascii=False, indent=2), encoding="utf-8")
        
        tools_file = node_dir / f"step5_tools_{node_id}.json"
        tools_file.write_text(json.dumps({"skipped": True, "reason": skip_reason}, ensure_ascii=False, indent=2), encoding="utf-8")
        
        observations_file = node_dir / f"sop_observations_{node_id}.json"
        observations_file.write_text(json.dumps({"skipped": True, "reason": skip_reason}, ensure_ascii=False, indent=2), encoding="utf-8")
        
        summary = f"# Step 5 Summary - {node_id}\n\n- node_id: {node_id}\n- node_name: {node_name}\n- generated_at: {datetime.now().isoformat()}\n\n## 状态\n模型决策：跳过二级分支生成\n原因：{skip_reason}\n"
        summary_file = node_dir / f"step5_summary_{node_id}.md"
        summary_file.write_text(summary, encoding="utf-8")
        
        return NodeTaskOutput(
            node_id=node_id,
            node_name=node_name,
            journey_file=journey_file,
            guidelines_file=guidelines_file,
            glossary_file=glossary_file,
            tools_file=tools_file,
            summary_file=summary_file,
            observations_file=observations_file,
            skipped_by_model=True,
            skip_reason=skip_reason,
        )
    
    # 检查是否使用了fallback模式
    fallback_source = journey.get("fallback_source")
    if fallback_source:
        logger.warning(f"【重要】分支SOP[{node_name}]使用了fallback模式: {fallback_source}")
    
    journey_file = node_dir / f"step5_journeys_{node_id}.json"
    journey_file.write_text(json.dumps(journey, ensure_ascii=False, indent=2), encoding="utf-8")

    # 2) local guidelines + dedupe vs global
    guidelines = _build_local_guidelines(main_journey_name=main_journey_name, node_id=node_id, node_name=node_name)
    local_list = _ensure_list(guidelines.get("sop_scoped_guidelines"))
    guidelines["sop_scoped_guidelines"] = _heuristic_dedupe_local_guidelines(local_list, global_texts)
    guidelines_file = node_dir / f"step5_guidelines_{node_id}.json"
    guidelines_file.write_text(json.dumps(guidelines, ensure_ascii=False, indent=2), encoding="utf-8")

    # 3) glossary - 使用Agent动态生成
    glossary = await _generate_glossary_via_agent(
        main_journey_name=main_journey_name,
        node_id=node_id,
        node_name=node_name,
        business_desc=business_desc,
        orchestrator=orchestrator,
    )
    glossary_file = node_dir / f"step5_glossary_{node_id}.json"
    glossary_file.write_text(json.dumps(glossary, ensure_ascii=False, indent=2), encoding="utf-8")

    # 4) tools
    tools = _build_node_tools(main_journey_name=main_journey_name, node_id=node_id, node_name=node_name)
    tools_file = node_dir / f"step5_tools_{node_id}.json"
    tools_file.write_text(json.dumps(tools, ensure_ascii=False, indent=2), encoding="utf-8")

    # 5) observations - SOP专属observation
    observations = _build_sop_observations(
        main_journey_name=main_journey_name,
        node_id=node_id,
        node_name=node_name,
        business_desc=business_desc,
    )
    observations_file = node_dir / f"sop_observations_{node_id}.json"
    observations_file.write_text(json.dumps(observations, ensure_ascii=False, indent=2), encoding="utf-8")

    # 6) summary
    summary = _build_summary(node_id=node_id, node_name=node_name)
    summary_file = node_dir / f"step5_summary_{node_id}.md"
    summary_file.write_text(summary, encoding="utf-8")

    return NodeTaskOutput(
        node_id=node_id,
        node_name=node_name,
        journey_file=journey_file,
        guidelines_file=guidelines_file,
        glossary_file=glossary_file,
        tools_file=tools_file,
        summary_file=summary_file,
        observations_file=observations_file,
    )


async def step5_branch_sop_parallel_handler(context: Dict[str, Any], orchestrator) -> Dict[str, Any]:
    logger.info("Step 5(v2): mining branch SOPs per main backbone node (optional parallel)")

    output_dir = Path(context.get("output_dir", "./output/step5_branch_sop_parallel"))
    output_dir.mkdir(parents=True, exist_ok=True)

    # 回填 Step2 产物（支持从中间步骤启动）
    if not context.get("main_sop_backbone") or not context.get("global_objective"):
        step2 = _load_step2_result(context)
        context.setdefault("main_sop_backbone", step2.get("main_sop_backbone", {}))
        context.setdefault("global_objective", step2.get("global_objective", ""))
        context.setdefault("core_goal", (step2.get("business_objectives") or {}).get("core_goal", ""))

    output_base_dir = output_dir.parent.resolve()
    step3_dir = output_base_dir / "step3_global_rules_and_glossary"
    _, global_texts = _load_global_guidelines(step3_dir)

    backbone = context.get("main_sop_backbone", {}) or {}
    nodes = _ensure_list(backbone.get("main_sop_nodes"))
    if not nodes:
        raise ValueError("Step5 requires main_sop_backbone.main_sop_nodes from Step2")

    business_desc = str(context.get("business_desc", ""))
    main_journey_name = _safe_id(str(context.get("agent_id", "")) or "main_journey")
    if main_journey_name == "id":
        main_journey_name = "main_journey"

    max_parallel = int(((context.get("config") or {}).get("max_parallel_step5_nodes") or 1))
    max_parallel = max(1, max_parallel)
    sem = asyncio.Semaphore(max_parallel)

    async def _guarded(node: dict) -> NodeTaskOutput:
        async with sem:
            return await _run_node_task(
                output_dir=output_dir,
                main_journey_name=main_journey_name,
                node=node,
                business_desc=business_desc,
                global_texts=global_texts,
                orchestrator=orchestrator,
            )

    gathered = await asyncio.gather(*[_guarded(n) for n in nodes], return_exceptions=True)
    outputs: List[NodeTaskOutput] = []
    errors: List[str] = []
    skipped_by_model: List[Dict[str, str]] = []
    for g in gathered:
        if isinstance(g, Exception):
            errors.append(f"{type(g).__name__}: {g}")
        else:
            outputs.append(g)
            if hasattr(g, 'skipped_by_model') and g.skipped_by_model:
                skipped_by_model.append({
                    "node_id": g.node_id,
                    "node_name": g.node_name,
                    "skip_reason": getattr(g, 'skip_reason', '模型判断不需要二级分支'),
                })

    if errors:
        raise RuntimeError(f"Step5 node tasks failed: {errors[:3]}")
    
    if skipped_by_model:
        logger.info(f"【模型决策】共{len(skipped_by_model)}个节点被模型判断为不需要二级分支: {[s['node_name'] for s in skipped_by_model]}")

    # Step5 合规门控（最小）：检查每个 node 的关键文件存在（跳过被模型决策跳过的节点）
    await orchestrator.initialize_agent(agent_type="ComplianceCheckAgent", agent_name="ComplianceCheckAgent")
    compliance_files: List[str] = []
    for o in outputs:
        # 跳过被模型决策跳过的节点
        if hasattr(o, 'skipped_by_model') and o.skipped_by_model:
            continue
        compliance_files.extend(
            [
                str(o.journey_file),
                str(o.guidelines_file),
                str(o.glossary_file),
                str(o.tools_file),
            ]
        )
    compliance_ctx = {
        "stage": "step5_branch_sop_parallel",
        "output_dir": str(output_dir),
        "step_num": context.get("step_num"),
        "files": compliance_files,
    }
    compliance_res = await orchestrator.execute_agent(
        agent_name="ComplianceCheckAgent",
        task="对 Step5 二级分支产物做门控校验（结构/关键字段/非空），不通过则终止",
        context=compliance_ctx,
    )
    if isinstance(compliance_res, dict) and compliance_res.get("passed") is False:
        raise ValueError(
            f"Step5 compliance check failed: {((compliance_res.get('compliance_report') or {}).get('issues') or [])[:5]}"
        )

    output_files = []
    for o in outputs:
        output_files.extend(
            [
                str(o.journey_file),
                str(o.guidelines_file),
                str(o.glossary_file),
                str(o.tools_file),
                str(o.observations_file),
                str(o.summary_file),
            ]
        )
    if isinstance(compliance_res, dict):
        output_files.extend(_ensure_list(compliance_res.get("output_files")))

    return {
        "step5_nodes": [{"node_id": o.node_id, "node_name": o.node_name, "skipped_by_model": getattr(o, 'skipped_by_model', False)} for o in outputs],
        "output_files": output_files,
        "metadata": {
            "node_count": len(outputs),
            "parallel_limit": max_parallel,
            "skipped_by_model_count": len(skipped_by_model),
            "skipped_by_model": skipped_by_model,
        },
    }

