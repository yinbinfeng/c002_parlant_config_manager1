# Parlant Agent 配置挖掘系统 - 软件工程化设计要求

**版本**: v5.0 (架构设计版)  
**创建日期**: 2026-03-13  
**最后更新**: 2026-03-22  
**文档类型**: 系统架构设计（纯架构，无代码）

---

## 四、并发控制机制

### 4.1 并发模型

系统采用基于 asyncio 的异步并发模型，通过 `max_parallel_agents` 参数控制并发行为：

| 配置值 | 执行模式 | 适用场景 |
|--------|---------|---------|
| `max_parallel_agents = 1` | 完全串行 | 调试、教学演示、资源受限环境 |
| `max_parallel_agents = N (N>1)` | 分批并行 | 生产环境，根据 CPU/内存资源设定 |

### 4.2 并发策略

**标准并发策略**:
```
Step 1: 串行执行（需求澄清）
    ↓
Step 2: 串行执行（多维度分析与原子化拆解）
    ↓
Step 3: 并行执行（工作流并行开发，内部可进一步并行）
    ↓
Step 4: 串行执行（全局规则检查与优化）
    ↓
Step 5: 串行执行（配置组装与最终检查）
```

**Step 3 内部并发**:
```
For each (用户画像 × 业务流程) 组合:
    启动任务组 [ProcessAgent, GlossaryAgent, QualityAgent]
    
If max_parallel_agents > 1:
    不同组合之间完全并行
    同一组合内的 Agent 可以并行或串行（取决于剩余并发配额）
Else:
    所有组合串行执行
    同一组合内的 Agent 串行执行
```

### 4.3 资源隔离

每个 Agent 拥有独立的工作目录，避免文件冲突：

```
workspace/
├── agent_{id}_workdir/
│   ├── tmp/           # 临时文件
│   ├── findings/      # 中间发现
│   └── output/        # 最终输出
└── ...
```

---

## 五、数据流设计

### 5.1 全局数据流

```
用户输入
  ├───────────────────────┐
  ↓                       ↓
业务描述文档         Data Agent 分析结果
  ↓                       ↓
  └───────────────┬───────┘
                  ↓
         [Step 1] 需求澄清与人工确认
                  ↓ (step1_clarification_questions.md, step1_structured_requirements.md)
                  ↓
         [Step 2] 多维度分析与原子化拆解
                  ↓ (step2_dimension_analysis.json, step2_atomic_tasks.yaml)
                  ↓
         [Step 3] 工作流并行开发
                  ↓ (step3_journeys_*.json, step3_guidelines_*.json, step3_tools_*.json, step3_profiles_*.json, step3_glossary_*.json)
                  ↓
         [Step 4] 全局规则检查与优化
                  ↓ (step4_global_rules.json, step4_compatibility_report.json)
                  ↓
         [Step 5] 配置组装与最终检查
                  ↓ (parlant_agent_config/)
```

### 5.2 关键数据结构

**step1_structured_requirements.md**:
```yaml
业务目标：string
用户画像维度:
  - 画像名称：string
  - 特征描述：string
  - 专属服务策略：string
业务流程维度:
  - 流程名称：string
  - 触发条件：string[]
  - 状态列表：string[]
所需规约:
  - 规约类型：global/sop_specific
  - 适用维度：string
工具需求:
  - 工具名称：string
  - 功能描述：string
  - 输入输出：object
专有词汇:
  - 术语名称：string
  - 定义：string
  - 同义词：string[]
```

**step2_atomic_tasks.yaml**:
```yaml
tasks:
  - task_id: string
    agent: string (Agent 类型)
    dimension: string (用户画像×业务流程)
    description: string
    dependencies: string[] (task_id 列表)
    expected_output_schema: object
```

---

## 六、控制流设计

### 6.1 主控制流

```
初始化
  ↓
加载配置文件（system_config.yaml）
  ↓
解析 start_step / end_step 参数
  ↓
for step_num in range(start_step, end_step + 1):
  ↓
  检查该步骤是否已完成（存在且未设置 force_rerun）
    ↓
  如果已完成：跳过
  如果未完成：执行步骤
    ↓
  保存步骤结果（StepManager.save_step_result）
    ↓
  记录执行日志
  ↓
所有步骤完成
  ↓
生成执行报告
```

### 6.2 异常处理机制

