# Parlant Agent 配置挖掘系统 - 设计文档索引 (v2)

**版本**: v2.0 (8 步法架构版)  
**创建日期**: 2026-03-30  
**最后更新**: 2026-04-06  
**文档类型**: 系统架构设计（纯架构，无代码）

---

## 📋 优化概述

### 一句话总结

本设计方案将当前的**5 步线性流程**升级为**8 步并行流程**,引入**中枢管控 Agent**和**3 层 SOP 架构**,实现执行效率提升 50%+,输出质量标准化 100%。

### 核心问题分析

通过深入分析，识别出当前系统存在的 7 大类问题:

| 问题类别 | 具体问题 | 优先级 |
|---------|---------|--------|
| **流程设计** | Step 2-5 过于线性，缺乏并行优化 | 🔴 高 |
| **架构设计** | 缺少 3 层 SOP 架构支持 (主干/分支/子弹) | 🔴 高 |
| **Agent 职责** | 缺少中枢管控 Agent，全局规则管理分散 | 🔴 高 |
| **并发控制** | 仅支持对话维度并发，轮次内并发未实现 | 🟡 中 |
| **配置规范** | Parlant 配置样例缺失，提示词缺少字段说明 | 🔴 高 |
| **工具调用** | Deep Research 未强制调用，依赖样例数据 | 🟡 中 |
| **工程化** | 日志使用 Print，错误处理不完善 | 🟡 中 |

### 优化方案设计

#### 1. 流程重构：5 步 → 8 步

```
Step 1: 需求澄清 + 人工确认
    ↓
Step 2: 目标对齐与主 SOP 主干挖掘 (新增)
    ↓
Step 3: 全局规则挖掘 (可并行 Step 4)
    ↓
Step 4: 用户画像挖掘 (可并行 Step 3)
    ↓
Step 5: 二级分支 SOP 并行挖掘 (核心优化点)
    ↓
Step 6: 边缘场景挖掘 (新增)
    ↓
Step 7: Parlant 配置组装
    ↓
Step 8: 最终校验与输出
```

**关键收益**:
- ✅ Step 3-6 可并行率≥70%
- ✅ 新增 Step 2 防止 Agent 偏离主题
- ✅ 新增 Step 6 实现全场景覆盖 100%

#### 2. 中枢管控机制

**新增 Agent**:
- `CoordinatorAgent`: 全局目标对齐 + 多 Agent 辩论组织
- `MainSOPMiningAgent`: 主 SOP 主干挖掘 (严格 5-9 节点)
- `GlobalRulesAgent`: 全局规则与合规管控
- `UserProfileAgent`: 用户画像挖掘
- `BranchSOPAgent`: 二级分支 SOP 挖掘 (遵守 1+2 铁律)
- `EdgeCaseSOPAgent`: 边缘场景子弹 SOP 挖掘

**核心机制**:
- 🎯 Step 2 组织多 Agent 辩论，确定业务价值和主 SOP 范围
- 🎯 写入 `global_objective.md` 防止后续偏离
- 🎯 合规拥有一票否决权

#### 3. 3 层 SOP 架构支持

```
第一层：一级主 SOP (主干层)
├─ 5-9 个节点，无分支
├─ 仅使用「核心主意图 + 业务流程节点」2 个维度
└─ 冻结后禁止修改

第二层：二级分支 SOP (适配层)
├─ 依附于主 SOP 节点
├─ 遵守 1+2 铁律 (1 个核心区分维度 + 最多 2 个补充适配维度)
└─ 单节点≤5 个分支

第三层：三级子弹 SOP (补全层)
├─ 边缘异常场景原子化补全
├─ 1 场景 1SOP，插件式设计
└─ 可独立插拔，不影响主流程复杂度
```

#### 4. Deep Research 强制调用

- ✅ 每个 Journey 至少调用 3 次 Deep Research
- ✅ 搜索话题拆分为小方向并发搜索
- ✅ 研究报告存入 `step{N}_research_reports/`
- ✅ 所有规则和术语必须标注来源

#### 5. 工程化改进

- ❌ Print → ✅ logrus
- 结构化日志，便于问题定位
- 支持日志分级和文件轮转
- 完善的重试机制
- 单元测试覆盖率≥80%

### 新旧方案对比

