#!/usr/bin/env python3
"""需求分析 Agent - 负责需求澄清和问题生成"""

import re
from json_repair import repair_json
from typing import Dict, Any, List
from pathlib import Path
from .base_agent import BaseAgent


class RequirementAnalystAgent(BaseAgent):
    """需求分析 Agent - 负责需求澄清和问题生成
    
    主要职责：
    - 分析用户业务描述，识别模糊点和缺失信息
    - 使用 Deep Research 搜索行业最佳实践
    - 生成待澄清问题清单
    - 支持人工确认环节（Human-in-the-Loop）
    
    工作流程：
    1. 接收用户业务描述
    2. 头脑风暴分析模糊点
    3. Deep Research 搜索行业需求
    4. 生成 3-5 个待澄清问题
    5. 输出问题清单并等待用户确认
    """
    
    def __init__(self, name: str, orchestrator, **kwargs):
        """初始化 Agent
        
        Args:
            name: Agent 名称
            orchestrator: Agent 编排器
            **kwargs: 其他参数
        """
        super().__init__(name, orchestrator, **kwargs)
        
        # 初始化 ReActAgent（需要多轮推理和工具调用）
        self._init_react_agent()
        
        # 从工具字典中获取工具
        self.deep_research_tool = self.tools.get('deep_research')
        self.json_validator = self.tools.get('json_validator')
        
        # 初始化状态标志
        self.agent_initialization_attempted = True
    
    async def execute(self, task: str, context: dict) -> dict:
        """执行任务
        
        Args:
            task: 任务描述
            context: 上下文信息，包含：
                - business_desc: 业务描述
                - mock_mode: 是否使用 Mock 模式（默认 True）
                - output_dir: 输出目录
                
        Returns:
            执行结果，包含：
                - questions: 待澄清问题列表
                - output_files: 输出文件列表
                - metadata: 元数据
        """
        self.logger.info(f"Starting requirement analysis for task: {task[:50]}...")
        
        # 提取上下文信息
        business_desc = context.get("business_desc", "")
        mock_mode = context.get("mock_mode", True)
        output_dir = Path(context.get("output_dir", "./output/step1"))
        
        # 确保输出目录存在
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Business description: {business_desc[:50]}...")
        self.logger.info(f"Mock mode: {mock_mode}")
        
        # 生成问题
        if mock_mode:
            self.logger.info("Generating MOCK questions...")
            questions = self._generate_mock_questions(business_desc)
        else:
            # 真实模式优先走稳定的 ChatModel 调用（严格要求输出 JSON，避免 ReAct 混入思考文本导致解析失败）
            try:
                self.logger.info("Generating questions with LLM (JSON-only)...")
                questions = await self._generate_questions_with_llm(business_desc, context)
            except Exception as e:
                error_msg = f"LLM question generation failed in REAL mode: {e}"
                self.logger.error(error_msg)
                raise RuntimeError(error_msg) from e
        
        # 格式化为 Markdown
        markdown_content = self._format_questions_to_markdown(questions)
        
        # 写入文件
        output_file = output_dir / "step1_clarification_questions.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        self.logger.info(f"Questions written to {output_file}")
        
        # 同时保存为 JSON 格式（便于后续处理）
        json_file = output_dir / "step1_questions.json"
        if self.json_validator:
            self.json_validator.save_json(
                {"questions": questions, "business_desc": business_desc},
                str(json_file)
            )
            self.logger.info(f"Questions saved to {json_file}")
        
        return {
            "questions": questions,
            "output_files": [str(output_file), str(json_file)],
            "metadata": {
                "question_count": len(questions),
                "mock_mode": mock_mode,
                "business_desc_length": len(business_desc),
            }
        }

    async def _generate_questions_with_llm(self, business_desc: str, context: Dict) -> List[Dict[str, str]]:
        """使用基础 ChatModel 生成问题（强制 JSON-only 输出）。"""
        data_agent_results = context.get("data_agent_results", {}) or {}
        research_results = context.get("research_results", {}) or {}

        # 注意：不要直接复用 YAML 中包含 `{}` 的模板做 str.format（会触发 KeyError）。
        import json as _json
        prompt = (
            "你是一名专业的需求分析师。请基于以下信息，生成待澄清问题清单。\n\n"
            "## 业务描述（人工提供）\n"
            f"{business_desc}\n\n"
            "## Data Agent 分析结果（如有）\n"
            f"{_json.dumps(data_agent_results, ensure_ascii=False)}\n\n"
            "## 行业研究结果（如有）\n"
            f"{_json.dumps(research_results, ensure_ascii=False)}\n\n"
            "请生成 5-8 个待澄清问题，覆盖：目标用户、核心流程、术语表、集成需求、合规要求。\n\n"
            "【严格输出要求】\n"
            "1) 只输出 JSON 数组本体（以 '[' 开头，以 ']' 结尾），不要输出任何解释、思考、markdown、代码块标记。\n"
            "2) 数组元素为对象，字段仅包含：id, question, category, priority, rationale。\n"
            "3) priority 仅允许 high/medium/low。\n"
        )

        response = await self.call_llm(prompt, context)
        parsed = None
        try:
            parsed = repair_json(response.strip(), return_objects=True)
        except Exception:
            # 复用与 ReAct 相同的提取逻辑：截取第一个 JSON 数组
            start = response.find("[")
            end = response.rfind("]")
            if start != -1 and end != -1 and end > start:
                candidate = response[start : end + 1]
                # 优先用 JsonValidator 修复常见格式问题（单引号、尾逗号等）
                if self.json_validator:
                    ok, data, _msg = self.json_validator.validate(candidate)
                    if ok:
                        parsed = data
                    else:
                        parsed = repair_json(candidate, return_objects=True)
                else:
                    parsed = repair_json(candidate, return_objects=True)

        if not isinstance(parsed, list):
            raise ValueError("LLM output is not a JSON array")

        # 兼容：部分网关/模型会把“内容块列表”序列化为 JSON，例如：
        # [{"type":"thinking","thinking":"..."}, {"type":"text","text":"[...]"}]
        # 此时需要先从 text 块里取出真正的 JSON 问题数组再解析。
        if parsed and isinstance(parsed[0], dict) and "type" in parsed[0] and ("text" in parsed[0] or "thinking" in parsed[0]):
            text_payload = "".join(
                str(it.get("text", "")) for it in parsed if isinstance(it, dict) and it.get("type") == "text"
            ).strip()
            if text_payload:
                try:
                    parsed2 = repair_json(text_payload, return_objects=True)
                except Exception:
                    start = text_payload.find("[")
                    end = text_payload.rfind("]")
                    if start != -1 and end != -1 and end > start:
                        candidate2 = text_payload[start : end + 1]
                        if self.json_validator:
                            ok2, data2, _ = self.json_validator.validate(candidate2)
                            parsed2 = data2 if ok2 else repair_json(candidate2, return_objects=True)
                        else:
                            parsed2 = repair_json(candidate2, return_objects=True)
                    else:
                        parsed2 = None
                if isinstance(parsed2, list):
                    parsed = parsed2

        # 轻量校验：确保每项都有 id/question
        cleaned: List[Dict[str, str]] = []
        for idx, item in enumerate(parsed):
            if not isinstance(item, dict):
                continue
            # 兼容中英字段名（部分模型可能输出中文 key）
            qid = str(
                item.get("id")
                or item.get("ID")
                or item.get("编号")
                or item.get("问题ID")
                or f"Q{idx+1}"
            )
            qq = str(item.get("question") or item.get("问题") or item.get("question_text") or "").strip()
            if not qq:
                continue
            cleaned.append(
                {
                    "id": qid,
                    "question": qq,
                    "category": str(item.get("category") or item.get("类别") or "unspecified"),
                    "priority": str(item.get("priority") or item.get("优先级") or "medium"),
                    "rationale": str(item.get("rationale") or item.get("理由") or item.get("原因") or ""),
                }
            )

        if not cleaned:
            try:
                if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
                    self.logger.warning(
                        f"LLM output parsed but invalid question items; first_item_keys={list(parsed[0].keys())}"
                    )
            except Exception:
                pass
            raise ValueError("LLM output parsed but contains no valid questions")
        return cleaned
    
    def _generate_mock_questions(self, business_desc: str) -> List[Dict[str, str]]:
        """生成 Mock 问题（用于测试）
        
        Args:
            business_desc: 业务描述
            
        Returns:
            问题列表
        """
        self.logger.info("Generating mock questions based on business description")
        return self._generate_mock_questions_default(business_desc)
    
    def _generate_mock_questions_default(self, business_desc: str) -> List[Dict[str, str]]:
        """生成 Mock 问题（硬编码逻辑，用于降级）
        
        Args:
            business_desc: 业务描述
            
        Returns:
            问题列表
        """
        self.logger.info("Generating default mock questions")
        
        # 从配置中读取 Mock 问题模板
        agent_config = self.config or {}
        mock_questions_config = agent_config.get('mock_questions', {})
        self._debug_log(
            run_id="post-fix",
            hypothesis_id="H3",
            location="requirement_analyst_agent.py:149",
            message="Reading requirement_analyst config from orchestrator",
            data={
                "orchestrator_config_keys": list((self.orchestrator.config or {}).keys()),
                "has_agent_configs": "agent_configs" in (self.orchestrator.config or {}),
                "agent_configs_keys": list((self.orchestrator.config.get("agent_configs", {}) or {}).keys()),
                "requirement_analyst_found": bool(self.config),
                "mock_questions_keys": list((mock_questions_config or {}).keys()),
            },
        )
        
        # 获取基础问题列表
        base_questions = mock_questions_config.get('base_questions', [])
        
        # 如果配置中没有，使用默认值
        if not base_questions:
            base_questions = self._get_default_base_questions()
        
        # 根据业务描述长度决定是否添加附加问题
        threshold = mock_questions_config.get('detailed_desc_threshold', 200)
        if len(business_desc) > threshold:
            additional_questions = mock_questions_config.get('additional_questions_for_detailed_desc', [])
            if not additional_questions:
                additional_questions = self._get_default_additional_questions()
            base_questions.extend(additional_questions)
        
        self.logger.info(f"Generated {len(base_questions)} mock questions")
        return base_questions
    
    def _get_default_base_questions(self) -> List[Dict[str, str]]:
        """获取默认的基础问题列表（从配置文件读取）
        
        Returns:
            基础问题列表
        """
        # 从配置中读取基础问题模板
        agent_config = self.config or {}
        mock_questions_config = agent_config.get('mock_questions', {})
        base_questions = mock_questions_config.get('base_questions')
        
        # 如果配置中没有，从 fallback 读取
        if not base_questions:
            fallback_templates = agent_config.get('fallback_templates', {})
            base_questions = fallback_templates.get('default_base_questions')
        
        # 如果仍然没有，使用空列表作为最后的降级保护
        if not base_questions:
            self.logger.warning("No base questions found in config")
            base_questions = []
        
        return base_questions
    
    def _get_default_additional_questions(self) -> List[Dict[str, str]]:
        """获取默认的附加问题列表（从配置文件读取）
        
        Returns:
            附加问题列表
        """
        # 从配置中读取附加问题模板
        agent_config = self.config or {}
        mock_questions_config = agent_config.get('mock_questions', {})
        additional_questions = mock_questions_config.get('additional_questions_for_detailed_desc')
        
        # 如果配置中没有，从 fallback 读取
        if not additional_questions:
            fallback_templates = agent_config.get('fallback_templates', {})
            additional_questions = fallback_templates.get('default_additional_questions')
        
        # 如果仍然没有，使用空列表作为最后的降级保护
        if not additional_questions:
            self.logger.warning("No additional questions found in config")
            additional_questions = []
        
        return additional_questions
    
    async def _generate_questions_with_react(self, business_desc: str, context: Dict) -> List[Dict[str, str]]:
        """使用 ReAct 模式生成问题（自主推理 + 工具调用）
        
        Args:
            business_desc: 业务描述
            context: 上下文信息，包含 data_agent_results 等
            
        Returns:
            问题列表
        """
        # 从配置中加载 ReAct prompt 模板
        agent_config = self.config or {}
        task_prompts = agent_config.get('task_prompts', {})
        react_prompt_template = task_prompts.get(
            'react_questions_with_deep_research',
            self._get_default_react_prompt_template()
        )
        
        # 格式化 prompt
        react_prompt = react_prompt_template.format(
            business_desc=business_desc,
            data_agent_results=context.get("data_agent_results", {})
        )

        # 使用 ReActAgent 调用（会自动进行多轮推理和工具调用）
        response = await self.call_react_agent(react_prompt, context)

        def _extract_json_array(text: str):
            if not isinstance(text, str):
                return None
            cleaned = text.strip()
            # 去掉常见 code fence
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s*```$", "", cleaned)

            # 直接尝试整段解析
            try:
                obj = repair_json(cleaned, return_objects=True)
                return obj
            except Exception:
                pass

            # 尝试截取第一个 JSON 数组
            start = cleaned.find("[")
            end = cleaned.rfind("]")
            if start != -1 and end != -1 and end > start:
                candidate = cleaned[start : end + 1]
                try:
                    return repair_json(candidate, return_objects=True)
                except Exception:
                    return None
            return None

        parsed = _extract_json_array(response)
        if isinstance(parsed, list):
            self.logger.info(f"Successfully generated {len(parsed)} questions with ReAct")
            return parsed

        error_msg = "Failed to parse ReAct response as JSON array in REAL mode"
        self.logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    def _get_default_react_prompt_template(self) -> str:
        """获取默认的 ReAct prompt 模板（配置降级保护）
        
        注意：提示词应从配置文件加载，此方法仅在配置缺失时作为降级保护
        
        Returns:
            ReAct prompt 模板字符串
        """
        # 从配置中读取 ReAct prompt 模板
        react_prompt_template = self.task_prompts.get('react_questions_with_deep_research', '')
        
        # 如果配置中没有，使用最小化降级保护
        if not react_prompt_template:
            self.logger.warning("ReAct prompt template not found in config, using minimal fallback")
            react_prompt_template = "请分析业务描述，识别模糊点和缺失信息，生成待澄清问题清单（包含id, question, category, priority, rationale）。"
        
        return react_prompt_template
    
    def _get_default_markdown_template(self) -> str:
        """获取默认的 Markdown 输出模板（配置降级保护）
        
        注意：模板应从配置文件加载，此方法仅在配置缺失时作为降级保护
        
        Returns:
            Markdown 模板字符串
        """
        # 从配置中读取 Markdown 模板
        output_formatting = self.config.get('output_formatting', {})
        markdown_template = output_formatting.get('markdown_template', '')
        
        # 如果配置中没有，使用最小化降级保护
        if not markdown_template:
            self.logger.warning("Markdown template not found in config, using minimal fallback")
            markdown_template = "# Step 1: 需求澄清问题清单\n\n{questions_content}"
        
        return markdown_template
    
    def _format_questions_to_markdown(self, questions: List[Dict[str, str]]) -> str:
        """将问题列表格式化为 Markdown
        
        Args:
            questions: 问题列表
            
        Returns:
            Markdown 格式的问题清单
        """
        # 从配置中加载 Markdown 模板
        agent_config = self.config or {}
        output_formatting = agent_config.get('output_formatting', {})
        markdown_template = output_formatting.get('markdown_template')
        
        # 如果配置中没有，使用默认模板
        if not markdown_template:
            markdown_template = self._get_default_markdown_template()
        
        # 获取优先级图标映射
        priority_icons = self._get_default_priority_icons()
        
        # 格式化每个问题
        questions_content = ""
        for question in questions:
            priority = question.get('priority', 'medium')
            icon = priority_icons.get(priority, '🟡')
            questions_content += self._format_single_question(question, icon) + "\n"
        
        # 填充到模板
        markdown_content = markdown_template.format(questions_content=questions_content)
        
        return markdown_content
    
    def _format_single_question(self, question: Dict[str, str], priority_icon: str) -> str:
        """格式化单个问题为 Markdown（默认实现）
        
        Args:
            question: 问题字典
            priority_icon: 优先级图标
            
        Returns:
            Markdown 格式的单个问题
        """
        lines = [
            f"### {priority_icon} {question['id']}: {question['question']}",
            "",
            f"**类别**: `{question['category']}`",
            "",
        ]
        
        if "rationale" in question:
            lines.extend([
                f"**为什么问这个问题**: {question['rationale']}",
                "",
            ])
        
        lines.extend([
            "**您的回答**:",
            "",
            "```",
            "（请填写您的回答）",
            "```",
            "",
            "---",
            "",
        ])
        
        return "\n".join(lines)
    
    def _get_default_priority_icons(self) -> Dict[str, str]:
        """获取默认的优先级图标映射（配置降级保护）
        
        注意：图标映射应从配置文件加载，此方法仅在配置缺失时作为降级保护
        
        Returns:
            优先级图标字典
        """
        # 从配置中读取优先级图标映射
        output_formatting = self.config.get('output_formatting', {})
        priority_icons = output_formatting.get('priority_icons')
        
        # 如果配置中没有，使用默认图标作为降级保护
        if not priority_icons:
            self.logger.warning("Priority icons not found in config, using default fallback")
            priority_icons = {
                'high': '🔴',
                'medium': '🟡',
                'low': '⚪'
            }
        
        return priority_icons
    
    async def close(self):
        """关闭资源"""
        self.logger.info("RequirementAnalystAgent closing")