**Step 执行失败**:
1. 记录错误日志到 `step{num}_error.log`
2. 保存当前中间状态（便于恢复）
3. 根据配置决定是否继续后续步骤：
   - `continue_on_error = true`: 跳过失败步骤，继续执行
   - `continue_on_error = false`: 终止执行

**JSON 校验失败**（Step 5）:
1. 尝试使用 json_repair 自动修复
2. 如果自动修复失败，调用 Agent 进行修正
3. 最多重试 3 次，仍失败则记录错误并跳过该文件

**Deep Research 超时**:
1. 设置单次搜索超时（默认 5 分钟）
2. 超时后记录已获取的部分结果
3. 继续执行后续流程（不阻塞整体进度）

### 6.3 目标对齐机制

为防止 Agent 在长链条执行中偏离总目标，采用以下机制：

1. **全局目标文件**: CoordinatorAgent 在 Step 2 完成后写入 `global_objective.md`，包含：
   - 业务目标摘要
   - 核心约束条件
   - 预期输出格式

2. **Prompt 约束**: 每个 Agent 的系统 Prompt 中包含：
   - 总目标描述
   - 具体任务描述
   - 输出前自检问题

3. **循环校验**: 每次输出前，Agent 需回答自检问题，如不符合则重新生成

---

## 七、工具服务设计

### 7.1 工具服务架构

所有工具通过 MCP（Model Context Protocol）协议提供统一接口：

```
┌──────────────────────────────────────────────┐
│              MCP Client (AgentScope)          │
├──────────────────────────────────────────────┤
│  deep_research_search   (深度研究搜索)        │
│  tavily-search          (基础网页搜索)        │
│  tavily-extract         (网页内容提取)        │
│  write_text_file        (文件写入)            │
│  read_text_file         (文件读取)            │
│  compute_embedding      (Embedding 向量计算)   │
│  compute_similarity     (余弦相似度计算)       │
│  repair_json            (JSON 格式修复)        │
└──────────────────────────────────────────────┘
```

**Deep Research Agent 封装说明**:

系统使用 AgentScope 官方提供的 `DeepResearchAgent` 封装为高级工具 `deep_research_search`，供其他 Agent 调用。

**封装方式**:
- 基于 `DeepResearchAgent`（位于 `agentscope_docs/examples/agent/deep_research_agent/`）
- 继承自 `ReActAgent`，具备多步推理和工具使用能力
- 内置子任务分解、Follow-up 判断、反思机制
- 自动调用 Tavily MCP 进行深度搜索和内容提取
- 支持中间结果总结和最终报告生成
- 内置失败反思和策略调整机制

**核心功能**:
1. **子任务分解**：将复杂查询分解为可管理的子任务
2. **智能搜索**：基于子任务执行多轮搜索
3. **Follow-up 机制**：自动判断是否需要深入搜索特定链接
4. **结果总结**：将搜索结果总结为结构化报告
5. **失败反思**：当搜索遇到困难时自动调整策略
6. **报告生成**：生成详细的最终研究报告

**使用方式**:
```python
# 在业务 Agent 中初始化 Deep Research 工具
from agentscope.agent import DeepResearchAgent
from agentscope.mcp import StdIOStatefulClient
from agentscope.memory import InMemoryMemory
from agentscope.message import Msg

# 创建 Tavily MCP 客户端
tavily_client = StdIOStatefulClient(
    name="tavily_mcp",
    command="npx",
    args=["-y", "tavily-mcp@latest"],
    env={"TAVILY_API_KEY": api_key},
)
await tavily_client.connect()

# 创建 DeepResearchAgent 实例
deep_researcher = DeepResearchAgent(
    name="DeepResearchWorker",
    model=dashscope_model,
    formatter=dashscope_formatter,
    memory=InMemoryMemory(),
    search_mcp_client=tavily_client,
    tmp_file_storage_dir="./tmp/deep_research",
    max_depth=3,  # 最大搜索深度
    max_iters=30,  # 最大迭代次数
    max_tool_results_words=10000,  # 工具结果最大字数
)

# 作为工具被其他 Agent 调用
async def call_deep_research(query: str) -> str:
    result = await deep_researcher(Msg("user", query, "user"))
    return result.get_text_content()
```