| 维度 | 旧方案 (v5.0) | 新方案 (v6.0) | 提升幅度 |
|------|-------------|-------------|---------||
| **流程步骤** | 5 步线性 | 8 步 (支持并行) | +60% 步骤，+70% 并行率 |
| **中枢管控** | ❌ 无 | ✅ CoordinatorAgent | 防止偏离主题 |
| **SOP 架构** | ❌ 不明确 | ✅ 3 层架构 | 粒度解耦 |
| **并发控制** | 对话维度 | 多维度并发 | 性能提升 50%+ |
| **Deep Research** | ❌ 依赖样例 | ✅ 强制调用 | 信息充分性↑ |
| **日志系统** | Print | logrus | 可维护性↑ |
| **错误处理** | 基础 | 完善的重试 + 降级 | 鲁棒性↑ |
| **测试覆盖** | ❌ 不足 | ✅ 全面测试 | 质量保障↑ |
| **输出质量** | 不稳定 | 标准化 100% | 格式校验通过率 100% |

---

## 文档目录结构

### 1. 总体设计
- **文件**: [01_overall_design.md](01_overall_design.md)
- **内容**: 系统定位与设计目标、8 步法流程、3 层 SOP 架构、并发策略
- **核心改进**: 
  - ✅ 引入 8 步法 SOP 挖掘流程
  - ✅ 完整支持 3 层 SOP 架构 (主干/分支/子弹)
  - ✅ 新增中枢管控机制 (CoordinatorAgent)
  - ✅ Step 5 高度并发 (加速比 5-8x)

### 2. 详细 Agent 运作机制
- **文件**: [02_agent_operation_mechanism.md](02_agent_operation_mechanism.md)
- **内容**: 12 个核心 Agent 的详细职责、8 步法协作流程、Parlant 配置文件样例与字段说明
- **核心改进**:
  - ✅ 新增 CoordinatorAgent、MainSOPMiningAgent 等 8 个 Agent
  - ✅ 明确 8 步法的输入输出和依赖关系
  - ✅ 完善 Parlant 配置样例 (3 层 Journey 架构)

### 3. 软件工程化设计要求
- **文件**: [03_engineering_design.md](03_engineering_design.md)
- **内容**: 并发控制机制、数据流设计、控制流设计、工具服务设计、日志系统、错误处理、测试验证
- **核心改进**:
  - ✅ 使用 logrus 日志库 (非 pylogrus,非 Python logging)
  - ✅ Step 5 并发控制伪代码与资源隔离机制
  - ✅ Deep Research 强制调用机制 (≥3 次/Journey)
  - ✅ 完善的错误处理与重试机制

### 4. UI 交互设计
- **文件**: [03_ui_design.md](03_ui_design.md)
- **内容**: 5 个界面详细设计、统一处理等待界面、Step 5 并发可视化、3 层 SOP 架构展示
- **核心改进**:
  - ✅ 从 10 界面精简为 5 界面 (界面 4-9 合并为统一等待界面)
  - ✅ 界面 4: 统一处理等待界面 (覆盖 Step 2-8 全流程)
  - ✅ 界面 5: 3 层 SOP 架构可视化
  - ✅ 并发进度条、加速比实时显示

### 5. UI 与后端交互设计
- **文件**: [05_ui_backend_interaction.md](05_ui_backend_interaction.md)
- **内容**: 架构概述、核心组件设计、交互流程、API 接口设计、Streamlit 状态管理
- **核心改进**:
  - ✅ 支持界面 4 统一等待界面的状态轮询 (Step 2-8)
  - ✅ 新增并发统计 API 接口
  - ✅ UI 实时显示加速比和预计完成时间
  - ✅ 关键决策点 (Step 2 完成后) 的人工确认交互

---

## 文档说明

本设计文档是对 Parlant Agent 配置挖掘系统的 v2 版本架构设计，基于 8 步法 SOP 挖掘流程全面重构了系统架构。文档按照功能模块进行了拆解，便于团队成员快速定位和理解相关内容。

### 核心设计理念

#### 8 大核心设计原则
1. **主干唯一不可逆**: 主 SOP 是单一权威主干，所有分支必须明确标注"偏离主干"
2. **维度分层锁死**: 严格区分主 SOP(主干层)、分支 SOP(适配层)、子弹 SOP(补全层)
3. **合规全链路前置**: 所有合规相关规则必须在全局规则层统一定义
4. **全局 - 局部协同**: 全局规则与分支 SOP 规则必须明确优先级和排除关系
5. **粒度解耦可控**: 主 SOP 节点聚焦单一核心目标，分支 SOP 依附于主 SOP 节点
6. **目标对齐防偏离**: CoordinatorAgent 在 Step 2 写入 global_objective.md
7. **并发安全与隔离**: Step 5 的 N 个主 SOP 节点完全并行，每个节点拥有独立工作目录
8. **过程可追溯**: 每步独立存储中间产物，支持断点续跑、快速重启特定阶段

