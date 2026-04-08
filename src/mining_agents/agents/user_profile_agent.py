#!/usr/bin/env python3
"""
user_profile_agent.py
文件格式: Python 源码

UserProfileAgent:
- 基于 Step2 的宏观目标（global_objective / core_goal）与业务描述生成用户分群与典型画像
- 强制使用 Deep Research（由提示词约束 + 工具可用性）
- 输出工程化的 `agent_user_profiles.json` 结构（用于后续组装为 Parlant 配置包）
"""

from __future__ import annotations

from typing import Any, Dict
from json_repair import repair_json

from .base_agent import BaseAgent


class UserProfileAgent(BaseAgent):
    _INVALID_REACT_SNIPPETS = (
        "interrupted me",
        "what can i do for you",
        "i noticed that you",
    )

    def __init__(self, name: str, orchestrator, **kwargs):
        super().__init__(name, orchestrator, **kwargs)
        use_react = bool((self.model_config or {}).get("use_react", True))
        if use_react:
            self._init_react_agent()
        else:
            self.logger.info("UserProfile ReAct disabled by config (use_react=false)")
        self.json_validator = self.tools.get("json_validator")

    def _build_deep_research_brief(self, task: str, context: Dict[str, Any]) -> str:
        task_prompts = self.task_prompts or {}
        template = task_prompts.get("deep_research_brief_template", "")
        business_desc = context.get("business_desc", "")
        core_goal = context.get("core_goal", business_desc[:200] if business_desc else "")
        industry = context.get("industry", "通用")
        global_objective = context.get("global_objective", "")
        if template:
            return (
                template.replace("{task}", str(task))
                .replace("{business_desc}", str(business_desc))
                .replace("{core_goal}", str(core_goal))
                .replace("{industry}", str(industry))
                .replace("{global_objective}", str(global_objective))
            )
        return (
            "请围绕该业务场景输出用户画像研究报告，覆盖：用户分群维度、行为信号、"
            "可判定标签、异议/痛点模式、合规注意事项。"
            f" 业务描述={business_desc}；核心目标={core_goal}；行业={industry}"
        )

    async def _fallback_template_fill(self, task: str, context: Dict[str, Any]) -> Dict[str, Any] | None:
        business_desc = context.get("business_desc", "")
        core_goal = context.get("core_goal", business_desc[:200] if business_desc else "")
        prompt = (
            "你需要按固定JSON模板填充字段并决定数组数量。\n"
            "要求：user_segments 3-6 个，personas 2-4 个；内容必须贴合业务，不得引入无关行业。\n"
            "仅输出 JSON，不要解释。\n\n"
            f"任务: {task}\n业务描述: {business_desc}\n核心目标: {core_goal}\n\n"
            "JSON模板:\n"
            "{\n"
            '  "agent_id": "xxx_agent_001",\n'
            '  "remark": "xxx",\n'
            '  "fallback_source": "template_fill_mode",\n'
            '  "user_segments": [],\n'
            '  "personas": []\n'
            "}\n"
        )
        response = await self.call_llm(prompt, context)
        parsed = None
        for candidate in self._extract_json_text_candidates(str(response or "")):
            try:
                parsed = repair_json(candidate, return_objects=True)
            except Exception:
                parsed = None
            if isinstance(parsed, dict):
                break
        if not isinstance(parsed, dict):
            try:
                fixed = await self._llm_fix_json_once(response, context, schema_hint="JSON object")
                parsed = repair_json(fixed, return_objects=True)
            except Exception:
                parsed = None
        if isinstance(parsed, dict):
            parsed.setdefault("fallback_source", "template_fill_mode")
            return parsed
        return None

    async def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        self.logger.info(f"Executing UserProfileAgent task: {task}")

        self.logger.info(f"UserProfileAgent self.task_prompts type: {type(self.task_prompts)}")
        self.logger.info(f"UserProfileAgent self.task_prompts: {self.task_prompts}")
        task_prompts = self.task_prompts or {}
        self.logger.info(f"UserProfileAgent task_prompts keys: {list(task_prompts.keys()) if task_prompts else 'None'}")
        react_prompt_template = task_prompts.get("generate_user_profiles", "")
        self.logger.info(f"UserProfileAgent react_prompt_template len: {len(react_prompt_template) if react_prompt_template else 0}")

        business_desc = context.get("business_desc", "")
        core_goal = context.get("core_goal", business_desc[:200] if business_desc else "")
        industry = context.get("industry", "通用")
        global_objective = context.get("global_objective", "")

        class _SafeDict(dict):
            def __missing__(self, key):
                return ""

        fmt_vars = _SafeDict(
            task=task,
            business_desc=business_desc,
            core_goal=core_goal,
            industry=industry,
            global_objective=global_objective,
        )

        if react_prompt_template:
            try:
                react_prompt = react_prompt_template.format_map(fmt_vars)
            except Exception as e:
                self.logger.error(f"UserProfileAgent format_map failed: {e}")
                react_prompt = ""
        else:
            react_prompt = ""

        if not react_prompt:
            self.logger.warning("UserProfileAgent prompt not found in config, using minimal fallback")
            react_prompt = (
                "请基于业务描述与全局目标，生成用户分群与典型画像，输出 JSON。"
            )

        dr_brief = self._build_deep_research_brief(task, context)
        react_guard = (
            "\n\n【执行流程约束（必须遵守）】\n"
            f"1) 先调用 deep_research，query 必须使用以下完整调研任务说明：\n{dr_brief}\n"
            "2) deep_research 返回的是研究文本证据，不要把它当 JSON 解析；\n"
            "3) 基于研究证据输出最终 parlant JSON；\n"
            "4) 最终输出前可调用 json_validator 自检；\n"
            "5) 最终回答只允许 JSON 本体，不要解释文本/代码块。\n"
        )
        response = await self.call_react_agent(react_prompt + react_guard, context)

        result: Any = None
        
        if any(s in (response or "").lower() for s in self._INVALID_REACT_SNIPPETS) or len((response or "").strip()) < 100:
            self.logger.warning(f"UserProfileAgent received interrupted/short response, trying direct LLM call")
            try:
                response = await self.call_llm(react_prompt + react_guard, context)
            except Exception as e:
                self.logger.error(f"UserProfileAgent direct LLM call also failed: {e}")

        for candidate in self._extract_json_text_candidates(str(response or "")):
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
                break

        if isinstance(result, dict):
            self.logger.info("Successfully generated user profiles with ReAct")
            return {
                "user_profiles": result,
                "message": "User profiles generated successfully",
            }

        fb = await self._fallback_template_fill(task, context)
        if isinstance(fb, dict):
            self.logger.warning("UserProfileAgent fallback template-fill activated")
            return {
                "user_profiles": fb,
                "message": "User profiles generated with template-fill fallback",
            }
        raise ValueError("UserProfileAgent failed to parse model output as JSON object")

