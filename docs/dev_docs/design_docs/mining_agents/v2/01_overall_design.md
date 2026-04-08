# Parlant Agent 配置挖掘系统 - 总体设计

**版本**: v2.0 (8 步法架构版)  
**创建日期**: 2026-03-30  
**最后更新**: 2026-04-06  
**文档类型**: 系统架构设计（纯架构，无代码）

---

## 🚀 快速导读

### 一句话总结

本设计方案将当前的**5 步线性流程**升级为**8 步并行流程**,引入**中枢管控 Agent**和**3 层 SOP 架构**,实现执行效率提升 50%+,输出质量标准化 100%。

### 核心改进点 TOP 5

#### 1️⃣ 流程重构：5 步 → 8 步
```
旧流程：Step1→Step2→Step3→Step4→Step5 (线性，无并行)
新流程：Step1→Step2→[Step3‖Step4]→Step5(多任务并发)→Step6(多任务并发)→Step7→Step8
```

**关键收益**:
- ✅ **Step 3-4 可并行**: GlobalRulesAgent ‖ UserProfileAgent
- ✅ **Step 5 高度并发**: N 个主 SOP 节点完全并行 (每个节点独立执行 5.1-5.5 子任务)
- ✅ **Step 6 多任务并发**: M 个边缘场景同时挖掘
- ✅ 新增 Step 2: 目标对齐与主 SOP 主干挖掘 (防止偏离主题)
- ✅ 新增 Step 7-8: 配置组装与最终校验 (串行保证质量)

#### 2️⃣ 中枢管控：CoordinatorAgent
**职责**: 全局目标对齐 + 多 Agent 辩论组织

**核心机制**:
- 🎯 在 Step 2 组织 RuleEngineerAgent、DomainExpertAgent 进行辩论
- 🎯 确定业务核心价值、主 SOP 范围、分支内容方向
- 🎯 写入 `global_objective.md` 防止后续 Agent 偏离主题

**解决的问题**:
- ❌ Agent 易偏离总主题
- ❌ 各 Agent 口径不一致
- ❌ 缺少全局视角

#### 3️⃣ 设计原则体系 (8 大原则 + 10 条红线)

**8 大核心设计原则**:
1. 🎯 **主干唯一不可逆**: 全流程仅一条无分支主 SOP，冻结后禁止修改
2. 🔒 **维度分层锁死**: 每层 SOP 仅能用指定维度，禁止跨层
3. ⚖️ **合规全链路前置**: 合规嵌入每个环节，非事后校验
4. 🌐 **全局 - 局部协同**: 全局规则/术语统一，局部不得冲突
5. 📏 **粒度解耦可控**: 主 SOP 粗 (5-9 节点)、分支中 (≤5 分支)、子弹细 (1 场景 1SOP)
6. 🎯 **目标对齐防偏离**: 每个 Agent 明确总目标和子目标
7. ⚡ **并发安全与隔离**: 高度并发同时确保数据一致性
8. 📝 **过程可追溯**: 所有决策、辩论、修正历史完整保存

**优先级顺序** (发生冲突时):
```
合规性 > 主干唯一性 > 维度分层 > 全局协同 > 粒度解耦 > 
目标对齐 > 并发安全 > 过程可追溯
```

**10 条避坑红线 (绝对不能碰)**:
1. ❌ 一个节点设置多个核心主目标 → 主流程状态机失控
2. ❌ 把可选子目标纳入强制结束条件 → 流程卡壳
3. ❌ 使用模糊、主观的结束条件 → 无法验证完成度
4. ❌ 结束条件和合规要求脱节 → 巨大合规风险
5. ❌ 跨节点设置目标 → 打乱主流程顺序
6. ❌ 主流程节点超过 9 个或有分支 → 状态机复杂度爆炸
7. ❌ 单个节点内分支超过 5 个 → 排列组合爆炸
8. ❌ 一个分支里用了超过 3 个维度 → 维度滥用导致混乱
9. ❌ 用补充维度拆了新的分支 → 分支数量失控
10. ❌ 跨节点做了维度组合 → 状态机混乱

#### 4️⃣ Agent 并行关系全景图

**前后依赖关系图**:
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
Step 5 (高度并发 - 核心优化点):
  For each 主 SOP 节点 i (完全并行):
    BranchSOPAgent_i → RuleEngineerAgent_i
           ↓                ↓
    GlossaryAgent_i ←──────┘
           ↓
    SummaryAgent_i
           ↓
    QualityAgent_i (检查前三个的输出)
         ↓ (所有节点完成后)
Step 6 (多任务并发):
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

**合规校验分层说明（避免误解）**：
- **Step 3 / Step 4**：产物落盘后立即执行 `ComplianceCheckAgent` **门控校验**，用于快速阻断“空产物/关键字段缺失/明显结构错误”等高风险输出；不通过则该步骤失败并要求重跑。
- **Step 8**：在完整配置包层面执行**全量校验**（schema/状态机/冲突/跨文件一致性），并输出 `step8_validation_report.md` + `step8_compliance_certificate.json`。

**Step 8（可选）工程化增强**：
- **Auto-fix（默认关闭）**：对“JSON 解析失败但可被 `json_repair` 修复”的文件，允许回写修复后的 JSON（`step8_auto_fix_json.enabled`）。
- **返工门控（默认关闭）**：基于 `quality_score` 质量分触发回跳返工（`step8_quality_gate.enabled`），低于阈值可回跳到指定步骤重跑，且限制最大返工轮数避免无限回路。

**并行开关说明（工程化配置）**：
- Step3‖Step4 并行：`concurrency.enable_step3_step4_parallel`（默认可关闭，迁移期建议按需开启）
- Step3 内部并行（可选）：`concurrency.enable_step3_globalrules_glossary_parallel`（GlobalRulesAgent ‖ GlossaryAgent，默认关闭）

**并行度分析表** (以 6 节点主 SOP 为例):

| 步骤 | 串行/并行 | 可并行对象 | 最大并发数 | 预计加速比 |
|------|----------|-----------|-----------|-----------|
| Step 1 | 串行 | - | 1 | 1x |
| Step 2 | 串行 (内部有依赖) | CoordinatorAgent → MainSOPMiningAgent | 1 | 1x |
| Step 3 | **可并行 Step 4** | GlobalRulesAgent ‖ UserProfileAgent | 2 | 1.5x |
| Step 4 | **可并行 Step 3** | UserProfileAgent ‖ GlobalRulesAgent | 2 | 1.5x |
| **Step 5** | **多任务并发** | **N 个主 SOP 节点完全并行** | **N (建议≤8)** | **5-8x** |
| **Step 6** | **多任务并发** | **M 个边缘场景并行** | **M (建议≤5)** | **2-3x** |
| Step 7 | 串行 | - | 1 | 1x |
| Step 8 | 串行 | - | 1 | 1x |

