#!/usr/bin/env python3
"""
日志模块（loguru）

实现目标：
- 统一日志入口，使用loguru
- 支持按 `system_config.yaml` 的 logging 配置设置 level / file / json
"""

from __future__ import annotations

from typing import Optional
from pathlib import Path
import sys

from loguru import logger




_CONFIGURED_SIGNATURE: Optional[str] = None


def _reconfigure_stdio_utf8() -> None:
    """在 Windows 等环境中统一 stdout/stderr 为 UTF-8，避免日志乱码。"""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                # 某些宿主流对象不支持重配，忽略并继续使用现有编码
                pass


def _coerce_level(level: str) -> str:
    if not level:
        return "INFO"
    return str(level).upper()


def configure_logging(
    *,
    level: str = "INFO",
    log_file: Optional[str] = None,
    json_format: bool = False,
):
    """配置全局 logger（幂等）。

    说明：loguru 的入口是 `logger.configure()`，可多次调用但同签名重复调用不重复配置。
    """
    global _CONFIGURED_SIGNATURE

    log_level = _coerce_level(level)

    signature = f"level={log_level}|log_file={log_file or ''}|json={int(bool(json_format))}"
    if _CONFIGURED_SIGNATURE == signature:
        return logger

    # 移除所有现有的 handler
    logger.remove()
    _reconfigure_stdio_utf8()

    # 添加控制台 handler
    log_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    logger.add(sys.stderr, format=log_format, level=log_level, colorize=True)

    # 添加文件 handler
    if log_file:
        Path(str(log_file)).parent.mkdir(parents=True, exist_ok=True)
        if json_format:
            logger.add(
                str(log_file),
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                level=log_level,
                serialize=True,
                encoding="utf-8",
            )
        else:
            logger.add(str(log_file), format=log_format, level=log_level, colorize=False, encoding="utf-8")

    _CONFIGURED_SIGNATURE = signature
    return logger


# 提供全局 logger（loguru 风格：logger.info/debug/warning/error/critical）
# 先移除默认 handler，等待 configure_logging 配置
logger.remove()


__all__ = ["logger", "configure_logging"]
