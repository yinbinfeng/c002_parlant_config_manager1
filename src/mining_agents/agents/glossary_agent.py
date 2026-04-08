#!/usr/bin/env python3
"""Glossary Agent - 词汇体系设计 Agent"""

from pathlib import Path
from json_repair import repair_json
from typing import Dict, Any, List
from .base_agent import BaseAgent


class GlossaryAgent(BaseAgent):
    """Glossary Agent - 负责提取和定义专业术语体系"""

    _INVALID_REACT_SNIPPETS = (
        "interrupted me",
        "what can i do for you",
        "i noticed that you",
    )

    def _react_response_is_invalid(self, response: str) -> bool:
        low = (response or "").lower()
        return any(p in low for p in self._INVALID_REACT_SNIPPETS)

    def _parse_glossary_from_text(self, response: str):
        if not response or not str(response).strip():
            return None
        for candidate in self._extract_json_text_candidates(str(response)):
            glossary_terms = None
            try:
                glossary_terms = repair_json(candidate, return_objects=True)
            except Exception:
                try:
                    if self.json_validator:
                        ok, data, _ = self.json_validator.validate(candidate)
                        glossary_terms = data if ok else repair_json(candidate, return_objects=True)
                    else:
                        glossary_terms = repair_json(candidate, return_objects=True)
                except Exception:
                    glossary_terms = None
            if isinstance(glossary_terms, list) or isinstance(glossary_terms, dict):
                return glossary_terms
        return None

    def _persist_glossary(
        self,
        glossary_data,
        context: Dict[str, Any],
        output_dir_path: Path,
        message: str,
    ) -> Dict[str, Any]:
        import json as _json

        glossary_name = context.get("glossary_name", "insurance")
        glossary_file = output_dir_path / f"step3_glossary_{glossary_name}.json"
        glossary_file.write_text(
            _json.dumps(glossary_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        glossary_files = [str(glossary_file)]
        return {
            "glossary_files": glossary_files,
            "output_files": glossary_files,
            "glossary_terms": glossary_data,
            "message": message,
        }

    async def _fallback_direct_llm_glossary(self, react_prompt: str, context: Dict[str, Any]):
        tighten = (
            "\n\n### 输出要求（兜底轮次）\n"
            "仅输出 JSON：可为术语对象数组，或包含 terms/agent_id 等字段的对象；"
            "不要使用 Markdown 代码围栏，不要添加解释性文字。"
        )
        self.logger.info("GlossaryAgent：尝试直连 LLM（无工具）兜底生成术语表")
        response = await self.call_llm(react_prompt + tighten, context)
        if self._react_response_is_invalid(response):
            return None
        parsed = self._parse_glossary_from_text(response)
        if parsed is not None:
            return parsed
        try:
            fixed = await self._llm_fix_json_once(
                response,
                context,
                schema_hint="JSON array or JSON object",
            )
            return self._parse_glossary_from_text(fixed)
        except Exception:
            return None

    def _build_deep_research_brief(self, task: str, context: Dict[str, Any]) -> str:
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
            "请围绕该业务场景输出术语研究报告，覆盖：核心业务术语、用户常用表达、"
            "同义词、易混淆词、合规相关术语。"
            f" 业务描述={business_desc}；核心目标={core_goal}；行业={industry}"
        )

    async def _fallback_template_fill_glossary(self, task: str, context: Dict[str, Any]):
        prompt = (
            "你需要按固定JSON模板填充字段并决定词条数量。\n"
            "要求：terms 数量不少于 6 条；仅输出 JSON；内容必须与业务主题一致。\n"
            f"任务: {task}\n业务描述: {context.get('business_desc','')}\n\n"
            "JSON模板:\n"
            "{\n"
            '  "agent_id": "xxx_agent_001",\n'
            '  "remark": "xxx",\n'
            '  "fallback_source": "template_fill_mode",\n'
            '  "terms": []\n'
            "}\n"
        )
        response = await self.call_llm(prompt, context)
        parsed = self._parse_glossary_from_text(response)
        if parsed is None:
            try:
                fixed = await self._llm_fix_json_once(
                    response,
                    context,
                    schema_hint="JSON array or JSON object",
                )
                parsed = self._parse_glossary_from_text(fixed)
            except Exception:
                parsed = None
        if isinstance(parsed, dict):
            parsed.setdefault("fallback_source", "template_fill_mode")
            return parsed
        if isinstance(parsed, list):
            return {"fallback_source": "template_fill_mode", "terms": parsed}
        return None
    
    def __init__(self, name: str, orchestrator, **kwargs):
        """初始化 Glossary Agent
        
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
            self.logger.info("Glossary ReAct disabled by config (use_react=false)")
        
        # 从工具字典中获取工具
        self.deep_research_tool = self.tools.get('deep_research')
        self.json_validator = self.tools.get('json_validator')

    async def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return await self.run(task, context)
    
    async def run(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行任务
        
        Args:
            task: 任务描述
            context: 上下文信息
            
        Returns:
            执行结果
        """
        self.logger.info(f"Starting glossary design for task: {task}")
        
        # 提取上下文信息
        business_desc = context.get("business_desc", "")
        step2_atomic_tasks = context.get("step2_atomic_tasks") or context.get("atomic_tasks") or []
        step1_structured_requirements = context.get("step1_structured_requirements") or context.get("structured_requirements") or {}
        output_dir = context.get("output_dir", "./output")
        mock_mode = context.get("mock_mode", True)
        
        self.logger.info(f"Business description: {business_desc[:50]}...")
        self.logger.info(f"Mock mode: {mock_mode}")
        
        if mock_mode:
            return self._mock_run(task, context)
        else:
            return await self._real_run(task, context)
    
    def _mock_run(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Mock 模式执行
        
        Args:
            task: 任务描述
            context: 上下文信息
            
        Returns:
            模拟执行结果
        """
        import json as _json
        
        self.logger.info("Generating MOCK glossary design...")
        
        output_dir = Path(context.get("output_dir", "./output"))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        glossary_name = context.get("glossary_name", "insurance")
        glossary_file = output_dir / f"step3_glossary_{glossary_name}.json"
        
        mock_glossary = {
            "agent_id": "insurance_retention_agent_001",
            "remark": "保险挽留业务Agent专属术语表",
            "terms": [
                {
                    "term_id": f"{glossary_name}_term_001",
                    "name": "客户流失预警",
                    "description": "通过数据分析识别可能流失的客户，提前预警",
                    "synonyms": ["流失风险预警", "客户流失预测"],
                    "language": "zh-CN"
                },
                {
                    "term_id": f"{glossary_name}_term_002",
                    "name": "挽留策略",
                    "description": "针对可能流失客户制定的保留措施和方案",
                    "synonyms": ["留存策略", "客户保留方案"],
                    "language": "zh-CN"
                }
            ]
        }
        
        glossary_file.write_text(_json.dumps(mock_glossary, ensure_ascii=False, indent=2), encoding="utf-8")
        glossary_files = [str(glossary_file)]
        
        result = {
            "glossary_files": glossary_files,
            "output_files": glossary_files,
            "glossary_terms": mock_glossary,
            "message": "Glossary design completed successfully (MOCK mode)"
        }
        
        self.logger.info("Mock glossary design generated successfully")
        return result
    
    async def _real_run(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """真实模式执行（使用 ReAct 进行术语提取和验证）
        
        Args:
            task: 任务描述
            context: 上下文信息
            
        Returns:
            真实执行结果
        """
        self.logger.info("Generating real glossary design with ReAct...")
        
        # 提取上下文信息
        business_desc = context.get("business_desc", "")
        step2_atomic_tasks = context.get("step2_atomic_tasks") or context.get("atomic_tasks") or []
        step1_structured_requirements = context.get("step1_structured_requirements") or context.get("structured_requirements") or {}
        output_dir = context.get("output_dir", "./output")
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)
        mock_mode = bool(context.get("mock_mode", True))
        
        # 提取核心目标和行业参数
        core_goal = context.get("core_goal", business_desc[:200] if business_desc else "提取业务术语体系")
        industry = context.get("industry", "通用")
        
        # 从配置中加载 ReAct prompt 模板
        agent_config = self.config or {}
        task_prompts = agent_config.get('task_prompts', {})
        react_prompt_template = task_prompts.get(
            'design_glossary',
            self._get_default_glossary_prompt(task, business_desc, step2_atomic_tasks, step1_structured_requirements)
        )

        # 使用定向替换替代 str.format_map：
        # - 模板中包含 JSON 示例花括号 `{}`，会被 str.format 误判为占位符并导致格式化失败
        # - 失败会触发兜底逻辑，进而导致 {business_desc} 等占位符不被替换，生成泛化 glossary
        fmt_vars = {
            "task": task,
            "business_desc": business_desc,
            "step2_atomic_tasks": step2_atomic_tasks,
            "step1_structured_requirements": step1_structured_requirements,
            "glossary_name": context.get("glossary_name", "default"),
            "core_goal": core_goal,
            "industry": industry,
        }

        react_prompt = react_prompt_template
        if not isinstance(react_prompt, str):
            react_prompt = self._get_default_glossary_prompt(
                task,
                business_desc,
                step2_atomic_tasks,
                step1_structured_requirements,
            )
        else:
            for k, v in fmt_vars.items():
                react_prompt = react_prompt.replace(f"{{{k}}}", str(v))

        dr_brief = self._build_deep_research_brief(task, context)
        react_guard = (
            "\n\n【执行流程约束（必须遵守）】\n"
            f"1) 先调用 deep_research，query 必须使用以下完整调研任务说明：\n{dr_brief}\n"
            "2) deep_research 返回研究文本，不要把该结果当 JSON 解析；\n"
            "3) 再基于研究证据输出 parlant 术语 JSON；\n"
            "4) 最终输出前可调用 json_validator 做结构校验；\n"
            "5) 最终回答必须是 JSON 本体，不要附带说明。\n"
        )
        
        # 使用 ReActAgent 进行术语提取和验证
        response = await self.call_react_agent(react_prompt + react_guard, context)

        if self._react_response_is_invalid(response):
            self.logger.warning(
                "Detected invalid ReAct response (placeholder/interruption) in GlossaryAgent",
            )
            glossary_terms = None
        else:
            glossary_terms = self._parse_glossary_from_text(response)

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
            return await self._generate_glossary_without_deep_research(task, context)
        
        glossary_data = None
        if isinstance(glossary_terms, list):
            glossary_data = glossary_terms
        elif isinstance(glossary_terms, dict):
            glossary_data = glossary_terms
        
        if glossary_data is not None:
            self.logger.info(f"Successfully generated glossary data with ReAct")
            return self._persist_glossary(
                glossary_data,
                context,
                output_dir_path,
                "Glossary design completed successfully with ReAct",
            )

        fb = await self._fallback_direct_llm_glossary(react_prompt, context)
        if fb is not None:
            self.logger.info("Glossary recovered via direct LLM fallback (no tools)")
            return self._persist_glossary(
                fb,
                context,
                output_dir_path,
                "Glossary design completed successfully (direct LLM fallback)",
            )

        templ = await self._fallback_template_fill_glossary(task, context)
        if templ is not None:
            self.logger.warning("GlossaryAgent template-fill fallback activated")
            return self._persist_glossary(
                templ,
                context,
                output_dir_path,
                "Glossary design completed (template-fill fallback)",
            )

        if mock_mode:
            self.logger.warning("Mock mode enabled: Falling back to mock glossary")
            return self._mock_run(task, context)
        raise RuntimeError("GlossaryAgent：ReAct/直连/模板填充均失败，无法生成有效术语表。")
    
    def _get_default_glossary_prompt(self, task, business_desc, step2_atomic_tasks, step1_structured_requirements) -> str:
        """获取默认术语表设计提示词（配置降级保护）
        
        注意：提示词应从配置文件加载，此方法仅在配置缺失时作为降级保护
        """
        # 从配置中获取提示词模板
        prompt_template = self.task_prompts.get('design_glossary', '')
        if prompt_template:
            return prompt_template
        
        # 配置缺失时的最小化保护
        self.logger.warning("Design glossary prompt not found in config, using minimal fallback")
        return "请基于提供的业务信息，提取并定义专业术语体系（包含术语名称、定义、使用示例和相关术语）"
    
    async def _generate_glossary_without_deep_research(self, task, context):
        """不使用 Deep Research，仅依靠模型自身知识生成术语表（Real 模式降级用）
        
        Args:
            task: 任务描述
            context: 上下文信息
            
        Returns:
            术语表配置
        """
        self.logger.info("Generating glossary WITHOUT Deep Research, using model's own knowledge")
        
        # 获取提示词模板
        react_prompt_template = self._get_default_glossary_prompt(
            task,
            context.get("business_desc", ""),
            context.get("step2_atomic_tasks", []),
            context.get("step1_structured_requirements", []),
        )
        
        # 移除 Deep Research 相关的内容
        react_prompt = react_prompt_template.replace("\n\n## Deep Research 行业研究结果\n{deep_research_results}", "")
        react_prompt = react_prompt.replace("\n\n## Deep Research 行业研究结果\n[Deep Research 不可用]", "")
        
        # 使用 ReActAgent 生成术语表
        response = await self.call_react_agent(react_prompt, context)

        if self._react_response_is_invalid(response):
            glossary_terms = None
        else:
            glossary_terms = self._parse_glossary_from_text(response)

        glossary_data = None
        if isinstance(glossary_terms, list):
            glossary_data = glossary_terms
        elif isinstance(glossary_terms, dict):
            glossary_data = glossary_terms

        output_dir_path = Path(context.get("output_dir", "./output"))
        output_dir_path.mkdir(parents=True, exist_ok=True)

        if glossary_data is not None:
            self.logger.info("Successfully generated glossary without Deep Research")
            return self._persist_glossary(
                glossary_data,
                context,
                output_dir_path,
                "Glossary design completed successfully without Deep Research",
            )

        fb = await self._fallback_direct_llm_glossary(react_prompt, context)
        if fb is not None:
            self.logger.info("Glossary (no-DR path) recovered via direct LLM fallback")
            return self._persist_glossary(
                fb,
                context,
                output_dir_path,
                "Glossary design completed successfully (no DR, direct LLM fallback)",
            )
        templ = await self._fallback_template_fill_glossary(task, context)
        if templ is not None:
            return self._persist_glossary(
                templ,
                context,
                output_dir_path,
                "Glossary design completed (no DR, template-fill fallback)",
            )
        if context.get("mock_mode", True):
            self.logger.warning("Failed to generate glossary without Deep Research, using mock")
            return self._mock_run(task, context)
        raise RuntimeError(
            "GlossaryAgent：无 Deep Research 路径下 ReAct 与直连 LLM 均失败；real 模式禁止返回 mock。",
        )