**整体加速比估算**:
- 旧方案 (串行): 6 × 10 分钟 = 60 分钟
- 新方案 (并行，max_parallel=6): 10 分钟
- **加速比**: 理论 6x，实际约 4-5x (考虑资源竞争)

#### 5️⃣ 工程化改进

- ❌ Print → ✅ logrus
- 完善的重试机制 (网络错误 3 次指数退避)
- 单元测试覆盖率≥80%
- 集成测试覆盖完整流程
- 端到端测试使用真实业务场景

---

## 一、系统定位与设计目标

### 1.1 系统定位

本系统是一个基于 AgentScope 框架的多 Agent 协作系统，用于自动化生成 Parlant 客服 Agent 的完整配置包。系统采用**8 步法 SOP 挖掘流程**,通过中枢管控机制组织多 Agent 辩论，从人工提供的业务描述文档和外部 Data Agent 分析生成的私域对话数据结果中挖掘并生成符合 Parlant 规范的结构化配置。

### 1.2 设计目标

| 目标 | 说明 |
|------|------|
| **8 步法流程** | Step1(需求澄清)→Step2(目标对齐与主 SOP 挖掘)→Step3(全局规则)→Step4(用户画像)→Step5(分支 SOP 并行挖掘)→Step6(边缘场景)→Step7(配置组装)→Step8(最终校验) |
| **3 层 SOP 架构** | 一级主 SOP(主干层，5-9 节点) → 二级分支 SOP(适配层，≤5 分支) → 三级子弹 SOP(补全层，1 场景 1SOP) |
| **中枢管控机制** | CoordinatorAgent 负责全局目标对齐、组织多 Agent 辩论、写入 global_objective.md |
| **高度并发** | Step 5 的 N 个主 SOP 节点完全并行，预计加速比 5-8x(以 6 节点为例，理论 6x，实际 4-5x) |
| **Deep Research 强制调用** | 每个 Journey 至少调用 3 次，搜索话题拆分，报告完整保存 |
| **可追溯输出** | 每步独立存储，支持断点续跑、快速重启特定阶段 |
| **格式校验** | 内置 json_repair 校验机制，确保输出符合 Parlant schema |

---

## 二、系统总体架构

### 2.1 顶层架构图 (8 步法版)

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
│  │                  StepManager(步骤管理器)                         │   │
│  │   - 步骤调度  - 状态持久化  - 断点续跑  - 结果加载                │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                  ↓                                       │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │               AgentOrchestrator(Agent 编排器)                     │   │
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
│                    Agent 协作层 (8 步法流程)                              │
│                                                                          │
│  Step 1         Step 2          Step 3         Step 4                   │
│  需求澄清     → 目标对齐      → 全局规则    → 用户画像                  │
│  +人工确认     +主 SOP 主干     +术语库      +多维画像                  │
│               +业务价值       +DeepResearch                             │
│               (串行)          (Step 3‖Step 4 可并行)                       │
│                                                                          │
│  Step 5 (高度并发 - 核心优化点)                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  For each 主 SOP 节点：并发执行                                        │  │
│  │   5.1 子 SOP 挖掘  →  5.2 术语提取  →  5.3 规则生成                 │  │
│  │         ↓                  ↓                 ↓                      │  │
│  │   5.4 子 SOP 总结  ←  5.5 质量校验 (含格式校验)                      │  │
│  │                                                                    │  │
│  │  [Node_1] [Node_2] ... [Node_N] 完全并行 (加速比 5-8x)             │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  Step 6 (多任务并发)        Step 7          Step 8                      │
│  边缘场景挖掘              → 配置组装    → 最终校验                     │
│  M 个场景并行               + 目录组装    + 格式校验                    │
│  + 补充规则                 + 验证报告    + 正式输出                    │
│                              (串行)                                      │
└─────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                        工具服务层 (MCP 协议)                              │
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
│  │  Parlant 配置包 (agents/{agent_name}/...)                          │  │
│  │  ├── 00_agent_base/ (元数据、术语表、用户画像)                     │  │
│  │  ├── 01_agent_rules/ (全局规则、观测、话术)                        │  │
│  │  │   └── 注入 chat_state 和 condition 判定逻辑                      │  │
│  │  ├── 02_journeys/ (SOP 流程、状态机)                               │  │
│  │  │   ├── {main_journey_name}/ (来自主 SOP 主干)                    │  │
│  │  │   │   ├── sop.json                                              │  │
│  │  │   │   └── sop_guidelines.json (该主 Journey 专属的全局规则引用) │  │
│  │  │   ├── {branch_journey_name}/ (来自 Step 5 分支 SOP)            │  │
│  │  │   │   ├── sop.json                                              │  │
│  │  │   │   └── sop_guidelines.json (该分支专属的规则)               │  │
│  │  │   └── {edge_case_journey_name}/ (来自 Step 6 子弹 SOP)         │  │
│  │  │       ├── sop.json                                              │  │
│  │  │       └── sop_guidelines.json (该边缘场景专属的规则)           │  │
│  │  └── 03_tools/ (工具元数据、实现代码)                              │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  过程产物 (可追溯)                                                 │  │
│  │  ├── step1_clarification_questions.md (+用户反馈记录)             │  │
│  │  ├── step1_structured_requirements.md                            │  │
│  │  ├── step2_global_objective.md (中枢管控目标对齐文件)             │  │
│  │  ├── step2_main_sop_nodes.yaml (主 SOP 节点列表，5-9 节点)         │  │
│  │  ├── agent_guidelines.json (Step 3 产物：全局规则 / agent-level guideline，工程化落盘文件名) │  │
│  │  ├── step3_glossary_master.json (Step 3 产物：全局统一术语库 / Glossary master)   │  │
│  │  ├── agent_user_profiles.json (Step 4 产物：用户画像 / user segments + personas，工程化落盘文件名) │
│  │  ├── step5_branch_sops_{node_id}.json (各节点分支 SOP,符合 Parlant Journey 格式) │
│  │  ├── step6_edge_case_sops.json (边缘场景子弹 SOP,符合 Parlant Journey 格式) │
│  │  ├── step7_assembly_report.md (组装报告)                         │  │
│  │  ├── step8_validation_report.md (最终验证报告)                   │  │
│  │  └── step8_compliance_certificate.json (合规证书)                │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 核心组件说明 (8 步法版)

