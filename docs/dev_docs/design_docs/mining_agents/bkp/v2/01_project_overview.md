# Parlant Agent 配置挖掘系统 - 架构设计文档

**版本**: v5.0 (架构设计版)  
**创建日期**: 2026-03-13  
**最后更新**: 2026-03-22  
**文档类型**: 系统架构设计（纯架构，无代码）

---

## 一、系统定位与设计目标

### 1.1 系统定位

本系统是一个基于 AgentScope 框架的多 Agent 协作系统，用于自动化生成 Parlant 客服 Agent 的完整配置包。系统通过流水线协作，从人工提供的业务描述文档和外部 Data Agent 分析生成的私域对话数据结果中挖掘并生成符合 Parlant 规范的结构化配置。

### 1.2 设计目标

| 目标 | 说明 |
|------|------|
| **自动化挖掘** | 从互联网（Deep Research）和外部 Data Agent 分析结果中自动提取配置信息 |
| **协作化生产** | 多个专业 Agent 分工协作，模拟人类咨询团队的工作模式 |
| **可追溯输出** | 每步独立存储，支持断点续跑、快速重启特定阶段 |
| **灵活并发** | 支持串行/并行模式切换，通过配置控制并发数 |
| **格式校验** | 内置 json_repair 校验机制，确保输出符合 Parlant schema |

---

## 二、系统总体架构

### 2.1 顶层架构图（优化版）

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           用户输入层                                     │
│  ┌─────────────┐    ┌──────────────────────┐    ┌──────────────┐       │
│  │ 业务描述文本 │    │ Data Agent 分析结果  │    │ 配置参数 YAML │       │
│  │ (人工提供)   │    │ (外部离线生成)        │    │              │       │
│  └─────────────┘    └──────────────────────┘    └──────────────┘       │
└─────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                      AgentScope 编排层                                   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                  StepManager（步骤管理器）                       │   │
│  │   - 步骤调度  - 状态持久化  - 断点续跑  - 结果加载                │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                  ↓                                       │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │               AgentOrchestrator（Agent 编排器）                   │   │
│  │   - 并发控制  - 任务分发  - 资源隔离  - 冲突仲裁                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                  ↓                                       │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │              Human-in-the-Loop Interface                         │   │
│  │   - 人工确认  - 反馈收集  - 修改审核  - 超时处理                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    Agent 协作层（多步流程）                               │
│                                                                          │
│  Step 1         Step 2         Step 3                                   │
│  需求澄清     → 多维度分析与原子化拆解 → 工作流并行开发                   │
│  +人工确认     +多 Agent 辩论         +三 Agent 协作                    │
│               +Deep Research          +流程/词汇/质检                    │
│                                                                          │
│  Step 4         Step 5                                                  │
│  全局规则检查与优化 → 配置组装与最终检查                                 │
│  +兼容性检查        +格式校验                                           │
│  +规则精简          +目录组装                                           │
└─────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                        工具服务层（MCP 协议）                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │DeepSearch│  │FileSystem│  │JsonRepair│               │
│  │(Tavily)  │  │(本地文件) │  │(格式校验) │               │
│  └──────────┘  └──────────┘  └──────────┘               │
│  ┌──────────┐  ┌──────────┐                                           │
│  │Debate    │  │HumanLoop │                                           │
│  │(辩论框架) │  │(人工介入) │                                           │
│  └──────────┘  └──────────┘                                           │
└─────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                        输出产物层                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  Parlant 配置包（agents/{agent_name}/...）                        │  │
│  │  ├── 00_agent_base/ (元数据、术语表、用户画像)                     │  │
│  │  ├── 01_agent_rules/ (全局规则、观测、话术)                        │  │
│  │  │   └── 注入 chat_state 和 condition 判定逻辑                      │  │
│  │  ├── 02_journeys/ (SOP 流程、状态机)                               │  │
│  │  │   └── 原子化设计 + 完整分支条件                                 │  │
│  │  └── 03_tools/ (工具元数据、实现代码)                              │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  过程产物（可追溯）                                               │  │
│  │  ├── step1_clarification_questions.md (+用户反馈记录)             │  │
│  │  ├── step1_structured_requirements.md                            │  │
│  │  ├── step2_dimension_analysis.json                               │  │
│  │  ├── step2_atomic_tasks.yaml                                     │  │
│  │  ├── step3_journeys_*.json (流程定义，符合 Parlant Journey 格式)   │  │
│  │  ├── step3_guidelines_*.json (规约定义，符合 Parlant Guideline 格式) │  │
│  │  ├── step3_tools_*.json (工具定义，符合 Parlant Tool 格式)         │  │
│  │  ├── step3_profiles_*.json (用户画像定义，符合 Parlant Customer 格式) │  │
│  │  ├── step3_glossary_*.json (词汇定义，符合 Parlant Glossary 格式)   │  │
│  │  ├── step3_qa_report_*.json (质检报告)                           │  │
│  │  ├── step4_global_rules.json                                     │  │
│  │  ├── step4_compatibility_report.json                             │  │
│  │  ├── step5_assembly_report.md                                    │  │
│  │  └── step5_validation_report.md                                  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 核心组件说明（优化版）

