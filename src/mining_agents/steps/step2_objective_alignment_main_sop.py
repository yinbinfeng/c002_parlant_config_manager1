#!/usr/bin/env python3
"""
step2_objective_alignment_main_sop.py
文件格式: Python 源码

Step 2（v2）: 目标对齐与主 SOP 主干挖掘
- 生成业务目标与全局目标文件
- 产出主 SOP 主干（5-9 节点，无分支）并标记冻结
- 保存辩论历史（可追溯）
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
import hashlib
import json
import re
import asyncio

from json_repair import repair_json

from ..utils.file_utils import write_json, write_markdown
from ..utils.logger import logger
import traceback


async def _run_multi_agent_debate(
    *,
    context: Dict[str, Any],
    orchestrator,
    output_dir: Path,
    deep_research_results: str,
) -> str:
    """v2 最小辩论实现（替代 legacy dimension_analysis 依赖）。

    目标：
    - 尽可能复用已有 CoordinatorAgent（如可用）
    - 不可用时，生成可追溯的最小 transcript，保证 Step2 可继续执行
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    transcript_file = output_dir / "debate_transcript.md"

    try:
        await orchestrator.initialize_agent(agent_type="CoordinatorAgent", agent_name="CoordinatorAgent")
        
        clarification_questions = context.get("clarification_questions", [])
        
        agent_ctx = {
            "business_desc": context.get("business_desc", ""),
            "structured_requirements": context.get("structured_requirements", {}),
            "deep_research_results": deep_research_results,
            "output_dir": str(output_dir),
            "mock_mode": context.get("mock_mode", True),
            "step_num": context.get("step_num"),
            "step1_questions": clarification_questions,
            "step2_expert_opinions": context.get("step2_expert_opinions", []),
            "step2_user_concerns": context.get("step2_user_concerns", []),
            "step2_requirement_defense": context.get("step2_requirement_defense", []),
            "step2_debate_transcript": context.get("step2_debate_transcript", ""),
        }
        res = await orchestrator.execute_agent(
            agent_name="CoordinatorAgent",
            task="组织目标对齐与范围澄清：提炼核心价值、主 SOP 范围与关键约束，并形成可追溯记录",
            context=agent_ctx,
        )
        transcript = str((res or {}).get("debate_transcript") or (res or {}).get("transcript") or res)
        transcript_file.write_text(transcript, encoding="utf-8")
        return transcript
    except Exception as e:
        minimal = "\n".join(
            [
                "# Step2 Debate Transcript (fallback)",
                "",
                f"- error: {type(e).__name__}: {e}",
                "",
                "## Business Desc",
                str(context.get("business_desc", "")),
                "",
                "## Structured Requirements (excerpt)",
                str(context.get("structured_requirements", ""))[:2000],
                "",
                "## Deep Research Results (excerpt)",
                (deep_research_results or "")[:4000],
                "",
                "## Traceback",
                traceback.format_exc(),
                "",
            ]
        )
        transcript_file.write_text(minimal, encoding="utf-8")
        logger.warning(f"Step2 debate fallback used: {type(e).__name__}: {e}")
        return minimal


def _load_step1_structured_requirements(context: Dict[str, Any]) -> Dict[str, Any] | str:
    sr = context.get("structured_requirements")
    if sr:
        return sr

    output_base = Path(context.get("output_base_dir", "./output"))
    step1_dir = output_base / "step1_requirement_clarification"
    result_file = step1_dir / "result.json"
    if result_file.exists():
        try:
            data = repair_json(result_file.read_text(encoding="utf-8"), return_objects=True)
            return data.get("structured_requirements") or {}
        except Exception:
            return {}

    md_file = step1_dir / "step1_structured_requirements.md"
    if md_file.exists():
        return md_file.read_text(encoding="utf-8")
    return {}


def _extract_keywords(text: str, limit: int = 8) -> List[str]:
    tokens = re.findall(r"[A-Za-z0-9_\-\u4e00-\u9fff]{2,20}", text or "")
    stop = {"用户", "流程", "需要", "进行", "系统", "以及", "一个", "我们", "可以", "通过", "客服", "agent"}
    uniq: List[str] = []
    for t in tokens:
        if t.lower() in stop:
            continue
        if t not in uniq:
            uniq.append(t)
        if len(uniq) >= limit:
            break
    return uniq