| 组件 | 职责 | **调用的工具** | 关键特性 |
|------|------|--------------|----------|
| **StepManager** | 步骤调度与状态管理 | - | 每步落盘、支持 `--start-step`/`--end-step` 参数跳过已完成阶段 |
| **AgentOrchestrator** | Agent 编排与并发控制 | - | 根据 `max_parallel_agents` 配置决定串行/并行执行策略，Step 5 实现完全并行 |
| **Human-in-the-Loop Interface** | 人工确认与反馈收集 | - | Step 1 后暂停等待用户确认、支持修改/补充问题、超时处理 |
| **CoordinatorAgent** | 中枢管控 (新增) | **Debate**(组织辩论), **FileSystem**(读写辩论记录), **MessageArchive**(保存辩论过程) | Step 2 使用、组织多 Agent 辩论、分析未覆盖的用户角色/业务场景/边缘情况、写入 global_objective.md |
| **MainSOPMiningAgent** | 主 SOP 挖掘 (新增) | **FileSystem**(读取全局目标), **JsonRepair**(格式校验), **StateMachineValidator**(状态机校验) | Step 2 使用、挖掘 5-9 节点的主 SOP 主干、无分支、冻结后禁止修改 |
| **GlobalRulesAgent** | 全局规则设计 | **DeepResearch**(行业最佳实践搜索), **FileSystem**(保存规则 + 报告), **Embedding**(规则相似度计算) | Step 3 使用、制定全局规则和术语体系、Deep Research 强制调用≥3 次 |
| **UserProfileAgent** | 用户画像设计 (新增) | **DeepResearch**(用户画像框架), **FileSystem**(画像配置保存), **Embedding**(画像维度聚类) | Step 4 使用、构建多维用户画像、制定画像到规则的映射关系 |
| **BranchSOPAgent** | 分支 SOP 挖掘 (新增) | **FileSystem**(读取主 SOP+ 规则 + 画像), **ParlantJourneyAPI**(Journey 模板加载), **JsonRepair**(格式预检) | Step 5 使用、针对每个主 SOP 节点并行挖掘分支 SOP、遵守 1+2 铁律、单节点≤5 分支 |
| **EdgeCaseSOPAgent** | 边缘 SOP 挖掘 (新增) | **FileSystem**(读取客诉案例 + 失败工单), **ParlantJourneyAPI**(原子 Journey 模板), **ComplianceAPI**(合规风险标注) | Step 6 使用、挖掘边缘异常场景的子弹 SOP、1 场景 1SOP、插件式设计 |
| **ConfigAssemblerAgent** | 配置组装 | **FileSystem**(读取所有中间产物), **ParlantSchemaValidator**(官方 schema 验证), **ConfigInjector**(chat_state/condition 注入) | Step 7 使用、按照 Parlant 官方目录结构组织文件、3 层 Journey 架构 |
| **QualityValidatorAgent** | 质量校验 (新增) | **JsonRepair**(JSON 修复), **JsonSchema**(schema 验证), **StateMachineValidator**(状态机死循环检查), **FileSystem**(读取待校验文件) | Step 8 使用、最终格式校验、合规性检查、输出验证报告 |
| **工具服务层** | 统一工具接口 (MCP 协议) | Deep Research、文件系统、JSON 校验、Debate、HumanLoop、Embedding、StateMachineValidator | MCP 协议封装、统一接口标准 |
| **输出产物层** | Parlant 配置包 + 过程产物 | - | 符合官方 schema、注入 chat_state/condition、3 层 Journey 原子化、过程产物可追溯 |

---

## 三、8 步法核心设计理念

### 3.1 两阶段挖掘模式 (核心设计)

**重要**: 每个挖掘步骤都遵循**"先内容挖掘，后格式套用"**的两阶段模式:

```
阶段 1: 基于 Parlant 目标与规则要求进行内容挖掘
  ├─ 加载 Parlant 核心概念与指导原则 (非详细格式)
  ├─ 理解业务需求与 Parlant 最佳实践
  ├─ 进行内容挖掘与决策
  └─ 产出结构化中间产物 (Markdown/YAML/JSON)

       ↓

阶段 2: 加载 Parlant 详细 schema 与格式约束
  ├─ 加载官方完整 schema 定义
  ├─ 加载输出样例与模板
  ├─ 将中间产物转换为符合官方 schema 的格式
  └─ 进行格式校验与修正
```

**各步骤的两阶段挖掘示例**:

| 步骤 | 阶段 1: 内容挖掘 (加载什么) | 阶段 2: 格式套用 (加载什么) |
|------|--------------------------|--------------------------|
| **Step 3**<br>全局规则 | • `journey_rule_requirements.md` (规则分类框架)<br>• `glossary_requirements.md` (术语库指导)<br>• Parlant Guidelines 核心概念<br>• 行业最佳实践 (Deep Research) | • `parlant_schema_full.json` (Guideline schema)<br>• `guideline_output_examples.json` (规则样例)<br>• JSON Schema 验证器 |
| **Step 4**<br>用户画像 | • `user_profile_requirements.md` (画像维度框架)<br>• `profile_dimension_constraints.md` (维度约束)<br>• Parlant Customer 核心概念<br>• 用户画像行业标准 (Deep Research) | • `customer_profile_template.json` (画像模板)<br>• `user_profile_examples.json` (画像样例)<br>• JSON Schema 验证器 |
| **Step 5**<br>分支 SOP | • `journey_branch_requirements.md` (分支指导)<br>• `journey_schema_outline.md` (Journey 概览)<br>• 1+2 铁律说明<br>• Parlant Journey 核心概念 | • `journey_output_examples.json` (Journey 样例)<br>• `parlant_journey_schema.json` (详细 schema)<br>• JsonRepair 预检工具 |
| **Step 6**<br>边缘场景 | • `edge_case_requirements.md` (边缘场景指导)<br>• `atomic_journey_outline.md` (原子 Journey 概览)<br>• `compliance_risk_requirements.md` (合规风险指导)<br>• 1 场景 1SOP 原则 | • `journey_output_examples.json` (边缘场景样例)<br>• `parlant_journey_schema.json` (详细 schema)<br>• ComplianceAPI 合规校验 |
| **Step 7**<br>配置组装 | • 所有中间产物 (Step 2-6)<br>• chat_state_injection_template.md (注入模板) | • `parlant_schema_full.json` (官方完整 schema)<br>• `journey_output_examples.json` (全量样例)<br>• ParlantSchemaValidator 全量验证 |

