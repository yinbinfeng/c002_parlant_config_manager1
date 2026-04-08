#!/usr/bin/env python3
"""Deep Research 工具封装 - 基于 AgentScope 的 DeepResearchAgent"""

import asyncio
import contextvars
from typing import Optional, Tuple
from datetime import datetime
import json
import time
import os
import sys
import traceback
import re
from pathlib import Path
from ..utils.logger import logger
from ..utils.performance_tracker import get_performance_tracker

# ReAct 通过 Toolkit 调用 deep_research 时无法传入 audit 参数，用上下文变量归因到当前 Agent / step 目录。
_dr_ctx_caller: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("mining_dr_caller", default=None)
_dr_ctx_audit_dir: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("mining_dr_audit_dir", default=None)


def push_deep_research_audit_context(
    caller: Optional[str],
    audit_dir: Optional[str],
) -> Tuple[contextvars.Token, contextvars.Token]:
    return _dr_ctx_caller.set(caller), _dr_ctx_audit_dir.set(audit_dir)


def reset_deep_research_audit_context(tokens: Optional[Tuple[contextvars.Token, contextvars.Token]]) -> None:
    if not tokens:
        return
    t1, t2 = tokens
    try:
        _dr_ctx_caller.reset(t1)
    except Exception:
        pass
    try:
        _dr_ctx_audit_dir.reset(t2)
    except Exception:
        pass


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
        self._ensure_utf8_stdio()
        self._init_lock = asyncio.Lock()
        self._search_lock = asyncio.Lock()
        self._tavily_connected = False
        # 失败计数和降级标志
        self._failure_count = 0
        self._max_failures = int(config.get("max_failures_before_fallback", 3))
        self._fallback_mode = False
        # 是否允许降级（从配置读取）
        self._allow_fallback = bool(config.get("allow_fallback_on_failure", True))
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
                "max_failures_before_fallback": self._max_failures,
                "allow_fallback_on_failure": self._allow_fallback,
            },
        )
        
        # 真实模式下需要初始化 AgentScope 组件
        if not self.mock_mode:
            self._initialize_real_mode()
        else:
            self.logger.info("DeepResearchTool initialized in MOCK mode")

    @staticmethod
    def _ensure_utf8_stdio() -> None:
        """在 Windows/GBK 终端下强制 UTF-8 输出，避免控制台编码异常。"""
        os.environ.setdefault("PYTHONUTF8", "1")
        os.environ["PYTHONIOENCODING"] = "utf-8"
        for stream_name in ("stdout", "stderr"):
            stream = getattr(sys, stream_name, None)
            if hasattr(stream, "reconfigure"):
                try:
                    stream.reconfigure(encoding="utf-8", errors="backslashreplace")
                except Exception:
                    # 某些运行时不可重配，保持兼容
                    continue

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
        pass

    async def _ensure_tavily_connected(self):
        async with self._init_lock:
            if self._tavily_connected:
                return
            try:
                # HTTP SDK client 无需显式 connect，这里仅做一次可用性检查与状态设置。
                if not getattr(self, "tavily_client", None):
                    raise RuntimeError("Tavily client not initialized")
                self._tavily_connected = True
                self.logger.info("Tavily SDK client ready")
            except Exception as e:
                self._tavily_connected = False
                self.logger.error("Failed to prepare Tavily SDK client: {}", e)
                self.logger.debug(
                    "Tavily SDK prepare traceback:\n{}",
                    "".join(traceback.format_exception(type(e), e, e.__traceback__, limit=16)),
                )
                raise
    
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
        kwargs.pop("max_depth", None)
        audit_output_dir = kwargs.get("audit_output_dir") or _dr_ctx_audit_dir.get()
        caller_agent = kwargs.get("caller_agent") or kwargs.get("caller") or _dr_ctx_caller.get()
        query_tag = kwargs.get("query_tag")
        result = await self.search(
            query,
            audit_output_dir=audit_output_dir,
            caller_agent=caller_agent,
            query_tag=query_tag,
        )
        return f"Search results for '{query}':\n{result}"
    
    def is_fallback_mode(self) -> bool:
        """检查是否已降级到 fallback 模式
        
        Returns:
            True 表示已降级，False 表示正常
        """
        return self._fallback_mode
    
    def get_failure_count(self) -> int:
        """获取当前失败次数
        
        Returns:
            失败次数
        """
        return self._failure_count
    
    def reset_failure_count(self):
        """重置失败计数（成功执行后调用）"""
        self._failure_count = 0
        self._fallback_mode = False
        self.logger.info("DeepResearchTool failure count reset")
    
    def increment_failure_count(self):
        """增加失败计数并检查是否需要降级或抛异常
        
        Returns:
            True 表示需要降级，False 表示还可以继续尝试
        Raises:
            RuntimeError: 当不允许降级且达到最大失败次数时
        """
        self._failure_count += 1
        if self._failure_count >= self._max_failures:
            if self._allow_fallback:
                # 允许降级：进入 fallback 模式
                self._fallback_mode = True
                self.logger.warning(
                    f"DeepResearchTool reached max failures ({self._failure_count}/{self._max_failures}), "
                    f"entering fallback mode (allow_fallback_on_failure=true). Subsequent calls will use model's own knowledge."
                )
                return True
            else:
                # 不允许降级：抛出异常停止
                error_msg = (
                    f"DeepResearchTool reached max failures ({self._failure_count}/{self._max_failures}) "
                    f"and fallback is disabled (allow_fallback_on_failure=false). "
                    f"Stopping execution. Please check Tavily API configuration and network status."
                )
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)
        self.logger.warning(
            f"DeepResearchTool failure count increased ({self._failure_count}/{self._max_failures})"
        )
        return False
    
    def _initialize_real_mode(self):
        """初始化真实模式下的组件"""
        try:
            try:
                from tavily import AsyncTavilyClient
            except ImportError as ie:
                raise RuntimeError(
                    "未安装 tavily-python，无法在真实模式下使用 Deep Research。"
                    "请执行：pip install tavily-python"
                ) from ie
            tavily_api_key = str(self.config.get("tavily_api_key") or "").strip()
            if not tavily_api_key:
                raise RuntimeError("tavily_api_key is empty in real mode")
            self.tavily_client = AsyncTavilyClient(api_key=tavily_api_key)
            self._tavily_connected = True
            self.logger.info("DeepResearchTool initialized in REAL mode with Tavily Python SDK")
        except Exception as e:
            self._debug_log(
                run_id="pre-fix-deep-research",
                hypothesis_id="DR-H4",
                location="deep_research.py:_initialize_real_mode",
                message="Real mode init failed",
                data={"error": str(e), "error_type": type(e).__name__},
            )
            error_msg = f"Failed to initialize DeepResearchTool in REAL mode: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    @staticmethod
    def _build_report_from_tavily_result(query: str, result: dict, max_items: int = 5) -> str:
        results = []
        if isinstance(result, dict):
            maybe_results = result.get("results")
            if isinstance(maybe_results, list):
                results = maybe_results[:max_items]
        lines = [f"# 深度研究报告", "", f"**查询**: {query}", "", "## 检索结果（Tavily SDK）", ""]
        if not results:
            lines.append("[无可用检索结果]")
        for idx, item in enumerate(results, start=1):
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "无标题")
            url = str(item.get("url") or "")
            content = str(item.get("content") or "").strip()
            if len(content) > 600:
                content = content[:600] + "..."
            lines.extend(
                [
                    f"{idx}. **{title}**",
                    f"   - URL: {url}",
                    f"   - 摘要: {content or '[无摘要]'}",
                ],
            )
        return "\n".join(lines)

    def _write_dr_audit(
        self,
        audit_output_dir: Optional[str],
        caller_agent: str,
        query: str,
        report: Optional[str],
        error: Optional[str],
        query_tag: Optional[str],
    ) -> None:
        """将单次 Deep Research（Tavily）检索结果写入 step 输出目录，便于审计。"""
        if not audit_output_dir:
            return
        try:
            root = Path(str(audit_output_dir))
            sub = root / "deep_research_audit"
            sub.mkdir(parents=True, exist_ok=True)
            safe_caller = "".join(c if c.isalnum() or c in "._-" else "_" for c in (caller_agent or "unknown"))[:72]
            ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            rec = {
                "ts": datetime.now().isoformat(),
                "caller_agent": caller_agent,
                "query_tag": query_tag,
                "query": query,
                "ok": error is None,
                "error": error,
                "report_chars": len(report or ""),
            }
            with open(sub / "audit.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            err_part = f"\n## 错误\n\n{error}\n" if error else ""
            tag_part = f"\n**标签**: {query_tag}\n" if query_tag else ""
            body = (
                f"# Deep Research（Tavily）审计\n\n"
                f"**caller**: {caller_agent}{tag_part}\n"
                f"**query**: {query}\n\n"
                f"## 报告正文\n\n{(report or '')}\n"
                f"{err_part}"
            )
            with open(sub / f"report_{safe_caller}_{ts}.md", "w", encoding="utf-8") as f:
                f.write(body)
            self.logger.info("Deep Research audit written under {}", sub)
        except Exception as ex:
            self.logger.warning("Failed to write deep research audit: {}", ex)
    
    async def search(
        self,
        query: str,
        *,
        audit_output_dir: Optional[str] = None,
        caller_agent: Optional[str] = None,
        query_tag: Optional[str] = None,
    ) -> str:
        """执行深度搜索
        
        Args:
            query: 搜索查询
            audit_output_dir: 审计日志目录（通常为当前 step 的 output_dir）
            caller_agent: 调用方标识（用于性能统计与审计文件命名）
            query_tag: 可选简短标签，区分同一步骤内多次查询
            
        Returns:
            综合研究报告（结构化文本）
        """
        caller = caller_agent or _dr_ctx_caller.get() or "DeepResearchTool"
        audit_merged = audit_output_dir or _dr_ctx_audit_dir.get()
        if self.mock_mode:
            return self._mock_search(query)
        else:
            # DeepResearchAgent 持有状态（memory/subtask），同实例并发调用会相互污染。
            async with self._search_lock:
                try:
                    result = await self._real_search(
                        query,
                        audit_output_dir=audit_merged,
                        caller_agent=caller,
                        query_tag=query_tag,
                    )
                    # 成功后重置失败计数
                    self.reset_failure_count()
                    return result
                except Exception as e:
                    # 失败时增加失败计数
                    self.increment_failure_count()
                    self._write_dr_audit(
                        audit_merged,
                        caller,
                        query,
                        None,
                        str(e),
                        query_tag,
                    )
                    raise
    
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
    
    async def _real_search(
        self,
        query: str,
        *,
        audit_output_dir: Optional[str] = None,
        caller_agent: str = "DeepResearchTool",
        query_tag: Optional[str] = None,
    ) -> str:
        """真实搜索（生产环境）
        
        Args:
            query: 搜索查询
            
        Returns:
            综合研究报告
        """
        normalized_query = " ".join((query or "").split())
        tavily_query = self._build_tavily_query_from_brief(normalized_query)
        query_preview = normalized_query[:300] + ("..." if len(normalized_query) > 300 else "")
        tavily_query_preview = tavily_query[:240] + ("..." if len(tavily_query) > 240 else "")
        self.logger.info(
            f"[REAL] Searching brief(query_len={len(normalized_query)}): {query_preview}",
        )
        self.logger.info(
            f"[REAL] Tavily keyword query(query_len={len(tavily_query)}): {tavily_query_preview}",
        )
        
        try:
            await self._ensure_tavily_connected()
            timeout_sec = int(self.config.get("timeout_sec", 120))
            max_report_chars = int(self.config.get("max_report_chars", 6000))
            max_results = int(self.config.get("tavily_max_results", 5))
            search_depth = str(self.config.get("tavily_search_depth", "advanced"))
            include_raw_content = bool(self.config.get("tavily_include_raw_content", False))
            tavily_retry_on_rate_limit = bool(self.config.get("tavily_retry_on_rate_limit", True))
            tavily_retry_delay_sec = int(self.config.get("tavily_retry_delay_sec", 30))
            tavily_max_retries = int(self.config.get("tavily_max_retries", 3))
            tavily_backoff_multiplier = float(self.config.get("tavily_retry_backoff_multiplier", 2.0))
            self.logger.info(
                "Tavily SDK search config: depth={}, max_results={}, on_rate_limit={}, delay={}s, max_retries={}, backoff={}",
                search_depth,
                max_results,
                tavily_retry_on_rate_limit,
                tavily_retry_delay_sec,
                tavily_max_retries,
                tavily_backoff_multiplier,
            )
            last_err = None
            for attempt in range(tavily_max_retries + 1):
                try:
                    coro = self.tavily_client.search(
                        tavily_query,
                        max_results=max_results,
                        search_depth=search_depth,
                        include_raw_content=include_raw_content,
                    )
                    result = await asyncio.wait_for(coro, timeout=timeout_sec)
                    self.logger.info("Tavily SDK raw result keys: {}", list(result.keys()) if isinstance(result, dict) else type(result))
                    report = self._build_report_from_tavily_result(normalized_query, result)
                    if isinstance(report, str) and len(report) > max_report_chars:
                        report = (
                            report[:max_report_chars]
                            + f"\n\n[TRUNCATED] report too long, kept first {max_report_chars} chars."
                        )
                    self.logger.info("Search completed successfully")
                    try:
                        get_performance_tracker().record_tavily_call(caller_agent)
                    except Exception:
                        pass
                    self._write_dr_audit(
                        audit_output_dir,
                        caller_agent,
                        normalized_query,
                        report,
                        None,
                        query_tag,
                    )
                    return report
                except Exception as e:
                    self.logger.error(
                        "【Tavily】search() 报错 message={!s} | repr={!r}",
                        e,
                        e,
                    )
                    self.logger.error("DeepResearch inner exception (Tavily SDK):")
                    self.logger.error(f"  - Exception type: {type(e).__name__}")
                    self.logger.error(f"  - Exception message: {e!s}")
                    self.logger.error(f"  - Exception args: {e.args}")
                    self.logger.error(
                        "  - Traceback (limit=12):\n"
                        + "".join(traceback.format_exception(type(e), e, e.__traceback__, limit=12)),
                    )

                    last_err = e
                    msg = str(e).lower()
                    is_timeout = isinstance(e, asyncio.TimeoutError) or "timed out" in msg
                    is_invalid_response = "invalid tavily response detected" in msg
                    is_rate_limit_http = any(
                        s in msg for s in ("429", "rate limit", "too many requests", "rpm", "quota")
                    )
                    is_rate_limit = (
                        (is_invalid_response and tavily_retry_on_rate_limit)
                        or is_rate_limit_http
                    )
                    if is_timeout:
                        self.logger.warning(
                            f"DeepResearch timeout (attempt={attempt + 1}/{tavily_max_retries + 1}, timeout_sec={timeout_sec}, query_len={len(normalized_query)})",
                        )
                    if is_invalid_response:
                        self.logger.warning(
                            f"DeepResearch invalid response (attempt={attempt + 1}/{tavily_max_retries + 1})",
                        )
                    if is_rate_limit_http:
                        self.logger.warning(
                            f"DeepResearch retryable rate error (attempt={attempt + 1}/{tavily_max_retries + 1}): "
                            f"rate_http={is_rate_limit_http}",
                        )
                    if is_rate_limit:
                        self.logger.warning("Detected retryable Tavily condition, will backoff and retry if attempts remain.")
                    if (is_timeout or is_rate_limit) and attempt < tavily_max_retries:
                        retry_reason = "timeout" if is_timeout else "rate_limit"
                        if is_timeout:
                            wait_time = 1.0 * (attempt + 1)
                        else:
                            wait_time = tavily_retry_delay_sec * (tavily_backoff_multiplier ** attempt)
                        self.logger.warning(
                            f"DeepResearch {retry_reason}, waiting {wait_time:.1f}s before retry "
                            f"(attempt={attempt + 1}/{tavily_max_retries + 1}, base_delay={tavily_retry_delay_sec}s, backoff={tavily_backoff_multiplier})...",
                        )
                        await asyncio.sleep(wait_time)
                        self.logger.warning(
                            f"DeepResearch {retry_reason}, retrying ({attempt + 1}/{tavily_max_retries})...",
                        )
                        continue
                    raise last_err
            
            # 如果循环正常结束但没有 return（理论上不应该发生）
            self.logger.error("DeepResearch retry loop completed without returning a result")
            raise RuntimeError("DeepResearch failed after all retries")
        
        except Exception as e:
            self.logger.error(
                "【Tavily】DeepResearch 搜索最终失败 message={!s} | repr={!r}",
                e,
                e,
            )
            error_msg = f"DeepResearch search failed in REAL mode: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    @staticmethod
    def _build_tavily_query_from_brief(research_brief: str) -> str:
        """把“深度研究任务说明”压缩为搜索引擎友好的关键词短语。"""
        text = " ".join((research_brief or "").split()).strip()
        if not text:
            return ""

        # 若本身已经是短查询，直接使用
        if len(text) <= 72 and text.count(" ") <= 8:
            return text

        # 去掉常见“提示词套话”，保留主题词
        text = re.sub(r"请研究|请分析|请基于|请调研|请输出|请给出|最佳实践|完整报告|深度报告", " ", text, flags=re.IGNORECASE)

        # 优先抽取“业务描述=”后的领域锚点，降低被“方法论措辞”带偏的概率
        business_part = ""
        if "业务描述=" in text:
            business_part = text.split("业务描述=", 1)[-1]
        elif "business_desc=" in text.lower():
            m = re.search(r"business_desc=(.*)$", text, flags=re.IGNORECASE)
            business_part = (m.group(1) if m else "") or ""

        domain_tokens = re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}|[\u4e00-\u9fff]{2,16}", business_part)
        tokens = re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}|[\u4e00-\u9fff]{2,16}", text)
        if not tokens:
            return research_brief[:96]

        stop_words = {
            "请研究", "请分析", "请调研", "场景", "完整", "报告", "深度", "输出", "要求",
            "根据", "基于", "相关", "以及", "关于", "进行", "生成", "提供",
            "best", "practice", "report", "analysis",
        }
        prioritized = []
        for t in domain_tokens:
            if t not in prioritized:
                prioritized.append(t)

        seen = set()
        kept = []
        for t in prioritized + tokens:
            low = t.lower()
            if t in stop_words or low in stop_words:
                continue
            if low in seen:
                continue
            seen.add(low)
            kept.append(t)
            if len(kept) >= 12:
                break

        if not kept:
            kept = tokens[:8]
        return " ".join(kept)
    
    async def close(self):
        """关闭资源（Tavily Python SDK 无需显式关闭）。"""
        if self.mock_mode:
            self.logger.info("DeepResearchTool closed")
            return
        self._tavily_connected = False
        self.logger.info("DeepResearchTool closed")
