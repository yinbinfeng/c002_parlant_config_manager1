#!/usr/bin/env python3
"""Step 2: 多维度分析与原子化拆解"""

from pathlib import Path
import re
import yaml
import os
import json
import asyncio
from datetime import datetime
from json_repair import repair_json
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from ..utils.logger import logger


def json_dumps(obj, **kwargs):
    """使用 json_repair 修复后再序列化"""
    json_str = json.dumps(obj, **kwargs)
    return json_str


async def dimension_analysis_handler(context, orchestrator):
    """多维度分析与原子化拆解"""
    from ..agents.coordinator_agent import CoordinatorAgent
    from ..managers.step_manager import StepManager
    
    logger.info("Starting Multi-Dimension Analysis...")
    
    structured_requirements = context.get("structured_requirements")
    if structured_requirements is None or structured_requirements == {} or structured_requirements == "":
        step1_output_dir = Path(context.get("step1_output_dir", "./output/requirement_clarification"))
        result_file = step1_output_dir / "result.json"
        if result_file.exists():
            with open(result_file, 'r', encoding='utf-8') as f:
                step1_result = repair_json(f.read(), return_objects=True)
            sr = step1_result.get("structured_requirements")
            if not sr:
                sr_file = step1_output_dir / "step1_structured_requirements.md"
                if sr_file.exists():
                    sr = sr_file.read_text(encoding="utf-8")
            context["structured_requirements"] = sr or {}
            if step1_result.get("use_clarification", False):
                context["clarification_questions"] = step1_result.get("clarification_questions", [])
            else:
                context["clarification_questions"] = []
        else:
            raise ValueError("Requirement clarification must be completed before dimension analysis")
    
    output_dir = Path(context.get("output_dir", "./output/dimension_analysis"))
    output_dir.mkdir(parents=True, exist_ok=True)
    
    mock_mode = context.get("mock_mode", True)
    business_desc = context.get("business_desc", "")
    
    deep_research_results = ""
    deep_research_tool = orchestrator.get_tool("deep_research") if "deep_research" in orchestrator.list_tools() else None
    if deep_research_tool and not mock_mode:
        logger.info("Executing Deep Research for industry best practices...")
        research_queries = [
            f"客服Agent系统任务分解最佳实践 {business_desc[:50]}",
            f"用户画像设计方法 客户分群策略",
            f"业务流程边缘情况处理 异常流程设计",
        ]
        research_results = []
        for query in research_queries:
            result = await deep_research_tool.search(query)
            research_results.append(f"### 查询: {query}\n\n{result}\n")
        
        deep_research_results = "\n---\n".join(research_results)
        research_file = output_dir / "step2_deep_research_results.md"
        research_file.write_text(deep_research_results, encoding="utf-8")
        logger.info(f"Deep Research results saved: {research_file}")
    
    logger.info("Starting Multi-Agent Debate...")
    debate_transcript = await _run_multi_agent_debate(context, orchestrator, output_dir, deep_research_results)
    
    await orchestrator.initialize_agent(
        agent_type="CoordinatorAgent",
        agent_name="Coordinator"
    )
    
    logger.info("Starting Multi-Dimension Analysis and Atomic Task Breakdown...")
    
    result = await orchestrator.execute_agent(
        agent_name="Coordinator",
        task="执行多维度分析并生成原子化任务列表，包括用户角色和业务流程的组合矩阵",
        context={
            "business_desc": context.get("business_desc", ""),
            "structured_requirements": context.get("structured_requirements", {}),
            "clarification_questions": context.get("clarification_questions", []),
            "step2_debate_transcript": debate_transcript,
            "step2_deep_research_results": deep_research_results,
            "mock_mode": mock_mode,
            "output_dir": str(output_dir),
        }
    )

    task_breakdown = result.get("task_breakdown") if isinstance(result, dict) else None
    if not task_breakdown:
        tb_file = output_dir / "step3_task_breakdown.json"
        if tb_file.exists():
            try:
                task_breakdown = repair_json(tb_file.read_text(encoding="utf-8"), return_objects=True).get("task_breakdown")
            except Exception:
                task_breakdown = None
    if task_breakdown and not result.get("dimension_analysis"):
        dimension_analysis = {
            "summary": task_breakdown.get("summary", {}),
            "components": task_breakdown.get("components", []),
            "implementation_phases": task_breakdown.get("implementation_phases", []),
            "risk_mitigation": task_breakdown.get("risk_mitigation", []),
        }
        result["dimension_analysis"] = dimension_analysis

    if task_breakdown and (not result.get("atomic_tasks") or result.get("atomic_tasks") == []):
        atomic_tasks = []
        for comp in task_breakdown.get("components", []) or []:
            comp_id = comp.get("id") or "COMP"
            comp_name = comp.get("name") or ""
            priority = comp.get("priority") or "medium"
            desc = comp.get("description") or ""

            agent = "ProcessAgent"
            if "glossary" in str(comp_name).lower():
                agent = "GlossaryAgent"
            elif "tool" in str(comp_name).lower():
                agent = "ProcessAgent"
            elif "guideline" in str(comp_name).lower():
                agent = "ProcessAgent"
            elif "journey" in str(comp_name).lower():
                agent = "ProcessAgent"

            atomic_tasks.append(
                {
                    "task_id": f"{comp_id}_MAIN",
                    "agent": agent,
                    "dimension": f"component::{comp_id}",
                    "description": f"{comp_name}: {desc}",
                    "priority": priority,
                    "dependencies": [],
                    "expected_output": "JSON config artifacts aligned with Parlant schema",
                }
            )

            for idx, sub in enumerate(comp.get("sub_components", []) or []):
                sub_name = sub.get("name") or f"{comp_id}_sub_{idx+1}"
                sub_desc = sub.get("description") or ""
                atomic_tasks.append(
                    {
                        "task_id": f"{comp_id}_SUB_{idx+1}",
                        "agent": agent,
                        "dimension": f"component::{comp_id}::sub::{idx+1}",
                        "description": f"{sub_name}: {sub_desc}",
                        "priority": priority,
                        "dependencies": [f"{comp_id}_MAIN"],
                        "expected_output": "Sub-config sections or design notes feeding final Parlant config",
                    }
                )

        result["atomic_tasks"] = atomic_tasks
    
    sr_text = str(context.get("structured_requirements", ""))
    business_desc_text = context.get("business_desc", "")
    combined_text = f"{business_desc_text}\n{sr_text}"
    
    user_segments = _extract_user_segments(combined_text)
    scenarios = _extract_business_scenarios(combined_text)
    edge_cases = _extract_edge_cases(combined_text)

    if not user_segments:
        user_segments = ["新用户", "活跃用户", "VIP用户"]
    if not scenarios:
        scenarios = ["咨询流程", "办理流程", "投诉处理"]
    if not edge_cases:
        edge_cases = ["正常流程", "异常中断", "超时处理", "用户投诉"]

    combos = []
    for u in user_segments[:4]:
        for s in scenarios[:5]:
            for e in edge_cases[:4]:
                combos.append((u, s, e))
                if len(combos) >= 30:
                    break
            if len(combos) >= 30:
                break
        if len(combos) >= 30:
            break

    existing_task_ids = {x.get("task_id") for x in (result.get("atomic_tasks") or []) if isinstance(x, dict)}
    for idx, (u, s, e) in enumerate(combos, start=1):
        tid = f"MATRIX_{idx:03d}"
        if tid in existing_task_ids:
            continue
        result.setdefault("atomic_tasks", []).append(
            {
                "task_id": tid,
                "agent": "ProcessAgent",
                "dimension": "user_segment_x_scenario_x_edge_case",
                "description": f"用户人群[{u}] × 业务场景[{s}] × 边缘情况[{e}] 组合设计",
                "priority": "high" if e not in ["正常流程", "normal_flow"] else "medium",
                "dependencies": [],
                "expected_output": "Journey/Guideline/Tool/Profile JSON sections for this combination",
            }
        )

    context["dimension_analysis_result"] = result.get("dimension_analysis", {})
    context["atomic_tasks"] = result.get("atomic_tasks", [])
    
    dimension_file = output_dir / "dimension_analysis.json"
    with open(dimension_file, 'w', encoding='utf-8') as f:
        f.write(json_dumps(result.get("dimension_analysis", {}), ensure_ascii=False, indent=2))
    
    tasks_file = output_dir / "atomic_tasks.yaml"
    with open(tasks_file, 'w', encoding='utf-8') as f:
        yaml.dump({"tasks": result.get("atomic_tasks", [])}, f, allow_unicode=True, default_flow_style=False)

    if not result.get("atomic_tasks") or not result.get("dimension_analysis"):
        raise ValueError("Step2 produced empty artifacts (dimension_analysis or atomic_tasks is empty)")
    
    logger.info(f"Dimension analysis completed. Atomic tasks: {len(result.get('atomic_tasks', []))}")
    logger.info(f"Output files: {dimension_file}, {tasks_file}")
    
    result["output_files"] = [str(dimension_file), str(tasks_file)]
    
    return result