**关键优势**:
1. ✅ **解耦内容与格式**: Agent 先专注于业务逻辑，再考虑格式约束
2. ✅ **降低认知负担**: 避免同时处理业务规则和复杂 schema
3. ✅ **提高输出质量**: 专业的内容挖掘 + 专业的格式校验
4. ✅ **便于人工审核**: 中间产物可读性强，易于理解和修改
5. ✅ **支持灵活调整**: 更换 schema 版本时，仅需修改阶段 2

---

### 3.2 8 大核心设计原则

| 原则 | 说明 | 违反后果 |
|------|------|----------|
| **主干唯一不可逆** | 主 SOP 是单一权威主干，所有分支必须明确标注"偏离主干"，禁止循环路径 | 流程混乱、死循环 |
| **维度分层锁死** | 严格区分主 SOP(主干层)、分支 SOP(适配层)、子弹 SOP(补全层),层级之间禁止跨越 | 层级混乱、维护困难 |
| **合规全链路前置** | 所有合规相关规则必须在全局规则层 (Step 3) 统一定义，禁止在分支 SOP 中临时添加 | 合规风险、审计失败 |
| **全局 - 局部协同** | 全局规则 (Step 3) 与分支 SOP 规则 (Step 5) 必须明确优先级和排除关系 | 规则冲突、行为不一致 |
| **粒度解耦可控** | 主 SOP 节点聚焦单一核心目标，分支 SOP 依附于主 SOP 节点，禁止一个节点多个主目标 | 粒度过粗、难以维护 |
| **目标对齐防偏离** | CoordinatorAgent 在 Step 2 写入 global_objective.md，后续所有 Agent 必须读取并对齐 | 目标偏离、产出不符预期 |
| **并发安全与隔离** | Step 5 的 N 个主 SOP 节点完全并行，每个节点拥有独立工作目录，避免文件冲突 | 并发冲突、数据损坏 |
| **过程可追溯** | 每步独立存储中间产物，支持断点续跑、快速重启特定阶段，便于问题定位和审计 | 无法追溯、调试困难 |

### 3.2 设计优先级顺序

```
最高优先级：主干唯一不可逆 > 维度分层锁死 > 合规全链路前置
中等优先级：全局 - 局部协同 > 粒度解耦可控 > 目标对齐防偏离
基础保障：并发安全与隔离 > 过程可追溯
```

### 3.3 10 条避坑红线

| 红线 | 说明 | 检查方法 |
|------|------|----------|
| **禁止一个节点多个主目标** | 每个主 SOP 节点只能有一个核心目标，禁止"完成 A 并且 B" | 检查节点 instruction 是否包含多个动词 |
| **禁止模糊结束条件** | 每个节点必须有明确的退出条件，禁止"适当时候"等模糊表述 | 检查 transition 的 condition 是否为布尔表达式 |
| **禁止主流程超过 9 节点** | 主 SOP 节点数量控制在 5-9 个，超过则拆解为多个主 SOP | 统计主 SOP 节点数量 |
| **禁止分支超过 5 个** | 单个主 SOP 节点的分支 SOP 数量≤5 个，超过则重新设计 | 统计 branch_sops 数组长度 |
| **禁止循环依赖** | guideline 的 exclusions 和 dependencies 不能形成环 | 图论算法检测环 |
| **禁止 dead-end 状态** | Journey 状态机不能有死胡同，所有状态必须有出口 | 图遍历算法检查 |
| **禁止 chat_state 缺失** | 所有 guideline 必须包含 chat_state 字段 | JSON Schema 校验 |
| **禁止 condition 模糊匹配** | condition 必须使用标准布尔表达式 (支持 AND/OR/NOT) | 正则表达式校验语法 |
| **禁止 Deep Research 滥用** | 每个 Journey 至少调用 3 次，但禁止过度调用 (>10 次) | 统计 Deep Research 调用次数 |
| **禁止配置文件硬编码** | 所有配置参数必须在 YAML 文件中定义，禁止在代码中硬编码 | 代码审查 |

---

## 四、3 层 SOP 架构详解

### 4.1 一级主 SOP(主干层)

**特征**:
- **节点数量**: 5-9 个节点
- **无分支设计**: 主干不包含任何分支，所有分支剥离到二级
- **冻结机制**: 主 SOP 一旦确定并写入 `step2_main_sop_nodes.yaml`,后续步骤禁止修改
- **核心目标**: 每个节点聚焦单一核心目标

**示例结构**:
```yaml
main_sop_nodes:
  - node_id: "node_000"
    node_name: "初访待对接"
    instruction: "友好问候用户，询问用户想要咨询的业务类型"
    exit_condition: "用户已明确表达业务需求"
    
  - node_id: "node_001"
    node_name: "需求调研中"
    instruction: "深入询问用户的具体需求细节"
    exit_condition: "用户需求已被充分理解和记录"
    
  - node_id: "node_002"
    node_name: "方案推荐中"
    instruction: "基于用户需求推荐合适的解决方案"
    exit_condition: "用户已了解方案详情并做出选择"
    
  # ... 更多节点，总计 5-9 个
```

### 4.2 二级分支 SOP(适配层)

**特征**:
- **依附关系**: 每个分支 SOP 明确标注所属的主 SOP 节点 ID(`parent_node_id`)
- **1+2 铁律**: 1 个主目标 + 最多 2 个辅助目标
- **分支数量限制**: 单节点≤5 个分支
- **遵守主干**: 分支 SOP 必须遵守主 SOP 的核心逻辑，禁止颠覆主干

**示例结构**:
```json
{
  "branch_sop_id": "branch_appt_dept_select",
  "parent_node_id": "node_002",
  "branch_name": "科室选择分支",
  "trigger_condition": "用户想要预约挂号但未明确科室",
  "sop_states": [
    {
      "state_id": "branch_state_000",
      "instruction": "介绍医院主要科室分类",
      "transitions": [...]
    }
  ]
}
```

### 4.3 三级子弹 SOP(补全层)

