#!/usr/bin/env python3
"""Agent 基类 - 集成 AgentScope 大模型能力"""

from typing import Dict, Any, Optional
import time
import os
from pathlib import Path
from agentscope.model import OpenAIChatModel, DashScopeChatModel
from agentscope.agent import ReActAgent
from agentscope.message import Msg
from agentscope.formatter import OpenAIChatFormatter, DashScopeChatFormatter
from ..utils.logger import logger
from ..utils.error_handler import AgentErrorHandler, FallbackStrategy


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
            'enable_thinking': self.model_config.get('enable_thinking', True),  # 启用思考过程
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
                model_kwargs["client_kwargs"] = {"base_url": base_url}
            if temperature:
                model_kwargs["generate_kwargs"] = {"temperature": temperature}
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
            # 复用模型创建方法
            model = self._create_model()

            # AgentScope 版本兼容：当前 ReActAgent 需要 formatter/toolkit，而不是 tools/max_rounds/enable_thinking
            model_type = self.model_config.get('type', 'OpenAIChatModel')
            formatter = DashScopeChatFormatter() if model_type == "DashScopeChatModel" else OpenAIChatFormatter()

            # 暂不在此处注入 Toolkit（后续如需工具调用，再接入 Toolkit.register_tool_function）
            self.agent = ReActAgent(
                name=self.name,
                sys_prompt=self.system_prompt or self._get_default_system_prompt(),
                model=model,
                formatter=formatter,
                toolkit=None,
                max_iters=int(self.react_config['max_rounds']),
                print_hint_msg=False,
            )
            
            self.logger.info(
                f"ReActAgent initialized (max_iters={self.react_config['max_rounds']}) for agent: {self.name}"
            )
            
        except Exception as e:
            # 使用错误处理器，静默失败
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
            self.logger.warning("Model not initialized, returning mock response")
            return self._get_mock_response(prompt)
        
        try:
            # AgentScope ChatModel 接口：传入 OpenAI 风格 messages
            messages = []
            sys_prompt = self.system_prompt or self._get_default_system_prompt()
            if sys_prompt:
                messages.append({"role": "system", "content": sys_prompt})
            messages.append({"role": "user", "content": prompt})

            result = await self.model(messages)

            # 兼容流式输出：result 可能是 AsyncGenerator[ChatResponse]
            if hasattr(result, "__aiter__"):
                last = None
                async for chunk in result:
                    last = chunk
                result = last

            if result is None:
                return self._get_mock_response(prompt)

            # 提取回复文本（ChatResponse.content 是一组 message blocks）
            response_parts = []
            content_blocks = getattr(result, "content", None) or []
            for b in content_blocks:
                text = getattr(b, "text", None)
                if text:
                    response_parts.append(text)
            response = "".join(response_parts).strip()
            if not response:
                # 尝试 dict / 兜底
                if isinstance(result, dict) and "content" in result:
                    response = str(result.get("content", "")).strip()

            self.logger.info(f"LLM response received, length: {len(response)}")
            return response
            
        except Exception as e:
            error_msg = f"LLM call failed: {e}"
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
        
        try:
            # 构建消息
            msg = Msg("user", prompt, "user")
            
            # 调用 ReActAgent（会自动进行多轮推理和工具调用）
            # 注意：max_rounds 已在初始化时配置，这里会自动管理
            result = await self.agent(msg)
            
            # 提取回复内容
            response = result.get_text_content()
            self.logger.info(f"ReActAgent response received, length: {len(response)}")
            
            return response
            
        except Exception as e:
            error_msg = f"ReActAgent call failed: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
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
