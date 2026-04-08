# Parlant Agent 配置挖掘系统 - 软件架构设计文档

**版本**: v1.0  
**创建日期**: 2026-03-14  
**状态**: 设计中  

---

## 目录

- [1. 文档概述](#1-文档概述)
- [2. 系统架构总览](#2-系统架构总览)
- [3. 技术栈选型](#3-技术栈选型)
- [4. 系统分层设计](#4-系统分层设计)
- [5. 核心模块设计](#5-核心模块设计)
- [6. 数据流与处理逻辑](#6-数据流与处理逻辑)
- [7. 并发与异步设计](#7-并发与异步设计)
- [8. 配置系统设计](#8-配置系统设计)
- [9. 异常处理与日志](#9-异常处理与日志)
- [10. 测试策略](#10-测试策略)
- [11. 部署与运行](#11-部署与运行)

---

## 1. 文档概述

### 1.1 文档目的

本文档描述 Parlant Agent 配置挖掘系统的软件架构设计，包括:
- 系统整体架构和技术选型
- 核心模块的职责和交互逻辑
- 关键设计决策和技术约束
- 可扩展性和维护性考虑

### 1.2 设计原则

基于用户需求，本系统遵循以下核心设计原则:

| 原则 | 说明 | 实现方式 |
|------|------|---------|
| **非 Langchain** | 不使用 Langchain 框架 | 直接使用 OpenAI SDK + 自定义抽象层 |
| **OpenAI 接口优先** | 仅开发 OpenAI 兼容接口 | 统一使用 OpenAI API 标准，支持多模型故障切换 |
| **配置分离** | 配置文件与代码分离 | YAML 配置文件 + 环境变量双重支持 |
| **异步并发** | 必要的地方采用异步 | asyncio + aiohttp，无并发需求处不用异步 |
| **可调试性** | 便于断点调试 | 独立 main.py 入口，支持 debug 模式，支持阶段控制 |
| **步骤可拆分** | 中间结果保存 | 每个步骤输出中间文件，支持从任意步骤重启 |
| **LLM 输出校验** | Hook 机制校验 JSON | Pydantic 校验 + LLM 修正循环 |
| **生产级日志** | 使用 logrus | Python logging 结构化日志 |

### 1.3 术语定义

| 术语 | 定义 |
|------|------|
| **Agent** | 具有特定职责的智能体，如 Coordinator、DomainExpert |
| **Sprint** | 项目开发阶段，共 6 个 Sprint 完成全流程 |
| **Review Board** | 评审团机制，用于关键决策的集体评审 |
| **Deep Research** | 互联网搜索工具，用于公域知识收集 |
| **Journey** | Parlant 中的对话流程状态机配置 |

---

## 2. 系统架构总览

### 2.1 架构分层图

```
┌─────────────────────────────────────────────────────────┐
│                    应用层 (Application Layer)            │
│  ┌─────────────────────────────────────────────────┐   │
│  │              main.py (主入口)                     │   │
│  │  - Debug 模式切换                                 │   │
│  │  - 配置加载                                       │   │
│  │  - 步骤编排                                       │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                  协调层 (Coordination Layer)             │
│  ┌─────────────────────────────────────────────────┐   │
│  │           Workflow Orchestrator                  │   │
│  │  - Sprint 流程控制                                │   │
│  │  - Agent 间协调                                   │   │
│  │  - 检查点管理                                     │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                   Agent 层 (Agent Layer)                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │Coordinator│ │Requirement│ │Domain   │ │Data     │  │
│  │          │ │Analyst   │ │Expert   │ │Analyst  │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │Process   │ │Rule      │ │Tool     │ │Journey   │  │
│  │Designer  │ │Engineer  │ │Architect│ │Builder   │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐               │
│  │Config    │ │Customer  │ │QA        │               │
│  │Assembler │ │Advocate  │ │Moderator │               │
│  └──────────┘ └──────────┘ └──────────┘               │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                 服务层 (Service Layer)                   │
│  ┌──────────────┐  ┌──────────────┐                     │
│  │LLM Service   │  │Embedding     │                     │
│  │- OpenAI API  │  │Service       │                     │
│  │- 多模型切换  │  │- 语义向量    │                     │
│  │- RMP 限流    │  │- 相似度计算  │                     │
│  └──────────────┘  └──────────────┘                     │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                  工具层 (Tool Layer)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │File Tool     │  │Search Tool   │  │Code Executor │  │
│  │- 读写文件    │  │- Deep Research│ │- Python 执行  │  │
│  │- 目录管理    │  │- 批量查询    │  │- 沙箱隔离    │  │
│  │- 中间文件保存│  │- 结果去重    │  │- 依赖管理    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │Git Tool      │  │JSON Validator│  │Skill Package │  │
│  │- 版本控制    │  │- Schema 校验  │  │- 技能加载   │  │
│  │- 变更追踪    │  │- LLM 修正     │  │- 动态注册   │  │
│  │- 协作管理    │  │- 格式转换    │  │- 热插拔     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 2.2 核心组件关系

```
main.py
  ↓
Workflow Orchestrator
  ↓
┌──────────────────────────────────────────┐
│ Sprint 0: 需求分析                        │
│ ├─ Coordinator 主持                       │
│ ├─ RequirementAnalyst 记录                │
│ ├─ DomainExpert 提供行业视角              │
│ └─ CustomerAdvocate 代表用户              │
└──────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────┐
│ Sprint 1: 知识挖掘                        │
│ ├─ DomainExpert: 公域知识 (Deep Research) │
│ ├─ DataAnalyst: 私域知识 (对话分析)       │
│ └─ UserPortraitMiner: 用户画像挖掘 (新增) │
└──────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────┐
│ Sprint 2: 流程设计                        │
│ └─ ProcessDesigner + CustomerAdvocate     │
└──────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────┐
│ Sprint 3: 规则挖掘                        │
│ └─ RuleEngineer + 语义去重                │
└──────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────┐
│ Sprint 4: 工具与旅程构建                  │
│ ├─ ToolArchitect (并行)                  │
│ ├─ JourneyBuilder (并行)                  │
│ └─ ConfigAssembler(整合用户画像配置)      │
└──────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────┐
│ Sprint 5: 集成质检                        │
│ ├─ ConfigAssembler                        │
│ └─ QAModerator (评审团主席)               │
└──────────────────────────────────────────┘
```

**新增说明**: 
- **UserPortraitMiner**: 负责从对话数据中挖掘典型用户画像，包括：
  - 用户特征提取（Tags、Behaviors、Metadata）
  - 增量式特征聚合（维护全局 feature_stats）
  - 用户分群聚类（DBSCAN/K-Means 算法）
  - 典型用户画像生成（LLM 拟人化）
  - Parlant 配置映射（Segments、Personas、Guidelines）
- **ConfigAssembler**: 负责将用户画像相关的配置整合到最终的 Parlant 配置包中
- 用户画像将应用于：
  - 为不同用户群体创建差异化的 Journeys
  - 制定针对特定用户群体的 Guidelines
  - 设计个性化的 Variables 和 Tools
  - 生成 agent_user_profiles.json 配置文件

---

## 3. 技术栈选型

### 3.1 核心技术栈

| 类别 | 技术 | 版本 | 选择理由 |
|------|------|------|---------|
| **编程语言** | Python | 3.11+ | 丰富的 AI 生态，异步支持好 |
| **LLM SDK** | openai | 1.x | 官方 SDK，稳定可靠 |
| **HTTP 客户端** | aiohttp | 3.9+ | 异步 HTTP，性能优异 |
| **数据验证** | pydantic | 2.x | 类型安全，JSON Schema 生成 |
| **JSON 修复** | json-repair | 0.29+ | 强大的非标准 JSON 解析能力 |
| **日志系统** | loguru | 0.7+ | 简洁易用，功能强大 |
| **配置管理** | pyyaml | 6.x | YAML 解析，人类可读 |
| **并发控制** | asyncio | 内置 | 原生异步支持 |
| **流程挖掘** | pm4py | 2.x | 成熟的流程挖掘库 |
| **聚类算法** | scikit-learn | 1.x | DBSCAN 等聚类算法 |
| **文本向量化** | text-embedding-3-small | 通过 OpenAI API 调用，无需本地模型 |

### 3.2 开发工具

| 工具 | 用途 |
|------|------|
| pytest | 单元测试框架 |
| pytest-asyncio | 异步测试支持 |
| coverage | 代码覆盖率 |
| black | 代码格式化 |
| mypy | 类型检查 |

### 3.3 运行时依赖

```python
# requirements.txt
openai>=1.0.0
aiohttp>=3.9.0
pydantic>=2.0.0
json-repair>=0.29.0  # JSON 修复库
loguru>=0.7.0
pyyaml>=6.0.0
pm4py>=2.0.0
scikit-learn>=1.0.0
pytest>=7.0.0
pytest-asyncio>=0.21.0
```

---

## 4. 系统分层设计

### 4.1 目录结构

```
parlant_mining_system/
├── main.py                      # 主入口
├── config/                      # 参数配置文件目录
│   ├── __init__.py
│   ├── schema.py                # 配置 Schema 定义
│   ├── loader.py                # 配置加载器
│   ├── default_config.yaml      # 默认参数配置
│   └── environment.py           # 环境变量处理
├── prompts/                     # Prompt 配置文件目录
│   ├── domain_expert.yaml       # 领域专家 Prompt
│   ├── data_analyst.yaml        # 数据分析师 Prompt
│   ├── process_designer.yaml    # 流程设计师 Prompt
│   ├── rule_engineer.yaml       # 规则工程师 Prompt
│   ├── journey_builder.yaml     # 旅程构建师 Prompt
│   ├── user_portrait_miner.yaml # 用户画像挖掘 Prompt (新增)
│   ├── config_assembler.yaml    # 配置组装师 Prompt
│   ├── json_correction.yaml     # JSON 修正 Prompt
│   └── templates/               # 通用 Prompt 模板
├── core/
│   ├── __init__.py
│   ├── orchestrator.py          # 工作流编排器
│   ├── checkpoint.py            # 检查点管理
│   └── coordinator.py           # Coordinator Agent
├── agents/
│   ├── __init__.py
│   ├── base_agent.py            # Agent 基类
│   ├── requirement_analyst.py
│   ├── domain_expert.py
│   ├── data_analyst.py
│   ├── process_designer.py
│   ├── rule_engineer.py
│   ├── tool_architect.py
│   ├── journey_builder.py
│   ├── user_portrait_miner.py   # 用户画像挖掘 Agent (新增)
│   ├── config_assembler.py
│   ├── customer_advocate.py
│   └── qa_moderator.py
├── tools/                       # 工具实现目录
│   ├── __init__.py
│   ├── file_tool.py             # 文件工具
│   ├── search_tool.py           # 搜索工具
│   ├── code_executor.py         # 代码执行器
│   ├── git_tool.py              # Git 工具
│   ├── json_validator.py        # JSON 校验工具
│   └── skill_package.py         # Skill 包管理
├── services/                    # 模型服务目录
│   ├── __init__.py
│   ├── llm_service.py           # LLM 服务 (OpenAI)
│   └── embedding_service.py     # Embedding 服务
├── utils/
│   ├── __init__.py
│   ├── text_processor.py        # 文本处理工具
│   └── retry_utils.py           # 重试工具
├── tests/
│   ├── unit/                    # 单元测试
│   ├── integration/             # 集成测试
│   └── mocks/                   # Mock 数据
├── logs/                        # 日志目录
├── checkpoints/                 # 检查点目录
├── output/                      # 输出目录
│   └── user_profiles/           # 用户画像输出
│       ├── segments.json        # 用户分群结果
│       ├── personas.json        # 典型用户画像
│       ├── behavior_patterns.json # 行为模式分析
│       └── agent_user_profiles.json # Parlant 配置映射
└── requirements.txt
```

### 4.2 模块职责划分

#### 4.2.1 main.py - 主入口

**职责**:
- 加载配置文件
- 初始化各服务
- 根据 debug 参数选择配置来源
- 启动工作流编排器
- 异常捕获和 traceback 打印

**伪代码逻辑**:
```python
def main(debug: bool = False, config_path: str = None, 
         start_stage: str = "sprint_0", stop_stage: str = "sprint_5"):
    try:
        # 1. 加载配置
        if debug:
            config = load_debug_config()  # 代码中固定配置
        else:
            config = load_config(config_path or "config.yaml")
        
        # 2. 初始化服务
        llm_service = LLMService(config.llm)
        embedding_service = EmbeddingService(config.embedding)
        file_service = FileService(config.workspace)
        
        # 3. 初始化编排器
        orchestrator = WorkflowOrchestrator(
            config=config,
            services={llm_service, embedding_service, file_service}
        )
        
        # 4. 执行工作流 (支持阶段控制)
        orchestrator.run(
            start_stage=start_stage,  # 从哪个阶段开始
            stop_stage=stop_stage     # 到哪个阶段停止
        )
        
    except Exception as e:
        # 5. 异常处理
        logger.exception(f"系统异常：{traceback.format_exc()}")
        raise
```

#### 4.2.2 Workflow Orchestrator - 工作流编排器

**职责**:
- 管理 6 个 Sprint 的执行顺序
- 协调 Agent 间的输入输出传递
- 管理检查点保存和恢复
- 处理并行任务的同步
- 支持阶段控制 (start_stage/stop_stage)

**关键设计**:
- **状态机模式**: 每个 Sprint 是一个状态，状态转移由完成条件触发
- **检查点机制**: 每个 Sprint 完成后保存中间结果到文件系统
- **并行调度**: 识别可并行的 Agent (如 ToolArchitect vs JourneyBuilder)
- **阶段控制**: 支持从指定阶段开始和停止，便于快速测试

**阶段控制逻辑**:
```python
class WorkflowOrchestrator:
    """工作流编排器"""
    
    def __init__(self, config: Config, services: ServiceContainer):
        self.config = config
        self.services = services
        self.stages = [
            "sprint_0",
            "sprint_1", 
            "sprint_2",
            "sprint_3",
            "sprint_4",
            "sprint_5"
        ]
    
    def run(self, start_stage: str = "sprint_0", stop_stage: str = "sprint_5"):
        """
        执行工作流
        
        Args:
            start_stage: 起始阶段 (如 "sprint_0")
            stop_stage: 结束阶段 (如 "sprint_5")
        """
        # 1. 验证阶段参数
        if start_stage not in self.stages:
            raise ValueError(f"无效的起始阶段：{start_stage}")
        if stop_stage not in self.stages:
            raise ValueError(f"无效的结束阶段：{stop_stage}")
        
        start_idx = self.stages.index(start_stage)
        stop_idx = self.stages.index(stop_stage)
        
        if start_idx > stop_idx:
            raise ValueError(
                f"起始阶段 ({start_stage}) 不能晚于结束阶段 ({stop_stage})"
            )
        
        # 2. 检查是否需要从检查点恢复
        if start_idx > 0:
            checkpoint_file = f"checkpoints/{self.stages[start_idx-1]}/state.json"
            if os.path.exists(checkpoint_file):
                logger.info(f"从检查点恢复：{checkpoint_file}")
                state = self._load_checkpoint(checkpoint_file)
            else:
                logger.warning(
                    f"未找到前一阶段的检查点，从头开始：{self.stages[start_idx]}"
                )
        
        # 3. 执行指定范围的阶段
        for idx in range(start_idx, stop_idx + 1):
            stage_name = self.stages[idx]
            logger.info(f">>> 开始执行阶段：{stage_name}")
            
            try:
                # 执行该阶段的任务
                self._execute_stage(stage_name, state)
                
                # 保存检查点
                self._save_checkpoint(stage_name, state)
                
                logger.info(f"<<< 阶段完成：{stage_name}")
                
            except Exception as e:
                logger.error(f"阶段执行失败：{stage_name}")
                logger.exception(e)
                raise
        
        logger.info("所有阶段执行完成!")
```

#### 4.2.3 Agent 基类设计 (Function Call + 轻量 ReAct 混合模式)

所有 Agent 继承自统一基类，采用 **Function Call 为主、轻量 ReAct 为辅**的混合模式:

**设计理念**:
- **常规工具调用**: 使用 Function Call，结构化、稳定、低成本
- **复杂任务**: 使用简化版 ReAct(最多 2 轮思考),增强推理能力
- **默认 Function Call**: 除非明确需要推理，否则不使用 ReAct

```python
class BaseAgent(ABC):
    """Agent 基类 (Function Call + 轻量 ReAct 混合模式)"""
    
    def __init__(self, config: Config, services: ServiceContainer, tools: ToolContainer):
        self.config = config
        self.services = services
        self.tools = tools
        self.logger = get_logger(self.__class__.__name__)
        # Function Call 模式配置
        self.use_function_call = config.agent.get('use_function_call', True)
        # ReAct 模式配置 (仅在复杂任务中启用)
        self.enable_react = config.agent.get('enable_react', False)
        self.max_thought_turns = config.agent.get('max_thought_turns', 2)  # 限制为 2 轮，避免过度推理
    
    @abstractmethod
    async def execute(self, input_data: dict) -> dict:
        """执行 Agent 任务"""
        pass
    
    async def execute_with_function_call(self, task: str, tools_to_use: list[str]) -> dict:
        """
        Function Call 模式执行
        
        流程:
        1. 构造 Function Schema
        2. 调用 LLM with Functions
        3. 解析并执行工具
        4. 返回结果
        
        适用场景:
        - 工具调用逻辑明确
        - 不需要复杂推理
        - 追求稳定性和低成本
        """
        # Step 1: 注册可用工具
        functions = [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for tool in self.tools.get_all(tools_to_use)
        ]
        
        # Step 2: 调用 LLM with Function Call
        response = await self.services.llm.chat_with_functions(
            messages=[{"role": "user", "content": task}],
            functions=functions,
            function_call="auto"  # 让 LLM 自动决定是否调用函数
        )
        
        # Step 3: 处理响应
        if response.choices[0].message.function_call:
            # LLM 决定调用工具
            function_name = response.choices[0].message.function_call.name
            function_args = json.loads(response.choices[0].message.function_call.arguments)
            
            # 执行工具
            result = await self.tools.execute(function_name, **function_args)
            
            # Step 4: 将工具结果返回给 LLM，生成最终回答
            final_response = await self.services.llm.chat(
                messages=[
                    {"role": "user", "content": task},
                    {"role": "assistant", "content": None, "function_call": response.choices[0].message.function_call},
                    {"role": "function", "name": function_name, "content": str(result)}
                ]
            )
            
            return {"result": final_response.choices[0].message.content, "tool_result": result}
        else:
            # LLM 直接回答 (不调用工具)
            return {"result": response.choices[0].message.content}
    
    async def react_loop(self, task: str) -> dict:
        """
        轻量级 ReAct 循环：思考 → 行动 → 观察 (→ 再思考)
        
        注意：仅在 enable_react=True 且任务复杂度高的场景下使用
        最大思考轮数限制为 2，避免过度推理和成本失控
        
        流程:
        1. Thought: 分析当前情况，决定下一步
        2. Action: 选择并执行工具
        3. Observation: 观察工具执行结果
        4. (可选) 再次思考：基于观察调整策略
        5. 返回最终答案
        
        适用场景:
        - 需要多步骤推理
        - 任务目标不明确
        - 需要动态调整策略
        """
        thought_history = []
        
        for turn in range(self.max_thought_turns):
            # Step 1: Thought - 思考
            thought = await self._think(task, thought_history)
            thought_history.append({'type': 'thought', 'content': thought})
            
            # Step 2: Decide - 决定是否完成任务
            if thought.is_final_answer:
                return thought.final_answer
            
            # Step 3: Action - 选择并执行工具
            action = thought.next_action
            tool_result = await self.tools.execute(action.tool_name, action.parameters)
            thought_history.append({'type': 'action', 'result': tool_result})
            
            # Step 4: Observation - 观察结果，继续下一轮思考
        
        # 达到最大轮数，强制返回最终答案
        final_answer = await self._generate_final_answer(task, thought_history)
        return final_answer
    
    async def validate_output(self, output: dict) -> tuple[bool, list[str]]:
        """验证输出格式 (默认使用 Pydantic)"""
        # 子类可重写
        return True, []
    
    async def execute_with_retry(self, input_data: dict, max_retries: int = 3) -> dict:
        """带重试和 LLM 修正的执行"""
        for attempt in range(max_retries):
            # 根据任务复杂度选择模式
            if self.enable_react and self._is_complex_task(input_data):
                result = await self.react_loop(input_data['task'])
            else:
                result = await self.execute_with_function_call(
                    input_data['task'], 
                    input_data.get('tools', [])
                )
            
            is_valid, errors = await self.validate_output(result)
            
            if is_valid:
                return result
            
            # 使用 LLM 修正
            if attempt < max_retries - 1:
                result = await self.fix_with_llm(result, errors)
        
        raise ValidationError(f"输出校验失败：{errors}")
    
    def _is_complex_task(self, input_data: dict) -> bool:
        """判断是否为复杂任务 (需要 ReAct 模式)"""
        # 简单规则：任务描述长度、是否需要多步骤、是否有歧义
        task_description = input_data.get('task', '')
        return (
            len(task_description) > 500 or  # 长任务
            input_data.get('requires_multi_step', False) or  # 明确需要多步骤
            input_data.get('has_ambiguity', False)  # 存在歧义
        )
```

**混合模式关键组件**:

| 组件 | 职责 | 实现方式 | 使用场景 |
|------|------|----------|----------|
| **Function Call** | 结构化调用工具 | OpenAI Functions API | 常规工具调用 (80% 场景) |
| **轻量 ReAct** | 复杂推理和多步骤规划 | 简化版思考循环 (最多 2 轮) | 复杂任务 (20% 场景) |
| **模式选择器** | 自动判断使用哪种模式 | 基于任务复杂度规则 | 智能决策 |
| **Tool Registry** | 管理可用工具 | 动态注册/卸载工具 | 两种模式共享 |

**模式选择策略**:
```python
# 使用 Function Call 的场景 (默认)
✅ 工具调用逻辑明确
✅ 单步骤任务
✅ 追求稳定性和低成本
✅ 例如：文件读写、数据查询、代码执行

# 使用 ReAct 的场景 (需明确启用)
✅ 需要多步骤推理
✅ 任务目标不明确
✅ 需要动态调整策略
✅ 例如：Deep Research 搜索策略制定、复杂数据分析
```

**工具接口**:
```python
class BaseTool(ABC):
    """工具基类"""
    
    name: str  # 工具名称
    description: str  # 工具描述
    parameters: dict  # 参数 Schema
    
    @abstractmethod
    async def execute(self, **kwargs) -> any:
        """执行工具"""
        pass

# 示例：FileTool
class FileTool(BaseTool):
    name = "file_tool"
    description = "读写文件，管理目录"
    parameters = {
        "operation": {"type": "string", "enum": ["read", "write", "list_dir"]},
        "path": {"type": "string"},
        "content": {"type": "string", "optional": True}
    }
    
    async def execute(self, operation: str, path: str, content: str = None):
        if operation == "read":
            return await read_file(path)
        elif operation == "write":
            return await write_file(path, content)
```

#### 4.2.4 Agent 并发控制器

**设计目标**: 支持 Agent 间并发执行，但可通过参数控制为串行。

```python
class AgentConcurrencyController:
    """Agent 并发控制器"""
    
    def __init__(self, max_concurrent: int = 5):
        """
        Args:
            max_concurrent: 最大并发数
                - >1: 并行执行
                - =1: 串行执行
        """
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)
    
    async def execute_agents(self, agents: list[BaseAgent], inputs: list[dict]) -> list[dict]:
        """
        执行多个 Agent，根据并发参数决定并行或串行
        
        Args:
            agents: Agent 列表
            inputs: 对应的输入列表
        
        Returns:
            每个 Agent 的输出结果
        """
        if self.max_concurrent == 1:
            # 串行模式
            logger.info("串行模式：依次执行 Agent")
            results = []
            for agent, input_data in zip(agents, inputs):
                result = await agent.execute_with_retry(input_data)
                results.append(result)
            return results
        else:
            # 并行模式
            logger.info(f"并行模式：最大并发数={self.max_concurrent}")
            
            async def execute_with_semaphore(agent, input_data, index):
                async with self._semaphore:
                    result = await agent.execute_with_retry(input_data)
                    return (index, result)
            
            tasks = [
                execute_with_semaphore(agent, inp, idx)
                for idx, (agent, inp) in enumerate(zip(agents, inputs))
            ]
            
            completed = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 按原始顺序排序结果
            results = sorted(
                [(idx, res) for idx, res in completed if not isinstance(res, Exception)],
                key=lambda x: x[0]
            )
            
            return [res for _, res in results]
```

#### 4.2.5 UserPortraitMiner - 用户画像挖掘 Agent (新增)

**职责定位**: 
从对话数据中自动挖掘用户特征、分群聚类和生成典型用户画像，并映射到 Parlant 配置。

**核心功能**:
1. **用户特征提取**: 从 DataAnalyst 提供的标注对话中提取 Tags、Behaviors、Metadata
2. **增量聚合统计**: 维护全局 feature_stats，实时更新群体特征
3. **分群聚类分析**: 使用 DBSCAN/K-Means 发现自然用户群体
4. **典型画像生成**: LLM 基于聚类结果生成拟人化画像（如"精明消费者小王"）
5. **Parlant 配置映射**: 生成 agent_user_profiles.json（Segments、Personas、Guidelines）

**工作流程**:
```
DataAnalyst 提供的标注对话
  ↓
用户特征提取（LLM）
  ├─ Tags: price_sensitive, vip, elderly...
  ├─ Behaviors: "频繁询问折扣", "对比竞品价格"...
  └─ Metadata: {price_sensitivity_score: 0.8, ...}
  ↓
增量聚合统计（每通对话独立处理）
  ├─ 更新 global_feature_stats[tag]['count']
  ├─ 追加 behaviors 和 dialogues
  └─ 每 10 个批次保存检查点
  ↓
分群聚类分析（所有对话处理完成后）
  ├─ 构建特征矩阵（基于 Tags 频次、Metadata）
  ├─ DBSCAN/K-Means 聚类
  └─ 提取簇特征（高频 Tags、代表性行为）
  ↓
典型用户画像生成（LLM）
  ├─ 输入：簇名称、特征、代表性对话
  ├─ 输出：拟人化画像（姓名、人口统计学、目标、痛点...）
  └─ 示例："精明消费者小王"、"高端商务人士张总"
  ↓
Parlant 配置映射
  ├─ 生成 user_segments（定义、Tags、Metadata Rules）
  ├─ 生成 personas（画像详情）
  ├─ 设计 special_guidelines（群体特定指南）
  └─ 定义 custom_variables（量化变量）
  ↓
输出 agent_user_profiles.json
```

**与其他 Agent 的协作**:
- **DataAnalyst**: 提供标注用户特征的对话数据集
- **CustomerAdvocate**: 验证画像合理性（模拟测试、体验反馈）
- **RuleEngineer**: 制定针对特定用户群体的 Guidelines
- **JourneyBuilder**: 为不同用户群体设计差异化的 Journeys
- **ConfigAssembler**: 将用户画像配置整合到最终 Parlant 配置包

**核心设计理念**:
1. **数据驱动的分群**: 基于真实对话数据，使用无监督学习发现自然分组
2. **增量式聚合**: 单通对话独立处理，实时更新全局统计，支持断点续传
3. **LLM+ 算法协同**: 算法负责聚类分析，LLM 负责画像生成和话术设计
4. **可解释性与可追溯性**: 每个分群都有特征描述和代表性对话支撑

**关键算法与技术**:
- **特征提取**: LLM Prompt Engineering
- **增量聚合**: 字典实时统计 + 检查点机制
- **聚类分析**: DBSCAN（无需预设簇数）、K-Means（已知分群数量）
- **画像生成**: LLM 基于结构化数据生成拟人化描述
- **质量评估**: 分群覆盖率（>80%）、纯度（>0.7）、画像真实性（LLM-Judge >4.0）

**输入输出规范**:
```python
# 输入
input_data = {
    "conversations": List[Dict],  # DataAnalyst 提供的标注对话
    "domain_knowledge": Dict,      # 领域知识（可选）
    "clustering_params": {         # 聚类参数（可选）
        "method": "DBSCAN",
        "eps": 0.5,
        "min_samples": 5
    }
}

# 输出
output_data = {
    "user_segments": [
        {
            "segment_id": "seg_price_sensitive",
            "segment_name": "价格敏感型客户",
            "definition": {
                "tags": ["price_sensitive", "coupon_user"],
                "metadata_rules": {"price_sensitivity_score": ">0.7"}
            },
            "behavior_patterns": [...],
            "special_guidelines": [...],
            "custom_variables": {...}
        }
    ],
    "personas": [
        {
            "persona_id": "persona_price_001",
            "persona_name": "精明消费者小王",
            "demographics": "25-35 岁，白领，月收入 1-2 万",
            "goals": "用最少的钱买到最好的商品",
            "pain_points": [...],
            "behavior_patterns": [...],
            "typical_dialogues": [...],
            "parlant_mapping": {...}
        }
    ],
    "agent_user_profiles.json": "完整配置文件路径"
}
```

**最佳实践建议**:
- **最小数据量**: 至少 500 通真实对话，覆盖不同业务场景
- **时间跨度**: 至少 1 个月，避免季节性偏差
- **分群数量**: 建议 3-7 个分群，每个分群 1-2 个典型画像
- **迭代策略**: V1.0 初版 → V1.1 人工评审调整 → V2.0 增量更新

**性能预估**:
- 1000 通对话：~12 分钟（包括特征提取、增量聚合、聚类分析、画像生成）
- 内存优化：增量式处理，不需要一次性加载所有对话（降低 90%+ 内存占用）
- 加速比：1.2x（时间提升不明显），但内存稳定性大幅提升

---

## 5. 核心模块设计

### 5.1 LLM Service - LLM 服务 (含 Embedding)

#### 5.1.1 核心功能

**功能列表**:
1. **OpenAI 接口封装**: 统一聊天接口 + Embedding 接口
2. **多模型支持**: 配置多个模型，自动故障切换
3. **RMP 限流**: 请求速率限制
4. **超时控制**: 请求超时设置
5. **重试机制**: 指数退避重试
6. **Embedding 服务**: 通过 OpenAI API 生成向量

#### 5.1.2 多模型故障切换逻辑

**配置示例**:
```yaml
llm:
  # Chat 模型配置
  chat_models:
    - name: "gpt-4"
      base_url: "https://api.openai.com/v1"
      api_key_env: "OPENAI_API_KEY"
      max_retries: 3
      timeout: 30
      
    - name: "gpt-3.5-turbo"
      base_url: "https://api.openai.com/v1"
      api_key_env: "OPENAI_API_KEY"
      max_retries: 3
      timeout: 30
  
  # Embedding 模型配置
  embedding_models:
    - name: "text-embedding-3-small"
      base_url: "https://api.openai.com/v1"
      api_key_env: "OPENAI_API_KEY"
      dimensions: 1536
    
    - name: "text-embedding-3-large"
      base_url: "https://api.openai.com/v1"
      api_key_env: "OPENAI_API_KEY"
      dimensions: 3072
  
  switch_after_failures: 3
  
  rate_limit:
    requests_per_minute: 60
    tokens_per_minute: 100000
```

**切换逻辑流程图**:
```
初始化模型列表
  ↓
选择当前模型 (索引 0)
  ↓
发送请求 → 成功 → 返回结果
  ↓失败
失败计数 +1
  ↓
失败计数 >= switch_after_failures?
  ├─ 否 → 重试 (最多 max_retries 次)
  └─ 是 → 切换到下一个模型
          ↓
        还有下一个模型？
        ├─ 是 → 重置失败计数，重试
        └─ 否 → 抛出异常 (所有模型失败)
```

**关键实现要点**:
- 使用装饰器实现 RMP 限流
- 使用 aiohttp.ClientTimeout 控制超时
- 使用指数退避策略重试 (1s, 2s, 4s, 8s...)
- 记录每个模型的失败历史

#### 5.1.3 RMP 限流实现

```python
class RateLimiter:
    """速率限制器"""
    
    def __init__(self, requests_per_minute: int, tokens_per_minute: int):
        self.rpm = requests_per_minute
        self.tpm = tokens_per_minute
        self.request_timestamps = deque()
        self.token_timestamps = deque()
    
    async def acquire(self, token_count: int):
        """获取许可 (异步等待直到可用)"""
        now = time.time()
        
        # 清理 60 秒前的记录
        while self.request_timestamps and now - self.request_timestamps[0] > 60:
            self.request_timestamps.popleft()
        
        while self.token_timestamps and now - self.token_timestamps[0] > 60:
            self.token_timestamps.popleft()
        
        # 检查是否超限
        if len(self.request_timestamps) >= self.rpm:
            wait_time = 60 - (now - self.request_timestamps[0])
            await asyncio.sleep(wait_time)
        
        if sum(self.token_timestamps) >= self.tpm:
            wait_time = 60 - (now - self.token_timestamps[0])
            await asyncio.sleep(wait_time)
        
        # 记录本次请求
        self.request_timestamps.append(now)
        self.token_timestamps.append((now, token_count))
```

### 5.2 File Service - 文件服务

#### 5.2.1 核心职责

**功能**:
1. 文件读写 (支持大文件分块)
2. 目录管理 (创建、删除、遍历)
3. 中间文件保存 (检查点)
4. 路径校验 (防止目录穿越)

#### 5.2.2 中间文件命名规范

```
checkpoints/
├── sprint_0_requirement_analysis/
│   ├── requirement_doc_v1.json
│   ├── clarification_questions.json
│   └── scope_statement.json
├── sprint_1_knowledge_mining/
│   ├── public_knowledge_v1.json
│   ├── private_knowledge_batch_10.pkl
│   └── private_knowledge_batch_20.pkl
├── sprint_2_process_design/
│   └── business_flowchart_v1.json
└── ...
```

**命名规则**: `sprint_{编号}_{步骤名称}/{文件描述}_v{版本}.{扩展名}`

### 5.3 JSON Validator - JSON 校验工具

#### 5.3.1 核心职责

**功能**:
1. **json_repair 解析**: 使用 json_repair 库解析非标准 JSON
2. **Pydantic Schema 校验**: 验证 JSON 结构和字段
3. **LLM 修正循环**: 自动修正格式错误和字段错误
4. **自定义规则校验**: 业务规则验证
5. **格式转换**: JSON ↔ YAML 等格式互转

#### 5.3.2 校验流程

```
Agent 输出原始文本
  ↓
json_repair 解析
  ├─ 解析成功 → 提取 JSON 对象
  └─ 解析失败 → LLM 重新生成
              ↓
         重新解析
              ↓
         仍失败？→ 抛出异常
  ↓
Pydantic 模型校验
  ↓
校验通过？ 
├─ 是 → 返回成功
└─ 否 → 收集字段错误
        ↓
      构造修正 Prompt
        ↓
      调用 LLM 修正字段
        ↓
      json_repair 重新解析
        ↓
      重新校验 (回到第 2 步)
        ↓
      达到最大重试次数？
      ├─ 是 → 抛出异常
      └─ 否 → 继续修正
```

#### 5.3.3 技术栈更新

```python
# requirements.txt 新增
json-repair>=0.29.0  # 强大的 JSON 修复库
```

#### 5.3.4 json_repair 集成

**核心优势**:
- ✅ 支持缺失引号的键名
- ✅ 支持单引号
- ✅ 支持尾随逗号
- ✅ 支持注释
- ✅ 自动修复常见格式错误

**使用示例**:
```python
from json_repair import repair_json, loads

def parse_with_repair(raw_text: str) -> dict:
    """
    使用 json_repair 解析 JSON
    
    Args:
        raw_text: LLM 输出的原始文本
    
    Returns:
        解析后的字典对象
    
    Raises:
        JSONParseError: 解析失败
    """
    try:
        # Step 1: 尝试直接解析
        return loads(raw_text)
    except:
        # Step 2: 使用 repair 修复后解析
        try:
            repaired = repair_json(raw_text)
            return loads(repaired)
        except Exception as e:
            raise JSONParseError(f"JSON 解析失败：{str(e)}")
```

#### 5.3.5 完整校验器实现

```python
from json_repair import repair_json, loads
from pydantic import BaseModel, ValidationError
from typing import Tuple, Optional

class JSONValidator:
    """JSON 校验器 (json_repair + Pydantic + LLM 修正)"""
    
    def __init__(self, llm_service, schema_model: type[BaseModel], 
                 max_retries: int = 3):
        """
        Args:
            llm_service: LLM 服务实例
            schema_model: Pydantic 模型类
            max_retries: 最大重试次数
        """
        self.llm_service = llm_service
        self.schema_model = schema_model
        self.max_retries = max_retries
    
    async def validate_and_fix(self, raw_output: str) -> dict:
        """
        校验并自动修复 JSON
        
        流程:
        1. json_repair 解析
        2. Pydantic 字段校验
        3. 失败则 LLM 修正
        4. 循环直到成功或达到最大重试
        
        Args:
            raw_output: LLM 原始输出
        
        Returns:
            校验通过的字典对象
        
        Raises:
            ValidationError: 校验失败
        """
        error_history = []
        
        for attempt in range(self.max_retries):
            try:
                # Step 1: json_repair 解析
                parsed = self._parse_with_repair(raw_output)
                
                # Step 2: Pydantic 校验
                validated_obj = self.schema_model(**parsed)
                
                # Step 3: 转换为字典返回
                return validated_obj.model_dump()
                
            except JSONParseError as e:
                # 解析失败，需要 LLM 重新生成
                logger.warning(f"JSON 解析失败 (尝试 {attempt+1}/{self.max_retries}): {e}")
                error_history.append({'type': 'parse', 'error': str(e)})
                
                raw_output = await self._request_llm_regenerate(
                    raw_output, 
                    error_history
                )
                
            except ValidationError as e:
                # 字段校验失败，需要 LLM 修正字段
                logger.warning(f"字段校验失败 (尝试 {attempt+1}/{self.max_retries}): {e}")
                error_history.append({'type': 'validation', 'error': str(e)})
                
                raw_output = await self._request_llm_fix_fields(
                    raw_output, 
                    parsed if 'parsed' in locals() else None,
                    e.errors(),
                    error_history
                )
        
        # 达到最大重试次数，抛出异常
        raise ValidationError(
            f"JSON 校验失败，已尝试 {self.max_retries} 次:\n"
            f"错误历史：{error_history}"
        )
    
    def _parse_with_repair(self, raw_text: str) -> dict:
        """使用 json_repair 解析 JSON"""
        try:
            # 先尝试直接解析
            return loads(raw_text)
        except:
            # 使用 repair 修复后解析
            try:
                repaired = repair_json(raw_text)
                return loads(repaired)
            except Exception as e:
                raise JSONParseError(f"JSON 解析失败：{str(e)}")
    
    async def _request_llm_regenerate(self, failed_output: str, 
                                      error_history: list) -> str:
        """请求 LLM 重新生成 JSON (解析失败场景)"""
        prompt = REGENERATE_PROMPT.format(
            original_output=failed_output,
            expected_schema=self.schema_model.model_json_schema(),
            error_history="\n".join([str(e) for e in error_history])
        )
        
        response = await self.llm_service.chat(prompt)
        return self._extract_json_from_response(response)
    
    async def _request_llm_fix_fields(self, raw_output: str, 
                                       parsed_data: Optional[dict],
                                       validation_errors: list,
                                       error_history: list) -> str:
        """请求 LLM 修正字段 (字段校验失败场景)"""
        prompt = FIX_FIELDS_PROMPT.format(
            original_output=raw_output,
            parsed_data=parsed_data,
            errors=validation_errors,
            expected_schema=self.schema_model.model_json_schema(),
            error_history="\n".join([str(e) for e in error_history])
        )
        
        response = await self.llm_service.chat(prompt)
        return self._extract_json_from_response(response)
    
    def _extract_json_from_response(self, text: str) -> str:
        """从 LLM 响应中提取 JSON 部分"""
        # 支持 ```json ... ``` 或 ``` ... ``` 包裹的 JSON
        import re
        pattern = r'```(?:json)?\s*([\s\S]*?)```'
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
        return text.strip()
```

#### 5.3.6 Prompt 模板

```python
# 重新生成 Prompt (解析失败时使用)
REGENERATE_PROMPT = """
你之前生成的 JSON 无法正确解析，请重新生成。

【原始输出】
{original_output}

【解析错误】
{error_history}

【期望的 JSON Schema】
{expected_schema}

请只返回标准的 JSON 格式，不要包含任何其他内容。
确保:
1. 所有键名使用双引号
2. 所有字符串值使用双引号
3. 不使用尾随逗号
4. 不使用注释
"""

# 字段修正 Prompt (校验失败时使用)
FIX_FIELDS_PROMPT = """
你生成的 JSON 可以解析，但字段不符合要求，请修正。

【原始输出】
{original_output}

【已解析的数据】
{parsed_data}

【字段错误】
{errors}

【期望的 JSON Schema】
{expected_schema}

【历史错误】
{error_history}

请修正上述字段错误，返回符合 Schema 的 JSON。
注意：只返回 JSON，不要包含其他内容。
"""
```

#### 5.3.7 使用示例

```python
# 定义 Pydantic 模型
class TerminologyExtraction(BaseModel):
    terminologies: list[str]
    processes: list[str]
    business_goals: list[str]

# 创建校验器
validator = JSONValidator(
    llm_service=llm_service,
    schema_model=TerminologyExtraction,
    max_retries=3
)

# Agent 输出校验
async def agent_execution():
    # 模拟 Agent 输出 (可能包含格式错误)
    raw_output = '''
    {
        terminologies: ["保险", "保费", "保额"],  // 键名缺少引号
        'processes': ['推销流程', '售后流程'],     // 使用单引号
        "business_goals": ["销售", "服务"]，       // 中文逗号
    }
    '''
    
    try:
        # 自动修复并校验
        result = await validator.validate_and_fix(raw_output)
        print(f"校验成功：{result}")
        
    except ValidationError as e:
        print(f"校验失败：{e}")
```

#### 5.3.8 错误处理策略

| 错误类型 | 处理方式 | 重试次数 |
|---------|---------|---------|
| **json_repair 解析失败** | LLM 重新生成 | 计入总重试 |
| **必需字段缺失** | LLM 补充字段 | 计入总重试 |
| **字段类型错误** | LLM 修正类型 | 计入总重试 |
| **枚举值不匹配** | LLM 修正为合法值 | 计入总重试 |
| **格式约束违反** | LLM 修正格式 | 计入总重试 |
| **连续 3 次失败** | 抛出异常，记录日志 | 终止 |

### 5.4 Skill Package - 技能包管理

#### 5.4.1 设计理念

**Skill Package** 是 Agent 可动态加载的技能集合，每个技能是一个独立的工具或能力模块。

**特点**:
- ✅ **热插拔**: 运行时动态加载/卸载
- ✅ **独立版本**: 每个技能有独立版本号
- ✅ **按需加载**: 根据任务需求加载相关技能
- ✅ **沙箱隔离**: 技能执行在隔离环境中

#### 5.4.2 技能包结构

```
skills/
├── __init__.py
├── skill_registry.py          # 技能注册表
├── base_skill.py              # 技能基类
├── web_search/                # Web 搜索技能
│   ├── __init__.py
│   ├── skill.yaml             # 技能描述文件
│   └── main.py                # 技能实现
├── code_interpreter/          # 代码解释技能
│   ├── __init__.py
│   ├── skill.yaml
│   └── main.py
├── data_analysis/             # 数据分析技能
│   ├── __init__.py
│   ├── skill.yaml
│   └── main.py
└── custom_skills/             # 用户自定义技能
    └── my_skill/
        ├── __init__.py
        ├── skill.yaml
        └── main.py
```

**skill.yaml 示例**:
```yaml
# skills/web_search/skill.yaml
name: "web_search"
version: "1.0.0"
description: "Web 搜索和信息收集技能"
author: "System Team"

# 技能依赖
dependencies:
  python_packages:
    - "aiohttp>=3.9.0"
    - "beautifulsoup4>=4.12.0"

# 技能参数
parameters:
  max_results:
    type: "int"
    default: 10
    description: "最大搜索结果数"
  
  search_engines:
    type: "list[str]"
    default: ["google", "bing"]
    description: "使用的搜索引擎列表"

# 技能提供的工具
tools:
  - name: "search_web"
    description: "执行 Web 搜索"
    parameters:
      query: {type: "string", required: true}
      num_results: {type: "int", default: 10}
  
  - name: "extract_page_content"
    description: "提取网页内容"
    parameters:
      url: {type: "string", required: true}

# 技能元数据
metadata:
  category: "information_gathering"
  tags: ["search", "web", "research"]
  enabled: true
```

#### 5.4.3 技能注册表

```python
class SkillRegistry:
    """技能注册表"""
    
    def __init__(self):
        self._skills = {}  # name -> Skill instance
        self._tools = {}   # tool_name -> (skill_name, tool_func)
    
    def register_skill(self, skill: BaseSkill):
        """注册技能"""
        self._skills[skill.name] = skill
        
        # 注册技能提供的所有工具
        for tool in skill.get_tools():
            self._tools[tool.name] = (skill.name, tool.execute)
        
        logger.info(f"注册技能：{skill.name} (版本 {skill.version})")
    
    def unregister_skill(self, skill_name: str):
        """卸载技能"""
        if skill_name not in self._skills:
            raise ValueError(f"技能不存在：{skill_name}")
        
        # 移除该技能提供的所有工具
        tools_to_remove = [
            tool_name for tool_name, (sname, _) in self._tools.items()
            if sname == skill_name
        ]
        for tool_name in tools_to_remove:
            del self._tools[tool_name]
        
        del self._skills[skill_name]
        logger.info(f"卸载技能：{skill_name}")
    
    async def execute_tool(self, tool_name: str, **kwargs) -> any:
        """执行工具"""
        if tool_name not in self._tools:
            raise ValueError(f"工具不存在：{tool_name}")
        
        skill_name, tool_func = self._tools[tool_name]
        return await tool_func(**kwargs)
    
    def get_available_tools(self) -> list[dict]:
        """获取所有可用工具列表"""
        return [
            {"name": name, "skill": skill_name}
            for name, (skill_name, _) in self._tools.items()
        ]
```

#### 5.4.4 技能基类

```python
class BaseSkill(ABC):
    """技能基类"""
    
    name: str  # 技能名称
    version: str  # 版本号
    description: str  # 描述
    
    def __init__(self, config: dict):
        self.config = config
        self.tools = []  # 技能提供的工具列表
    
    @abstractmethod
    async def initialize(self):
        """初始化技能 (加载资源等)"""
        pass
    
    @abstractmethod
    async def shutdown(self):
        """关闭技能 (清理资源)"""
        pass
    
    @abstractmethod
    def get_tools(self) -> list[BaseTool]:
        """获取技能提供的所有工具"""
        pass
```

#### 5.4.5 使用示例

```python
# 1. 加载技能包
registry = SkillRegistry()

# 2. 从配置文件加载技能
skill_configs = load_yaml("skills/web_search/skill.yaml")
web_search_skill = WebSearchSkill(skill_configs)
await web_search_skill.initialize()
registry.register_skill(web_search_skill)

# 3. Agent 使用技能
async def agent_with_skills():
    agent = DomainExpert(config, services, tools)
    
    # Agent 可以通过工具名直接调用技能
    search_results = await registry.execute_tool(
        "search_web",
        query="保险推销流程",
        num_results=10
    )
    
    # 或者获取所有可用工具列表
    available_tools = registry.get_available_tools()
    print(f"可用工具：{available_tools}")

# 4. 动态加载新技能 (无需重启)
async def hot_reload_skill():
    # 检测技能目录变化
    new_skill_files = detect_new_skills()
    
    for skill_file in new_skill_files:
        skill_module = import_skill(skill_file)
        skill_instance = skill_module.create_skill()
        await skill_instance.initialize()
        registry.register_skill(skill_instance)
        logger.info(f"热加载技能：{skill_instance.name}")
```

### 5.4 Search Service - 搜索服务

#### 5.4.1 Deep Research 封装

**核心功能**:
1. 批量查询生成
2. 并发搜索控制
3. 结果去重和融合
4. 按业务维度组织

**业务维度拆分逻辑**:
```python
def split_by_business_dimensions(domain: list[str], business_goals: list[str]) -> list[SearchQuery]:
    """
    根据业务维度拆分搜索查询
    
    示例:
    domain = ["保险", "寿险"]
    business_goals = ["推销流程", "售后流程"]
    
    返回:
    [
        SearchQuery(topic="保险推销流程_术语表", priority=HIGH),
        SearchQuery(topic="保险推销流程_最佳实践", priority=MEDIUM),
        SearchQuery(topic="保险售后流程_术语表", priority=HIGH),
        ...
    ]
    """
    queries = []
    
    for goal in business_goals:
        # 每个业务目标拆分为 4 种知识类型
        knowledge_types = ["术语表", "业务流程", "合规要求", "最佳实践"]
        
        for ktype in knowledge_types:
            query_text = f"{domain} {goal} {ktype}"
            priority = calculate_priority(domain, goal, ktype)
            
            queries.append(SearchQuery(
                topic=query_text,
                priority=priority,
                business_goal=goal,
                knowledge_type=ktype
            ))
    
    return queries
```

#### 5.4.2 并发控制策略

```python
async def execute_searches_concurrently(
    queries: list[SearchQuery], 
    max_concurrent: int = 5
) -> list[SearchResult]:
    """并发执行搜索"""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def search_with_semaphore(query):
        async with semaphore:
            return await deep_research_search(query)
    
    tasks = [search_with_semaphore(q) for q in queries]
    results = await asyncio.gather(*tasks)
    
    return results
```

---

## 6. 数据流与处理逻辑

### 6.1 完整数据流图

```
用户输入
  ↓
┌─────────────────────┐
│ Sprint 0: 需求分析   │
│ 输入：领域关键词     │
│ 输出：需求文档 v2.0  │
└─────────────────────┘
  ↓
┌─────────────────────────────────┐
│ Sprint 1: 知识挖掘 (并行)       │
│ ┌─────────────────────────────┐ │
│ │ DomainExpert                │ │
│ │ 输入：领域关键词            │ │
│ │ 输出：公开知识库 v1.0       │ │
│ └─────────────────────────────┘ │
│              ↓                  │
│ ┌─────────────────────────────┐ │
│ │ DataAnalyst                 │ │
│ │ 输入：对话日志              │ │
│ │ 输出：私域知识库 v1.0       │ │
│ └─────────────────────────────┘ │
│              ↓                  │
│     融合知识库 v1.0             │
└─────────────────────────────────┘
  ↓
┌─────────────────────┐
│ Sprint 2: 流程设计   │
│ 输入：需求 + 知识    │
│ 输出：业务流程图 v1.0│
└─────────────────────┘
  ↓
┌─────────────────────┐
│ Sprint 3: 规则挖掘   │
│ 输入：流程 + 知识    │
│ 输出：规则集 v1.0    │
└─────────────────────┘
  ↓
┌─────────────────────────────┐
│ Sprint 4: 工具与旅程 (并行)  │
│ ┌──────────┐  ┌──────────┐  │
│ │ToolArch  │  │Journey   │  │
│ │输出：工具│  │输出：Journey│ │
│ └──────────┘  └──────────┘  │
└─────────────────────────────┘
  ↓
┌─────────────────────┐
│ Sprint 5: 集成质检   │
│ 输入：所有中间产物   │
│ 输出：Parlant 配置包  │
└─────────────────────┘
```

### 6.2 私域对话数据处理流程

```
对话日志文件
  ↓
预处理 (清洗、格式化)
  ↓
┌───────────────────────────────────┐
│ 单通对话独立处理 (并发)           │
│ for each conversation:            │
│   1. LLM 事件提取                  │
│   2. 意图识别                     │
│   3. 槽位填充                     │
│   4. 场景 Embedding 计算            │
│   5. **用户特征标注**             │
│   6. 保存到临时文件               │
└───────────────────────────────────┘
  ↓
场景聚类 (DBSCAN)
  ├─ 计算所有对话的 Embedding 相似度矩阵
  ├─ DBSCAN 聚类 (eps=0.4, min_samples=5)
  └─ 输出场景簇
  ↓
流程挖掘 (Heuristic Miner)
  ├─ 每个场景簇内的事件序列分析
  ├─ 发现频繁路径和分支
  └─ 生成 BPMN 流程图
  ↓
与公域知识对比融合
  ├─ 标注差异 (企业特有实践)
  ├─ 标注缺失 (可能遗漏)
  └─ 标注冲突 (需人工审核)
  ↓
融合知识库 v1.0
  ↓
UserPortraitMiner 处理
  ├─ 用户特征提取 (LLM + 规则)
  ├─ 增量聚合统计 (实时更新 global_feature_stats)
  ├─ 检查点保存 (每 10 个批次)
  ├─ 分群聚类 (DBSCAN/KMeans, 所有对话处理完成后)
  ├─ 典型用户画像生成 (LLM 拟人化)
  └─ Parlant 配置映射
  ↓
用户画像库 v1.0
  ├─ segments.json        # 用户分群
  ├─ personas.json        # 典型画像
  ├─ behavior_patterns.json # 行为模式
  └─ agent_user_profiles.json # 完整配置
```

### 6.3 评审团 (Review Board) 决策流程

```
阶段完成信号
  ↓
QAModerator 安排评审会议
  ↓
提前 24 小时分发评审材料
  ↓
┌─────────────────────────────────┐
│ 独立评审阶段                     │
│ 各评审成员阅读材料              │
│ 提交书面评审意见                │
└─────────────────────────────────┘
  ↓
汇总问题清单
  ↓
召开评审会议
  ├─ 集中讨论争议点
  ├─ 投票表决
  └─ 形成决议
  ↓
投票结果
├─ 通过 (≥50% 赞成，无一票否决) → 进入下一阶段
├─ 有条件通过 → 跟踪行动项 → 验证完成 → 进入下一阶段
└─ 驳回 → 返工 → 重新评审
```

---

## 7. 并发与异步设计

### 7.1 并发机会识别

| 环节 | 并发策略 | 预期加速比 | 实现方式 |
|------|---------|-----------|---------|
| **DomainExpert 搜索** | 4 个业务目标并行 | 1.8x | asyncio.gather |
| **DomainExpert 内批量查询** | 每目标内并发执行 | 2.5x | Semaphore 控制 |
| **DataAnalyst 对话处理** | 单通对话完全并行 | 5-10x | 进程池/线程池 |
| **ProcessDesigner vs CustomerAdvocate** | 同步评估体验 | 1.3x | 并行执行 |
| **ToolArchitect vs JourneyBuilder** | 完全解耦并行 | 2.0x | 独立任务 |
| **总体理论加速比** | - | **3.5-5x** | - |

### 7.2 异步编程原则

**使用异步的场景**:
- ✅ IO 密集型操作 (HTTP 请求、文件读写)
- ✅ 需要并发的任务
- ✅ 等待外部响应 (LLM API)

**不使用异步的场景**:
- ❌ CPU 密集型计算 (使用进程池)
- ❌ 简单的顺序逻辑
- ❌ 需要同步状态的共享资源访问

### 7.3 并发安全

**文件写入同步**:
```python
class FileLock:
    """文件锁，防止并发写入冲突"""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.lock = asyncio.Lock()
    
    async def __aenter__(self):
        await self.lock.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.lock.release()

# 使用示例
async with FileLock("output.json"):
    await write_json("output.json", data)
```

---

## 8. 配置系统设计

### 8.1 配置分离原则

**核心思想**: 将所有可配置内容从代码中完全分离，分为两大类:

1. **参数配置** (`config/` 目录): 系统参数、模型参数、Agent 参数等
2. **Prompt 配置** (`prompts/` 目录): 所有 LLM 交互的提示词模板

```
配置体系:
├── 参数配置 (config/)
│   ├── default_config.yaml      # 默认参数
│   └── user_config.yaml         # 用户自定义参数
└── Prompt 配置 (prompts/)
    ├── domain_expert.yaml       # 领域专家 Prompt
    ├── data_analyst.yaml        # 数据分析师 Prompt
    └── ...其他 Prompt
```

### 8.2 配置层次

```
环境变量 (最高优先级)
  ↓
用户参数配置 (user_config.yaml)
  ↓
默认参数配置 (default_config.yaml)
  ↓
Prompt 配置 (prompts/*.yaml) - 独立版本管理
```

### 8.2 配置文件结构

```yaml
# config.yaml
# 文件格式：YAML
# 编码：UTF-8

system:
  workspace: "./workspace"
  log_level: "INFO"
  debug: false

llm:
  # Chat 模型配置
  chat_models:
    - name: "gpt-4"
      base_url: "https://api.openai.com/v1"
      api_key_env: "OPENAI_API_KEY"
      max_retries: 3
      timeout: 30
    
    - name: "gpt-3.5-turbo"
      base_url: "https://api.openai.com/v1"
      api_key_env: "OPENAI_API_KEY"
      max_retries: 3
      timeout: 30
  
  # Embedding 模型配置
  embedding_models:
    - name: "text-embedding-3-small"
      base_url: "https://api.openai.com/v1"
      api_key_env: "OPENAI_API_KEY"
      dimensions: 1536
  
  switch_after_failures: 3
  
  rate_limit:
    requests_per_minute: 60
    tokens_per_minute: 100000

search:
  deep_research:
    api_key_env: "DEEP_RESEARCH_API_KEY"
    max_concurrent: 5

agents:
  # Agent 并发控制
  concurrency:
    max_concurrent: 5  # >1 并行，=1 串行
  
  # Agent 特定配置
  domain_expert:
    search_depth: "deep"
    max_queries: 50
    prompt_file: "domain_expert.yaml"
  
  data_analyst:
    batch_size: 10
    checkpoint_interval: 10
    prompt_file: "data_analyst.yaml"

workflow:
  max_sprints: 6
  enable_review_board: true
  review_board_members:
    - "qa_moderator"
    - "coordinator"
    - "domain_expert"
```

### 8.3 Prompt 加载器

```python
class PromptLoader:
    """Prompt 加载和管理类"""
    
    def __init__(self, prompts_dir: str):
        self.prompts_dir = prompts_dir
        self._cache = {}  # Prompt 缓存
    
    def load(self, prompt_file: str, variables: dict = None) -> dict:
        """
        加载 Prompt 并替换变量
        
        Args:
            prompt_file: Prompt 文件路径 (相对于 prompts_dir)
            variables: 变量字典，用于替换模板中的占位符
        
        Returns:
            包含 system_prompt 和 user_prompt 的字典
        """
        # 检查缓存
        cache_key = f"{prompt_file}_{hash(str(variables))}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # 加载 YAML 文件
        full_path = os.path.join(self.prompts_dir, prompt_file)
        prompt_data = load_yaml(full_path)
        
        # 验证必需字段
        self._validate_prompt(prompt_data, prompt_file)
        
        # 替换变量
        if variables:
            self._validate_variables(prompt_data.get('variables', {}), variables)
            system_prompt = self._replace_variables(
                prompt_data['system_prompt'], 
                variables
            )
            user_prompt = self._replace_variables(
                prompt_data['user_prompt_template'], 
                variables
            )
        else:
            system_prompt = prompt_data['system_prompt']
            user_prompt = prompt_data['user_prompt_template']
        
        result = {
            'system_prompt': system_prompt,
            'user_prompt': user_prompt,
            'response_schema': prompt_data.get('response_schema'),
            'examples': prompt_data.get('examples', []),
            'metadata': prompt_data.get('metadata', {})
        }
        
        # 缓存结果
        self._cache[cache_key] = result
        return result
    
    def _replace_variables(self, template: str, variables: dict) -> str:
        """替换模板中的变量"""
        result = template
        for key, value in variables.items():
            # 支持 {key} 和 {{key}} (转义)
            placeholder = "{" + key + "}"
            if isinstance(value, list):
                value = ", ".join(map(str, value))
            result = result.replace(placeholder, str(value))
        return result
    
    def _validate_variables(self, schema: dict, provided: dict):
        """验证提供的变量是否符合 Schema"""
        for var_name, var_schema in schema.items():
            if var_schema.get('required', False) and var_name not in provided:
                raise ValueError(f"缺少必需的变量：{var_name}")
    
    def _validate_prompt(self, prompt_data: dict, prompt_file: str):
        """验证 Prompt 文件的完整性"""
        required_fields = ['metadata', 'system_prompt', 'user_prompt_template']
        for field in required_fields:
            if field not in prompt_data:
                raise ValueError(
                    f"Prompt 文件 {prompt_file} 缺少必需字段：{field}"
                )
```

### 8.4 Prompt 目录结构

```
prompts/
├── domain_expert.yaml          # 领域专家搜索 Prompt
├── data_analyst.yaml           # 数据分析师对话处理 Prompt
├── process_designer.yaml       # 流程设计师 Prompt
├── rule_engineer.yaml          # 规则工程师 Prompt
├── journey_builder.yaml        # 旅程构建师 Prompt
├── json_correction.yaml        # JSON 修正 Prompt
├── review_board_vote.yaml      # 评审团投票 Prompt
└── templates/                   # 通用模板
    ├── system_prompt_base.yaml  # 基础系统提示模板
    └── correction_base.yaml     # 基础修正提示模板
```

### 8.5 Prompt 版本管理

**版本命名规范**: `主版本号。次版本号.修订号` (如 1.0.0)

- **主版本号**: 不兼容的 API 修改
- **次版本号**: 向后兼容的功能性新增
- **修订号**: 向后兼容的问题修正

**A/B 测试支持**:

```yaml
# prompts/domain_expert_v2_test.yaml
metadata:
  name: "domain_expert_search_prompt_v2_test"
  version: "2.0.0-test"
  ab_test_group: "B"  # A/B 测试分组
  parent_version: "1.0.0"

# ... 其他内容
```

### 8.6 配置加载器

```python
class ConfigLoader:
    """配置加载器"""
    
    @staticmethod
    def load(config_path: str = None, debug: bool = False) -> Config:
        """加载配置"""
        if debug:
            # Debug 模式：使用代码中的固定配置
            return ConfigLoader._get_debug_config()
        
        # 正常模式：加载配置文件
        config_dict = {}
        
        # 1. 加载默认配置
        default_config = load_yaml("config/default_config.yaml")
        config_dict.update(default_config)
        
        # 2. 加载用户配置 (覆盖默认值)
        if config_path:
            user_config = load_yaml(config_path)
            config_dict.update(user_config)
        
        # 3. 环境变量覆盖 (最高优先级)
        config_dict = ConfigLoader._apply_env_vars(config_dict)
        
        # 4. 转换为 Pydantic 模型
        return Config(**config_dict)
    
    @staticmethod
    def _apply_env_vars(config_dict: dict) -> dict:
        """应用环境变量"""
        # 递归遍历 config_dict，替换 ${ENV_VAR} 格式的占位符
        pass
```

### 8.7 用户画像配置映射

**Parlant 官方用户群体特定指南实现**:

根据 Parlant 官方文档，支持为特定客户群体创建差异化指南:

```python
# 从用户画像生成 VIP 客户专属指南
async def create_segment_specific_guidelines(user_segments: list):
    """
    基于用户分群创建特定指南
    
    参考：Parlant 官方文档 - Customer Segments Specific Guidelines
    """
    for segment in user_segments:
        # 1. 定义基于代码的 matcher，检查客户标签
        async def segment_matcher(
            ctx: p.GuidelineMatchingContext,
            guideline: p.Guideline
        ) -> p.GuidelineMatch:
            # 检查客户是否属于该分群
            matched = segment['segment_id'] in p.Customer.current.tags
            
            return p.GuidelineMatch(
                id=guideline.id,
                matched=matched,
                rationale=f"Customer has {segment['segment_name']} tag" if matched 
                         else f"Customer does not have {segment['segment_name']} tag"
            )
        
        # 2. 使用该 matcher 创建 observation
        segment_observation = await agent.create_observation(matcher=segment_matcher)
        
        # 3. 创建仅对该群体客户激活的指南
        for guideline_config in segment['special_guidelines']:
            await agent.create_guideline(
                condition=guideline_config['condition'],
                action=guideline_config['action'],
                dependencies=[segment_observation],
                labels=[f"segment_{segment['segment_id']}"]
            )
```

**用户画像在 Parlant 中的应用场景**:

| 应用场景 | Parlant 元素 | 示例 |
|---------|-------------|------|
| **客户细分** | `Tags` + `Variables` | VIP 标签、价格敏感度评分 |
| **群体特定指南** | `Observations` + `Guidelines` | VIP 客户专属折扣指南 |
| **个性化旅程** | `Journeys` | 为新用户提供简化版预订流程 |
| **动态变量** | `Variables` + `Tools` | 实时计算用户的优惠券使用率 |
| **预设回复** | `Canned Responses` | 为价格敏感用户提供优惠导向的话术 |

**输出文件结构**:

```json
// output/user_profiles/agent_user_profiles.json
{
  "agent_id": "medical_customer_service_agent_001",
  "user_segments": [
    {
      "segment_id": "vip_customers",
      "segment_name": "VIP 客户",
      "definition": {
        "tags": ["vip", "high_value"],
        "metadata_rules": {
          "total_purchase_amount": ">10000",
          "subscription_plan": "enterprise"
        }
      },
      "behavior_patterns": [
        "偏好高效、私密的服务",
        "愿意为优质服务支付溢价"
      ],
      "special_guidelines": [
        {
          "guideline_id": "vip_exclusive_discount",
          "condition": "VIP 客户询问价格",
          "action": "提供 VIP 专属 9 折优惠",
          "priority": 8
        }
      ]
    }
  ],
  "personas": [
    {
      "persona_id": "persona_vip_001",
      "persona_name": "高端商务人士张总",
      "segment_id": "vip_customers",
      "demographics": "40-50 岁，企业高管，年收入 200 万+",
      "goals": "高效、私密、定制化服务",
      "pain_points": "时间宝贵，厌恶等待和繁琐流程",
      "behavior_patterns": [
        "偏好一对一专属服务",
        "注重隐私和效率",
        "愿意为优质服务支付溢价"
      ],
      "typical_dialogues": [
        "帮我安排最快的方案，价格不是问题"
      ],
      "parlant_mapping": {
        "tags": ["vip", "time_sensitive", "premium_service"],
        "variables": ["response_time_preference", "privacy_level"],
        "journeys": ["vip_fast_track_booking"],
        "guidelines": ["skip_price_discussion", "offer_premium_options"]
      }
    }
  ]
}
```

---

## 9. 异常处理与日志

### 9.1 异常分类

| 异常类型 | 处理方式 | 示例 |
|---------|---------|------|
| **配置错误** | 立即终止 | 配置文件不存在、格式错误 |
| **LLM API 错误** | 重试 + 切换模型 | 网络超时、RMP 超限 |
| **校验错误** | LLM 修正 | JSON Schema 不匹配 |
| **文件 IO 错误** | 重试 3 次后终止 | 磁盘满、权限不足 |
| **业务逻辑错误** | 记录并提交评审团 | 流程设计不合理 |

### 9.2 日志配置

```python
from loguru import logger
import sys

# 配置日志
logger.remove()  # 移除默认处理器

# 控制台输出
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
    colorize=True
)

# 文件输出 (按级别分割)
logger.add(
    "logs/error_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="30 days",
    level="ERROR",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)

logger.add(
    "logs/info_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="7 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)
```

### 9.3 Traceback 处理

```python
import traceback

def handle_exception(exc_type, exc_value, exc_traceback):
    """全局异常处理器"""
    if issubclass(exc_type, KeyboardInterrupt):
        return
    
    logger.critical(
        "未捕获的异常",
        exc_info=(exc_type, exc_value, exc_traceback)
    )
    logger.error(traceback.format_exception(exc_type, exc_value, exc_traceback))

# 设置为全局异常处理器
sys.excepthook = handle_exception
```

---

## 10. 测试策略

### 10.1 测试分层

```
┌─────────────────────────────┐
│   E2E 测试 (手动/自动化)      │  ← 最少
├─────────────────────────────┤
│   集成测试                   │  ← 中等
├─────────────────────────────┤
│   单元测试                   │  ← 最多
└─────────────────────────────┘
```

### 10.2 单元测试范围

**测试对象**:
- 每个 Agent 的 execute 方法
- 服务的核心方法
- 工具函数
- 配置加载器

**Mock 策略**:
```python
# 测试 Agent 时使用 Mock 的 LLM 服务
@pytest.mark.asyncio
async def test_domain_expert():
    # 准备 Mock 数据
    mock_llm_response = """
    {
        "terminologies": ["保险", "保费", "保额"],
        "processes": ["推销流程", "售后流程"]
    }
    """
    
    mock_service = Mock(LLMService)
    mock_service.chat.return_value = mock_llm_response
    
    # 创建 Agent
    agent = DomainExpert(config=config, services={"llm": mock_service})
    
    # 执行测试
    result = await agent.execute({"domain": ["保险"]})
    
    # 验证结果
    assert "terminologies" in result
    assert len(result["terminologies"]) > 0
```

### 10.3 集成测试场景

**测试场景**:
1. **Sprint 0→1 流转**: 需求分析完成后，知识挖掘能正确读取需求
2. **公域 vs 私域融合**: 验证对比标注逻辑
3. **评审团投票**: 模拟投票流程
4. **检查点恢复**: 中断后从检查点恢复

### 10.4 测试运行命令

```bash
# 运行所有测试
pytest tests/ -v

# 运行单元测试 (带覆盖率)
pytest tests/unit/ --cov=src --cov-report=html

# 运行集成测试
pytest tests/integration/ -v

# 运行特定测试
pytest tests/unit/test_domain_expert.py -v
```

---

## 11. 部署与运行

### 11.1 环境准备

**系统要求**:
- Python 3.11+
- 内存：8GB+(推荐 16GB)
- 磁盘：10GB 可用空间

**依赖安装**:
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 11.2 运行模式

#### 11.2.1 Debug 模式 (开发调试)

```bash
python main.py --debug
```

**特点**:
- 使用代码中的固定配置
- 日志级别 DEBUG
- 保存所有中间结果
- 适合断点调试

#### 11.2.2 生产模式

```bash
python main.py --config config.yaml
```

**特点**:
- 使用配置文件
- 日志级别 INFO/WARNING
- 优化性能

#### 11.2.3 阶段控制模式 (快速测试)

```bash
# 只运行 Sprint 0 (需求分析)
python main.py --config config.yaml --start-stage sprint_0 --stop-stage sprint_0

# 从 Sprint 1 开始，运行到 Sprint 2
python main.py --config config.yaml --start-stage sprint_1 --stop-stage sprint_2

# 从检查点恢复，继续运行到结束
python main.py --config config.yaml --start-stage sprint_3

# 完整运行 (默认行为)
python main.py --config config.yaml
```

**参数说明**:
- `--start-stage`: 从哪个阶段开始，可选值：`sprint_0` ~ `sprint_5`，默认 `sprint_0`
- `--stop-stage`: 到哪个阶段停止，可选值：`sprint_0` ~ `sprint_5`，默认 `sprint_5`
- 当只指定 `--start-stage` 时，会运行到结束
- 阶段名称必须有效，否则会抛出配置错误

### 11.3 运行步骤示例

**完整流程**:
```bash
# 1. 准备配置文件
cp config.example.yaml config.yaml

# 2. 编辑配置 (设置 API Key 等)
vim config.yaml

# 3. 运行系统
python main.py --config config.yaml

# 4. 查看输出
ls output/
cat logs/info_*.log
```

**从检查点恢复**:
```bash
# 从 Sprint 2 开始
python main.py --config config.yaml --checkpoint sprint_2_process_design
```

### 11.4 输出目录结构

```
output/
├── final_package/           # 最终 Parlant 配置包
│   ├── agent_config.json
│   ├── journeys.json
│   ├── rules.json
│   └── tools/
├── intermediate/            # 中间产物
│   ├── requirement_doc.json
│   ├── knowledge_base.json
│   ├── flowchart.json
│   └── ...
└── reports/                 # 报告
    ├── quality_report.json
    └── evaluation_metrics.json
```

---

## 附录

### A. 配置项完整列表

详见 `config/default_config.yaml`

### B. Agent 输入输出 Schema

详见各 Agent 的详细设计文档

### C. 错误码表

| 错误码 | 含义 | 处理方式 |
|--------|------|---------|
| E001 | 配置文件不存在 | 检查路径，创建配置文件 |
| E002 | API Key 未设置 | 设置环境变量或修改配置 |
| E003 | LLM 连续失败 | 检查网络，切换模型 |
| E004 | JSON 校验失败 | 查看日志，修正输出格式 |
| E005 | 文件 IO 错误 | 检查磁盘空间和权限 |

### D. 性能调优建议

1. **增加并发数**: 修改 `max_concurrent` 参数
2. **使用 GPU**: Embedding 服务配置 `device: "cuda"`
3. **批量处理**: 增大批次大小，减少 IO 次数
4. **缓存复用**: 启用 Embedding 缓存，避免重复计算

---

**文档维护者**: System Team  
**最后更新**: 2026-03-14  
**审阅周期**: 每次重大架构调整后审阅
