#!/usr/bin/env python3
"""Process Agent - 流程设计 Agent"""

from pathlib import Path
from json_repair import repair_json
from typing import Dict, Any, List
import re
from .base_agent import BaseAgent


class ProcessAgent(BaseAgent):
    """Process Agent - 负责设计具体业务流程、制定相关规约、选择适用工具、构建用户画像"""
    
    def __init__(self, name: str, orchestrator, **kwargs):
        super().__init__(name, orchestrator, **kwargs)
        self._init_react_agent()
        self.deep_research_tool = self.tools.get('deep_research')
        self.json_validator = self.tools.get('json_validator')

    async def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return await self.run(task, context)
    
    async def run(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        self.logger.info(f"Starting process design for task: {task}")
        
        business_desc = context.get("business_desc", "")
        step2_atomic_tasks = context.get("step2_atomic_tasks") or context.get("atomic_tasks") or []
        step1_structured_requirements = context.get("step1_structured_requirements") or context.get("structured_requirements") or {}
        output_dir = context.get("output_dir", "./output")
        mock_mode = context.get("mock_mode", True)
        
        self.logger.info(f"Business description: {business_desc[:50]}...")
        self.logger.info(f"Mock mode: {mock_mode}")
        self.logger.info(f"Atomic tasks count: {len(step2_atomic_tasks)}")
        
        if mock_mode:
            return self._mock_run(task, context)
        else:
            return await self._real_run(task, context)

    def _split_design_payload(self, design_result: Dict[str, Any]) -> Dict[str, Any]:
        journeys = design_result.get("journeys")
        guidelines = design_result.get("guidelines")
        tools = design_result.get("tools")
        profiles = design_result.get("profiles")

        if journeys is None and isinstance(design_result.get("journey"), (dict, list)):
            journeys = design_result.get("journey")
        if guidelines is None and isinstance(design_result.get("guideline"), (dict, list)):
            guidelines = design_result.get("guideline")
        if tools is None and isinstance(design_result.get("tool"), (dict, list)):
            tools = design_result.get("tool")
        if profiles is None and isinstance(design_result.get("profile"), (dict, list)):
            profiles = design_result.get("profile")

        return {
            "journeys": journeys if journeys is not None else [],
            "guidelines": guidelines if guidelines is not None else [],
            "tools": tools if tools is not None else [],
            "profiles": profiles if profiles is not None else [],
        }
    
    def _derive_journey_name_from_task(self, task_id: str, dimension: str, description: str, idx: int) -> str:
        if "MATRIX_" in task_id:
            parts = []
            if "用户人群" in description:
                m = re.search(r"用户人群\[([^\]]+)\]", description)
                if m:
                    parts.append(m.group(1)[:10])
            if "业务场景" in description:
                m = re.search(r"业务场景\[([^\]]+)\]", description)
                if m:
                    parts.append(m.group(1)[:10])
            if "边缘情况" in description:
                m = re.search(r"边缘情况\[([^\]]+)\]", description)
                if m:
                    parts.append(m.group(1)[:8])
            if parts:
                name = "_".join(parts)
                name = re.sub(r"[^a-zA-Z0-9_\u4e00-\u9fa5]", "_", name)
                return name[:30]
        
        if dimension and "component::" in dimension:
            comp_id = dimension.split("::")[1].split("::")[0]
            return f"comp_{comp_id}".lower()
        
        desc_clean = re.sub(r"[^a-zA-Z0-9_\u4e00-\u9fa5]", "_", description[:20])
        return f"journey_{idx}_{desc_clean}".lower()[:30]
    
    def _mock_run(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        self.logger.info("Generating MOCK process design...")
        
        output_dir = context.get("output_dir", "./output")
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

        atomic_tasks = context.get("atomic_tasks") or context.get("step2_atomic_tasks") or []
        business_desc = (context.get("business_desc") or "")[:500]
        
        journey_files = []
        guideline_files = []
        tool_files = []
        profile_files = []
        output_files = []
        
        journey_names_generated = set()
        
        if atomic_tasks:
            self.logger.info(f"Generating journeys for {len(atomic_tasks)} atomic tasks...")
            
            import json as _json
            
            for idx, atask in enumerate(atomic_tasks):
                task_id = atask.get("task_id", f"TASK_{idx}")
                dimension = atask.get("dimension", "")
                description = atask.get("description", "")
                priority = atask.get("priority", "medium")
                
                journey_name = self._derive_journey_name_from_task(task_id, dimension, description, idx)
                if journey_name in journey_names_generated:
                    journey_name = f"{journey_name}_{idx}"
                journey_names_generated.add(journey_name)
                
                journey_file = output_dir_path / f"step3_journeys_{journey_name}.json"
                guideline_file = output_dir_path / f"step3_guidelines_{journey_name}.json"
                tool_file = output_dir_path / f"step3_tools_{journey_name}.json"
                profile_file = output_dir_path / f"step3_profiles_{journey_name}.json"
                
                journey_payload = {
                    "mode": "mock",
                    "source_task_id": task_id,
                    "source_dimension": dimension,
                    "journeys": [
                        {
                            "sop_id": f"{journey_name}_sop_001",
                            "sop_title": f"{description[:50]}流程",
                            "sop_description": f"基于任务 {task_id} 生成的业务流程",
                            "trigger_conditions": [f"用户触发: {description[:30]}"],
                            "timeout": 1800,
                            "sop_states": [
                                {
                                    "state_id": "state_000",
                                    "state_name": "初始 - 需求确认",
                                    "state_type": "chat",
                                    "instruction": f"询问用户关于 {description[:30]} 的具体需求",
                                    "bind_guideline_ids": [f"{journey_name}_guide_001"],
                                    "transitions": [{"target_state_id": "state_001", "condition": "用户已明确需求"}]
                                },
                                {
                                    "state_id": "state_001",
                                    "state_name": "执行处理",
                                    "state_type": "chat",
                                    "instruction": f"处理用户的 {description[:30]} 请求",
                                    "transitions": [
                                        {"target_state_id": "state_002", "condition": "处理成功"},
                                        {"target_state_id": "state_003", "condition": "处理失败或异常"}
                                    ]
                                },
                                {
                                    "state_id": "state_002",
                                    "state_name": "完成",
                                    "state_type": "chat",
                                    "instruction": "告知用户处理结果",
                                    "is_end_state": True
                                },
                                {
                                    "state_id": "state_003",
                                    "state_name": "异常处理",
                                    "state_type": "chat",
                                    "instruction": "安抚用户并提供替代方案或转人工",
                                    "is_end_state": True
                                }
                            ]
                        }
                    ]
                }
                
                guideline_payload = {
                    "mode": "mock",
                    "source_task_id": task_id,
                    "guidelines": [
                        {
                            "guideline_id": f"{journey_name}_guide_001",
                            "scope": "journey",
                            "chat_state": f"{journey_name}.state_000",
                            "condition": "用户进入该流程",
                            "action": f"按照 {description[:30]} 的规范引导用户",
                            "priority": 5 if priority == "high" else 8,
                            "composition_mode": "FLUID"
                        }
                    ]
                }
                
                tool_payload = {
                    "mode": "mock",
                    "source_task_id": task_id,
                    "tools": [
                        {
                            "tool_id": f"{journey_name}_tool_001",
                            "tool_name": f"{journey_name}_helper",
                            "tool_description": f"辅助完成 {description[:30]} 的工具",
                            "timeout": 5,
                            "input_params": [{"param_name": "query", "param_type": "string", "required": True}],
                            "output_params": [{"field_name": "result", "field_type": "string"}]
                        }
                    ]
                }
                
                profile_payload = {
                    "mode": "mock",
                    "source_task_id": task_id,
                    "profiles": [
                        {
                            "segment_id": f"{journey_name}_segment_001",
                            "segment_name": f"{description[:20]}用户群",
                            "description": f"需要 {description[:30]} 服务的用户群体",
                            "behavior_patterns": ["主动咨询", "需要引导"],
                            "preferred_journeys": [f"{journey_name}_sop_001"]
                        }
                    ]
                }
                
                journey_file.write_text(_json.dumps(journey_payload, ensure_ascii=False, indent=2), encoding="utf-8")
                guideline_file.write_text(_json.dumps(guideline_payload, ensure_ascii=False, indent=2), encoding="utf-8")
                tool_file.write_text(_json.dumps(tool_payload, ensure_ascii=False, indent=2), encoding="utf-8")
                profile_file.write_text(_json.dumps(profile_payload, ensure_ascii=False, indent=2), encoding="utf-8")
                
                journey_files.append(str(journey_file))
                guideline_files.append(str(guideline_file))
                tool_files.append(str(tool_file))
                profile_files.append(str(profile_file))
                output_files.extend([str(journey_file), str(guideline_file), str(tool_file), str(profile_file)])
        else:
            journey_name = context.get("journey_name", "retention")
            files = [
                str(output_dir_path / f"step3_journeys_{journey_name}.json"),
                str(output_dir_path / f"step3_guidelines_{journey_name}.json"),
                str(output_dir_path / f"step3_tools_{journey_name}.json"),
                str(output_dir_path / f"step3_profiles_{journey_name}.json"),
            ]
            payload_base = {"mode": "mock", "task": task, "business_desc": business_desc}
            payload_map = {
                files[0]: {"journeys": [{"id": f"{journey_name}_journey", "name": f"{journey_name} journey", "description": "Mock journey", "trigger": "user_intent_detected", "states": []}], **payload_base},
                files[1]: {"guidelines": [{"id": f"{journey_name}_guideline_001", "chat_state": "global.default", "condition": "true", "specifications": ["Use concise style."]}], **payload_base},
                files[2]: {"tools": [{"id": f"{journey_name}_tool_001", "name": "mock_tool", "description": "Mock tool"}], **payload_base},
                files[3]: {"profiles": [{"id": f"{journey_name}_profile_001", "name": "default_profile"}], **payload_base},
            }
            import json as _json
            for fp in files:
                Path(fp).write_text(_json.dumps(payload_map[fp], ensure_ascii=False, indent=2), encoding="utf-8")
            journey_files = [files[0]]
            guideline_files = [files[1]]
            tool_files = [files[2]]
            profile_files = [files[3]]
            output_files = files
        
        result = {
            "journey_files": journey_files,
            "guideline_files": guideline_files,
            "tool_files": tool_files,
            "profile_files": profile_files,
            "output_files": output_files,
            "atomic_tasks_processed": len(atomic_tasks),
            "message": f"Process design completed successfully (MOCK mode), generated {len(journey_files)} journeys"
        }
        
        self.logger.info(f"Mock process design generated: {len(journey_files)} journeys from {len(atomic_tasks)} atomic tasks")
        return result
    
    async def _real_run(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        self.logger.info("Generating real process design with ReAct...")
        
        business_desc = context.get("business_desc", "")
        step2_atomic_tasks = context.get("step2_atomic_tasks") or context.get("atomic_tasks") or []
        step1_structured_requirements = context.get("step1_structured_requirements") or context.get("structured_requirements") or {}
        output_dir = context.get("output_dir", "./output")
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)
        
        core_goal = context.get("core_goal", business_desc[:200] if business_desc else "设计业务流程配置")
        industry = context.get("industry", "通用")
        
        agent_config = self.config or {}
        task_prompts = agent_config.get('task_prompts', {})
        react_prompt_template = task_prompts.get(
            'design_process',
            self._get_default_process_prompt(task, business_desc, step2_atomic_tasks, step1_structured_requirements)
        )

        class _SafeDict(dict):
            def __missing__(self, key):
                return ""

        fmt_vars = _SafeDict(
            task=task,
            business_desc=business_desc,
            step2_atomic_tasks=step2_atomic_tasks,
            step1_structured_requirements=step1_structured_requirements,
            journey_name=context.get("journey_name", "retention_flow"),
            core_goal=core_goal,
            industry=industry,
        )
        try:
            react_prompt = react_prompt_template.format_map(fmt_vars)
        except Exception:
            react_prompt = self._get_default_process_prompt(task, business_desc, step2_atomic_tasks, step1_structured_requirements)
        
        response = await self.call_react_agent(react_prompt, context)

        design_result = None
        try:
            design_result = repair_json(response.strip(), return_objects=True)
        except Exception:
            start = response.find("{")
            end = response.rfind("}")
            if start != -1 and end != -1 and end > start:
                candidate = response[start : end + 1]
                if self.json_validator:
                    ok, data, _ = self.json_validator.validate(candidate)
                    design_result = data if ok else repair_json(candidate, return_objects=True)
                else:
                    design_result = repair_json(candidate, return_objects=True)

        if isinstance(design_result, dict):
            self.logger.info("Successfully generated process design with ReAct")
            
            import json as _json
            design_file = output_dir_path / "step3_process_design.json"
            design_file.write_text(_json.dumps(design_result, ensure_ascii=False, indent=2), encoding="utf-8")

            journey_name = context.get("journey_name", "retention")
            journey_file = output_dir_path / f"step3_journeys_{journey_name}.json"
            guideline_file = output_dir_path / f"step3_guidelines_{journey_name}.json"
            tool_file = output_dir_path / f"step3_tools_{journey_name}.json"
            profile_file = output_dir_path / f"step3_profiles_{journey_name}.json"

            split_payload = self._split_design_payload(design_result)
            journey_file.write_text(_json.dumps({"journeys": split_payload["journeys"]}, ensure_ascii=False, indent=2), encoding="utf-8")
            guideline_file.write_text(_json.dumps({"guidelines": split_payload["guidelines"]}, ensure_ascii=False, indent=2), encoding="utf-8")
            tool_file.write_text(_json.dumps({"tools": split_payload["tools"]}, ensure_ascii=False, indent=2), encoding="utf-8")
            profile_file.write_text(_json.dumps({"profiles": split_payload["profiles"]}, ensure_ascii=False, indent=2), encoding="utf-8")

            journey_files = [str(journey_file)]
            guideline_files = [str(guideline_file)]
            tool_files = [str(tool_file)]
            profile_files = [str(profile_file)]
            
            result = {
                "journey_files": journey_files,
                "guideline_files": guideline_files,
                "tool_files": tool_files,
                "profile_files": profile_files,
                "output_files": journey_files + guideline_files + tool_files + profile_files,
                "design_result": design_result,
                "message": "Process design completed successfully with ReAct"
            }
            
            return result

        error_msg = "Failed to parse ReAct response as JSON object in REAL mode"
        self.logger.error(error_msg)
        raise RuntimeError(error_msg)

    def _get_default_process_prompt(self, task, business_desc, step2_atomic_tasks, step1_structured_requirements) -> str:
        prompt_template = self.task_prompts.get('design_process', '')
        if prompt_template:
            return prompt_template
        
        self.logger.warning("Design process prompt not found in config, using minimal fallback")
        return "请基于提供的业务信息，生成业务流程设计（Journey）、指导原则（Guideline）、工具定义（Tool）和用户画像（Profile）。"
