#!/usr/bin/env python3
"""Quality Agent - 质量检查 Agent"""

from pathlib import Path
from json_repair import repair_json
from typing import Dict, Any, List
from .base_agent import BaseAgent


class QualityAgent(BaseAgent):
    """Quality Agent - 负责对设计内容进行质量检查"""
    
    def __init__(self, name: str, orchestrator, **kwargs):
        """初始化 Quality Agent
        
        Args:
            name: Agent 名称
            orchestrator: Agent 编排器
            **kwargs: 其他参数
        """
        super().__init__(name, orchestrator, **kwargs)
        
        # 初始化 ReActAgent（需要多步骤质量检查和自验证）
        self._init_react_agent()
        
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
        self.logger.info(f"Starting quality check for task: {task}")
        
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
        self.logger.info("Generating MOCK quality check...")
        
        # 生成并落盘最小可用的模拟报告
        output_dir = context.get("output_dir", "./output")
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)
        qa_file = output_dir_path / "step3_qa_report_customer_service.json"
        import json as _json
        qa_file.write_text(
            _json.dumps(
                {
                    "mode": "mock",
                    "task": task,
                    "business_desc": (context.get("business_desc") or "")[:500],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        qa_files = [str(qa_file)]
        
        result = {
            "qa_files": qa_files,
            "output_files": qa_files,
            "message": "Quality check completed successfully (MOCK mode)"
        }
        
        self.logger.info("Mock quality check generated successfully")
        return result
    
    async def _real_run(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """真实模式执行（使用 ReAct 进行多步骤质量检查）
        
        Args:
            task: 任务描述
            context: 上下文信息
            
        Returns:
            真实执行结果
        """
        self.logger.info("Generating real quality check with ReAct...")
        
        # 提取上下文信息
        business_desc = context.get("business_desc", "")
        step2_atomic_tasks = context.get("step2_atomic_tasks") or context.get("atomic_tasks") or []
        step1_structured_requirements = context.get("step1_structured_requirements") or context.get("structured_requirements") or {}
        output_dir = context.get("output_dir", "./output")
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)
        
        # 提取核心目标和行业参数
        core_goal = context.get("core_goal", business_desc[:200] if business_desc else "执行质量检查")
        industry = context.get("industry", "通用")
        
        # 从配置中加载 ReAct prompt 模板
        agent_config = self.config or {}
        task_prompts = agent_config.get('task_prompts', {})
        react_prompt_template = task_prompts.get(
            'quality_check',
            self._get_default_quality_prompt(task, business_desc, step2_atomic_tasks, step1_structured_requirements)
        )

        # 格式化 prompt（容错：模板可能包含 JSON 花括号示例，导致 str.format 误判占位符）
        class _SafeDict(dict):
            def __missing__(self, key):
                return ""

        fmt_vars = _SafeDict(
            task=task,
            business_desc=business_desc,
            step2_atomic_tasks=step2_atomic_tasks,
            step1_structured_requirements=step1_structured_requirements,
            core_goal=core_goal,
            industry=industry,
        )
        try:
            react_prompt = react_prompt_template.format_map(fmt_vars)
        except Exception:
            # 兜底：使用默认模板（避免配置模板中的花括号冲突）
            react_prompt = self._get_default_quality_prompt(task, business_desc, step2_atomic_tasks, step1_structured_requirements)
        
        # 使用 ReActAgent 进行多步骤检查
        response = await self.call_react_agent(react_prompt, context)

        quality_report = None
        try:
            quality_report = repair_json(response.strip(), return_objects=True)
        except Exception:
            start = response.find("{")
            end = response.rfind("}")
            if start != -1 and end != -1 and end > start:
                candidate = response[start : end + 1]
                if self.json_validator:
                    ok, data, _ = self.json_validator.validate(candidate)
                    quality_report = data if ok else repair_json(candidate, return_objects=True)
                else:
                    quality_report = repair_json(candidate, return_objects=True)

        if isinstance(quality_report, dict):
            self.logger.info("Successfully generated quality report with ReAct")
            
            qa_file = output_dir_path / "step3_qa_report_customer_service.json"
            import json as _json
            qa_file.write_text(_json.dumps(quality_report, ensure_ascii=False, indent=2), encoding="utf-8")
            qa_files = [str(qa_file)]
            
            result = {
                "qa_files": qa_files,
                "output_files": qa_files,
                "quality_report": quality_report,
                "message": "Quality check completed successfully with ReAct"
            }
            
            return result

        error_msg = "Failed to parse ReAct response as JSON object in REAL mode"
        self.logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    def _get_default_quality_prompt(self, task, business_desc, step2_atomic_tasks, step1_structured_requirements) -> str:
        """获取默认质量检查提示词（配置降级保护）
        
        注意：提示词应从配置文件加载，此方法仅在配置缺失时作为降级保护
        """
        # 从配置中获取提示词模板
        prompt_template = self.task_prompts.get('quality_check', '')
        if prompt_template:
            return prompt_template
        
        # 配置缺失时的最小化保护
        self.logger.warning("Quality check prompt not found in config, using minimal fallback")
        return "请基于提供的业务信息，执行质量检查（包含规则冲突、状态机、工具调用、chat_state一致性和condition逻辑检查），返回质量报告。"
