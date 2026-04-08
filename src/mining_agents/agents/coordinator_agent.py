#!/usr/bin/env python3
"""协调员 Agent - 负责整合各方意见并生成任务分解方案"""

import asyncio
import traceback
from typing import Dict, Any, List
from json_repair import repair_json
from pathlib import Path
from .base_agent import BaseAgent

# Step2 ReAct 解析失败时的重试次数（含首次共 N 次）
_REACT_TASK_BREAKDOWN_MAX_ATTEMPTS = 3
_REACT_RETRY_DELAY_SEC = 2.0


class CoordinatorAgent(BaseAgent):
    """协调员 Agent - 负责整合各方意见并生成任务分解方案
    
    主要职责：
    - 收集 Step 2 中领域专家、客户倡导者和需求分析师的意见
    - 识别共识点和分歧点
    - 生成平衡各方需求的任务分解方案
    - 制定 Journey、Guideline、Tool、Glossary 的初步设计
    
    协调原则：
    - 优先满足高优先级/高影响的需求
    - 在技术可行性和用户体验之间寻找平衡点
    - 采用 MVP 思维，先实现核心功能
    """
    
    def __init__(self, name: str, orchestrator, **kwargs):
        """初始化 Agent
        
        Args:
            name: Agent 名称
            orchestrator: Agent 编排器
            **kwargs: 其他参数
        """
        super().__init__(name, orchestrator, **kwargs)
        use_react = bool((self.model_config or {}).get("use_react", True))
        if use_react:
            self._init_react_agent()
        else:
            self.logger.info("Coordinator ReAct disabled by config (use_react=false)")
        
        # 从工具字典中获取工具
        self.deep_research_tool = self.tools.get('deep_research')
        self.json_validator = self.tools.get('json_validator')

    def _parse_task_breakdown_from_text(self, response: str) -> Dict[str, Any] | None:
        for candidate in self._extract_json_text_candidates(str(response or "")):
            try:
                task_breakdown = repair_json(candidate, return_objects=True)
            except Exception:
                continue
            if isinstance(task_breakdown, list):
                first_dict = next((x for x in task_breakdown if isinstance(x, dict)), None)
                if first_dict is not None:
                    self.logger.warning(
                        "repair_json returned list; using first dict item (len={})",
                        len(task_breakdown),
                    )
                    task_breakdown = first_dict
            if isinstance(task_breakdown, dict):
                if "combination_matrix" not in task_breakdown:
                    task_breakdown["combination_matrix"] = []
                return task_breakdown
        return None

    async def _fix_task_breakdown_json_once(self, response: str, context: Dict[str, Any] | None = None) -> Dict[str, Any] | None:
        try:
            fixed = await self._llm_fix_json_once(response, context, schema_hint="JSON object")
        except Exception:
            return None
        return self._parse_task_breakdown_from_text(fixed)

    def _build_deep_research_brief(self, business_desc: str) -> str:
        template = (self.task_prompts or {}).get("deep_research_brief_template", "")
        if template:
            return template.replace("{business_desc}", str(business_desc))
        return (
            "请围绕该业务场景输出任务分解研究报告，覆盖：主流程阶段划分、"
            "关键规则约束、边缘场景信号、工具边界与依赖。"
            f" 业务描述={business_desc}"
        )

    async def _fallback_template_fill_task_breakdown(
        self,
        business_desc: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any] | None:
        prompt = (
            "你需要按固定JSON模板填充字段并决定数组数量。\n"
            "要求：components 4-7 个、implementation_phases 2-4 个、risk_mitigation 3-6 个；"
            "combination_matrix 至少 12 条；仅输出 JSON。\n"
            f"业务描述: {business_desc}\n\n"
            "JSON模板:\n"
            "{\n"
            '  "summary": {"title":"", "vision":"", "mvp_focus":""},\n'
            '  "fallback_source": "template_fill_mode",\n'
            '  "components": [],\n'
            '  "implementation_phases": [],\n'
            '  "risk_mitigation": [],\n'
            '  "combination_matrix": []\n'
            "}\n"
        )
        response = await self.call_llm(prompt, context)
        parsed = self._parse_task_breakdown_from_text(response)
        if parsed is None:
            parsed = await self._fix_task_breakdown_json_once(response, context)
        if isinstance(parsed, dict):
            parsed.setdefault("fallback_source", "template_fill_mode")
            parsed.setdefault("combination_matrix", [])
            return parsed
        return None
    
    async def execute(self, task: str, context: dict) -> dict:
        """执行任务
        
        Args:
            task: 任务描述
            context: 上下文信息，包含：
                - business_desc: 业务描述
                - step1_questions: Step 1 生成的澄清问题
                - step2_expert_opinions: Step 2 专家意见
                - step2_user_concerns: Step 2 用户关切
                - step2_requirement_defense: Step 2 需求辩护
                - mock_mode: 是否使用 Mock 模式
                - output_dir: 输出目录
                
        Returns:
            执行结果，包含：
                - task_breakdown: 任务分解方案
                - journey_outline: 用户旅程大纲
                - guideline_outline: 指导原则大纲
                - tool_requirements: 工具需求列表
                - glossary_items: 术语表项
                - output_files: 输出文件列表
        """
        self.logger.info(f"Starting coordination and task breakdown for task: {task[:50]}...")
        
        # 提取上下文信息
        business_desc = context.get("business_desc", "")
        step1_questions = context.get("step1_questions", [])
        step2_expert_opinions = context.get("step2_expert_opinions", [])
        step2_user_concerns = context.get("step2_user_concerns", [])
        step2_requirement_defense = context.get("step2_requirement_defense", [])
        step2_debate_transcript = context.get("step2_debate_transcript", "")  # 新增：辩论记录
        mock_mode = context.get("mock_mode", True)
        output_dir = Path(context.get("output_dir", "./output/step3"))
        
        # 确保输出目录存在
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Business description: {business_desc[:50]}...")
        self.logger.info(f"Mock mode: {mock_mode}")
        
        # 生成任务分解方案
        if mock_mode:
            self.logger.info("Generating MOCK task breakdown...")
            task_breakdown = self._generate_mock_task_breakdown(
                business_desc,
                step1_questions,
                step2_expert_opinions,
                step2_user_concerns,
                step2_requirement_defense
            )
        else:
            self.logger.info("Generating task breakdown with LLM...")
            task_breakdown = await self._generate_task_breakdown_with_llm(
                business_desc,
                step1_questions,
                step2_expert_opinions,
                step2_user_concerns,
                step2_requirement_defense,
                step2_debate_transcript,
                output_dir,
                mock_mode=mock_mode
            )
        
        # 格式化为 Markdown
        markdown_content = self._format_task_breakdown_to_markdown(task_breakdown)
        
        # 写入文件
        output_file = output_dir / "step3_task_breakdown.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        self.logger.info(f"Task breakdown written to {output_file}")
        
        # 同时保存为 JSON 格式
        json_file = output_dir / "step3_task_breakdown.json"
        if self.json_validator:
            self.json_validator.save_json(
                {
                    "task_breakdown": task_breakdown,
                    "business_desc": business_desc,
                    "input_summary": {
                        "step1_question_count": len(step1_questions),
                        "step2_expert_opinion_count": len(step2_expert_opinions),
                        "step2_user_concern_count": len(step2_user_concerns),
                    }
                },
                str(json_file)
            )
            self.logger.info(f"Task breakdown saved to {json_file}")
        
        return {
            "task_breakdown": task_breakdown,
            "output_files": [str(output_file), str(json_file)],
            "metadata": {
                "component_count": len(task_breakdown.get("components", [])),
                "mock_mode": mock_mode,
            }
        }
    
    def _generate_mock_task_breakdown(
        self,
        business_desc: str,
        step1_questions: List[Dict],
        step2_expert_opinions: List[Dict],
        step2_user_concerns: List[Dict],
        step2_requirement_defense: List[Dict]
    ) -> Dict[str, Any]:
        """生成 Mock 任务分解方案（用于测试）
        
        Args:
            business_desc: 业务描述
            step1_questions: Step 1 生成的澄清问题
            step2_expert_opinions: Step 2 专家意见
            step2_user_concerns: Step 2 用户关切
            step2_requirement_defense: Step 2 需求辩护
            
        Returns:
            任务分解方案
        """
        self.logger.info("Generating mock task breakdown based on input analysis")
        return self._generate_mock_task_breakdown_default(
            business_desc, step1_questions, step2_expert_opinions,
            step2_user_concerns, step2_requirement_defense
        )
    
    def _generate_mock_task_breakdown_default(
        self,
        business_desc: str,
        step1_questions: List[Dict],
        step2_expert_opinions: List[Dict],
        step2_user_concerns: List[Dict],
        step2_requirement_defense: List[Dict]
    ) -> Dict[str, Any]:
        """生成 Mock 任务分解方案（硬编码逻辑，用于降级）
        
        Args:
            business_desc: 业务描述
            step1_questions: Step 1 生成的澄清问题
            step2_expert_opinions: Step 2 专家意见
            step2_user_concerns: Step 2 用户关切
            step2_requirement_defense: Step 2 需求辩护
            
        Returns:
            任务分解方案
        """
        self.logger.info("Generating default mock task breakdown")
        
        # 基于输入生成任务分解
        task_breakdown = {
            "summary": {
                "title": f"{business_desc[:30]} - 任务分解方案",
                "vision": "构建一个平衡技术可行性、用户体验和业务需求的智能客服系统",
                "mvp_focus": "优先实现核心对话流程，确保基本功能稳定可靠",
            },
            "components": [
                {
                    "id": "COMP1",
                    "name": "Journey (用户旅程)",
                    "priority": "high",
                    "description": "定义用户与 Agent 交互的完整流程和状态转换",
                    "sub_components": [
                        {
                            "name": "意图识别流程",
                            "description": "识别用户意图并路由到对应的处理流程",
                            "states": ["初始问候", "意图确认", "问题处理", "解决确认", "结束"],
                        },
                        {
                            "name": "多轮对话管理",
                            "description": "管理多轮对话的上下文和状态保持",
                            "features": ["上下文记忆", "指代消解", "话题切换"],
                        },
                        {
                            "name": "异常处理流程",
                            "description": "处理无法识别、模糊或错误的用户输入",
                            "strategies": ["重试引导", "澄清询问", "转人工服务"],
                        },
                    ],
                    "considerations_from_step2": [
                        "领域专家建议：遵循行业标准的状态机设计",
                        "客户倡导者建议：简化流程，减少用户等待时间",
                    ]
                },
                {
                    "id": "COMP2",
                    "name": "Guideline (指导原则)",
                    "priority": "high",
                    "description": "定义 Agent 的行为准则、话术风格和服务标准",
                    "sub_components": [
                        {
                            "name": "话术风格规范",
                            "description": "定义 Agent 的语言风格、语气和表达方式",
                            "guidelines": ["友好专业", "简洁清晰", "避免 jargon"],
                        },
                        {
                            "name": "服务质量标准",
                            "description": "定义响应时间、解决率等服务质量指标",
                            "metrics": ["首次响应<2 秒", "解决率>80%", "满意度>4.5/5"],
                        },
                        {
                            "name": "合规与安全要求",
                            "description": "定义数据保护、隐私政策和合规要求",
                            "requirements": ["不存储敏感信息", "明确告知 AI 身份", "支持数据删除"],
                        },
                    ],
                    "considerations_from_step2": [
                        "领域专家建议：遵循行业服务标准",
                        "客户倡导者建议：建立信任机制，提供转人工选项",
                    ]
                },
                {
                    "id": "COMP3",
                    "name": "Tool (工具集成)",
                    "priority": "medium",
                    "description": "定义 Agent 需要调用的外部工具和 API",
                    "sub_components": [
                        {
                            "name": "知识库查询工具",
                            "description": "查询产品文档、FAQ 和解决方案库",
                            "integration_points": ["REST API", "Elasticsearch"],
                        },
                        {
                            "name": "订单查询工具",
                            "description": "查询订单状态、物流信息和退换货进度",
                            "integration_points": ["ERP 系统 API", "物流跟踪 API"],
                        },
                        {
                            "name": "CRM 集成工具",
                            "description": "同步用户信息、历史记录和服务工单",
                            "integration_points": ["CRM API", "用户画像服务"],
                        },
                    ],
                    "considerations_from_step2": [
                        "领域专家建议：使用 API Gateway 统一管理",
                        "客户倡导者建议：确保数据安全和隐私保护",
                    ]
                },
                {
                    "id": "COMP4",
                    "name": "Glossary (术语表)",
                    "priority": "medium",
                    "description": "定义业务领域的专业术语、缩写和同义词",
                    "terms": [
                        {
                            "term": "SKU",
                            "definition": "库存量单位 (Stock Keeping Unit)",
                            "usage_example": "这个商品的 SKU 是多少？",
                        },
                        {
                            "term": "退换货",
                            "definition": "退货和换货服务的统称",
                            "usage_example": "我想申请退换货",
                        },
                        {
                            "term": "工单",
                            "definition": "客户服务请求的记录和跟踪单元",
                            "usage_example": "您的问题已创建工单，编号为 XXX",
                        },
                    ],
                    "considerations_from_step2": [
                        "需求分析师建议：确保术语准确反映业务含义",
                        "客户倡导者建议：避免使用用户不理解的内部术语",
                    ]
                },
            ],
            "implementation_phases": [
                {
                    "phase": "Phase 1 - MVP",
                    "duration": "2-3 周",
                    "focus": "核心对话流程和基础功能",
                    "deliverables": [
                        "基础 Journey 设计（3-5 个核心场景）",
                        "基础 Guideline（话术规范和服务标准）",
                        "1-2 个核心 Tool 集成",
                        "基础 Glossary（20-30 个核心术语）",
                    ]
                },
                {
                    "phase": "Phase 2 - 增强",
                    "duration": "3-4 周",
                    "focus": "扩展功能和优化体验",
                    "deliverables": [
                        "扩展 Journey（覆盖 80% 常见场景）",
                        "完善 Guideline（增加异常处理和升级流程）",
                        "更多 Tool 集成（3-5 个）",
                        "完善 Glossary（50+ 术语）",
                    ]
                },
                {
                    "phase": "Phase 3 - 优化",
                    "duration": "持续",
                    "focus": "性能优化和智能化提升",
                    "deliverables": [
                        "基于数据的 Journey 优化",
                        "A/B 测试 Guideline 效果",
                        "Tool 性能优化和错误率降低",
                        "Glossary 自动更新机制",
                    ]
                },
            ],
            "risk_mitigation": [
                {
                    "risk": "技术复杂性导致开发延期",
                    "mitigation": "采用 MVP 策略，优先实现核心功能，使用成熟框架",
                    "owner": "技术负责人",
                },
                {
                    "risk": "用户体验不佳导致采纳率低",
                    "mitigation": "早期用户测试，快速迭代优化，保持简单直观",
                    "owner": "产品经理",
                },
                {
                    "risk": "数据安全和隐私泄露风险",
                    "mitigation": "严格的数据治理策略，加密存储和传输，定期安全审计",
                    "owner": "安全负责人",
                },
            ],
        }
        
        self.logger.info(f"Generated task breakdown with {len(task_breakdown['components'])} components")
        return task_breakdown
    
    async def _generate_task_breakdown_with_llm(
        self,
        business_desc: str,
        step1_questions: List[Dict],
        step2_expert_opinions: List[Dict],
        step2_user_concerns: List[Dict],
        step2_requirement_defense: List[Dict],
        step2_debate_transcript: str = "",
        output_dir: Path = None,
        mock_mode: bool = True,
    ) -> Dict[str, Any]:
        """使用 ReAct 生成任务分解方案（整合多方意见和复杂决策）
        
        Args:
            business_desc: 业务描述
            step1_questions: Step 1 生成的澄清问题
            step2_expert_opinions: Step 2 专家意见
            step2_user_concerns: Step 2 用户关切
            step2_requirement_defense: Step 2 需求辩护
            step2_debate_transcript: Step 2 辩论记录
            output_dir: 输出目录，用于保存对话记录
            mock_mode: 是否允许降级到 mock 模式
            
        Returns:
            任务分解方案
            
        Raises:
            RuntimeError: 当 real 模式下解析失败且不允许降级时
        """
        self.logger.info("Generating task breakdown with ReAct (integrating multi-party opinions)")
        
        # 检查 Deep Research 是否已进入降级模式
        is_fallback_mode = (
            self.deep_research_tool is not None and 
            hasattr(self.deep_research_tool, 'is_fallback_mode') and 
            self.deep_research_tool.is_fallback_mode()
        )
        
        # 强制调用 Deep Research 获取行业最佳实践（除非已降级）
        deep_research_results = ""
        if self.deep_research_tool and not is_fallback_mode:
            try:
                self.logger.info("[强制调用] Deep Research 搜索行业任务分解最佳实践...")
                business_desc_for_query = " ".join((business_desc or "").split())
                research_query = self._build_deep_research_brief(business_desc_for_query)
                deep_research_results = await self.deep_research_tool.search(
                    research_query,
                    audit_output_dir=str(output_dir) if output_dir else None,
                    caller_agent=self.name,
                    query_tag="coordinator_task_breakdown",
                )
                self.logger.info(f"Deep Research 完成，结果长度：{len(deep_research_results)}")
                
                # 保存 Deep Research 结果
                if output_dir:
                    research_output_file = output_dir / "step2_deep_research_results.md"
                    with open(research_output_file, 'w', encoding='utf-8') as f:
                        f.write("# Step 2: Deep Research 搜索结果\n\n")
                        f.write(f"**查询**: {research_query}\n\n")
                        f.write("## 研究结果\n\n")
                        f.write(deep_research_results)
                    self.logger.info(f"Deep Research 结果已保存：{research_output_file}")
            except Exception as e:
                self.logger.error("Deep Research 调用失败（底层为 Tavily Python SDK）：{}", e)
                self.logger.error(
                    "【Tavily / Deep Research】完整报错与堆栈：\n{}",
                    "".join(traceback.format_exception(type(e), e, e.__traceback__, limit=24)),
                )
                # 检查是否因失败次数过多而降级
                if hasattr(self.deep_research_tool, 'is_fallback_mode') and self.deep_research_tool.is_fallback_mode():
                    self.logger.warning("DeepResearchTool entered fallback mode due to max failures. Will use model's own knowledge.")
                    is_fallback_mode = True
                deep_research_results = "[Deep Research 调用失败，使用默认知识]"
        elif is_fallback_mode:
            self.logger.warning("DeepResearchTool is in fallback mode. Skipping Deep Research call and using model's own knowledge.")
            deep_research_results = "[Deep Research 已降级，使用模型自身知识]"
        
        prompt_template = self.task_prompts.get("llm_task_breakdown", "")
        if prompt_template:
            # 使用字符串替换而不是 format_map，避免 JSON 中的花括号被误解析
            react_prompt = prompt_template.replace("{business_desc}", business_desc)
            react_prompt = react_prompt.replace("{step1_questions}", str(step1_questions))
            react_prompt = react_prompt.replace("{step2_expert_opinions}", str(step2_expert_opinions))
            react_prompt = react_prompt.replace("{step2_user_concerns}", str(step2_user_concerns))
            react_prompt = react_prompt.replace("{step2_requirement_defense}", str(step2_requirement_defense))
            react_prompt = react_prompt.replace("{step2_debate_transcript}", step2_debate_transcript)
            react_prompt = react_prompt.replace("{deep_research_results}", deep_research_results)
        else:
            react_prompt = self._get_default_llm_prompt(
                business_desc=business_desc,
                step1_questions=step1_questions,
                step2_expert_opinions=step2_expert_opinions,
                step2_user_concerns=step2_user_concerns,
                step2_requirement_defense=step2_requirement_defense,
                step2_debate_transcript=step2_debate_transcript,
                deep_research_results=deep_research_results,
            )
        
        react_guard = (
            "\n\n【执行流程约束（必须遵守）】\n"
            f"1) 深度研究必须先调用 deep_research，query 使用：{self._build_deep_research_brief(business_desc)}\n"
            "2) deep_research 返回的是 markdown 研究文本，不要把该结果当 JSON 解析；\n"
            "3) 基于研究文本与任务要求输出 Parlant JSON；\n"
            "4) 解析失败时只允许 1 次 json 修复（json_repair + 一次LLM修复）。\n"
        )

        # 使用 ReActAgent 进行多轮整合和决策（失败则重试，再失败则走无 DR 的 LLM fallback）
        invalid_patterns = [
            "interrupted me",
            "what can i do for you",
            "i noticed that you",
        ]
        last_err: Exception | None = None
        final_response = ""

        for attempt in range(_REACT_TASK_BREAKDOWN_MAX_ATTEMPTS):
            self.logger.info(
                "ReAct 任务分解 第 {}/{} 次调用",
                attempt + 1,
                _REACT_TASK_BREAKDOWN_MAX_ATTEMPTS,
            )
            response = await self.call_react_agent(react_prompt + react_guard, {})
            final_response = response

            try:
                if any(pattern in response.lower() for pattern in invalid_patterns):
                    # 说明：该话术来自「协调用 LLM / ReAct」的常见占位输出，并非 Tavily HTTP 响应体。
                    # 旧链路经 MCP 时容易误判为「Tavily 打断」；当前 Tavily 已改为 Python SDK，二者应区分看待。
                    self.logger.warning(
                        "ReAct 返回疑似 LLM 占位/中断类话术（非 Tavily 接口原文）。预览: {!r}",
                        response[:500],
                    )
                    raise ValueError(f"Invalid ReAct response: {response[:200]}")

                task_breakdown = self._parse_task_breakdown_from_text(response)
                if task_breakdown is None:
                    task_breakdown = await self._fix_task_breakdown_json_once(
                        response,
                        {"mock_mode": mock_mode},
                    )
                if task_breakdown is None:
                    self.logger.warning(
                        "task_breakdown parse failed after one LLM-fix attempt; response preview: {!r}",
                        response[:200],
                    )
                    raise ValueError("Expected dict task_breakdown after parse+llm-fix")
                self.logger.info("Successfully generated task breakdown with ReAct")

                if output_dir:
                    react_log_file = output_dir / "step2_react_conversation_log.md"
                    with open(react_log_file, "w", encoding="utf-8") as f:
                        f.write("# Step 2: ReAct Agent 多轮对话记录\n\n")
                        f.write("## 输入 Prompt\n\n")
                        f.write("```\n")
                        f.write(
                            react_prompt[:2000] + "...\n"
                            if len(react_prompt) > 2000
                            else react_prompt,
                        )
                        f.write("\n```\n\n")
                        f.write(f"## ReAct 响应（成功，第 {attempt + 1} 次尝试）\n\n")
                        f.write("```\n")
                        f.write(response)
                        f.write("\n```\n")
                    self.logger.info("ReAct 对话记录已保存: {}", react_log_file)

                return task_breakdown

            except Exception as e:
                last_err = e
                self.logger.warning(
                    "ReAct 解析未成功（尝试 {}/{}）：{}",
                    attempt + 1,
                    _REACT_TASK_BREAKDOWN_MAX_ATTEMPTS,
                    e,
                )
                if attempt + 1 < _REACT_TASK_BREAKDOWN_MAX_ATTEMPTS:
                    await asyncio.sleep(_REACT_RETRY_DELAY_SEC)
                    continue
                break

        # 所有 ReAct 尝试失败：落盘最后一次响应，再按模式降级
        if output_dir and final_response:
            react_log_file = output_dir / "step2_react_conversation_log.md"
            with open(react_log_file, "w", encoding="utf-8") as f:
                f.write("# Step 2: ReAct Agent 多轮对话记录\n\n")
                f.write("## 输入 Prompt\n\n")
                f.write("```\n")
                f.write(
                    react_prompt[:2000] + "...\n"
                    if len(react_prompt) > 2000
                    else react_prompt,
                )
                f.write("\n```\n\n")
                f.write("## ReAct 响应（全部尝试失败，以下为最后一次）\n\n")
                f.write("```\n")
                f.write(final_response)
                f.write("\n```\n")
            self.logger.info("ReAct 对话记录已保存（失败末次）: {}", react_log_file)

        if not mock_mode:
            self.logger.warning(
                "ReAct 在 {} 次尝试后仍失败，降级为无 Deep Research 的直连 LLM。末次错误: {}",
                _REACT_TASK_BREAKDOWN_MAX_ATTEMPTS,
                last_err,
            )
            no_dr = await self._generate_task_breakdown_without_deep_research(
                business_desc,
                step1_questions,
                step2_expert_opinions,
                step2_user_concerns,
                step2_requirement_defense,
                step2_debate_transcript,
                output_dir,
            )
            if isinstance(no_dr, dict):
                return no_dr
            templ = await self._fallback_template_fill_task_breakdown(
                business_desc,
                {"mock_mode": False},
            )
            if isinstance(templ, dict):
                return templ
            raise RuntimeError("CoordinatorAgent：无DR直连与模板填充均失败。")

        self.logger.warning("Mock mode enabled: Falling back to mock task breakdown")
        templ = await self._fallback_template_fill_task_breakdown(
            business_desc,
            {"mock_mode": True},
        )
        if isinstance(templ, dict):
            return templ
        return self._generate_mock_task_breakdown_default(
            business_desc,
            step1_questions,
            step2_expert_opinions,
            step2_user_concerns,
            step2_requirement_defense,
        )
    
    def _get_default_llm_prompt(self,
                                business_desc: str = "",
                                step1_questions: List[Dict] = [],
                                step2_expert_opinions: List[Dict] = [],
                                step2_user_concerns: List[Dict] = [],
                                step2_requirement_defense: List[Dict] = [],
                                step2_debate_transcript: str = "",
                                deep_research_results: str = "") -> str:
        """获取默认 LLM 提示词（配置降级保护）

        注意：提示词应从配置文件加载，此方法仅在配置缺失时作为降级保护
        """
        # 从配置中获取提示词模板
        prompt_template = self.task_prompts.get('llm_task_breakdown', '')
        if prompt_template:
            # 使用字符串替换而不是 format_map，避免 JSON 中的花括号被误解析
            react_prompt = prompt_template.replace("{business_desc}", business_desc)
            react_prompt = react_prompt.replace("{step1_questions}", str(step1_questions))
            react_prompt = react_prompt.replace("{step2_expert_opinions}", str(step2_expert_opinions))
            react_prompt = react_prompt.replace("{step2_user_concerns}", str(step2_user_concerns))
            react_prompt = react_prompt.replace("{step2_requirement_defense}", str(step2_requirement_defense))
            react_prompt = react_prompt.replace("{step2_debate_transcript}", step2_debate_transcript)
            react_prompt = react_prompt.replace("{deep_research_results}", deep_research_results)
            return react_prompt

        # 配置缺失时的最小化保护
        self.logger.warning("LLM task breakdown prompt not found in config, using minimal fallback")
        return f"""请基于以下信息生成任务分解方案：

## 业务描述
{business_desc}

## Deep Research 行业研究结果
{deep_research_results[:500] if deep_research_results else "暂无"}

请生成包含 summary、components、implementation_phases、risk_mitigation 的 JSON 格式任务分解方案。"""

    async def _generate_task_breakdown_without_deep_research(self,
                                                              business_desc: str,
                                                              step1_questions: List[Dict],
                                                              step2_expert_opinions: List[Dict],
                                                              step2_user_concerns: List[Dict],
                                                              step2_requirement_defense: List[Dict],
                                                              step2_debate_transcript: str,
                                                              output_dir: Path) -> dict:
        """不使用 Deep Research，仅依靠模型自身知识生成任务分解方案（Real 模式降级用）
        
        Args:
            business_desc: 业务描述
            step1_questions: Step 1 生成的澄清问题
            step2_expert_opinions: Step 2 专家意见
            step2_user_concerns: Step 2 用户关切
            step2_requirement_defense: Step 2 需求辩护
            step2_debate_transcript: Step 2 辩论记录
            output_dir: 输出目录
            
        Returns:
            任务分解方案
        """
        self.logger.info("Generating task breakdown WITHOUT Deep Research, using model's own knowledge")
        
        # 构建提示词，不包含 Deep Research 结果
        react_prompt = f"""你是一名高级任务规划 Agent，负责生成任务分解方案。

## 业务描述
{business_desc}

## Deep Research 行业研究结果
[Deep Research 不可用，使用模型自身知识]

## 需求澄清问题
{step1_questions}

## 多维度分析
- 领域专家意见：{step2_expert_opinions}
- 客户倡导者意见：{step2_user_concerns}
- 需求辩护结论：{step2_requirement_defense}

## 多 Agent 辩论记录
{step2_debate_transcript}

请基于你的内部知识生成包含 summary、components、implementation_phases、risk_mitigation、combination_matrix 的 JSON 格式任务分解方案。不要输出任何解释性文字，只返回 JSON。"""
        
        # 使用 LLM 直接生成（不使用 ReActAgent，避免调用 Deep Research 工具）
        response = await self.call_llm(react_prompt, {})
        
        # 保存对话记录
        if output_dir:
            react_log_file = output_dir / "step2_react_conversation_log_no_dr.md"
            with open(react_log_file, 'w', encoding='utf-8') as f:
                f.write("# Step 2: LLM 对话记录（无 Deep Research）\n\n")
                f.write("## 输入 Prompt\n\n")
                f.write("```\n")
                f.write(react_prompt[:2000] + "...\n" if len(react_prompt) > 2000 else react_prompt)
                f.write("\n```\n\n")
                f.write("## LLM 响应\n\n")
                f.write("```\n")
                f.write(response)
                f.write("\n```\n")
            self.logger.info(f"LLM 对话记录已保存：{react_log_file}")
        
        # 解析 JSON 响应（失败时先走一次 LLM 修复）
        try:
            task_breakdown = self._parse_task_breakdown_from_text(response)
            if task_breakdown is None:
                task_breakdown = await self._fix_task_breakdown_json_once(
                    response,
                    {"mock_mode": False},
                )
            if task_breakdown is None:
                raise ValueError("Expected dict task_breakdown after parse+llm-fix (no DR path)")
            self.logger.info("Successfully generated task breakdown without Deep Research")
            return task_breakdown
        except Exception as e:
            self.logger.error(f"Failed to parse LLM response (no Deep Research): {e}")
            templ = await self._fallback_template_fill_task_breakdown(
                business_desc,
                {"mock_mode": False},
            )
            if isinstance(templ, dict):
                return templ
            # 如果仍然失败，抛出异常
            raise RuntimeError(f"Real mode: Failed to generate task breakdown without Deep Research. Original error: {e}")

    def _format_task_breakdown_to_markdown(self, task_breakdown: Dict[str, Any]) -> str:
        """将任务分解方案格式化为 Markdown
        
        Args:
            task_breakdown: 任务分解方案
            
        Returns:
            Markdown 格式的文本
        """
        if not isinstance(task_breakdown, dict):
            return (
                f"# Step 3: 任务分解方案\n\n"
                f"_（无法格式化：期望 dict，实际为 {type(task_breakdown).__name__}）_\n"
            )

        lines = [
            "# Step 3: 任务分解方案",
            "",
            "**协调员**: Coordinator Agent",
            "**目标**: 整合 Step 2 各方意见，生成平衡的任务分解方案",
            "",
            "---",
            "",
        ]
        
        # 摘要（模型偶发把 summary 输出成纯字符串）
        summary = task_breakdown.get("summary", {})
        if isinstance(summary, str):
            summary = {"title": "任务分解方案", "vision": summary, "mvp_focus": "N/A"}
        elif not isinstance(summary, dict):
            summary = {}
        lines.extend([
            f"## 📋 {summary.get('title', '任务分解方案')}",
            "",
            f"**愿景**: {summary.get('vision', 'N/A')}",
            "",
            f"**MVP 重点**: {summary.get('mvp_focus', 'N/A')}",
            "",
            "---",
            "",
        ])
        
        # 组件详情
        lines.append("## 🧩 核心组件")
        lines.append("")
        
        components = task_breakdown.get("components", [])
        if not isinstance(components, list):
            components = []

        for comp in components:
            if not isinstance(comp, dict):
                lines.append(f"- （跳过非对象组件项: {type(comp).__name__}）")
                lines.append("")
                continue
            cid = str(comp.get("id", "N/A"))
            cname = str(comp.get("name", "N/A"))
            priority_icon = "🔴" if comp.get("priority") == "high" else ("🟡" if comp.get("priority") == "medium" else "⚪")
            lines.extend([
                f"### {priority_icon} {cid}: {cname}",
                "",
                f"**描述**: {comp.get('description', 'N/A')}",
                "",
            ])
            
            # 子组件
            if "sub_components" in comp and comp["sub_components"]:
                lines.extend(["**子组件**:", ""])
                for sub in comp["sub_components"]:
                    if isinstance(sub, dict):
                        lines.append(f"- **{sub.get('name', 'N/A')}**: {sub.get('description', 'N/A')}")
                    else:
                        lines.append(f"- {sub}")
                lines.append("")
            
            # Step 2 考虑因素
            if "considerations_from_step2" in comp and comp["considerations_from_step2"]:
                lines.extend(["**Step 2 考虑因素**:", ""])
                for consideration in comp["considerations_from_step2"]:
                    lines.append(f"- {consideration}")
                lines.append("")
            
            lines.extend(["---", ""])
        
        # 实施阶段
        lines.extend(["## 📅 实施阶段", ""])
        phases = task_breakdown.get("implementation_phases", [])
        if not isinstance(phases, list):
            phases = []
        for phase in phases:
            if not isinstance(phase, dict):
                lines.append(f"- （跳过非对象阶段项: {type(phase).__name__}）")
                lines.append("")
                continue
            lines.extend([
                f"### {phase.get('phase', 'N/A')}",
                "",
                f"**周期**: {phase.get('duration', 'N/A')}",
                "",
                f"**重点**: {phase.get('focus', 'N/A')}",
                "",
                "**交付物**:",
                "",
            ])
            dels = phase.get("deliverables", [])
            if not isinstance(dels, list):
                dels = []
            for deliverable in dels:
                lines.append(f"- {deliverable}")
            lines.extend(["", "---", ""])
        
        # 风险缓解
        lines.extend(["## ⚠️ 风险与缓解措施", ""])
        risks = task_breakdown.get("risk_mitigation", [])
        if not isinstance(risks, list):
            risks = []
        for risk in risks:
            if not isinstance(risk, dict):
                lines.append(f"- {risk}")
                lines.append("")
                continue
            lines.extend([
                f"- **风险**: {risk.get('risk', 'N/A')}",
                f"  - **缓解措施**: {risk.get('mitigation', 'N/A')}",
                f"  - **负责人**: {risk.get('owner', 'N/A')}",
                "",
            ])
        
        lines.extend(["---", ""])
        
        # 下一步
        lines.extend([
            "## 下一步操作",
            "",
            "基于本任务分解方案，后续步骤将并行或串行执行：",
            "",
            "- **Step 4**: 全局规则设计（RuleEngineer Agent）",
            "- **Step 5**: 专项 Agent 配置（DomainExpert Agent）",
            "- **Step 6**: 私域数据抽取（UserPortraitMiner Agent）",
            "- **Step 7**: 质量检查（QAModerator Agent）",
            "- **Step 8**: 配置生成（ConfigAssembler Agent）",
            "",
        ])
        
        return "\n".join(lines)
    
    async def close(self):
        """关闭资源"""
        self.logger.info("CoordinatorAgent closing")