def _build_business_objectives(business_desc: str, sr: Dict[str, Any] | str) -> Dict[str, Any]:
    sr_text = sr if isinstance(sr, str) else json.dumps(sr or {}, ensure_ascii=False)
    text = f"{business_desc}\n{sr_text}"
    kws = _extract_keywords(text, limit=10)
    core_goal = f"围绕业务场景构建可落地的 Parlant 配置，优先保障合规、流程闭环与可维护性（关键词：{', '.join(kws[:5]) or '通用场景'}）"
    return {
        "generated_at": datetime.now().isoformat(),
        "core_goal": core_goal,
        "scope": [
            "先主干后分支：主 SOP 先冻结，再开展分支与边缘场景",
            "主干节点 5-9 个、无分支、每节点单一核心目标",
            "过程可追溯：中间产物独立落盘，支持断点续跑",
        ],
        "non_goals": [
            "不在目标对齐与主SOP主干挖掘阶段输出最终 Parlant 目录结构",
            "不在目标对齐与主SOP主干挖掘阶段处理边缘场景子弹 SOP"
        ],
        "quality_bar": [
            "结束条件可验证（避免主观描述）",
            "术语命名一致、可追溯",
            "后续步骤不得修改已冻结主干",
        ],
    }


def _build_main_sop_backbone_fallback(business_desc: str) -> Dict[str, Any]:
    """Fallback模板：当Agent动态生成失败时使用。
    
    注意：这是一个通用模板，不同业务应该由Agent动态生成不同的SOP结构。
    此模板仅作为回退方案，确保流程可继续执行。
    """
    scene_hint = "业务咨询"
    m = re.search(r"(保险|医疗|电商|客服|预约|理赔|投诉|退货|改签|营销)", business_desc or "")
    if m:
        scene_hint = m.group(1)

    nodes = [
        {
            "node_id": "node_000",
            "node_name": "初访待对接",
            "instruction": f"友好接待用户并确认{scene_hint}咨询意图",
            "exit_condition": "用户已明确说出具体咨询主题（如产品类型/服务名称/问题类别），且表达了期望的目标或诉求",
            "exit_condition_examples": [
                "用户说：我想咨询XX保险的挽留政策",
                "用户说：我有问题想了解一下你们的产品",
                "用户明确表达：我想XX/我需要XX",
            ],
        },
        {
            "node_id": "node_001",
            "node_name": "需求澄清中",
            "instruction": "收集关键信息并完成需求边界确认",
            "exit_condition": "已获取用户的核心需求信息（至少包含：用户身份/场景、具体问题、期望结果），且用户确认信息无误",
            "exit_condition_examples": [
                "用户确认：是的，我想要XX",
                "用户已回答至少3个关键问题",
                "用户说：就这些了，没问题了",
            ],
        },
        {
            "node_id": "node_002",
            "node_name": "方案匹配中",
            "instruction": "基于需求与规则匹配可执行方案",
            "exit_condition": "已向用户清晰说明至少1个可执行方案，且用户表示理解方案内容",
            "exit_condition_examples": [
                "用户说：我明白了",
                "用户说：这个方案可以",
                "用户询问方案细节（表示已理解并想深入了解）",
            ],
        },
        {
            "node_id": "node_003",
            "node_name": "方案确认中",
            "instruction": "与用户确认方案与必要参数",
            "exit_condition": "用户已明确表示接受或拒绝当前方案，若接受则已确认关键参数；若拒绝则已说明原因",
            "exit_condition_examples": [
                "用户说：好的，就这样办",
                "用户说：我不想要这个，因为XX",
                "用户确认了时间/金额/方式等参数",
            ],
        },
        {
            "node_id": "node_004",
            "node_name": "执行与反馈",
            "instruction": "执行方案并反馈关键结果",
            "exit_condition": "已向用户反馈执行结果（成功/失败/等待中），且用户对结果无进一步疑问或异议",
            "exit_condition_examples": [
                "用户说：好的我知道了",
                "用户说：明白了，谢谢",
                "用户确认收到结果且无追问",
            ],
        },
        {
            "node_id": "node_005",
            "node_name": "收尾与引导",
            "instruction": "完成收尾并给出后续引导",
            "exit_condition": "用户明确表示会话结束（如感谢/再见/没问题了），或已给出后续行动指引且用户确认理解",
            "exit_condition_examples": [
                "用户说：谢谢，没问题了",
                "用户说：好的再见",
                "用户确认后续步骤",
            ],
        },
    ]

    backbone = {
        "sop_id": "main_sop_backbone_v2",
        "sop_type": "main",
        "frozen": True,
        "frozen_at": datetime.now().isoformat(),
        "constraints": {
            "node_count_range": "5-9",
            "allow_branch_in_main": False,
            "single_core_objective_per_node": True,
        },
        "main_sop_nodes": nodes,
    }
    raw = json.dumps(backbone, ensure_ascii=False, sort_keys=True).encode("utf-8")
    backbone["freeze_hash"] = hashlib.sha256(raw).hexdigest()
    return backbone