**特征**:
- **原子化设计**: 1 场景 1SOP，每个子弹 SOP 只处理一个边缘异常场景
- **插件式**: 可插拔设计，不影响主流程和分支流程
- **明确标注**: `is_edge_case: true`,`priority: 1`(最低优先级)

**示例场景**:
- 用户突然改变主意
- 系统故障降级方案
- 敏感词触发合规流程
- VIP 客户特殊处理

**示例结构**:
```json
{
  "edge_case_sop_id": "edge_user_change_mind",
  "parent_node_id": "node_002",
  "scene_description": "用户在方案推荐过程中突然表示'我再考虑一下'",
  "is_edge_case": true,
  "priority": 1,
  "sop_states": [
    {
      "state_id": "edge_state_000",
      "instruction": "表示理解，提供保留方案的选项",
      "transitions": [...]
    }
  ]
}
```

---

## 五、并发策略与性能优化

### 5.1 Step 5 并发机制

**并发模型**:
```
For each 主 SOP 节点 node_i:
    启动并发任务 Task_i:
        5.1 BranchSOPAgent 挖掘分支 SOP
        5.2 GlossaryExtractor 提取术语
        5.3 RuleGenerator 生成规则
        5.4 SummaryWriter 撰写总结
        5.5 QualityValidator 质量校验
        
If max_parallel_agents > 1:
    所有 Task_i 完全并行 (i=1,2,...,N)
Else:
    所有 Task_i 串行执行
```

**并发数计算**:
- **理论加速比**: N (主 SOP 节点数量，通常 5-9)
- **实际加速比**: 4-5x (考虑资源竞争和同步开销)
- **推荐配置**: `max_parallel_agents = 8`(适应大多数场景)

**Step 5.2 术语提取增强要求**:

每个分支节点生成的术语库应满足以下要求：

| 术语类别 | 数量要求 | 示例术语 |
|---------|---------|---------|
| **产品术语** | 4-6个 | 终身寿险、定期寿险、重大疾病险、医疗保险、年金保险、万能险 |
| **业务/流程术语** | 5-7个 | 冷静期、等待期、免责条款、保额、保费、现金价值、犹豫期 |
| **合规/法规术语** | 4-6个 | 说明义务、适合性确认、明示同意、保险营销合规、反洗钱、信息披露 |
| **服务/沟通术语** | 2-4个 | 挽留话术、需求分析、方案定制、异议处理 |

**术语生成总要求**:
- **总术语数**: 15-20个
- **语言一致性**: 与业务描述语言保持一致
- **定义准确性**: 每个术语必须有明确的业务定义
- **同义词覆盖**: 提供用户可能使用的同义表达
- **term_id规范**: 使用 `{业务前缀}_{node_id}_term_{序号}` 格式

### 5.2 资源隔离机制

每个并发任务拥有独立的工作目录:
```
workspace/
├── task_node_000_workdir/
│   ├── tmp/           # 临时文件
│   ├── findings/      # 中间发现
│   └── output/        # 最终输出
├── task_node_001_workdir/
└── ...
```

### 5.3 并发安全保证

1. **文件锁**: 使用文件锁机制防止并发写入冲突
2. **独立上下文**: 每个任务独立的内存上下文
3. **原子操作**: 关键写操作使用原子操作
4. **超时控制**: 每个任务设置超时时间，避免长时间阻塞

---

## 六、Parlant 配置目录结构 (3 层 Journey 架构)

### 6.1 Journey 命名与映射规则 (SOP 术语说明)

> **重要术语说明**: 
> 
> #### Parlant 官方术语与工程化配置别名对照表
> 
> | Parlant 官方术语 | 工程化配置别名 | 说明 |
> |-----------------|---------------|------|
> | **Journey** | SOP (Standard Operating Procedure) | 结构化对话流程，包含状态机、转换条件等。Journey 是 Parlant 官方术语；SOP 是本方案针对业务流程场景提出的易懂别名 |
> | **Guideline** | 规则 | 条件-动作对的行为规则，格式为"当 X 时，做 Y"。Guideline 是 Parlant 核心概念；规则是中文语境下的通俗表达 |
> | **Observation** | 观测 | 仅检测状态不包含动作的 Guideline，用于触发其他元素。用于门控指南、排除冲突、工具触发等场景 |
> | **Canned Response** | 预设回复 / 固定话术 | 预审批的回复模板，消除幻觉风险。用于合规披露、法律义务、敏感话题等场景 |
> | **Glossary** | 术语表 / 术语库 | 领域专用词汇表，将口语术语对应到精确业务定义 |
> | **Tool** | 工具 | 外部 API 和工作流的封装，仅在 Observation 匹配时触发 |
> | **Agent** | 智能体 | 与用户交互的定制化 AI 人格 |
> | **Customer** | 客户 / 用户 | 与 Agent 互动的终端用户 |
> | **Variable** | 变量 | 存储动态数据，支持个性化和上下文记忆 |
> | **Tag** | 标签 | 分类跟踪对话事件的字符串标签 |
> | **Preamble** | 序言 | 简短的致谢语，保持对话自然响应 |
> 
> #### Journey 相关术语对照
> 
> | Parlant 官方术语 | 工程化配置别名 | 说明 |
> |-----------------|---------------|------|
> | **Journey Title** | SOP 名称 / 流程名称 | Journey 的简短描述性名称 |
> | **Journey Conditions** | 触发条件 / 进入条件 | 决定 Journey 何时被激活的上下文查询列表 |
> | **Chat State** | 聊天状态 | Agent 与客户对话的状态，可花费多轮 |
> | **Tool State** | 工具状态 | Agent 调用外部工具执行动作并加载结果到上下文 |
> | **Fork State** | 分叉状态 | 评估条件并分支对话流的路由状态 |
> | **Direct Transition** | 直接转换 | 总是执行的转移（无条件） |
> | **Conditional Transition** | 条件转换 | 仅在条件满足时执行的转移 |
> | **Journey-Scoped Guideline** | Journey 专属规则 / SOP 专属规则 | 仅在该 Journey 激活时才生效的 Guideline |
> | **Journey-Scoped Canned Response** | Journey 专属话术 | 仅在该 Journey 激活时才考虑的话术模板 |
> 
> #### Guideline 关系术语对照
> 
> | Parlant 官方术语 | 工程化配置别名 | 说明 |
> |-----------------|---------------|------|
> | **Exclusions** | 排除关系 | 当 S 和 T 同时激活时，只有 S 激活 |
> | **Dependencies** | 依赖关系 | 当 S 激活时，除非 T 也激活否则关闭 |
> | **Entailment** | 后产关系 | 当 S 激活时，T 也应该始终被激活 |
> | **Disambiguation** | 消歧义关系 | 当 S 激活且多个 T 激活时，请客户澄清 |
> 
> #### 3 层 SOP 架构与 Parlant Journey 对应关系
> 
> | 层级 | 名称 | Parlant 对应 | 特征 |
> |-----|------|-------------|------|
> | **一级** | 主 SOP (主干层) | Main Journey | 5-9 个节点，无分支，冻结后禁止修改 |
> | **二级** | 分支 SOP (适配层) | Branch Journey | 依附于主 SOP 节点，单节点≤5 分支，遵守 1+2 铁律 |
> | **三级** | 子弹 SOP (补全层) | Edge Case Journey | 边缘异常场景原子化，1 场景 1SOP，插件式设计 |
> 
> #### 文档使用规范
> 
> - 技术实现层面统一使用 "Journey"
> - 业务描述层面可使用"SOP"作为易懂的别名
> - 配置文件字段保留 `sop_id`, `sop_title` 等历史命名 (向后兼容)
> - 代码注释优先使用 Parlant 官方术语，便于与官方文档对照