def _extract_user_segments(text: str) -> list:
    """提取用户人群/分群信息"""
    patterns = [
        r"用户[群体人群分]*[：:]\s*([^\n]+)",
        r"客群[：:]\s*([^\n]+)",
        r"目标[用户客户][：:]\s*([^\n]+)",
        r"用户画像[：:]\s*([^\n]+)",
        r"VIP[客户用户]*",
        r"新[用户客户]",
        r"老[用户客户]",
        r"活跃[用户客户]",
        r"高价值[用户客户]",
        r"潜在[用户客户]",
    ]
    
    segments = set()
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, str):
                items = re.split(r"[,，、；;和及]", match)
                for item in items:
                    item = item.strip()
                    if item and len(item) < 20:
                        segments.add(item)
            elif isinstance(match, tuple):
                for m in match:
                    if m and len(m) < 20:
                        segments.add(m.strip())
    
    direct_keywords = ["VIP用户", "新用户", "老用户", "活跃用户", "高价值用户", "潜在客户", "普通用户"]
    for kw in direct_keywords:
        if kw in text:
            segments.add(kw)
    
    return list(segments)[:6]


def _extract_business_scenarios(text: str) -> list:
    """提取业务场景/流程信息"""
    patterns = [
        r"业务流程[：:]\s*([^\n]+)",
        r"核心流程[：:]\s*([^\n]+)",
        r"场景[：:]\s*([^\n]+)",
        r"业务场景[：:]\s*([^\n]+)",
        r"主要功能[：:]\s*([^\n]+)",
        r"服务内容[：:]\s*([^\n]+)",
    ]
    
    scenarios = set()
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            items = re.split(r"[,，、；;和及\n]", match)
            for item in items:
                item = item.strip()
                if item and len(item) < 30 and not item.startswith("#"):
                    scenarios.add(item)
    
    scenario_keywords = [
        "咨询", "预约", "办理", "查询", "投诉", "退订", "续费", 
        "购买", "注册", "登录", "支付", "退款", "转人工"
    ]
    for kw in scenario_keywords:
        if kw in text:
            scenarios.add(f"{kw}流程")
    
    return list(scenarios)[:8]