_MAIN_SOP_SCHEMA_HINT = """
【结构提示（非业务示例，严禁照抄业务内容）】
- main_sop_nodes 为 5-10 个业务阶段节点
- 每个节点必须包含：node_id / node_name / instruction / exit_condition / exit_condition_examples
- exit_condition 必须可判定，exit_condition_examples 提供 2-3 个可观测样例

【主SOP颗粒度原则 - 必须遵守】
1. 主SOP是粗颗粒度的核心业务流程，每个节点代表一个独立的业务阶段
2. 主SOP节点应该是宏观的业务阶段，如：身份核验、需求诊断、方案呈现、签约确认、收尾
3. 【严禁】在主SOP中出现重复的业务阶段，如：一级挽留、二级挽留、三级挽留
4. 【严禁】在主SOP中包含细节处理，如：异议处理、价格谈判、风险评估
5. 细节处理（如挽留、异议处理、风险评估）应该在二级分支中实现
6. 边缘场景（如投诉、超时、系统异常）应该在三级边缘场景中实现

【错误示例 - 严禁照抄】
❌ 错误：node_004 一级挽留 → node_005 二级挽留 → node_006 三级挽留
   原因：挽留是细节处理，不应该作为主SOP节点，更不应该重复出现

【正确示例 - 仅供参考结构】
✅ 正确：node_001 身份核验 → node_002 需求诊断 → node_003 方案呈现 → node_004 签约确认 → node_005 收尾
   说明：每个节点是独立的业务阶段，挽留等细节在node_002或node_003的二级分支中实现
"""