**核心原则**: 每个分支 Journey 和边缘场景 Journey 必须明确标注其所属的主 Journey,通过 `parent_node_id` 建立映射关系。

**命名规范**:
```
main_journey_name:     {业务场景}_main (例：appointment_booking_main)
branch_journey_name:   {main_journey_name}__branch_{分支标识} (例：appointment_booking_main__branch_dept_selection)
edge_case_journey_name: {main_journey_name}__edge_{场景标识} (例：appointment_booking_main__edge_user_change_mind)
```

**映射关系示例**:
```
主 Journey: appointment_booking_main (node_002: 方案推荐中)
├─ 分支 Journey 1: appointment_booking_main__branch_dept_selection (科室选择分支)
├─ 分支 Journey 2: appointment_booking_main__branch_time_selection (时间选择分支)
└─ 边缘场景 Journey 1: appointment_booking_main__edge_user_change_mind (用户改变主意)
```

### 6.2 目录结构设计

```
parlant_agent_config/
├── agents/
│   └── {agent_name}/
│       ├── 00_agent_base/
│       │   ├── agent_metadata.json
│       │   ├── agent_observability.json
│       │   ├── agent_user_profiles.json
│       │   └── glossary/
│       │       └── glossary_master.json (合并后的术语库，包含Step 3全局术语 + Step 5各分支术语)
│       ├── 01_agent_rules/
│       │   ├── agent_guidelines.json (仅来自 Step 3 - 全局规则)
│       │   ├── agent_observations.json
│       │   └── agent_canned_responses.json
│       ├── 02_journeys/
│       │   ├── {main_journey_name}/ (来自主 SOP 主干)
│       │   │   ├── sop.json
│       │   │   └── sop_guidelines.json (该主 Journey 专属的全局规则引用)
│       │   ├── branch_{节点名称}_{node_id}/ (来自 Step 5 分支 SOP，命名示例: branch_合规告知与继续意愿确认_node_002)
│       │   │   ├── sop.json
│       │   │   ├── sop_guidelines.json (该分支专属的规则)
│       │   │   ├── sop_canned_responses.json (可选)
│       │   │   ├── sop_observations.json (可选)
│       │   │   └── **parent_node_id**: "node_002" (映射到主 Journey 的节点 ID)
│       │   └── edge_{场景名称}_{parent_node_id}_{index}/ (来自 Step 6 子弹 SOP - 边缘场景)
│       │       ├── sop.json
│       │       ├── sop_guidelines.json (该边缘场景专属的规则)
│       │       └── **parent_node_id**: "node_002", **is_edge_case**: true
│       └── 03_tools/
│           └── {tool_name}/
│               ├── tool_meta.json
│               └── tool_impl.py
└── automation/
    └── build_agent.py (可选，用于自动化构建)
```

**目录命名规则说明**:

1. **分支 Journey 命名规则** (Step 5 输出):
   - 格式: `branch_{节点名称}_{node_id}`
   - 示例: `branch_呼叫接入与身份确认_node_001`
   - 节点名称从 `step2_main_sop_nodes.yaml` 中获取
   - 被模型判断为不需要二级分支的节点，不会创建对应目录

2. **边缘场景 Journey 命名规则** (Step 6 输出):
   - 格式: `edge_{场景名称}_{parent_node_id}_{index}`
   - 示例: `edge_用户改变主意_node_002_001`

3. **Glossary 合并规则** (Step 7 处理):
   - 合并来源: Step 3 全局术语库 + Step 5 各分支术语文件
   - 去重策略: 基于 `term_id` 去重
   - 重新编号: 统一编号为 `{业务前缀}_term_{序号}` 格式
   - 输出位置: `00_agent_base/glossary/glossary_master.json`

### 6.3 Step 7 配置组装详细逻辑

**ConfigAssemblerAgent 处理流程**:

```
Step 7 输入:
├── Step 2: main_sop_backbone.json (主 SOP 主干)
├── Step 3: agent_guidelines.json, step3_glossary_master.json, agent_observations.json
├── Step 4: agent_user_profiles.json
├── Step 5: node_{node_id}/ 目录 (各节点分支产物)
│   ├── step5_journeys_{node_id}.json
│   ├── step5_guidelines_{node_id}.json
│   ├── step5_glossary_{node_id}.json
│   └── sop_observations_{node_id}.json
└── Step 6: step6_edge_case_sops.json

Step 7 处理逻辑:
1. Glossary 合并:
   - 读取 Step 3 的 glossary_master.json
   - 遍历 Step 5 各节点的 glossary 文件
   - 合并所有术语，基于 term_id 去重
   - 重新统一编号
   - 输出到 00_agent_base/glossary/glossary_master.json

2. 分支 Journey 目录创建:
   - 读取 main_sop_backbone.json 获取节点列表
   - 对于每个节点:
     a. 检查 step5_journeys_{node_id}.json 的 skipped_by_model 标记
     b. 如果被跳过，跳过该节点，不创建目录
     c. 如果未跳过:
        - 获取节点名称 (从 main_sop_nodes 中)
        - 创建目录: branch_{节点名称}_{node_id}/
        - 复制 sop.json, sop_guidelines.json 等文件

3. 边缘场景 Journey 目录创建:
   - 读取 step6_edge_case_sops.json
   - 为每个边缘场景创建目录: edge_{场景名称}_{parent_node_id}_{index}/

4. 主 Journey 组装:
   - 创建 {main_journey_name}/ 目录
   - 生成主 sop.json (包含所有子 Journey 的链接关系)
   - 生成主 sop_guidelines.json (引用全局规则)
```

