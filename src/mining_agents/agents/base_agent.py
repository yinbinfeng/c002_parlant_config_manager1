#!/usr/bin/env python3
"""Agent 基类 - 集成 AgentScope 大模型能力"""

from typing import Dict, Any, Optional, List
import time
import os
import json
import asyncio
import re
from datetime import datetime
from pathlib import Path
from agentscope.model import OpenAIChatModel, DashScopeChatModel
from agentscope.agent import ReActAgent
from agentscope.message import Msg
from agentscope.formatter import OpenAIChatFormatter, DashScopeChatFormatter
from agentscope.tool import Toolkit, ToolResponse
from ..utils.logger import logger
from ..utils.error_handler import AgentErrorHandler, FallbackStrategy
from ..utils.performance_tracker import get_performance_tracker
from ..tools.deep_research import push_deep_research_audit_context, reset_deep_research_audit_context


class BaseAgent:
    """Agent 基类 - 集成 AgentScope 大模型能力
    
    提供统一的大模型调用接口，所有具体 Agent 都应该继承自此类。
    """
    
    def __init__(self, name: str, orchestrator, **kwargs):
        """初始化 Agent
        
        Args:
            name: Agent 名称
            orchestrator: Agent 编排器
            **kwargs: 其他参数，包含：
                - model: 模型配置
                - tools: 工具列表
        """
        self.name = name
        self.orchestrator = orchestrator
        self.logger = logger
        
        self.performance_tracker = get_performance_tracker()
        
        # 加载配置
        from ..utils.config_loader import get_config_loader
        config_loader = get_config_loader()
        self.config = config_loader.load_agent_config(name)
        
        # 从配置获取系统提示词
        # 注意：system_prompt_template 在 agent yaml 中通常是“提示词文本”，而不是“模板文件路径”
        self.system_prompt = self.config.get('system_prompt_template', None)

        # BaseAgent 内部目前并不需要额外的 prompt_template 文件加载
        self.prompt_template = ""
        if isinstance(self.system_prompt, str) and self.system_prompt.strip():
            # region agent log
            try:
                self._debug_log(
                    run_id="post-fix",
                    hypothesis_id="PW-H1",
                    location="base_agent.py:49",
                    message="system_prompt_template treated as inline prompt text",
                    data={
                        "system_prompt_is_multiline": "\n" in self.system_prompt,
                        "system_prompt_preview": self.system_prompt.strip()[:30],
                        "system_prompt_len": len(self.system_prompt),
                    },
                )
            except Exception:
                pass
            # endregion
        
        # 加载任务提示词模板（新增）
        self.task_prompts = self.config.get('task_prompts', {})
        
        # 模型配置
        self.model_config = self.config.get('model', {})
        
        # ReAct 配置
        self.react_config = {
            'max_rounds': self.model_config.get('react_max_rounds', 5),  # 默认 5 轮
            # 与 OpenAI 兼容网关下 Qwen 非思考模式默认对齐；需思考时在 agent yaml 显式 enable_thinking: true
            'enable_thinking': self.model_config.get('enable_thinking', False),
        }
        
        # 初始化模型（默认使用 Model 接口）
        self.model = None
        self.agent = None  # 仅当需要 ReAct 时才初始化
        
        # 初始化错误处理器
        self.error_handler = AgentErrorHandler(logger=self.logger, default_retries=3)
        
        self._init_model()
        
        # 从编排器获取工具
        self.tools = {}
        self._load_tools()

    def _debug_log(self, run_id: str, hypothesis_id: str, location: str, message: str, data: Dict[str, Any]):
        # region agent log
        try:
            log_path = Path(__file__).resolve().parents[3] / "debug-ced296.log"
            with open(log_path, "a", encoding="utf-8") as f:
                import json as _json
                f.write(_json.dumps({
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

    def _llm_log_preview_chars(self) -> int:
        try:
            system_config = (getattr(self.orchestrator, "config", {}) or {}).get("system_config", {}) or {}
            logging_cfg = system_config.get("logging", {}) or {}
            return max(200, int(logging_cfg.get("llm_message_preview_chars", 1200)))
        except Exception:
            return 1200

    def _preview_text(self, text: Any) -> str:
        s = str(text or "")
        limit = self._llm_log_preview_chars()
        return s[:limit] + ("..." if len(s) > limit else "")

    @staticmethod
    def _safe_error_text(err: Any) -> str:
        try:
            return str(err)
        except Exception:
            try:
                return repr(err)
            except Exception:
                return "<unprintable error>"

    def _react_trace_file(self, context: Dict[str, Any] = None) -> Optional[Path]:
        try:
            ctx = context or {}
            base_dir = ctx.get("output_dir") or ctx.get("step_message_archive_dir")
            if not base_dir:
                return None
            p = Path(str(base_dir))
            p.mkdir(parents=True, exist_ok=True)
            return p / f"{self.name}_react_trace.log"
        except Exception:
            return None

    def _react_messages_jsonl_path(self, context: Dict[str, Any] = None) -> Optional[Path]:
        try:
            ctx = context or {}
            base_dir = ctx.get("output_dir") or ctx.get("step_message_archive_dir")
            if not base_dir:
                return None
            p = Path(str(base_dir))
            p.mkdir(parents=True, exist_ok=True)
            return p / f"{self.name}_react_messages.jsonl"
        except Exception:
            return None

    def _content_to_jsonable(self, content: Any) -> Any:
        if content is None:
            return None
        if isinstance(content, (str, int, float, bool)):
            return content
        if isinstance(content, list):
            blocks = []
            for b in content:
                if isinstance(b, dict):
                    blocks.append(b)
                    continue
                if hasattr(b, "model_dump"):
                    try:
                        blocks.append(b.model_dump())
                        continue
                    except Exception:
                        pass
                blocks.append(
                    {
                        "type": getattr(b, "type", None),
                        "text": getattr(b, "text", None),
                        "thinking": getattr(b, "thinking", None),
                    }
                )
            return blocks
        if hasattr(content, "model_dump"):
            try:
                return content.model_dump()
            except Exception:
                pass
        return str(content)

    def _message_to_dict(self, m: Any) -> Dict[str, Any]:
        if isinstance(m, dict):
            c = m.get("content")
            return {
                "role": m.get("role"),
                "name": m.get("name"),
                "content": self._content_to_jsonable(c),
            }
        role = getattr(m, "role", None)
        name = getattr(m, "name", None)
        content = getattr(m, "content", None)
        return {
            "role": role,
            "name": name,
            "content": self._content_to_jsonable(content),
        }

    @staticmethod
    def _estimate_react_llm_rounds(msgs: List[Any]) -> int:
        n = 0
        for m in msgs:
            if isinstance(m, dict):
                r = m.get("role")
            else:
                r = getattr(m, "role", None)
            if str(r or "").lower() == "assistant":
                n += 1
        return n

    def _is_mock_mode(self, context: Optional[Dict[str, Any]]) -> bool:
        if context is not None and "mock_mode" in context:
            return bool(context.get("mock_mode"))
        oc = getattr(self.orchestrator, "config", None) or {}
        return bool(oc.get("mock_mode", True))

    @staticmethod
    def _text_from_chat_response(result: Any) -> str:
        """从 AgentScope ChatResponse（或兼容结构）提取正文，跳过 thinking 块。"""
        parts: List[str] = []
        content_blocks = getattr(result, "content", None) or []
        for b in content_blocks:
            btype = getattr(b, "type", None)
            if btype is None and isinstance(b, dict):
                btype = b.get("type")
            if str(btype or "").lower() == "thinking":
                continue
            text = getattr(b, "text", None)
            if text is None and isinstance(b, dict):
                text = b.get("text")
            if text:
                parts.append(str(text))
        out = "".join(parts).strip()
        if out:
            return out
        if isinstance(result, dict) and "content" in result:
            return str(result.get("content", "")).strip()
        return ""

    @staticmethod
    def _extract_json_text_candidates(text: str) -> List[str]:
        """从混合输出中抽取可疑 JSON 文本候选（兼容 think/markdown 包裹）。"""
        s = str(text or "").strip()
        if not s:
            return []

        candidates: List[str] = [s]

        # ```json ... ``` / ``` ... ``` 代码块
        for block in re.findall(r"```(?:json)?\s*(.*?)```", s, flags=re.IGNORECASE | re.DOTALL):
            b = (block or "").strip()
            if b:
                candidates.append(b)

        # <think> ... </think> 分离（保留 think 内外两种候选）
        for th in re.findall(r"<think>(.*?)</think>", s, flags=re.IGNORECASE | re.DOTALL):
            t = (th or "").strip()
            if t:
                candidates.append(t)
        outside_think = re.sub(r"<think>.*?</think>", " ", s, flags=re.IGNORECASE | re.DOTALL).strip()
        if outside_think:
            candidates.append(outside_think)

        # 兼容日志样式：Agent(thinking): ... / Agent: ...
        for m in re.findall(r"\b[\w.-]+\s*\(thinking\)\s*:\s*(.*?)(?=\n[\w.-]+\s*:|\Z)", s, flags=re.DOTALL):
            t = (m or "").strip()
            if t:
                candidates.append(t)
        for m in re.findall(r"\b[\w.-]+\s*:\s*(.*)$", s, flags=re.DOTALL):
            t = (m or "").strip()
            if t:
                candidates.append(t)

        # 对每个候选再尝试抽出最外层 {} / []
        expanded: List[str] = []
        for c in candidates:
            cc = (c or "").strip()
            if not cc:
                continue
            expanded.append(cc)
            l_obj, r_obj = cc.find("{"), cc.rfind("}")
            if l_obj != -1 and r_obj != -1 and r_obj > l_obj:
                expanded.append(cc[l_obj:r_obj + 1])
            l_arr, r_arr = cc.find("["), cc.rfind("]")
            if l_arr != -1 and r_arr != -1 and r_arr > l_arr:
                expanded.append(cc[l_arr:r_arr + 1])

        uniq: List[str] = []
        seen = set()
        for c in expanded:
            if c not in seen:
                seen.add(c)
                uniq.append(c)
        return uniq

    async def _llm_fix_json_once(
        self,
        raw_text: str,
        context: Optional[Dict[str, Any]] = None,
        schema_hint: str = "JSON object",
    ) -> str:
        """调用一次 LLM 将损坏文本修复为纯 JSON（不含解释/围栏）。"""
        prompt = (
            f"请把下面内容修复成严格合法的 {schema_hint}。\n"
            "要求：\n"
            "1) 仅输出 JSON 本体；\n"
            "2) 不要输出 Markdown 代码围栏；\n"
            "3) 不要解释说明；\n"
            "4) 若存在 think/日志前缀，去掉它们，仅保留业务结果。\n\n"
            "待修复内容：\n"
            f"{raw_text}"
        )
        return await self.call_llm(prompt, context)

    async def _get_react_memory_messages(self) -> List[Any]:
        memory = getattr(self.agent, "memory", None)
        if memory is None:
            return []
        try:
            if hasattr(memory, "get_memory"):
                msgs = await memory.get_memory()
            else:
                msgs = getattr(memory, "messages", None)
            if not isinstance(msgs, list):
                return []
            return msgs
        except Exception:
            return []

    def _append_react_messages_jsonl(self, context: Dict[str, Any], messages_raw: List[Any]) -> None:
        fp = self._react_messages_jsonl_path(context)
        if fp is None:
            return
        try:
            serialized = [self._message_to_dict(m) for m in messages_raw]
            record = {
                "ts": datetime.now().isoformat(),
                "agent": self.name,
                "message_count": len(serialized),
                "messages": serialized,
            }
            with open(fp, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            self.logger.info("[{}] ReAct messages appended to {}", self.name, fp)
        except Exception:
            pass

    def _append_react_trace(self, context: Dict[str, Any], message: str) -> None:
        fp = self._react_trace_file(context)
        if fp is None:
            return
        try:
            line = f"{datetime.now().isoformat()} | {message}\n"
            with open(fp, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            pass

    async def _react_memory_snapshot(self) -> str:
        """尽力抓取 ReAct 内存快照，用于长耗时期间可观测性。"""
        try:
            memory = getattr(self.agent, "memory", None)
            if memory is None:
                return "memory=none"
            # 兼容不同 memory API：优先 get_memory，再兜底 messages
            if hasattr(memory, "get_memory"):
                msgs = await memory.get_memory()
            else:
                msgs = getattr(memory, "messages", None)
            if not isinstance(msgs, list) or not msgs:
                return "memory=empty"
            last = msgs[-1]
            role = getattr(last, "role", None) or (last.get("role") if isinstance(last, dict) else None)
            content = getattr(last, "content", None) if not isinstance(last, dict) else last.get("content")
            return f"memory_count={len(msgs)}, last_role={role}, last_content={self._preview_text(content)}"
        except Exception as e:
            return f"memory_snapshot_error={e}"
    
    def _create_model(self):
        """创建模型实例（复用方法）
        
        Returns:
            模型实例
        """
        nested_config = self.model_config.get('config', {})
        if not isinstance(nested_config, dict):
            nested_config = {}

        model_name = self.model_config.get('model_name') or nested_config.get('model_name') or 'Qwen/Qwen3.5-27B'
        temperature = self.model_config.get('temperature')
        if temperature is None:
            temperature = nested_config.get('temperature', 0.7)
        enable_thinking = self.model_config.get('enable_thinking')
        if enable_thinking is None:
            enable_thinking = nested_config.get('enable_thinking')
        timeout_sec = self.model_config.get('timeout_sec')
        if timeout_sec is None:
            timeout_sec = nested_config.get('timeout_sec')

        model_type = self.model_config.get('type', 'OpenAIChatModel')

        # 从 agent 配置获取 api_key 和 base_url
        api_key = (
            self.model_config.get('api_key')
            or nested_config.get('api_key')
        )
        base_url = (
            self.model_config.get('base_url')
            or nested_config.get('base_url')
        )
        
        # 从 orchestrator 配置回退获取系统级凭据
        if not api_key and hasattr(self, 'orchestrator') and hasattr(self.orchestrator, 'config'):
            system_config = self.orchestrator.config.get('system_config', {})
            openai_cfg = system_config.get('openai', {})
            api_key = openai_cfg.get('api_key')
            if not base_url:
                base_url = openai_cfg.get('base_url')
            if timeout_sec is None:
                timeout_sec = openai_cfg.get('request_timeout_sec')
        if timeout_sec is None:
            timeout_sec = 180.0
        
        # 最后从环境变量回退（按模型类型区分默认 Key）
        if not api_key:
            if model_type == "DashScopeChatModel":
                api_key = os.getenv("DASHSCOPE_API_KEY")
            else:
                api_key = os.getenv("OPENAI_API_KEY")

        # base_url 优先从环境变量读取（兼容 OpenAI 网关/代理）
        if not base_url and model_type != "DashScopeChatModel":
            base_url = os.getenv("OPENAI_BASE_URL") or base_url
        if not base_url:
            base_url = "https://api.openai.com/v1"
        
        self._debug_log(
            run_id="post-fix",
            hypothesis_id="H2",
            location="base_agent.py:102",
            message="Preparing model init arguments",
            data={
                "agent_name": self.name,
                "model_type": model_type,
                "model_config_keys": list((self.model_config or {}).keys()),
                "model_name": model_name,
                "temperature": temperature,
                "has_direct_api_key": bool(api_key),
                "base_url": base_url,
            },
        )

        if model_type == 'DashScopeChatModel':
            # 初始化 DashScopeChatModel
            model_kwargs = {
                "model_name": model_name,
            }
            if api_key:
                model_kwargs["api_key"] = api_key
            if temperature:
                model_kwargs["generate_kwargs"] = {"temperature": temperature}
            return DashScopeChatModel(**model_kwargs)
        else:
            # 初始化 OpenAIChatModel 或兼容模型
            model_kwargs = {
                "model_name": model_name,
            }
            if api_key:
                model_kwargs["api_key"] = api_key
            if base_url:
                model_kwargs["client_kwargs"] = {
                    "base_url": base_url,
                    "timeout": float(timeout_sec),
                }
            else:
                model_kwargs["client_kwargs"] = {
                    "timeout": float(timeout_sec),
                }
            generate_kwargs = {}
            if temperature is not None:
                generate_kwargs["temperature"] = temperature
            # 与 Qwen/OpenAI 兼容接口建议一致：默认关闭 thinking，减少多余块与下游 JSON 解析风险；仅当配置显式为 true 时开启
            thinking_on = enable_thinking is True
            generate_kwargs["extra_body"] = {
                "chat_template_kwargs": {"enable_thinking": thinking_on},
            }
            model_kwargs["generate_kwargs"] = generate_kwargs
            return OpenAIChatModel(**model_kwargs)
    
    def _init_model(self):
        """初始化 Model（基础接口）"""
        try:
            self.model = self._create_model()
            self.logger.info(f"Model initialized: {self.model_config.get('model_name')}")
            
        except Exception as e:
            # 使用错误处理器，静默失败
            self.model = self.error_handler.handle(
                error=e,
                fallback_strategy=FallbackStrategy.SILENT,
                operation_name="Model initialization"
            )
    
    def _init_react_agent(self):
        """初始化 ReActAgent（仅当需要时调用）
        
        ReAct 模式适用于：
        - 需要调用工具的 Agent
        - 需要自主选择工具的 Agent
        - 需要反思修正的 Agent
        - 需要多轮推理的 Agent
        """
        try:
            model = self._create_model()
            system_config = (getattr(self.orchestrator, "config", {}) or {}).get("system_config", {}) or {}
            logging_cfg = system_config.get("logging", {}) or {}
            react_print_hint_msg = bool(logging_cfg.get("react_print_hint_msg", True))

            model_type = self.model_config.get('type', 'OpenAIChatModel')
            formatter = DashScopeChatFormatter() if model_type == "DashScopeChatModel" else OpenAIChatFormatter()

            toolkit = None
            if self.tools:
                toolkit = Toolkit()
                for tool_name, tool_instance in self.tools.items():
                    try:
                        if tool_name == "deep_research":
                            tool_inst = tool_instance
                            async def deep_research_wrapper(query: str, tool_inst=tool_inst) -> ToolResponse:
                                """Deep Research 工具 - 执行深度搜索并返回研究报告"""
                                result = await tool_inst.search(query)
                                return ToolResponse(content=[result])
                            deep_research_wrapper.__name__ = "deep_research"
                            deep_research_wrapper.__doc__ = "执行深度搜索，返回研究报告。参数: query - 搜索查询词"
                            toolkit.register_tool_function(
                                tool_func=deep_research_wrapper,
                                func_name="deep_research",
                                func_description="执行深度搜索，返回研究报告。用于获取行业最佳实践、合规要求等信息。",
                            )
                            self.logger.info(f"Registered tool 'deep_research' to ReActAgent toolkit")
                        elif tool_name == "json_validator":
                            tool_inst = tool_instance
                            def json_validator_wrapper(json_str: str, tool_inst=tool_inst) -> ToolResponse:
                                """JSON 校验工具 - 验证JSON格式是否正确"""
                                ok, data, msg = tool_inst.validate(json_str)
                                result = json.dumps({"valid": ok, "data": data, "message": msg}, ensure_ascii=False)
                                return ToolResponse(content=[result])
                            json_validator_wrapper.__name__ = "json_validator"
                            json_validator_wrapper.__doc__ = "验证JSON格式是否正确"
                            toolkit.register_tool_function(
                                tool_func=json_validator_wrapper,
                                func_name="json_validator",
                                func_description="验证JSON格式是否正确，返回验证结果。",
                            )
                            self.logger.info(f"Registered tool 'json_validator' to ReActAgent toolkit")
                    except Exception as e:
                        self.logger.warning(f"Failed to register tool '{tool_name}' to toolkit: {e}")

            self.agent = ReActAgent(
                name=self.name,
                sys_prompt=self.system_prompt or self._get_default_system_prompt(),
                model=model,
                formatter=formatter,
                toolkit=toolkit,
                max_iters=int(self.react_config['max_rounds']),
                print_hint_msg=react_print_hint_msg,
            )
            
            self.logger.info(
                f"ReActAgent initialized (max_iters={self.react_config['max_rounds']}, print_hint_msg={react_print_hint_msg}, toolkit_tools={len(self.tools)}) for agent: {self.name}"
            )
            
        except Exception as e:
            self.agent = self.error_handler.handle(
                error=e,
                fallback_strategy=FallbackStrategy.SILENT,
                operation_name="ReActAgent initialization"
            )
    
    def _load_tools(self):
        """加载工具"""
        try:
            # 从配置中获取工具列表
            tools_config = self.config.get('tools', [])
            for tool_config in tools_config:
                tool_name = tool_config.get('name')
                if tool_name:
                    try:
                        tool = self.orchestrator.get_tool(tool_name)
                        self.tools[tool_name] = tool
                        self.logger.info(f"Loaded tool: {tool_name}")
                    except ValueError as e:
                        self.logger.warning(f"Tool not available: {tool_name}, {e}")
            
            # 注意：工具注册到 ReActAgent 已在 _init_react_agent() 中完成
            
        except Exception as e:
            self.logger.error(f"Failed to load tools: {e}")
    
    async def call_llm(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """调用大模型（使用 Model 接口）
        
        Args:
            prompt: 提示词
            context: 上下文信息
            
        Returns:
            大模型的回复
        """
        if not self.model:
            if self._is_mock_mode(context):
                self.logger.warning("Model not initialized, returning mock response")
                return self._get_mock_response(prompt)
            raise RuntimeError(
                f"[{self.name}] Model not initialized in real mode; 禁止返回占位或 mock 文本",
            )

        try:
            self.performance_tracker.record_llm_call(self.name)
            
            messages = []
            sys_prompt = self.system_prompt or self._get_default_system_prompt()
            if sys_prompt:
                messages.append({"role": "system", "content": sys_prompt})
            messages.append({"role": "user", "content": prompt})
            self.logger.info(
                f"[{self.name}] LLM request messages: {self._preview_text(json.dumps(messages, ensure_ascii=False))}",
            )

            result = await self.model(messages)

            # 兼容流式输出：result 可能是 AsyncGenerator[ChatResponse]
            if hasattr(result, "__aiter__"):
                last = None
                async for chunk in result:
                    last = chunk
                result = last

            if result is None:
                if self._is_mock_mode(context):
                    return self._get_mock_response(prompt)
                raise RuntimeError(f"[{self.name}] LLM returned empty response (None) in real mode")

            response = self._text_from_chat_response(result)
            if not response and self._is_mock_mode(context):
                response = self._get_mock_response(prompt)
            elif not response:
                raise RuntimeError(f"[{self.name}] LLM response has no extractable text in real mode")

            self.logger.info(f"LLM response received, length: {len(response)}")
            self.logger.info(f"[{self.name}] LLM response content: {self._preview_text(response)}")
            return response
            
        except Exception as e:
            error_msg = f"LLM call failed: {self._safe_error_text(e)}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    async def call_react_agent(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """调用 ReActAgent（支持多轮推理和工具调用）
        
        Args:
            prompt: 提示词
            context: 上下文信息
            
        Returns:
            ReActAgent 的回复
        """
        if not self.agent:
            self.logger.warning("ReActAgent not initialized, using Model instead")
            return await self.call_llm(prompt, context)
        
        audit_tokens = None
        try:
            od = (context or {}).get("output_dir")
            audit_tokens = push_deep_research_audit_context(self.name, str(od) if od else None)
        except Exception:
            audit_tokens = None

        try:
            self.logger.info(f"[{self.name}] ReAct input prompt: {self._preview_text(prompt)}")
            self._append_react_trace(context or {}, f"ReAct input: {self._preview_text(prompt)}")
            # 构建消息
            msg = Msg("user", prompt, "user")

            # 调用 ReActAgent（会自动进行多轮推理和工具调用）
            # 长耗时期间定时打印心跳与记忆快照，避免“无输出等待”。
            system_config = (getattr(self.orchestrator, "config", {}) or {}).get("system_config", {}) or {}
            logging_cfg = system_config.get("logging", {}) or {}
            interval = max(3, int(logging_cfg.get("react_progress_log_interval_sec", 10)))

            task = asyncio.create_task(self.agent(msg))
            started_at = time.monotonic()
            while True:
                try:
                    result = await asyncio.wait_for(task, timeout=interval)
                    break
                except asyncio.TimeoutError:
                    elapsed = int(time.monotonic() - started_at)
                    snapshot = await self._react_memory_snapshot()
                    self.logger.info(
                        f"[{self.name}] ReAct running (elapsed={elapsed}s): {snapshot}",
                    )
                    self._append_react_trace(
                        context or {},
                        f"ReAct running elapsed={elapsed}s | {snapshot}",
                    )
            
            # 提取回复内容
            response = result.get_text_content()
            self.logger.info(f"ReActAgent response received, length: {len(response)}")
            self.logger.info(f"[{self.name}] ReAct response content: {self._preview_text(response)}")
            self._append_react_trace(
                context or {},
                f"ReAct response: {self._preview_text(response)}",
            )

            msgs = await self._get_react_memory_messages()
            n_llm = self._estimate_react_llm_rounds(msgs)
            if n_llm == 0 and (response or "").strip():
                n_llm = 1
            if n_llm > 0:
                self.performance_tracker.record_llm_calls(self.name, n_llm)
            self._append_react_messages_jsonl(context or {}, msgs)
            try:
                serialized = [self._message_to_dict(m) for m in msgs]
                preview = json.dumps(serialized, ensure_ascii=False)
                self.logger.info("[{}] ReAct memory (json preview): {}", self.name, self._preview_text(preview))
            except Exception:
                pass
            
            return response
            
        except Exception as e:
            error_msg = f"ReActAgent call failed: {self._safe_error_text(e)}"
            self.logger.error(error_msg)
            self._append_react_trace(context or {}, f"ReAct error: {error_msg}")
            try:
                msgs = await self._get_react_memory_messages()
                self._append_react_messages_jsonl(context or {}, msgs)
            except Exception:
                pass
            raise RuntimeError(error_msg) from e
        finally:
            reset_deep_research_audit_context(audit_tokens)
    
    def _get_default_system_prompt(self) -> str:
        """获取默认系统提示词"""
        # 从配置文件中读取系统提示词
        if self.system_prompt:
            return self.system_prompt
        # 如果配置中没有，返回默认提示词
        return f"你是 {self.name}，一个专业的 AI 助手，负责解决特定领域的问题。"
    
    def _get_mock_response(self, prompt: str) -> str:
        """获取模拟响应（当 LLM 不可用时）"""
        return f"[Mock response for: {prompt[:50]}...]"
    
    async def close(self):
        """关闭资源"""
        self.logger.info(f"{self.name} closing")
