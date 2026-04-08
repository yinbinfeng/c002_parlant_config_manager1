# Parlant Agent 配置挖掘系统 - 设计文档优化方案

**版本**: v6.0 (SOP 挖掘优化版)  
**创建日期**: 2026-03-30  
**文档类型**: 设计优化方案说明  
**状态**: 待用户确认

---

## 术语对照表

> 本节说明 Parlant 官方术语与工程化配置术语的对应关系，详细对照表请参见 [index.md - 术语对照表](index.md#术语对照表)。

### 核心术语速查

| Parlant 官方术语 | 工程化配置别名 | 一句话说明 |
|-----------------|---------------|-----------|
| **Journey** | SOP (标准作业流程) | 结构化对话流程，包含状态机、转换条件 |
| **Guideline** | 规则 | 条件-动作对，"当 X 时，做 Y" |
| **Observation** | 观测 | 仅检测状态不行动的 Guideline |
| **Canned Response** | 预设回复 / 固定话术 | 预审批的回复模板 |
| **Glossary** | 术语表 | 领域专用词汇定义 |
| **Tool** | 工具 | 外部 API 封装 |
| **Agent** | 智能体 | AI 人格 |
| **Customer** | 客户 / 用户 | 终端用户 |

### 3 层 SOP 架构术语

| 层级 | 名称 | Parlant 对应 | 特征 |
|-----|------|-------------|------|
| **一级** | 主 SOP (主干层) | Main Journey | 5-9 节点，无分支，冻结禁止修改 |
| **二级** | 分支 SOP (适配层) | Branch Journey | 依附主 SOP，单节点≤5 分支，1+2 铁律 |
| **三级** | 子弹 SOP (补全层) | Edge Case Journey | 1 场景 1SOP，插件式设计 |

### 文档使用规范

- **技术实现**: 统一使用 Parlant 官方术语（Journey、Guideline、Observation）
- **业务描述**: 可使用工程化别名（SOP、规则、观测）
- **配置字段**: 保留 `sop_id`、`sop_title` 等历史命名（向后兼容）

---

## 一、优化背景与目标

### 1.1 当前问题分析

基于现有设计文档 (v5.0) 和实际运行反馈，识别出以下核心问题:

| 问题类别 | 具体问题 | 影响范围 | 优先级 |
|---------|---------|---------|--------|
| **流程设计** | Step 2-5 过于线性，缺乏并行优化 | 执行效率低，无法充分利用多 Agent 协作 | 🔴 高 |
| **架构设计** | 缺少 3 层 SOP 架构支持 (主干/分支/子弹) | 输出粒度失衡，易导致状态机混乱 | 🔴 高 |
| **Agent 职责** | 缺少中枢管控 Agent，全局规则管理分散 | Agent 易偏离主题，口径不一致 | 🔴 高 |
| **并发控制** | 仅支持对话维度并发，轮次内并发未实现 | 性能瓶颈明显 | 🟡 中 |
| **配置规范** | Parlant 配置样例缺失，提示词缺少字段说明 | 输出质量不稳定，格式不规范 | 🔴 高 |
| **工具调用** | Deep Research 未强制调用，依赖样例数据 | 互联网信息获取不充分 | 🟡 中 |
| **工程化** | 日志使用 Print，错误处理不完善 | 可维护性差，问题定位困难 | 🟡 中 |

### 1.2 优化目标

| 目标 | 说明 | 验收标准 |
|------|------|---------|
| **流程优化** | 引入 8 步法 SOP 挖掘流程，支持并行执行 | Step 3-6 可并行率≥70% |
| **架构升级** | 完整支持 3 层 SOP 架构 (主干/分支/子弹) | 输出符合 5-9 节点主干，单节点≤5 分支 |
| **中枢管控** | 新增中枢 Agent，统一全局规则与术语管理 | 全流程术语统一度 100%，无冲突规则 |
| **并发提升** | 实现轮次内并发 + 对话维度并发 | 整体执行时间减少 50%+ |
| **配置规范** | 完善 Parlant 配置样例与提示词说明 | 输出格式校验通过率 100% |
| **工具强化** | 强制 Deep Research 调用，移除样例依赖 | 每个 Journey 至少包含 3 个互联网来源 |
| **工程化** | 使用 logrus 日志库，完善错误处理 | 日志结构化，错误可追溯 |

---

## 二、设计原则与理念

### 2.1 核心设计原则 (全流程必须严格遵守)

#### 原则 1: 主干唯一不可逆原则 🎯
- **定义**: 全流程仅存在一条无分支的主 SOP 主干，锁定后禁止修改
- **作用**: 是所有分支、边缘场景的唯一根节点，确保状态机极简可控
- **实施**: 
  - Step 2 完成后主 SOP 主干立即冻结 (`step2_main_sop_backbone.json`)
  - 所有后续步骤必须基于已冻结的主干执行
  - 禁止任何 Agent 修改主干结构
- **违规判定**: 任何对已冻结主干的修改尝试都将被 ComplianceCheckAgent 一票否决

#### 原则 2: 维度分层锁死原则 🔒
- **定义**: 每一层 SOP 仅能使用指定范围内的维度，禁止跨层级、超范围使用
- **作用**: 从根源上杜绝维度滥用导致的排列组合爆炸
- **实施**:
  - **主 SOP 层**: 仅允许使用「核心主意图 + 业务流程节点」2 个维度
  - **分支 SOP 层**: 遵守 1+2 铁律 (1 个核心区分维度 + 最多 2 个补充适配维度)
  - **子弹 SOP 层**: 仅允许使用「异常边缘场景 + 原子动作意图」2 个维度
- **违规判定**: BranchSOPAgent 输出前必须通过维度使用合规性检查

#### 原则 3: 合规全链路前置原则 ⚖️
- **定义**: 合规规则嵌入从主干到边缘场景的全流程每个环节，而非事后校验
- **作用**: 合规校验拥有一票否决权，确保零合规风险
- **实施**:
  - 每个节点的强制结束条件必须包含「全局合规校验通过」
  - ComplianceCheckAgent 参与 Step 2、Step 3、Step 5、Step 6、Step 8
  - 法定红线条款直接嵌入主 SOP 每个节点的结束条件
- **违规判定**: 任何未通过合规校验的输出直接无效，必须重新生成

#### 原则 4: 全局 - 局部协同原则 🌐
- **定义**: 全局规则、术语体系全流程统一，分支/边缘场景的局部规则不得与全局规则冲突
- **作用**: 确保口径统一、合规无死角
- **实施**:
  - GlobalRulesAgent 在 Step 3 生成全局规则库 (唯一法定源)
  - GlossaryAgent 在 Step 3 生成全局术语库 (唯一法定源)
  - 所有后续 Agent 仅能引用，禁止私自定义
- **违规判定**: QualityAgent 负责检查局部规则是否与全局规则冲突

#### 原则 5: 粒度解耦可控原则 📏
- **定义**: 主 SOP 粗粒度 (5-9 个节点)、分支 SOP 中粒度 (单节点≤5 个分支)、子弹 SOP 细粒度 (1 场景 1SOP)
- **作用**: 三层完全解耦，互不影响复杂度
- **实施**:
  - MainSOPMiningAgent: 严格控制在 5-9 个节点
  - BranchSOPAgent: 单节点分支数严格≤5 个
  - EdgeCaseSOPAgent: 1 个 SOP 对应 1 个场景 +1 个原子意图
- **违规判定**: 超过限制直接打回重新生成

#### 原则 6: 目标对齐防偏离原则 🎯
- **定义**: 每个 Agent 在执行任务时必须明确总目标和子目标，防止长链条执行中偏离
- **作用**: 确保所有 Agent 的输出都围绕同一核心目标
- **实施**:
  - CoordinatorAgent 在 Step 2 写入 `global_objective.md`
  - 每个 Agent 的系统 Prompt 中包含总目标描述
  - 每次输出前，Agent 需回答自检问题 (如：我的输出是否服务于总目标？)
- **违规判定**: CoordinatorAgent 定期检查各 Agent 输出的目标对齐情况

#### 原则 7: 并发安全与资源隔离原则 ⚡
- **定义**: 在支持高度并发的同时，确保数据一致性和资源隔离
- **作用**: 避免并发冲突，提高系统稳定性
- **实施**:
  - 每个 Agent 拥有独立的工作目录
  - 共享数据通过 StepManager 统一管理
  - 使用 asyncio 信号量控制并发数
- **违规判定**: 检测到资源竞争或数据冲突时自动降级为串行

#### 原则 8: 过程可追溯原则 📝
- **定义**: 所有关键决策、辩论记录、修正历史都必须完整保存
- **作用**: 便于问题定位、结果回溯和持续优化
- **实施**:
  - 所有 Agent 的 REACT 对话记录保存到 `step{N}_react_history.json`
  - 多 Agent 辩论记录保存到 `step{N}_debate_history.json`
  - Deep Research 报告保存到 `step{N}_research_reports/`
- **违规判定**: 缺少过程记录的输出视为无效

### 2.2 避坑红线 (绝对不能碰)

| 红线 | 描述 | 后果 | 防控措施 |
|------|------|------|---------|
| ❌ **禁止一个节点设置多个核心主目标** | 多个主目标会导致顺序混乱、结束条件无法判定 | 主流程状态机失控 | QualityAgent 强制检查 |
| ❌ **禁止把可选子目标纳入强制结束条件** | 无强顺序的子目标不能作为主流程流转的强制要求 | 流程卡壳 | 结束条件必须可量化验证 |
| ❌ **禁止使用模糊、主观的结束条件** | 如"客户满意了""客户有兴趣了"等 | 无法验证完成度 | 所有结束条件必须可量化、可验证 |
| ❌ **禁止结束条件和合规要求脱节** | 强监管场景，结束条件必须包含合规校验 | 合规风险巨大 | ComplianceCheckAgent 一票否决 |
| ❌ **禁止跨节点设置目标** | 每个节点的目标必须只对应这个节点的业务范围 | 打乱主流程顺序逻辑 | MainSOPMiningAgent 严格把关 |
| ❌ **禁止主流程节点超过 9 个或有分支** | 违反 5-9 节点原则 | 状态机复杂度爆炸 | 程序强制校验 |
| ❌ **禁止单个节点内分支超过 5 个** | 违反 1+2 铁律 | 排列组合爆炸 | BranchSOPAgent 自动检查 |
| ❌ **禁止一个分支里用了超过 3 个维度** | 违反维度分层锁死原则 | 维度滥用导致混乱 | 维度使用合规性检查 |
| ❌ **禁止用补充维度拆了新的分支** | 补充维度只能调整动作，不能拆分新分支 | 分支数量失控 | 1+2 铁律强制检查 |
| ❌ **禁止跨节点做了维度组合** | 禁止跨节点组合维度 | 状态机混乱 | 程序强制校验 |

### 2.3 设计优先级

当多个设计原则发生冲突时，遵循以下优先级:

```
合规性 (原则 3) > 主干唯一性 (原则 1) > 维度分层 (原则 2) > 全局协同 (原则 4) > 粒度解耦 (原则 5) > 目标对齐 (原则 6) > 并发安全 (原则 7) > 过程可追溯 (原则 8)
```

**示例**: 
- 如果为了合规需要增加一个主 SOP 节点 (违反原则 1),优先保证合规
- 如果为了并发效率可能破坏资源隔离 (原则 7),优先保证资源隔离

---

## 三、新流程设计方案 (8 步法)

### 3.1 整体流程图

```
┌─────────────────────────────────────────────────────────────────────┐
│                        用户输入层                                     │
│  业务描述文档 + Data Agent 分析结果 (可选) + 配置参数 YAML              │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                     AgentScope 编排层                                 │
│  StepManager (步骤调度) + AgentOrchestrator (并发控制)                │
│  + Human-in-the-Loop Interface (人工介入)                            │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    Agent 协作层 (8 步流程)                             │
│                                                                      │
│  Step 1          Step 2          Step 3         Step 4              │
│  需求澄清      → 目标对齐     → 全局规则    → 用户画像               │
│  + 人工确认      + 主 SOP 主干    + 术语库      + 多维画像             │
│                  + 业务价值                                          │
│                  (串行)        (可并行)                              │
│                                                                      │
│  Step 5 (高度并行)                                                   │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │  For each 主 SOP 节点：并发执行                              │       │
│  │   5.1 子 SOP 挖掘  →  5.2 术语提取  →  5.3 规则生成        │       │
│  │         ↓                  ↓                 ↓             │       │
│  │   5.4 子 SOP 总结  ←  5.5 质量校验 (含格式校验)             │       │
│  │                                                              │       │
│  │  [Node_1] [Node_2] ... [Node_N] 完全并行                   │       │
│  └──────────────────────────────────────────────────────────┘       │
│                                                                      │
│  Step 6          Step 7          Step 8                            │
│  边缘场景挖掘   → 配置组装    → 最终校验                           │
│  + 补充规则      + 目录组装    + 格式校验                           │
│  + 格式校验      + 验证报告    + 正式输出                           │
│                  (串行)                                              │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      工具服务层 (MCP 协议)                            │
│  DeepResearch(深度调研) + FileSystem(本地文件) + JsonRepair(校验)   │
│  + Debate(辩论框架) + HumanLoop(人工介入) + Embedding(向量计算)     │
│  + **LoggerService**(日志服务) + MessageArchive**(对话归档)**         │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                        输出产物层                                    │
│  Parlant 配置包 (符合官方 schema) + 过程产物 (可追溯)                  │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Agent 依赖关系与并行矩阵

#### 3.2.1 Agent 清单与职责 (含工具调用)

| Agent 名称 | 所属步骤 | 核心职责 | 输入依赖 | 输出产物 | **调用工具** | **日志记录** | 可并行对象 |
|-----------|---------|---------|---------|---------|------------|-------------|-----------|
| **RequirementAnalystAgent** | Step 1 | 需求澄清，REACT 模式自我反思 | 业务描述文档 | step1_clarification_questions.md | **FileSystem**(读取业务文档) | **MessageArchive**(保存 REACT 对话全流程), **LoggerService**(记录需求分析日志) | ❌ 无 |
| **CoordinatorAgent** | Step 2 | 组织多 Agent 辩论，目标对齐 | Step 1 输出 | step2_business_objectives.md, global_objective.md | **Debate**(组织辩论), **FileSystem**(读写辩论记录) | **MessageArchive**(保存辩论全过程 message), **LoggerService**(记录目标对齐日志) | ❌ 无 |
| **MainSOPMiningAgent** | Step 2 | 主 SOP 主干挖掘 | CoordinatorAgent 输出 | step2_main_sop_backbone.json | **FileSystem**(读取全局目标), **JsonRepair**(格式校验) | **MessageArchive**(保存 SOP 挖掘对话), **LoggerService**(记录状态机设计日志) | ❌ 无 (依赖 CoordinatorAgent) |
| **ComplianceCheckAgent** | Step 2,3,4,5,6,8 | 合规校验，一票否决权 | 各步骤输出 | `*_compliance_report.json`（按步骤区分，门控结构校验） | **FileSystem**(读取待检查文件), **JsonSchema**(schema 验证) | **MessageArchive**(保存合规检查对话), **LoggerService**(记录合规判定日志) | ✅ GlobalRulesAgent |
| **GlobalRulesAgent** | Step 3 | 全局规则挖掘 | Step 2 主干 | agent_guidelines.json | **DeepResearch**(行业最佳实践搜索), **FileSystem**(保存规则 + 报告) | **MessageArchive**(保存规则挖掘对话), **LoggerService**(记录 Deep Research 搜索日志) | ✅ GlossaryAgent, UserProfileAgent |
| **GlossaryAgent** | Step 3, 5 | 全局术语库 + 分支术语提取 | Step 2 主干 | step3_glossary_master.json | **DeepResearch**(行业标准术语), **Embedding**(术语相似度计算), **FileSystem**(术语库持久化) | **MessageArchive**(保存术语提取对话), **LoggerService**(记录术语关联构建日志) | ✅ GlobalRulesAgent, UserProfileAgent |
| **UserProfileAgent** | Step 4 | 用户画像挖掘 | Step 2 主干 | agent_user_profiles.json | **DeepResearch**(用户画像框架), **FileSystem**(画像配置保存) | **MessageArchive**(保存画像挖掘对话), **LoggerService**(记录维度选择日志) | ✅ GlobalRulesAgent, GlossaryAgent |
| **BranchSOPAgent** | Step 5 | 二级分支 SOP 挖掘 | Step 2 主干 + Step 3 全局规则 + Step 4 画像 | step5_journeys_*.json | **FileSystem**(读取主 SOP+ 规则 + 画像), **ParlantJourneyAPI**(Journey 模板加载), **JsonRepair**(格式预检) | **MessageArchive**(保存分支挖掘全流程 message), **LoggerService**(记录 1+2 铁律应用日志) | ✅ 其他 BranchSOPAgent (不同节点) |
| **RuleEngineerAgent** | Step 5 | 分支规则生成 | Step 3 全局规则 + BranchSOPAgent 输出 | step5_guidelines_*.json | **FileSystem**(读取全局规则 + 分支 SOP), **ParlantGuidelineAPI**(规则模板加载), **ConflictDetector**(规则冲突检测) | **MessageArchive**(保存规则生成对话), **LoggerService**(记录冲突检测日志) | ❌ 依赖 BranchSOPAgent |
| **QualityAgent** | Step 5, 8 | 质量校验，逻辑冲突检测 | Step 5 所有输出 | step5_qa_report_*.json | **JsonRepair**(JSON 修复), **JsonSchema**(schema 验证), **StateMachineValidator**(状态机死循环检查), **FileSystem**(读取待校验文件) | **MessageArchive**(保存质量检查对话), **LoggerService**(记录校验失败详情) | ❌ 依赖 Step 5 所有 Agent |
| **EdgeCaseSOPAgent** | Step 6 | 边缘场景子弹 SOP 挖掘 | Step 2 主干 + Step 3 全局规则 | step6_edge_case_sops.json | **FileSystem**(读取客诉案例 + 失败工单), **ParlantJourneyAPI**(原子 Journey 模板), **ComplianceAPI**(合规风险标注) | **MessageArchive**(保存边缘场景挖掘对话), **LoggerService**(记录风险等级标注日志) | ✅ 其他 EdgeCaseSOPAgent (不同场景) |
| **AssemblyAgent** | Step 7 | Parlant 配置组装 | Step 2-6 所有输出 | parlant_agent_config/ | **FileSystem**(读取所有中间产物), **ParlantSchemaValidator**(官方 schema 验证), **ConfigInjector**(chat_state/condition 注入) | **MessageArchive**(保存配置组装对话), **LoggerService**(记录 schema 验证日志) | ❌ 无 (依赖所有前置步骤) |
| **ValidationAgent** | Step 8 | 最终校验与效果评估 | Step 7 输出 | step8_validation_report.md | **JsonSchema**(全量 schema 验证), **ParlantSimulator**(模拟对话测试), **FileSystem**(读取配置包) | **MessageArchive**(保存最终校验对话), **LoggerService**(记录效果评估日志) | ❌ 无 (依赖 AssemblyAgent) |

#### 3.2.1.1 合规校验分层（门控校验 vs 全量校验）

为避免“重复校验 / 校验缺口 / 误判已合规”等问题，本方案将合规与质量校验拆分为两层：

1. **门控合规校验（Step 3 / Step 4 产物落盘后立即执行）**
   - **执行者**：`ComplianceCheckAgent`
   - **定位**：快速阻断“空产物、关键字段缺失、明显结构错误”等高风险输出，保证后续步骤不会在错误输入上继续扩散。
   - **最小检查项**（可逐步扩充，但不得弱化）：
     - Step 3：
       - `agent_guidelines.json`：必须是 JSON 对象；必须包含 `agent_id`；`agent_guidelines` 为非空数组
       - `step3_glossary_master.json`：必须是 JSON 对象；必须包含 `agent_id`；`terms` 为非空数组
     - Step 4：
       - `agent_user_profiles.json`：必须是 JSON 对象；必须包含 `agent_id`；`user_segments`/`personas` 为非空数组
   - **输出**：`step3_global_guidelines_compliance_report.json`、`step4_user_profiles_compliance_report.json`（命名按步骤区分）
   - **失败策略**：**一票否决**（不通过则该步骤失败，必须修复并重跑）

2. **全量校验（Step 8 最终校验）**
   - **执行者**：`ValidationAgent`（可组合 ComplianceCheckAgent 的更严格规则集）
   - **定位**：在完整配置包层面做“可运行、可审计、可维护”的全量检查，覆盖：
     - JSON 解析/修复（`json_repair`）
     - JSON Schema 校验（Parlant schema）
     - Journey schema / 状态机一致性（死胡同、循环、缺失 end state 等）
     - rules 冲突检测（dependencies/exclusions 环路、自依赖等）
     - 关键路径文件齐全性（目录结构与必需文件存在）
   - **输出**：`step8_validation_report.md`、`step8_compliance_certificate.json`

#### 3.2.2 前后依赖关系图

```
Step 1 (串行):
  RequirementAnalystAgent
         ↓
Step 2 (串行，内部有依赖):
  CoordinatorAgent → MainSOPMiningAgent → ComplianceCheckAgent
         ↓
Step 3 (可并行 Step 4):
  ┌→ GlobalRulesAgent ─→ ComplianceCheckAgent
  ├→ GlossaryAgent ────→ ComplianceCheckAgent
  └→ DeepResearchAgent (被调用)
         ↓
Step 4 (可并行 Step 3):
  ┌→ UserProfileAgent ─→ ComplianceCheckAgent
  └→ DomainExpertAgent (辅助)
         ↓
Step 5 (高度并行):
  For each 主 SOP 节点 i (完全并行):
    BranchSOPAgent_i → RuleEngineerAgent_i
           ↓                ↓
    GlossaryAgent_i ←──────┘
           ↓
    SummaryAgent_i
           ↓
    QualityAgent_i (检查前三个的输出)
         ↓ (所有节点完成后)
Step 6 (可部分并行):
  EdgeCaseSOPAgent_1 ─┐
  EdgeCaseSOPAgent_2 ─┼→ ComplianceCheckAgent
  EdgeCaseSOPAgent_N ─┘
         ↓
Step 7 (串行):
  AssemblyAgent
         ↓
Step 8 (串行):
  ValidationAgent → ComplianceCheckAgent (最终合规校验)
```

#### 3.2.3 并行度分析表

| 步骤 | 串行/并行 | 可并行对象 | 最大并发数 | 预计加速比 | 备注 |
|------|----------|-----------|-----------|-----------|------|
| Step 1 | 串行 | - | 1 | 1x | REACT 模式内部可多轮反思 |
| Step 2 | 串行 (内部有依赖) | CoordinatorAgent → MainSOPMiningAgent | 1 | 1x | 辩论可多轮，但必须顺序执行 |
| Step 3 | 部分并行 | GlobalRulesAgent ‖ GlossaryAgent | 2 | 1.5x | 两者共享 Deep Research 资源 |
| Step 4 | 部分并行 | UserProfileAgent ‖ (Step 3) | 2 | 1.5x | 可与 Step 3 同时执行 |
| Step 5 | **高度并行** | N 个主 SOP 节点完全并行 | N (建议≤8) | 5-8x | 核心优化点，每个节点独立 |
| Step 5 内部 | 可配置 | 5 个子步骤可串行或并行 | 1-3 | 1-2x | 取决于剩余并发配额 |
| Step 6 | 部分并行 | M 个边缘场景并行 | M (建议≤5) | 2-3x | 边缘场景通常较少 |
| Step 7 | 串行 | - | 1 | 1x | 配置组装必须顺序执行 |
| Step 8 | 串行 | - | 1 | 1x | 最终校验必须顺序执行 |

**整体加速比估算**:
- 假设主 SOP 有 6 个节点，每个节点 Step 5 耗时 10 分钟
- 旧方案 (串行): 6 × 10 = 60 分钟
- 新方案 (并行，max_parallel=6): 10 分钟
- **加速比**: 6x (理论值),实际约 4-5x (考虑资源竞争)

#### 3.2.4 资源隔离机制

**设计原则**:
- 每个 Agent 拥有独立的工作目录，避免文件冲突
- 通过信号量 (Semaphore) 控制最大并发数
- 异常时自动清理临时文件，仅保留输出产物
- **所有对话 message 必须完整保存，供追溯和审计**

**实施机制**:
1. **工作空间隔离**: 为每个 Agent 创建 `./workspace/{agent_id}/` 目录
2. **并发控制**: 使用异步信号量限制同时执行的 Agent 数量
3. **生命周期管理**: 
   - 执行前创建工作目录
   - 执行中在隔离目录内操作
   - 执行后清理临时文件，保留最终输出
4. **日志与对话归档** (新增):
   - **LoggerService**: 结构化日志记录到 `./logs/step{N}_{agent_name}/{agent_id}.log`
     - 示例：`logs/step1_requirement_analyst/requirement_analyst_001.log`
     - 示例：`logs/step5_branch_sop_node_002/branch_sop_node_002_agent.log`
   - **MessageArchive**: 完整对话 message 保存到 `./message_archive/step{N}_{agent_name}/{agent_id}_messages.jsonl`
     - 示例：`message_archive/step1_requirement_analyst/requirement_analyst_001_messages.jsonl`
     - 示例：`message_archive/step5_branch_sop_node_002/branch_sop_node_002_messages.jsonl`
   - **REACT 历史记录**: 自我反思过程保存到 `step{N}_{agent_name}_react_history.json`
     - 示例：`step1_requirement_analyst_react_history.json`
   - **辩论记录**: 多 Agent 辩论保存到 `step{N}_{agent_name}_debate_history.json`
     - 示例：`step2_coordinator_debate_history.json`

#### 3.2.5 数据依赖与共享机制

| 数据类型 | 生产者 | 消费者 | 共享方式 | 一致性保障 |
|---------|--------|--------|---------|-----------|
| `step1_structured_requirements.md` | RequirementAnalystAgent | All Agents | StepManager 统一加载 | 只读，禁止修改 |
| `step2_main_sop_backbone.json` | MainSOPMiningAgent | Step 3-8 所有 Agent | StepManager 统一加载 | 冻结后只读 |
| `global_objective.md` | CoordinatorAgent | All Agents | StepManager 统一加载 | 只读，目标对齐检查 |
| `agent_guidelines.json` | GlobalRulesAgent | Step 5, 6, 8 Agents | StepManager 统一加载 | 只读，ComplianceCheckAgent 监督 |
| `step3_glossary_master.json` | GlossaryAgent | Step 3-8 所有 Agent | StepManager 统一加载 | 只读，禁止私自定义 |
| `agent_user_profiles.json` | UserProfileAgent | Step 5 Agents | StepManager 统一加载 | 只读 |
| `step5_*_{node_id}.json` | BranchSOPAgent 等 | AssemblyAgent | 按节点隔离存储 | 节点间独立 |
| `step6_edge_case_sops.json` | EdgeCaseSOPAgent | AssemblyAgent | 统一存储 | 场景间独立 |

### 3.3 各步骤详细设计

#### **Step 1: 需求澄清 + 人工确认** (保持不变)

**核心 Agent**: `RequirementAnalystAgent` (REACT 模式)

**执行流程**:
1. 分析用户输入的业务描述文档
2. 使用 REACT 模式进行多轮自我反思:
   - 分析需求 → 输出待澄清问题 → 自我检查合理性 → 修正 → 直到正确
3. 输出澄清问题文档，等待人工确认
4. 人工在文档中录入答案后，命令行输入 `yes` 继续 (或 `no` 跳过)

**输入**: 
- 业务描述文档 (必需)
- Data Agent 分析结果 (可选)

**输出**:
- `step1_clarification_questions.md` (含用户反馈记录)
- `step1_structured_requirements.md`

**关键改进**:
- ✅ 增加 REACT 自我检查机制
- ✅ 人工确认为可选项 (支持跳过)
- ✅ 澄清问题可选带入后续步骤

---

#### **Step 2: 目标对齐与主 SOP 主干挖掘** (新增)

**核心 Agent**: `CoordinatorAgent` + `MainSOPMiningAgent` + `ComplianceCheckAgent`

**执行流程**:
1. **多 Agent 辩论**: CoordinatorAgent 组织 RuleEngineerAgent、DomainExpertAgent 进行辩论
   - 确定业务核心价值与目标
   - 确定主 SOP 覆盖的范围与边界
   - 确定每个分支的大概内容方向
2. **主 SOP 主干挖掘**: MainSOPMiningAgent 基于辩论结果挖掘主流程
   - 严格遵循 5-9 个节点
   - 仅使用「核心主意图 + 业务流程节点」2 个维度
   - 每个节点明确唯一核心主目标 + 可量化结束条件
3. **合规校验**: ComplianceCheckAgent 进行合规前置校验
   - 嵌入法定合规要求到结束条件
   - 一票否决权

**输出**:
- `step2_business_objectives.md` (业务价值与目标)
- `step2_main_sop_backbone.json` (主 SOP 主干，冻结后禁止修改)
- `step2_debate_history.json` (辩论记录，可追溯)
- `global_objective.md` (全局目标文件，防止后续偏离)

**关键设计要求**:
- ✅ 必须先完成主干挖掘与锁定，才能启动下层 SOP
- ✅ 主干冻结后禁止修改，是所有分支/子弹的唯一根节点
- ✅ 结束条件必须嵌入合规校验要求

---

#### **Step 3: 全局规则与术语库挖掘** (可并行 Step 4)

**核心 Agent**: `GlobalRulesAgent` + `GlossaryAgent` + `DeepResearchAgent`

**执行流程**:

**阶段 1: Parlant 配置指导要求加载** (新增关键步骤)
```
在正式挖掘前，先加载 Parlant 配置的结构化指导要求 (非详细格式):

GlobalRulesAgent 加载:
  - journey_rule_requirements.md (旅程规则指导)
    * 规则分类框架 (合规红线/操作规范/审批规则/话术标准)
    * 规则优先级定义 (P0-P3)
    * 规则冲突检测原则
  
  - glossary_requirements.md (术语库指导)
    * 术语分类框架 (法定术语/行业术语/内部术语)
    * 术语关联关系类型 (同义词/上下位词/相关词)
    * 术语唯一性约束
```

**阶段 2: 基于指导要求进行挖掘**
1. **全局规则挖掘**: GlobalRulesAgent 主导
   - 从互联网 (Deep Research) 搜索行业最佳实践、法规要求
   - 从业务描述提取公司特有规则
   - 按照指导要求的分类框架组织规则
   
2. **术语库构建**: GlossaryAgent 主导
   - 提取法定强制术语、行业通用术语、公司内部术语
   - 建立术语关联关系 (同义词、上下位词)
   - 形成全局统一术语库 (唯一法定定义源)

**阶段 3: Deep Research 强制调用与报告保存**
- 每个规则类别至少调用 3 次 Deep Research
- 搜索话题拆分为小方向并发搜索
- 输出详细研究报告并存入 `step3_research_reports/`

**输出**:
- `agent_guidelines.json` (Step 3 全局规则配置，agent-level guideline，符合 Parlant Guideline schema)
- `step3_glossary_master.json` (全局统一术语库，符合 Parlant Glossary schema)
- `step3_research_reports/` (Deep Research 报告目录)
- `step3_debate_history.json` (辩论记录)
 - `step3_global_guidelines_compliance_report.json`（门控合规/结构校验报告，不通过直接终止）

**关键设计要求**:
- ✅ **分阶段挖掘**: 先加载指导要求 → 再挖掘 → 最后套用详细 schema
- ✅ 全局规则是所有层级 SOP 必须遵守的最高标准
- ✅ 术语库是唯一法定定义源，各 SOP 仅能引用，禁止私自定义
- ✅ 强制 Deep Research 调用并输出报告

---

#### **Step 4: 用户画像挖掘** (可并行 Step 3)

**核心 Agent**: `UserProfileAgent` + `DomainExpertAgent`

**执行流程**:

**阶段 1: Parlant 配置指导要求加载** (新增关键步骤)
```
在正式挖掘前，先加载 Parlant 配置的结构化指导要求 (非详细格式):

UserProfileAgent 加载:
  - user_profile_requirements.md (用户画像指导)
    * 画像维度分类框架 (核心必选维度/扩展补充维度)
    * 维度分层约束 (仅用于分支适配，禁止用于主 SOP 拆分)
    * 画像与服务策略映射关系模板
  
  - profile_dimension_constraints.md (维度约束)
    * 允许使用的维度类型列表
    * 禁止使用的维度类型列表
    * 维度组合规则
```

**阶段 2: 基于业务描述和 Step 2 的主 SOP，识别关键用户维度**
1. 使用 Deep Research 搜索行业标准用户画像框架
2. 构建多层级用户画像体系:
   - 核心必选维度：与业务强相关的属性 (年龄、职业、收入等)
   - 扩展补充维度：渠道、情感风险等级、资源权限等
3. 为每个画像定义专属服务策略

**输出**:
- `agent_user_profiles.json` (用户画像配置，符合 Parlant User Profile schema)
- `step4_research_reports/` (Deep Research 报告)
 - `step4_user_profiles_compliance_report.json`（门控合规/结构校验报告，不通过直接终止）

**关键设计要求**:
- ✅ **分阶段挖掘**: 先加载指导要求 → 再挖掘 → 最后套用详细 schema
- ✅ 用户画像仅作为分支适配维度，禁止用于主 SOP 拆分
- ✅ 区分核心必选维度与扩展补充维度
- ✅ 每个画像明确服务策略差异

---

#### **Step 5: 二级分支 SOP 并行挖掘** (核心优化点)

**核心 Agent**: `BranchSOPAgent` + `GlossaryAgent` + `RuleEngineerAgent` + `QualityAgent`

**执行流程** (针对每个主 SOP 节点并发执行):

**阶段 1: Parlant 配置指导要求加载** (新增关键步骤，每个节点独立加载)
```
For each 主 SOP 节点 i (完全并行):
  
  BranchSOPAgent_i 加载:
    - journey_branch_requirements.md (分支旅程指导)
      * 1+2 铁律说明 (1 个核心区分维度 + 最多 2 个补充适配维度)
      * 分支数量约束 (单节点≤5 分支)
      * 维度选择优先级 (用户画像 > 核心子意图 > 业务场景)
      * 分支回归主流程要求
    
    - journey_schema_outline.md (Journey schema 概览，非详细格式)
      * Journey 核心字段说明 (name, steps, conditions)
      * 状态流转约束
      * 结束条件定义要求
  
  RuleEngineerAgent_i 加载:
    - guideline_requirements.md (规则生成指导)
      * 规则分类框架 (操作细则/话术模板/审批流程)
      * 规则优先级定义
      * 与全局规则冲突检测原则
  
  GlossaryAgent_i 加载:
    - glossary_extraction_requirements.md (术语提取指导)
      * 术语来源 (全局术语库引用 vs 场景专属提取)
      * 术语关联关系类型
```

**阶段 2: 基于指导要求并发挖掘**
```
For each 主 SOP 节点 i (完全并行):
    ├─ Step 5.1: BranchSOPAgent_i 挖掘子 SOP
    │   - 选择 1 个核心区分维度 (用户画像/核心子意图/业务场景)
    │   - 拆分最多 5 个分支
    │   - 每个分支内最多叠加 2 个补充适配维度
    │   └─ 输出：step5_journeys_{node_id}.json
    │
    ├─ Step 5.2: GlossaryAgent_i 挖掘对应术语
    │   - 从全局术语库引用相关术语
    │   - 提取场景专属术语 (如有)
    │   └─ 输出：step5_glossary_{node_id}.json
    │
    ├─ Step 5.3: RuleEngineerAgent_i 挖掘对应规则
    │   - 基于全局规则，制定场景专属操作规则
    │   - 确保不与全局规则冲突
    │   └─ 输出：step5_guidelines_{node_id}.json
    │
    ├─ Step 5.4: SummaryAgent_i 总结子 SOP
    │   - 整合 5.1-5.3 的输出
    │   - 形成完整的分支 SOP 文档
    │   └─ 输出：step5_summary_{node_id}.md
    │
    └─ Step 5.5: QualityAgent_i 质量与格式校验
        - 进行逻辑合理性验证
        - 检查规则冲突、状态机死循环
        - 使用 json_repair 进行格式校验
        └─ 输出：step5_qa_report_{node_id}.json
```

**依赖关系**:
```
Node_1: BranchSOP_1 → RuleEngineer_1
             ↓              ↓
        Glossary_1 ←────────┘
             ↓
        Summary_1
             ↓
        Quality_1 (检查前三个的输出)

Node_2: BranchSOP_2 → RuleEngineer_2  (与 Node_1 完全并行)
             ↓              ↓
        Glossary_2 ←────────┘
             ↓
        Summary_2
             ↓
        Quality_2

...

Node_N: (与 Node_1, Node_2, ... 完全并行)
```

**并发控制策略**:

| 并发层级 | 并发对象 | 并发模式 | 最大并发数 | 说明 |
|---------|---------|---------|-----------|------|
| **节点间并发** | 不同主 SOP 节点的任务组 | 完全并行 | `max_parallel_nodes` (建议≤8) | 核心优化点，每个节点独立处理 |
| **节点内并发** | 同一节点内的 5.1-5.3 | 可配置串行或并行 | 1-3 | 取决于剩余并发配额 |
| **5.5 质量校验** | QualityAgent | 必须串行 | 1 | 必须在 5.1-5.4 完成后执行 |

**伪代码示例**:
**并发控制策略** (Step 5 核心优化点):

**执行流程**:
1. 为每个主 SOP 节点创建独立的工作目录
2. **并发加载指导要求**: 各 Agent 并行读取指导文档
3. 使用信号量控制最大并发数
4. 并发执行所有节点的任务
5. 收集所有节点的执行结果
6. 检查失败任务并根据配置决定是否继续

**节点内部处理**:
- **方案 1(推荐)**: 节点内串行执行 5 个子步骤，更安全
- **方案 2**: 节点内部分并行执行，更快但需要更多资源

**输出**:
- `step5_journeys_*.json` (流程定义，符合 Parlant Journey schema)
- `step5_glossary_*.json` (词汇定义，符合 Parlant Glossary schema)
- `step5_guidelines_*.json` (规约定义，符合 Parlant Guideline schema)
- `step5_summary_*.md` (分支 SOP 总结文档)
- `step5_qa_report_*.json` (质检报告)
- `step5_correction_history.json` (修正历史记录)

**关键设计要求**:
- ✅ **分阶段挖掘**: 先加载指导要求 → 再挖掘 → 最后套用详细 schema
- ✅ 严格遵守 1+2 铁律 (1 个核心区分维度 + 最多 2 个补充适配维度)
- ✅ 单个主节点内分支数严格≤5 个
- ✅ 每个分支必须回归主流程对应节点
- ✅ 局部规则不得与全局规则冲突

---

#### **Step 6: 边缘场景挖掘** (新增)

**核心 Agent**: `EdgeCaseSOPAgent` + `ComplianceCheckAgent`

**执行流程**:

**阶段 1: Parlant 配置指导要求加载** (新增关键步骤)
```
在正式挖掘前，先加载 Parlant 配置的结构化指导要求 (非详细格式):

EdgeCaseSOPAgent 加载:
  - edge_case_requirements.md (边缘场景指导)
    * 边缘场景识别原则 (客诉/失败案例/异常工单)
    * 原子化设计约束 (1 场景 1SOP 原则)
    * 插件式插拔机制说明
    * 挂载主流程节点定义方法
    * 返回节点定义方法
  
  - atomic_journey_outline.md (原子 Journey 概览)
    * Journey 核心字段说明
    * 原子意图定义要求
    * 场景 - 意图映射关系
  
  ComplianceCheckAgent 加载:
    - compliance_risk_requirements.md (合规风险指导)
      * 合规风险等级分类 (P0-P3)
      * 主流程断点位置标注要求
      * 合规前置校验原则
```

**阶段 2: 基于指导要求挖掘边缘场景**
1. **边缘场景识别**: 基于主 SOP、分支 SOP 覆盖不到的场景
   - 从客诉案例、失败案例、异常工单中提取
   - 标注合规风险等级、主流程断点位置
   
2. **原子化子弹 SOP 生成**: 为每个边缘场景生成
   - 1 个 SOP 对应 1 个场景 +1 个原子意图
   - 明确挂载的主流程节点和返回节点
   
3. **规则补充**: 将边缘场景规则补充进全局规则
4. **格式校验和合规校验**

**输出**:
- `step6_edge_case_sops.json` (子弹 SOP 原子化库，符合 Parlant Journey schema)
- `step6_supplementary_rules.json` (补充规则，符合 Parlant Guideline schema)
- `step6_validation_report.json` (验证报告)

**关键设计要求**:
- ✅ **分阶段挖掘**: 先加载指导要求 → 再挖掘 → 最后套用详细 schema
- ✅ 1 场景 1SOP，禁止多场景合并
- ✅ 插件式设计，可独立插拔
- ✅ 必须明确场景专属合规要求

---

#### **Step 7: Parlant 配置组装**

**核心 Agent**: `AssemblyAgent`

**执行流程**:

**阶段 1: Parlant 详细 schema 加载** (新增关键步骤)
```
在正式组装前，先加载 Parlant 官方详细 schema 和输出样例:

AssemblyAgent 加载:
  - parlant_schema_full.json (官方完整 schema)
    * Agent 配置结构定义
    * Journey schema 详细约束
    * Guideline schema 格式要求
    * Glossary schema 字段说明
  
  - journey_output_examples.json (Journey 输出样例)
    * 主 Journey 样例 (来自主 SOP 主干)
    * 分支 Journey 样例 (来自 Step 5)
    * 边缘场景 Journey 样例 (来自 Step 6)
  
  - guideline_output_examples.json (Guideline 输出样例)
    * 全局规则样例 (来自 Step 3)
    * 分支规则样例 (来自 Step 5)
    * 补充规则样例 (来自 Step 6)
  
  - chat_state_injection_template.md (chat_state 注入模板)
    * 状态流转条件定义
    * condition 判定逻辑模板
    * 变量引用规范
```

**阶段 2: 基于详细 schema 进行配置组装**
1. **目录结构组织**: 按照官方 schema 组织目录结构:
   ```
   parlant_agent_config/
   ├── agents/{agent_name}/
   │   ├── 00_agent_base/
   │   │   ├── agent_metadata.json
   │   │   ├── agent_observability.json
   │   │   ├── agent_user_profiles.json (来自 Step 4)
   │   │   └── glossary/ (来自 Step 3 + Step 5)
   │   ├── 01_agent_rules/
   │   │   ├── agent_guidelines.json (仅来自 Step 3 - 全局规则)
   │   │   ├── agent_observations.json
   │   │   └── agent_canned_responses.json
   │   ├── 02_journeys/
   │   │   ├── {main_journey_name}/ (来自主 SOP 主干)
   │   │   │   ├── sop.json
   │   │   │   ├── sop_guidelines.json (该主 Journey 专属的全局规则引用)
   │   │   │   └── sop_observations.json
   │   │   ├── {branch_journey_name}/ (来自 Step 5 分支 SOP)
   │   │   │   ├── sop.json
   │   │   │   ├── sop_guidelines.json (该分支专属的规则)
   │   │   │   └── sop_observations.json
   │   │   └── {edge_case_journey_name}/ (来自 Step 6 子弹 SOP)
   │   │       ├── sop.json
   │   │       ├── sop_guidelines.json (该边缘场景专属的规则)
   │   │       └── sop_observations.json
   │   └── 03_tools/
   │       └── {tool_name}/
   │           ├── tool_meta.json
   │           └── tool_impl.py
   ```

2. **配置注入**: 注入 chat_state 和 condition 判定逻辑
3. **Schema 验证**: 使用 ParlantSchemaValidator 进行全量验证
4. **生成组装报告**

> **重要说明 - Journey 配置文件与 Parlant 官方 API 的对应关系**:
> 
> 本工程化配置方案采用以下文件组织方式 (便于人工维护和审核):
> - `sop.json` → 对应 Parlant 官方的 Journey 定义 (`agent.create_journey()`)
> - `sop_guidelines.json` → 包含两部分:
>   - `sop_canned_responses` → 对应 `journey.create_canned_response()` 创建的 Journey 专属话术
>   - `sop_scoped_guidelines` → 对应 `journey.create_guideline()` 创建的 Journey 专属规则，必须包含`scope: "sop_only"`
> - `sop_observations.json` → 对应 Parlant 官方的 Observations(`agent.create_observation()`),本质是"没有 action 的 Guideline"
> 
> **Parlant 官方核心概念**:
> 1. **Journey**: 结构化对话流程，包含 Title、Conditions、Description、States & Transitions
> 2. **Guideline**: 上下文相关的行为指导，包含 Condition + Action，可绑定 Tools
> 3. **Observation**: 仅包含 Condition 的 Guideline，用于通过关系激活/停用其他 Guidelines 或 Journeys
> 4. **Canned Response**: 预定义的话术模板，可 Journey-scoped 或 State-scoped
> 5. **Scope**: Guidelines 的作用域，`"sop_only"`=Journey 专属，`"agent_global"`=Agent 全局

**输出**:
- `parlant_agent_config/` (完整配置包，符合官方 schema)
- `step7_assembly_report.md` (组装报告，含 schema 验证结果)

**关键设计要求**:
- ✅ **分阶段组装**: 先加载详细 schema → 再组装 → 最后验证
- ✅ 符合 Parlant 官方 schema
- ✅ 注入 chat_state/condition 逻辑
- ✅ 原子化旅程设计
- ✅ 全局规则 (Step 3) 放在 01_agent_rules/guidelines.json
- ✅ 分支/边缘场景规则放在对应 journey 的 guidelines.json 中

---

#### **Step 8: 最终校验与输出**

**核心 Agent**: `ValidationAgent` + `ComplianceCheckAgent`

**执行流程**:

**阶段 1: 校验工具加载** (新增关键步骤)
```
在正式校验前，先加载校验工具和验证规则:

ValidationAgent 加载:
  - jsonschema_validator.py (JSON Schema 验证器)
    * Parlant 官方 schema 定义
    * 自定义验证规则
  
  - parlant_simulator_config.yaml (Parlant 模拟器配置)
    * 模拟对话轮数设置
    * 测试用例覆盖度要求
    * 边界场景测试集
  
  ComplianceCheckAgent 加载:
    - compliance_check_rules.md (合规检查规则)
      * 全局 - 局部规则冲突检测算法
      * 结束条件合规校验清单
      * 术语统一性检查规则
```

**阶段 2: 多层级校验**
1. **格式校验**: 使用 json_repair + jsonschema 校验所有 JSON 文件
   - JSON 语法正确性
   - Schema 符合度验证
   - 必填字段完整性
   
2. **合规校验**: ComplianceCheckAgent 进行全量合规检查
   - 检查局部规则是否与全局规则冲突
   - 检查结束条件是否嵌入合规要求
   - 检查术语使用是否统一
   
3. **效果验证**: 
   - 主流程流转通过率 (目标≥95%)
   - 边缘场景覆盖率 (目标 100%)
   - 合规校验通过率 (目标 100%)
   - 术语统一度 (目标 100%)
   
4. **差异标注**: 在验证报告中标注数据来源
   - ✅ 互联网搜索 (Deep Research): 已处理
   - ✅ 外部 Data Agent 分析结果：已处理
   
5. **生成最终报告**: 包含评估指标和改进建议

**阶段 3（可选）: 小错误自动修复与返工门控**（工程化可选开关，默认关闭）
- **小错误自动修复（Auto-fix）**：
  - **目标**：对“JSON 解析失败但可被 `json_repair` 修复”的文件，允许将修复后的 JSON **回写覆盖原文件**，避免后续重复报同类格式问题。
  - **开关**：`step8_auto_fix_json.enabled`
  - **说明**：仅处理语法/格式类问题，不修改业务语义；默认关闭，避免在迁移期引入不可预期的落盘差异。
- **质量分门控返工（Rework gate）**：
  - **目标**：当错误过多导致质量分低于阈值时，允许流程**回跳到指定步骤**重新生成（返工可选）。
  - **开关**：`step8_quality_gate.enabled`
  - **阈值**：`step8_quality_gate.rework_trigger_threshold`（质量分 < 阈值触发）
  - **回跳步**：`step8_quality_gate.rework_restart_step`（建议 5 或 3）
  - **最大轮数**：`step8_quality_gate.max_rework_rounds`（避免无限回路）
  - **产物**：合规证书中应记录 `quality_score`，用于审计与回溯。

**输出**:
- `step8_validation_report.md` (最终验证报告)
- `step8_compliance_certificate.json` (合规证书)
- `final_parlant_config/` (正式发布版本)

**关键设计要求**:
- ✅ **分阶段校验**: 先加载校验工具 → 再校验 → 最后输出报告
- ✅ 最大重试 3 次，仍失败则记录错误并跳过
- ✅ 验证报告包含差异标注
- ✅ 所有输出纳入 Git 版本管理

---

## 三、核心 Agent 职责设计

### 3.1 新增 Agent

| Agent 名称 | 职责 | 所属步骤 | 关键能力 |
|-----------|------|---------|---------|
| **CoordinatorAgent** | 全局目标对齐、多 Agent 辩论组织 | Step 2 | 辩论框架、目标管理 |
| **MainSOPMiningAgent** | 主 SOP 主干挖掘 | Step 2 | 状态机设计、维度控制 |
| **GlobalRulesAgent** | 全局规则与合规管控 | Step 3 | Deep Research、法规提取 |
| **UserProfileAgent** | 用户画像挖掘 | Step 4 | 多维画像构建 |
| **BranchSOPAgent** | 二级分支 SOP 挖掘 | Step 5 | 分支适配、1+2 铁律 |
| **EdgeCaseSOPAgent** | 边缘场景子弹 SOP 挖掘 | Step 6 | 异常场景识别、插件式设计 |
| **AssemblyAgent** | Parlant 配置组装 | Step 7 | 格式转换、目录组织 |
| **ValidationAgent** | 最终校验与效果评估 | Step 8 | 格式校验、效果验证 |

### 3.2 保留 Agent (优化职责)

| Agent 名称 | 优化点 |
|-----------|--------|
| **RequirementAnalystAgent** | 增加 REACT 自我检查机制 |
| **RuleEngineerAgent** | 聚焦局部规则生成，确保不与全局冲突 |
| **GlossaryAgent** | 从全局术语库引用，禁止私自定义 |
| **QualityAgent** | 增加逻辑冲突检测、状态机死循环检测 |
| **ComplianceCheckAgent** | 提升为一票否决权，全链路嵌入 |

---

## 四、并发控制机制优化

### 4.1 并发策略总览

| 步骤 | 并发模式 | 并发对象 | 并发数控制 |
|------|---------|---------|-----------|
| Step 1 | 串行 | - | - |
| Step 2 | 串行 | - | - |
| Step 3 | 并行 | 全局规则/术语库挖掘 | `max_parallel_agents` |
| Step 4 | 并行 | 用户画像挖掘 | `max_parallel_agents` |
| Step 5 | 高度并行 | 不同主 SOP 节点的分支挖掘 | `max_parallel_agents` × 节点数 |
| Step 6 | 并行 | 多个边缘场景 | `max_parallel_agents` |
| Step 7 | 串行 | - | - |
| Step 8 | 并行 | 多个校验任务 | `max_parallel_agents` |

### 4.2 Step 5 内部并发策略

```python
# 伪代码示例
async def execute_step5(main_sop_nodes, max_parallel):
    """
    Step 5: 二级分支 SOP 并行挖掘
    """
    tasks = []
    for node in main_sop_nodes:
        # 每个主 SOP 节点启动一个任务组
        node_task = asyncio.create_task(
            process_single_node(node, max_parallel)
        )
        tasks.append(node_task)
    
    # 并发执行所有节点
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results

async def process_single_node(node, max_parallel):
    """
    处理单个主 SOP 节点的分支 SOP 挖掘
    """
    # 5 个子步骤可以串行或并行 (取决于剩余并发配额)
    step5_1_result = await branch_sop_agent.execute(node)
    step5_2_result = await glossary_agent.execute(step5_1_result)
    step5_3_result = await rule_engineer_agent.execute(step5_1_result)
    step5_4_result = await summary_agent.execute([
        step5_1_result, step5_2_result, step5_3_result
    ])
    step5_5_result = await quality_agent.execute(step5_4_result)
    
    return step5_5_result
```

### 4.3 资源隔离机制

每个 Agent 拥有独立的工作目录，避免文件冲突:

```
workspace/
├── session_{session_id}/
│   ├── step{N}/
│   │   ├── agent_{id}_workdir/
│   │   │   ├── tmp/           # 临时文件
│   │   │   ├── findings/      # 中间发现
│   │   │   └── output/        # 最终输出
│   │   └── agent_{id+1}_workdir/
│   │   └── ...
│   └── ...
```

---

## 五、配置管理规范

### 5.1 配置文件结构

```
config/
├── system_config.yaml         # 系统级配置 (全局共享)
├── agents/                    # Agent 配置目录 (每个 Agent 一个 YAML)
│   ├── requirement_analyst.yaml
│   ├── coordinator.yaml
│   ├── main_sop_mining.yaml
│   ├── global_rules.yaml
│   ├── glossary.yaml
│   ├── user_profile.yaml
│   ├── branch_sop.yaml
│   ├── rule_engineer.yaml
│   ├── edge_case.yaml
│   ├── assembly.yaml
│   ├── validation.yaml
│   └── quality_agent.yaml
├── prompts/                   # 提示词模板目录 (与 Agent 一一对应)
│   ├── requirement_analysis.yaml
│   ├── coordinator_objective.yaml
│   ├── main_sop_extraction.yaml
│   ├── global_rules_generation.yaml
│   ├── glossary_generation.yaml
│   ├── user_profile_generation.yaml
│   ├── branch_sop_generation.yaml
│   ├── rule_engineer_generation.yaml
│   ├── edge_case_generation.yaml
│   ├── assembly_instructions.yaml
│   ├── validation_checklist.yaml
│   └── quality_checklist.yaml
└── parlant_templates/         # Parlant 输出模板 (JSON Schema)
    ├── journey_template.json
    ├── guideline_template.json
    ├── tool_template.json
    ├── glossary_template.json
    └── customer_profile_template.json
```

**设计原则**:
- ✅ **按功能模块组织**: 每个 Agent 的配置和提示词独立成文件
- ✅ **配置与提示词分离**: `agents/` 存放 Agent 参数配置，`prompts/` 存放提示词模板
- ✅ **命名一致性**: Agent 配置和提示词文件名保持一致 (如 `coordinator.yaml` ↔ `coordinator_objective.yaml`)
- ✅ **便于扩展**: 新增 Agent 时只需添加对应的配置和提示词文件

### 5.2 关键配置项

**system_config.yaml**:
```yaml
# 并发控制
max_parallel_agents: 4        # 最大并发 Agent 数 (1=串行)
max_parallel_step5_nodes: 8   # Step 5 最大并发节点数

# 步骤控制
start_step: 1                 # 起始步骤 (1-8)
end_step: 8                   # 结束步骤 (1-8)
force_rerun: false            # 是否强制重跑已完成的步骤
continue_on_error: false      # 错误时是否继续执行

# 人工介入
skip_clarification: false     # 是否跳过人工澄清环节
clarification_timeout: 3600   # 人工澄清超时时间 (秒)

# Deep Research 配置
deep_research:
  enabled: true
  min_calls_per_journey: 3    # 每个 Journey 最少调用次数
  max_depth: 3                # 最大搜索深度
  max_iters: 30               # 最大迭代次数
  timeout_per_search: 300     # 单次搜索超时 (秒)

# 并发策略
concurrency:
  enable_dialog_level: true   # 启用对话维度并发
  enable_turn_level: true     # 启用轮次内并发
  embedding_cache: true       # 启用 Embedding 缓存
  batch_size: 32              # 批量处理大小

# 输出配置
output_base_dir: "./output"   # 输出目录
enable_version_control: true  # 是否启用 Git 版本管理
save_react_history: true      # 是否保存 REACT 对话记录
save_debate_history: true     # 是否保存辩论记录

# 校验配置
json_validation:
  max_retries: 3              # JSON 校验最大重试次数
  auto_fix: true              # 是否启用自动修复

agent_correction:
  max_correction_attempts: 3  # Agent 最大修正次数
  auto_correct: true          # 是否启用自动修正

# 合规校验
compliance:
  veto_power: true            # 合规拥有一票否决权
  check_all_stages: true      # 全链路嵌入校验
```

**Agent 配置示例** (`mining_agents/coordinator.yaml`):
```yaml
agent_name: CoordinatorAgent
base_class: ReActAgent
description: 负责全局目标对齐、组织多 Agent 辩论、确保不偏离主题

model:
  type: DashScopeChatModel
  config:
    model_name: qwen3-max
    temperature: 0.7
    max_tokens: 4096

tools:
  - deep_research_search
  - write_text_file
  - read_text_file
  - debate_moderate  # 新增：辩论主持工具

system_prompt_template: prompts/coordinator_objective.yaml
output_schema: BusinessObjectivesSchema

# 目标对齐机制
objective_alignment:
  enforce_global_goal: true   # 强制全局目标
  check_deviation: true       # 检查偏离
  max_deviation_tolerance: 0.3  # 最大偏离容忍度

# REACT 模式配置
react_mode:
  enabled: true
  max_reflection_rounds: 5    # 最大反思轮数
  self_check_before_output: true  # 输出前自我检查
```

### 5.3 Parlant 配置模板

**journey_template.json**:
```json
{
  "name": "{{journey_name}}",
  "description": "{{journey_description}}",
  "trigger_conditions": {{trigger_conditions}},
  "states": [
    {
      "name": "{{state_name}}",
      "description": "{{state_description}}",
      "core_objective": "{{core_objective}}",
      "entry_actions": [],
      "exit_conditions": {{exit_conditions}},
      "next_states": ["{{next_state_name}}"]
    }
  ],
  "guidelines": {{guidelines}},
  "observations": {{observations}},
  "_metadata": {
    "source": "{{source_type}}",  // "internet_research" | "data_agent" | "business_description"
    "deep_research_reports": ["{{report_paths}}"],
    "created_at": "{{timestamp}}",
    "version": "1.0"
  }
}
```

**提示词中必须包含的样例和说明**:
```markdown
## 输出格式要求

你必须严格按照以下 JSON Schema 输出 Journey 配置:

```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "description": "流程名称，必须简洁明了"
    },
    "description": {
      "type": "string",
      "description": "流程描述，说明该流程的用途和触发场景"
    },
    "trigger_conditions": {
      "type": "array",
      "items": {"type": "string"},
      "description": "触发条件列表，满足任一条件即进入该流程"
    },
    "states": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": {"type": "string"},
          "description": {"type": "string"},
          "core_objective": {
            "type": "string",
            "description": "该状态的核心主目标，必须唯一且可量化"
          },
          "exit_conditions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "结束条件列表，必须包含合规校验要求"
          },
          "next_states": {
            "type": "array",
            "items": {"type": "string"},
            "description": "下一状态列表，支持分支跳转"
          }
        },
        "required": ["name", "core_objective", "exit_conditions"]
      }
    }
  },
  "required": ["name", "description", "trigger_conditions", "states"]
}
```

## 示例 (日本共安保险寿险营销场景)

```json
{
  "name": "客户进线与需求初判",
  "description": "完成合规接待与意向确认，匹配对应营销员",
  "trigger_conditions": [
    "客户主动发起咨询",
    "客户通过 LINE 进线",
    "客户参加说明会后咨询"
  ],
  "states": [
    {
      "name": "初访待对接",
      "description": "客户首次进线，完成基本信息收集与意向确认",
      "core_objective": "完成合规接待与意向确认，匹配对应营销员",
      "exit_conditions": [
        "已告知个人信息使用规则，客户确认",
        "明确核心咨询意向",
        "符合《个人信息保护法》,全局合规校验通过"
      ],
      "next_states": ["需求调研中"]
    }
  ],
  "_metadata": {
    "source": "internet_research",
    "deep_research_reports": [
      "step3_research_reports/japanese_insurance_law.md",
      "step3_research_reports/customer_protection_act.md"
    ]
  }
}
```

## 注意事项

1. **核心主目标唯一性**: 每个状态只能有一个核心主目标，禁止设置多个
2. **结束条件可量化**: 所有结束条件必须可验证、可量化，禁止模糊表述
3. **合规嵌入**: 结束条件必须包含「全局合规校验通过」
4. **术语引用**: 所有术语必须来自全局术语库，禁止私自定义
5. **来源标注**: _metadata 中必须标注数据来源和 Deep Research 报告路径
```

---

## 六、工具服务设计优化

### 6.1 Deep Research 工具强化

**问题**: 当前 Deep Research 调用样例数据，未实际执行搜索

**解决方案**:

1. **强制调用机制**:
   ```python
   class BaseSOPAgent(ReActAgent):
       async def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
           # 强制调用 Deep Research
           if self.require_deep_research():
               research_query = self.build_research_query(task, context)
               research_report = await self.call_tool(
                   "deep_research_search",
                   query=research_query,
                   max_depth=3,
                   max_iters=30
               )
               
               # 保存研究报告
               await self.save_research_report(research_report, task)
               
               # 将研究报告注入上下文
               context["deep_research_report"] = research_report
           
           # 执行正常流程
           return await super().execute(task, context)
   
       def require_deep_research(self) -> bool:
           """判断是否需要调用 Deep Research"""
           return True  # 默认都需要，可被子类重写
   ```

2. **搜索话题拆分**:
   ```python
   async def search_with_decomposition(query: str) -> List[str]:
       """
       将复杂查询分解为小方向并发搜索
       """
       # 使用 LLM 分解查询
       sub_queries = await llm_decompose_query(query)
       
       # 并发搜索
       tasks = [
           call_deep_research(q) for q in sub_queries
       ]
       results = await asyncio.gather(*tasks)
       
       # 汇总结果
       return combine_results(results)
   ```

3. **输出要求**:
   - 每个 Journey 至少包含 3 个互联网来源
   - 所有规则和术语必须标注来源
   - 研究报告存入 `step{N}_research_reports/` 目录

### 6.2 工具服务清单

| 工具名 | 提供方 | 用途 | 输入 | 输出 | 优化点 |
|--------|--------|------|------|------|--------|
| `deep_research_search` | AgentScope | 深度研究搜索 (多步推理) | query, max_depth, max_iters | 综合研究报告 | 强制调用、话题拆分、报告保存 |
| `tavily-search` | Tavily MCP | 基础网页搜索 | query, search_depth | 搜索结果列表 | 作为 Deep Research 补充 |
| `tavily-extract` | Tavily MCP | 网页内容提取 | urls[], extract_depth | 网页正文内容 | - |
| `write_text_file` | Local FS | 文件写入 | file_path, content | 写入结果 | 增加版本控制 |
| `read_text_file` | Local FS | 文件读取 | file_path | 文件内容 | - |
| `repair_json` | json_repair | JSON 格式修复 | invalid_json_string | 修复后的 JSON | 最大重试 3 次 |
| `debate_moderate` | 自研 | 辩论主持与记录 | agents[], topic, rounds | 辩论记录 | 新增工具 |
| `compute_embedding` | SentenceTransformer | Embedding 向量计算 | text_list | embeddings | 增加缓存机制 |
| `compute_similarity` | sklearn | 余弦相似度计算 | vectors_a, vectors_b | similarity_scores | - |

---

## 七、输出产物设计

### 7.1 中间产物 (每步输出)

| 步骤 | 文件名 | 格式 | 用途 | 可选性 |
|------|--------|------|------|--------|
| Step 1 | step1_clarification_questions.md | Markdown | 待用户澄清的问题清单 (+用户反馈记录) | 必需 |
| Step 1 | step1_structured_requirements.md | Markdown | 结构化的需求规格说明 | 必需 |
| Step 2 | step2_business_objectives.md | Markdown | 业务价值与目标 | 必需 |
| Step 2 | step2_main_sop_backbone.json | JSON | 主 SOP 主干 (冻结) | 必需 |
| Step 2 | step2_debate_history.json | JSON | 辩论记录 (可追溯) | 必需 |
| Step 2 | global_objective.md | Markdown | 全局目标文件 (防偏离) | 必需 |
| Step 3 | agent_guidelines.json | JSON | 全局规则配置（agent-level guideline） | 必需 |
| Step 3 | step3_glossary_master.json | JSON | 全局统一术语库 | 必需 |
| Step 3 | step3_research_reports/*.md | Markdown | Deep Research 报告集 | 必需 |
| Step 4 | agent_user_profiles.json | JSON | 用户画像配置 | 必需 |
| Step 5 | step5_journeys_*.json | JSON | 流程定义 (Parlant Journey 格式) | 必需 |
| Step 5 | step5_guidelines_*.json | JSON | 规约定义 (Parlant Guideline 格式) | 必需 |
| Step 5 | step5_tools_*.json | JSON | 工具定义 (Parlant Tool 格式) | 必需 |
| Step 5 | step5_glossary_*.json | JSON | 词汇定义 (Parlant Glossary 格式) | 必需 |
| Step 5 | step5_summary_*.md | Markdown | 分支 SOP 总结文档 | 必需 |
| Step 5 | step5_qa_report_*.json | JSON | 质检报告 | 必需 |
| Step 5 | step5_correction_history.json | JSON | 修正历史记录 | 必需 |
| Step 6 | step6_edge_case_sops.json | JSON | 子弹 SOP 原子化库 | 必需 |
| Step 6 | step6_supplementary_rules.json | JSON | 补充规则 | 必需 |
| Step 6 | step6_validation_report.json | JSON | 验证报告 | 必需 |
| Step 7 | step7_assembly_report.md | Markdown | 组装报告 | 必需 |
| Step 8 | step8_validation_report.md | Markdown | 最终验证报告 (含差异标注) | 必需 |
| Step 8 | step8_compliance_certificate.json | JSON | 合规证书 | 必需 |

### 7.2 过程产物增强

**新增过程产物**:
1. **REACT 对话记录**: `step{N}_react_history.json`
   - 记录每个 Agent 的 REACT 多轮对话
   - 包含思考过程和工具调用历史
   
2. **辩论记录**: `step{N}_debate_history.json`
   - 记录多 Agent 辩论全过程
   - 包含各方观点和最终结论

3. **Deep Research 报告**: `step{N}_research_reports/`
   - 每次 Deep Research 调用的详细报告
   - 包含搜索查询、子任务分解、中间结果、最终报告

4. **目标对齐检查记录**: `step{N}_objective_alignment.json`
   - 记录每次输出的目标对齐检查结果
   - 防止 Agent 偏离主题

### 7.3 最终产物质量标准

| 产物类型 | 质量指标 | 校验方法 | 目标值 |
|----------|---------|---------|--------|
| JSON 文件 | 符合 Parlant schema | json_repair + jsonschema 校验 | 100% 通过 |
| 主 SOP 主干 | 节点数 5-9 个，无分支 | 程序校验 + 人工抽检 | 100% 符合 |
| 分支 SOP | 单节点≤5 分支，1+2 铁律 | 程序校验 | 100% 符合 |
| 子弹 SOP | 1 场景 1SOP，插件式 | 程序校验 | 100% 符合 |
| 全局规则 | 无冲突，全链路嵌入 | ComplianceCheckAgent 校验 | 100% 一致 |
| 术语库 | 统一定义，无私自定义 | 术语一致性检查 | 100% 统一 |
| Deep Research | 每个 Journey≥3 个来源 | 来源计数检查 | 100% 达标 |
| 效果验证 | 主流程流转通过率 | 模拟测试 | ≥95% |
| 效果验证 | 边缘场景覆盖率 | 覆盖度测试 | 100% |
| 效果验证 | 合规校验通过率 | 合规检查 | 100% |

---

## 八、工程化改进

### 8.1 日志系统优化

**问题**: 当前代码使用大量 Print，不利于问题定位

**解决方案**: 使用 `logrus` 日志库

**实施步骤**:

1. **安装依赖**:
   ```bash
   pip install logrus
   ```

2. **更新 requirements.txt**:
   ```diff
   + logrus>=0.1.0
   - (移除 print 相关依赖，如果有)
   ```

3. **代码改造示例**:
   ```python
   # 旧代码
   print(f"Starting process design for task: {task}")
   
   # 新代码
   from logrus import logger
   
   logger.info(f"Starting process design for task: {task}")
   ```

4. **日志级别规范**:
   | 级别 | 使用场景 | 示例 |
   |------|---------|------|
   | DEBUG | 调试信息，详细执行过程 | `logger.debug(f"Calling tool: {tool_name}")` |
   | INFO | 正常流程信息 | `logger.info(f"Step {N} completed")` |
   | WARNING | 警告但不影响执行 | `logger.warning("JSON repair failed, retrying...")` |
   | ERROR | 错误但已捕获 | `logger.error(f"Agent execution failed: {error}")` |
   | CRITICAL | 严重错误，系统终止 | `logger.critical("Database connection lost")` |

5. **日志输出目录**:
   ```
   logs/
   ├── mining_agents.log          # 主日志文件
   ├── step1_requirement.log      # Step 1 专用日志
   ├── step2_main_sop.log         # Step 2 专用日志
   ├── step3_global_rules.log     # Step 3 专用日志
   ├── ...
   └── error.log                  # 错误日志汇总
   ```

### 8.2 错误处理机制

**错误分类与处理策略**:

| 错误类型 | 重试次数 | 重试间隔 | 降级策略 | 日志记录 |
|----------|----------|----------|----------|---------|
| **网络错误** | 3 次 | 指数退避 (2s, 4s, 8s) | 提示检查网络，保存当前状态 | ERROR + 堆栈跟踪 |
| **LLM 超时** | 2 次 | 5 秒 | 切换到备用模型，保存部分结果 | ERROR + 超时详情 |
| **JSON 校验失败** | 3 次 | - | 调用 Agent 修正，仍失败则跳过该文件 | WARNING + 原始 JSON |
| **Deep Research 超时** | 0 次 | - | 记录已获取的部分结果，继续执行 | WARNING + 部分报告 |
| **Agent 执行错误** | 1 次 | - | 记录日志，提示重试或跳过 | ERROR + 输入输出快照 |
| **文件 IO 错误** | 0 次 | - | 提示检查文件权限和路径 | ERROR + 文件路径 |

**异常处理框架**:
```python
from functools import wraps
from typing import Optional, Callable
import asyncio

def retry_on_error(
    max_retries: int = 3,
    delay: float = 2.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    重试装饰器，支持指数退避
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_delay = delay
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        logger.error(f"{func.__name__} failed after {max_retries} retries: {e}")
                        raise
                    
                    logger.warning(f"{func.__name__} attempt {attempt + 1} failed: {e}, retrying in {current_delay}s...")
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
            
            return None
        return wrapper
    return decorator

# 使用示例
@retry_on_error(max_retries=3, delay=2.0, exceptions=(ConnectionError, TimeoutError))
async def call_deep_research(query: str) -> str:
    # ... 实现代码
    pass
```

### 8.3 测试验证机制

**测试策略**:

1. **单元测试**: 针对每个 Agent 的核心方法
   ```python
   # tests/test_branch_sop_agent.py
   import pytest
   from src.mining_agents.agents.branch_sop_agent import BranchSOPAgent
   
   class TestBranchSOPAgent:
       @pytest.mark.asyncio
       async def test_one_plus_two_rule(self):
           """测试 1+2 铁律执行情况"""
           agent = BranchSOPAgent()
           result = await agent.generate_branches(node="节点 1", core_dimension="用户画像")
           
           assert len(result["branches"]) <= 5
           for branch in result["branches"]:
               assert len(branch["supplemental_dimensions"]) <= 2
   ```

2. **集成测试**: 测试完整流程
   ```python
   # tests/test_full_pipeline.py
   @pytest.mark.integration
   def test_full_8_step_pipeline():
       """测试完整 8 步流程"""
       config = load_test_config()
       result = run_full_pipeline(config)
       
       assert result["main_sop"]["nodes_count"] >= 5
       assert result["main_sop"]["nodes_count"] <= 9
       assert result["branch_sops"]["max_branches_per_node"] <= 5
       assert result["validation"]["compliance_passed"] == True
   ```

3. **端到端测试**: 使用真实业务场景
   ```python
   # tests/e2e/test_insurance_scenario.py
   @pytest.mark.e2e
   def test_insurance_retention_scenario():
       """测试保险挽留场景"""
       input_data = {
           "business_description": "日本共安保险寿险营销场景...",
           "skip_clarification": True
       }
       
       output = run_mining_agents(input_data)
       
       # 验证输出质量
       assert output["journeys_count"] > 0
       assert output["deep_research_reports_count"] >= 3 * output["journeys_count"]
   ```

---

## 九、扩展性与维护性

### 9.1 扩展点设计

| 扩展点 | 扩展方式 | 影响范围 | 示例 |
|--------|---------|---------|------|
| **新增 Agent 类型** | 继承 AgentScope 的 Agent 基类，实现特定逻辑 | 需在 Step 管理中注册 | 新增 ComplianceAgent |
| **新增工具** | 实现 MCP 兼容的工具接口，注册到 toolkit | 需在 Agent 配置中引用 | 新增知识库检索工具 |
| **新增步骤** | 在 StepManager 中注册新的 step handler | 需定义输入输出 schema | 新增 Step 9: 效果追踪 |
| **更换 LLM 提供商** | 修改 system_config.yaml 中的 model 配置 | 无需修改代码 | DashScope → OpenAI |
| **更换 Embedding 模型** | 修改 system_config.yaml 中的 embedding_service 配置 | 无需修改代码 | SentenceTransformer → OpenAI Embedding |
| **新增 SOP 层级** | 扩展 3 层架构为 N 层 | 需修改 Step 5 和 Step 6 逻辑 | 4 层架构 (主干/分支/子分支/子弹) |

### 9.2 维护性保障

1. **配置与代码分离**: 
   - 所有 Prompt、Agent 配置、系统配置均在 YAML 文件中
   - 修改配置无需改动代码

2. **模块化设计**: 
   - 每个 Agent 职责单一，便于单独维护和测试
   - Agent 之间松耦合，通过 StepManager 协调

3. **日志与监控**: 
   - 完整的执行日志 (使用 logrus)
   - 状态监控和告警机制

4. **版本控制**: 
   - 内置 Git 版本管理
   - 支持配置回滚和变更追踪
   - 所有输出产物纳入版本管理

5. **文档完备性**: 
   - 详细的设计文档 (本系列文档)
   - API 文档和使用说明
   - 常见问题 FAQ

6. **代码注释规范**:
   ```python
   class BranchSOPAgent(ReActAgent):
       """
       二级分支 SOP 挖掘 Agent
       
       职责:
           - 基于主 SOP 节点，挖掘二级分支 SOP
           - 遵守 1+2 铁律 (1 个核心区分维度 + 最多 2 个补充适配维度)
           - 单节点分支数严格≤5 个
       
       输入:
           - node: 主 SOP 节点信息
           - global_rules: 全局规则库
           - glossary_master: 全局术语库
       
       输出:
           - journeys: 分支 SOP 流程定义
           - guidelines: 分支规约
           - glossary: 分支术语
       
       约束:
           - 局部规则不得与全局规则冲突
           - 每个分支必须回归主流程对应节点
           - 术语仅能引用全局库，禁止私自定义
       """
       
       async def generate_branches(
           self,
           node: Dict[str, Any],
           core_dimension: str,
           supplemental_dimensions: Optional[List[str]] = None
       ) -> Dict[str, Any]:
           """
           生成分支 SOP
           
           Args:
               node: 主 SOP 节点信息
               core_dimension: 核心区分维度 (三选一)
               supplemental_dimensions: 补充适配维度 (最多 2 个)
           
           Returns:
               包含 branches, journeys, guidelines 等的字典
           
           Raises:
               ValueError: 当维度数量超过限制时
               ComplianceError: 当规则与全局规则冲突时
           """
           # ... 实现代码
   ```

---

## 十、风险评估与缓解措施

| 风险 | 影响 | 可能性 | 缓解措施 |
|------|------|--------|---------|
| **维度越界与排列组合爆炸** | 主流程混乱，状态机难以跟踪 | 高 | 1. 每层维度使用规则锁死; 2. 严格执行分支数≤5; 3. 效果验证阶段全量校验 |
| **合规风险** | 监管处罚，保单无效 | 高 | 1. 合规全链路前置; 2. 法定红线嵌入结束条件; 3. 合规一票否决权 |
| **大模型幻觉与虚假内容** | 输出内容不可信 | 中 | 1. 所有输出必须标注来源; 2. 术语仅引用全局库; 3. 历史案例交叉验证 |
| **流程失控与状态机混乱** | 流程无法落地 | 中 | 1. 主 SOP 主干冻结后禁止修改; 2. 严格按 Pipeline 顺序执行; 3. 每个节点明确结束条件 |
| **Agent 偏离主题** | 输出不符合预期 | 中 | 1. 全局目标文件约束; 2. Prompt 中包含自检问题; 3. 循环校验机制 |
| **并发数过高导致资源耗尽** | 系统崩溃 | 低 | 1. 根据硬件资源合理设置 max_parallel_agents; 2. 资源隔离机制; 3. 限流保护 |
| **Deep Research 调用失败** | 互联网信息获取不充分 | 低 | 1. 多次重试机制; 2. 备用搜索方案; 3. 部分结果也可接受 |

---

## 十一、实施计划与建议

### 11.1 分阶段实施计划

**阶段 1: 核心流程重构** (预计 3-5 天)
- [ ] 实现 8 步法流程框架
- [ ] 新增 CoordinatorAgent、MainSOPMiningAgent
- [ ] 实现 Step 2 的目标对齐与主 SOP 挖掘
- [ ] 实现 Step 5 的并行挖掘机制

**阶段 2: Agent 职责优化** (预计 2-3 天)
- [ ] 新增 GlobalRulesAgent、UserProfileAgent
- [ ] 新增 BranchSOPAgent、EdgeCaseSOPAgent
- [ ] 优化现有 Agent 职责边界
- [ ] 实现中枢管控机制

**阶段 3: 配置与提示词完善** (预计 2-3 天)
- [ ] 完善 Parlant 配置模板
- [ ] 优化所有 Agent 的提示词 (加入样例和字段说明)
- [ ] 实现 Deep Research 强制调用机制
- [ ] 配置系统参数优化

**阶段 4: 工程化改进** (预计 2-3 天)
- [ ] 使用 logrus 替换 Print
- [ ] 实现完善的错误处理机制
- [ ] 编写单元测试和集成测试
- [ ] 性能优化和并发测试

**阶段 5: 端到端验证** (预计 2-3 天)
- [ ] 使用真实业务场景测试 (如日本共安保险)
- [ ] 对比新旧流程输出质量
- [ ] 收集用户反馈并迭代优化
- [ ] 编写使用文档和 FAQ

### 11.2 关键成功因素

1. **用户确认**: 本方案需经用户确认后再开始实施
2. **最小化改动**: 每次迭代保持最小化改动，便于回滚
3. **充分测试**: 每个阶段完成后进行充分测试
4. **文档同步**: 代码变更同步更新设计文档
5. **版本管理**: 使用 Git 进行版本控制，支持快速回滚

### 11.3 验收标准

| 验收项 | 验收方法 | 通过标准 |
|--------|---------|---------|
| **流程正确性** | 端到端测试 | 8 步流程完整执行，无错误 |
| **输出质量** | 对比样例配置 | 符合 Parlant schema，内容深入且准确 |
| **并发性能** | 性能测试 | 整体执行时间减少 50%+ |
| **合规校验** | 合规检查 | 100% 通过合规校验 |
| **术语统一** | 术语一致性检查 | 全流程术语 100% 统一 |
| **Deep Research** | 来源计数 | 每个 Journey≥3 个互联网来源 |
| **日志规范** | 日志审查 | 100% 使用 logrus，无 Print |
| **测试覆盖** | 测试报告 | 单元测试覆盖率≥80% |

---

## 十二、需要用户确认的关键点

### 12.1 流程设计确认

✅ **请确认**:
1. 是否同意将当前的 5 步法升级为 8 步法？
2. Step 3-6 的并行执行策略是否符合预期？
3. Step 5 内部的 5 个子步骤是否合理？

### 12.2 Agent 设计确认

✅ **请确认**:
1. 是否需要新增 CoordinatorAgent 作为中枢管控？
2. Agent 职责划分是否清晰合理？
3. 是否需要额外的 Agent 角色？

### 12.3 并发策略确认

✅ **请确认**:
1. `max_parallel_agents` 的默认值设置为多少合适？(建议：4-8)
2. Step 5 是否允许节点内子步骤并行？(串行更安全，并行更快)
3. 是否需要动态调整并发数的机制？

### 12.4 配置规范确认

✅ **请确认**:
1. Parlant 配置模板是否符合需求？
2. 提示词中加入样例和字段说明是否足够？
3. Deep Research 强制调用次数是否合理？(建议：每个 Journey≥3 次)

### 12.5 工程化改进确认

✅ **请确认**:
1. 是否同意使用 logrus 替换 Print?
2. 错误处理策略是否符合预期？
3. 是否需要额外的监控或告警机制？

---

## 十三、下一步行动

### 用户确认后，将执行:

1. **创建新的设计文档**:
   - `01_overall_design_v6.md` (总体设计)
   - `02_eight_step_pipeline.md` (8 步法详细设计)
   - `03_agent_roles_and_responsibilities.md` (Agent 职责)
   - `04_concurrency_and_parallelism.md` (并发与并行)
   - `05_configuration_specification.md` (配置规范)
   - `06_engineering_best_practices.md` (工程化最佳实践)

2. **更新索引文件**:
   - 更新 `index.md` 添加新文档链接

3. **代码实施**:
   - 按照分阶段计划逐步实施
   - 每个阶段完成后提交测试报告

4. **持续迭代**:
   - 根据测试结果和用户反馈持续优化

---

**最后更新**: 2026-03-30  
**维护者**: System Team  
**状态**: ⏳ 待用户确认

---

## 附录 A: 术语表

| 术语 | 定义 |
|------|------|
| **主 SOP 主干** | 一级主流程，全局唯一，5-9 个节点，无分支 |
| **分支 SOP** | 二级流程，依附于主 SOP 节点，单节点≤5 个分支 |
| **子弹 SOP** | 三级流程，边缘场景原子化补全，1 场景 1SOP |
| **1+2 铁律** | 1 个核心区分维度 + 最多 2 个补充适配维度 |
| **中枢管控 Agent** | 负责全局目标对齐和多 Agent 协调的 Agent |
| **Deep Research** | 基于 AgentScope 的深度研究工具，支持多步推理 |
| **REACT 模式** | 反思 - 行动循环模式，用于自我检查和修正 |
| **合规一票否决权** | 合规校验不通过则整个流程终止 |

## 附录 B: 参考文档

1. Parlant 官方文档：`docs/tools_docs/parlant_docs/`
2. AgentScope 框架文档：`docs/tools_docs/agentscope_docs/`
3. 现有设计文档 (v5.0): `docs/dev_docs/design_docs/mining_agents/`
4. SOP 挖掘新方案设计：`docs/dev_docs/design_process_log/a_design_refine.md`
5. TODO 清单：`egs_llm_app/b04_conversation_insight/a002_chatbot_insight_analyzer/TODO.md`