async def _generate_main_sop_via_agent(
    *,
    business_desc: str,
    deep_research_results: str,
    debate_transcript: str,
    orchestrator,
    output_dir: Path,
) -> Dict[str, Any]:
    """通过Agent动态生成主SOP主干结构。
    
    策略：
    1. 优先让模型生成完整JSON
    2. 失败时使用模板填空模式，让模型只填写关键字段
    3. 所有fallback输出都会标记fallback_source字段
    
    Returns:
        主SOP字典，包含fallback_source字段标识来源
    """
    
    prompt = f'''
请根据以下业务描述和研究结果，生成主SOP主干结构。

## 业务描述
{business_desc}

## Deep Research 结果
{deep_research_results[:4000] if deep_research_results else "无"}

## 辩论记录
{debate_transcript[:2000] if debate_transcript else "无"}

## 输出结构提示
{_MAIN_SOP_SCHEMA_HINT}

## 生成要求（必须严格遵守）
1. 节点数量：5-10个（严格控制，避免节点爆炸）
2. 每个节点包含：node_id, node_name, instruction, exit_condition, exit_condition_examples
3. 节点抽象度：每个节点代表一个"业务阶段"，不是"具体话术"
4. exit_condition必须可判定，避免"用户满意"等模糊描述
5. 必须结合业务特点，不要照搬示例
6. 严禁输出与业务描述无关的行业内容；如业务未提及某行业，不得引入该行业术语

## 主SOP颗粒度要求（核心原则）
1. 【粗颗粒度】主SOP是核心业务流程的骨架，每个节点代表一个独立的业务阶段
2. 【禁止重复】严禁在主SOP中出现重复的业务阶段（如：一级挽留、二级挽留、三级挽留）
3. 【细节下沉】细节处理（挽留、异议处理、价格谈判、风险评估）应该在二级分支中实现
4. 【边缘下沉】边缘场景（投诉、超时、系统异常）应该在三级边缘场景中实现

## 典型主SOP结构（仅供参考结构，不要照抄内容）
- 身份核验与意图声明 → 需求诊断与现况评估 → 方案呈现与价值说明 → 签约确认与流程引导 → 收尾与后续安排
- 注意：挽留、异议处理等细节应该在"需求诊断"或"方案呈现"节点的二级分支中实现

## 输出格式（JSON）
{{
  "sop_id": "main_sop_backbone_v2",
  "sop_type": "main",
  "sop_title": "主SOP标题",
  "main_sop_nodes": [
    {{
      "node_id": "node_000",
      "node_name": "节点名称",
      "instruction": "节点指令",
      "exit_condition": "退出条件（可判定）",
      "exit_condition_examples": ["示例1", "示例2"]
    }}
  ]
}}

请只输出JSON，不要输出其他内容。
'''

    try:
        await orchestrator.initialize_agent(agent_type="CoordinatorAgent", agent_name="MainSOPGenerator")
        agent = orchestrator.agents.get("MainSOPGenerator")
        if not agent:
            logger.warning("无法获取MainSOPGenerator agent实例，使用fallback模板填空模式")
            return await _generate_main_sop_via_fallback(
                business_desc=business_desc,
                agent=orchestrator.agents.get("CoordinatorAgent"),
            )
        
        response = await agent.call_llm(
            prompt=prompt,
            context={
                "business_desc": business_desc,
                "output_dir": str(output_dir),
            },
        )
        
        if not response:
            logger.warning("Agent call_llm返回空响应，使用fallback模板填空模式")
            return await _generate_main_sop_via_fallback(business_desc=business_desc, agent=agent)
        
        backbone = repair_json(response.strip(), return_objects=True)
        
        if not isinstance(backbone, dict) or "main_sop_nodes" not in backbone:
            logger.warning(f"Agent返回的结果不包含main_sop_nodes，使用fallback模板填空模式")
            return await _generate_main_sop_via_fallback(business_desc=business_desc, agent=agent)
        
        nodes = backbone.get("main_sop_nodes", [])
        if not (5 <= len(nodes) <= 10):
            logger.warning(f"Agent生成的节点数量{len(nodes)}不在5-10范围内，使用fallback模板填空模式")
            return await _generate_main_sop_via_fallback(business_desc=business_desc, agent=agent)
        
        for i, node in enumerate(nodes):
            if not node.get("exit_condition_examples"):
                node["exit_condition_examples"] = [f"用户在{node.get('node_name', f'节点{i}')}完成目标"]
        
        backbone["sop_id"] = "main_sop_backbone_v2"
        backbone["sop_type"] = "main"
        backbone["frozen"] = True
        backbone["frozen_at"] = datetime.now().isoformat()
        backbone["constraints"] = {
            "node_count_range": "5-9",
            "allow_branch_in_main": False,
            "single_core_objective_per_node": True,
        }
        backbone["fallback_source"] = None  # 标识：非fallback生成
        
        raw = json.dumps(backbone, ensure_ascii=False, sort_keys=True).encode("utf-8")
        backbone["freeze_hash"] = hashlib.sha256(raw).hexdigest()
        
        logger.info(f"Agent动态生成主SOP成功，节点数: {len(nodes)}")
        return backbone
        
    except Exception as e:
        logger.warning(f"Agent动态生成主SOP失败: {e}，使用fallback模板填空模式")
        return await _generate_main_sop_via_fallback(
            business_desc=business_desc,
            agent=orchestrator.agents.get("CoordinatorAgent") if orchestrator.agents else None,
        )


