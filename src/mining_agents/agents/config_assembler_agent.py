#!/usr/bin/env python3
"""配置组装师 Agent - 负责组装最终的 Parlant Agent 配置文件"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from json_repair import repair_json
from .base_agent import BaseAgent


class ConfigAssemblerAgent(BaseAgent):
    """配置组装师 Agent - 负责组装最终的 Parlant Agent 配置文件
    
    主要职责：
    - 收集 Step 1-7 的所有产出物
    - 整合并组装成完整的 Parlant Agent 配置
    - 生成 YAML 和 JSON 两种格式的配置
    - 进行最终验证和完整性检查
    - 提供配置说明和使用指南
    
    输出格式：
    - YAML: 适合人工阅读和编辑
    - JSON: 适合程序解析和处理
    - Markdown: 配置说明文档
    """
    
    def __init__(self, name: str, orchestrator, **kwargs):
        """初始化 Agent
        
        Args:
            name: Agent 名称
            orchestrator: Agent 编排器
            **kwargs: 其他参数
        """
        super().__init__(name, orchestrator, **kwargs)
        
        # 从工具字典中获取工具
        self.deep_research_tool = self.tools.get('deep_research')
        self.json_validator = self.tools.get('json_validator')
        
        # 尝试导入 yaml
        try:
            import yaml
            self.yaml = yaml
            self.logger.info("PyYAML imported successfully")
        except ImportError:
            self.yaml = None
            self.logger.warning("PyYAML not available, will use JSON only")
    
    async def execute(self, task: str, context: dict) -> dict:
        """执行任务
        
        Args:
            task: 任务描述
            context: 上下文信息，包含：
                - business_desc: 业务描述
                - step1_output: Step 1 输出
                - step2_output: Step 2 输出
                - step3_output: Step 3 输出
                - step4_output: Step 4 输出
                - step5_output: Step 5 输出
                - step6_output: Step 6 输出
                - step7_output: Step 7 输出
                - mock_mode: 是否使用 Mock 模式
                - output_dir: 输出目录
                
        Returns:
            执行结果，包含：
                - final_config: 最终配置
                - config_files: 配置文件列表
                - validation_result: 验证结果
                - usage_guide: 使用指南
                - output_files: 输出文件列表
        """
        self.logger.info(f"Starting configuration assembly for task: {task[:50]}...")
        
        # 提取上下文信息
        business_desc = context.get("business_desc", "")
        mock_mode = context.get("mock_mode", True)
        output_dir = Path(context.get("output_dir", "./output/step8"))
        
        # 收集所有步骤的输出
        all_step_outputs = {
            "step1": context.get("step1_output", {}),
            "step2": {
                "expert_opinions": context.get("step2_expert_opinions", []),
                "user_concerns": context.get("step2_user_concerns", []),
                "debate_summary": context.get("step2_requirement_defense", []),
            },
            "step3": context.get("step3_task_breakdown", {}),
            "step4": context.get("step4_global_rules", {}),
            "step5": context.get("step5_domain_config", {}),
            "step6": context.get("step6_user_portraits", {}),
            "step7": context.get("step7_quality_report", {}),
        }
        
        # 确保输出目录存在
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Business description: {business_desc[:50]}...")
        self.logger.info(f"Mock mode: {mock_mode}")
        self.logger.info(f"Collected outputs from {len([k for k, v in all_step_outputs.items() if v])} steps")
        
        # 组装最终配置
        self.logger.info("Assembling final configuration...")
        final_config = await self._assemble_final_config(all_step_outputs, business_desc, mock_mode=mock_mode)
        
        # 验证配置
        self.logger.info("Validating final configuration...")
        validation_result = self._validate_config(final_config)
        
        # 生成配置文件
        self.logger.info("Generating configuration files...")
        config_files = self._generate_config_files(final_config, output_dir)
        
        # 生成使用指南
        usage_guide = self._generate_usage_guide(final_config, business_desc)
        
        # 写入使用指南
        guide_file = output_dir / "README.md"
        with open(guide_file, 'w', encoding='utf-8') as f:
            f.write(usage_guide)
        
        self.logger.info(f"Usage guide written to {guide_file}")
        
        # 组装输出
        output_files = config_files + [str(guide_file)]
        
        return {
            "final_config": final_config,
            "config_files": config_files,
            "validation_result": validation_result,
            "usage_guide": usage_guide,
            "output_files": output_files,
            "metadata": {
                "mock_mode": mock_mode,
                "config_version": final_config.get("metadata", {}).get("version", "1.0.0"),
                "generated_at": final_config.get("metadata", {}).get("generated_at", ""),
                "total_components": self._count_components(final_config),
            }
        }
    
    async def _assemble_final_config(self, all_step_outputs: Dict, business_desc: str, mock_mode: bool = True) -> Dict[str, Any]:
        """组装最终配置
        
        Args:
            all_step_outputs: 所有步骤的输出
            business_desc: 业务描述
            mock_mode: 是否允许降级到默认配置
            
        Returns:
            最终配置字典
            
        Raises:
            RuntimeError: 当 real 模式下解析失败且不允许降级时
        """
        self.logger.info("Assembling components from all steps...")
        
        # 从配置文件获取提示词模板
        prompt_template = self.task_prompts.get('assemble_config', '')
        
        if not prompt_template:
            self.logger.warning("Assemble config prompt not found in config, using default prompt")
            # 使用默认提示词（向后兼容）
            prompt = self._get_default_assemble_prompt(business_desc, all_step_outputs)
        else:
            # 填充提示词模板
            prompt = prompt_template.format(
                business_desc=business_desc,
                all_step_outputs=all_step_outputs
            )

        # 调用大模型
        response = await self.call_llm(prompt)
        
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
        
        if result:
            self.logger.info("Successfully generated Parlant config with LLM")
            return result
        else:
            error_msg = "Failed to parse LLM response in REAL mode"
            self.logger.error(error_msg)
            
            # Real 模式下禁止降级到默认配置，直接抛出异常
            if not mock_mode:
                raise RuntimeError(error_msg)
            
            # Mock 模式下允许降级
            self.logger.warning("Mock mode enabled: Falling back to default config")
            return self._get_default_config(all_step_outputs, business_desc)
    
    def _get_default_assemble_prompt(self, business_desc: str, all_step_outputs: Dict) -> str:
        """获取默认配置组装提示词（配置降级保护）
        
        注意：提示词应从配置文件加载，此方法仅在配置缺失时作为降级保护
        """
        # 从配置中获取提示词模板
        prompt_template = self.task_prompts.get('assemble_config', '')
        if prompt_template:
            return prompt_template
        
        # 配置缺失时的最小化保护
        self.logger.warning("Assemble config prompt not found in config, using minimal fallback")
        return "请基于提供的业务描述和各阶段产出物，生成完整的 Parlant Agent 配置（包含元数据、Agent配置、Journeys、Guidelines、Tools、Glossary、Rules、Knowledge Base等）"

    def _get_default_config(self, all_step_outputs: Dict, business_desc: str) -> Dict[str, Any]:
        """获取默认配置（当 LLM 调用失败时使用）
        
        Args:
            all_step_outputs: 所有步骤的输出
            business_desc: 业务描述
            
        Returns:
            默认配置字典
        """
        # 基础元数据
        final_config = {
            "metadata": {
                "name": f"mining_agents_config_{self._sanitize_name(business_desc)[:20]}",
                "version": "1.0.0",
                "generated_at": "2026-03-20T00:00:00Z",
                "business_description": business_desc,
                "steps_completed": ["Step 1", "Step 2", "Step 3", "Step 4", "Step 5", "Step 6", "Step 7"],
            },
            
            # Step 1: 需求澄清
            "requirements": {
                "clarification_questions": all_step_outputs.get("step1", {}).get("questions", []),
            },
            
            # Step 2: 辩论结果
            "debate_results": {
                "expert_opinions": all_step_outputs.get("step2", {}).get("expert_opinions", []),
                "user_concerns": all_step_outputs.get("step2", {}).get("user_concerns", []),
            },
            
            # Step 3: 任务分解
            "task_breakdown": all_step_outputs.get("step3", {}).get("components", []),
            
            # Step 4: 全局规则
            "global_rules": {
                "categories": all_step_outputs.get("step4", {}).get("rule_categories", {}),
                "rules": all_step_outputs.get("step4", {}).get("all_rules", []),
                "conflict_resolution": all_step_outputs.get("step4", {}).get("conflict_resolution", {}),
            },
            
            # Step 5: 领域配置
            "domain_configuration": {
                "journeys": all_step_outputs.get("step5", {}).get("journey_designs", []),
                "guidelines": all_step_outputs.get("step5", {}).get("guideline_designs", []),
                "tools": all_step_outputs.get("step5", {}).get("tool_definitions", []),
                "glossary": all_step_outputs.get("step5", {}).get("glossary", []),
            },
            
            # Step 6: 数据洞察
            "data_insights": {
                "user_portraits": all_step_outputs.get("step6", {}).get("user_portraits", {}),
                "conversation_patterns": all_step_outputs.get("step6", {}).get("conversation_patterns", []),
                "common_issues": all_step_outputs.get("step6", {}).get("common_issues", []),
                "pain_points": all_step_outputs.get("step6", {}).get("pain_points", []),
                "optimization_suggestions": all_step_outputs.get("step6", {}).get("optimization_suggestions", []),
            },
            
            # Step 7: 质量报告
            "quality_assurance": {
                "overall_score": all_step_outputs.get("step7", {}).get("overall_score", 0),
                "quality_level": all_step_outputs.get("step7", {}).get("quality_level", "N/A"),
                "issues_found": all_step_outputs.get("step7", {}).get("issues_found", []),
                "recommendations": all_step_outputs.get("step7", {}).get("recommendations", []),
            },
        }
        
        # 转换为 Parlant 格式
        return self._convert_to_parlant_format(final_config)
    
    def _convert_to_parlant_format(self, config: Dict) -> Dict:
        """转换为 Parlant 格式
        
        Args:
            config: 原始配置
            
        Returns:
            Parlant 格式的配置
        """
        self.logger.info("Converting to Parlant format...")
        
        domain_config = config.get("domain_configuration", {})
        global_rules = config.get("global_rules", {})
        
        parlant_config = {
            "metadata": config.get("metadata", {}),
            
            # Agent 配置
            "agent": {
                "name": config["metadata"].get("name", "mining_agents_agent"),
                "description": config["metadata"].get("business_description", ""),
                "version": config["metadata"].get("version", "1.0.0"),
            },
            
            # Journeys (用户旅程)
            "journeys": [],
            
            # Guidelines (指导原则)
            "guidelines": [],
            
            # Tools (工具)
            "tools": [],
            
            # Glossary (术语表)
            "glossary": [],
            
            # Rules (规则)
            "rules": {
                "behavioral_rules": [],
                "compliance_rules": [],
                "business_rules": [],
            },
            
            # Knowledge Base (知识库)
            "knowledge_base": {
                "faq": [],
                "documents": [],
            },
            
            # Configuration (其他配置)
            "configuration": {
                "logging": {
                    "level": "INFO",
                },
                "performance": {
                    "max_response_time_seconds": 2,
                    "target_resolution_rate": 0.80,
                    "target_satisfaction_score": 4.5,
                },
            },
        }
        
        # 转换 Journeys
        journeys = domain_config.get("journeys", [])
        for journey in journeys:
            parlant_journey = {
                "id": journey.get("id", ""),
                "name": journey.get("name", ""),
                "description": journey.get("description", ""),
                "trigger": journey.get("trigger", ""),
                "priority": journey.get("priority", "medium"),
                "states": [],
            }
            
            # 转换状态
            for state in journey.get("states", []):
                parlant_state = {
                    "id": state.get("state_id", ""),
                    "name": state.get("state_name", ""),
                    "actions": state.get("actions", []),
                    "sample_dialogue": state.get("sample_dialogue", ""),
                    "transitions": state.get("transitions", []),
                }
                parlant_journey["states"].append(parlant_state)
            
            parlant_config["journeys"].append(parlant_journey)
        
        # 转换 Guidelines
        guidelines = domain_config.get("guideline_designs", [])
        for guideline in guidelines:
            parlant_guideline = {
                "id": guideline.get("id", ""),
                "category": guideline.get("category", ""),
                "name": guideline.get("name", ""),
                "description": guideline.get("description", ""),
                "specifications": guideline.get("guidelines", []),
            }
            parlant_config["guidelines"].append(parlant_guideline)
        
        # 转换 Tools
        tools = domain_config.get("tool_definitions", [])
        for tool in tools:
            parlant_tool = {
                "id": tool.get("id", ""),
                "name": tool.get("name", ""),
                "description": tool.get("description", ""),
                "api_endpoint": tool.get("api_endpoint", ""),
                "authentication": tool.get("authentication", ""),
                "input_parameters": tool.get("input_parameters", []),
                "output_schema": tool.get("output_schema", {}),
            }
            parlant_config["tools"].append(parlant_tool)
        
        # 转换 Glossary
        glossary = domain_config.get("glossary", [])
        for term in glossary:
            parlant_term = {
                "term": term.get("term", ""),
                "definition": term.get("definition", ""),
                "full_name": term.get("full_name", ""),
                "usage_examples": term.get("usage_examples", []),
                "related_terms": term.get("related_terms", []),
            }
            parlant_config["glossary"].append(parlant_term)
        
        # 转换 Rules
        rules = global_rules.get("rules", [])
        for rule in rules:
            parlant_rule = {
                "id": rule.get("id", ""),
                "category": rule.get("category", ""),
                "name": rule.get("name", ""),
                "description": rule.get("description", ""),
                "rule_text": rule.get("rule_text", ""),
                "enforcement": rule.get("enforcement", "should"),
                "priority": rule.get("priority", "medium"),
            }
            
            category = rule.get("category", "")
            if category == "compliance_rules":
                parlant_config["rules"]["compliance_rules"].append(parlant_rule)
            elif category == "business_rules":
                parlant_config["rules"]["business_rules"].append(parlant_rule)
            else:
                parlant_config["rules"]["behavioral_rules"].append(parlant_rule)
        
        return parlant_config
    
    def _validate_config(self, config: Dict) -> Dict[str, Any]:
        """验证配置
        
        Args:
            config: 待验证的配置
            
        Returns:
            验证结果
        """
        self.logger.info("Running validation checks...")
        
        validation_checks = []
        errors = []
        warnings = []
        
        # 检查必需字段
        required_fields = ["metadata", "agent", "journeys", "guidelines", "tools", "glossary"]
        for field in required_fields:
            if field in config:
                validation_checks.append({
                    "field": field,
                    "status": "pass",
                    "message": f"Field '{field}' present"
                })
            else:
                validation_checks.append({
                    "field": field,
                    "status": "fail",
                    "message": f"Field '{field}' missing"
                })
                errors.append(f"Missing required field: {field}")
        
        # 检查 Journeys
        journeys = config.get("journeys", [])
        if len(journeys) > 0:
            validation_checks.append({
                "field": "journeys",
                "status": "pass",
                "message": f"{len(journeys)} journeys defined"
            })
            
            # 检查每个 Journey 的状态
            for journey in journeys:
                if not journey.get("states"):
                    warnings.append(f"Journey '{journey.get('id', 'N/A')}' has no states defined")
        else:
            validation_checks.append({
                "field": "journeys",
                "status": "warning",
                "message": "No journeys defined"
            })
            warnings.append("No journeys defined in configuration")
        
        # 检查 Tools
        tools = config.get("tools", [])
        if len(tools) > 0:
            validation_checks.append({
                "field": "tools",
                "status": "pass",
                "message": f"{len(tools)} tools defined"
            })
        else:
            validation_checks.append({
                "field": "tools",
                "status": "warning",
                "message": "No tools defined"
            })
            warnings.append("No tools defined in configuration")
        
        # 检查 Glossary
        glossary = config.get("glossary", [])
        if len(glossary) > 0:
            validation_checks.append({
                "field": "glossary",
                "status": "pass",
                "message": f"{len(glossary)} terms defined"
            })
        else:
            validation_checks.append({
                "field": "glossary",
                "status": "warning",
                "message": "No glossary terms defined"
            })
        
        # 总体验证结果
        is_valid = len(errors) == 0
        
        return {
            "is_valid": is_valid,
            "total_checks": len(validation_checks),
            "passed": len([c for c in validation_checks if c["status"] == "pass"]),
            "warnings": len(warnings),
            "errors": len(errors),
            "checks": validation_checks,
            "error_list": errors,
            "warning_list": warnings,
        }
    
    def _generate_config_files(self, config: Dict, output_dir: Path) -> List[str]:
        """生成配置文件
        
        Args:
            config: 最终配置
            output_dir: 输出目录
            
        Returns:
            生成的文件路径列表
        """
        generated_files = []
        
        # 生成 JSON 配置
        import json as _json
        json_file = output_dir / "parlant_config.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            _json.dump(config, f, ensure_ascii=False, indent=2)
        generated_files.append(str(json_file))
        self.logger.info(f"JSON config written to {json_file}")
        
        # 生成 YAML 配置（如果可用）
        if self.yaml:
            yaml_file = output_dir / "parlant_config.yaml"
            with open(yaml_file, 'w', encoding='utf-8') as f:
                self.yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
            generated_files.append(str(yaml_file))
            self.logger.info(f"YAML config written to {yaml_file}")
        
        # 生成简化版配置（仅核心部分）
        minimal_config = {
            "metadata": config.get("metadata", {}),
            "agent": config.get("agent", {}),
            "journeys": config.get("journeys", []),
            "tools": config.get("tools", []),
        }
        
        minimal_json_file = output_dir / "parlant_config.minimal.json"
        with open(minimal_json_file, 'w', encoding='utf-8') as f:
            _json.dump(minimal_config, f, ensure_ascii=False, indent=2)
        generated_files.append(str(minimal_json_file))
        self.logger.info(f"Minimal JSON config written to {minimal_json_file}")
        
        return generated_files
    
    def _generate_usage_guide(self, config: Dict, business_desc: str) -> str:
        """生成使用指南
        
        Args:
            config: 最终配置
            business_desc: 业务描述
            
        Returns:
            Markdown 格式的使用指南
        """
        lines = [
            "# Parlant Agent 配置说明",
            "",
            f"**业务场景**: {business_desc}",
            f"**配置版本**: {config.get('metadata', {}).get('version', '1.0.0')}",
            f"**生成日期**: {config.get('metadata', {}).get('generated_at', 'N/A')}",
            "",
            "---",
            "",
            "## 📋 配置概览",
            "",
            f"- **Journeys (用户旅程)**: {len(config.get('journeys', []))} 个",
            f"- **Guidelines (指导原则)**: {len(config.get('guidelines', []))} 个",
            f"- **Tools (工具集成)**: {len(config.get('tools', []))} 个",
            f"- **Glossary (术语表)**: {len(config.get('glossary', []))} 条",
            f"- **Rules (规则)**: {sum(len(v) for k, v in config.get('rules', {}).items())} 条",
            "",
        ]
        
        # Journeys 列表
        journeys = config.get("journeys", [])
        if journeys:
            lines.extend([
                "## 🗺️ Journeys (用户旅程)",
                "",
            ])
            for journey in journeys:
                lines.extend([
                    f"### {journey.get('id', 'N/A')}: {journey.get('name', 'N/A')}",
                    "",
                    f"**触发条件**: {journey.get('trigger', 'N/A')}",
                    f"**优先级**: {journey.get('priority', 'N/A')}",
                    f"**状态数**: {len(journey.get('states', []))}",
                    "",
                ])
            lines.extend(["---", ""])
        
        # Tools 列表
        tools = config.get("tools", [])
        if tools:
            lines.extend([
                "## 🛠️ Tools (工具集成)",
                "",
            ])
            for tool in tools:
                lines.extend([
                    f"### {tool.get('id', 'N/A')}: {tool.get('name', 'N/A')}",
                    "",
                    f"**API**: `{tool.get('api_endpoint', 'N/A')}`",
                    f"**认证**: {tool.get('authentication', 'N/A')}",
                    "",
                ])
            lines.extend(["---", ""])
        
        # 部署说明
        lines.extend([
            "## 🚀 部署指南",
            "",
            "### 1. 准备环境",
            "",
            "```bash",
            "# 安装依赖",
            "pip install parlant-sdk  # 假设的 SDK",
            "```",
            "",
            "### 2. 加载配置",
            "",
            "```python",
            "import parlant",
            "",
            "# 加载配置",
            "config = parlant.load_config('parlant_config.yaml')",
            "",
            "# 初始化 Agent",
            "agent = parlant.Agent(config)",
            "```",
            "",
            "### 3. 启动服务",
            "",
            "```python",
            "# 启动 Agent 服务",
            "agent.start()",
            "```",
            "",
            "---",
            "",
        ])
        
        # 配置说明
        lines.extend([
            "## 📁 文件说明",
            "",
            "```",
            "output/step8/",
            "├── parlant_config.json          # 完整 JSON 配置",
            "├── parlant_config.yaml          # 完整 YAML 配置",
            "├── parlant_config.minimal.json  # 简化版配置",
            "└── README.md                    # 本文件",
            "```",
            "",
            "---",
            "",
        ])
        
        # 下一步
        lines.extend([
            "## ✅ 完成！",
            "",
            "您已成功生成完整的 Parlant Agent 配置。",
            "",
            "**下一步操作**:",
            "",
            "1. 审查生成的配置文件",
            "2. 根据实际需求调整参数",
            "3. 部署到测试环境验证",
            "4. 收集反馈并优化",
            "",
            "---",
            "",
            "**Mining Agents 8 步流程已全部完成！** 🎉",
            "",
        ])
        
        return "\n".join(lines)
    
    def _count_components(self, config: Dict) -> int:
        """统计组件数量
        
        Args:
            config: 配置字典
            
        Returns:
            组件总数
        """
        count = 0
        count += len(config.get("journeys", []))
        count += len(config.get("guidelines", []))
        count += len(config.get("tools", []))
        count += len(config.get("glossary", []))
        count += sum(len(v) for v in config.get("rules", {}).values())
        return count
    
    def _sanitize_name(self, text: str) -> str:
        """清理名称中的特殊字符
        
        Args:
            text: 原始文本
            
        Returns:
            清理后的文本
        """
        import re
        sanitized = re.sub(r'[^\w\s\u4e00-\u9fff]', '', text)
        return sanitized.replace(' ', '_')
    
    async def close(self):
        """关闭资源"""
        self.logger.info("ConfigAssemblerAgent closing")