| 组件 | 职责 | 关键特性 |
|------|------|----------|
| **StepManager** | 步骤调度与状态管理 | 每步落盘、支持 `--start-step`/`--end-step` 参数跳过已完成阶段 |
| **AgentOrchestrator** | Agent 编排与并发控制 | 根据 `max_parallel_agents` 配置决定串行/并行执行策略 |
| **Human-in-the-Loop Interface** | 人工确认与反馈收集 | Step 1 后暂停等待用户确认、支持修改/补充问题、超时处理 |
| **Multi-Agent Debate Framework** | 多 Agent 辩论组织 | Step 2 使用、分析未覆盖的用户角色/业务场景/边缘情况、辩论记录可追溯 |
| **ProcessAgent** | 流程设计 | Step 3 使用、设计具体业务流程、制定相关规约、选择适用工具、构建用户画像 |
| **GlossaryAgent** | 词汇体系设计 | Step 3 使用、提取和定义专业术语体系 |
| **QualityAgent** | 质量检查 | Step 3 使用、设计明确的检查指标、对所有设计内容进行逻辑合理性验证 |
| **GlobalRulesAgent** | 全局规则检查与优化 | Step 4 使用、检查全局规则与各子流程规约的兼容性、保持全局规则的精简性 |
| **工具服务层** | 统一工具接口（MCP 协议） | Deep Research、文件系统、JSON 校验、Debate、HumanLoop |
| **输出产物层** | Parlant 配置包 + 过程产物 | 符合官方 schema、注入 chat_state/condition、原子化旅程、过程产物可追溯 |

---

## 三、多 Agent 协作流程设计

### 3.1 多步协作流程总览（优化版）

```
【Step 1】需求澄清 + 人工确认
    结合人工提供的业务描述文档和 Data Agent 分析结果 → 生成待澄清问题 → 用户确认 → 记录反馈
    ↓
【Step 2】多维度分析与原子化拆解
    多 Agent 辩论 + Deep Research → 分析用户角色/业务场景/边缘情况 → 原子化任务列表
    ↓
【Step 3】工作流并行开发
    三 Agent 协作：流程 Agent + 词汇 Agent + 质检 Agent → 输出各工作流配置
    ↓
【Step 4】全局规则检查与优化
    全局规则 Agent → 兼容性检查 + 规则精简 → 输出全局规则配置
    ↓
【Step 5】配置组装与最终检查
    组装所有内容 → 格式校验 → 输出完整 Parlant 配置包
```

### 3.2 各步骤详细设计

#### Step 1: 需求澄清与人工确认

**定位**: Step 1 是**连接外部分析与在线交互的桥梁**，结合人工提供的业务描述文档和外部 Data Agent 分析生成的私域对话数据结果，生成待澄清问题，等待用户确认。

**输入**: 
- 人工提供的业务描述文档（业务背景、流程描述、目标客群等）
- Data Agent 分析生成的私域对话数据结果（仅包含每个流程 journey 文件的名称与描述字段）

**处理逻辑**:
1. **需求分析**：分析人工提供的业务描述文档，识别关键信息缺口
   - 业务目标和范围
   - 目标客户群体
   - 核心业务流程
   - 服务边界和约束

2. **结合 Data Agent 分析结果**：
   - 分析 Data Agent 提供的流程 journey 文件名称与描述
   - 对比业务描述文档与 Data Agent 分析结果的一致性
   - 识别需要用户确认的差异点
   - 补充业务描述中未提及但重要的细节

3. **生成澄清问题**：
   - 针对模糊或不完整的业务需求提出问题
   - 针对 Data Agent 分析发现的潜在流程寻求确认
   - 针对边缘情况和异常处理征询意见

4. **人工确认**（Human-in-the-Loop）：
   - 暂停流程，等待用户回复
   - 收集用户对问题的澄清反馈
   - 支持用户修改或补充问题
   - 超时处理（默认超时时间可配置）

5. **文件输出**：
   - 写入 `step1_clarification_questions.md`（包含生成的问题和用户反馈）
   - 写入 `step1_structured_requirements.md`（结构化的需求规格说明）

**输出**: 
- 待澄清问题文件（Markdown 格式）
- 用户需求反馈记录（Markdown 格式）
- 结构化需求规格说明（Markdown 格式）

