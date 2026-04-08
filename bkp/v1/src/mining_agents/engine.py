#!/usr/bin/env python3
"""
engine.py
文件格式: Python 源码

统一构建 Mining Agents CoreEngine（StepManager + AgentOrchestrator）。
用于 CLI/UI 共享同一套核心逻辑，避免两套实现漂移。
"""

from __future__ import annotations

from pathlib import Path
import os

from .utils.logger import logger, configure_logging
from .managers.step_manager import StepManager
from .managers.agent_orchestrator import AgentOrchestrator
from .tools.deep_research import DeepResearchTool
from .tools.json_validator import JsonValidator

from .steps.requirement_clarification import requirement_clarification_handler
from .steps.dimension_analysis import dimension_analysis_handler
from .steps.workflow_development import workflow_development_handler
from .steps.global_rules_check import global_rules_check_handler
from .steps.config_assembly import config_assembly_handler


def build_core_engine(
    *,
    config_path: str,
    output_dir: str,
    mode: str = "real",
    max_parallel: int = 1,
    debug_mode: bool = False,
) -> tuple[StepManager, AgentOrchestrator]:
    """
    构建核心引擎对象，并注册工具与 Step handlers。

    约束：
    - Key 仅从环境变量读取（配置文件仅写 env 名）
    - 并发仅在需要的地方使用异步（Step handlers 本身是 async）
    """

    # 初始化日志（logrus 风格）：先用默认，再根据 system_config 二次配置（幂等）
    configure_logging(level="INFO")

    config_path_p = Path(config_path)
    step_manager = StepManager(str(config_path_p), str(output_dir))

    logging_cfg = step_manager.config.get("logging", {}) or {}
    configure_logging(
        level=str(logging_cfg.get("level", "INFO")),
        log_file=logging_cfg.get("file"),
        json_format=bool(logging_cfg.get("json", False)),
    )

    mock_mode = mode == "mock"
    orchestrator_config = {
        "mock_mode": mock_mode,
        "max_parallel_agents": max_parallel,
        "system_config": step_manager.config,
    }
    if debug_mode:
        orchestrator_config.update(
            {
                "debug": True,
                "log_level": "DEBUG",
                "timeout": 30,
                "retry_attempts": 2,
            }
        )

    orchestrator = AgentOrchestrator(config=orchestrator_config)

    # 注册工具（DeepResearch 需要 openai/base_url/tavily）
    openai_cfg = step_manager.config.get("openai", {}) or {}
    tavily_cfg = ((step_manager.config.get("mcp_clients", {}) or {}).get("tavily_search", {}) or {})

    tavily_api_key_env = tavily_cfg.get("api_key_env") or "TAVILY_API_KEY"
    tavily_api_key = os.getenv(str(tavily_api_key_env), "")

    deep_research_cfg = step_manager.config.get("deep_research", {}) or {}

    openai_api_key_env = openai_cfg.get("api_key_env") or "OPENAI_API_KEY"
    openai_base_url_env = openai_cfg.get("base_url_env") or "OPENAI_BASE_URL"
    openai_api_key = os.getenv(str(openai_api_key_env), "")
    openai_base_url = os.getenv(str(openai_base_url_env), "") or openai_cfg.get("base_url") or None

    if mode == "real":
        if not tavily_api_key:
            logger.warning(
                f"真实模式下未检测到 Tavily Key（环境变量 {tavily_api_key_env} 为空），Deep Research 可能不可用"
            )
        if not openai_api_key:
            logger.warning(
                f"真实模式下未检测到 OpenAI Key（环境变量 {openai_api_key_env} 为空），LLM 调用可能失败"
            )

    deep_research_tool = DeepResearchTool(
        config={
            "openai_api_key": openai_api_key,
            "openai_base_url": openai_base_url,
            "tavily_api_key": tavily_api_key,
            "model_name": deep_research_cfg.get("model_name", "Qwen/Qwen3.5-27B"),
            "max_depth": deep_research_cfg.get("max_depth", 3),
            "max_iters": deep_research_cfg.get("max_iters", 2),
            "temperature": deep_research_cfg.get("temperature", 0.7),
        },
        mock_mode=mock_mode,
    )
    json_validator = JsonValidator()
    orchestrator.register_tool("deep_research", deep_research_tool)
    orchestrator.register_tool("json_validator", json_validator)

    # 注册 Step handlers
    async def wrapped_requirement_clarification_handler(context):
        return await requirement_clarification_handler(context, orchestrator)

    async def wrapped_dimension_analysis_handler(context):
        return await dimension_analysis_handler(context, orchestrator)

    async def wrapped_workflow_development_handler(context):
        return await workflow_development_handler(context, orchestrator)

    async def wrapped_global_rules_check_handler(context):
        return await global_rules_check_handler(context, orchestrator)

    async def wrapped_config_assembly_handler(context):
        return await config_assembly_handler(context, orchestrator)

    step_manager.register_step_handler(1, wrapped_requirement_clarification_handler)
    step_manager.register_step_handler(2, wrapped_dimension_analysis_handler)
    step_manager.register_step_handler(3, wrapped_workflow_development_handler)
    step_manager.register_step_handler(4, wrapped_global_rules_check_handler)
    step_manager.register_step_handler(5, wrapped_config_assembly_handler)

    return step_manager, orchestrator