async def _generate_main_sop_via_fallback(
    business_desc: str,
    agent: Any = None,
) -> Dict[str, Any]:
    """Fallback模板填空模式：让模型只填写关键字段。
    
    策略：
    1. 固化JSON模板结构
    2. 让模型只生成：节点数量、节点名称、指令、退出条件
    3. 序号等由代码自动生成
    4. 输出中标记fallback_source
    """
    logger.warning("=" * 60)
    logger.warning("【FALLBACK模式】使用模板填空模式生成主SOP")
    logger.warning("=" * 60)
    
    fallback_prompt = f'''
请根据以下业务描述，生成主SOP的关键字段。

## 业务描述
{business_desc}

## 任务
请生成5-8个主SOP节点，每个节点只需要提供：
1. node_name: 节点名称（简洁，4-8个字）
2. instruction: 节点指令（一句话描述该节点要做什么）
3. exit_condition: 退出条件（可判定的条件，避免模糊描述）
4. exit_condition_examples: 判定示例（2-3个具体示例）

## 输出格式（JSON数组）
[
  {{
    "node_name": "节点名称",
    "instruction": "节点指令",
    "exit_condition": "退出条件",
    "exit_condition_examples": ["示例1", "示例2"]
  }}
]

注意：
- 节点数量控制在5-8个
- 每个节点代表一个业务阶段，不是具体话术
- 只输出JSON数组，不要输出其他内容
'''

    nodes_data = None
    
    if agent:
        try:
            response = await agent.call_llm(
                prompt=fallback_prompt,
                context={"business_desc": business_desc},
            )
            if response:
                nodes_data = repair_json(response.strip(), return_objects=True)
        except Exception as e:
            logger.warning(f"Fallback模式LLM调用失败: {e}")
    
    if not nodes_data or not isinstance(nodes_data, list):
        logger.warning("Fallback模式LLM未返回有效数据，使用完全固化模板")
        return _build_main_sop_backbone_fallback(business_desc)
    
    if not (5 <= len(nodes_data) <= 10):
        logger.warning(f"Fallback模式节点数量{len(nodes_data)}不在范围内，使用完全固化模板")
        return _build_main_sop_backbone_fallback(business_desc)
    
    nodes = []
    for i, node_data in enumerate(nodes_data):
        if not isinstance(node_data, dict):
            continue
        node = {
            "node_id": f"node_{i:03d}",
            "node_name": node_data.get("node_name", f"节点{i+1}"),
            "instruction": node_data.get("instruction", ""),
            "exit_condition": node_data.get("exit_condition", ""),
            "exit_condition_examples": node_data.get("exit_condition_examples", []),
        }
        if not node["exit_condition_examples"]:
            node["exit_condition_examples"] = [f"用户在{node['node_name']}完成目标"]
        nodes.append(node)
    
    if len(nodes) < 5:
        logger.warning(f"Fallback模式有效节点不足5个，使用完全固化模板")
        return _build_main_sop_backbone_fallback(business_desc)
    
    backbone = {
        "sop_id": "main_sop_backbone_v2",
        "sop_type": "main",
        "sop_title": f"主SOP - {business_desc[:30]}",
        "frozen": True,
        "frozen_at": datetime.now().isoformat(),
        "constraints": {
            "node_count_range": "5-9",
            "allow_branch_in_main": False,
            "single_core_objective_per_node": True,
        },
        "main_sop_nodes": nodes,
        "fallback_source": "template_fill_mode",  # 标识：fallback模板填空模式
        "fallback_warning": "此SOP由fallback模板填空模式生成，可能不如Agent直接生成的精确",
    }
    
    raw = json.dumps(backbone, ensure_ascii=False, sort_keys=True).encode("utf-8")
    backbone["freeze_hash"] = hashlib.sha256(raw).hexdigest()
    
    logger.warning(f"【FALLBACK模式】主SOP生成完成，节点数: {len(nodes)}")
    logger.warning("【FALLBACK模式】输出文件中将包含fallback_source字段标识")
    
    return backbone


def _should_mine_canned_responses(business_desc: str) -> bool:
    """是否需要在 Step2 挖掘全局 canned responses（可选）。"""
    text = (business_desc or "")
    # 强监管/营销外呼/隐私场景通常需要预审批话术
    keywords = ["合规", "隐私", "个人信息", "投诉", "退订", "拒绝", "外呼", "营销", "保险", "理赔", "金融", "披露"]
    return any(k in text for k in keywords)