def _extract_edge_cases(text: str) -> list:
    """提取边缘情况/异常场景信息"""
    patterns = [
        r"异常[情况处理]*[：:]\s*([^\n]+)",
        r"边缘[情况场景]*[：:]\s*([^\n]+)",
        r"错误处理[：:]\s*([^\n]+)",
        r"失败[情况场景]*[：:]\s*([^\n]+)",
        r"超时[处理]*[：:]\s*([^\n]+)",
    ]
    
    edge_cases = set()
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            items = re.split(r"[,，、；;和及\n]", match)
            for item in items:
                item = item.strip()
                if item and len(item) < 30:
                    edge_cases.add(item)
    
    edge_keywords = [
        ("超时", "超时处理"),
        ("失败", "操作失败"),
        ("异常", "异常处理"),
        ("投诉", "用户投诉"),
        ("拒", "拒绝/拒保"),
        ("错误", "错误处理"),
        ("中断", "流程中断"),
        ("取消", "用户取消"),
        ("重试", "重试机制"),
        ("降级", "降级处理"),
    ]
    for kw, label in edge_keywords:
        if kw in text:
            edge_cases.add(label)
    
    if not edge_cases:
        edge_cases = {"正常流程"}
    
    return list(edge_cases)[:6]


class DebateJudgeModel(BaseModel):
    """辩论判断模型 - 用于 Moderator 判断辩论是否结束"""
    finished: bool = Field(description="辩论是否结束")
    consensus_points: List[str] = Field(default_factory=list, description="已达成共识的观点")
    divergence_points: List[str] = Field(default_factory=list, description="仍存在分歧的观点")
    final_decision: str | None = Field(default=None, description="最终决策建议，仅当辩论结束时提供")


def _load_debate_config() -> Dict[str, Any]:
    """加载辩论配置文件"""
    config_path = Path(__file__).parent.parent.parent.parent / "egs" / "v0.1.0_minging_agents" / "config" / "agents" / "debate_prompts.yaml"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    else:
        logger.warning(f"Debate config file not found: {config_path}")
        return {}


def _build_debate_roles_from_config(config: Dict[str, Any], business_desc: str) -> List[Dict]:
    """从配置构建辩论角色列表"""
    roles_config = config.get("debate_roles", {})
    roles = []
    
    for role_key, role_data in roles_config.items():
        sys_prompt_template = role_data.get("sys_prompt_template", "")
        sys_prompt = sys_prompt_template.format(business_desc=business_desc[:500])
        
        roles.append({
            "name": role_data.get("name", role_key),
            "display_name": role_data.get("display_name", role_key),
            "perspective": role_data.get("perspective", ""),
            "stance": role_data.get("stance", "neutral"),
            "focus": role_data.get("focus", []),
            "sys_prompt": sys_prompt,
        })
    
    return roles


async def _run_multi_agent_debate(context, orchestrator, output_dir: Path, deep_research_results: str = "") -> str:
    """执行多 Agent 辩论，整合不同视角的意见
    
    基于 AgentScope 的 Multi-Agent Debate 模式实现：
    - 使用 MsgHub 广播消息给所有参与者
    - 使用 ReActAgent 作为辩论者，支持 Deep Research 工具调用
    - 使用 Moderator 判断辩论是否结束
    - 支持多轮辩论直到达成共识或达到最大轮数
    """
    logger.info("Executing Multi-Agent Debate (AgentScope Pattern)...")
    
    business_desc = context.get("business_desc", "")
    structured_requirements = context.get("structured_requirements", {})
    mock_mode = context.get("mock_mode", True)
    
    debate_config = _load_debate_config()
    debate_roles = _build_debate_roles_from_config(debate_config, business_desc)
    
    if not debate_roles:
        logger.warning("Failed to load debate roles from config, using defaults")
        debate_roles = [
            {
                "name": "DomainExpert",
                "display_name": "领域专家",
                "perspective": "技术可行性和行业最佳实践",
                "stance": "positive",
                "focus": ["技术实现难度", "架构合理性", "行业标准化", "可维护性"],
                "sys_prompt": f"你是一名领域专家，专注于技术可行性和行业最佳实践。\n辩论话题：{business_desc[:500]}"
            },
            {
                "name": "CustomerAdvocate", 
                "display_name": "客户倡导者",
                "perspective": "用户体验和服务质量",
                "stance": "positive",
                "focus": ["用户满意度", "交互友好性", "响应速度", "服务连续性"],
                "sys_prompt": f"你是一名客户倡导者，专注于用户体验和服务质量。\n辩论话题：{business_desc[:500]}"
            },
            {
                "name": "RequirementAnalyst",
                "display_name": "需求分析师",
                "perspective": "需求完整性和可追溯性",
                "stance": "neutral",
                "focus": ["需求覆盖度", "边界条件", "合规要求", "可测试性"],
                "sys_prompt": f"你是一名需求分析师，专注于需求完整性和可追溯性。\n辩论话题：{business_desc[:500]}"
            },
            {
                "name": "RiskController",
                "display_name": "风险控制专家",
                "perspective": "风险识别和合规审查",
                "stance": "critical",
                "focus": ["合规风险", "数据安全", "隐私保护", "业务风险"],
                "sys_prompt": f"你是一名风险控制专家，专注于风险识别和合规审查。\n辩论话题：{business_desc[:500]}"
            }
        ]
    
    debate_lines = [
        "# Step 2: 多 Agent 辩论记录 (AgentScope Multi-Agent Debate)",
        "",
        f"**时间**: {datetime.now().isoformat()}",
        f"**业务描述**: {business_desc[:100]}...",
        "",
        "## 辩论规则",
        "",
        "1. 每个角色从不同视角分析需求，使用 Deep Research 工具支持观点",
        "2. 角色之间进行多轮辩论，交换观点并深入讨论",
        "3. Moderator 判断是否达成共识或达到最大轮数",
        "4. 形成最终决策并记录理由",
        "",
        "---",
        "",
    ]
    
    if deep_research_results:
        debate_lines.extend([
            "## Deep Research 行业研究摘要",
            "",
            deep_research_results[:2000],
            "",
            "---",
            "",
        ])
    
    if mock_mode:
        logger.info("Generating MOCK debate transcript...")
        mock_result = _generate_mock_debate_transcript(business_desc, debate_roles, debate_config)
        debate_lines.extend(mock_result["transcript"])
        
        process_logs = mock_result["process_logs"]
        process_log_file = output_dir / "debate_process.log"
        with open(process_log_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(process_logs))
        logger.info(f"辩论过程日志已保存: {process_log_file}")
    else:
        logger.info("Running Multi-Agent Debate with AgentScope framework...")
        try:
            debate_result = await _run_agentscope_debate(
                business_desc=business_desc,
                structured_requirements=structured_requirements,
                debate_roles=debate_roles,
                deep_research_results=deep_research_results,
                output_dir=output_dir,
                debate_config=debate_config
            )
            debate_lines.extend(debate_result["transcript"])
        except Exception as e:
            logger.error(f"AgentScope debate failed: {e}", exc_info=True)
            raise RuntimeError(f"Multi-Agent Debate failed in REAL mode: {e}") from e
    
    debate_file = output_dir / "step2_debate_transcript.md"
    debate_content = "\n".join(debate_lines)
    with open(debate_file, 'w', encoding='utf-8') as f:
        f.write(debate_content)
    
    logger.info(f"Debate transcript saved: {debate_file}")
    
    return debate_content


