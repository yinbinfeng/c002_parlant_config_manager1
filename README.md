# Mining Agents - Parlant 客服 Agent 配置挖掘系统

基于 AgentScope 框架的多 Agent 协作系统，用于自动化生成 Parlant 客服 Agent 的完整配置包。

## 目录

- [概述](#概述)
- [工程结构](#工程结构)
- [原理](#原理)
- [使用](#使用)
- [调试](#调试)
- [Vibe Coding](#vibe-coding)
- [不足](#不足)

---

## 概述

本系统是一个多 Agent 协作系统，通过 8 步法流程，从用户业务描述自动挖掘生成符合 Parlant 规范的客服 Agent 配置包，包括 Journey（流程）、Guideline（规则）、Glossary（术语）、Tool（工具）、UserProfile（用户画像）、CannedResponse（固定话术）等核心配置元素。

**核心价值**：将业务需求描述转化为可直接部署的 Parlant Agent 配置，支持 Deep Research 互联网调研、多 Agent 辩论、合规校验等高级特性。

---

## 工程结构

### 目录树

```
E:/cursorworkspace/c002_parlant_config_manager1/
├── egs/                                    # 入口与配置目录
│   └── v0.1.0_minging_agents/
│       ├── main.py                         # CLI主入口
│       ├── run_ui.py                       # UI入口（Streamlit）
│       ├── config/                         # 配置文件目录
│       │   ├── system_config.yaml          # 系统配置（并发/超时/模型）
│       │   ├── agents/                     # Agent提示词配置
│       │   │   ├── coordinator_agent.yaml
│       │   │   ├── global_rules_agent.yaml
│       │   │   ├── glossary_agent.yaml
│       │   │   ├── user_profile_agent.yaml
│       │   │   ├── requirement_analyst_agent.yaml
│       │   │   ├── compliance_check_agent.yaml
│       │   │   ├── config_assembler_agent.yaml
│       │   │   └── debate_prompts.yaml
│       │   └── mock/                       # Mock数据
│       │       ├── ui_examples.yaml
│       │       └── insurance_mock_data.yaml
│       └── scripts/
│           └── verify_output.py            # 输出验证脚本
│
├── src/                                    # 核心源码目录
│   └── mining_agents/
│       ├── engine.py                       # 引擎入口（注册步骤/工具）
│       ├── cli.py                          # CLI参数解析
│       ├── agents/                         # Agent实现
│       │   ├── base_agent.py               # Agent基类
│       │   ├── coordinator_agent.py        # 协调Agent
│       │   ├── global_rules_agent.py       # 全局规则Agent
│       │   ├── glossary_agent.py           # 术语Agent
│       │   ├── user_profile_agent.py       # 用户画像Agent
│       │   ├── requirement_analyst_agent.py
│       │   ├── compliance_check_agent.py
│       │   └── config_assembler_agent.py
│       ├── steps/                          # 步骤实现
│       │   ├── requirement_clarification.py    # Step1
│       │   ├── step2_objective_alignment_main_sop.py  # Step2
│       │   ├── step3_global_guidelines.py      # Step3
│       │   ├── step4_user_profiles.py          # Step4
│       │   ├── step5_branch_sop_parallel.py    # Step5
│       │   ├── step6_edge_cases.py             # Step6
│       │   ├── step7_config_assembly.py        # Step7
│       │   └── step8_validation.py             # Step8
│       ├── managers/                       # 管理器
│       │   ├── step_manager.py             # 步骤管理器
│       │   ├── agent_orchestrator.py       # Agent编排器
│       │   └── session_manager.py          # 会话管理器（UI用）
│       ├── tools/                          # 工具实现
│       │   ├── deep_research.py            # Deep Research工具
│       │   ├── deep_research_pool.py       # Deep Research实例池
│       │   ├── json_validator.py           # JSON校验工具
│       │   ├── file_service.py             # 文件服务工具
│       │   └── deep_research_agent/        # Deep Research Agent
│       │       └── deep_research_agent.py
│       └── utils/                          # 工具函数
│           ├── logger.py                   # 日志工具
│           ├── config_loader.py            # 配置加载器
│           ├── error_handler.py            # 错误处理
│           ├── performance_tracker.py      # 性能追踪
│           └── file_utils.py               # 文件工具
│
├── docs/                                   # 文档目录
│   ├── dev_docs/                           # 开发文档
│   │   ├── design_docs/                    # 设计文档
│   │   │   └── mining_agents/
│   │   │       ├── v1/                     # v1设计文档（已废弃）
│   │   │       └── v2/                     # v2设计文档（最新）
│   │   │           ├── index.md
│   │   │           └── 01_overall_design.md
│   │   ├── design_process_log/
│   │   │   └── auto_mining_refine.md       # Vibe Coding历史任务
│   │   └── parlant_agent_config/           # Parlant配置样例
│   │       └── agents/
│   │           ├── insurance_sales_agent/
│   │           └── medical_customer_service_agent/
│   └── tools_docs/                         # 框架文档
│       ├── agentscope_docs/                # AgentScope使用文档
│       └── parlant_docs/                   # Parlant使用文档
│
├── tests/                                  # 测试目录
│   ├── test_mvp.py
│   ├── test_debate_function.py
│   ├── test_deep_research_pool.py
│   └── ...
│
├── output/                                 # 输出目录（运行时生成）
│   ├── step1_requirement_clarification/
│   ├── step2_objective_alignment_main_sop/
│   ├── ...
│   ├── parlant_agent_config/
│   ├── final_parlant_config/
│   ├── performance_report.json
│   └── run_config_snapshot/
│
├── bkp/                                    # 备份目录
│   └── v1/                                 # v1版本备份
│
├── requirements.txt                        # 依赖清单
├── changelog.md                            # 修改日志
└── README.md                               # 本文件
```

### 核心模块说明

| 模块 | 路径 | 职责 |
|------|------|------|
| **入口层** | `egs/v0.1.0_minging_agents/` | CLI/UI启动、配置加载 |
| **引擎层** | `src/mining_agents/engine.py` | 步骤注册、工具注册、流程编排 |
| **Agent层** | `src/mining_agents/agents/` | 各业务Agent实现（ReAct模式） |
| **步骤层** | `src/mining_agents/steps/` | 8步法各步骤的业务逻辑 |
| **工具层** | `src/mining_agents/tools/` | Deep Research、JSON校验等工具 |
| **管理层** | `src/mining_agents/managers/` | 步骤管理、Agent编排、会话管理 |
| **配置层** | `egs/.../config/` | YAML配置文件（提示词、参数） |

---

## 原理

### 系统架构图

系统采用**五层架构**设计，自顶向下依次为用户输入层、AgentScope编排层、Agent协作层、工具服务层和输出产物层。各层职责清晰，通过标准化接口解耦。

**架构说明**：
- **用户输入层**：支持CLI命令行、Streamlit UI、API三种接入方式，统一接收业务描述输入
- **AgentScope编排层**：核心引擎`engine.py`负责步骤注册、工具注册和流程编排（串行/并行调度）
- **Agent协作层**：8步法流程的执行主体，各步骤由专用Agent负责，支持步骤间并行（如Step3║Step4）
- **工具服务层**：提供Deep Research（互联网调研）、JSON校验、文件服务等基础能力
- **输出产物层**：按Parlant规范组织输出目录，包含agent_base、agent_rules、journeys、tools四大模块

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              用户输入层                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │  CLI模式     │    │   UI模式     │    │  API模式     │                  │
│  │  main.py     │    │  run_ui.py   │    │  (预留)      │                  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                  │
└─────────┼───────────────────┼───────────────────┼──────────────────────────┘
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AgentScope编排层                                    │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                          engine.py                                    │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │   │
│  │  │ 步骤注册    │  │ 工具注册    │  │ 流程编排    │                  │   │
│  │  │ Step1-8     │  │ DeepResearch│  │ 串行/并行   │                  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Agent协作层（8步法）                                │
│                                                                              │
│  ┌────────┐   ┌────────┐   ┌────────────────┐   ┌────────┐                │
│  │ Step1  │──▶│ Step2  │──▶│ Step3 ║ Step4  │──▶│ Step5  │                │
│  │需求澄清│   │目标对齐│   │全局规则║用户画像│   │分支SOP │                │
│  └────────┘   └────────┘   └────────────────┘   └────┬───┘                │
│                                                   │                      │
│                                                   ▼                      │
│  ┌────────┐   ┌────────┐   ┌────────┐         ┌────────┐                │
│  │ Step8  │◀──│ Step7  │◀──│ Step6  │◀────────│ 并发   │                │
│  │最终校验│   │配置组装│   │边缘场景│         │ 执行   │                │
│  └────────┘   └────────┘   └────────┘         └────────┘                │
│                                                                              │
│  各步骤Agent:                                                                │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ RequirementAnalyst │ Coordinator │ GlobalRules │ Glossary │ UserProfile│  │
│  │ ComplianceCheck    │ ConfigAssembler │ ...                          │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            工具服务层                                        │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │  Deep Research   │  │  JSON Validator  │  │  File Service    │          │
│  │  ┌────────────┐  │  │  ┌────────────┐  │  │  ┌────────────┐  │          │
│  │  │ Tavily SDK │  │  │  │ json_repair│  │  │  │ 文件读写   │  │          │
│  │  │ LLM Client │  │  │  │ LLM修复    │  │  │  │ 目录管理   │  │          │
│  │  └────────────┘  │  │  └────────────┘  │  │  └────────────┘  │          │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘          │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            输出产物层                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      parlant_agent_config/                            │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐          │   │
│  │  │ 00_agent_base/ │  │ 01_agent_rules/│  │ 02_journeys/   │          │   │
│  │  │ ├─ metadata    │  │ ├─ guidelines  │  │ ├─ main_sop    │          │   │
│  │  │ ├─ user_profile│  │ ├─ observations│  │ ├─ branch_sop  │          │   │
│  │  │ └─ glossary    │  │ └─ canned_resp │  │ └─ edge_sop    │          │   │
│  │  └────────────────┘  └────────────────┘  └────────────────┘          │   │
│  │  ┌────────────────┐                                                   │   │
│  │  │ 03_tools/      │                                                   │   │
│  │  │ └─ tool_meta   │                                                   │   │
│  │  └────────────────┘                                                   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

**图解要点**：
- 箭头表示数据流向，自顶向下传递
- `Step3 ║ Step4` 表示并行执行，通过`enable_step3_step4_parallel`配置控制
- 工具服务层是共享资源，被多个Agent调用
- 输出产物层按Parlant规范组织，可直接部署到Parlant平台

### 8 步法流程图

8步法是系统的核心处理流程，从用户业务描述输入到最终输出Parlant配置包，涵盖需求澄清、目标对齐、规则生成、SOP挖掘、配置组装和校验等环节。

**流程特点**：
- **串行为主，局部并行**：Step1→Step2串行执行，Step3和Step4可并行，Step5/Step6支持节点级并发
- **人工介入点**：Step1澄清环节支持人工确认（可通过`--skip-clarification`跳过）
- **质量门控**：Step8进行最终校验，质量分低于阈值可触发返工（需手动开启）
- **并发控制**：通过`max_parallel_step5_nodes`和`max_parallel_edge_cases`参数控制并发粒度

**数据流向**：
```
业务描述 → Step1(澄清问题) → Step2(主SOP) → Step3/4(全局规则+用户画像) 
         → Step5(分支SOP并发) → Step6(边缘场景) → Step7(组装) → Step8(校验) → 最终配置包
```

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           用户业务描述输入                                   │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step1: 需求澄清                                                              │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ Agent: RequirementAnalystAgent                                          │ │
│ │ 工具: Deep Research (互联网调研行业合规要求)                             │ │
│ │ 输出: step1_clarification_questions.md, step1_structured_requirements.md│ │
│ │ 交互: 可跳过 (--skip-clarification)                                     │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step2: 目标对齐与主SOP主干                                                   │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ Agent: CoordinatorAgent + 多模型辩论                                    │ │
│ │ 工具: Deep Research (行业最佳实践调研)                                   │ │
│ │ 流程: 辩论(领域专家/客户倡导者/需求分析师/风险控制者) → 主持人裁决       │ │
│ │ 输出: global_objective.md, main_sop_backbone.json (5-9节点)            │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    │                                   │
                    ▼                                   ▼
┌───────────────────────────────┐   ┌───────────────────────────────┐
│ Step3: 全局规则与术语         │   │ Step4: 用户画像               │
│ ┌───────────────────────────┐ │   │ ┌───────────────────────────┐ │
│ │ Agent: GlobalRulesAgent   │ │   │ │ Agent: UserProfileAgent   │ │
│ │        GlossaryAgent      │ │   │ │ 工具: Deep Research       │ │
│ │ 工具: Deep Research       │ │   │ │ 输出: agent_user_profiles │ │
│ │ 输出: agent_guidelines    │ │   │ │       (用户分群+persona)  │ │
│ │       step3_glossary      │ │   │ └───────────────────────────┘ │
│ │       agent_observations  │ │   └───────────────┬───────────────┘
│ └───────────────────────────┘ │                   │
└───────────────┬───────────────┘                   │
                │                                   │
                └─────────────────┬─────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step5: 分支SOP并发挖掘                                                       │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 输入: main_sop_backbone.json 的每个节点                                 │ │
│ │ 并发: max_parallel_step5_nodes 控制并发数                               │ │
│ │ 每个节点生成:                                                            │ │
│ │   - step5_journeys_{node_id}.json (二级Journey, 5-10节点)              │ │
│ │   - step5_guidelines_{node_id}.json (局部Guideline, 去重)              │ │
│ │   - step5_glossary_{node_id}.json                                       │ │
│ │   - step5_tools_{node_id}.json                                          │ │
│ │   - step5_summary_{node_id}.md                                          │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step6: 边缘场景挖掘                                                          │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 输入: Step5各节点的summary描述                                          │ │
│ │ 并发: max_parallel_edge_cases 控制并发数                                │ │
│ │ 输出: 边缘场景单节点Journey → 注入对应Step5的guidelines                 │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step7: 配置组装                                                              │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 按Parlant目录结构整合文件:                                               │ │
│ │   00_agent_base/  ←  metadata, user_profile, glossary                  │ │
│ │   01_agent_rules/ ←  agent_guidelines, observations, canned_responses  │ │
│ │   02_journeys/    ←  main_sop, branch_sop, edge_sop                    │ │
│ │   03_tools/       ←  tool_meta                                          │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step8: 最终校验                                                              │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 校验项:                                                                  │ │
│ │   - JSON格式校验 (json_repair自动修复)                                  │ │
│ │   - Parlant Schema校验                                                  │ │
│ │   - Journey状态机检查 (起始/终止节点、边连通性)                         │ │
│ │   - 跨文件一致性检查                                                    │ │
│ │   - 合规校验 (ComplianceCheckAgent)                                     │ │
│ │ 输出: final_parlant_config/ (校验后的最终版本)                          │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          最终输出: Parlant Agent 配置包                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

**图解要点**：
- Step1生成澄清问题，人工确认后可进入Step2，跳过则使用默认假设
- Step2通过多模型辩论达成共识，主持人进行终局裁决
- Step3和Step4可并行执行，通过`enable_step3_step4_parallel`配置
- Step5按主SOP节点并行执行，每个节点生成独立的分支SOP
- Step6基于Step5的summary描述挖掘边缘场景
- Step7将所有步骤的产出按Parlant目录结构组装
- Step8进行JSON校验、Schema校验、状态机检查和合规校验

### Agent ReAct 流程图

每个业务Agent采用**ReAct（Reasoning + Acting）模式**执行任务，通过"思考-行动"循环完成复杂任务。核心特点是先调用Deep Research获取互联网知识，再基于调研结果生成Parlant配置。

**ReAct执行机制**：
1. **任务接收**：Agent接收任务描述、业务描述和上下文信息
2. **查询生成**：使用`deep_research_brief_template`生成完整调研任务（非简单关键词）
3. **Deep Research执行**：调用Tavily搜索引擎，迭代搜索生成Markdown报告
4. **配置生成**：基于调研报告，按Parlant格式要求生成JSON配置
5. **JSON解析**：使用`json_repair`解析，失败时LLM修复1次，仍失败则Fallback

**关键设计**：
- Deep Research返回的是**Markdown报告**，不是JSON
- JSON解析在Agent生成内容后进行，不是在Deep Research返回后
- Fallback模式只固化结构，关键字段由模型生成，避免与业务无关

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ReAct Agent 执行流程                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. 接收任务                                                                  │
│    输入: task_description, business_desc, context                           │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. 生成Deep Research查询                                                     │
│    使用 deep_research_brief_template 生成完整调研任务                        │
│    示例: "请研究保险行业外呼营销场景的合规要求..."                           │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 3. Deep Research执行                                                         │
│    ┌─────────────────────────────────────────────────────────────────────┐  │
│    │ DeepResearchAgent                                                    │  │
│    │   ├─ 调用Tavily搜索 (关键词由Agent生成)                              │  │
│    │   ├─ 迭代搜索 (max_depth, max_iters控制)                            │  │
│    │   └─ 生成Markdown报告                                                │  │
│    └─────────────────────────────────────────────────────────────────────┘  │
│    输出: Markdown格式的调研报告                                              │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 4. 基于报告生成Parlant配置                                                   │
│    Agent根据调研报告，按任务要求生成Parlant格式JSON                          │
│    输出: {"agent_guidelines": [...], "agent_observations": [...]}           │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    │                                   │
                    ▼                                   ▼
┌───────────────────────────────┐   ┌───────────────────────────────┐
│ 5a. JSON解析成功              │   │ 5b. JSON解析失败              │
│ ┌───────────────────────────┐ │   │ ┌───────────────────────────┐ │
│ │ json_repair解析           │ │   │ │ json_repair解析失败       │ │
│ │ Schema校验                │ │   │ │ LLM修复(最多1次)          │ │
│ │ 质量检查                  │ │   │ │ 仍失败 → Fallback模式     │ │
│ │ 文件写入                  │ │   │ │ (模板填充，模型生成字段)  │ │
│ └───────────────────────────┘ │   │ └───────────────────────────┘ │
└───────────────────────────────┘   └───────────────────────────────┘
```

**图解要点**：
- 步骤1-4是顺序执行，不可跳过
- 步骤5a和5b是分支处理：JSON解析成功走5a流程，失败走5b流程
- Deep Research返回Markdown报告，Agent需要基于报告生成JSON
- `json_repair`是第一道防线，LLM修复是第二道防线，Fallback是最后兜底
- Fallback模式下模板只提供结构，内容字段由模型根据业务描述生成

### 3 层 SOP 架构图

系统采用**三层SOP（Standard Operating Procedure）架构**，从主干到分支再到边缘场景，逐层细化，形成完整的业务流程覆盖。

**层级说明**：

| 层级 | 名称 | 生成步骤 | 节点数量 | 特点 |
|------|------|----------|----------|------|
| **一级** | 主SOP（主干层） | Step2 | 5-9个 | 无分支，冻结后禁止修改，是单一权威主干 |
| **二级** | 分支SOP（适配层） | Step5 | 每分支5-10个 | 依附于主SOP节点，单节点≤5分支，支持业务场景分化 |
| **三级** | 子弹SOP（补全层） | Step6 | 单节点 | 边缘异常场景原子化，作为Guideline注入 |

**设计约束**：
- **主干唯一不可逆**：主SOP一旦确定，后续步骤只能扩展分支，不能修改主干
- **分支数量限制**：每个主SOP节点最多5个分支，避免流程爆炸
- **Guideline去重**：二级SOP的局部Guideline需与全局Guideline去重
- **边缘场景原子化**：每个边缘场景只生成单节点SOP，简化管理

**示例说明**：
- 一级主SOP：初始 → 需求 → 方案 → 成交 → 结束（5个节点）
- 二级分支SOP：在"需求"节点下扩展"新客分支"、"老客分支"、"拒绝分支"等
- 三级子弹SOP：在"拒绝分支"下补充"超时场景"、"投诉场景"等边缘情况

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          一级主SOP（主干层）                                  │
│                                                                              │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐ │
│   │ 节点1   │───▶│ 节点2   │───▶│ 节点3   │───▶│ 节点4   │───▶│ 节点5   │ │
│   │ 初始    │    │ 需求    │    │ 方案    │    │ 成交    │    │ 结束    │ │
│   └────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘ │
│        │              │              │              │              │       │
└────────┼──────────────┼──────────────┼──────────────┼──────────────┼───────┘
         │              │              │              │              │
         ▼              ▼              ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          二级分支SOP（适配层）                                │
│                                                                              │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│   │ 分支1: 新客 │  │ 分支2: 老客 │  │ 分支3: 拒绝 │  │ 分支4: 疑问 │       │
│   │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │       │
│   │ │子节点1  │ │  │ │子节点1  │ │  │ │挽留节点 │ │  │ │解答节点 │ │       │
│   │ │子节点2  │ │  │ │子节点2  │ │  │ │转化节点 │ │  │ │确认节点 │ │       │
│   │ │...      │ │  │ │...      │ │  │ │...      │ │  │ │...      │ │       │
│   │ └─────────┘ │  │ └─────────┘ │  │ └─────────┘ │  │ └─────────┘ │       │
│   └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │
│                                                                              │
│   约束: 单节点≤5个分支，每个分支5-10个节点                                   │
└─────────────────────────────────────────────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          三级子弹SOP（补全层）                                │
│                                                                              │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│   │ 边缘场景: 超时  │  │ 边缘场景: 投诉  │  │ 边缘场景: 转人工│             │
│   │ ┌─────────────┐ │  │ ┌─────────────┐ │  │ ┌─────────────┐ │             │
│   │ │ 单节点SOP   │ │  │ │ 单节点SOP   │ │  │ │ 单节点SOP   │ │             │
│   │ │ + Guideline │ │  │ │ + Guideline │ │  │ │ + Guideline │ │             │
│   │ └─────────────┘ │  │ └─────────────┘ │  │ └─────────────┘ │             │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                                                              │
│   特点: 1场景1SOP，作为Guideline注入对应分支SOP                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**图解要点**：
- 一级主SOP是线性流程，节点间用箭头连接，表示执行顺序
- 每个主SOP节点可以向下扩展多个二级分支SOP，用垂直箭头表示
- 二级分支SOP内部也是线性流程，但依附于主SOP节点
- 三级子弹SOP是单节点，不形成流程，而是作为Guideline规则注入
- 纵向箭头表示"扩展/细化"关系，横向箭头表示"执行顺序"关系
- 边缘场景（如超时、投诉、转人工）通过三级子弹SOP补全，不破坏主流程结构

### 核心设计原则

1. **主干唯一不可逆**：主SOP是单一权威主干
2. **合规全链路前置**：合规规则在Step3统一定义
3. **目标对齐防偏离**：Step2写入global_objective.md防止后续偏离
4. **并发安全隔离**：Step5每个节点独立工作目录

---

## 使用

### 环境准备

1. **Python 环境**：使用 conda 的 python3.11 环境
   ```bash
   conda activate python3.11
   ```

2. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```

3. **配置 API Key**：在 `.env` 文件中配置（默认路径：`E:\cursorworkspace\c002_parlant_config_manager1\.env`，亦可将 `.env` 放在项目根目录并通过 `--env-file` 指定）
   ```env
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_BASE_URL=https://api-inference.modelscope.cn/v1/  # 可选
   TAVILY_API_KEY=your_tavily_api_key
   ```

### CLI 命令行参数详解

#### 基本启动命令

```bash
python egs/v0.1.0_minging_agents/main.py [参数]
```

#### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--mode` | str | `real` | 运行模式：`real`(真实调用LLM) / `mock`(测试模式，不调用真实LLM) |
| `--max-parallel` | int | `1` | 全局最大并发Agent数（免费版Tavily建议设为1） |
| `--start-step` | int | `1` | 起始步骤（1-8） |
| `--end-step` | int | `8` | 结束步骤（1-8） |
| `--business-desc` | str | 必填 | 业务描述文本 |
| `--skip-clarification` | flag | False | 跳过澄清环节（仍生成问题，但不等待人工确认） |
| `--force-rerun` | flag | False | 强制重跑，删除指定步骤的输出目录 |
| `--debug` | bool | False | 调试模式，Step5只扩展2个节点 |
| `--env-file` | str | `E:\cursorworkspace\c002_parlant_config_manager1\.env` | 环境变量文件路径 |

#### 常用命令示例

```bash
# 完整运行（8步）
python egs/v0.1.0_minging_agents/main.py --mode real --business-desc "您的业务描述"

# 跳过澄清环节
python egs/v0.1.0_minging_agents/main.py --mode real --skip-clarification --business-desc "..."

# 断点续跑（从第3步开始）
python egs/v0.1.0_minging_agents/main.py --mode real --start-step 3 --end-step 8 --business-desc "..."

# 强制重跑指定步骤
python egs/v0.1.0_minging_agents/main.py --mode real --force-rerun --start-step 3 --end-step 8 --business-desc "..."

# 调试模式（二级SOP只扩展2个节点）
python egs/v0.1.0_minging_agents/main.py --mode real --debug True --business-desc "..."

# Mock模式（链路测试，不调用真实LLM）
python egs/v0.1.0_minging_agents/main.py --mode mock --business-desc "..."

# 指定环境变量文件
python egs/v0.1.0_minging_agents/main.py --mode real --env-file "E:\cursorworkspace\c002_parlant_config_manager1\.env" --business-desc "..."
```

### UI 模式

#### 启动方式

```bash
# 正常模式
python egs/v0.1.0_minging_agents/run_ui.py

# Mock模式（不调用真实LLM，用于UI测试）
python egs/v0.1.0_minging_agents/run_ui.py --mock
```

#### UI 页面功能

| 页面 | 功能说明 |
|------|----------|
| **首页（需求输入）** | 输入业务描述、上传JSON文件（可选）、选择分类标签、点击示例快速填充 |
| **等待页（Step1处理）** | 实时显示处理进度、子任务状态、预计剩余时间 |
| **澄清页** | 显示系统生成的澄清问题、用户可回答或跳过、支持新增自定义问题 |
| **等待页（Step3-8处理）** | 显示各步骤进度、子任务执行状态 |
| **结果页** | 展示生成的配置包，支持导出ZIP、查看校验报告 |

#### 结果页选项卡

- **流程视图**：流程图展示、节点关联资源、父子流程链接
- **规则视图**：按作用域筛选、显示触发条件/执行动作/优先级/排除关系
- **术语视图**：术语定义、使用场景、同义词
- **工具视图**：工具描述、输入输出参数、使用位置
- **固定话术视图**：话术内容、变量占位符、关联规则

### 输出产物

```
output/
├── step1_requirement_clarification/    # Step1 输出
│   ├── step1_clarification_questions.md
│   ├── step1_structured_requirements.md
│   └── step1_research_reports/
├── step2_objective_alignment_main_sop/ # Step2 输出
│   ├── global_objective.md
│   ├── main_sop_backbone.json
│   ├── business_objectives.md
│   └── step2_research_reports/
├── step3_global_rules_and_glossary/    # Step3 输出
│   ├── agent_guidelines.json
│   └── step3_glossary_master.json
├── step4_user_profile/                 # Step4 输出
│   └── agent_user_profiles.json
├── step5_branch_sop_parallel/          # Step5 输出
│   ├── step5_journeys_{node_id}.json
│   ├── step5_guidelines_{node_id}.json
│   └── step5_summary_{node_id}.md
├── step6_edge_cases/                   # Step6 输出
├── step7_config_assembly/              # Step7 输出
├── step8_validation/                   # Step8 输出
├── parlant_agent_config/               # Step7 组装结果
├── final_parlant_config/               # Step8 校验后的最终版本
├── performance_report.json             # 性能统计报告
└── run_config_snapshot/                # 本次运行的YAML配置快照
```

### 可修改配置文件

主要配置文件位于 `egs/v0.1.0_minging_agents/config/`：

| 文件 | 用途 |
|------|------|
| `system_config.yaml` | 系统级配置（并发、超时、模型等） |
| `agents/coordinator_agent.yaml` | 协调Agent提示词 |
| `agents/global_rules_agent.yaml` | 全局规则Agent提示词 |
| `agents/glossary_agent.yaml` | 术语Agent提示词 |
| `agents/user_profile_agent.yaml` | 用户画像Agent提示词 |
| `agents/requirement_analyst_agent.yaml` | 需求分析Agent提示词 |
| `agents/compliance_check_agent.yaml` | 合规校验Agent提示词 |
| `agents/config_assembler_agent.yaml` | 配置组装Agent提示词 |
| `agents/debate_prompts.yaml` | 多模型辩论提示词 |
| `mock/ui_examples.yaml` | UI首页示例选项 |

---

## 调试

### YAML 关键配置参数（system_config.yaml）

#### 并发控制

```yaml
max_parallel_agents: 1           # 全局最大并发Agent数
max_parallel_step5_nodes: 1      # Step5节点并发数
max_parallel_edge_cases: 1       # Step6边缘场景并发数

concurrency:
  enable_step3_step4_parallel: false  # Step3/Step4并行开关
  enable_step3_globalrules_glossary_parallel: false  # Step3内部并行
```

**调优建议**：
- 免费版Tavily：所有并发参数设为1，避免RPM限制
- 付费版Tavily：可适当提高并发数（如3-5）

#### Deep Research 配置

```yaml
deep_research:
  max_depth: 1                   # 搜索深度（调试用1，生产用3）
  max_iters: 1                   # 迭代次数
  timeout_sec: 120               # 超时时间
  client_timeout_sec: 120        # LLM客户端超时
  timeout_retry_count: 2         # 超时重试次数
  max_failures_before_fallback: 3 # 失败阈值，超过后降级到模型知识
  allow_fallback_on_failure: true # 允许降级
  step1_query_count: 1           # Step1查询条数
  step1_max_parallel_queries: 1  # Step1并发查询数
  step2_max_parallel_queries: 1  # Step2并发查询数
```

**调优建议**：
- 调试阶段：`max_depth=1, max_iters=1` 提速
- 生产环境：`max_depth=3, max_iters=2` 提升质量

#### Tavily RPM 限制对策

```yaml
deep_research:
  tavily_retry_on_rate_limit: true   # 检测限流时自动重试
  tavily_retry_delay_sec: 30         # 重试前等待秒数
  tavily_max_retries: 3              # 最大重试次数
  tavily_retry_backoff_multiplier: 2.0  # 等待时间倍增系数
```

**调优建议**：
- 免费版Tavily（RPM=100）：`tavily_retry_delay_sec: 30`，所有并发设为1
- 付费版Tavily：可降低等待时间，提高并发

#### 模型配置

```yaml
openai:
  model_name: "Qwen/Qwen3.5-27B"
  request_timeout_sec: 180       # 请求超时
  enable_thinking: false         # 关闭思考模式

deep_research:
  model_name: "Qwen/Qwen3.5-27B"
  temperature: 0.7
```

#### ReAct Agent 配置（各agent yaml文件）

```yaml
model:
  type: OpenAIChatModel
  react_max_rounds: 3            # ReAct最大轮数
  use_react: true                # 是否启用ReAct模式
  config:
    temperature: 0.7
  enable_thinking: false
```

**调优建议**：
- 简单任务：`react_max_rounds: 2`
- 复杂任务：`react_max_rounds: 5-8`

#### 日志配置

```yaml
logging:
  level: INFO
  llm_message_preview_chars: 1200    # LLM交互日志预览长度
  react_print_hint_msg: true         # 打印ReAct过程
  react_progress_log_interval_sec: 10  # ReAct进度日志间隔
```

#### 质量门控

```yaml
quality_gate:
  rework_trigger_threshold: 0    # 调试时关闭自动返工
  severe_diff_threshold: 0
  max_rework_rounds: 2

step8_quality_gate:
  enabled: false                 # 默认关闭Step8返工
  rework_trigger_threshold: 80   # 质量分阈值
  rework_restart_step: 5         # 返工起始步骤
```

### 常见问题排查

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| Tavily返回中断消息 | 免费版RPM限制 | 增大`tavily_retry_delay_sec`，设置`max_parallel=1` |
| JSON解析失败 | 模型输出格式异常 | 检查`json_repair`日志，优化提示词，使用fallback模式 |
| ReAct中断 | 工具注册失败 | 检查`deep_research`工具是否正确注册 |
| 主题偏离 | 提示词示例误导 | 检查Agent YAML中的示例，确保与业务一致 |
| Real模式降级到Mock | Deep Research连续失败 | 检查API Key，或允许fallback使用模型知识 |
| 超时错误 | 请求时间过长 | 增大`request_timeout_sec`，降低`max_depth` |
| 编码错误 | GBK无法处理Unicode | 设置`PYTHONUTF8=1`环境变量 |

### 调试技巧

1. **单步调试**：使用 `--start-step N --end-step N` 单独运行某一步
2. **查看日志**：`output/logs/mining_agents.log` 和各步骤目录下的日志文件
3. **ReAct追踪**：各步骤目录下的 `*_react_trace.log` 记录完整ReAct过程
4. **配置快照**：`output/run_config_snapshot/` 保存本次运行的完整配置
5. **性能报告**：`output/performance_report.json` 记录各Agent执行时间

---

## Vibe Coding

基于项目开发过程中的历史任务记录（`auto_mining_refine.md`）和修改日志（`changelog.md`），总结以下常见问题和建议：

### 常见问题与解决方案

#### 1. Real模式数据造假风险

**问题表现**：Real模式下返回Mock数据或固化模板内容

**根因分析**：
- Agent执行失败时静默降级到Mock模板
- 未正确区分Real/Mock模式的降级策略

**解决方案**：
- Real模式必须严格检查，禁止返回Mock数据
- 失败时应抛出异常，而非静默降级
- 输出中明确标记数据来源（`fallback_source`字段）
- 在`StepManager`中增加硬门控，检测`fallback_source/fallback_warning/mock`痕迹

**代码示例**：
```python
if mode == "real" and result.get("fallback_source"):
    raise RuntimeError("Real mode cannot use fallback data")
```

#### 2. ReAct流程错误

**问题表现**：在Deep Research返回结果时就尝试解析JSON

**根因分析**：
- Deep Research返回的是Markdown报告，不是JSON
- JSON解析应在Agent基于报告生成内容后进行

**正确流程**：
```
1. Agent生成查询任务 → Deep Research → Markdown报告
2. Agent基于报告生成内容 → Parlant格式JSON
3. json_repair解析 → 1次LLM修复 → 质量校验 → 文件写入
```

**解决方案**：
- 使用`deep_research_brief_template`注入完整调研任务说明
- 在ReAct流程中显式要求"先deep research，再基于markdown证据产出JSON"

#### 3. 查询词偏离主题

**问题表现**：Tavily搜索返回无关结果

**根因分析**：
- 给Deep Research的是简单关键词，而非完整研究任务
- 硬编码查询词（如"日本 保险"）与实际业务不符

**解决方案**：
- Deep Research需要完整的调研任务描述，不是简单关键词
- 使用`deep_research_brief_template`模板，结合业务描述动态生成
- Tavily由Deep Research控制，只需给它完整的研究brief

**配置示例**：
```yaml
deep_research_brief_template: |
  你是全局规则研究员。请围绕当前业务场景输出调研报告，覆盖：
  1) 监管合规要求与禁止事项；
  2) 用户拒绝/异议场景下的规则设计；
  任务={task}
  业务描述={business_desc}
  行业={industry}
```

#### 4. 提示词示例误导

**问题表现**：示例中的具体行业内容被模型照抄

**根因分析**：
- 提示词示例使用具体行业（如航空、保险）
- 模型倾向于照抄示例内容

**解决方案**：
- 示例使用通用占位符（如`{业务前缀}`），不涉及具体行业
- 在提示词开头添加"业务导向原则"说明
- 强调输出必须基于用户传入的业务描述

**提示词模板**：
```
【重要提示 - 业务导向原则】
本系统的核心原则：**所有输出必须严格基于用户传入的【业务描述】**。
- 下文中的所有示例、模板、占位符仅用于展示字段结构和格式要求
- 实际内容必须根据【业务描述】中的具体业务场景自行撰写
- **禁止照抄示例中的具体业务内容**
```

#### 5. 澄清问题未回答仍被带入

**问题表现**：用户未回答的澄清问题仍出现在后续提示词中

**解决方案**：
- 检测澄清问题是否有答案
- 无答案的问题不注入后续步骤
- 使用`use_clarification`参数控制是否注入

#### 6. Fallback模板完全固化

**问题表现**：Fallback时使用完全固化的模板，与业务无关

**解决方案**：
- Fallback模板只固化结构，关键字段由模型生成
- 输出中标记`fallback_source: "template_fill_mode"`
- 让模型决策JSON块的数量和关键字段内容

#### 7. 编码问题

**问题表现**：GBK编码无法处理Unicode字符

**解决方案**：
- 统一使用UTF-8编码
- 设置`PYTHONUTF8`环境变量
- 在`DeepResearchTool`初始化时强制`stdout/stderr`使用UTF-8

#### 8. Tavily RPM限制

**问题表现**：免费版Tavily频繁返回中断消息

**解决方案**：
- 所有并发参数设为1
- 增大`tavily_retry_delay_sec`到30秒以上
- 使用指数退避策略

#### 9. 多模型辩论未达成一致

**问题表现**：辩论轮数结束后无最终结论

**解决方案**：
- 达到最大轮数时，由主持人进行"终局裁决"
- 产出最终结论并写入transcript

#### 10. 配置文件与代码不一致

**问题表现**：修改YAML配置后行为未变化

**解决方案**：
- 检查`output/run_config_snapshot/`确认实际使用的配置
- 确保代码从YAML读取参数而非硬编码

### 开发最佳实践

1. **配置与代码分离**：所有提示词和参数放在YAML配置文件中
2. **日志使用loguru**：不使用print或Python标准logging
3. **JSON解析使用json_repair**：处理大模型输出的格式问题
4. **异常处理完善**：使用traceback打印完整异常信息
5. **每次修改后回归测试**：避免引入历史已修复的问题
6. **查看changelog.md**：了解历史修改记录，避免重复错误

### Vibe Coding 协作要点

与AI Agent协作开发时，遵循以下三点原则可显著提升效率和成功率：

#### 1. 定义清楚需求，告知清楚背景

**原则**：在任务开始前，必须明确告知AI完整的需求背景和上下文。

**具体做法**：
- 描述当前遇到的问题或需要实现的功能
- 说明业务场景和约束条件
- 提供相关的代码文件路径、配置文件位置
- 指出相关的文档或参考样例
- 说明期望的输出格式和质量标准

**示例**：
```markdown
# 当前任务
背景：Step5分支SOP生成时，部分Guideline与全局Guideline重复
需求：实现Guideline去重功能
相关文件：src/mining_agents/steps/step5_branch_sop_parallel.py
约束：去重时需考虑语义相似度，而非仅字符串匹配
```

#### 2. 确认AI的计划再开始修改

**原则**：在AI开始编码前，先让其输出实施计划，人工确认后再执行。

**具体做法**：
- 要求AI先分析问题，给出解决方案思路
- 让AI列出需要修改的文件和修改点
- 评估修改的影响范围和风险
- 确认计划符合预期后，再让AI开始编码
- 对于复杂任务，可要求AI分步骤执行，每步确认后再继续

**示例**：
```markdown
请先给出实施计划，包括：
1. 需要修改哪些文件
2. 每个文件的修改内容
3. 可能的影响范围
4. 测试验证方案

确认计划后，再开始编码。
```

#### 3. 修改后进行回测，验证需求一致性

**原则**：修改完成后，必须进行完整的回归测试，验证输出产物与需求的一致性。

**具体做法**：
- **流程级测试**：按照正常业务流程运行，而非仅单元测试
- **模型比对验证**：让AI比对需求和输出产物，检查一致性
- **边界条件测试**：测试异常输入、极端场景
- **历史回归**：确保修改未破坏已有功能
- **Mock和Real双模式测试**：确保两种模式都能正常工作

**示例验证流程**：
```markdown
修改完成后，请执行以下验证：
1. 运行单元测试：pytest tests/test_xxx.py
2. 运行流程测试：python main.py --mode mock --start-step 5 --end-step 5
3. 比对验证：检查输出文件是否包含预期的去重结果
4. 回归测试：运行完整的8步流程，确保无破坏性影响
```

**自动化验证模板**：
```markdown
请比对以下需求和输出产物的一致性：

**需求**：
[原始需求描述]

**输出产物**：
[输出文件内容或路径]

**验证项**：
1. 是否满足需求中的功能要求？
2. 是否引入了新的问题？
3. 代码风格是否符合项目规范？
4. 是否有遗漏的边界情况？
```

### Vibe Coding 任务模板

当给Agent下达任务时，建议使用以下模板：

```markdown
# 当前任务

### task N

[任务描述]

**问题背景**：
[描述当前遇到的问题]

**优化内容**：
1. [具体优化点1]
2. [具体优化点2]

**修改文件**：
- [文件路径1]
- [文件路径2]

**验证方式**：
[如何验证修改是否正确]

**注意事项**：
- [注意点1]
- [注意点2]
```

---

## 不足

### 当前局限性

#### 1. 并发控制未充分测试

**问题描述**：
- Step5/Step6的并发执行仅在低并发（1-2）场景下验证
- 高并发场景（如5+节点并行）可能存在资源竞争、状态冲突等问题
- Tavily免费版RPM限制导致无法进行高并发测试

**影响范围**：
- 生产环境高并发部署可能不稳定
- 性能优化空间未充分挖掘

**建议**：
- 付费版Tavily环境下进行高并发压测
- 增加并发安全测试用例
- 完善并发锁和资源隔离机制

#### 2. Deep Research与商用存在差距

**问题描述**：
- 当前Deep Research依赖Tavily搜索引擎，功能相对简单
- 缺少多搜索引擎支持（DuckDuckGo、Google等）
- 搜索深度和迭代次数受限（调试用1，生产用3）
- 缺少知识图谱、专业数据库等高级数据源

**影响范围**：
- 调研报告质量受限
- 特定行业（如医疗、法律）的专业信息覆盖不足

**建议**：
- 集成DuckDuckGo等免费搜索引擎
- 支持自定义数据源接入
- 增加搜索结果去重和质量评估机制

#### 3. 设计细节有待调优

**问题描述**：
- 提示词工程：部分Agent提示词过长，可能影响模型理解
- 数量控制：Guideline/Journey数量控制不够精确
- 去重机制：全局与局部Guideline去重依赖启发式规则，可能遗漏
- 状态机校验：Journey状态机检查不够严格

**影响范围**：
- 输出质量波动
- 部分场景需要人工干预

**建议**：
- 持续优化提示词，精简冗余内容
- 增强Schema校验和自动修复能力
- 完善状态机校验规则

#### 4. JSON输出稳定性

**问题描述**：
- 大模型JSON输出偶尔格式异常
- json_repair修复成功率约90%，仍有10%需要LLM二次修复
- 复杂嵌套结构（如多层Journey）更容易出错

**影响范围**：
- 偶发解析失败需要重试
- Fallback模式可能影响输出质量

**建议**：
- 持续优化提示词，使用结构化输出引导
- 增加JSON Schema约束
- 探索Function Calling等原生JSON输出方式

#### 5. 边缘场景覆盖不完整

**问题描述**：
- 依赖Step5的总结描述生成，可能遗漏重要边缘场景
- 边缘场景识别缺少系统性方法论
- 部分边缘场景（如系统异常、网络故障）覆盖不足

**建议**：
- 增加边缘场景识别机制
- 支持用户自定义边缘场景
- 建立边缘场景知识库

#### 6. 质量校验自动化程度有限

**问题描述**：
- Step8校验发现问题后自动修复能力不足
- 返工机制默认关闭，需要手动开启
- 质量评分体系不够完善

**建议**：
- 增强自动修复和返工机制
- 完善质量评分体系
- 增加人工审核接口

#### 7. Observation生成不完整

**问题描述**：
- 部分场景下Observation未随全局Guideline生成
- Observation与Guideline的依赖关系不够清晰

**建议**：
- 检查Step3的GlobalRulesAgent配置
- 增加Observation生成校验

#### 8. UI测试不充分

**问题描述**：
- UI界面仅在Mock模式下进行了功能验证
- Real模式下UI与后端Agent的完整链路未充分测试
- 长时间运行、大输出场景下的UI稳定性未验证
- 多用户并发访问UI的场景未测试

**影响范围**：
- Real模式下可能出现UI与后端状态不同步
- 大输出场景下可能存在性能问题
- 生产环境部署风险

**建议**：
- 完成Real模式下UI端到端测试
- 增加大输出场景的压力测试
- 增加多用户并发测试
- 完善UI错误处理和重试机制

#### 9. 输入超长未检测和处理

**问题描述**：
- 用户输入的业务描述长度没有上限检测
- 超长输入可能导致LLM上下文溢出、响应超时或质量下降
- UI和CLI均未对输入长度进行有效校验和提示
- Deep Research的查询也可能因超长而失败

**影响范围**：
- 超长输入时系统可能静默失败或返回低质量结果
- 用户体验差，无法得知输入过长是问题根源
- 可能触发API限制或产生额外费用

**建议**：
- 在CLI和UI入口处增加输入长度校验（如限制在2000字符内）
- 超长输入时给出明确提示，建议精简或分段处理
- 对Deep Research查询进行长度截断或分段
- 增加输入预处理模块，自动提取关键信息

### 未来优化方向

#### 短期优化（1-2周）

1. **并发测试与优化**
   - 付费版Tavily环境下进行高并发压测
   - 完善并发锁和资源隔离机制
   - 增加并发安全测试用例

2. **Deep Research增强**
   - 集成DuckDuckGo搜索引擎
   - 优化搜索查询生成策略
   - 增加搜索结果质量评估

3. **提示词优化**
   - 精简冗余内容
   - 统一业务导向原则
   - 增加负例示例

#### 中期优化（1-2月）

1. **质量体系完善**
   - 增强Schema校验和自动修复
   - 完善状态机校验规则
   - 建立质量评分体系

2. **边缘场景增强**
   - 建立边缘场景知识库
   - 支持用户自定义边缘场景
   - 增加系统性识别机制

3. **工程化改进**
   - 完善单元测试和集成测试
   - 增加CI/CD流程
   - 优化错误提示和用户引导

#### 长期优化（3-6月）

1. **多搜索引擎支持**
   - 集成Google、Bing等搜索引擎
   - 支持自定义数据源接入
   - 建立搜索引擎调度策略

2. **多模态支持**
   - 支持图片、PDF等输入格式
   - 增加语音交互能力
   - 支持视频内容分析

3. **商业化准备**
   - 完善API接口
   - 增加用户管理和权限控制
   - 建立监控和告警体系

---

## 许可证

MIT License
