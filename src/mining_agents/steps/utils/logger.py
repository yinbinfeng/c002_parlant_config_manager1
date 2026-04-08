#!/usr/bin/env python3
"""日志工具模块"""

from ...utils.logger import logger, configure_logging


def setup_logger(name, verbose=False):
    """设置日志记录器
    
    Args:
        name: 日志记录器名称
        verbose: 是否启用详细日志
    
    Returns:
        logger: 配置好的日志记录器
    """
    level = "DEBUG" if verbose else "INFO"
    configure_logging(level=level)
    return logger