async def _run_agentscope_debate(
    business_desc: str,
    structured_requirements: dict,
    debate_roles: List[Dict],
    deep_research_results: str,
    output_dir: Path,
    debate_config: Dict[str, Any] = None
) -> Dict[str, Any]:
    """使用 AgentScope 框架运行 Multi-Agent Debate
    
    基于 AgentScope 官方文档的 Multi-Agent Debate 模式：
    - 使用 MsgHub 广播消息
    - 使用 ReActAgent 作为辩论者（支持工具调用）
    - 使用 Moderator 判断辩论结束
    - 支持多轮辩论
    """
    from agentscope.agent import ReActAgent
    from agentscope.model import OpenAIChatModel
    from agentscope.memory import InMemoryMemory
    from agentscope.formatter import OpenAIChatFormatter
    from agentscope.pipeline import MsgHub
    from agentscope.message import Msg
    from agentscope.tool import ToolResponse
    
    logger.info("Initializing AgentScope debate agents...")
    
    debate_config = debate_config or {}
    prompts_config = debate_config.get("debate_prompts", {})
    config_settings = debate_config.get("debate_config", {})
    moderator_config = debate_config.get("moderator", {})
    summary_config = debate_config.get("debate_summary", {})
    
    from ..utils.config_loader import get_config_loader
    config_loader = get_config_loader()
    system_config = config_loader.config or {}
    openai_cfg = system_config.get("openai", {})
    model_name = openai_cfg.get("model_name", "Qwen/Qwen3.5-27B")
    
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    model_kwargs = {
        "model_name": model_name,
        "api_key": api_key,
        "generate_kwargs": {"temperature": 0.7}
    }
    if base_url:
        model_kwargs["client_kwargs"] = {"base_url": base_url}
    
    model = OpenAIChatModel(**model_kwargs)
    formatter = OpenAIChatFormatter()
    
    max_iters = config_settings.get("max_iters_per_agent", 3)
    
    process_logs = []
    process_logs.append(f"[{datetime.now().isoformat()}] 开始初始化辩论 Agent")
    process_logs.append(f"[{datetime.now().isoformat()}] 模型配置: {model_name}, temperature=0.7")
    process_logs.append(f"[{datetime.now().isoformat()}] 最大迭代次数: {max_iters}")
    
    logger.info("=== 辩论初始化开始 ===")
    
    solver_agents = []
    for role in debate_roles:
        agent = ReActAgent(
            name=role["name"],
            sys_prompt=role["sys_prompt"],
            model=model,
            formatter=formatter,
            memory=InMemoryMemory(),
            max_iters=max_iters,
        )
        
        deep_research_tool = _create_debate_research_tool(business_desc, role)
        if deep_research_tool:
            agent.toolkit.register_tool_function(deep_research_tool)
        
        solver_agents.append(agent)
        log_msg = f"[{datetime.now().isoformat()}] 初始化 Agent: {role['name']} ({role['display_name']}) - 视角: {role['perspective']}"
        logger.info(f"Initialized solver agent: {role['name']} ({role['display_name']}) - {role['perspective']}")
        process_logs.append(log_msg)
    
    moderator_sys_prompt_template = moderator_config.get("sys_prompt_template", "")
    if moderator_sys_prompt_template:
        moderator_sys_prompt = moderator_sys_prompt_template.format(business_desc=business_desc[:500])
    else:
        moderator_sys_prompt = f"你是一个辩论主持人。\n辩论话题：{business_desc[:500]}"
    
    moderator = ReActAgent(
        name=moderator_config.get("name", "Moderator"),
        sys_prompt=moderator_sys_prompt,
        model=model,
        formatter=formatter,
        memory=InMemoryMemory(),
        max_iters=1,
    )
    process_logs.append(f"[{datetime.now().isoformat()}] 初始化主持人 Agent: Moderator")
    logger.info("Initialized moderator agent")
    
    transcript_lines = []
    max_rounds = config_settings.get("max_rounds", 3)
    round_num = 0
    all_consensus = []
    all_divergence = []
    final_decision = None
    
    process_logs.append(f"[{datetime.now().isoformat()}] 最大辩论轮数: {max_rounds}")
    process_logs.append(f"[{datetime.now().isoformat()}] 开始辩论...")
    logger.info("=== 辩论开始 ===")
    
    while round_num < max_rounds:
        round_num += 1
        round_start_time = datetime.now()
        logger.info(f"Starting debate round {round_num}/{max_rounds}")
        process_logs.append(f"[{round_start_time.isoformat()}] ========== 第 {round_num} 轮辩论开始 ==========")
        logger.info(f"--- 第 {round_num} 轮辩论开始 ---")
        
        transcript_lines.extend([
            f"## 第 {round_num} 轮辩论",
            "",
            f"**时间**: {datetime.now().isoformat()}",
            "",
        ])
        
        async with MsgHub(participants=solver_agents):
            for i, (agent, role) in enumerate(zip(solver_agents, debate_roles)):
                agent_start_time = datetime.now()
                process_logs.append(f"[{agent_start_time.isoformat()}] Agent {role['name']} 开始发言...")
                logger.info(f"{role['display_name']} ({role['name']}) 开始发言...")
                
                transcript_lines.extend([
                    f"### {role['display_name']} ({role['name']}) 发言",
                    "",
                    f"**视角**: {role['perspective']}",
                    "",
                    f"**关注点**: {', '.join(role['focus'])}",
                    "",
                    "**观点**:",
                    "",
                ])
                
                if round_num == 1:
                    first_round_template = prompts_config.get("first_round_prompt", "")
                    if first_round_template:
                        prompt = first_round_template.format(
                            business_desc=business_desc,
                            structured_requirements=json_dumps(structured_requirements, ensure_ascii=False, indent=2)[:1500],
                            deep_research_results=deep_research_results[:800] if deep_research_results else "暂无"
                        )
                    else:
                        prompt = f"请分析以下业务需求：\n{business_desc}"
                else:
                    subsequent_template = prompts_config.get("subsequent_round_prompt", "")
                    if subsequent_template:
                        prompt = subsequent_template.format(round_num=round_num)
                    else:
                        prompt = f"这是第 {round_num} 轮辩论，请继续。"
                
                try:
                    response = await agent(Msg("user", prompt, "user"))
                    response_text = response.get_text_content() if hasattr(response, 'get_text_content') else str(response.content)
                    
                    for line in response_text.strip().split("\n"):
                        if line.strip():
                            transcript_lines.append(line)
                    
                    transcript_lines.append("")
                    agent_end_time = datetime.now()
                    agent_duration = (agent_end_time - agent_start_time).total_seconds()
                    logger.info(f"{role['name']} completed response in round {round_num} ({agent_duration:.2f}s)")
                    process_logs.append(f"[{agent_end_time.isoformat()}] Agent {role['name']} 发言完成, 耗时: {agent_duration:.2f}秒")
                    process_logs.append(f"[{agent_end_time.isoformat()}] 发言内容摘要: {response_text[:200]}...")
                    logger.info(f"{role['display_name']} 发言内容: {response_text[:300]}...")
                    
                except Exception as e:
                    import traceback
                    logger.warning(f"Agent {role['name']} failed in round {round_num}: {e}", exc_info=True)
                    logger.warning(f"Full traceback: {traceback.format_exc()}")
                    process_logs.append(f"[{datetime.now().isoformat()}] Agent {role['name']} 发言失败: {e}")
                    transcript_lines.append(f"[发言失败: {e}]")
                    transcript_lines.append("")
                
                transcript_lines.extend(["---", ""])
        
        transcript_lines.extend([
            "### 主持人总结",
            "",
        ])
        
        judge_template = prompts_config.get("judge_prompt", "")
        if judge_template:
            judge_prompt = judge_template.format(
                round_num=round_num,
                round_summary=_summarize_round(solver_agents)
            )
        else:
            judge_prompt = f"第 {round_num} 轮辩论结束，请判断是否可以结束辩论。\n各方观点摘要：{_summarize_round(solver_agents)}"
        
        try:
            judge_start_time = datetime.now()
            process_logs.append(f"[{judge_start_time.isoformat()}] 主持人开始判断辩论状态...")
            logger.info("主持人开始判断辩论状态...")
            
            judge_response = await moderator(
                Msg("user", judge_prompt, "user"),
                structured_model=DebateJudgeModel
            )
            
            judge_data = judge_response.metadata if hasattr(judge_response, 'metadata') else {}
            finished = judge_data.get("finished", False)
            consensus = judge_data.get("consensus_points", [])
            divergence = judge_data.get("divergence_points", [])
            decision = judge_data.get("final_decision")
            
            all_consensus.extend(consensus)
            all_divergence.extend(divergence)
            if decision:
                final_decision = decision
            
            judge_end_time = datetime.now()
            judge_duration = (judge_end_time - judge_start_time).total_seconds()
            process_logs.append(f"[{judge_end_time.isoformat()}] 主持人判断完成, 耗时: {judge_duration:.2f}秒")
            process_logs.append(f"[{judge_end_time.isoformat()}] 判断结果: finished={finished}, consensus={len(consensus)}项, divergence={len(divergence)}项")
            logger.info(f"主持人判断完成 - finished={finished}, 共识={len(consensus)}项, 分歧={len(divergence)}项")
            
            transcript_lines.append(f"**辩论是否结束**: {'是' if finished else '否'}")
            transcript_lines.append("")
            
            if consensus:
                transcript_lines.append("**本轮共识**:")
                for c in consensus:
                    transcript_lines.append(f"- {c}")
                transcript_lines.append("")
                logger.info(f"本轮共识: {consensus}")
            
            if divergence:
                transcript_lines.append("**仍存在分歧**:")
                for d in divergence:
                    transcript_lines.append(f"- {d}")
                transcript_lines.append("")
                logger.info(f"仍存在分歧: {divergence}")
            
            if decision:
                transcript_lines.append(f"**决策建议**: {decision}")
                transcript_lines.append("")
                logger.info(f"决策建议: {decision}")
            
            transcript_lines.extend(["---", ""])
            
            round_end_time = datetime.now()
            round_duration = (round_end_time - round_start_time).total_seconds()
            process_logs.append(f"[{round_end_time.isoformat()}] ========== 第 {round_num} 轮辩论结束, 总耗时: {round_duration:.2f}秒 ==========")
            logger.info(f"--- 第 {round_num} 轮辩论结束, 总耗时: {round_duration:.2f}秒 ---")
            
            if finished:
                logger.info(f"辩论提前结束: 达成共识 (第 {round_num} 轮)")
                process_logs.append(f"[{round_end_time.isoformat()}] 辩论提前结束: 达成共识")
                break
                
        except Exception as e:
            logger.warning(f"Moderator judgment failed in round {round_num}: {e}", exc_info=True)
            process_logs.append(f"[{datetime.now().isoformat()}] 主持人判断失败: {e}")
            transcript_lines.append(f"[主持人判断失败: {e}]")
            transcript_lines.extend(["---", ""])
    
    process_logs.append(f"[{datetime.now().isoformat()}] ========== 辩论全部结束 ==========")
    process_logs.append(f"[{datetime.now().isoformat()}] 总轮数: {round_num}")
    logger.info("=== 辩论全部结束 ===")
    logger.info(f"总轮数: {round_num}")
    
    final_consensus = list(dict.fromkeys(all_consensus))
    final_divergence = list(dict.fromkeys(all_divergence))
    
    if not final_consensus:
        final_consensus = summary_config.get("final_consensus", [
            "需要优先实现核心业务流程",
            "用户体验是关键成功因素",
            "合规要求必须严格遵守",
            "异常处理流程必须完善"
        ])
    
    if not final_divergence:
        final_divergence = summary_config.get("key_divergences", [
            "技术实现路径选择（领域专家倾向成熟方案，客户倡导者倾向创新方案）",
            "功能优先级排序（不同角色对high/medium优先级判定有差异）",
            "异常处理策略（风险控制专家倾向保守策略，客户倡导者倾向用户友好策略）"
        ])
    
    final_decisions = [final_decision] if final_decision else summary_config.get("final_decisions", [
        "采用MVP策略: 优先实现核心功能，后续迭代优化",
        "平衡各方需求: 在技术可行性和用户体验之间寻找平衡点",
        "建立反馈机制: 每个迭代周期收集各方反馈并调整",
        "完善异常处理: 覆盖所有识别的边缘情况"
    ])
    
    suggested_user_segments = summary_config.get("suggested_user_segments", ["新用户", "活跃用户", "VIP用户", "流失风险用户"])
    suggested_business_scenarios = summary_config.get("suggested_business_scenarios", ["咨询流程", "办理流程", "投诉处理", "售后服务"])
    suggested_edge_cases = summary_config.get("suggested_edge_cases", ["超时处理", "操作失败", "用户投诉", "数据异常"])
    
    transcript_lines.extend([
        "## 辩论总结",
        "",
        "### 最终共识",
        "",
    ])
    for item in final_consensus:
        transcript_lines.append(f"- {item}")
    logger.info(f"最终共识: {final_consensus}")
    
    transcript_lines.extend([
        "",
        "### 关键分歧",
        "",
    ])
    for item in final_divergence:
        transcript_lines.append(f"- {item}")
    logger.info(f"关键分歧: {final_divergence}")
    
    transcript_lines.extend([
        "",
        "### 最终决策",
        "",
    ])
    for idx, item in enumerate(final_decisions, 1):
        if isinstance(item, str):
            if ":" in item:
                transcript_lines.append(f"{idx}. **{item.split(':')[0]}**: {item.split(':')[1].strip()}")
            else:
                transcript_lines.append(f"{idx}. {item}")
        else:
            transcript_lines.append(f"{idx}. {item}")
    logger.info(f"最终决策: {final_decisions}")
    
    transcript_lines.extend([
        "",
        "### 建议的用户人群",
        "",
    ])
    for item in suggested_user_segments:
        transcript_lines.append(f"- {item}")
    
    transcript_lines.extend([
        "",
        "### 建议的业务场景",
        "",
    ])
    for item in suggested_business_scenarios:
        transcript_lines.append(f"- {item}")
    
    transcript_lines.extend([
        "",
        "### 建议的边缘情况",
        "",
    ])
    for item in suggested_edge_cases:
        transcript_lines.append(f"- {item}")
    
    transcript_lines.append("")
    
    process_log_file = output_dir / "debate_process.log"
    with open(process_log_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(process_logs))
    logger.info(f"辩论过程日志已保存: {process_log_file}")
    
    return {
        "transcript": transcript_lines,
        "rounds": round_num,
        "process_log": str(process_log_file),
        "final_consensus": final_consensus,
        "final_divergence": final_divergence,
        "final_decisions": final_decisions,
    }


