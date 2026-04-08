#!/usr/bin/env python3
"""Deep Research 工具池 - 支持多实例并发分发"""

import asyncio
from typing import Any, Dict, List

from ..utils.logger import logger
from .deep_research import DeepResearchTool


class DeepResearchToolPool:
    """DeepResearchTool 池化包装器。

    设计目标：
    - 对外保持与单工具一致接口（search/execute/get_tool_schema/close）
    - 内部维护多个独立实例，避免同实例并发导致状态冲突
    """

    def __init__(self, *, config: Dict[str, Any], mock_mode: bool, pool_size: int = 1):
        size = max(1, int(pool_size))
        self.logger = logger
        self.pool_size = size
        self._tools: List[DeepResearchTool] = [
            DeepResearchTool(config=config, mock_mode=mock_mode) for _ in range(size)
        ]
        self._rr_lock = asyncio.Lock()
        self._rr_index = 0
        self.logger.info(f"DeepResearchToolPool initialized with pool_size={self.pool_size}")

    async def _acquire_tool(self) -> DeepResearchTool:
        async with self._rr_lock:
            tool = self._tools[self._rr_index]
            self._rr_index = (self._rr_index + 1) % self.pool_size
            return tool

    def get_tool_schema(self) -> dict:
        return self._tools[0].get_tool_schema()

    async def search(self, query: str, **kwargs) -> str:
        tool = await self._acquire_tool()
        return await tool.search(query, **kwargs)

    async def execute(self, query: str, **kwargs) -> str:
        tool = await self._acquire_tool()
        return await tool.execute(query, **kwargs)

    async def close(self):
        for tool in self._tools:
            try:
                await tool.close()
            except Exception as e:
                self.logger.error(f"Error closing pooled deep_research tool: {e}")

