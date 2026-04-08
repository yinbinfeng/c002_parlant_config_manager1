# -*- coding: utf-8 -*-
"""
Deep Research 独立测试（max_depth=1, max_iters=1，两轮 search 间隔 30s）。
文件格式: Python 源码

用法（在项目根目录 c002_parlant_config_manager1 下）:
  conda activate py311
  python test_deep_research_standalone.py
"""
from __future__ import annotations

import asyncio
import os
import sys
import traceback
from pathlib import Path

import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = PROJECT_ROOT / "egs" / "v0.1.0_minging_agents" / "config" / "system_config.yaml"

sys.path.insert(0, str(PROJECT_ROOT))

from src.mining_agents.tools.deep_research import DeepResearchTool
from src.mining_agents.utils.logger import configure_logging, logger


def _load_dotenv_files() -> list[str]:
    loaded: list[str] = []
    for p in (Path(r"E:\cursorworkspace\c002_parlant_config_manager1\.env"),):
        if p.is_file():
            load_dotenv(p, override=False)
            loaded.append(str(p))
    return loaded


def _build_deep_research_config(cfg: dict) -> dict:
    openai_cfg = cfg.get("openai") or {}
    tavily_cfg = (cfg.get("mcp_clients") or {}).get("tavily_search") or {}
    dr = cfg.get("deep_research") or {}

    openai_key_env = openai_cfg.get("api_key_env") or "OPENAI_API_KEY"
    base_url_env = openai_cfg.get("base_url_env") or "OPENAI_BASE_URL"
    tavily_key_env = tavily_cfg.get("api_key_env") or "TAVILY_API_KEY"

    tool_cfg: dict = {
        "openai_api_key": os.getenv(str(openai_key_env), ""),
        "openai_base_url": os.getenv(str(base_url_env), "") or openai_cfg.get("base_url"),
        "tavily_api_key": os.getenv(str(tavily_key_env), ""),
        "model_name": dr.get("model_name", "Qwen/Qwen3.5-27B"),
        "max_depth": 1,
        "max_iters": 1,
        "timeout_sec": int(dr.get("timeout_sec", 120)),
        "client_timeout_sec": int(dr.get("client_timeout_sec", dr.get("timeout_sec", 120))),
        "timeout_retry_count": int(dr.get("timeout_retry_count", 2)),
        "enable_thinking": dr.get("enable_thinking", False),
        "temperature": float(dr.get("temperature", 0.7)),
        "max_failures_before_fallback": int(dr.get("max_failures_before_fallback", 3)),
        "allow_fallback_on_failure": bool(dr.get("allow_fallback_on_failure", True)),
    }
    for k in (
        "tavily_retry_on_rate_limit",
        "tavily_retry_delay_sec",
        "tavily_max_retries",
        "tavily_retry_backoff_multiplier",
        "progress_log_interval_sec",
        "max_report_chars",
    ):
        if k in dr:
            tool_cfg[k] = dr[k]
    return tool_cfg


async def run() -> bool:
    configure_logging(level="INFO")
    loaded = _load_dotenv_files()
    logger.info("已尝试加载 .env: {}", loaded or "（未找到 E:\\cursorworkspace\\c002_parlant_config_manager1\\.env）")

    with open(CONFIG_PATH, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    tool_cfg = _build_deep_research_config(cfg)
    if not tool_cfg["tavily_api_key"]:
        logger.error("TAVILY_API_KEY 为空，无法测试 Deep Research 真实模式")
        return False
    tool = DeepResearchTool(config=tool_cfg, mock_mode=False)
    queries = [
        "日本 保険 電話 勧誘 コンプライアンス 要点",
        "customer service agent task decomposition best practices",
    ]
    try:
        for i, q in enumerate(queries):
            logger.info("Deep Research 独立测试 第 {}/{} 轮，query={!r}", i + 1, len(queries), q)
            try:
                text = await tool.search(q)
                logger.info("Deep Research 返回长度={} 预览={!r}", len(text), text[:800])
            except Exception:
                logger.error("Deep Research 调用失败:\n{}", traceback.format_exc())
                return False
            if i + 1 < len(queries):
                logger.info("等待 30 秒后进行下一轮（与 Tavily RPM 保守间隔对齐）...")
                await asyncio.sleep(30.0)
        logger.info("Deep Research 独立测试完成")
        return True
    finally:
        await tool.close()


def main() -> None:
    ok = asyncio.run(run())
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