def _create_debate_research_tool(business_desc: str, role: Dict) -> callable:
    """为辩论 Agent 创建 Deep Research 工具
    
    这个工具允许辩论者在发言前进行深度研究
    """
    from ..utils.config_loader import get_config_loader
    config_loader = get_config_loader()
    system_config = config_loader.config or {}
    openai_cfg = system_config.get("openai", {})
    deep_research_cfg = system_config.get("deep_research", {})
    
    async def deep_research_for_debate(query: str) -> str:
        """Deep Research 工具 - 用于辩论中搜索证据
        
        Args:
            query: 搜索查询关键词
            
        Returns:
            搜索结果摘要
        """
        from ..tools.deep_research import DeepResearchTool
        
        try:
            config = {
                "openai_api_key": os.getenv("OPENAI_API_KEY"),
                "openai_base_url": os.getenv("OPENAI_BASE_URL"),
                "tavily_api_key": os.getenv("TAVILY_API_KEY"),
                "model_name": openai_cfg.get("model_name", "Qwen/Qwen3.5-27B"),
                "max_depth": deep_research_cfg.get("max_depth", 2),
                "max_iters": deep_research_cfg.get("max_iters", 2),
            }
            
            tool = DeepResearchTool(config=config, mock_mode=False)
            result = await tool.search(query)
            await tool.close()
            return result
            
        except Exception as e:
            logger.warning(f"Deep research tool failed: {e}")
            return f"[搜索失败: {e}]"
    
    deep_research_for_debate.__name__ = "deep_research"
    deep_research_for_debate.__doc__ = f"""Deep Research 工具 - 搜索行业最佳实践和证据
    
作为 {role['display_name']}，你可以使用此工具搜索与 {role['perspective']} 相关的信息。

Args:
    query: 搜索查询关键词，例如 "{role['focus'][0]} 最佳实践"
    
Returns:
    搜索结果摘要
"""
    return deep_research_for_debate