def _build_canned_responses(business_desc: str) -> Dict[str, Any]:
    """Step2 产出：全局 canned responses 候选（供 Step3 生成全局 rules 时引用/绑定）。"""
    # 仅生成最小合规/隐私/退订相关话术，避免堆砌
    agent_id = "agent_001"
    prefix = "global"
    return {
        "agent_id": agent_id,
        "remark": "Step2 候选：全局 canned responses（如无需可为空；供 Step3 绑定到全局 guidelines）",
        "agent_canned_responses": [
            {
                "canned_response_id": f"{prefix}_cr_privacy_001",
                "content": "为保护您的个人信息与沟通质量，我仅会在必要范围内向您确认信息，并严格用于本次沟通目的。您也可以随时选择不继续。",
                "language": "zh-CN",
            },
            {
                "canned_response_id": f"{prefix}_cr_opt_out_002",
                "content": "如果您不希望继续接收此类联系，我可以为您登记不再联系/退订偏好。请问需要我现在为您处理吗？",
                "language": "zh-CN",
            },
            {
                "canned_response_id": f"{prefix}_cr_no_overpromise_003",
                "content": "我会尽力为您说明，但涉及具体结果/赔付/最终解释的内容仍需以正式条款、系统记录或人工核验为准，避免给您造成误解。",
                "language": "zh-CN",
            },
        ],
    }


