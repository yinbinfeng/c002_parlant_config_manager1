#!/usr/bin/env python3
"""错误处理器 - 统一的错误处理策略"""

from typing import Any, Optional, Callable
from enum import Enum
from .logger import logger


class FallbackStrategy(Enum):
    """降级策略枚举"""
    SILENT = "silent"  # 静默失败，返回 None
    DEFAULT = "default"  # 使用默认值
    RAISE = "raise"  # 抛出异常
    RETRY = "retry"  # 重试（需配合重试次数）


class AgentErrorHandler:
    """Agent 错误处理器"""
    
    def __init__(self, logger=None, default_retries: int = 3):
        """初始化错误处理器
        
        Args:
            logger: 日志记录器
            default_retries: 默认重试次数
        """
        self.logger = logger or logger
        self.default_retries = default_retries
    
    def handle(
        self,
        error: Exception,
        fallback_strategy: FallbackStrategy = FallbackStrategy.DEFAULT,
        default_value: Any = None,
        operation_name: str = "",
        retries: int = 0
    ) -> Any:
        """处理异常
        
        Args:
            error: 捕获的异常
            fallback_strategy: 降级策略
            default_value: 默认值（当策略为 DEFAULT 时使用）
            operation_name: 操作名称（用于日志）
            retries: 剩余重试次数
            
        Returns:
            降级后的返回值
            
        Raises:
            Exception: 当策略为 RAISE 时重新抛出异常
        """
        if retries > 0:
            self.logger.warning(f"{operation_name} failed, retrying... ({retries} attempts left): {error}")
            return None  # 返回 None 表示需要调用方重试
        
        if fallback_strategy == FallbackStrategy.SILENT:
            self.logger.warning(f"{operation_name} failed (silent mode): {error}")
            return None
        
        elif fallback_strategy == FallbackStrategy.DEFAULT:
            self.logger.error(f"{operation_name} failed, using default value: {error}")
            return default_value
        
        elif fallback_strategy == FallbackStrategy.RAISE:
            self.logger.error(f"{operation_name} failed, raising exception: {error}")
            raise error
        
        elif fallback_strategy == FallbackStrategy.RETRY:
            self.logger.error(f"{operation_name} failed after {self.default_retries} retries: {error}")
            return default_value
        
        else:
            self.logger.error(f"{operation_name} failed with unknown strategy: {error}")
            return default_value
    
    async def execute_with_retry(
        self,
        operation: Callable,
        operation_name: str,
        fallback_strategy: FallbackStrategy = FallbackStrategy.DEFAULT,
        default_value: Any = None,
        max_retries: int = None
    ) -> Any:
        """执行操作并自动重试
        
        Args:
            operation: 要执行的操作（异步函数）
            operation_name: 操作名称
            fallback_strategy: 降级策略
            default_value: 默认值
            max_retries: 最大重试次数
            
        Returns:
            操作结果或降级值
        """
        retries = max_retries if max_retries is not None else self.default_retries
        
        while retries >= 0:
            try:
                result = await operation()
                return result
            except Exception as e:
                if retries > 0:
                    self.logger.warning(f"{operation_name} failed, retrying... ({retries} attempts left): {e}")
                    retries -= 1
                    continue
                else:
                    return self.handle(
                        error=e,
                        fallback_strategy=fallback_strategy,
                        default_value=default_value,
                        operation_name=operation_name,
                        retries=0
                    )
        
        return default_value  # 理论上不会到这里
