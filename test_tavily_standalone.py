# -*- coding: utf-8 -*-
"""
Tavily MCP 独立测试（与 Deep Research 解耦）。
文件格式: Python 源码

默认：每 20 秒一次 tavily_search（符合低于 100 RPM 的保守间隔）。
用法（在项目根目录 c002_parlant_config_manager1 下）:
  conda activate py311
  python test_tavily_standalone.py
  python test_tavily_standalone.py --interval 20 --rounds 3
"""
from __future__ import annotations

import argparse
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

from agentscope.mcp import StdIOStatefulClient

from src.mining_agents.utils.logger import configure_logging, logger
from src.mining_agents.utils.tavily_mcp_stdio import tavily_mcp_command_and_args


def _load_dotenv_files() -> list[str]:
    loaded: list[str] = []
    for p in (Path(r"E:\cursorworkspace\c002_parlant_config_manager1\.env"),):
        if p.is_file():
            load_dotenv(p, override=False)
            loaded.append(str(p))
    return loaded


def _resolve_tavily_key(cfg: dict) -> tuple[str, str]:
    tavily_cfg = (cfg.get("mcp_clients") or {}).get("tavily_search") or {}
    env_name = tavily_cfg.get("api_key_env") or "TAVILY_API_KEY"
    return env_name, os.getenv(env_name, "").strip()


def _log_tool_result(tag: str, result: object) -> None:
    """记录 MCP call_tool 的原始返回，便于排查 Tavily / MCP 层错误。"""
    logger.info("[Tavily MCP] {} result_type={}", tag, type(result).__name__)
    try:
        logger.info("[Tavily MCP] {} repr_preview={!r}", tag, repr(result)[:4000])
    except Exception as e:
        logger.warning("[Tavily MCP] {} repr 失败: {}", tag, e)
    for attr in ("content", "data", "text", "structuredContent"):
        if hasattr(result, attr):
            try:
                val = getattr(result, attr)
                logger.info("[Tavily MCP] {}.{}={!r}", tag, attr, repr(val)[:4000])
            except Exception as e:
                logger.warning("[Tavily MCP] {} 读取 {} 失败: {}", tag, attr, e)


async def _disconnect_client(client: StdIOStatefulClient) -> None:
    for meth in ("disconnect", "aclose", "close"):
        fn = getattr(client, meth, None)
        if callable(fn):
            try:
                out = fn()
                if asyncio.iscoroutine(out):
                    await out
                logger.info("Tavily MCP client {}() 已调用", meth)
                return
            except Exception as e:
                if "not connected" in str(e).lower():
                    logger.debug("Tavily MCP skip {}: {}", meth, e)
                    return
                logger.warning("Tavily MCP client {}() 失败: {}", meth, e)
    logger.warning("Tavily MCP client 未找到可用的 disconnect/aclose/close")


async def run_http_interval_test(*, interval_sec: float, rounds: int, api_key: str) -> bool:
    """使用 tavily-python 直连 REST API（不依赖 Node/npx/MCP）。"""
    from tavily import AsyncTavilyClient

    configure_logging(level="INFO")
    client = AsyncTavilyClient(api_key=api_key)
    queries = [
        "Japan insurance telemarketing compliance",
        "保険 電話 勧誘 規制",
        "tavily python sdk test",
    ]
    for i in range(rounds):
        q = queries[i % len(queries)]
        logger.info("HTTP 第 {}/{} 轮 tavily.search query={!r}", i + 1, rounds, q)
        try:
            resp = await client.search(q, max_results=3, search_depth="basic")
            logger.info("HTTP 响应 keys={} preview={!r}", list(resp.keys()) if isinstance(resp, dict) else type(resp), repr(resp)[:4000])
        except Exception:
            logger.error("tavily-python 调用失败:\n{}", traceback.format_exc())
            return False
        if i + 1 < rounds:
            logger.info("等待 {:.1f} 秒后进行下一轮...", interval_sec)
            await asyncio.sleep(interval_sec)
    logger.info("Tavily HTTP 直连测试全部轮次成功")
    return True


async def run_interval_test(*, interval_sec: float, rounds: int) -> bool:
    configure_logging(level="INFO")
    loaded = _load_dotenv_files()
    logger.info("已尝试加载 .env: {}", loaded or "（未找到 E:\\cursorworkspace\\c002_parlant_config_manager1\\.env）")

    with open(CONFIG_PATH, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    env_name, api_key = _resolve_tavily_key(cfg)
    if not api_key:
        logger.error("未找到 Tavily Key：请设置环境变量 {}", env_name)
        return False

    logger.info("使用环境变量 {} ，Key 前缀: {}...", env_name, api_key[:6])

    t_cmd, t_args = tavily_mcp_command_and_args()
    client = StdIOStatefulClient(
        name="tavily_mcp",
        command=t_cmd,
        args=t_args,
        env={"TAVILY_API_KEY": api_key},
    )
    try:
        logger.info("正在连接 Tavily MCP (npx tavily-mcp@latest)...")
        await client.connect()
        logger.info("Tavily MCP 连接成功")

        tools = client.list_tools()
        logger.info("MCP list_tools 数量={} 名称={}", len(tools), [getattr(t, "name", str(t)) for t in tools])

        queries = [
            "Japan insurance telemarketing compliance",
            "保険 電話 勧誘 規制",
            "tavily mcp test query round",
        ]

        for i in range(rounds):
            q = queries[i % len(queries)]
            logger.info("第 {}/{} 轮 tavily_search，query={!r}", i + 1, rounds, q)
            try:
                result = await client.call_tool(
                    "tavily_search",
                    {
                        "query": q,
                        "max_results": 3,
                        "search_depth": "basic",
                    },
                )
                _log_tool_result(f"round_{i + 1}", result)
            except Exception:
                logger.error("tavily_search 调用异常:\n{}", traceback.format_exc())
                return False

            if i + 1 < rounds:
                logger.info("等待 {:.1f} 秒后进行下一轮（RPM 保守间隔）...", interval_sec)
                await asyncio.sleep(interval_sec)

        logger.info("Tavily 独立测试全部轮次成功")
        return True
    except Exception:
        logger.error("Tavily 独立测试失败:\n{}", traceback.format_exc())
        return False
    finally:
        await _disconnect_client(client)


def main() -> None:
    parser = argparse.ArgumentParser(description="Tavily 独立测试")
    parser.add_argument(
        "--backend",
        choices=("mcp", "http"),
        default="http",
        help="http=tavily-python 直连（当前默认）；mcp=stdio+npx（兼容模式）",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=20.0,
        help="每两轮搜索之间的间隔秒数（默认 20，低于 100 RPM 的保守值）",
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=3,
        help="搜索轮数（默认 3）",
    )
    args = parser.parse_args()
    if args.backend == "http":
        _load_dotenv_files()
        with open(CONFIG_PATH, encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        _, api_key = _resolve_tavily_key(cfg)
        if not api_key:
            logger.error("未配置 TAVILY_API_KEY")
            sys.exit(1)
        configure_logging(level="INFO")
        ok = asyncio.run(
            run_http_interval_test(
                interval_sec=args.interval,
                rounds=args.rounds,
                api_key=api_key,
            ),
        )
    else:
        ok = asyncio.run(run_interval_test(interval_sec=args.interval, rounds=args.rounds))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