#### 10 条避坑红线
1. ❌ 禁止一个节点设置多个核心主目标
2. ❌ 禁止把可选子目标纳入强制结束条件
3. ❌ 禁止使用模糊、主观的结束条件
4. ❌ 禁止结束条件和合规要求脱节
5. ❌ 禁止跨节点设置目标
6. ❌ 禁止主流程节点超过 9 个或有分支
7. ❌ 禁止单个节点内分支超过 5 个
8. ❌ 禁止一个分支里用了超过 3 个维度
9. ❌ 禁止用补充维度拆了新的分支
10. ❌ 禁止跨节点做了维度组合

### 系统架构

- **用户输入层**: 业务描述文本、Data Agent 分析结果、配置参数 YAML
- **AgentScope 编排层**: StepManager、AgentOrchestrator、Human-in-the-Loop Interface
- **Agent 协作层**: 8 步法流程 (需求澄清→目标对齐→全局规则→用户画像→分支 SOP 并行挖掘→边缘场景→配置组装→最终校验)
- **工具服务层**: DeepSearch、FileSystem、JsonRepair、Debate、HumanLoop
- **输出产物层**: Parlant 配置包 (3 层 Journey 架构)、过程产物

### 核心流程 (8 步法)

1. **Step 1**: 需求澄清 + 人工确认 (RequirementAnalystAgent)
2. **Step 2**: 目标对齐与主 SOP 主干挖掘 (CoordinatorAgent + MainSOPMiningAgent)
3. **Step 3**: 全局规则与术语库挖掘 (GlobalRulesAgent + GlossaryAgent)
4. **Step 4**: 用户画像挖掘 (UserProfileAgent)
5. **Step 5**: 二级分支 SOP 并行挖掘 (BranchSOPAgent 等，高度并发，加速比 5-8x)
6. **Step 6**: 边缘场景挖掘 (EdgeCaseSOPAgent)
7. **Step 7**: Parlant 配置组装 (AssemblyAgent)
8. **Step 8**: 最终校验与输出 (ValidationAgent)

### 与 v1 的核心差异

| 维度 | v1(5 步法) | v2(8 步法) | 改进效果 |
|------|------------|------------|----------|
| **流程步骤** | 5 步 | 8 步 | 更精细的分工，更清晰的责任边界 |
| **SOP 架构** | 扁平化设计 | 3 层架构 (主/分支/子弹) | 结构清晰，易于维护和扩展 |
| **中枢管控** | 无 | CoordinatorAgent 目标对齐 | 防止 Agent 偏离总目标 |
| **并发策略** | Step 3 内部有限并发 | Step 5 完全并行 (5-8x 加速) | 显著提升执行效率 |
| **Deep Research** | 可选调用 | 强制调用≥3 次 | 增强信息广度和深度 |
| **边缘场景** | 混合在主流程中 | 独立 Step 6 子弹 SOP | 边缘场景覆盖更全面 |
| **质量校验** | Step 5 内置 | 独立 Step 8 专业校验 | 质量更有保障 |
| **配置目录** | 扁平 Journeys | 3 层 Journeys | 符合 Parlant 最佳实践 |

---

---

## 术语对照表

本节说明 Parlant 官方术语与工程化配置术语的对应关系，确保文档阅读和代码实现时术语使用一致。

### 核心概念术语对照

| Parlant 官方术语 | 工程化配置别名 | 说明 | 使用场景 |
|-----------------|---------------|------|---------|
| **Journey** | SOP (Standard Operating Procedure) | 结构化对话流程，包含状态机、转换条件等 | Journey 是 Parlant 官方术语；SOP 是本方案针对业务流程场景提出的易懂别名 |
| **Guideline** | 规则 | 条件-动作对的行为规则，格式为"当 X 时，做 Y" | Guideline 是 Parlant 核心概念；规则是中文语境下的通俗表达 |
| **Observation** | 观测 | 仅检测状态不包含动作的 Guideline，用于触发其他元素 | 用于门控指南、排除冲突、工具触发等场景 |
| **Canned Response** | 预设回复 / 固定话术 | 预审批的回复模板，消除幻觉风险 | 合规披露、法律义务、敏感话题等场景 |
| **Glossary** | 术语表 / 术语库 | 领域专用词汇表，将口语术语对应到精确业务定义 | 行业术语、公司内部用语、产品特定名称 |
| **Tool** | 工具 | 外部 API 和工作流的封装，仅在 Observation 匹配时触发 | 查询库存、预约时间、调用外部系统 |
| **Agent** | 智能体 | 与用户交互的定制化 AI 人格 | 客服 Agent、技术支持 Agent |
| **Customer** | 客户 / 用户 | 与 Agent 互动的终端用户 | 支持个性化、细分群体 |
| **Variable** | 变量 | 存储动态数据，支持个性化和上下文记忆 | 客户偏好、账户余额、会话上下文 |
| **Tag** | 标签 | 分类跟踪对话事件的字符串标签 | 分析和路由、会话筛选 |
| **Preamble** | 序言 | 简短的致谢语，保持对话自然响应 | "让我查查"、"稍等一下" |