def _summarize_round(agents: List) -> str:
    """总结一轮辩论中各方的观点"""
    summaries = []
    for agent in agents:
        if hasattr(agent, 'memory') and agent.memory:
            try:
                memory_content = str(agent.memory.get_memory())
                if memory_content:
                    summaries.append(f"{agent.name}: {memory_content[:200]}...")
            except Exception:
                pass
    return "\n".join(summaries) if summaries else "暂无观点摘要"


def _generate_mock_debate_transcript(business_desc: str, debate_roles: List[Dict], debate_config: Dict[str, Any] = None) -> Dict[str, Any]:
    """生成 Mock 辩论记录"""
    lines = []
    process_logs = []
    debate_config = debate_config or {}
    mock_opinions_config = debate_config.get("mock_opinions", {})
    summary_config = debate_config.get("debate_summary", {})
    config_settings = debate_config.get("debate_config", {})
    
    max_rounds = config_settings.get("max_rounds", 2)
    
    from ..utils.config_loader import get_config_loader
    config_loader = get_config_loader()
    system_config = config_loader.config or {}
    openai_cfg = system_config.get("openai", {})
    model_name = openai_cfg.get("model_name", "Qwen/Qwen3.5-27B")
    
    process_logs.append(f"[{datetime.now().isoformat()}] 开始初始化辩论 Agent (Mock 模式)")
    process_logs.append(f"[{datetime.now().isoformat()}] 模型配置: {model_name}, temperature=0.7")
    logger.info("=== 辩论初始化开始 (Mock 模式) ===")
    
    for role in debate_roles:
        log_msg = f"[{datetime.now().isoformat()}] 初始化 Agent: {role['name']} ({role['display_name']}) - 视角: {role['perspective']}"
        logger.info(f"Initialized solver agent: {role['name']} ({role['display_name']}) - {role['perspective']}")
        process_logs.append(log_msg)
    
    process_logs.append(f"[{datetime.now().isoformat()}] 初始化主持人 Agent: Moderator")
    logger.info("Initialized moderator agent")
    
    process_logs.append(f"[{datetime.now().isoformat()}] 最大辩论轮数: {max_rounds}")
    process_logs.append(f"[{datetime.now().isoformat()}] 开始辩论...")
    logger.info("=== 辩论开始 (Mock 模式) ===")
    
    for round_num in range(1, max_rounds + 1):
        round_start_time = datetime.now()
        process_logs.append(f"[{round_start_time.isoformat()}] ========== 第 {round_num} 轮辩论开始 ==========")
        logger.info(f"--- 第 {round_num} 轮辩论开始 (Mock 模式) ---")
        
        lines.extend([
            f"## 第 {round_num} 轮辩论",
            "",
            f"**时间**: {datetime.now().isoformat()}",
            "",
        ])
        
        for role in debate_roles:
            agent_start_time = datetime.now()
            process_logs.append(f"[{agent_start_time.isoformat()}] Agent {role['name']} 开始发言...")
            logger.info(f"{role['display_name']} ({role['name']}) 开始发言...")
            
            lines.extend([
                f"### {role['display_name']} ({role['name']}) 发言",
                "",
                f"**视角**: {role['perspective']}",
                "",
                f"**关注点**: {', '.join(role['focus'])}",
                "",
                "**观点**:",
                "",
            ])
            
            mock_opinions = _generate_mock_opinions(role, business_desc, mock_opinions_config)
            for opinion in mock_opinions:
                lines.append(f"- {opinion}")
            
            agent_end_time = datetime.now()
            agent_duration = (agent_end_time - agent_start_time).total_seconds()
            process_logs.append(f"[{agent_end_time.isoformat()}] Agent {role['name']} 发言完成, 耗时: {agent_duration:.2f}秒")
            process_logs.append(f"[{agent_end_time.isoformat()}] 发言内容摘要: {mock_opinions[0][:100]}...")
            logger.info(f"{role['name']} completed response in round {round_num} ({agent_duration:.2f}s)")
            logger.info(f"{role['display_name']} 发言内容: {mock_opinions[0][:150]}...")
            
            lines.extend(["", "---", ""])
        
        lines.extend([
            "### 主持人总结",
            "",
            f"**辩论是否结束**: {'是' if round_num == max_rounds else '否'}",
            "",
            "**本轮共识**:",
        ])
        
        round_consensus = ["需要优先实现核心业务流程", "用户体验是关键成功因素"] if round_num == 1 else ["技术方案需要平衡用户体验", "异常处理需要完善"]
        for c in round_consensus:
            lines.append(f"- {c}")
        
        lines.extend([
            "",
            "---",
            "",
        ])
        
        process_logs.append(f"[{datetime.now().isoformat()}] 主持人开始判断辩论状态...")
        logger.info("主持人开始判断辩论状态...")
        process_logs.append(f"[{datetime.now().isoformat()}] 主持人判断完成, 耗时: 0.01秒")
        process_logs.append(f"[{datetime.now().isoformat()}] 判断结果: finished={round_num == max_rounds}, consensus=2项, divergence=1项")
        logger.info(f"主持人判断完成 - finished={round_num == max_rounds}, 共识=2项, 分歧=1项")
        logger.info(f"本轮共识: {round_consensus}")
        
        round_end_time = datetime.now()
        round_duration = (round_end_time - round_start_time).total_seconds()
        process_logs.append(f"[{round_end_time.isoformat()}] ========== 第 {round_num} 轮辩论结束, 总耗时: {round_duration:.2f}秒 ==========")
        logger.info(f"--- 第 {round_num} 轮辩论结束, 总耗时: {round_duration:.2f}秒 ---")
    
    process_logs.append(f"[{datetime.now().isoformat()}] ========== 辩论全部结束 ==========")
    process_logs.append(f"[{datetime.now().isoformat()}] 总轮数: {max_rounds}")
    logger.info("=== 辩论全部结束 (Mock 模式) ===")
    logger.info(f"总轮数: {max_rounds}")
    
    final_consensus = summary_config.get("final_consensus", [
        "需要优先实现核心业务流程",
        "用户体验是关键成功因素",
        "合规要求必须严格遵守",
        "异常处理流程必须完善"
    ])
    
    key_divergences = summary_config.get("key_divergences", [
        "技术实现路径选择（领域专家倾向成熟方案，客户倡导者倾向创新方案）",
        "功能优先级排序（不同角色对high/medium优先级判定有差异）",
        "异常处理策略（风险控制专家倾向保守策略，客户倡导者倾向用户友好策略）"
    ])
    
    final_decisions = summary_config.get("final_decisions", [
        "采用MVP策略: 优先实现核心功能，后续迭代优化",
        "平衡各方需求: 在技术可行性和用户体验之间寻找平衡点",
        "建立反馈机制: 每个迭代周期收集各方反馈并调整",
        "完善异常处理: 覆盖所有识别的边缘情况"
    ])
    
    suggested_user_segments = summary_config.get("suggested_user_segments", ["新用户", "活跃用户", "VIP用户", "流失风险用户"])
    suggested_business_scenarios = summary_config.get("suggested_business_scenarios", ["咨询流程", "办理流程", "投诉处理", "售后服务"])
    suggested_edge_cases = summary_config.get("suggested_edge_cases", ["超时处理", "操作失败", "用户投诉", "数据异常"])
    
    lines.extend([
        "## 辩论总结",
        "",
        "### 最终共识",
        "",
    ])
    for item in final_consensus:
        lines.append(f"- {item}")
    logger.info(f"最终共识: {final_consensus}")
    
    lines.extend([
        "",
        "### 关键分歧",
        "",
    ])
    for item in key_divergences:
        lines.append(f"- {item}")
    logger.info(f"关键分歧: {key_divergences}")
    
    lines.extend([
        "",
        "### 最终决策",
        "",
    ])
    for idx, item in enumerate(final_decisions, 1):
        lines.append(f"{idx}. **{item.split(':')[0]}**: {item.split(':')[1].strip() if ':' in item else item}")
    logger.info(f"最终决策: {final_decisions}")
    
    lines.extend([
        "",
        "### 建议的用户人群",
        "",
    ])
    for item in suggested_user_segments:
        lines.append(f"- {item}")
    
    lines.extend([
        "",
        "### 建议的业务场景",
        "",
    ])
    for item in suggested_business_scenarios:
        lines.append(f"- {item}")
    
    lines.extend([
        "",
        "### 建议的边缘情况",
        "",
    ])
    for item in suggested_edge_cases:
        lines.append(f"- {item}")
    
    lines.append("")
    
    return {
        "transcript": lines,
        "process_logs": process_logs,
        "final_consensus": final_consensus,
        "final_divergence": key_divergences,
        "final_decisions": final_decisions,
    }


