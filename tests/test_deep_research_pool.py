#!/usr/bin/env python3
"""DeepResearchToolPool 测试"""

import asyncio


def test_pool_round_robin_dispatch(monkeypatch):
    """应按轮询把请求分发到不同实例。"""
    from mining_agents.tools import deep_research_pool as pool_mod

    class _FakeTool:
        _counter = 0

        def __init__(self, config, mock_mode):
            self.config = config
            self.mock_mode = mock_mode
            self.idx = _FakeTool._counter
            _FakeTool._counter += 1

        def get_tool_schema(self):
            return {"type": "object"}

        async def search(self, query: str):
            return f"tool{self.idx}:{query}"

        async def execute(self, query: str, **kwargs):
            return f"exec{self.idx}:{query}:{kwargs.get('max_depth')}"

        async def close(self):
            return None

    monkeypatch.setattr(pool_mod, "DeepResearchTool", _FakeTool)
    pool = pool_mod.DeepResearchToolPool(config={}, mock_mode=True, pool_size=2)

    async def _run():
        r1 = await pool.search("q1")
        r2 = await pool.search("q2")
        r3 = await pool.execute("q3", max_depth=3)
        return r1, r2, r3

    r1, r2, r3 = asyncio.run(_run())
    assert r1.startswith("tool0:")
    assert r2.startswith("tool1:")
    assert r3.startswith("exec0:")


def test_pool_close_all_instances(monkeypatch):
    """关闭时应遍历关闭所有实例。"""
    from mining_agents.tools import deep_research_pool as pool_mod

    closed = []

    class _FakeTool:
        _counter = 0

        def __init__(self, config, mock_mode):
            self.idx = _FakeTool._counter
            _FakeTool._counter += 1

        def get_tool_schema(self):
            return {"type": "object"}

        async def search(self, query: str):
            return query

        async def execute(self, query: str, **kwargs):
            return query

        async def close(self):
            closed.append(self.idx)

    monkeypatch.setattr(pool_mod, "DeepResearchTool", _FakeTool)
    pool = pool_mod.DeepResearchToolPool(config={}, mock_mode=True, pool_size=3)
    asyncio.run(pool.close())
    assert sorted(closed) == [0, 1, 2]

