#!/usr/bin/env python3
"""Deep Research 工具封装 - 基于 AgentScope 的 DeepResearchAgent"""

import asyncio
from typing import Optional
import json
import time
from pathlib import Path
from ..utils.logger import logger
from .deep_research_agent_provider import get_deep_research_agent_class


class DeepResearchTool:
    """Deep Research 工具封装
    
    基于 AgentScope 的 DeepResearchAgent，提供深度搜索能力。
    支持 Mock 模式（测试用）和真实模式（生产用）。
    """
    
    def __init__(self, config: dict, mock_mode: bool = True):
        """初始化工具
        
        Args:
            config: 配置字典，包含：
                - openai_api_key: OpenAI API Key
                - openai_base_url: OpenAI API Base URL
                - tavily_api_key: Tavily API Key
                - embedding_model: Embedding 模型名称（默认 text-embedding-v3）
                - max_depth: 最大搜索深度（默认 3）
                - max_iters: 最大迭代次数（默认 30）
            mock_mode: 是否使用 Mock 模式（默认 True，用于测试）
        """
        self.config = config
        self.mock_mode = mock_mode
        self.logger = logger
        self._debug_log(
            run_id="pre-fix-deep-research",
            hypothesis_id="DR-H2",
            location="deep_research.py:38",
            message="DeepResearchTool init params",
            data={
                "mock_mode": mock_mode,
                "config_keys": list((config or {}).keys()),
                "has_openai_api_key": bool((config or {}).get("openai_api_key")),
                "has_tavily_api_key": bool((config or {}).get("tavily_api_key")),
            },
        )
        
        # 真实模式下需要初始化 AgentScope 组件
        if not self.mock_mode:
            self._initialize_real_mode()
        else:
            self.logger.info("DeepResearchTool initialized in MOCK mode")

    def _debug_log(self, run_id: str, hypothesis_id: str, location: str, message: str, data: dict):
        # region agent log
        try:
            log_path = Path(__file__).resolve().parents[3] / "debug-ced296.log"
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "sessionId": "ced296",
                    "runId": run_id,
                    "hypothesisId": hypothesis_id,
                    "location": location,
                    "message": message,
                    "data": data,
                    "timestamp": int(time.time() * 1000),
                }, ensure_ascii=False) + "\n")
        except Exception:
            pass
        # endregion

    def _schedule_tavily_connect(self):
        """Schedule Tavily MCP client connect for async contexts safely."""
        self._tavily_connect_task = None
        try:
            loop = asyncio.get_running_loop()
            # In async context: create a task instead of run_until_complete.
            self._tavily_connect_task = loop.create_task(self.tavily_client.connect())
            return
        except RuntimeError:
            # Not in a running event loop.
            asyncio.get_event_loop().run_until_complete(self.tavily_client.connect())
            self._tavily_connect_task = None

    async def _ensure_tavily_connected(self):
        task = getattr(self, "_tavily_connect_task", None)
        if task:
            await task
    
    def get_tool_schema(self) -> dict:
        """获取工具 Schema（用于 ReActAgent 注册）
        
        Returns:
            JSON Schema 定义
        """
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索查询关键词"
                },
                "max_depth": {
                    "type": "integer",
                    "description": "最大搜索深度（可选，默认 3）"
                }
            },
            "required": ["query"]
        }
    
    async def execute(self, query: str, **kwargs) -> str:
        """执行工具（统一接口）
        
        Args:
            query: 搜索查询
            kwargs: 其他参数（如 max_depth）
            
        Returns:
            搜索结果
        """
        max_depth = kwargs.get("max_depth", self.config.get("max_depth", 3))
        result = await self.search(query)
        return f"Search results for '{query}':\n{result}"
    
    def _initialize_real_mode(self):
        """初始化真实模式下的组件"""
        try:
            self._debug_log(
                run_id="pre-fix-deep-research",
                hypothesis_id="DR-H1",
                location="deep_research.py:110",
                message="Attempt importing DeepResearchAgent from agentscope.agent",
                data={},
            )
            from agentscope.agent import DeepResearchAgent
            from agentscope.model import OpenAIChatModel
            from agentscope.memory import InMemoryMemory
            from agentscope.mcp import StdIOStatefulClient
            from agentscope.message import Msg
            DeepResearchAgentImpl = DeepResearchAgent
            
            self.Msg = Msg
            
            # 获取配置
            api_key = self.config.get("openai_api_key")
            base_url = self.config.get("openai_base_url")
            model_name = self.config.get("model_name", "Qwen/Qwen3.5-27B")
            max_depth = self.config.get("max_depth", 3)
            max_iters = self.config.get("max_iters", 2)
            temperature = self.config.get("temperature", 0.7)
            self._debug_log(
                run_id="pre-fix-deep-research",
                hypothesis_id="DR-H2",
                location="deep_research.py:128",
                message="Resolved real mode config values",
                data={
                    "has_openai_api_key": bool(api_key),
                    "has_openai_base_url": bool(base_url),
                    "model_name": model_name,
                    "max_depth": max_depth,
                    "max_iters": max_iters,
                    "temperature": temperature,
                    "has_tavily_api_key": bool(self.config.get("tavily_api_key")),
                },
            )
            
            # 初始化 OpenAI 模型
            model_kwargs = {
                "model_name": model_name,
            }
            if api_key:
                model_kwargs["api_key"] = api_key
            if base_url:
                model_kwargs["client_kwargs"] = {"base_url": base_url}
            model_kwargs["generate_kwargs"] = {"temperature": temperature}
            self.model = OpenAIChatModel(**model_kwargs)
            
            # 初始化 Tavily MCP 客户端
            self.tavily_client = StdIOStatefulClient(
                name="tavily_mcp",
                command="npx",
                args=["-y", "tavily-mcp@latest"],
                env={"TAVILY_API_KEY": self.config.get("tavily_api_key")},
            )

            self._debug_log(
                run_id="pre-fix-deep-research",
                hypothesis_id="DR-H3",
                location="deep_research.py:155",
                message="Scheduling tavily client connect",
                data={"event_loop_running": True},
            )
            self._schedule_tavily_connect()
            
            # 初始化 DeepResearchAgent
            self.agent = DeepResearchAgent(
                name="DeepResearchWorker",
                model=self.model,
                memory=InMemoryMemory(),
                search_mcp_client=self.tavily_client,
                max_depth=max_depth,
                max_iters=max_iters,
            )
            
            self.logger.info("DeepResearchTool initialized in REAL mode with OpenAI API")

        except ImportError as e:
            try:
                from agentscope.model import OpenAIChatModel
                from agentscope.memory import InMemoryMemory
                from agentscope.mcp import StdIOStatefulClient
                from agentscope.message import Msg
                from agentscope.formatter import OpenAIChatFormatter
                DeepResearchAgentImpl = get_deep_research_agent_class()

                self.Msg = Msg

                self._debug_log(
                    run_id="post-fix-deep-research",
                    hypothesis_id="DR-H5",
                    location="deep_research.py:189",
                    message="DeepResearchAgent loaded by provider",
                    data={"agentscope_import_error": str(e), "impl_name": getattr(DeepResearchAgentImpl, "__name__", None)},
                )

                formatter = OpenAIChatFormatter()

                api_key = self.config.get("openai_api_key")
                base_url = self.config.get("openai_base_url")
                model_name = self.config.get("model_name", "Qwen/Qwen3.5-27B")
                max_depth = self.config.get("max_depth", 3)
                max_iters = self.config.get("max_iters", 2)
                temperature = self.config.get("temperature", 0.7)

                model_kwargs = {
                    "model_name": model_name,
                }
                if api_key:
                    model_kwargs["api_key"] = api_key
                if base_url:
                    model_kwargs["client_kwargs"] = {"base_url": base_url}
                model_kwargs["generate_kwargs"] = {"temperature": temperature}
                self.model = OpenAIChatModel(**model_kwargs)

                self.tavily_client = StdIOStatefulClient(
                    name="tavily_mcp",
                    command="npx",
                    args=["-y", "tavily-mcp@latest"],
                    env={"TAVILY_API_KEY": self.config.get("tavily_api_key")},
                )
                self._debug_log(
                    run_id="post-fix-deep-research",
                    hypothesis_id="DR-H7",
                    location="deep_research.py:234",
                    message="Scheduling tavily client connect (local fallback)",
                    data={"event_loop_running": True},
                )
                self._schedule_tavily_connect()

                self.agent = DeepResearchAgentImpl(
                    name="DeepResearchWorker",
                    model=self.model,
                    formatter=formatter,
                    memory=InMemoryMemory(),
                    search_mcp_client=self.tavily_client,
                    max_depth=max_depth,
                    max_iters=max_iters,
                    tmp_file_storage_dir="./tmp/deep_research",
                )

                self.logger.info("DeepResearchTool initialized in REAL mode using examples implementation")
                self.mock_mode = False
                return
            except Exception as inner_e:
                self._debug_log(
                    run_id="pre-fix-deep-research",
                    hypothesis_id="DR-H6",
                    location="deep_research.py:176",
                    message="DeepResearchAgent import failed (agentscope) and local fallback failed",
                    data={"error_type": type(e).__name__, "inner_error": str(inner_e)},
                )
                error_msg = f"DeepResearchAgent initialization failed in REAL mode: {inner_e}"
                self.logger.error(error_msg)
                raise RuntimeError(error_msg) from inner_e

        except Exception as e:
            self._debug_log(
                run_id="pre-fix-deep-research",
                hypothesis_id="DR-H4",
                location="deep_research.py:176",
                message="Real mode init failed",
                data={"error": str(e), "error_type": type(e).__name__},
            )
            error_msg = f"Failed to initialize DeepResearchTool in REAL mode: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    async def search(self, query: str) -> str:
        """执行深度搜索
        
        Args:
            query: 搜索查询
            
        Returns:
            综合研究报告（结构化文本）
        """
        if self.mock_mode:
            return self._mock_search(query)
        else:
            return await self._real_search(query)
    
    def _mock_search(self, query: str) -> str:
        """Mock 搜索（用于测试）
        
        Args:
            query: 搜索查询
            
        Returns:
            Mock 研究报告
        """
        self.logger.info(f"[MOCK] Searching for: {query}")
        
        # 返回一个示例报告
        return f"""# 深度研究报告

**查询**: {query}

## 关键发现

1. **行业最佳实践**: 
   - 客服 Agent 应该具备清晰的角色定位和职责范围
   - 需要定义明确的服务流程和状态转换规则
   - 应提供友好的用户引导和错误处理机制

2. **用户需求分析**:
   - 快速响应是首要需求
   - 准确理解用户意图至关重要
   - 提供个性化的服务体验

3. **技术实现建议**:
   - 使用状态机管理对话流程
   - 集成知识库提供准确信息
   - 支持人工坐席无缝转接

## 推荐澄清问题

基于以上研究，建议向用户提出以下问题以明确需求：

1. 目标客户群体是谁？
2. 核心业务流程有哪些？
3. 需要集成哪些外部系统？
4. 有哪些特定的合规要求？

---
*注：这是 Mock 模式的示例报告，实际使用时会调用真实的 Deep Research Agent 生成详细报告。*
"""
    
    async def _real_search(self, query: str) -> str:
        """真实搜索（生产环境）
        
        Args:
            query: 搜索查询
            
        Returns:
            综合研究报告
        """
        self.logger.info(f"[REAL] Searching for: {query}")
        
        try:
            await self._ensure_tavily_connected()
            result = await self.agent(self.Msg("user", query, "user"))
            report = result.get_text_content()
            
            self.logger.info("Search completed successfully")
            return report
        
        except Exception as e:
            error_msg = f"DeepResearch search failed in REAL mode: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    async def close(self):
        """关闭资源"""
        if not self.mock_mode and hasattr(self, 'tavily_client'):
            try:
                # Best-effort: agentscope client APIs differ by version.
                await self._ensure_tavily_connected()
                client = self.tavily_client

                if hasattr(client, "disconnect") and callable(getattr(client, "disconnect")):
                    await client.disconnect()
                    self.logger.info("Tavily MCP client disconnected")
                elif hasattr(client, "aclose") and callable(getattr(client, "aclose")):
                    await client.aclose()
                    self.logger.info("Tavily MCP client aclose() completed")
                elif hasattr(client, "close") and callable(getattr(client, "close")):
                    maybe_awaitable = client.close()
                    if asyncio.iscoroutine(maybe_awaitable):
                        await maybe_awaitable
                    self.logger.info("Tavily MCP client close() completed")
                else:
                    self.logger.warning("Tavily MCP client has no known close method; skipping")
            except Exception as e:
                self.logger.error(f"Error disconnecting Tavily client: {e}")
        
        self.logger.info("DeepResearchTool closed")