**被跳过分支处理**:
- 当模型判断某节点不需要二级分支时，step5_journeys_{node_id}.json 会包含 `skipped_by_model: true`
- Step 7 检测到该标记后，不会为该节点创建 branch_ 目录
- 避免生成无意义的"skipped"占位文件

### 6.4 Step 5 输出与 Journey 映射

**Step 5 输出结构** (针对每个主 SOP 节点并发执行):

根据 Parlant 官方文档和工程化配置规范，每个 Journey 输出包含 3 个核心配置文件:

> **重要说明**: Parlant 官方 API 中，Observations 本质是"没有 action 的 Guideline",Canned Responses 可直接隶属于 Journey 或 State。但为便于人工维护和审核，本方案采用以下工程化目录结构:
> - `sop.json`: Journey 流程核心文件 (对应 Parlant Journey)
> - `sop_guidelines.json`: Journey 专属规则 (包含该 Journey 专属的 Guidelines + Canned Responses)
> - `sop_observations.json`: Journey 专属观测条件 (仅包含 condition，无 action，对应 Parlant Observational Guidelines)

#### (1) sop.json - Journey 流程核心文件

```json
{
  "sop_id": "branch_dept_select_001",
  "sop_type": "branch",
  "parent_sop_id": "appointment_booking_main",
  "parent_state_id": "node_002",
  "sop_title": "科室选择分支 Journey",
  "sop_description": "当用户不确定选择哪个科室时，引导用户描述症状，智能推荐合适的科室",
  "trigger_conditions": [
    "用户不知道该挂哪个科室",
    "用户询问科室推荐",
    "用户描述症状但未确定科室"
  ],
  "timeout": 1800,
  "sop_states": [
    {
      "state_id": "branch_state_000",
      "state_name": "症状收集",
      "state_type": "chat",
      "instruction": "询问用户的主要症状或不适部位，收集足够信息用于科室推荐",
      "bind_guideline_ids": [],
      "transitions": [
        {
          "target_state_id": "branch_state_001",
          "condition": "用户已描述主要症状"
        }
      ]
    },
    {
      "state_id": "branch_state_001",
      "state_name": "科室推荐",
      "state_type": "chat",
      "instruction": "根据用户描述的症状，推荐 1-3 个合适的科室，并说明推荐理由",
      "bind_guideline_ids": ["branch_dept_recommend_001"],
      "transitions": [
        {
          "target_state_id": "branch_state_002",
          "condition": "用户接受推荐并选择科室"
        },
        {
          "target_state_id": "branch_state_000",
          "condition": "用户需要提供更多症状信息"
        }
      ]
    },
    {
      "state_id": "branch_state_002",
      "state_name": "分支结束",
      "state_type": "chat",
      "instruction": "确认用户选择的科室，引导返回主 Journey 流程继续预约",
      "is_end_state": true,
      "return_to_parent": true
    }
  ]
}
```

#### (2) sop_guidelines.json - Journey 专属规则与话术

> **Parlant 官方对应关系**:
> - `sop_canned_responses` → 对应 `journey.create_canned_response()` 创建的 Journey 专属话术
> - `sop_scoped_guidelines` → 对应 `journey.create_guideline()` 创建的 Journey 专属规则
> - **注意**: 所有 Guidelines 必须包含 `scope` 字段，值为 `"sop_only"`(Journey 专属) 或 `"agent_global"`(Agent 全局)

```json
{
  "sop_id": "branch_dept_select_001",
  "sop_title": "科室选择分支 Journey",
  "remark": "科室选择分支专属规则",
  "sop_canned_responses": [
    {
      "canned_response_id": "branch_cr_symptom_ask_001",
      "content": "为了帮您推荐最合适的科室，请告诉我您的主要症状是什么？比如哪里不舒服、持续多久了？",
      "language": "zh-CN"
    },
    {
      "canned_response_id": "branch_cr_dept_recommend_001",
      "content": "根据您描述的{symptoms}，建议您挂{recommended_dept}。{reason}",
      "language": "zh-CN"
    }
  ],
  "sop_scoped_guidelines": [
    {
      "guideline_id": "branch_dept_symptom_collect_001",
      "scope": "sop_only",
      "condition": "用户进入科室选择分支，未描述症状",
      "action": "使用症状询问模板话术，引导用户描述主要症状",
      "priority": 4,
      "composition_mode": "FLUID",
      "bind_canned_response_ids": ["branch_cr_symptom_ask_001"],
      "exclusions": [],
      "dependencies": []
    },
    {
      "guideline_id": "branch_dept_recommend_001",
      "scope": "sop_only",
      "condition": "用户已描述症状，需要推荐科室",
      "action": "根据症状智能推荐科室，说明推荐理由",
      "priority": 5,
      "composition_mode": "FLUID",
      "bind_canned_response_ids": ["branch_cr_dept_recommend_001"],
      "exclusions": ["branch_dept_symptom_collect_001"],
      "dependencies": []
    }
  ]
}
```

#### (3) sop_observations.json - Journey 专属观测条件

> **Parlant 官方对应关系**:
> - Observations 本质是"没有 action 的 Guideline",用于通过关系激活/停用其他 Guidelines 或 Journeys
> - 官方 API: `await agent.create_observation(matcher=...)`
> - 本工程化配置将 Observations 独立存储，便于人工维护和审核
> - **注意**: Observations 仅包含 `condition` 字段，不包含`action` 字段

```json
{
  "sop_id": "branch_dept_select_001",
  "sop_title": "科室选择分支 Journey",
  "remark": "科室选择分支专属观测",
  "sop_observations": [
    {
      "observation_id": "branch_obs_user_has_symptom_001",
      "condition": "用户已描述主要症状或不适部位",
      "remark": "观测用户是否已提供症状信息，用于科室推荐的依赖"
    },
    {
      "observation_id": "branch_obs_user_accept_recommend_001",
      "condition": "用户接受了推荐的科室",
      "remark": "观测用户是否接受推荐，用于确认返回主 Journey 的依赖"
    }
  ]
}
```