def _generate_mock_opinions(role: dict, business_desc: str, mock_opinions_config: Dict[str, Any] = None) -> list:
    """生成模拟观点"""
    mock_opinions_config = mock_opinions_config or {}
    role_name = role['name']
    
    role_key_map = {
        "DomainExpert": "domain_expert",
        "CustomerAdvocate": "customer_advocate",
        "RequirementAnalyst": "requirement_analyst",
        "RiskController": "risk_controller"
    }
    
    config_key = role_key_map.get(role_name)
    if config_key and config_key in mock_opinions_config:
        return mock_opinions_config[config_key]
    
    if "领域专家" in role_name or "DomainExpert" in role_name:
        return [
            "建议采用微服务架构，便于后续扩展和维护",
            "状态机设计需要覆盖所有异常分支，避免死循环",
            "工具集成应使用标准API网关模式",
            "术语表需要与行业标准对齐，避免自定义歧义",
            "建议引入缓存机制提升响应速度"
        ]
    elif "客户倡导者" in role_name or "CustomerAdvocate" in role_name:
        return [
            "首响时间应控制在2秒以内，提升用户体验",
            "需要提供更友好的错误提示，避免技术术语",
            "应支持多轮对话上下文保持，减少用户重复输入",
            "转人工服务的触发条件应更加灵活",
            "建议增加用户满意度评价机制"
        ]
    elif "需求分析师" in role_name or "RequirementAnalyst" in role_name:
        return [
            "需求覆盖度检查：当前遗漏了数据合规性要求",
            "边界条件需要明确：超时、重试、降级策略",
            "可追溯性：每个guideline需要关联到具体需求来源",
            "测试覆盖：需要为每个journey定义测试用例",
            "建议增加用户行为埋点需求"
        ]
    elif "风险控制" in role_name or "RiskController" in role_name:
        return [
            "需要评估数据存储和传输的合规性",
            "敏感信息处理需要加密和脱敏",
            "建议增加操作审计日志",
            "异常情况需要有人工兜底机制",
            "需要考虑服务降级和熔断策略"
        ]
    else:
        return ["参与讨论并提供专业意见"]
