#!/usr/bin/env python3
"""DeepResearchAgent 提供器（按环境选择可用实现）

优先使用已安装的 agentscope DeepResearchAgent；
如果当前 agentscope 版本不包含，则从项目 src 内置实现中加载。

说明：
- 该模块是 DeepResearchTool 的"封装层"，避免在业务工具中散落
  sys.path 修改逻辑。
"""

from __future__ import annotations

from typing import Type


def get_deep_research_agent_class() -> Type:
    """获取可用的 DeepResearchAgent 类。

    Returns:
        DeepResearchAgent 的类对象
    """
    try:
        from agentscope.agent import DeepResearchAgent

        return DeepResearchAgent
    except ImportError:
        return _load_deep_research_agent_from_src()


def _load_deep_research_agent_from_src() -> Type:
    """从项目 src 目录加载 DeepResearchAgent 实现。"""
    from .deep_research_agent import DeepResearchAgent

    return DeepResearchAgent