async def step2_objective_alignment_main_sop_handler(context: Dict[str, Any], orchestrator) -> Dict[str, Any]:
    logger.info("Step 2(v2): objective alignment + main SOP backbone mining")
    import traceback

    output_dir = Path(context.get("output_dir", "./output/step2_objective_alignment_main_sop"))
    output_dir.mkdir(parents=True, exist_ok=True)
    context["output_base_dir"] = str(output_dir.parent)

    business_desc = context.get("business_desc", "")
    sr = _load_step1_structured_requirements(context)
    context["structured_requirements"] = sr

    # 澄清问题注入策略：
    # - 仅当 use_clarification=true 时，把澄清问题注入“辩论/后续提示词输入”
    # - 若 use_clarification=false（包括 --skip-clarification），则不注入任何澄清问题
    use_clarification = bool(context.get("use_clarification", False))
    clarification_questions = context.get("clarification_questions", []) if use_clarification else []
    sr_for_debate: Any = sr
    if clarification_questions:
        try:
            # 将澄清问题附加到 structured_requirements 文本（供辩论 prompt 使用）
            if not isinstance(sr_for_debate, str):
                sr_for_debate = json.dumps(sr_for_debate or {}, ensure_ascii=False)
            q_lines = [
                str(sr_for_debate).rstrip(),
                "",
                "## 澄清问题（注入，仅供参考）",
                "",
            ]
            for q in clarification_questions:
                if not isinstance(q, dict):
                    continue
                q_lines.append(f"- {q.get('id', '')}: {q.get('question', '')}")
            sr_for_debate = "\n".join(q_lines)
        except Exception:
            sr_for_debate = sr

    # Step2: 强制调用 Deep Research，并保存报告（供辩论参考 + 可追溯）
    deep_research_results = ""
    deep_research_tool = (
        orchestrator.get_tool("deep_research")
        if hasattr(orchestrator, "list_tools") and "deep_research" in (orchestrator.list_tools() or [])
        else None
    )
    try:
        if deep_research_tool:
            business_desc_for_query = " ".join((business_desc or "").split())
            
            industry_keywords = []
            industry_patterns = [
                (r"保险|insurance", "保险"),
                (r"银行|bank", "银行"),
                (r"医疗|医疗|hospital|health", "医疗"),
                (r"电商|电商|e-commerce|shopping", "电商"),
                (r"教育|教育|education|school", "教育"),
                (r"旅游|旅游|travel|hotel", "旅游"),
                (r"金融|金融|finance|loan", "金融"),
                (r"物流|物流|logistics|delivery", "物流"),
            ]
            for pattern, keyword in industry_patterns:
                if re.search(pattern, business_desc_for_query, re.IGNORECASE):
                    industry_keywords.append(keyword)
            
            scenario_keywords = []
            scenario_patterns = [
                (r"外呼|outbound|电话营销", "外呼营销"),
                (r"客服|customer service|客户服务", "客服"),
                (r"投诉|complaint", "投诉处理"),
                (r"挽留|retention|挽回", "挽留"),
                (r"续保|renewal", "续保"),
                (r"理赔|claim", "理赔"),
                (r"预约|appointment|booking", "预约"),
                (r"咨询|consultation|inquiry", "咨询"),
            ]
            for pattern, keyword in scenario_patterns:
                if re.search(pattern, business_desc_for_query, re.IGNORECASE):
                    scenario_keywords.append(keyword)
            
            industry_str = " ".join(industry_keywords) if industry_keywords else "通用"
            scenario_str = " ".join(scenario_keywords) if scenario_keywords else "客服"
            
            research_brief = (
                "你是面向客服流程设计的行业研究员。请围绕以下业务描述，"
                "生成一份用于“主SOP主干设计”的研究资料，重点包含："
                "1) 合规要求与禁区；2) 用户拒绝/继续倾听等状态识别信号；"
                "3) 主流程阶段划分原则（仅主干，不含分支）；4) 各阶段可判定退出条件。"
                f" 行业={industry_str}；场景={scenario_str}；业务描述={business_desc_for_query}"
            )
            queries = [research_brief]
            
            logger.info(f"Step2 Deep Research: 动态生成描述性查询 (行业={industry_str}, 场景={scenario_str})")

            # Tavily 免费版 RPM 限制对策：支持可配置的并发模式
            # - step2_max_parallel_queries: 1（串行，免费版）或 3（并发，付费版）
            system_config = context.get("config") or {}
            max_parallel = int((system_config.get("deep_research") or {}).get("step2_max_parallel_queries", 1))
            
            reports_dir = output_dir / "research_reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            blocks: List[str] = []
            reports = []
            
            if max_parallel <= 1:
                # 串行模式（免费版 Tavily，避免触发 RPM 限制）
                logger.info(f"Step2 Deep Research: 串行模式 (max_parallel={max_parallel})")
                for idx, q in enumerate(queries, start=1):
                    logger.info(f"Step2 Deep Research [{idx}/{len(queries)}]: {q[:80]}...")
                    try:
                        rep = await deep_research_tool.search(
                            q,
                            audit_output_dir=str(output_dir),
                            caller_agent="Step2_ObjectiveAlignment",
                            query_tag=f"step2_q{idx}",
                        )
                        reports.append(rep)
                        fp = reports_dir / f"report_{idx:02d}.md"
                        fp.write_text(str(rep), encoding="utf-8")
                        blocks.append(f"### 查询 {idx}: {q}\n\n- report_path: {fp}\n\n{str(rep)}\n")
                        logger.info(f"Step2 Deep Research [{idx}/{len(queries)}] completed, saved to {fp}")
                    except Exception as e:
                        logger.warning(f"Deep Research failed for query[{idx}]: {q}. err={e}")
                        reports.append(e)
                        blocks.append(f"### 查询 {idx}: {q}\n\n[搜索失败：{e}]\n")
            else:
                # 并发模式（付费版 Tavily，提速）
                logger.info(f"Step2 Deep Research: 并发模式 (max_parallel={max_parallel})")
                # 使用信号量限制并发数
                semaphore = asyncio.Semaphore(max_parallel)
                
                async def limited_search(idx: int, q: str):
                    async with semaphore:
                        return await deep_research_tool.search(
                            q,
                            audit_output_dir=str(output_dir),
                            caller_agent="Step2_ObjectiveAlignment",
                            query_tag=f"step2_q{idx}",
                        )
                
                tasks = [limited_search(i, q) for i, q in enumerate(queries, start=1)]
                reports = await asyncio.gather(*tasks, return_exceptions=True)
                
                for idx, (q, rep) in enumerate(zip(queries, reports), start=1):
                    if isinstance(rep, Exception):
                        logger.warning(f"Deep Research failed for query[{idx}]: {q}. err={rep}")
                        blocks.append(f"### 查询 {idx}: {q}\n\n[搜索失败：{rep}]\n")
                    else:
                        fp = reports_dir / f"report_{idx:02d}.md"
                        fp.write_text(str(rep), encoding="utf-8")
                        blocks.append(f"### 查询 {idx}: {q}\n\n- report_path: {fp}\n\n{str(rep)}\n")
            
            deep_research_results = "\n---\n".join(blocks)
            write_markdown(deep_research_results, str(output_dir / "deep_research_results.md"))
    except Exception as e:
        logger.warning(f"Deep Research failed in Step2: {e}")
        logger.warning(f"Traceback: {traceback.format_exc()}")
        deep_research_results = ""

    try:
        debate_transcript = await _run_multi_agent_debate(
            context={**context, "structured_requirements": sr_for_debate},
            orchestrator=orchestrator,
            output_dir=output_dir,
            deep_research_results=deep_research_results,
        )
    except Exception as e:
        logger.error(f"Debate failed with error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

    business_objectives = _build_business_objectives(business_desc, sr)
    
    # 使用Agent动态生成主SOP（内部已包含fallback策略）
    main_backbone = await _generate_main_sop_via_agent(
        business_desc=business_desc,
        deep_research_results=deep_research_results,
        debate_transcript=debate_transcript,
        orchestrator=orchestrator,
        output_dir=output_dir,
    )
    
    # 检查是否使用了fallback模式
    fallback_source = main_backbone.get("fallback_source")
    if fallback_source:
        logger.warning(f"【重要】主SOP使用了fallback模式: {fallback_source}")
        logger.warning("【重要】输出JSON中将包含fallback_source和fallback_warning字段")
    else:
        logger.info(f"Agent动态生成主SOP成功，节点数: {len(main_backbone.get('main_sop_nodes', []))}")

    global_objective_text = "\n".join(
        [
            "# global_objective",
            "",
            f"- core_goal: {business_objectives['core_goal']}",
            "- rules:",
            "  - 主干唯一不可逆：Step2 冻结后禁止修改主 SOP 结构",
            "  - 合规优先：合规性高于效率与复杂度控制",
            "  - 过程可追溯：每步产物可单独审计与复跑",
            "",
        ]
    )

    business_objectives_md = "\n".join(
        [
            "# Business Objectives",
            "",
            f"- generated_at: {business_objectives['generated_at']}",
            f"- core_goal: {business_objectives['core_goal']}",
            "",
            "## Scope",
            *[f"- {x}" for x in business_objectives["scope"]],
            "",
            "## Non Goals",
            *[f"- {x}" for x in business_objectives["non_goals"]],
            "",
            "## Quality Bar",
            *[f"- {x}" for x in business_objectives["quality_bar"]],
            "",
        ]
    )

    debate_history = {
        "generated_at": datetime.now().isoformat(),
        "note": "raw transcript stored for traceability",
        "transcript_file": "debate_transcript.md",
        "transcript_excerpt": debate_transcript[:2000],
    }

    write_markdown(business_objectives_md, str(output_dir / "business_objectives.md"))
    write_markdown(global_objective_text, str(output_dir / "global_objective.md"))
    write_json(main_backbone, str(output_dir / "main_sop_backbone.json"))
    write_json(debate_history, str(output_dir / "debate_history.json"))

    # Step2 可选：挖掘全局 canned responses（预审批话术候选），供 Step3 输出时一并落盘
    canned_responses: Dict[str, Any] = {}
    if _should_mine_canned_responses(business_desc):
        canned_responses = _build_canned_responses(business_desc)
        write_json(canned_responses, str(output_dir / "canned_responses.json"))

    context["business_objectives"] = business_objectives
    context["core_goal"] = business_objectives.get("core_goal", "")
    context["global_objective"] = global_objective_text
    context["main_sop_backbone"] = main_backbone
    context["debate_history"] = debate_history
    if canned_responses:
        context["canned_responses"] = canned_responses

    output_files = [
        "business_objectives.md",
        "global_objective.md",
        "main_sop_backbone.json",
        "debate_history.json",
        "debate_transcript.md",
    ]
    if canned_responses:
        output_files.append("canned_responses.json")
    return {
        "business_objectives": business_objectives,
        "global_objective": global_objective_text,
        "main_sop_backbone": main_backbone,
        "debate_history": debate_history,
        "canned_responses": canned_responses,
        "output_files": output_files,
        "metadata": {
            "step": 2,
            "frozen": True,
            "main_node_count": len(main_backbone.get("main_sop_nodes", [])),
        },
    }

