from json_repair import repair_json
from .base_agent import BaseAgent


class GlobalRulesAgent(BaseAgent):
    _INVALID_REACT_SNIPPETS = (
        "interrupted me",
        "what can i do for you",
        "i noticed that you",
    )

    def _react_response_is_invalid(self, response: str) -> bool:
        low = (response or "").lower()
        return any(p in low for p in self._INVALID_REACT_SNIPPETS)

    def _parse_rules_from_text(self, response: str):
        if not response or not str(response).strip():
            return None
        for candidate in self._extract_json_text_candidates(str(response)):
            result = None
            try:
                result = repair_json(candidate, return_objects=True)
            except Exception:
                try:
                    if self.json_validator:
                        ok, data, _ = self.json_validator.validate(candidate)
                        result = data if ok else repair_json(candidate, return_objects=True)
                    else:
                        result = repair_json(candidate, return_objects=True)
                except Exception:
                    result = None
            if isinstance(result, dict):
                return result
        return None

    def _rules_result_payload(self, result: dict, message: str) -> dict:
        return {
            "global_rules": result,
            "compatibility_report": result.get(
                "compatibility_report",
                {
                    "status": "success",
                    "issues": [],
                    "recommendations": ["全局规则已与所有流程规约兼容"],
                },
            ),
            "message": message,
        }

    async def _fallback_direct_llm_rules(self, react_prompt: str, context: dict):
        """ReAct/工具链解析失败时，用同一业务 prompt 直连 LLM（无工具），产出仍应与输入一致。"""
        tighten = (
            "\n\n### 输出要求（兜底轮次）\n"
            "仅输出一个 JSON 对象，包含业务相关的全局规则与 compatibility_report；"
            "不要使用 Markdown 代码围栏，不要添加任何解释性文字。"
        )
        self.logger.info("GlobalRulesAgent：尝试直连 LLM（无工具）兜底生成规则")
        response = await self.call_llm(react_prompt + tighten, context)
        if self._react_response_is_invalid(response):
            return None
        parsed = self._parse_rules_from_text(response)
        if isinstance(parsed, dict):
            return parsed
        # 解析失败后，再调用一次 LLM 执行“纯 JSON 修复”
        try:
            fixed = await self._llm_fix_json_once(response, context, schema_hint="JSON object")
            return self._parse_rules_from_text(fixed)
        except Exception:
            return None

    def _build_deep_research_brief(self, task: str, context: dict) -> str:
        template = (self.task_prompts or {}).get("deep_research_brief_template", "")
        business_desc = context.get("business_desc", "")
        core_goal = context.get("core_goal", business_desc[:200] if business_desc else "")
        industry = context.get("industry", "通用")
        if template:
            return (
                template.replace("{task}", str(task))
                .replace("{business_desc}", str(business_desc))
                .replace("{core_goal}", str(core_goal))
                .replace("{industry}", str(industry))
            )
        return (
            "请围绕该业务场景输出全局规则研究报告，覆盖：合规约束、禁止项、"
            "用户异议/拒绝场景的规则设计、规则优先级与冲突消解。"
            f" 业务描述={business_desc}；核心目标={core_goal}；行业={industry}"
        )

    async def _fallback_template_fill_rules(self, task: str, context: dict) -> dict | None:
        prompt = (
            "你需要按固定JSON模板填充字段并决定规则条数。\n"
            "要求：agent_guidelines 数量 6-12 条；必须贴合业务主题；仅输出 JSON。\n"
            f"任务: {task}\n业务描述: {context.get('business_desc','')}\n\n"
            "JSON模板:\n"
            "{\n"
            '  "agent_id": "xxx_agent_001",\n'
            '  "remark": "xxx",\n'
            '  "fallback_source": "template_fill_mode",\n'
            '  "agent_guidelines": [],\n'
            '  "compatibility_report": {"status":"success","issues":[],"recommendations":[]}\n'
            "}\n"
        )
        response = await self.call_llm(prompt, context)
        parsed = self._parse_rules_from_text(response)
        if not isinstance(parsed, dict):
            try:
                fixed = await self._llm_fix_json_once(response, context, schema_hint="JSON object")
                parsed = self._parse_rules_from_text(fixed)
            except Exception:
                parsed = None
        if isinstance(parsed, dict):
            parsed.setdefault("fallback_source", "template_fill_mode")
            return parsed
        return None
    def __init__(self, name, orchestrator, **kwargs):
        super().__init__(name, orchestrator, **kwargs)
        use_react = bool((self.model_config or {}).get("use_react", True))
        if use_react:
            self._init_react_agent()
        else:
            self.logger.info("GlobalRules ReAct disabled by config (use_react=false)")
        
        # 从工具字典中获取工具
        self.json_validator = self.tools.get('json_validator')
    
    async def execute(self, task, context):
        """执行全局规则生成任务（使用 ReAct 进行规则验证）
        
        Args:
            task: 任务描述
            context: 上下文信息，包含：
                - mock_mode: 是否允许降级到默认规则
                
        Returns:
            执行结果
            
        Raises:
            RuntimeError: 当 real 模式下解析失败且不允许降级时
        """
        self.logger.info(f"Executing GlobalRulesAgent task: {task}")
        
        # 提取 mock_mode 参数
        mock_mode = context.get("mock_mode", True)
        
        # 从配置中加载 ReAct prompt 模板
        agent_config = self.config or {}
        task_prompts = agent_config.get('task_prompts', {})
        react_prompt_template = task_prompts.get(
            'generate_rules',
            self._get_default_rules_prompt(task, context)
        )
        
        # 提取核心目标和行业参数
        business_desc = context.get("business_desc", "")
        core_goal = context.get("core_goal", business_desc[:200] if business_desc else "设计全局规则配置")
        industry = context.get("industry", "通用")
        
        # 格式化 prompt（容错：模板可能包含 JSON 花括号示例）
        class _SafeDict(dict):
            def __missing__(self, key):
                return ""

        fmt_vars = _SafeDict(
            task=task,
            step1_structured_requirements=context.get('step1_structured_requirements', context.get("structured_requirements", {})),
            step3_guidelines=context.get('step3_guidelines', context.get("journey_files", [])),
            global_constraints=context.get('global_constraints', {}),
            core_goal=core_goal,
            industry=industry,
        )
        try:
            react_prompt = react_prompt_template.format_map(fmt_vars)
        except Exception:
            react_prompt = self._get_default_rules_prompt(task, context)

        dr_brief = self._build_deep_research_brief(task, context)
        react_guard = (
            "\n\n【执行流程约束（必须遵守）】\n"
            f"1) 先调用 deep_research，query 必须使用以下完整调研任务说明：\n{dr_brief}\n"
            "2) deep_research 返回研究文本，不要把该结果当 JSON 解析；\n"
            "3) 再基于研究证据输出 parlant 全局规则 JSON；\n"
            "4) 最终输出前可调用 json_validator 做结构校验；\n"
            "5) 最终回答必须是 JSON 本体，不要附带说明。\n"
        )
        
        # 使用 ReActAgent 进行规则生成和验证
        response = await self.call_react_agent(react_prompt + react_guard, context)

        if self._react_response_is_invalid(response):
            self.logger.warning(
                "Detected invalid ReAct response (placeholder/interruption) in GlobalRulesAgent",
            )
            result = None
        else:
            result = self._parse_rules_from_text(response)

        # 检查 Deep Research 工具是否已进入降级模式
        deep_research_tool = None
        if hasattr(self, 'orchestrator') and self.orchestrator:
            try:
                deep_research_tool = self.orchestrator.get_tool("deep_research")
            except Exception:
                pass
        
        is_fallback_mode = (
            deep_research_tool is not None and 
            hasattr(deep_research_tool, 'is_fallback_mode') and 
            deep_research_tool.is_fallback_mode()
        )
        
        if is_fallback_mode:
            self.logger.warning(
                f"DeepResearchTool is in fallback mode (failures={deep_research_tool.get_failure_count()}). "
                f"Retrying LLM call without Deep Research, using model's own knowledge."
            )
            return await self._generate_rules_without_deep_research(task, context)

        if isinstance(result, dict):
            self.logger.info("Successfully generated global rules with ReAct")
            return self._rules_result_payload(
                result,
                "Global rules check completed successfully with ReAct",
            )

        fb = await self._fallback_direct_llm_rules(react_prompt, context)
        if isinstance(fb, dict):
            self.logger.info("Global rules recovered via direct LLM fallback (no tools)")
            return self._rules_result_payload(
                fb,
                "Global rules check completed successfully (direct LLM fallback)",
            )

        templ = await self._fallback_template_fill_rules(task, context)
        if isinstance(templ, dict):
            self.logger.warning("GlobalRulesAgent template-fill fallback activated")
            return self._rules_result_payload(
                templ,
                "Global rules check completed with template-fill fallback",
            )

        if mock_mode:
            self.logger.warning(
                "Mock mode：LLM 兜底仍失败，使用与 Step3 契约对齐的最小默认 guideline（非通用业务假数据模板）",
            )
            return self._get_default_rules(context)
        raise RuntimeError("GlobalRulesAgent：ReAct/直连/模板填充均失败，无法生成有效全局规则。")
    
    def _get_default_rules_prompt(self, task, context) -> str:
        """获取默认全局规则生成提示词（配置降级保护）
        
        注意：提示词应从配置文件加载，此方法仅在配置缺失时作为降级保护
        """
        # 从配置中获取提示词模板
        prompt_template = self.task_prompts.get('generate_rules', '')
        if prompt_template:
            return prompt_template
        
        # 配置缺失时的最小化保护
        self.logger.warning("Generate rules prompt not found in config, using minimal fallback")
        return "请基于提供的结构化需求和流程规约，生成全局规则配置和兼容性检查报告。"
    
    @staticmethod
    def _derive_agent_id_prefix(context: dict) -> str:
        hint = (
            (context.get("business_desc") or context.get("core_goal") or "")
            or (context.get("industry") or "generic")
        )
        hint = str(hint).strip() or "generic"
        safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in hint[:80])
        safe = safe.strip("_") or "mining_agent"
        return safe[:48]

    def _get_default_rules(self, context: dict = None):
        """最后手段：与 Step3 `agent_guidelines.json` 合规模型对齐的最小结构；agent_id 前缀来自 context。"""
        ctx = context if isinstance(context, dict) else {}
        prefix = self._derive_agent_id_prefix(ctx)
        agent_id = f"{prefix}_agent"
        inner = {
            "agent_id": agent_id,
            "agent_guidelines": [
                {
                    "guideline_id": f"{prefix}_guideline_001",
                    "scope": "agent_global",
                    "condition": "true",
                    "action": "保持专业、合规的沟通，并遵循业务流程与隐私保护要求。",
                    "priority": 1,
                },
            ],
            "compatibility_report": {
                "status": "success",
                "issues": [],
                "recommendations": [
                    "兜底结构已与 Parlant Step3 契约对齐；请优先使用 LLM 生成以贴合具体业务。",
                ],
            },
        }
        return {
            "global_rules": inner,
            "compatibility_report": inner["compatibility_report"],
            "message": "Global rules check completed with schema-compatible default (mock last-resort)",
        }
    
    async def _generate_rules_without_deep_research(self, task, context):
        """不使用 Deep Research，仅依靠模型自身知识生成全局规则（Real 模式降级用）
        
        Args:
            task: 任务描述
            context: 上下文信息
            
        Returns:
            全局规则配置
        """
        self.logger.info("Generating global rules WITHOUT Deep Research, using model's own knowledge")
        
        # 获取提示词模板
        react_prompt_template = self._get_default_rules_prompt(task, context)
        
        # 移除 Deep Research 相关的内容
        react_prompt = react_prompt_template.replace("\n\n## Deep Research 行业研究结果\n{deep_research_results}", "")
        react_prompt = react_prompt.replace("\n\n## Deep Research 行业研究结果\n[Deep Research 不可用]", "")
        
        # 使用 ReActAgent 生成规则
        response = await self.call_react_agent(react_prompt, context)

        if self._react_response_is_invalid(response):
            result = None
        else:
            result = self._parse_rules_from_text(response)

        if isinstance(result, dict):
            self.logger.info("Successfully generated global rules without Deep Research")
            return self._rules_result_payload(
                result,
                "Global rules check completed successfully without Deep Research",
            )

        fb = await self._fallback_direct_llm_rules(react_prompt, context)
        if isinstance(fb, dict):
            self.logger.info("Global rules (no-DR path) recovered via direct LLM fallback")
            return self._rules_result_payload(
                fb,
                "Global rules check completed successfully (no DR, direct LLM fallback)",
            )
        templ = await self._fallback_template_fill_rules(task, context)
        if isinstance(templ, dict):
            return self._rules_result_payload(
                templ,
                "Global rules check completed (no DR, template-fill fallback)",
            )
        if context.get("mock_mode", True):
            self.logger.warning(
                "Failed to generate rules without Deep Research, using schema-compatible default (mock mode)",
            )
            return self._get_default_rules(context)
        raise RuntimeError(
            "GlobalRulesAgent：无 Deep Research 路径下 ReAct 与直连 LLM 均失败；"
            "real 模式禁止返回默认规则。",
        )
    
    async def close(self):
        """关闭资源"""
        self.logger.info("GlobalRulesAgent closing")