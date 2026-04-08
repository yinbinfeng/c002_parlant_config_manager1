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
import json
import shutil

from .utils.logger import logger, configure_logging
from .managers.step_manager import StepManager
from .managers.agent_orchestrator import AgentOrchestrator
from .tools.deep_research import DeepResearchTool
from .tools.deep_research_pool import DeepResearchToolPool
from .tools.json_validator import JsonValidator

from .steps.requirement_clarification import requirement_clarification_handler
from .steps.step3_global_guidelines import step3_global_guidelines_handler
from .steps.step4_user_profiles import step4_user_profiles_handler
from .steps.step5_branch_sop_parallel import step5_branch_sop_parallel_handler
from .steps.step6_edge_cases import step6_edge_cases_handler
from .steps.step_extract_canned_obs import step_extract_canned_obs_handler
from .steps.step7_config_assembly import step7_config_assembly_handler
from .steps.step8_validation import step8_validation_handler
from .steps.step2_objective_alignment_main_sop import step2_objective_alignment_main_sop_handler


def _snapshot_yaml_configs(config_path: Path, output_dir: Path) -> None:
    """将本次运行使用的 YAML 配置快照到输出目录，便于问题追踪与参数回溯。"""
    try:
        config_root = config_path.parent
        snapshot_dir = output_dir / "run_config_snapshot"
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        yaml_files = list(config_root.rglob("*.yaml")) + list(config_root.rglob("*.yml"))
        manifest = {
            "source_config_root": str(config_root.resolve()),
            "snapshot_dir": str(snapshot_dir.resolve()),
            "total_yaml_files": 0,
            "files": [],
        }

        for src in yaml_files:
            if not src.is_file():
                continue
            rel = src.relative_to(config_root)
            dst = snapshot_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            manifest["files"].append(str(rel).replace("\\", "/"))

        manifest["files"] = sorted(set(manifest["files"]))
        manifest["total_yaml_files"] = len(manifest["files"])
        (snapshot_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info(f"Config snapshot saved: {snapshot_dir} ({manifest['total_yaml_files']} yaml files)")
    except Exception as e:
        logger.warning(f"Failed to snapshot yaml configs: {e}")


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

    # 初始化日志（loguru 风格）：先用默认，再根据 system_config 二次配置（幂等）
    configure_logging(level="INFO")

    config_path_p = Path(config_path)
    output_dir_p = Path(output_dir)
    output_dir_p.mkdir(parents=True, exist_ok=True)
    _snapshot_yaml_configs(config_path=config_path_p, output_dir=output_dir_p)
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
        if not str(tavily_api_key or "").strip():
            raise RuntimeError(
                f"真实模式必须配置 Tavily API Key（环境变量 {tavily_api_key_env} 非空），"
                "禁止使用 Mock 检索结果。请设置密钥或使用 `--mode mock`。"
            )
        if not openai_api_key:
            logger.warning(
                f"真实模式下未检测到 OpenAI Key（环境变量 {openai_api_key_env} 为空），LLM 调用可能失败"
            )
        if bool(deep_research_cfg.get("allow_fallback_on_failure", True)):
            logger.warning("真实模式启用 Deep Research fallback：超过失败阈值后改为使用模型自身知识。")

    deep_research_tool_config = {
        "openai_api_key": openai_api_key,
        "openai_base_url": openai_base_url,
        "tavily_api_key": tavily_api_key,
        "model_name": deep_research_cfg.get("model_name", "Qwen/Qwen3.5-27B"),
        "max_depth": deep_research_cfg.get("max_depth", 3),
        "max_iters": deep_research_cfg.get("max_iters", 2),
        "timeout_sec": deep_research_cfg.get("timeout_sec", 120),
        "client_timeout_sec": deep_research_cfg.get(
            "client_timeout_sec",
            deep_research_cfg.get("timeout_sec", 120),
        ),
        "timeout_retry_count": deep_research_cfg.get("timeout_retry_count", 1),
        "enable_thinking": deep_research_cfg.get("enable_thinking", False),
        "temperature": deep_research_cfg.get("temperature", 0.7),
        # 降级机制配置
        "max_failures_before_fallback": deep_research_cfg.get("max_failures_before_fallback", 3),
        "allow_fallback_on_failure": deep_research_cfg.get("allow_fallback_on_failure", True),
    }
    _dr_extra_keys = (
        "tavily_retry_on_rate_limit",
        "tavily_retry_delay_sec",
        "tavily_max_retries",
        "tavily_retry_backoff_multiplier",
        "progress_log_interval_sec",
        "max_report_chars",
    )
    for _k in _dr_extra_keys:
        if _k in deep_research_cfg:
            deep_research_tool_config[_k] = deep_research_cfg[_k]
    deep_research_effective_mock = bool(mock_mode)

    deep_research_pool_size = int(deep_research_cfg.get("pool_size", 1))
    if deep_research_pool_size > 1:
        deep_research_tool = DeepResearchToolPool(
            config=deep_research_tool_config,
            mock_mode=deep_research_effective_mock,
            pool_size=deep_research_pool_size,
        )
    else:
        deep_research_tool = DeepResearchTool(
            config=deep_research_tool_config,
            mock_mode=deep_research_effective_mock,
        )
    json_validator = JsonValidator()
    orchestrator.register_tool("deep_research", deep_research_tool)
    orchestrator.register_tool("json_validator", json_validator)

    # 注册 Step handlers
    async def wrapped_requirement_clarification_handler(context):
        return await requirement_clarification_handler(context, orchestrator)

    async def wrapped_step2_objective_alignment_handler(context):
        return await step2_objective_alignment_main_sop_handler(context, orchestrator)

    async def wrapped_step3_global_guidelines_handler(context):
        return await step3_global_guidelines_handler(context, orchestrator)

    async def wrapped_step4_user_profiles_handler(context):
        return await step4_user_profiles_handler(context, orchestrator)

    async def wrapped_step5_branch_sop_parallel_handler(context):
        return await step5_branch_sop_parallel_handler(context, orchestrator)

    async def wrapped_step6_edge_cases_handler(context):
        return await step6_edge_cases_handler(context, orchestrator)

    async def wrapped_step_extract_canned_obs_handler(context):
        return await step_extract_canned_obs_handler(context, orchestrator)

    async def wrapped_step7_config_assembly_handler(context):
        return await step7_config_assembly_handler(context, orchestrator)

    async def wrapped_step8_validation_handler(context):
        return await step8_validation_handler(context, orchestrator)

    step_manager.register_step_handler(1, wrapped_requirement_clarification_handler)
    # v2（8 步法）迁移期映射：
    # - 2-5 暂时复用既有 5 步实现，先保证链路可跑通
    # - 6-8 先用 stub 占位，后续逐步替换为真实实现
    step_manager.register_step_handler(2, wrapped_step2_objective_alignment_handler)
    step_manager.register_step_handler(3, wrapped_step3_global_guidelines_handler)
    step_manager.register_step_handler(4, wrapped_step4_user_profiles_handler)
    step_manager.register_step_handler(5, wrapped_step5_branch_sop_parallel_handler)
    step_manager.register_step_handler(6, wrapped_step6_edge_cases_handler)
    # Step 7: 提取 canned responses 和 observations（新增步骤）
    step_manager.register_step_handler(7, wrapped_step_extract_canned_obs_handler)
    # Step 8-9: 原 Step 7-8 后移
    step_manager.register_step_handler(8, wrapped_step7_config_assembly_handler)
    step_manager.register_step_handler(9, wrapped_step8_validation_handler)

    return step_manager, orchestrator