**与其他工具的区别**:
| 工具 | 能力层级 | 适用场景 |
|------|---------|---------|
| `deep_research_search` | 高级工具（多步推理） | 复杂调研任务，需要多轮搜索和信息整合 |
| `tavily-search` | 基础工具（单步搜索） | 简单事实查询，快速获取网页结果 |

**推荐使用时机**:
- Step 1: 需求澄清 - 使用 `deep_research_search` 搜索行业最佳实践
- Step 2: 需求辩论 - 使用 `deep_research_search` 提供行业标准证据
- Step 3: 工作流并行开发 - 各 Agent 可根据需要多次调用 `deep_research_search`
- Step 4: 全局规则检查与优化 - 使用 `deep_research_search` 并发搜索多个角度

### 7.2 核心工具说明

| 工具名 | 提供方 | 用途 | 输入 | 输出 |
|--------|--------|------|------|------|
| `deep_research_search` | AgentScope DeepResearchAgent | 深度研究搜索（多步推理） | query, max_depth | 综合研究报告（结构化文本） |
| `tavily-search` | Tavily MCP | 基础网页搜索 | query, search_depth | 搜索结果列表（标题 + 摘要+URL） |
| `tavily-extract` | Tavily MCP | 网页内容提取 | urls[], extract_depth | 网页正文内容 |
| `write_text_file` | Local FS | 文件写入 | file_path, content | 写入结果（成功/失败） |
| `read_text_file` | Local FS | 文件读取 | file_path | 文件内容 |
| `repair_json` | json_repair | JSON 格式修复 | invalid_json_string | 修复后的 JSON 字符串 |

### 7.3 工具调用规范

所有 Agent 遵循统一的工具调用规范：

1. **工具注册**: 在 Agent 初始化时注册所需工具
2. **工具调用**: 通过统一接口调用工具
3. **结果处理**: 所有工具返回标准响应对象，包含内容和元数据

---

## 八、配置管理设计

### 8.1 配置文件结构

```
config/
├── system_config.yaml         # 系统级配置
├── agents/
│   ├── coordinator.yaml       # CoordinatorAgent 配置
│   ├── requirement_analyst.yaml
│   ├── rule_engineer.yaml
│   └── ...
└── prompts/
    ├── requirement_analysis.yaml
    ├── task_decomposition.yaml
    ├── rule_generation.yaml
    └── ...
```

### 8.2 关键配置项

**system_config.yaml**:
```yaml
max_parallel_agents: 4        # 最大并发 Agent 数（1=串行）
start_step: 1                 # 起始步骤（1-5）
end_step: 5                   # 结束步骤（1-5）
force_rerun: false            # 是否强制重跑已完成的步骤
continue_on_error: false      # 错误时是否继续执行

output_base_dir: "./output"   # 输出目录
enable_version_control: true  # 是否启用 Git 版本管理

mcp_clients:
  tavily_search:
    enabled: true
    api_key_env: TAVILY_API_KEY
  embedding_service:
    type: SentenceTransformer
    model_name: paraphrase-multilingual-MiniLM-L12-v2

json_validation:
  max_retries: 3              # JSON 校验最大重试次数
  auto_fix: true              # 是否启用自动修复

agent_correction:
  max_correction_attempts: 3  # Agent 最大修正次数
  auto_correct: true          # 是否启用自动修正
```

**Agent 配置**:
```yaml
agent_name: RuleEngineerAgent
base_class: ReActAgent
description: string

model:
  type: DashScopeChatModel
  config:
    model_name: qwen3-max
    temperature: 0.7

tools:
  - deep_research_search
  - write_text_file
  - read_text_file

system_prompt_template: prompts/rule_generation.yaml
output_schema: ParlantRulesSchema
```

---

## 九、输出产物设计

### 9.1 中间产物（每步输出）