**关键决策点**:
- 问题数量的控制（避免过多问题导致用户疲劳）
- 问题优先级的排序（先问核心问题，再问细节）
- 人工确认的超时策略（默认 30 分钟，可配置）
- Data Agent 分析结果的权重（数据分析 vs 人工描述的优先级）

**Parlant 规范符合性检查**:
- 结构化需求必须映射到 Parlant 配置元素
- 所有模糊表述必须被澄清为精确的条件判定
- 用户反馈必须被完整记录并追踪

---

#### Step 2: 多维度分析与原子化拆解（CoordinatorAgent）

**定位**: 从 Step 2 开始，进入**详细的执行阶段**，将结构化的需求分解为原子化的任务单元。

**输入**: 
- `step1_structured_requirements.md`（结构化的需求规格说明）
- `step1_clarification_questions.md`（含用户反馈）

**处理逻辑**:
1. **维度拆解**：按照"用户画像 × 业务流程"矩阵生成任务组合
   - 识别所有用户角色类型
   - 识别所有业务流程节点
   - 生成用户角色与流程的组合矩阵

2. **Deep Research 增强**（可选）：
   - 针对每个维度调用 Deep Research 搜索行业最佳实践
   - 收集类似业务的常见场景和边缘情况
   - 补充用户需求中未明确但重要的维度

3. **多 Agent 辩论**（Multi-Agent Debate）：
   - 不同角色的 Agent 代表不同的视角（如：用户体验视角、业务效率视角、合规视角）
   - 对任务分解的合理性进行辩论
   - 记录辩论过程和最终决策理由

4. **任务分配**：为每个任务指定执行 Agent、依赖关系、预期输出
   - 确定任务的执行顺序（哪些可以并行，哪些必须串行）
   - 为每个任务分配合适的专业 Agent
   - 定义任务的输入输出规范

5. **文件输出**：写入 `step2_atomic_tasks.yaml`
   - task_id: 任务唯一标识
   - agent: 执行 Agent 名称
   - dimension: 所属维度（用户画像×业务流程）
   - description: 任务详细描述
   - dependencies: 依赖的任务 ID 列表
   - expected_output: 预期输出格式

**输出**: 
- 任务分解文件（YAML 格式）
- 维度分析报告（JSON 格式）
- 多 Agent 辩论记录（Markdown 格式）

**关键决策点**:
- 任务粒度的控制（过粗导致执行困难，过细增加协调成本）
- 任务依赖关系的确定（基于数据依赖和执行顺序）
- Agent 选择的策略（根据任务类型匹配最合适的 Agent）
- 辩论终止条件（达成一致或达到最大轮数）

---

#### Step 3: 工作流并行开发（ProcessAgent + GlossaryAgent）

**输入**: 
- `step1_structured_requirements.md`（结构化的需求规格说明）
- `step2_atomic_tasks.yaml`（原子化任务列表）

**参与 Agent**:
- **ProcessAgent**（流程设计）：设计具体业务流程、制定相关规约、选择适用工具、构建用户画像
- **GlossaryAgent**（词汇体系设计）：提取和定义专业术语体系

**处理逻辑**:

1. **并行开发**：
   - ProcessAgent 设计业务流程和状态机
   - GlossaryAgent 提取和定义专业术语

2. **流程设计**（ProcessAgent）：
   - 基于 Step 2 的原子化任务列表，设计具体的业务流程
   - 制定相关规约和规则
   - 选择适用的工具
   - 构建用户画像
   - 确保流程的原子化设计，每个流程聚焦单一核心目标
   - **Loop 检查和修正**：
     - 对设计结果进行自检，检查是否符合 Parlant 规范
     - 如果发现问题，自动进行修正
     - 最多修正次数：可配置（默认 3 次）
     - 记录修正历史和决策依据

3. **词汇体系设计**（GlossaryAgent）：
   - 从业务描述和 Data Agent 分析结果中提取专业术语
   - 定义术语的标准含义和使用场景
   - 建立术语之间的关联关系
   - **Loop 检查和修正**：
     - 对词汇定义进行自检，检查准确性和一致性
     - 如果发现问题，自动进行修正
     - 最多修正次数：可配置（默认 3 次）
     - 记录修正历史和决策依据

4. **文件输出**：
   - `step3_journeys_*.json`（流程定义，符合 Parlant Journey 格式）
   - `step3_guidelines_*.json`（规约定义，符合 Parlant Guideline 格式）
   - `step3_tools_*.json`（工具定义，符合 Parlant Tool 格式）
   - `step3_profiles_*.json`（用户画像定义，符合 Parlant Customer 格式）
   - `step3_glossary_*.json`（词汇定义，符合 Parlant Glossary 格式）
   - `step3_correction_history.json`（修正历史记录）

**输出**: 
- 各专项配置（规则、词汇、工具、旅程）
- 用户画像分群及行为模式（JSON 格式）
- 画像到规则的映射关系（JSON 格式）
- 修正历史记录（JSON 格式）