### Journey 相关术语对照

| Parlant 官方术语 | 工程化配置别名 | 说明 |
|-----------------|---------------|------|
| **Journey Title** | SOP 名称 / 流程名称 | Journey 的简短描述性名称 |
| **Journey Conditions** | 触发条件 / 进入条件 | 决定 Journey 何时被激活的上下文查询列表 |
| **Journey Description** | SOP 描述 | Journey 的性质描述 |
| **Chat State** | 聊天状态 | Agent 与客户对话的状态，可花费多轮 |
| **Tool State** | 工具状态 | Agent 调用外部工具执行动作并加载结果到上下文 |
| **Fork State** | 分叉状态 | 评估条件并分支对话流的路由状态 |
| **Direct Transition** | 直接转换 | 总是执行的转移（无条件） |
| **Conditional Transition** | 条件转换 | 仅在条件满足时执行的转移 |
| **Journey-Scoped Guideline** | Journey 专属规则 / SOP 专属规则 | 仅在该 Journey 激活时才生效的 Guideline |
| **Journey-Scoped Canned Response** | Journey 专属话术 | 仅在该 Journey 激活时才考虑的话术模板 |

### Guideline 相关术语对照

| Parlant 官方术语 | 工程化配置别名 | 说明 |
|-----------------|---------------|------|
| **Condition** | 条件 | 指定何时动作应该发生的触发条件 |
| **Action** | 动作 | 描述 Guideline 应该完成什么 |
| **Description** | 描述 | 提供背景信息帮助理解为什么要这样做 |
| **Criticality** | 关键性级别 | 告诉 Agent 应投入多少注意力资源（LOW/MEDIUM/HIGH） |
| **Composition Mode** | 组合模式 | 预设回复的使用模式（Fluid/Composited/Strict） |
| **Exclusions** | 排除关系 | 当 S 和 T 同时激活时，只有 S 激活 |
| **Dependencies** | 依赖关系 | 当 S 激活时，除非 T 也激活否则关闭 |
| **Entailment** | 后产关系 | 当 S 激活时，T 也应该始终被激活 |
| **Disambiguation** | 消歧义关系 | 当 S 激活且多个 T 激活时，请客户澄清 |

### 3 层 SOP 架构术语说明

本方案基于 Parlant Journey 概念，设计了 3 层 SOP 架构：

| 层级 | 名称 | Parlant 对应 | 特征 |
|-----|------|-------------|------|
| **一级** | 主 SOP (主干层) | Main Journey | 5-9 个节点，无分支，冻结后禁止修改 |
| **二级** | 分支 SOP (适配层) | Branch Journey | 依附于主 SOP 节点，单节点≤5 分支，遵守 1+2 铁律 |
| **三级** | 子弹 SOP (补全层) | Edge Case Journey | 边缘异常场景原子化，1 场景 1SOP，插件式设计 |

### 文档使用规范

1. **技术实现层面**：统一使用 Parlant 官方术语（Journey、Guideline、Observation 等）
2. **业务描述层面**：可使用工程化别名（SOP、规则、观测等）作为易懂的表达
3. **配置文件字段**：保留 `sop_id`、`sop_title` 等历史命名（向后兼容）
4. **代码注释**：优先使用 Parlant 官方术语，便于与官方文档对照

### 配置文件与 Parlant API 对应关系

| 配置文件 | Parlant 官方 API | 说明 |
|---------|-----------------|------|
| `sop.json` | `agent.create_journey()` | Journey 流程核心定义 |
| `sop_guidelines.json` 中的 `sop_scoped_guidelines` | `journey.create_guideline()` | Journey 专属规则 |
| `sop_guidelines.json` 中的 `sop_canned_responses` | `journey.create_canned_response()` | Journey 专属话术 |
| `sop_observations.json` | `agent.create_observation()` | Journey 专属观测条件（无 action 的 Guideline） |
| `agent_guidelines.json` | `agent.create_guideline()` | Agent 全局规则 |
| `glossary/*.json` | `agent.create_term()` | 术语定义 |

---

**最后更新**: 2026-03-30  
**维护者**: System Team  
**文档版本**: v2.0 (8 步法架构版)