| 步骤 | 文件名 | 格式 | 用途 | 可选性 |
|------|--------|------|------|--------|
| Step 1 | step1_clarification_questions.md | Markdown | 待用户澄清的问题清单 | 必需 |
| Step 1 | step1_structured_requirements.md | Markdown | 结构化的需求规格说明 | 必需 |
| Step 2 | step2_dimension_analysis.json | JSON | 维度分析结果 | 必需 |
| Step 2 | step2_atomic_tasks.yaml | YAML | 原子化任务列表 | 必需 |
| Step 3 | step3_journeys_*.json | JSON | 流程定义（符合 Parlant Journey 格式） | 必需 |
| Step 3 | step3_guidelines_*.json | JSON | 规约定义（符合 Parlant Guideline 格式） | 必需 |
| Step 3 | step3_tools_*.json | JSON | 工具定义（符合 Parlant Tool 格式） | 必需 |
| Step 3 | step3_profiles_*.json | JSON | 用户画像定义（符合 Parlant Customer 格式） | 必需 |
| Step 3 | step3_glossary_*.json | JSON | 词汇定义（符合 Parlant Glossary 格式） | 必需 |
| Step 3 | step3_correction_history.json | JSON | 修正历史记录 | 必需 |
| Step 4 | step4_global_rules.json | JSON | 全局规则配置 | 必需 |
| Step 4 | step4_compatibility_report.json | JSON | 兼容性检查报告 | 必需 |
| Step 5 | step5_assembly_report.md | Markdown | 组装报告 | 必需 |
| Step 5 | step5_validation_report.md | Markdown | 验证报告 | 必需 |

**Step 1 输入说明**:
- **业务描述文档**: 人工提供的业务背景、流程描述、目标客群等信息
- **Data Agent 分析结果**: 外部离线生成的私域对话数据结果，仅包含每个流程 journey 文件的名称与描述字段

**Step 5 验证报告的差异标注**:
```markdown
# 配置包验证报告

## 数据来源
- ✅ 互联网搜索（Deep Research）：已处理
- ✅ 外部 Data Agent 分析结果：已处理

## 检查范围
本次验证基于业务描述文档和 Data Agent 分析结果产生的规则和词汇...
```

### 9.2 最终产物（Parlant 配置包）

```
output/parlant_agent_config/
├── agents/
│   └── {agent_name}/
│       ├── 00_agent_base/
│       │   ├── agent_metadata.json
│       │   ├── agent_observability.json
│       │   ├── agent_user_profiles.json
│       │   └── glossary/
│       ├── 01_agent_rules/
│       │   ├── agent_guidelines.json
│       │   ├── agent_observations.json
│       │   └── agent_canned_responses.json
│       ├── 02_journeys/
│       │   └── {journey_name}/
│       │       ├── sop.json
│       │       ├── sop_guidelines.json
│       │       └── sop_observations.json
│       └── 03_tools/
│           └── {tool_name}/
│               ├── tool_meta.json
│               └── tool_impl.py
└── automation/
    └── build_agent.py
```

### 9.3 产物质量标准

所有输出产物需满足以下质量标准：

| 产物类型 | 质量指标 | 校验方法 |
|----------|---------|---------|
| JSON 文件 | 符合 Parlant schema | json_repair + jsonschema 校验 |
| Markdown 文件 | 结构清晰、无乱码 | 人工可读性检查 |
| Python 代码 | 语法正确、可导入 | Python AST 解析 + 试导入 |
| 配置文件 | YAML 格式正确 | yaml.safe_load 校验 |

---

## 十、扩展性与维护性

### 10.1 扩展点设计

| 扩展点 | 扩展方式 | 影响范围 |
|--------|---------|---------|
| 新增 Agent 类型 | 继承 AgentScope 的 Agent 基类，实现特定逻辑 | 需在 Step 2 的任务分配逻辑中注册 |
| 新增工具 | 实现 MCP 兼容的工具接口，注册到 toolkit | 需在 Agent 配置中添加工具引用 |
| 新增加密步骤 | 在 StepManager 中注册新的 step handler | 需定义输入输出 schema |
| 更换 LLM 提供商 | 修改 system_config.yaml 中的 model 配置 | 无需修改代码 |
| 更换 Embedding 模型 | 修改 system_config.yaml 中的 embedding_service 配置 | 无需修改代码 |

### 10.2 维护性保障

1. **配置与代码分离**: 所有 Prompt、Agent 配置、系统配置均在 YAML 文件中，修改无需改代码
2. **模块化设计**: 每个 Agent 职责单一，便于单独维护和测试
3. **日志与监控**: 完整的执行日志和状态监控，便于问题定位
4. **版本控制**: 内置 Git 版本管理，支持配置回滚和变更追踪
5. **文档完备性**: 详细的设计文档和使用说明，降低维护成本

---

**最后更新**: 2026-03-22  
**维护者**: System Team