**关键决策点**:
- 并发数的控制（受 `max_parallel_agents` 限制）
- 目标一致性的维护（如何防止 Agent 偏离总目标）
- 冲突检测（不同画像的专属规则是否冲突）
- 用户画像特征的提取精度（基于规则 vs 基于 Embedding 聚类）
- 旅程原子化的粒度（单一目标 vs 复合目标）
- 分支条件的完备性（覆盖所有可能的用户行为）
- 修正次数的配置（默认 3 次，可根据需求调整）
- 修正策略的选择（自动修正 vs 人工介入）

**Parlant 规范符合性检查**:
- 所有 guideline 必须包含 `chat_state` 字段
- journey 的每个节点必须定义清晰的进入/退出条件
- 状态转换必须形成 DAG，避免死循环
- 工具定义必须包含 input_schema 和 output_schema

---

#### Step 4: 全局规则检查与优化（GlobalRulesAgent）

**输入**: 
- `step1_structured_requirements.md`（结构化的需求规格说明）
- `step3_journeys_*.json`（流程定义）
- `step3_guidelines_*.json`（规约定义）

**参与 Agent**:
- **GlobalRulesAgent**（主责）：全局规则检查与优化

**处理逻辑**:

1. **全局规则检查**：
   - 检查全局规则与各子流程规约的兼容性
   - 确保全局规则的精简性和一致性
   - 识别并解决规则冲突

2. **规则优化**：
   - 精简冗余规则
   - 优化规则优先级
   - 确保规则的可执行性和准确性

3. **兼容性检查**：
   - 检查不同流程之间的规则兼容性
   - 确保规则在不同场景下的一致性
   - 验证规则与 Parlant 规范的符合性

4. **文件输出**：
   - `step4_global_rules.json`（全局规则配置）
   - `step4_compatibility_report.json`（兼容性检查报告）

**输出**: 
- 全局规则配置（JSON 格式，符合 Parlant schema）
- 兼容性检查报告（JSON 格式）

**关键决策点**:
- 搜索角度的选择（覆盖全局规则的各个维度）
- 优先级设定（priority 范围 1-15）
- 排除/依赖关系的设计（避免循环依赖）
- chat_state 的粒度控制（过粗导致规则冲突，过细增加复杂度）
- condition 判定的精确性（避免模糊匹配导致的误触发）

**Parlant 规范符合性检查**:
- 所有 guideline 必须包含明确的 `chat_state` 字段
- condition 必须使用标准布尔表达式（支持 AND/OR/NOT）
- 状态转换必须形成有向无环图（DAG），避免死循环

---

#### Step 5: 配置组装与最终检查（ConfigAssemblerAgent）

**输入**: 
- `step3_journeys_*.json`（流程定义）
- `step3_guidelines_*.json`（规约定义）
- `step3_tools_*.json`（工具定义）
- `step3_profiles_*.json`（用户画像定义）
- `step3_glossary_*.json`（词汇定义）
- `step4_global_rules.json`（全局规则配置）

**处理逻辑**:

1. **目录组装**：
   - 按照 Parlant 官方要求的目录结构组织文件
   - 确保所有配置文件放在正确的目录中

2. **格式校验**：
   - 使用 json_repair 库检查 JSON 格式
   - 确保所有配置文件符合 Parlant schema

3. **质量检查**：
   - 检查规则之间的排除关系是否循环依赖
   - 检查 Journey 状态机的转移是否有死胡同
   - 检查工具调用的输入输出是否匹配
   - 检查 chat_state 定义是否一致、无歧义
   - 检查 condition 判定逻辑是否存在矛盾

4. **冲突检测**：
   - 检查同一场景下是否存在矛盾的规则
   - 检查全局规则与流程专属规则是否冲突

5. **最终组装**：
   - 整合所有配置文件
   - 生成完整的 Parlant 配置包

6. **文件输出**：
   - `step5_assembly_report.md`（组装报告）
   - `step5_validation_report.md`（验证报告）
   - 完整的 Parlant 配置包（目录结构符合官方规范）

**输出**: Parlant 配置包（目录结构符合官方规范）

**关键决策点**:
- 校验失败的修正策略（自动修复 vs Agent 修正）
- 重试次数的上限（避免无限循环）

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
    
如果 max_parallel_agents > 1:
    不同组合之间完全并行
    同一组合内的 Agent 可以并行或串行（取决于剩余并发配额）
否则:
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
- 内置子任务分解、 Follow-up 判断、反思机制
- 自动调用 Tavily MCP 进行深度搜索

**使用方式**:
```python
# 在业务 Agent 中初始化 Deep Research 工具
from agentscope.agent import DeepResearchAgent
from agentscope.mcp import StdIOStatefulClient

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