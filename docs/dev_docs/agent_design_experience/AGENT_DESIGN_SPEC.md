# nanobot Agent 设计规范文档

> 本文档基于 nanobot v0.1.4.post4 源码分析，为开发者提供完整的 Agent 设计规范和架构参考。

## 📋 目录

- [1. 项目概述](#1-项目概述)
- [2. 核心架构](#2-核心架构)
- [3. Agent 核心模块](#3-agent-核心模块)
- [4. 工具系统](#4-工具系统)
- [5. 记忆系统](#5-记忆系统)
- [6. 技能系统](#6-技能系统)
- [7. 渠道系统](#7-渠道系统)
- [8. Provider 系统](#8-provider-系统)
- [9. 配置系统](#9-配置系统)
- [10. 最佳实践](#10-最佳实践)

---

## 1. 项目概述

### 1.1 定位与特点

**nanobot** 是一个超轻量级个人 AI 助手框架，具有以下特点：

- **超轻量**: 比 OpenClaw 少 99% 的代码量
- **模块化**: 清晰的模块划分，易于理解和扩展
- **多渠道**: 支持 Telegram、Discord、WhatsApp、飞书等 10+ 聊天平台
- **本地优先**: 支持 Ollama、vLLM 等本地 LLM 部署
- **研究友好**: 代码简洁易读，适合研究和二次开发

### 1.2 技术栈

- **语言**: Python 3.11+
- **核心依赖**:
  - `pydantic` - 配置和数据验证
  - `litellm` - LLM 提供商抽象
  - `loguru` - 日志系统
  - `typer` - CLI 接口
  - `websockets` / `websocket-client` - 长连接支持

### 1.3 项目结构

```
nanobot/
├── agent/              # Agent 核心逻辑
│   ├── tools/         # 工具实现
│   ├── context.py     # 上下文构建
│   ├── loop.py        # Agent 循环
│   ├── memory.py      # 记忆系统
│   └── skills.py      # 技能管理
├── bus/               # 消息总线
├── channels/          # 聊天渠道适配
├── config/            # 配置系统
├── providers/         # LLM 提供商
├── session/           # 会话管理
├── skills/            # 内置技能
└── templates/         # 模板文件
```

---

## 2. 核心架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────┐
│                    Chat Channels                        │
│  Telegram │ Discord │ WhatsApp │ Feishu │ DingTalk ... │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │    Message Bus (事件总线)  │
         └───────────────────────┘
                │           │
                │           │
                ▼           ▼
        ┌───────────┐   ┌──────────┐
        │ Inbound   │   │ Outbound │
        └─────┬─────┘   └────┬─────┘
              │              │
              └──────┬───────┘
                     │
                     ▼
         ┌───────────────────────┐
         │     Agent Loop        │◄───┐
         │  (核心处理引擎)         │    │
         └───────────────────────┘    │
                │                     │
                ├─────────────────────┤
                │                     │
                ▼                     ▼
       ┌────────────────┐   ┌────────────────┐
       │ Context Builder│   │ Tool Registry  │
       │ (上下文构建器)  │   │  (工具注册表)   │
       └────────────────┘   └────────────────┘
                │                     │
                ▼                     ▼
       ┌────────────────┐   ┌────────────────┐
       │ Memory Store   │   │ MCP Servers    │
       │ (记忆存储)      │   │ (外部工具)      │
       └────────────────┘   └────────────────┘
                │
                ▼
       ┌────────────────┐
       │ Skills Loader  │
       │ (技能加载器)    │
       └────────────────┘
```

### 2.2 消息流

1. **用户发送消息** → Channel 接收
2. **Channel** → 封装为 `InboundMessage` → 发布到 MessageBus
3. **AgentLoop** → 从 Bus 消费消息
4. **ContextBuilder** → 构建完整上下文（系统提示 + 历史 + 记忆 + 技能）
5. **LLM Provider** → 调用大模型 → 返回响应（可能包含工具调用）
6. **ToolRegistry** → 执行工具 → 返回结果
7. **多轮迭代** → 直到获得最终回复
8. **OutboundMessage** → 通过 Bus → Channel 发送给用户

### 2.3 核心设计模式

#### 2.3.1 策略模式 (Strategy Pattern)

- **Provider**: 不同 LLM 提供商的策略切换
- **Channel**: 不同聊天平台的策略适配
- **Tools**: 不同工具能力的策略实现

#### 2.3.2 观察者模式 (Observer Pattern)

- **MessageBus**: 事件发布/订阅机制
- **Progress Callback**: 实时进度推送

#### 2.3.3 责任链模式 (Chain of Responsibility)

- **工具验证链**: `cast_params` → `validate_params` → `execute`
- **消息处理链**: `build_system_prompt` → `build_messages` → `add_assistant_message`

---

## 3. Agent 核心模块

### 3.1 AgentLoop - 核心处理引擎

**职责**:
- 消息分发和处理
- 工具调用循环
- 任务管理（启动/停止/重启）
- MCP 连接管理

**核心方法**:

```python
class AgentLoop:
    async def run(self) -> None:
        """主循环：从总线消费消息并分发处理"""
        
    async def _process_message(self, msg: InboundMessage) -> OutboundMessage:
        """处理单条消息的完整流程"""
        
    async def _run_agent_loop(
        self, 
        initial_messages: list[dict],
        on_progress: Callable[..., Awaitable[None]] | None = None,
    ) -> tuple[str | None, list[str], list[dict]]:
        """
        运行多轮对话循环
        
        Returns:
            final_content: 最终回复内容
            tools_used: 使用的工具列表
            messages: 完整消息历史
        """
        
    async def _dispatch(self, msg: InboundMessage) -> None:
        """在锁保护下处理消息（防止并发冲突）"""
```

**关键特性**:

1. **最大迭代次数控制**: 防止无限工具调用循环（默认 40 次）
2. **错误恢复**: 工具执行失败时自动重试或回退
3. **进度流**: 支持实时输出思考和工具调用状态
4. **会话隔离**: 每个 session_key 独立处理
5. **任务取消**: 支持 `/stop` 命令中断正在执行的任务

### 3.2 ContextBuilder - 上下文构建器

**职责**: 组装 LLM 调用所需的完整上下文

**系统提示组成**:

```python
system_prompt = """
# Identity (身份)
- 运行时信息（OS、Python 版本、工作空间路径）
- 平台策略（Windows/POSIX 特定指令）
- Agent 行为准则

# Bootstrap Files (引导文件)
- AGENTS.md: Agent 指令
- SOUL.md: 人格和价值观
- USER.md: 用户偏好
- TOOLS.md: 工具使用说明

# Memory (记忆)
- 长期记忆 (MEMORY.md)
- 历史摘要 (HISTORY.md)

# Active Skills (激活技能)
- always=true 的技能

# Skills Summary (技能摘要)
- XML 格式的技能清单（含可用性状态）
"""
```

**运行时上下文注入**:

```python
runtime_context = """
[Runtime Context — metadata-only, not instructions]
Current Time: 2026-03-13 13:44 (Friday, CST)
Channel: telegram
Chat ID: 123456789
"""
```

**消息构建策略**:

1. **合并同角色消息**: 避免连续相同 role 导致某些 Provider 报错
2. **多媒体支持**: 自动将图片转为 base64 编码
3. **截断保护**: 过大的工具结果会被截断（16K 字符限制）

### 3.3 SubagentManager - 子代理管理器

**职责**: 管理动态生成的子代理（通过 `spawn` 工具）

**特性**:
- 独立的 Provider 和配置
- 共享消息总线
- 会话级联取消（父任务取消时自动取消所有子任务）
- 资源隔离和清理

---

## 4. 工具系统

### 4.1 工具基类设计

```python
class Tool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称（用于函数调用）"""
        
    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述（LLM 根据此决定何时调用）"""
        
    @property
    @abstractmethod
    def parameters(self) -> dict[str, Any]:
        """JSON Schema 参数定义"""
        
    @abstractmethod
    async def execute(self, **kwargs: Any) -> str:
        """执行工具并返回字符串结果"""
    
    def cast_params(self, params: dict[str, Any]) -> dict[str, Any]:
        """类型转换：根据 JSON Schema 自动转换参数类型"""
        
    def validate_params(self, params: dict[str, Any]) -> list[str]:
        """参数验证：返回错误列表（空表示验证通过）"""
        
    def to_schema(self) -> dict[str, Any]:
        """转换为 OpenAI function calling 格式"""
```

### 4.2 参数验证流程

```
LLM 返回 tool_call
    ↓
ToolRegistry.execute()
    ↓
tool.cast_params(params)      # 类型转换
    ↓
tool.validate_params(params)  # 验证
    ↓
如果验证失败 → 返回错误信息（带改进提示）
如果验证通过 → tool.execute(**params)
    ↓
捕获异常 → 返回格式化错误信息
```

### 4.3 内置工具分类

#### 4.3.1 文件系统工具

| 工具名 | 功能 | 安全策略 |
|--------|------|----------|
| `read_file` | 读取文件内容 | 可限制在工作空间内 |
| `write_file` | 写入/创建文件 | 可限制在工作空间内 |
| `edit_file` | 精确编辑文件（行级） | 可限制在工作空间内 |
| `list_dir` | 列出目录内容 | 可限制在工作空间内 |

#### 4.3.2 系统工具

| 工具名 | 功能 | 配置项 |
|--------|------|--------|
| `exec` | 执行 shell 命令 | timeout, path_append, restrict_to_workspace |
| `message` | 发送消息到指定渠道 | 自动设置 channel/chat_id 上下文 |
| `spawn` | 创建子代理 | 继承父代理大部分配置 |
| `cron` | 管理定时任务 | 集成 CronService |

#### 4.3.3 Web 工具

| 工具名 | 功能 | 依赖 |
|--------|------|------|
| `web_search` | 搜索互联网 | Brave API Key |
| `web_fetch` | 抓取网页内容 | readability-lxml |

#### 4.3.4 MCP 工具

- **动态注册**: 从 MCP 服务器自动发现工具
- **双传输模式**: stdio（本地进程）和 HTTP/SSE（远程端点）
- **超时控制**: 每个工具独立配置 timeout

### 4.4 自定义工具开发指南

**步骤 1: 继承 Tool 基类**

```python
from nanobot.agent.tools.base import Tool

class MyCustomTool(Tool):
    @property
    def name(self) -> str:
        return "my_custom_tool"
    
    @property
    def description(self) -> str:
        return "这是一个自定义工具，用于..."
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "参数 1 的描述",
                },
                "count": {
                    "type": "integer",
                    "description": "数量",
                    "minimum": 1,
                    "maximum": 100,
                },
            },
            "required": ["param1"],
        }
    
    async def execute(self, param1: str, count: int = 10) -> str:
        # 实现工具逻辑
        result = await self._do_something(param1, count)
        return f"执行成功：{result}"
```

**步骤 2: 注册到工具注册表**

```python
# 在 AgentLoop 初始化时
self.tools.register(MyCustomTool())
```

**步骤 3: 测试工具**

```python
# 单元测试示例
async def test_my_custom_tool():
    tool = MyCustomTool()
    
    # 测试参数验证
    errors = tool.validate_params({"param1": "test"})
    assert len(errors) == 0
    
    # 测试执行
    result = await tool.execute(param1="test", count=5)
    assert "执行成功" in result
```

---

## 5. 记忆系统

### 5.1 双层记忆架构

```
┌─────────────────────────────────────┐
│         MEMORY.md (长期记忆)         │
│ - 持久化事实                         │
│ - 用户偏好                            │
│ - 重要决策记录                       │
│ - 由 LLM 智能提炼                      │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│         HISTORY.md (历史记录)        │
│ - 时间戳索引                         │
│ - grep 可搜索                        │
│ - 详细事件日志                       │
│ - 支持原始归档（fallback）             │
└─────────────────────────────────────┘
```

### 5.2 记忆巩固 (Consolidation) 流程

```python
# 触发条件
1. 会话 token 数超过阈值（context_window_tokens / 2）
2. 用户主动触发 /new 命令
3. 每轮对话结束后异步检查

# 巩固流程
Session Messages → MemoryConsolidator
    ↓
选择需要归档的消息块（基于 token 边界）
    ↓
调用 LLM + save_memory 工具
    ↓
LLM 返回:
{
    "history_entry": "[2026-03-13 13:44] 讨论了项目架构...",
    "memory_update": "# 更新后的长期记忆内容..."
}
    ↓
写入 HISTORY.md（追加）
更新 MEMORY.md（覆盖）
更新 session.last_consolidated 指针
```

### 5.3 记忆工具定义

```python
_SAVE_MEMORY_TOOL = [{
    "type": "function",
    "function": {
        "name": "save_memory",
        "description": "Save the memory consolidation result to persistent storage.",
        "parameters": {
            "type": "object",
            "properties": {
                "history_entry": {
                    "type": "string",
                    "description": "A paragraph summarizing key events/decisions/topics. "
                                   "Start with [YYYY-MM-DD HH:MM]. Include detail useful for grep search.",
                },
                "memory_update": {
                    "type": "string",
                    "description": "Full updated long-term memory as markdown. Include all existing "
                                   "facts plus new ones. Return unchanged if nothing new.",
                },
            },
            "required": ["history_entry", "memory_update"],
        },
    },
}]
```

### 5.4 容错机制

**连续失败处理**:
- 计数器：`_consecutive_failures`
- 阈值：3 次失败后触发降级
- 降级策略：直接归档原始消息（不经过 LLM 总结）

```python
def _fail_or_raw_archive(self, messages: list[dict]) -> bool:
    """失败计数达到阈值后，直接归档原始消息"""
    self._consecutive_failures += 1
    if self._consecutive_failures < self._MAX_FAILURES_BEFORE_RAW_ARCHIVE:
        return False  # 继续重试
    self._raw_archive(messages)  # 降级为原始归档
    self._consecutive_failures = 0
    return True
```

### 5.5 Token 估算策略

**链式估算**（提高准确性）:
```python
def estimate_prompt_tokens_chain(
    provider, model, messages, tools
) -> tuple[int, str]:
    """
    实际调用 Provider API 进行 token 估算
    
    Returns:
        (token_count, source_description)
    """
```

**保守边界选择**:
- 只在 user 消息处切分（保证对话完整性）
- 向下取整确保不会超出目标 token 数

---

## 6. 技能系统

### 6.1 技能文件格式

```markdown
---
description: "技能的简短描述"
always: false  # 是否始终激活
requires:
  bins: ["git", "docker"]  # 需要的命令行工具
  env: ["GITHUB_TOKEN"]    # 需要的环境变量
---

# Skill: skill-name

这里是技能的详细说明...

## Usage

如何使用此技能...

## Examples

示例...
```

### 6.2 技能元数据解析

```python
def _parse_nanobot_metadata(self, raw: str) -> dict:
    """解析 frontmatter 中的 JSON 元数据"""
    data = json.loads(raw)
    # 支持 nanobot 和 openclaw 两种 key
    return data.get("nanobot", data.get("openclaw", {}))
```

### 6.3 技能加载优先级

```
Workspace Skills (最高优先级)
    ↓
Built-in Skills (内置技能)
    ↓
过滤不可用技能（检查 requires）
    ↓
生成 XML 摘要（供 Agent 查阅）
```

### 6.4 技能可用性检查

```python
def _check_requirements(self, skill_meta: dict) -> bool:
    """检查技能依赖是否满足"""
    requires = skill_meta.get("requires", {})
    
    # 检查二进制文件
    for b in requires.get("bins", []):
        if not shutil.which(b):
            return False
    
    # 检查环境变量
    for env in requires.get("env", []):
        if not os.environ.get(env):
            return False
    
    return True
```

### 6.5 技能使用流程

**Agent 视角**:
1. 读取系统提示中的 `<skills>` XML 摘要
2. 根据需要调用 `read_file` 读取具体技能的 SKILL.md
3. 按照技能说明执行操作

**开发者视角**:
1. 创建技能目录：`workspace/skills/my-skill/`
2. 编写 SKILL.md 文件（包含 frontmatter）
3. Agent 自动发现并可用

---

## 7. 渠道系统

### 7.1 渠道基类设计

```python
class BaseChannel(ABC):
    name: str = "base"  # 渠道标识符
    display_name: str = "Base"  # 显示名称
    
    def __init__(self, config: Any, bus: MessageBus):
        self.config = config  # Pydantic 配置对象
        self.bus = bus        # 消息总线
        self._running = False
    
    @abstractmethod
    async def start(self) -> None:
        """启动渠道（长连接或轮询）"""
        
    @abstractmethod
    async def stop(self) -> None:
        """停止渠道并清理资源"""
        
    @abstractmethod
    async def send(self, msg: OutboundMessage) -> None:
        """发送消息到渠道"""
    
    def is_allowed(self, sender_id: str) -> bool:
        """检查发送者是否在允许列表中"""
        
    async def _handle_message(
        self,
        sender_id: str,
        chat_id: str,
        content: str,
        media: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        session_key: str | None = None,
    ) -> None:
        """处理入站消息（权限检查 + 发布到总线）"""
```

### 7.2 渠道分类

#### 7.2.1 WebSocket 长连接

- **Telegram**: bot API + python-telegram-bot
- **Discord**: Gateway API + websocket
- **Feishu**: WebSocket 长连接（无需公网 IP）
- **QQ**: botpy SDK + WebSocket
- **DingTalk**: Stream Mode
- **Slack**: Socket Mode
- **Wecom**: WebSocket 长连接

#### 7.2.2 客户端直连

- **WhatsApp**: 本地 bridge 服务（Node.js + whatsapp-web.js）
- **Matrix**: matrix-nio SDK + E2EE 支持

#### 7.2.3 轮询模式

- **Email**: IMAP 轮询 + SMTP 发送

### 7.3 通用访问控制

```python
def is_allowed(self, sender_id: str) -> bool:
    allow_list = getattr(self.config, "allow_from", [])
    
    if not allow_list:
        logger.warning("{}: allow_from is empty — all access denied")
        return False
    
    if "*" in allow_list:
        return True  # 允许所有人
    
    return str(sender_id) in allow_list  # 白名单检查
```

### 7.4 群组策略

```python
# 常见的群组行为配置
group_policy: Literal["mention", "open", "allowlist"]

- "mention": 仅在@提及时响应
- "open": 响应所有群消息
- "allowlist": 仅响应指定群组
```

### 7.5 自定义渠道开发步骤

**步骤 1: 定义配置 Schema**

```python
from pydantic import BaseModel

class MyChannelConfig(BaseModel):
    enabled: bool = False
    token: str = ""
    allow_from: list[str] = []
    # 其他渠道特定配置...
```

**步骤 2: 实现渠道类**

```python
from nanobot.channels.base import BaseChannel

class MyChannel(BaseChannel):
    name = "mychannel"
    display_name = "My Channel"
    
    def __init__(self, config: MyChannelConfig, bus: MessageBus):
        super().__init__(config, bus)
    
    async def start(self) -> None:
        self._running = True
        # 实现连接和消息监听逻辑
        while self._running:
            message = await self._receive_message()
            await self._handle_message(
                sender_id=message.from_user,
                chat_id=message.chat_id,
                content=message.text,
            )
    
    async def stop(self) -> None:
        self._running = False
        # 清理连接资源
    
    async def send(self, msg: OutboundMessage) -> None:
        # 实现消息发送逻辑
        await self._api_send(
            chat_id=msg.chat_id,
            text=msg.content,
        )
```

**步骤 3: 注册到渠道管理器**

```python
# nanobot/channels/manager.py
from .mychannel import MyChannel, MyChannelConfig

CHANNEL_REGISTRY["mychannel"] = {
    "config_class": MyChannelConfig,
    "channel_class": MyChannel,
}
```

**步骤 4: 添加到配置 Schema**

```python
# nanobot/config/schema.py
class ChannelsConfig(Base):
    # ... 现有字段
    mychannel: MyChannelConfig = Field(default_factory=MyChannelConfig)
```

---

## 8. Provider 系统

### 8.1 Provider 基类设计

```python
class LLMProvider(ABC):
    def __init__(self, api_key: str | None = None, api_base: str | None = None):
        self.api_key = api_key
        self.api_base = api_base
        self.generation: GenerationSettings = GenerationSettings(
            temperature=0.7,
            max_tokens=4096,
            reasoning_effort=None,
        )
    
    @staticmethod
    def _sanitize_empty_content(messages: list[dict]) -> list[dict]:
        """替换空内容以避免 Provider 400 错误"""
        
    @staticmethod
    def _sanitize_request_messages(
        messages: list[dict],
        allowed_keys: frozenset[str],
    ) -> list[dict]:
        """过滤掉 Provider 不支持的消息字段"""
    
    @abstractmethod
    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        reasoning_effort: str | None = None,
        tool_choice: str | dict | None = None,
    ) -> LLMResponse:
        """发送聊天请求"""
        
    async def chat_with_retry(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        model: str | None = None,
        # ... 其他参数
    ) -> LLMResponse:
        """带重试机制的聊天方法"""
```

### 8.2 Provider 注册表

**核心设计**: 通过声明式配置自动匹配 Provider

```python
# nanobot/providers/registry.py
PROVIDERS = [
    ProviderSpec(
        name="openrouter",
        keywords=("openrouter",),
        env_key="OPENROUTER_API_KEY",
        display_name="OpenRouter",
        litellm_prefix="openrouter",
        skip_prefixes=("openrouter/",),
        is_gateway=True,
    ),
    ProviderSpec(
        name="ollama",
        keywords=("ollama",),
        env_key=None,
        display_name="Ollama",
        litellm_prefix="ollama",
        is_local=True,
        default_api_base="http://localhost:11434",
        detect_by_base_keyword="11434",
    ),
    # ... 更多 Provider
]
```

### 8.3 Provider 自动匹配逻辑

```python
def _match_provider(self, model: str | None = None):
    """
    匹配 Provider 的优先级顺序:
    
    1. 强制指定 provider (agents.defaults.provider != "auto")
    2. 按 model 前缀精确匹配（如 "github-copilot/..."）
    3. 按关键词匹配（model 名称包含 provider 关键词）
    4. 本地 Provider fallback（Ollama/vLLM）
    5. 网关 Provider（有 API Key 的第一个）
    """
```

### 8.4 LiteLLM 集成

**环境变量自动设置**:
```python
def _setup_env(self) -> None:
    """为 LiteLLM 设置必要的环境变量"""
    if self.spec.env_key and self.api_key:
        os.environ[self.spec.env_key] = self.api_key
    
    # 设置额外环境变量
    for env_var, value in self.spec.env_extras:
        os.environ[env_var] = value.format(api_key=self.api_key)
```

**模型名称自动前缀**:
```python
def _normalize_model_name(self, model: str) -> str:
    """自动添加 Provider 前缀"""
    if any(model.startswith(prefix) for prefix in self.spec.skip_prefixes):
        return model  # 已有前缀，跳过
    
    return f"{self.spec.litellm_prefix}/{model}"
```

### 8.5 特殊 Provider 支持

#### 8.5.1 OAuth Provider

- **OpenAI Codex**: ChatGPT Plus/Pro 账户 OAuth
- **GitHub Copilot**: GitHub 账户 OAuth

**特点**:
- 无需 API Key，使用 OAuth token
- 需要交互式登录 (`nanobot provider login`)
- Token 自动刷新和持久化

#### 8.5.2 本地 Provider

- **Ollama**: `http://localhost:11434`
- **vLLM**: `http://localhost:8000/v1`

**特点**:
- 无需 API Key
- 自动检测 base URL 关键词
- 支持自定义模型名称

### 8.6 新增 Provider 开发指南

**两步添加法**:

**Step 1: 添加到 Provider Registry**

```python
# nanobot/providers/registry.py
ProviderSpec(
    name="myprovider",
    keywords=("myprovider", "mymodel"),  # 用于自动匹配的关键词
    env_key="MYPROVIDER_API_KEY",        # 环境变量名
    display_name="My Provider",          # 显示名称
    litellm_prefix="myprovider",         # LiteLLM 前缀
    skip_prefixes=("myprovider/",),      # 避免重复前缀
    default_api_base="https://api.myprovider.com/v1",
    is_gateway=False,
    is_local=False,
    is_oauth=False,
)
```

**Step 2: 添加到配置 Schema**

```python
# nanobot/config/schema.py
class ProvidersConfig(Base):
    # ... 现有字段
    myprovider: ProviderConfig = Field(default_factory=ProviderConfig)
```

**完成!** 环境配置、模型前缀、状态显示全部自动生效。

### 8.7 Provider 高级选项

```python
ProviderSpec(
    # ... 基础字段
    
    # 额外环境变量
    env_extras=(("ZHIPUAI_API_KEY", "{api_key}"),),
    
    # 按模型覆盖参数
    model_overrides=(
        ("kimi-k2.5", {"temperature": 1.0}),
    ),
    
    # API Key 前缀检测
    detect_by_key_prefix="sk-or-",
    
    # Base URL 关键词检测
    detect_by_base_keyword="openrouter",
    
    # 剥离已存在的前缀
    strip_model_prefix=True,
)
```

---

## 9. 配置系统

### 9.1 配置层次结构

```yaml
Config (根配置)
├── agents (Agent 配置)
│   └── defaults (默认值)
│       ├── workspace
│       ├── model
│       ├── provider
│       ├── max_tokens
│       └── ...
├── channels (渠道配置)
│   ├── telegram
│   ├── discord
│   ├── whatsapp
│   └── ...
├── providers (Provider 配置)
│   ├── openrouter
│   ├── anthropic
│   ├── ollama
│   └── ...
├── gateway (网关配置)
│   ├── host
│   ├── port
│   └── heartbeat
└── tools (工具配置)
    ├── web
    ├── exec
    ├── restrict_to_workspace
    └── mcp_servers
```

### 9.2 Pydantic 配置特性

**驼峰命名自动转换**:
```python
class Base(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,      # 自动生成 camelCase 别名
        populate_by_name=True,         # snake_case 和 camelCase 都接受
    )
```

**环境变量支持**:
```python
class Config(BaseSettings):
    model_config = ConfigDict(
        env_prefix="NANOBOT_",              # 环境变量前缀
        env_nested_delimiter="__",          # 嵌套配置分隔符
    )

# 使用示例:
# NANOBOT_AGENTS__DEFAULTS__MODEL=claude-opus-4-5
```

### 9.3 配置验证和默认值

```python
class AgentDefaults(Base):
    workspace: str = "~/.nanobot/workspace"
    model: str = "anthropic/claude-opus-4-5"
    provider: str = "auto"  # 自动检测
    max_tokens: int = 8192
    context_window_tokens: int = 65_536
    temperature: float = 0.1
    max_tool_iterations: int = 40
```

### 9.4 配置合并策略

**配置文件位置**: `~/.nanobot/config.json`

**合并规则**:
1. 读取配置文件
2. 应用环境变量覆盖
3. 使用 Pydantic 验证和类型转换
4. 未指定的字段使用默认值

### 9.5 配置示例

```json
{
  "providers": {
    "openrouter": {
      "apiKey": "sk-or-v1-xxx"
    },
    "ollama": {
      "apiBase": "http://localhost:11434"
    }
  },
  "agents": {
    "defaults": {
      "model": "anthropic/claude-opus-4-5",
      "provider": "openrouter",
      "temperature": 0.7
    }
  },
  "channels": {
    "telegram": {
      "enabled": true,
      "token": "YOUR_BOT_TOKEN",
      "allowFrom": ["123456789"],
      "groupPolicy": "mention"
    }
  },
  "tools": {
    "restrictToWorkspace": false,
    "mcpServers": {
      "filesystem": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"]
      }
    }
  }
}
```

---

## 10. 最佳实践

### 10.1 Agent 开发最佳实践

#### 10.1.1 系统设计原则

✅ **推荐**:
- **单一职责**: 每个模块专注于一个职责
- **依赖注入**: 通过构造函数传递依赖（如 Bus、Provider）
- **异步优先**: 所有 I/O 操作使用 async/await
- **错误隔离**: 使用 Lock 防止并发冲突

❌ **避免**:
- 全局状态（使用 Session 管理状态）
- 阻塞操作（会卡住整个事件循环）
- 过度耦合（模块间通过接口通信）

#### 10.1.2 工具设计原则

✅ **推荐**:
- **明确的描述**: LLM 根据 description 决定是否调用
- **严格的验证**: 使用 JSON Schema 验证参数
- **友好的错误**: 返回可操作的错误信息
- **幂等性**: 工具可以安全重试

❌ **避免**:
- 副作用（修改全局状态）
- 长时间阻塞（使用异步操作）
- 模糊的错误（"出错了" vs "文件不存在：/path/to/file"）

#### 10.1.3 记忆管理原则

✅ **推荐**:
- **及时巩固**: 定期归档旧对话以节省 token
- **分层存储**: MEMORY.md（事实）+ HISTORY.md（日志）
- **降级策略**: LLM 失败时自动切换到原始归档

❌ **避免**:
- 过度总结（丢失关键细节）
- 忽略失败（连续失败后应降级）
- 同步阻塞（使用异步巩固）

### 10.2 性能优化建议

#### 10.2.1 Token 优化

```python
# 1. 合理设置 context_window_tokens
# 建议设为模型上限的 50-70%
context_window_tokens = 65536  # Claude 200K 的 1/3

# 2. 定期巩固记忆
# 当 prompt tokens > context_window_tokens / 2 时触发
target = self.context_window_tokens // 2

# 3. 截断大工具结果
_TOOl_RESULT_MAX_CHARS = 16000
```

#### 10.2.2 并发控制

```python
# 1. 使用 Lock 保护共享状态
async with self._processing_lock:
    response = await self._process_message(msg)

# 2. 任务级联取消
task.add_done_callback(
    lambda t, k=msg.session_key: 
        self._active_tasks[k].remove(t)
)

# 3. 后台任务异步执行
asyncio.create_task(_do_restart())
```

#### 10.2.3 连接管理

```python
# 1. Lazy 连接（首次使用时建立）
async def _connect_mcp(self) -> None:
    if self._mcp_connected or self._mcp_connecting:
        return
    # 建立连接...

# 2. 优雅关闭
async def close_mcp(self) -> None:
    if self._mcp_stack:
        await self._mcp_stack.aclose()
```

### 10.3 调试技巧

#### 10.3.1 日志级别

```python
from loguru import logger

# 开发时开启详细日志
logger.add("nanobot_{time}.log", level="DEBUG")

# 关键节点打点
logger.info("Processing message from {}:{}: {}", 
            msg.channel, msg.sender_id, preview)
logger.error("Tool execution failed: {}", error)
```

#### 10.3.2 会话检查

```bash
# 查看当前会话历史
cat ~/.nanobot/workspace/memory/HISTORY.md | tail -100

# 查看记忆状态
cat ~/.nanobot/workspace/memory/MEMORY.md

# 查看会话 JSON
cat ~/.nanobot/workspace/sessions/*.json | jq .
```

#### 10.3.3 Provider 调试

```python
# 启用 LiteLLM 详细日志
import litellm
litellm.set_verbose = True

# 查看 token 使用
response.usage  # {"prompt_tokens": 100, "completion_tokens": 50}
```

### 10.4 测试策略

#### 10.4.1 单元测试

```python
import pytest
from nanobot.agent.tools.filesystem import ReadFileTool

@pytest.mark.asyncio
async def test_read_file(tmp_path):
    # 创建测试文件
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!")
    
    # 测试工具
    tool = ReadFileTool(workspace=tmp_path)
    result = await tool.execute(path="test.txt")
    
    assert "Hello, World!" in result
```

#### 10.4.2 集成测试

```python
@pytest.mark.asyncio
async def test_agent_loop():
    # 创建测试环境
    bus = MessageBus()
    provider = TestProvider()  # Mock Provider
    workspace = tempfile.mkdtemp()
    
    # 创建 AgentLoop
    loop = AgentLoop(bus, provider, Path(workspace))
    
    # 发送测试消息
    await bus.publish_inbound(InboundMessage(
        channel="cli",
        sender_id="user",
        chat_id="test",
        content="Hello!",
    ))
    
    # 验证响应
    response = await asyncio.wait_for(
        bus.consume_outbound(),
        timeout=5.0
    )
    assert response is not None
```

### 10.5 安全建议

#### 10.5.1 访问控制

```json
{
  "channels": {
    "telegram": {
      "allowFrom": ["YOUR_USER_ID"]  // 永远不要留空或使用 "*" 在生产环境
    }
  }
}
```

#### 10.5.2 工具限制

```json
{
  "tools": {
    "restrictToWorkspace": true,  // 限制文件访问范围
    "exec": {
      "timeout": 60,              // 设置执行超时
      "pathAppend": ""            // 谨慎添加 PATH
    }
  }
}
```

#### 10.5.3 密钥管理

```bash
# 使用环境变量而非配置文件
export NANOBOT_PROVIDERS__OPENROUTER__API_KEY="sk-or-xxx"

# 配置文件加入 .gitignore
echo "~/.nanobot/config.json" >> .gitignore
```

### 10.6 扩展开发路线图

#### 10.6.1 短期扩展（1-2 天）

- ✅ 添加新的工具
- ✅ 创建自定义技能
- ✅ 调整系统提示和人格
- ✅ 配置新的 Provider

#### 10.6.2 中期扩展（1-2 周）

- ✅ 实现新的聊天渠道
- ✅ 集成 MCP 服务器
- ✅ 定制记忆巩固策略
- ✅ 添加监控和指标

#### 10.6.3 长期扩展（1-2 月）

- ⚠️ 修改 Agent 核心循环
- ⚠️ 实现自定义 Provider（非 LiteLLM）
- ⚠️ 重构消息总线
- ⚠️ 添加数据库支持

---

## 附录

### A. 关键文件和目录

| 文件/目录 | 作用 | 修改频率 |
|-----------|------|----------|
| `~/.nanobot/config.json` | 主配置文件 | 高 |
| `~/.nanobot/workspace/` | 工作空间 | 中 |
| `nanobot/agent/loop.py` | Agent 核心 | 低 |
| `nanobot/agent/tools/` | 工具实现 | 中 |
| `nanobot/channels/` | 渠道适配 | 低 |
| `nanobot/providers/` | Provider 适配 | 低 |

### B. 常用 CLI 命令

```bash
# 初始化
nanobot onboard

# 启动网关（监听消息）
nanobot gateway

# CLI 直接交互
nanobot agent -m "Hello!"

# 查看状态
nanobot status

# Provider OAuth 登录
nanobot provider login openai-codex

# 渠道登录（WhatsApp QR）
nanobot channels login
```

### C. 故障排查清单

**问题 1: Agent 不响应**
- [ ] 检查 `allowFrom` 配置
- [ ] 查看日志是否有错误
- [ ] 验证 Provider API Key 有效
- [ ] 确认会话未被锁定

**问题 2: 工具调用失败**
- [ ] 检查工具参数 JSON Schema
- [ ] 验证工具依赖（bin/env）
- [ ] 查看工具执行日志
- [ ] 确认工作空间权限

**问题 3: 记忆不巩固**
- [ ] 检查 token 阈值设置
- [ ] 验证 LLM 是否支持 tool_choice
- [ ] 查看失败计数器
- [ ] 确认 MEMORY.md 可写

### D. 参考资源

- **官方文档**: https://github.com/HKUDS/nanobot
- **PyPI**: https://pypi.org/project/nanobot-ai/
- **Discord 社区**: https://discord.gg/MnCvHqpUGB
- **Issue Tracker**: https://github.com/HKUDS/nanobot/issues

---

## 总结

nanobot 是一个设计精良的轻量级 AI 助手框架，其核心优势在于：

1. **清晰的架构**: 模块职责明确，易于理解和扩展
2. **强大的抽象**: Provider/Channel/Tools 的统一接口设计
3. **灵活的配置**: Pydantic 带来的类型安全和灵活性
4. **生产就绪**: 完善的错误处理、重试、降级机制
5. **生态丰富**: 10+ 渠道、20+ Provider、MCP 支持

遵循本规范文档中的设计原则和最佳实践，您可以：
- 快速开发自定义工具和技能
- 轻松集成新的聊天渠道
- 灵活选择和切换 LLM Provider
- 构建稳定可靠的个人 AI 助手

祝您开发愉快！🐈
