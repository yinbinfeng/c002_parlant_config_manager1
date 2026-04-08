#!/usr/bin/env python3
"""
日志模块（Loguru 风格）

实现目标：
- 统一日志入口，使用 loguru 作为日志库
- 支持按 `system_config.yaml` 的 logging 配置设置 level / file
"""

from __future__ import annotations

import sys
from typing import Optional

from loguru import logger


_CONFIGURED = False


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
    """配置全局 logger（幂等）。"""
    global _CONFIGURED
    if _CONFIGURED:
        return logger

    logger.remove()

    log_level = _coerce_level(level)

    log_format = (
        "{{\"time\": \"{{time:YYYY-MM-DDTHH:mm:ssZ}}\", \"name\": \"{{name}}\", "
        "\"level\": \"{{level}}\", \"message\": \"{{message}}\"}}"
        if json_format
        else "<green>{time:YYYY-MM-DD HH:mm:ss}</green> - <cyan>{name}</cyan> - <level>{level}</level> - {message}"
    )

    logger.add(
        sys.stdout,
        level=log_level,
        format=log_format,
        colorize=not json_format,
    )

    if log_file:
        logger.add(
            log_file,
            level=log_level,
            format=log_format,
            encoding="utf-8",
        )

    _CONFIGURED = True
    return logger


__all__ = ["logger", "configure_logging"]
