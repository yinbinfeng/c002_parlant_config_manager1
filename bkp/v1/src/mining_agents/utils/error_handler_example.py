#!/usr/bin/env python3
"""错误处理器使用示例"""

from .error_handler import AgentErrorHandler, FallbackStrategy


class ExampleAgent:
    """示例 Agent - 展示如何使用错误处理器"""
    
    def __init__(self):
        """初始化示例 Agent"""
        self.error_handler = AgentErrorHandler()
    
    async def example_with_retry(self):
        """示例：带重试的操作"""
        
        # 方式 1：使用 execute_with_retry 自动重试
        result = await self.error_handler.execute_with_retry(
            operation=self._risky_operation,
            operation_name="Risky operation",
            fallback_strategy=FallbackStrategy.DEFAULT,
            default_value={"status": "failed", "data": None},
            max_retries=3
        )
        return result
    
    async def _risky_operation(self):
        """模拟可能失败的操作"""
        # 这里放可能抛出异常的代码
        pass
    
    def example_manual_handling(self):
        """示例：手动处理异常"""
        try:
            # 可能失败的操作
            result = self._another_risky_operation()
            return result
        except Exception as e:
            # 使用错误处理器统一处理
            return self.error_handler.handle(
                error=e,
                fallback_strategy=FallbackStrategy.SILENT,
                operation_name="Another risky operation"
            )
    
    def _another_risky_operation(self):
        """另一个可能失败的操作"""
        pass
