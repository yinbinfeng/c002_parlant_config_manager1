#!/usr/bin/env python3
"""Glossary Agent - 词汇体系设计 Agent"""

from pathlib import Path
from json_repair import repair_json
from typing import Dict, Any, List
from .base_agent import BaseAgent


class GlossaryAgent(BaseAgent):
    """Glossary Agent - 负责提取和定义专业术语体系"""
    
    def __init__(self, name: str, orchestrator, **kwargs):
        """初始化 Glossary Agent
        
        Args:
            name: Agent 名称
            orchestrator: Agent 编排器
            **kwargs: 其他参数
        """
        super().__init__(name, orchestrator, **kwargs)
        
        # 初始化 ReActAgent（需要调用 json_validator 工具）
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

        # 格式化 prompt（容错：模板里可能包含额外占位符，如 {glossary_name}）
        class _SafeDict(dict):
            def __missing__(self, key):
                return ""

        fmt_vars = _SafeDict(
            task=task,
            business_desc=business_desc,
            step2_atomic_tasks=step2_atomic_tasks,
            step1_structured_requirements=step1_structured_requirements,
            glossary_name=context.get("glossary_name", "default"),
            core_goal=core_goal,
            industry=industry,
        )
        try:
            react_prompt = react_prompt_template.format_map(fmt_vars)
        except Exception:
            react_prompt = self._get_default_glossary_prompt(task, business_desc, step2_atomic_tasks, step1_structured_requirements)
        
        # 使用 ReActAgent 进行术语提取和验证
        response = await self.call_react_agent(react_prompt, context)

        glossary_terms = None
        try:
            glossary_terms = repair_json(response.strip(), return_objects=True)
        except Exception:
            start = response.find("[")
            end = response.rfind("]")
            if start != -1 and end != -1 and end > start:
                candidate = response[start : end + 1]
                if self.json_validator:
                    ok, data, _ = self.json_validator.validate(candidate)
                    glossary_terms = data if ok else repair_json(candidate, return_objects=True)
                else:
                    glossary_terms = repair_json(candidate, return_objects=True)

        import json as _json
        
        glossary_data = None
        if isinstance(glossary_terms, list):
            glossary_data = glossary_terms
        elif isinstance(glossary_terms, dict):
            glossary_data = glossary_terms
        
        if glossary_data is not None:
            self.logger.info(f"Successfully generated glossary data with ReAct")
            
            glossary_name = context.get("glossary_name", "insurance")
            glossary_file = output_dir_path / f"step3_glossary_{glossary_name}.json"
            glossary_file.write_text(_json.dumps(glossary_data, ensure_ascii=False, indent=2), encoding="utf-8")
            glossary_files = [str(glossary_file)]
            
            result = {
                "glossary_files": glossary_files,
                "output_files": glossary_files,
                "glossary_terms": glossary_data,
                "message": "Glossary design completed successfully with ReAct"
            }
            
            return result

        error_msg = "Failed to parse ReAct response as JSON in REAL mode"
        self.logger.error(error_msg)
        raise RuntimeError(error_msg)
    
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
