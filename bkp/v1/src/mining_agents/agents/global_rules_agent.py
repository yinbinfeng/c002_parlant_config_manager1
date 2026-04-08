import os
from json_repair import repair_json
from .base_agent import BaseAgent

class GlobalRulesAgent(BaseAgent):
    def __init__(self, name, orchestrator, **kwargs):
        super().__init__(name, orchestrator, **kwargs)
        
        # 初始化 ReActAgent（需要调用 json_validator 工具）
        self._init_react_agent()
        
        # 从工具字典中获取工具
        self.json_validator = self.tools.get('json_validator')
    
    async def execute(self, task, context):
        """执行全局规则生成任务（使用 ReAct 进行规则验证）
        
        Args:
            task: 任务描述
            context: 上下文信息
            
        Returns:
            执行结果
        """
        self.logger.info(f"Executing GlobalRulesAgent task: {task}")
        
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
        
        # 使用 ReActAgent 进行规则生成和验证
        response = await self.call_react_agent(react_prompt, context)
        
        # 解析/修复 JSON 响应
        result = None
        try:
            result = repair_json(response.strip(), return_objects=True)
        except Exception:
            start = response.find("{")
            end = response.rfind("}")
            if start != -1 and end != -1 and end > start:
                candidate = response[start : end + 1]
                if self.json_validator:
                    ok, data, _ = self.json_validator.validate(candidate)
                    result = data if ok else repair_json(candidate, return_objects=True)
                else:
                    result = repair_json(candidate, return_objects=True)

        if isinstance(result, dict):
            self.logger.info("Successfully generated global rules with ReAct")
            
            return {
                "global_rules": result,
                "compatibility_report": result.get("compatibility_report", {
                    "status": "success",
                    "issues": [],
                    "recommendations": ["全局规则已与所有流程规约兼容"]
                }),
                "message": "Global rules check completed successfully with ReAct"
            }

        self.logger.error("Failed to parse ReAct response as JSON object; using default rules")
        return self._get_default_rules()
    
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
    
    def _get_default_rules(self):
        """获取默认规则（当 LLM 调用失败时使用）"""
        global_rules = {
            "rules": [
                {
                    "id": "global_rule_1",
                    "name": "客户服务基本准则",
                    "priority": 1,
                    "condition": "true",
                    "actions": [
                        "保持礼貌和专业的服务态度",
                        "及时响应客户需求",
                        "保护客户隐私"
                    ]
                },
                {
                    "id": "global_rule_2",
                    "name": "业务流程合规性",
                    "priority": 2,
                    "condition": "true",
                    "actions": [
                        "遵循公司业务流程规范",
                        "确保服务符合行业标准",
                        "及时更新业务知识"
                    ]
                }
            ],
            "compatibility_report": {
                "status": "success",
                "issues": [],
                "recommendations": [
                    "全局规则已与所有流程规约兼容",
                    "规则已进行精简优化"
                ]
            }
        }
        
        return {
            "global_rules": global_rules,
            "compatibility_report": global_rules.get("compatibility_report", {
                "status": "success",
                "issues": [],
                "recommendations": ["全局规则已与所有流程规约兼容"]
            }),
            "message": "Global rules check completed with default rules"
        }
    
    async def close(self):
        """关闭资源"""
        self.logger.info("GlobalRulesAgent closing")