**Journey 核心组件说明** (基于 Parlant 官方文档):
1. **Title (`sop_title`)**: 简短描述性的 Journey 名称
2. **Trigger Conditions**: 上下文查询列表，决定 Journey 何时被激活 (进入条件)，对应官方的 `conditions` 参数
3. **Description (`sop_description`)**: Journey 的性质描述
4. **States & Transitions**: 状态图，向 Agent 传达理想流程
   - **Chat States (`state_type: "chat"`)**: Agent 与客户对话的状态，可花费多轮直到决定转移，对应官方`transition_to(chat_state=...)`
   - **Tool States (`state_type: "tool"`)**: Agent 调用外部工具执行动作并加载结果到上下文，对应官方`transition_to(tool_state=...)`,需绑定`bind_tool_id`
   - **Direct Transitions**: 总是执行的转移 (无 condition 字段或使用 always 条件)
   - **Conditional Transitions**: 仅在条件满足时执行的转移 (包含 `condition` 字段)
5. **Journey-Scoped Guidelines**: 仅在该 Journey 激活时才生效的规则，必须在 `scope` 字段标注`"sop_only"`
6. **Journey-Scoped Canned Responses**: 仅在该 Journey 激活时才考虑的话术模板

### 6.4 Step 6 输出与 Journey 映射

**Step 6 输出结构** (多任务并发挖掘边缘场景):

边缘场景 Journey 同样输出 3 个核心配置文件:

#### (1) sop.json - 边缘场景 Journey 流程核心文件

```json
{
  "sop_id": "edge_user_change_mind_001",
  "sop_type": "edge",
  "parent_sop_id": "appointment_booking_main",
  "sop_title": "用户改变主意场景 Journey",
  "sop_description": "处理用户在预约过程中突然表示'我再考虑一下'或'暂时不需要'等场景",
  "is_edge_case": true,
  "priority": 1,
  "trigger_conditions": [
    "用户表示'我再考虑一下'",
    "用户表示'暂时不需要'",
    "用户表示'以后再说'",
    "用户想要退出预约流程"
  ],
  "timeout": 900,
  "sop_states": [
    {
      "state_id": "edge_state_000",
      "state_name": "理解与挽留",
      "state_type": "chat",
      "instruction": "表示理解用户的决定，友好询问是否需要保留已选择的预约信息",
      "bind_canned_response_ids": ["edge_cr_understand_001"],
      "transitions": [
        {
          "target_state_id": "edge_state_001",
          "condition": "用户愿意保留信息"
        },
        {
          "target_state_id": "edge_state_002",
          "condition": "用户确认退出"
        }
      ]
    },
    {
      "state_id": "edge_state_001",
      "state_name": "信息保留",
      "state_type": "chat",
      "instruction": "告知用户已保留其选择的信息，下次可以直接继续预约",
      "is_end_state": true
    },
    {
      "state_id": "edge_state_002",
      "state_name": "友好结束",
      "state_type": "chat",
      "instruction": "礼貌结束对话，告知用户随时可以回来咨询",
      "is_end_state": true
    }
  ]
}
```

#### (2) sop_guidelines.json - 边缘场景专属规则

```json
{
  "sop_id": "edge_user_change_mind_001",
  "sop_title": "用户改变主意场景 Journey",
  "remark": "用户改变主意场景专属规则",
  "sop_canned_responses": [
    {
      "canned_response_id": "edge_cr_understand_001",
      "content": "完全理解您的想法，预约就诊确实需要慎重考虑。请问您需要我为您保留当前已选择的科室和医生信息吗？这样您下次可以直接继续预约。",
      "language": "zh-CN"
    },
    {
      "canned_response_id": "edge_cr_keep_info_001",
      "content": "好的，我已经为您保留了选择的科室 ({dept}) 和医生 ({doctor}) 信息。您下次咨询时可以直接说'继续预约',我会帮您快速恢复。",
      "language": "zh-CN"
    }
  ],
  "sop_scoped_guidelines": [
    {
      "guideline_id": "edge_understand_001",
      "scope": "sop_only",
      "condition": "用户表示需要考虑或犹豫不决",
      "action": "使用理解与挽留模板话术，表达同理心，询问是否需要保留信息",
      "priority": 4,
      "composition_mode": "FLUID",
      "bind_canned_response_ids": ["edge_cr_understand_001"],
      "exclusions": [],
      "dependencies": []
    },
    {
      "guideline_id": "edge_keep_info_002",
      "scope": "sop_only",
      "condition": "用户愿意保留已选择的信息",
      "action": "使用信息保留模板话术，告知用户已保留的信息内容",
      "priority": 5,
      "composition_mode": "FLUID",
      "bind_canned_response_ids": ["edge_cr_keep_info_001"],
      "exclusions": ["edge_understand_001"],
      "dependencies": []
    }
  ]
}
```

#### (3) sop_observations.json - 边缘场景专属观测

```json
{
  "sop_id": "edge_user_change_mind_001",
  "sop_title": "用户改变主意场景 Journey",
  "remark": "用户改变主意场景专属观测",
  "sop_observations": [
    {
      "observation_id": "edge_obs_user_hesitate_001",
      "condition": "用户表达犹豫、需要考虑、暂时不需要等情绪",
      "remark": "观测用户是否有退出意向，用于触发边缘场景 Journey"
    },
    {
      "observation_id": "edge_obs_user_willing_keep_001",
      "condition": "用户表示愿意保留已选择的信息",
      "remark": "观测用户是否接受信息保留，用于后续关怀规则的依赖"
    }
  ]
}
```

### 6.5 关键设计原则

1. **命名前缀一致性**: 分支/边缘场景 Journey 必须包含主 Journey 名称作为前缀
2. **显式映射关系**: 通过 `parent_node_id` 字段明确标注所属主 SOP 节点
3. **唯一标识符**: `branch_identifier` 和 `edge_identifier` 在同一主 Journey 下必须唯一
4. **类型标记**: 边缘场景必须设置 `is_edge_case: true` 和 `priority` 字段
5. **多对一映射**: 多个分支 Journey 和多个边缘场景 Journey 可以映射到同一个主 Journey

---

## 七、与旧版 v1 的核心差异

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

**最后更新**: 2026-03-30  
**维护者**: System Team  
**文档版本**: v2.0 (8 步法架构版)
