# Parlant Agent 工程化配置管理方案（完全隔离版·整合优化）

## 一、方案设计背景

### 1.1 Parlant 框架官方介绍

Parlant 是由 Emcie 公司开发、**专为生产级客户交互场景设计的高可控 LLM Agent 开发框架**,官方定位为「LLM agents built for control. Designed for real-world use. Deployed in minutes.」,核心理念是**「Stop Fighting Prompts, Teach Principles」**——彻底颠覆传统「写超长系统提示词碰运气」的 Agent 开发模式，通过结构化的规则定义，确保 LLM Agent 严格遵循业务要求，从根源上解决传统 Agent 框架普遍存在的「无视系统提示、关键场景幻觉、边缘场景处理不稳定、行为不可预测」四大生产级痛点。

Parlant 原生适配金融、医疗、电商、法律等**合规要求高、对 Agent 行为可控性要求极强**的客户-facing 场景，目前已被全球超 10000 名开发者、医疗机构、医疗服务商、零售企业用于生产环境。

### 1.2 业务落地痛点与方案设计初衷

Parlant 框架提供了强大的可控 Agent 构建能力，但在多业务线、多 Agent、多人协作的生产级落地过程中，普遍存在以下痛点：

1. **配置零散化**：规则、旅程、关系、工具配置散落在代码文件中，人工维护、审核、版本管理难度极大；
2. **关系错配风险**：排除关系、依赖关系硬编码在代码中，人工修改易出现错配、漏改，导致规则冲突、误触发；
3. **多 Agent 隔离性差**：不同业务线的 Agent 配置混杂，共享层配置修改易影响所有 Agent，不符合金融、医疗等行业的**严格合规隔离要求**；
4. **职责边界模糊**：流程、规则、话术、工具代码耦合，产品、运营、开发、合规人员无法分工协作；
5. **版本追溯困难**：配置与代码混存，无法精准追溯单个 Agent 的规则、流程变更历史，不符合审计要求。

基于以上痛点，本方案设计了一套**完全贴合 Parlant 原生特性、每个 Agent 完全独立隔离、面向人工维护、可版本化、可审计**的工程化配置管理体系，将每个 Agent 的所有配置（基础配置、规则、旅程、关系、工具、术语）100% 内聚到单个独立文件夹内，实现真正的「物理隔离、互不干扰」，完美满足多业务线、多 Agent 的生产级落地需求。

---

## 二、方案总览与核心设计目标

### 2.1 方案总览

本方案是面向 Parlant 框架的**多 Agent 完全隔离**工程化配置管理方案，专为人工维护、多业务线严格隔离、版本可控的生产场景设计。方案严格遵循 Parlant 原生的核心设计逻辑，将每个 Agent 的所有组成模块（观测、规则、旅程、关系、工具、术语）**100% 内聚到单个独立文件夹内**，Agent 之间无任何共享配置，完全物理隔离；同时完整实现了 Parlant 原生的排除关系与依赖关系，确保 Agent 的语境始终「狭窄且聚焦」，解决了生产落地中的配置维护、多人协作、合规审计、多 Agent 严格隔离等核心问题。

### 2.2 核心设计目标

| 目标 | 详细说明 |
|------|----------|
| **Agent 完全物理隔离** | **核心目标**：每个 Agent 一个完全独立的文件夹，包含该 Agent 的所有配置（基础配置、规则、工具、术语表），Agent 之间无任何共享配置，修改一个 Agent 的配置不会影响其他任何 Agent，完美满足金融、医疗等行业的严格合规隔离要求。 |
| 职责完全解耦 | 流程（SOP）、规则（Guideline）、观测（Observation）、工具（Tool）四大核心模块在单个 Agent 文件夹内彻底拆分，修改流程不影响规则、修改规则不影响工具、修改工具不影响业务配置，多人协作零干扰。 |
| 关系设计严格合规 | 完整实现 Parlant 原生的排除关系与依赖关系，确保语境狭窄聚焦，避免规则冲突与冗余激活，100% 贴合框架原生能力。 |
| 人工维护友好 | 单个 Agent 文件夹内结构扁平、职责清晰，关系定义直观，人工维护无需写代码，审核可按单个 Agent 拆分，责任到人。 |
| 高可扩展性 | 新增 Agent 仅需复制完整的 Agent 模板文件夹，无需修改任何其他配置；新增 SOP、规则、工具仅需在对应 Agent 文件夹内新增文件，完美适配业务快速增长。 |
| 全流程可审计 | 每个 Agent 的所有配置均为独立的结构化文件，支持 Git 版本管理，单个 Agent 的变更历史可独立追溯，符合金融、医疗等行业的审计要求。 |

---

## 三、整体架构设计（完全隔离版）

### 3.1 顶层架构

顶层仅保留两个目录：
1. `agents/`：所有独立 Agent 的存放目录，每个子文件夹对应一个完全独立的 Agent；
2. `automation/`：自动化构建脚本，支持指定单个 Agent 独立构建。

### 3.2 单个 Agent 的完整内部架构

每个 Agent 文件夹内部包含完整的子架构体系，100% 内聚该 Agent 的所有配置：

```
单个 Agent 文件夹/
├── 00_agent_base/                # 该Agent专属的基础配置
│   ├── agent_metadata.json        # 该Agent 的名称、描述、超时、端口等
│   ├── agent_observability.json   # 该Agent专属的可观测性、日志配置
│   ├── agent_user_profiles.json   # 该Agent专属的用户画像配置（新增）
│   └── glossary/                  # 该Agent专属的领域术语表
│       ├── core_terms.json
│       └── industry_terms.json
├── 01_agent_rules/                # 该Agent专属的全局规则
│   ├── agent_guidelines.json      # 该Agent 跨 SOP 生效的全局 Guideline（含关系）
│   ├── agent_observations.json    # 该Agent专属的全局 Observation
│   └── agent_canned_responses.json # 该Agent专属的全局模板话术
├── 02_journeys/                   # 该Agent 的所有业务 SOP（3层架构，平铺结构）
│   ├── schedule_appt/             # 【一级主SOP】预约挂号主流程
│   │   ├── sop.json               # SOP 流程、状态机、规则映射
│   │   ├── sop_guidelines.json    # 该 SOP 专属规则（含关系）
│   │   └── sop_observations.json  # 该 SOP 专属观测
│   ├── schedule_appt__branch_dept_select/     # 【二级分支SOP】科室选择分支
│   │   ├── sop.json               # 包含 parent_sop_id, parent_state_id
│   │   ├── sop_guidelines.json
│   │   └── sop_observations.json
│   ├── schedule_appt__branch_doctor_recommend/ # 【二级分支SOP】医生推荐分支
│   │   ├── sop.json
│   │   ├── sop_guidelines.json
│   │   └── sop_observations.json
│   ├── schedule_appt__edge_user_change_mind/  # 【三级子弹SOP】用户改变主意场景
│   │   ├── sop.json               # 包含 parent_sop_id, is_edge_case: true
│   │   ├── sop_guidelines.json
│   │   └── sop_observations.json
│   └── lab_results_query/         # 【一级主SOP】化验结果查询主流程
│       ├── sop.json
│       ├── sop_guidelines.json
│       ├── sop_observations.json
│       ├── lab_results_query__edge_report_not_found/ # 【三级子弹SOP】报告未找到
│       │   ├── sop.json
│       │   ├── sop_guidelines.json
│       │   └── sop_observations.json
└── 03_tools/                      # 该Agent专属的工具库
    ├── tool_get_upcoming_slots/   # 门诊可预约时间查询工具
    │   ├── tool_meta.json         # 工具元信息
    │   └── tool_impl.py           # 工具实现代码
    └── tool_get_lab_results/      # 化验结果查询工具
        ├── tool_meta.json
        └── tool_impl.py
```

---

## 四、完整目录结构（完全隔离版）

```
parlant_agent_config/
├── agents/                         # 【核心】所有独立 Agent 的存放目录
│   ├── medical_customer_service_agent/ # 医疗客服 Agent（完全独立）
│   │   ├── 00_agent_base/
│   │   │   ├── agent_metadata.json
│   │   │   ├── agent_observability.json
│   │   │   ├── agent_user_profiles.json    # 用户画像配置（新增）
│   │   │   └── glossary/
│   │   │       ├── core_terms.json
│   │   │       └── medical_terms.json
│   │   ├── 01_agent_rules/
│   │   │   ├── agent_guidelines.json
│   │   │   ├── agent_observations.json
│   │   │   └── agent_canned_responses.json
│   │   ├── 02_journeys/
│   │   │   ├── schedule_appt/                    # 【一级主SOP】预约挂号主流程
│   │   │   │   ├── sop.json
│   │   │   │   ├── sop_guidelines.json
│   │   │   │   └── sop_observations.json
│   │   │   ├── schedule_appt__branch_dept_select/       # 【二级分支SOP】科室选择分支
│   │   │   │   ├── sop.json                     # 包含 parent_sop_id, parent_state_id
│   │   │   │   ├── sop_guidelines.json
│   │   │   │   └── sop_observations.json
│   │   │   ├── schedule_appt__branch_doctor_recommend/  # 【二级分支SOP】医生推荐分支
│   │   │   │   ├── sop.json
│   │   │   │   ├── sop_guidelines.json
│   │   │   │   └── sop_observations.json
│   │   │   ├── schedule_appt__edge_user_change_mind/    # 【三级子弹SOP】用户改变主意
│   │   │   │   ├── sop.json                     # 包含 parent_sop_id, is_edge_case: true
│   │   │   │   ├── sop_guidelines.json
│   │   │   │   └── sop_observations.json
│   │   │   ├── lab_results_query/               # 【一级主SOP】化验结果查询
│   │   │   │   ├── sop.json
│   │   │   │   ├── sop_guidelines.json
│   │   │   │   ├── sop_observations.json
│   │   │   ├── lab_results_query__edge_report_not_found/ # 【三级子弹SOP】报告未找到
│   │   │   │   ├── sop.json
│   │   │   │   ├── sop_guidelines.json
│   │   │   │   └── sop_observations.json
│   │   │   └── cancel_appt/                     # 【一级主SOP】预约取消
│   │   │       ├── sop.json
│   │   │       ├── sop_guidelines.json
│   │   │       ├── sop_observations.json
│   │   │       ├── cancel_appt__edge_appt_not_found/ # 【三级子弹SOP】预约不存在
│   │   │       │   ├── sop.json
│   │   │       │   ├── sop_guidelines.json
│   │   │       │   └── sop_observations.json
│   │   └── 03_tools/
│   │       ├── tool_get_upcoming_slots/
│   │       │   ├── tool_meta.json
│   │       │   └── tool_impl.py
│   │       └── tool_get_lab_results/
│   │           ├── tool_meta.json
│   │           └── tool_impl.py
│   └── airline_customer_service_agent/ # 航空客服 Agent（完全独立，与医疗无任何共享）
│       ├── 00_agent_base/
│       │   ├── agent_metadata.json
│       │   ├── agent_observability.json
│       │   ├── agent_user_profiles.json    # 用户画像配置（新增）
│       │   └── glossary/
│       │       ├── core_terms.json
│       │       └── airline_terms.json
│       ├── 01_agent_rules/
│       │   ├── agent_guidelines.json
│       │   ├── agent_observations.json
│       │   └── agent_canned_responses.json
│       ├── 02_journeys/
│       │   ├── book_flight/                      # 【一级主SOP】机票预订主流程
│       │   │   ├── sop.json
│       │   │   ├── sop_guidelines.json
│       │   │   └── sop_observations.json
│       │   ├── book_flight__branch_route_select/      # 【二级分支SOP】航线选择分支
│       │   │   ├── sop.json                      # 包含 parent_sop_id, parent_state_id
│       │   │   ├── sop_guidelines.json
│       │   │   └── sop_observations.json
│       │   ├── book_flight__edge_flight_cancelled/    # 【三级子弹SOP】航班取消场景
│       │   │   ├── sop.json                      # 包含 parent_sop_id, is_edge_case: true
│       │   │   ├── sop_guidelines.json
│       │   │   └── sop_observations.json
│       │   └── change_flight/                    # 【一级主SOP】机票改签
│       │       ├── sop.json
│       │       ├── sop_guidelines.json
│       │       ├── sop_observations.json
│       │       ├── change_flight__edge_no_available_flight/ # 【三级子弹SOP】无可用航班
│       │       │   ├── sop.json
│       │       │   ├── sop_guidelines.json
│       │       │   └── sop_observations.json
│       └── 03_tools/
│           ├── tool_load_flight_deals/
│           │   ├── tool_meta.json
│           │   └── tool_impl.py
│           └── tool_book_flight/
│               ├── tool_meta.json
│               └── tool_impl.py
└── automation/                     # 自动化构建脚本
    └── build_agent.py             # 支持指定单个 Agent 独立构建
```

---

## 五、核心配置文件格式定义（完全隔离版）

### 5.1 Agent专属基础配置

**文件路径**: `agents/medical_customer_service_agent/00_agent_base/agent_metadata.json`

> 定义该Agent的专属基础属性，与其他 Agent 完全隔离。

```json
{
  "agent_id": "medical_customer_service_agent_001",
  "agent_name": "智慧医疗客服 Agent",
  "agent_description": "专业的医疗客服代理，为用户提供预约挂号、化验结果查询、预约取消、就诊咨询等全流程服务",
  "default_language": "zh-CN",
  "default_priority": 5,
  "conversation_timeout": 3600,
  "playground_port": 8801,
  "remark": "医疗业务线专属 Agent，完全独立配置，与其他 Agent 无任何共享"
}
```

#### 补充示例 1:agent_observability.json(Agent专属可观测性配置)

**文件路径**: `agents/medical_customer_service_agent/00_agent_base/agent_observability.json`

```json
{
  "agent_id": "medical_customer_service_agent_001",
  "opentelemetry_enabled": true,
  "trace_exporter": "otlp",
  "trace_endpoint": "http://localhost:4317",
  "log_level": "INFO",
  "track_config": {
    "track_guideline_matches": true,
    "track_journey_state_changes": true,
    "track_tool_calls": true,
    "track_user_intent_recognition": true
  },
  "remark": "医疗客服 Agent专属可观测性配置，独立于其他 Agent"
}
```

#### 补充示例 2:agent_user_profiles.json(Agent专属用户画像配置)（新增）

**文件路径**: `agents/medical_customer_service_agent/00_agent_base/agent_user_profiles.json`

> 定义该Agent 服务的目标用户群体画像与分群策略，支持基于 Tags 的群体细分和个性化指南激活，与其他 Agent 完全隔离。

```json
{
  "agent_id": "medical_customer_service_agent_001",
  "remark": "医疗客服 Agent专属用户画像配置，用于实现差异化、个性化医疗服务",
  "user_segments": [
    {
      "segment_id": "vip_customers",
      "segment_name": "VIP 客户",
      "description": "高价值客户，享受优先服务和专属优惠",
      "definition": {
        "tags": ["vip", "high_value"],
        "metadata_rules": {
          "total_purchase_amount": ">10000",
          "subscription_plan": "enterprise"
        }
      },
      "behavior_patterns": [
        "偏好高效、私密的服务",
        "愿意为优质服务支付溢价",
        "注重隐私和时间效率"
      ],
      "preferred_journeys": ["vip_fast_track_booking", "premium_consultation"],
      "special_guidelines": [
        {
          "guideline_id": "vip_exclusive_discount",
          "condition": "VIP 客户询问价格",
          "action": "提供 VIP 专属 9 折优惠",
          "priority": 8
        },
        {
          "guideline_id": "vip_skip_queue",
          "condition": "VIP 客户需要等待",
          "action": "提供优先安排，无需排队",
          "priority": 9
        }
      ],
      "custom_variables": {
        "response_time_preference": "fast",
        "privacy_level": "high",
        "price_sensitivity_score": 0.2
      }
    },
    {
      "segment_id": "price_sensitive_customers",
      "segment_name": "价格敏感型客户",
      "description": "对价格高度关注，倾向于选择经济实惠的方案",
      "definition": {
        "tags": ["price_sensitive", "budget_conscious"],
        "metadata_rules": {
          "coupon_usage_rate": ">0.5",
          "avg_order_value": "<500"
        }
      },
      "behavior_patterns": [
        "频繁询问价格和折扣",
        "对促销活动高度关注",
        "决策周期较长，多次比较"
      ],
      "preferred_journeys": ["discount_inquiry", "price_comparison"],
      "special_guidelines": [
        {
          "guideline_id": "highlight_savings",
          "condition": "价格敏感客户询问方案",
          "action": "优先推荐性价比高的方案，强调节省金额",
          "priority": 7
        },
        {
          "guideline_id": "offer_coupons",
          "condition": "价格敏感客户犹豫不决",
          "action": "主动提供优惠券或折扣信息",
          "priority": 6
        }
      ],
      "custom_variables": {
        "price_sensitivity_score": 0.8,
        "coupon_usage_rate": 0.65,
        "promotion_response_rate": 0.75
      }
    },
    {
      "segment_id": "elderly_customers",
      "segment_name": "银发族客户",
      "description": "60 岁以上老年客户，需要更多耐心和简化流程",
      "definition": {
        "tags": ["elderly", "senior"],
        "metadata_rules": {
          "age": ">=60"
        }
      },
      "behavior_patterns": [
        "可能需要更详细的解释",
        "偏好电话沟通而非在线操作",
        "需要更多关怀和耐心"
      ],
      "preferred_journeys": ["simplified_booking", "phone_assistance"],
      "special_guidelines": [
        {
          "guideline_id": "elderly_patient_explanation",
          "condition": "银发族客户询问医疗流程",
          "action": "使用简单易懂的语言，分步骤详细解释",
          "priority": 8
        },
        {
          "guideline_id": "elderly_phone_support",
          "condition": "银发族客户表达困惑",
          "action": "主动提供电话人工协助服务",
          "priority": 7
        }
      ],
      "custom_variables": {
        "communication_preference": "phone",
        "explanation_detail_level": "detailed",
        "patience_required": "high"
      }
    }
  ],
  "personas": [
    {
      "persona_id": "persona_vip_001",
      "persona_name": "高端商务人士张总",
      "segment_id": "vip_customers",
      "demographics": "40-50 岁，企业高管，年收入 200 万+",
      "goals": "高效、私密、定制化医疗服务",
      "pain_points": "时间宝贵，厌恶繁琐流程",
      "behavior_patterns": [
        "偏好一对一专属服务",
        "注重隐私和效率",
        "愿意为优质服务支付溢价"
      ],
      "typical_dialogues": [
        "帮我安排最快的方案，价格不是问题",
        "我需要最私密的就诊环境",
        "直接给我最好的专家号"
      ],
      "parlant_mapping": {
        "tags": ["vip", "time_sensitive", "premium_service"],
        "variables": ["response_time_preference", "privacy_level"],
        "journeys": ["vip_fast_track_booking"],
        "guidelines": ["skip_price_discussion", "offer_premium_options"]
      }
    },
    {
      "persona_id": "persona_price_001",
      "persona_name": "精明消费者小王",
      "segment_id": "price_sensitive_customers",
      "demographics": "25-35 岁，白领，月收入 1-2 万",
      "goals": "用最少的钱买到最好的医疗服务",
      "pain_points": "担心被过度收费，希望透明定价",
      "behavior_patterns": [
        "会对比多家医院价格",
        "善于使用优惠券和医保",
        "决策前会仔细研究所有选项"
      ],
      "typical_dialogues": [
        "这个检查能走医保吗？",
        "有没有更经济的方案？",
        "现在有什么优惠活动吗？"
      ],
      "parlant_mapping": {
        "tags": ["price_sensitive", "coupon_user"],
        "variables": ["price_sensitivity_score", "coupon_usage_rate"],
        "journeys": ["price_comparison", "discount_inquiry"],
        "guidelines": ["highlight_savings", "offer_coupons"]
      }
    }
  ]
}
```

**字段说明**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `agent_id` | string | ✅ | Agent 唯一标识 |
| `remark` | string | ❌ | 配置备注说明 |
| `user_segments` | array | ✅ | 用户分群列表，每个分群包含定义、行为模式、专属指南 |
| `user_segments[].segment_id` | string | ✅ | 分群唯一标识 |
| `user_segments[].segment_name` | string | ✅ | 分群名称 |
| `user_segments[].description` | string | ✅ | 分群描述 |
| `user_segments[].definition.tags` | array | ✅ | 用于识别该分群的标签列表 |
| `user_segments[].definition.metadata_rules` | object | ❌ | 基于元数据的规则，支持数值比较 |
| `user_segments[].behavior_patterns` | array | ❌ | 该分群用户的典型行为特征 |
| `user_segments[].preferred_journeys` | array | ❌ | 该分群偏好的业务旅程 |
| `user_segments[].special_guidelines` | array | ❌ | 仅对该分群激活的专属指南列表 |
| `user_segments[].custom_variables` | object | ❌ | 自定义变量，用于量化用户特征 |
| `personas` | array | ❌ | 典型用户画像列表，用于细化用户理解 |
| `personas[].persona_id` | string | ✅ | 画像唯一标识 |
| `personas[].persona_name` | string | ✅ | 画像名称（拟人化） |
| `personas[].segment_id` | string | ✅ | 所属分群 ID |
| `personas[].demographics` | string | ❌ | 人口统计学特征 |
| `personas[].goals` | string | ❌ | 用户核心目标 |
| `personas[].pain_points` | string | ❌ | 用户痛点 |
| `personas[].behavior_patterns` | array | ❌ | 典型行为模式 |
| `personas[].typical_dialogues` | array | ❌ | 典型对话示例 |
| `personas[].parlant_mapping` | object | ❌ | 与 Parlant 元素的映射关系 |

**Parlant 中的应用方式**：

1. **Tags + Variables** → 客户细分识别
2. **Observations** → 基于代码的 matcher 检查客户标签
3. **Guidelines** → 群体特定指南激活
4. **Journeys** → 个性化旅程引导
5. **Tools** → 动态计算用户变量值
6. **Canned Responses** → 预设分群专属话术

#### 补充示例 2:glossary/medical_terms.json(Agent专属领域术语表)

**文件路径**: `agents/medical_customer_service_agent/00_agent_base/glossary/medical_terms.json`

```json
{
  "agent_id": "medical_customer_service_agent_001",
  "remark": "医疗客服 Agent专属领域术语，确保 Agent 精准理解医疗相关表述",
  "terms": [
    {
      "term_id": "medical_term_001",
      "name": "专家号",
      "description": "副主任医师及以上职称的医生出诊的号源，挂号费用高于普通号，诊疗经验更丰富",
      "synonyms": ["专家门诊", "主任医师号", "副主任医师号"],
      "language": "zh-CN"
    },
    {
      "term_id": "medical_term_002",
      "name": "普通号",
      "description": "主治医师及以下职称的医生出诊的号源，挂号费用较低，适合常规就诊、复诊",
      "synonyms": ["普通门诊", "主治医师号"],
      "language": "zh-CN"
    },
    {
      "term_id": "medical_term_003",
      "name": "化验结果",
      "description": "用户在医院完成抽血、检验、影像检查后出具的检查报告，包含各项指标数据与医生诊断意见",
      "synonyms": ["检查报告", "检验结果", "化验单", "体检报告"],
      "language": "zh-CN"
    }
  ]
}
```

### 5.2 Agent专属全局观测配置

**文件路径**: `agents/medical_customer_service_agent/01_agent_rules/agent_observations.json`

> 定义该Agent专属的全局观测条件，与其他Agent 完全隔离。

```json
{
  "agent_id": "medical_customer_service_agent_001",
  "remark": "医疗客服 Agent专属的全局观测",
  "agent_observations": [
    {
      "observation_id": "medical_obs_user_angry_001",
      "condition": "用户表达不满、愤怒、抱怨，使用负面情绪词汇",
      "remark": "观测用户是否处于负面情绪状态，用于后续安抚规则的依赖"
    },
    {
      "observation_id": "medical_obs_user_requests_human_001",
      "condition": "用户要求转人工、找客服、对自动回复不满意",
      "remark": "观测用户是否有转人工需求，用于后续转人工规则的依赖"
    }
  ]
}
```

### 5.3 Agent专属全局 Canned Responses 配置

**文件路径**: `agents/medical_customer_service_agent/01_agent_rules/agent_canned_responses.json`

> 定义该Agent专属的全局模板话术，与其他Agent 完全隔离。

```json
{
  "agent_id": "medical_customer_service_agent_001",
  "remark": "医疗客服 Agent专属全局模板话术，跨所有 SOP 生效",
  "agent_canned_responses": [
    {
      "canned_response_id": "medical_cr_greet_001",
      "content": "您好～很高兴为您服务，请问您有什么医疗相关的需求呢？",
      "language": "zh-CN"
    },
    {
      "canned_response_id": "medical_cr_soothe_001",
      "content": "非常抱歉给您带来不好的就医体验，您先消消气，我会尽力帮您解决问题的。",
      "language": "zh-CN"
    },
    {
      "canned_response_id": "medical_cr_transfer_human_001",
      "content": "理解您的需求，您可以拨打我们的医疗客服热线：400-XXX-XXXX，服务时间：周一至周日 8:00-20:00。",
      "language": "zh-CN"
    },
    {
      "canned_response_id": "medical_cr_no_diagnosis_001",
      "content": "抱歉，我无法为您提供疾病诊断、处方开具、治疗方案制定等医疗服务，建议您咨询专业医生或前往正规医院就诊。",
      "language": "zh-CN"
    }
  ]
}
```

### 5.4 Agent专属全局 Guideline 配置（含排除/依赖关系）

**文件路径**: `agents/medical_customer_service_agent/01_agent_rules/agent_guidelines.json`

> 定义该Agent专属的全局规则，完整实现 Parlant 原生的排除关系与依赖关系，与其他Agent 完全隔离。

```json
{
  "agent_id": "medical_customer_service_agent_001",
  "remark": "医疗客服 Agent专属的全局 Guideline（含排除/依赖关系）",
  "agent_guidelines": [
    {
      "guideline_id": "medical_greet_001",
      "scope": "agent_global",
      "condition": "用户首次对话、向代理打招呼（如你好、哈喽、早上好）",
      "action": "用友好的语气回应用户，主动询问用户的医疗相关需求，保持简洁不超过 2 句话",
      "priority": 3,
      "composition_mode": "FLUID",
      "bind_canned_response_ids": ["medical_cr_greet_001"],
      "exclusions": [],
      "dependencies": []
    },
    {
      "guideline_id": "medical_soothe_001",
      "scope": "agent_global",
      "condition": "用户处于负面情绪状态",
      "action": "先使用医疗专属安抚模板话术安抚用户情绪，再询问用户的具体问题",
      "priority": 8,
      "composition_mode": "FLUID",
      "bind_canned_response_ids": ["medical_cr_soothe_001"],
      "exclusions": ["medical_greet_001"],
      "dependencies": ["medical_obs_user_angry_001"]
    },
    {
      "guideline_id": "medical_no_diagnosis_001",
      "scope": "agent_global",
      "condition": "用户要求诊断疾病、开具处方、提供治疗方案、推荐药品",
      "action": "礼貌拒绝用户的请求，使用医疗合规模板话术告知用户无法提供相关服务，引导用户咨询专业医生",
      "priority": 12,
      "composition_mode": "STRICT",
      "bind_canned_response_ids": ["medical_cr_no_diagnosis_001"],
      "exclusions": ["medical_greet_001", "medical_soothe_001"],
      "dependencies": []
    },
    {
      "guideline_id": "medical_transfer_human_001",
      "scope": "agent_global",
      "condition": "用户有转人工需求",
      "action": "使用医疗专属转人工模板话术告知用户人工客服的联系方式",
      "priority": 10,
      "composition_mode": "STRICT",
      "bind_canned_response_ids": ["medical_cr_transfer_human_001"],
      "exclusions": ["medical_greet_001", "medical_soothe_001"],
      "dependencies": ["medical_obs_user_requests_human_001"]
    }
  ]
}
```

### 5.5 Agent专属工具配置

#### （1）工具元信息配置

**文件路径**: `agents/medical_customer_service_agent/03_tools/tool_get_upcoming_slots/tool_meta.json`

> 定义该Agent专属工具的元信息，与其他Agent 完全隔离。

```json
{
  "tool_id": "medical_tool_get_upcoming_slots",
  "tool_name": "get_upcoming_slots",
  "tool_description": "查询指定科室未来 7 天可预约的医生、职称、可预约时段，支持按科室、医生姓名筛选",
  "timeout": 3,
  "implementation_file": "./tool_impl.py",
  "use_scenarios": [
    "用户进入预约挂号SOP，选择科室后",
    "用户询问某科室的可预约医生",
    "用户询问某医生的可预约时段"
  ],
  "input_params": [
    {
      "param_name": "department",
      "param_type": "string",
      "required": true,
      "default": "",
      "description": "科室名称，如“内科”“外科”"
    },
    {
      "param_name": "doctor_name",
      "param_type": "string",
      "required": false,
      "default": "",
      "description": "医生姓名，用于精准筛选指定医生的可预约时段"
    }
  ],
  "output_params": [
    {
      "field_name": "doctors",
      "field_type": "array",
      "description": "可预约医生数组"
    },
    {
      "field_name": "doctors[].name",
      "field_type": "string",
      "description": "医生姓名"
    },
    {
      "field_name": "doctors[].title",
      "field_type": "string",
      "description": "医生职称"
    },
    {
      "field_name": "doctors[].available_slots",
      "field_type": "array",
      "description": "该医生的可预约时段数组"
    }
  ]
}
```

#### （2）工具实现代码

**文件路径**: `agents/medical_customer_service_agent/03_tools/tool_get_upcoming_slots/tool_impl.py`

> 该Agent专属工具的实现代码，与其他Agent 完全隔离。

```python
import asyncio
from parlant.sdk import ToolContext, ToolResult

@p.tool
async def get_upcoming_slots(
    context: ToolContext, 
    department: str, 
    doctor_name: str = ""
) -> ToolResult:
    """
    医疗客服 Agent专属：门诊可预约时间查询工具
    对应元信息 ID：medical_tool_get_upcoming_slots
    """
    # 模拟调用医院 HIS 系统接口
    await asyncio.sleep(0.2)
    
    # 模拟返回可预约数据
    doctors = [
        {
            "name": "张建国",
            "title": "主任医师",
            "available_slots": [
                {"date": "2026-03-10", "time": "09:00"},
                {"date": "2026-03-10", "time": "10:30"},
                {"date": "2026-03-11", "time": "14:00"}
            ]
        },
        {
            "name": "李梅",
            "title": "副主任医师",
            "available_slots": [
                {"date": "2026-03-10", "time": "11:00"},
                {"date": "2026-03-12", "time": "09:30"}
            ]
        }
    ]
    
    # 按医生姓名过滤数据
    if doctor_name:
        doctors = [d for d in doctors if doctor_name in d["name"]]
    
    return ToolResult(
        data=doctors,
        guidelines=[
            {"action": "优先展示职称更高、可预约时段更多的医生", "priority": 4}
        ]
    )
```

---

### 5.5 Journeys 核心 SOP 流程配置（重点补全）

该文件夹存放单个 Agent 的所有业务 SOP，**每个 SOP 一个独立子文件夹**,包含 3 个核心文件:`sop_observations.json`(SOP 专属观测)、`sop_guidelines.json`(SOP 专属规则)、`sop.json`(SOP 流程核心文件)。

以**预约挂号SOP**为例，给出 3 个文件的完整示例:

#### 示例 1:sop_observations.json(SOP 专属观测)

**文件路径**: `agents/medical_customer_service_agent/02_journeys/schedule_appt/sop_observations.json`

```json
{
  "sop_id": "schedule_appt_001",
  "sop_title": "预约挂号全流程 SOP",
  "remark": "仅预约挂号SOP 生效的专属观测，作为 SOP 内规则的依赖前置条件",
  "sop_observations": [
    {
      "observation_id": "schedule_appt_obs_user_has_dept_001",
      "condition": "用户已明确选择具体就诊科室，科室名称在医院开放预约的科室列表内",
      "remark": "观测用户是否已选定科室，用于后续医生推荐规则的依赖"
    },
    {
      "observation_id": "schedule_appt_obs_user_has_doctor_001",
      "condition": "用户已明确选择具体就诊医生，医生在对应科室的出诊列表内",
      "remark": "观测用户是否已选定医生，用于后续时段选择规则的依赖"
    },
    {
      "observation_id": "schedule_appt_obs_time_unavailable_001",
      "condition": "用户选择的预约时段已约满、不在出诊时间内、医院停诊",
      "remark": "观测用户选择的时段是否不可用，用于后续时段校验规则的依赖"
    }
  ]
}
```

#### 示例 2:sop_guidelines.json(SOP 专属规则，含排除/依赖关系)

**文件路径**: `agents/medical_customer_service_agent/02_journeys/schedule_appt/sop_guidelines.json`

```json
{
  "sop_id": "schedule_appt_001",
  "sop_title": "预约挂号全流程 SOP",
  "remark": "仅预约挂号SOP 生效的专属规则，完整实现 Parlant 原生排除/依赖关系",
  "sop_canned_responses": [
    {
      "canned_response_id": "schedule_appt_cr_dept_list_001",
      "content": "我们医院目前开放预约的科室有：内科、外科、儿科、妇科、眼科、口腔科、皮肤科、耳鼻喉科，请问您想要预约哪个科室的号呢？",
      "language": "zh-CN"
    },
    {
      "canned_response_id": "schedule_appt_cr_doctor_recommend_001",
      "content": "为您推荐{dept}科室的以下可预约医生:\n{doctor_list}\n请问您想要预约哪位医生的号呢？",
      "language": "zh-CN"
    },
    {
      "canned_response_id": "schedule_appt_cr_time_unavailable_001",
      "content": "非常抱歉，您选择的{time}时段已约满/不可预约，为您推荐以下相近的可预约时段:\n{available_slots}\n请问您是否需要调整预约时间？",
      "language": "zh-CN"
    },
    {
      "canned_response_id": "schedule_appt_cr_success_001",
      "content": "🎉 您的预约已成功！\n预约号：{appt_id}\n就诊科室：{dept}\n就诊医生：{doctor_name}\n就诊时间：{appt_time}\n请您在就诊当天携带有效身份证件，提前 30 分钟到医院门诊大厅取号，祝您就诊顺利！",
      "language": "zh-CN"
    }
  ],
  "sop_scoped_guidelines": [
    {
      "guideline_id": "schedule_appt_dept_guide_001",
      "scope": "sop_only",
      "condition": "用户进入本 SOP 后，未明确选择科室、选择的科室不存在、科室名称表述模糊",
      "action": "使用科室列表模板话术引导用户选择，若科室不存在，建议用户选择相近科室或拨打人工客服咨询",
      "priority": 4,
      "composition_mode": "FLUID",
      "bind_canned_response_ids": ["schedule_appt_cr_dept_list_001"],
      "exclusions": [],
      "dependencies": []
    },
    {
      "guideline_id": "schedule_appt_doctor_recommend_001",
      "scope": "sop_only",
      "condition": "用户已选择科室，需要推荐可预约的医生",
      "action": "使用医生推荐模板话术，优先推荐职称高、可预约时段多的医生",
      "priority": 5,
      "composition_mode": "FLUID",
      "bind_canned_response_ids": ["schedule_appt_cr_doctor_recommend_001"],
      "exclusions": ["schedule_appt_dept_guide_001"],
      "dependencies": ["schedule_appt_obs_user_has_dept_001"]
    },
    {
      "guideline_id": "schedule_appt_time_verify_001",
      "scope": "sop_only",
      "condition": "用户选择的预约时段不可用",
      "action": "友好告知用户该时段无法预约，使用时段不可用模板话术推荐其他可预约时段",
      "priority": 6,
      "composition_mode": "FLUID",
      "bind_canned_response_ids": ["schedule_appt_cr_time_unavailable_001"],
      "exclusions": ["schedule_appt_doctor_recommend_001"],
      "dependencies": ["schedule_appt_obs_time_unavailable_001", "schedule_appt_obs_user_has_doctor_001"]
    }
  ]
}
```

#### 示例 3:sop.json(SOP 流程核心文件，状态机定义)

**文件路径**: `agents/medical_customer_service_agent/02_journeys/schedule_appt/sop.json`

```json
{
  "sop_id": "schedule_appt_001",
  "sop_title": "预约挂号全流程 SOP",
  "sop_description": "引导用户完成科室选择、医生选择、时段选择、信息确认、预约提交的全流程，严格遵循医院预约挂号业务规范",
  "trigger_conditions": [
    "用户想要预约挂号",
    "用户询问门诊可预约时间",
    "用户想要找医生就诊",
    "用户需要挂某个科室的号"
  ],
  "timeout": 1800,
  "sop_guideline_mapping": {
    "sop_guideline_file": "./sop_guidelines.json",
    "sop_global_bind_guideline_ids": [
      "schedule_appt_dept_guide_001",
      "schedule_appt_doctor_recommend_001",
      "schedule_appt_time_verify_001"
    ]
  },
  "sop_states": [
    {
      "state_id": "state_000",
      "state_name": "初始 - 科室选择",
      "state_type": "chat",
      "instruction": "友好问候用户，询问用户想要预约哪个科室的号",
      "bind_guideline_ids": ["schedule_appt_dept_guide_001"],
      "transitions": [
        {
          "target_state_id": "state_001",
          "condition": "用户已明确选择具体科室，科室在医院开放列表内"
        }
      ]
    },
    {
      "state_id": "state_001",
      "state_name": "加载可预约医生",
      "state_type": "tool",
      "bind_tool_id": "medical_tool_get_upcoming_slots",
      "instruction": "调用门诊可预约时间查询工具，获取用户选定科室未来 7 天可预约的医生、职称、可预约时段",
      "transitions": [
        {
          "target_state_id": "state_002",
          "condition": "工具返回可预约医生与时段信息后"
        }
      ]
    },
    {
      "state_id": "state_002",
      "state_name": "医生与时段选择",
      "state_type": "chat",
      "instruction": "清晰列出该科室可预约的 3-5 个医生选项，包含医生姓名、职称、可预约日期与时段",
      "bind_guideline_ids": ["schedule_appt_doctor_recommend_001", "schedule_appt_time_verify_001"],
      "transitions": [
        {
          "target_state_id": "state_003",
          "condition": "用户已明确选择具体医生和预约时段"
        }
      ]
    },
    {
      "state_id": "state_003",
      "state_name": "预约信息确认",
      "state_type": "chat",
      "instruction": "与用户二次确认就诊科室、医生姓名、预约时段、就诊人姓名、就诊人身份证号信息",
      "transitions": [
        {
          "target_state_id": "state_004",
          "condition": "用户确认所有预约信息无误",
          "bind_tool_id": "medical_tool_schedule_appt"
        },
        {
          "target_state_id": "state_002",
          "condition": "用户需要修改预约信息、更换医生或时段"
        }
      ]
    },
    {
      "state_id": "state_004",
      "state_name": "提交预约",
      "state_type": "tool",
      "bind_tool_id": "medical_tool_schedule_appt",
      "instruction": "调用预约挂号提交工具，传入用户确认的预约信息，完成挂号",
      "transitions": [
        {
          "target_state_id": "state_005",
          "condition": "工具返回预约成功结果后"
        }
      ]
    },
    {
      "state_id": "state_005",
      "state_name": "预约完成",
      "state_type": "chat",
      "instruction": "告知用户预约结果，发送预约号、就诊信息，提醒就诊注意事项与取号流程",
      "bind_canned_response_ids": ["schedule_appt_cr_success_001"],
      "is_end_state": true
    }
  ]
}
```

---

### 5.6 3层SOP架构设计（子Journey机制）

本方案完整支持**3层SOP架构**，通过子Journey机制实现业务流程的层次化组织，确保主流程清晰、分支流程灵活、边缘场景独立处理。

#### 5.6.1 架构概述

```
第一层：一级主SOP（主干层）
├─ 5-9 个节点，无分支
├─ 仅使用「核心主意图 + 业务流程节点」2 个维度
├─ 冻结后禁止修改
└─ 定义业务的核心流程骨架

第二层：二级分支SOP（适配层）
├─ 依附于主SOP节点，命名格式：{main_journey}__branch_{branch_name}
├─ 遵守 1+2 铁律（1 个核心区分维度 + 最多 2 个补充适配维度）
├─ 单节点≤5 个分支
└─ 处理主流程中的业务分支场景

第三层：三级子弹SOP（补全层）
├─ 边缘异常场景原子化补全，命名格式：{main_journey}__edge_{edge_name}
├─ 1 场景 1SOP，插件式设计
├─ 可独立插拔，不影响主流程复杂度
└─ 处理异常、边缘、降级等场景
```

#### 5.6.2 目录结构规范

所有Journey平铺存放在 `02_journeys/` 目录下，通过命名规范和字段关联建立父子关系：

```
02_journeys/
├── {main_journey_name}/                         # 【一级主SOP】
│   ├── sop.json                                 # 主SOP流程定义
│   ├── sop_guidelines.json                      # 主SOP专属规则
│   └── sop_observations.json                    # 主SOP专属观测
├── {main_journey_name}__branch_{branch_name}/   # 【二级分支SOP】
│   ├── sop.json                                 # 包含 parent_sop_id, parent_state_id
│   ├── sop_guidelines.json                      # 分支SOP专属规则
│   └── sop_observations.json                    # 分支SOP专属观测
└── {main_journey_name}__edge_{edge_name}/       # 【三级子弹SOP】
    ├── sop.json                                 # 包含 parent_sop_id, is_edge_case: true
    ├── sop_guidelines.json                      # 子弹SOP专属规则
    └── sop_observations.json                    # 子弹SOP专属观测
```

**命名规范**：
```
main_journey_name:     {业务场景} (例：schedule_appt)
branch_journey_name:   {main_journey_name}__branch_{分支标识} (例：schedule_appt__branch_dept_select)
edge_case_journey_name: {main_journey_name}__edge_{场景标识} (例：schedule_appt__edge_user_change_mind)
```

**关联方式**：
- 二级分支SOP：通过 `sop.json` 中的 `parent_sop_id` 和 `parent_state_id` 字段关联到主SOP
- 三级子弹SOP：通过 `sop.json` 中的 `parent_sop_id` 和 `is_edge_case: true` 字段标识

#### 5.6.3 二级分支SOP配置示例

**场景说明**：在预约挂号主SOP的"科室选择"节点，用户可能需要科室推荐分支。

**文件路径**: `agents/medical_customer_service_agent/02_journeys/schedule_appt__branch_dept_select/sop.json`

```json
{
  "sop_id": "branch_dept_select_001",
  "sop_type": "branch",
  "parent_sop_id": "schedule_appt_001",
  "parent_state_id": "state_000",
  "sop_title": "科室推荐分支SOP",
  "sop_description": "当用户不确定选择哪个科室时，引导用户描述症状，智能推荐合适的科室",
  "trigger_conditions": [
    "用户不知道该挂哪个科室",
    "用户询问科室推荐",
    "用户描述症状但未确定科室"
  ],
  "sop_states": [
    {
      "state_id": "branch_state_000",
      "state_name": "症状收集",
      "state_type": "chat",
      "instruction": "询问用户的主要症状或不适部位，收集足够信息用于科室推荐",
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
      "instruction": "根据用户描述的症状，推荐1-3个合适的科室，并说明推荐理由",
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
      "instruction": "确认用户选择的科室，引导返回主SOP流程继续预约",
      "is_end_state": true,
      "return_to_parent": true
    }
  ]
}
```

**关键字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `sop_type` | string | SOP类型：`main`(主SOP)、`branch`(分支SOP)、`edge`(子弹SOP) |
| `parent_sop_id` | string | 父级SOP的ID，分支SOP和子弹SOP必填 |
| `parent_state_id` | string | 父级SOP中触发该子SOP的状态节点ID |
| `return_to_parent` | boolean | 结束状态是否返回父级SOP继续执行 |

#### 5.6.4 三级子弹SOP配置示例

**场景说明**：用户在预约过程中突然改变主意，需要处理这种边缘场景。

**文件路径**: `agents/medical_customer_service_agent/02_journeys/schedule_appt__edge_user_change_mind/sop.json`

```json
{
  "sop_id": "edge_user_change_mind_001",
  "sop_type": "edge",
  "parent_sop_id": "schedule_appt_001",
  "sop_title": "用户改变主意场景SOP",
  "sop_description": "处理用户在预约过程中突然表示'我再考虑一下'或'暂时不需要'等场景",
  "is_edge_case": true,
  "priority": 1,
  "trigger_conditions": [
    "用户表示'我再考虑一下'",
    "用户表示'暂时不需要'",
    "用户表示'以后再说'",
    "用户想要退出预约流程"
  ],
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

**关键字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `is_edge_case` | boolean | 标识是否为边缘场景SOP |
| `priority` | integer | 优先级，子弹SOP通常为1（最低优先级） |

#### 5.6.5 子Journey专属规则配置

**文件路径**: `agents/medical_customer_service_agent/02_journeys/schedule_appt__branch_dept_select/sop_guidelines.json`

```json
{
  "sop_id": "branch_dept_select_001",
  "sop_title": "科室推荐分支SOP",
  "remark": "科室推荐分支专属规则",
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
      "condition": "用户进入科室推荐分支，未描述症状",
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

#### 5.6.6 子Journey专属观测配置

**文件路径**: `agents/medical_customer_service_agent/02_journeys/schedule_appt__branch_dept_select/sop_observations.json`

```json
{
  "sop_id": "branch_dept_select_001",
  "sop_title": "科室推荐分支SOP",
  "remark": "科室推荐分支专属观测",
  "sop_observations": [
    {
      "observation_id": "branch_obs_user_has_symptom_001",
      "condition": "用户已描述主要症状或不适部位",
      "remark": "观测用户是否已提供症状信息，用于科室推荐的依赖"
    },
    {
      "observation_id": "branch_obs_user_accept_recommend_001",
      "condition": "用户接受了推荐的科室",
      "remark": "观测用户是否接受推荐，用于确认返回主SOP的依赖"
    }
  ]
}
```

#### 5.6.7 设计原则与约束

**8大核心设计原则**：

| 原则 | 说明 | 违反后果 |
|------|------|----------|
| **主干唯一不可逆** | 主SOP是单一权威主干，所有分支必须明确标注"偏离主干"，禁止循环路径 | 流程混乱、死循环 |
| **维度分层锁死** | 严格区分主SOP(主干层)、分支SOP(适配层)、子弹SOP(补全层)，层级之间禁止跨越 | 层级混乱、维护困难 |
| **合规全链路前置** | 所有合规相关规则必须在全局规则层统一定义，禁止在分支SOP中临时添加 | 合规风险、审计失败 |
| **全局-局部协同** | 全局规则与分支SOP规则必须明确优先级和排除关系 | 规则冲突、行为不一致 |
| **粒度解耦可控** | 主SOP节点聚焦单一核心目标，分支SOP依附于主SOP节点，禁止一个节点多个主目标 | 粒度过粗、难以维护 |
| **目标对齐防偏离** | 子Journey必须有明确的父级关联，确保业务目标一致 | 目标偏离、产出不符预期 |
| **并发安全与隔离** | 子Journey之间相互独立，可并行加载和执行 | 并发冲突、数据损坏 |
| **过程可追溯** | 子Journey配置独立存储，支持独立版本管理 | 无法追溯、调试困难 |

**10条避坑红线**：

1. ❌ 禁止一个节点设置多个核心主目标
2. ❌ 禁止把可选子目标纳入强制结束条件
3. ❌ 禁止使用模糊、主观的结束条件
4. ❌ 禁止结束条件和合规要求脱节
5. ❌ 禁止跨节点设置目标
6. ❌ 禁止主流程节点超过9个或有分支
7. ❌ 禁止单个节点内分支超过5个
8. ❌ 禁止一个分支里用了超过3个维度
9. ❌ 禁止用补充维度拆了新的分支
10. ❌ 禁止跨节点做了维度组合

#### 5.6.8 构建脚本适配

构建脚本 `automation/build_agent.py` 需要支持递归加载子Journey：

```python
async def _load_journeys(self):
    """加载所有业务SOP（含子Journey）"""
    journeys_dir = self.agent_path / "02_journeys"
    
    for journey_folder in journeys_dir.iterdir():
        if journey_folder.is_dir():
            # 加载一级主SOP
            await self._load_single_journey(journey_folder)
            
            # 递归加载子Journey
            sub_journeys_dir = journey_folder / "sub_journeys"
            if sub_journeys_dir.exists():
                for sub_folder in sub_journeys_dir.iterdir():
                    if sub_folder.is_dir():
                        await self._load_single_journey(sub_folder, is_sub_journey=True)
```

---

## 六、核心构建脚本说明

### 6.1 脚本位置与功能

**文件路径**: `automation/build_agent.py`

> 该脚本已独立拆分到 `automation/` 目录下，包含详细的中文注释和完整的错误处理。

**核心功能**:
1. **完全隔离构建**: 仅加载指定 Agent 文件夹内的所有配置，与其他 Agent 无任何交互
2. **资产加载**: 按顺序加载术语表、用户画像、观测、Guideline、工具、SOP
3. **关系绑定**: 完整实现 Parlant 原生的排除关系与依赖关系
4. **状态机构建**: 根据 SOP 配置文件构建 Journey 状态机
5. **动态导入**: 支持动态导入 Agent 专属的工具实现代码
6. **用户画像应用**: 基于用户分群创建群体特定指南，实现个性化服务

### 6.2 使用方式

#### 基本用法

```bash
# 构建单个完全隔离 Agent
python automation/build_agent.py [agent_folder_name]

# 示例：构建医疗客服 Agent
python automation/build_agent.py medical_customer_service_agent

# 示例：构建航空客服 Agent
python automation/build_agent.py airline_customer_service_agent
```

#### 不带参数运行

```bash
python automation/build_agent.py
```

输出:
```
============================================================
❌ 请指定要构建的完全隔离 Agent 文件夹名称
============================================================

使用示例:
   python build_agent.py medical_customer_service_agent
   python build_agent.py airline_customer_service_agent

💡 当前可用的 Agent:
   - medical_customer_service_agent
   - airline_customer_service_agent

============================================================
```

### 6.3 构建流程详解

构建过程分为 6 个主要阶段:

```
阶段 1: 前置校验
  └─ 验证 Agent 文件夹是否存在
  └─ 检查基础配置文件是否完整（含 user_profiles）

阶段 2: 加载基础信息
  └─ 读取 agent_metadata.json
  └─ 获取 Agent 名称、描述、端口等配置

阶段 3: 初始化 Parlant Server
  └─ 创建 Server 实例
  └─ 创建 Agent 实例

阶段 4: 加载基础资产
  ├─ 加载领域术语表 (glossary/)
  ├─ 加载用户画像配置 (agent_user_profiles.json) 【新增】
  ├─ 加载全局观测 (agent_observations.json)
  ├─ 加载全局 Guideline(agent_guidelines.json)
  └─ 加载专属工具库 (03_tools/)

阶段 5: 加载业务 SOP
  ├─ 遍历 journeys/ 目录
  ├─ 对每个 SOP:
  │   ├─ 加载 SOP 专属观测
  │   ├─ 加载 SOP 专属 Guideline
  │   ├─ 绑定 SOP 内关系
  │   └─ 构建 Journey 状态机
  └─ 创建 Journey 并绑定全局规则

阶段 6: 构建完成
  └─ 显示构建成功消息
  └─ 提供测试地址
  └─ 保持服务运行
```

### 6.4 核心类与函数

#### IsolatedAgentBuilder 类

完全隔离式 Agent 构建器，包含以下核心方法:

| 方法名 | 功能说明 |
|--------|----------|
| `build(agent_folder_name)` | 构建主入口，协调整个构建流程 |
| `_load_glossary()` | 加载领域术语表 |
| `_load_global_observations()` | 加载全局观测 |
| `_load_global_guidelines()` | 加载全局 Guideline 并绑定关系 |
| `_load_tools()` | 加载专属工具库 |
| `_load_journeys()` | 加载所有业务 SOP |
| `_bind_sop_relationships()` | 绑定 SOP 内的排除/依赖关系 |
| `_build_journey_state_machine()` | 构建 Journey 状态机 |

#### 关键设计特性

1. **资产实例池**: 
   ```python
   self.instance_pool = {
       "tools": {},
       "canned_responses": {},
       "observations": {},
       "guidelines": {},
       "journeys": {}
   }
   ```
   - 每个 Agent 独立维护自己的资产池
   - 构建完成后自动清空，确保完全隔离

2. **分阶段加载**:
   - 先创建所有对象实例
   - 再统一绑定关系
   - 避免循环依赖导致的实例化失败

3. **错误处理**:
   - 完善的文件存在性校验
   - 友好的错误提示消息
   - 详细的异常堆栈追踪

### 6.5 日志输出示例

构建过程中的典型日志输出:

```
============================================================
🚀 开始构建完全隔离 Agent: medical_customer_service_agent
============================================================
✅ 加载 Agent 基础信息完成：智慧医疗客服 Agent
✅ Agent 实例创建成功（完全隔离）
📚 加载术语表：medical_terms.json (3 个术语)
✅ 加载 Agent专属领域术语表完成，共 3 个术语
👥 加载用户画像配置：agent_user_profiles.json (3 个分群，2 个画像)
✅ 加载 Agent专属用户画像完成：VIP 客户、价格敏感型客户、银发族客户
✅ 加载 Agent专属全局观测完成，共 2 个观测
✅ 加载 Agent专属全局模板话术完成，共 4 个话术
✅ 加载 Agent专属全局 Guideline 完成，共 4 个规则
🔗 绑定 Agent 排除关系：medical_soothe_001 → medical_greet_001
🔗 绑定 Agent 依赖关系：medical_soothe_001 → ['medical_obs_user_angry_001']
✅ 加载 Agent专属全局规则完成 (排除关系:2, 依赖关系:2)

🔧 正在加载 Agent专属工具：tool_get_upcoming_slots
✅ 工具 medical_tool_get_upcoming_slots 加载成功
✅ 加载 Agent专属工具完成，共加载 2 个工具：['medical_tool_get_upcoming_slots', 'medical_tool_schedule_appt']

------------------------------------------------------------
📋 开始处理 Agent专属业务 SOP: schedule_appt
------------------------------------------------------------
✅ SOP 专属观测加载完成，共 3 个观测
✅ SOP schedule_appt_001 专属模板话术加载完成，共 4 个话术
✅ SOP schedule_appt_001 专属 Guideline 加载完成，共 3 个规则
🔗 绑定 SOP 排除关系：schedule_appt_doctor_recommend_001 → schedule_appt_dept_guide_001
🔗 绑定 SOP 依赖关系：schedule_appt_doctor_recommend_001 → ['schedule_appt_obs_user_has_dept_001']
✅ SOP schedule_appt_001 专属规则关系绑定完成 (排除:1, 依赖:2)
📍 创建初始状态：初始 - 科室选择
📍 创建状态：加载可预约医生
📍 创建状态：医生与时段选择
📍 创建状态：预约信息确认
📍 创建状态：提交预约
📍 创建状态：预约完成
🏁 标记结束状态：预约完成
🎉 SOP 预约挂号全流程 SOP 状态机构建完成

============================================================
🎉 完全隔离 Agent 智慧医疗客服 Agent 构建完成！
🔗 测试地址：http://localhost:8801
============================================================
```

### 6.6 高级特性

#### 6.6.1 动态导入机制

构建脚本支持动态导入 Agent专属的工具实现:

```python
# 根据工具文件夹路径动态生成模块名
module_path = str(impl_path.parent).replace(
    str(ROOT_PATH), ""
).replace("/", ".").strip(".")

# 动态导入模块
tool_module = __import__(
    f"{module_path}.{module_name}",
    fromlist=[meta_config["tool_name"]]
)

# 获取工具函数
tool_func = getattr(tool_module, meta_config["tool_name"])
```

#### 6.6.2 关系绑定优先级

依赖关系查找遵循以下优先级:

```
SOP 内 Guideline > 全局 Guideline > SOP 内 Observation > 全局 Observation
```

排除关系查找遵循以下优先级:

```
SOP 内 Guideline > 全局 Guideline
```

#### 6.6.3 状态机容错

- 源状态不存在时自动跳过该转移
- 未找到 Guideline 时使用空列表
- 工具不存在时不绑定工具
- 所有异常都会记录详细日志

### 6.7 调试技巧

#### 启用详细日志

修改脚本中的打印语句，可以查看更详细的构建过程:

```python
# 在 IsolatedAgentBuilder.__init__ 中添加
print(f"🔍 资产实例池初始化完成")

# 在每个加载方法中添加详细日志
print(f"📝 正在加载配置文件：{config_path}")
print(f"🔧 正在创建 {asset_type}: {asset_id}")
```

#### 查看错误详情

当构建失败时，使用以下方式查看详细错误:

```bash
# 重定向错误输出到文件
python automation/build_agent.py medical_customer_service_agent 2>&1 | tee build_error.log
```

#### 验证配置文件

在运行构建前，可以先验证 JSON 配置文件的格式:

```bash
# 使用 Python 验证 JSON 格式
python -c "import json; json.load(open('agents/medical/00_agent_base/agent_metadata.json'))"
```

### 6.8 性能优化建议

1. **批量加载**: 对于大量工具的 Agent，可以考虑批量加载策略
2. **缓存机制**: 对于频繁构建的场景，可以添加配置缓存
3. **并行加载**: 不同 SOP 之间可以并行加载 (需确保无依赖关系)
4. **懒加载**: 仅在需要时才加载特定的工具或 SOP

---

## 七、方案核心优势（完全隔离版）

### 7.1 Agent 完全物理隔离，完美满足合规要求

- **核心优势**：每个 Agent 一个完全独立的文件夹，包含该 Agent 的所有配置（基础配置、规则、工具、术语表），Agent 之间无任何共享配置，修改一个 Agent 的配置不会影响其他任何 Agent；
- **合规价值**：完美满足金融、医疗等行业的**严格合规隔离要求**，不同业务线的 Agent 配置完全独立，审计可按单个 Agent 拆分，责任到人。

### 7.2 职责完全解耦，多人协作零干扰

- 流程（SOP）、规则（Guideline）、观测（Observation）、工具（Tool）四大核心模块在单个 Agent 文件夹内彻底拆分；
- 修改流程不影响规则、修改规则不影响工具、修改工具不影响业务配置；
- 产品、运营、开发、合规人员可在单个 Agent 文件夹内分工协作，零干扰。

### 7.3 关系设计严格合规，语境始终狭窄聚焦

- 完整实现 Parlant 原生的排除关系与依赖关系，100% 贴合框架原生能力；
- 排除关系彻底解决了规则冲突问题，依赖关系建立了清晰的规则触发层级；
- 所有规则的激活都严格基于当前对话语境，确保 Agent 的行为 100% 符合业务预期。

### 7.4 人工维护友好，新增 Agent 零成本

- 单个 Agent 文件夹内结构扁平、职责清晰，关系定义直观，人工维护无需写代码；
- 新增 Agent 仅需复制完整的 Agent 模板文件夹，无需修改任何其他配置；
- 新增 SOP、规则、工具仅需在对应 Agent 文件夹内新增文件，完美适配业务快速增长。

### 7.5 全流程可审计，版本追溯精准

- 每个 Agent 的所有配置均为独立的结构化文件，支持 Git 版本管理；
- 单个 Agent 的变更历史可独立追溯，无需过滤其他Agent 的变更；
- 完全符合金融、医疗等行业的审计要求。

---

## 八、使用与维护最佳实践（完全隔离版）

### 8.1 新增完全隔离 Agent

1. 复制现有的 Agent 模板文件夹（如 `medical_customer_service_agent`），重命名为新的 Agent 名称；
2. 修改新 Agent 文件夹内的 `00_agent_base/agent_metadata.json`，定义新 Agent 的基础信息；
3. **修改新 Agent 文件夹内的 `00_agent_base/agent_user_profiles.json`，定义目标用户群体画像与分群策略（可选）**；
4. 修改新 Agent 文件夹内的 `01_agent_rules/` 下的配置，定义新 Agent的专属全局规则；
5. 在新 Agent 文件夹内的 `02_journeys/` 下新增/修改业务 SOP；
6. 在新 Agent 文件夹内的 `03_tools/` 下新增/修改专属工具；
7. 构建新 Agent：`python automation/build_agent.py [新 Agent 文件夹名称]`。

### 8.2 修改单个 Agent 的配置

- **修改基础配置**：仅修改该 Agent 文件夹内的 `00_agent_base/` 下的文件；
- **修改用户画像**：仅修改该 Agent 文件夹内的 `00_agent_base/agent_user_profiles.json`，调整用户分群、画像或专属指南；
- **修改全局规则**：仅修改该 Agent 文件夹内的 `01_agent_rules/` 下的文件；
- **修改业务 SOP**：仅修改该 Agent 文件夹内的 `02_journeys/` 下的对应 SOP 子文件夹；
- **修改工具**：仅修改该 Agent 文件夹内的 `03_tools/` 下的对应工具子文件夹；
- **所有修改仅影响该 Agent，与其他 Agent 完全隔离**。

### 8.3 用户画像配置最佳实践

#### （1）何时需要配置用户画像？

- ✅ **多客户群体服务场景**：同时服务 VIP 客户、普通客户、特殊群体（如老年人、儿童）
- ✅ **差异化服务策略**：不同客户群体需要不同的服务流程、话术、优惠策略
- ✅ **个性化体验需求**：需要根据客户特征提供定制化推荐、专属旅程
- ✅ **精细化运营**：需要追踪不同客户群体的行为模式、转化率、满意度

#### （2）用户分群设计原则

- **基于可识别的特征**：使用 Tags（标签）和 Metadata（元数据）进行明确区分
  - 示例：`tags: ["vip", "price_sensitive", "elderly"]`
  - 示例：`metadata_rules: {"total_purchase_amount": ">10000", "age": ">=60"}`

- **行为模式清晰**：每个分群应有明确的行为特征描述
  - 示例："频繁询问价格和折扣"、"偏好高效私密服务"

- **专属指南具体**：为每个分群设计特定的 Guidelines
  - 示例：VIP 客户 → "提供专属 9 折优惠"
  - 示例：价格敏感客户 → "强调节省金额，提供优惠券"

#### （3）典型用户画像设计技巧

- **拟人化命名**：给画像起一个具体的名字，便于团队理解和沟通
  - 示例："高端商务人士张总"、"精明消费者小王"

- **详细人口统计学特征**：包含年龄、职业、收入等信息
  - 示例："40-50 岁，企业高管，年收入 200 万+"

- **典型对话示例**：提供 3-5 个该画像的典型对话
  - 示例："帮我安排最快的方案，价格不是问题"

- **映射到 Parlant 元素**：明确指定对应的 Tags、Variables、Journeys、Guidelines

#### （4）用户画像落地流程

```python
# 1. 在 agent_user_profiles.json 中定义用户分群
{
  "user_segments": [
    {
      "segment_id": "vip_customers",
      "definition": {
        "tags": ["vip"],
        "metadata_rules": {"total_purchase_amount": ">10000"}
      }
    }
  ]
}

# 2. 在 Guidelines 中使用 Observations 检查客户标签
async def is_vip_matcher(
    ctx: p.GuidelineMatchingContext,
    guideline: p.Guideline
) -> p.GuidelineMatch:
    matched = vip_tag.id in p.Customer.current.tags
    return p.GuidelineMatch(
        id=guideline.id,
        matched=matched,
        rationale="Customer has VIP tag" if matched else "Customer does not have VIP tag"
    )

# 3. 创建仅对特定群体激活的指南
vip_observation = await agent.create_observation(matcher=is_vip_matcher)
vip_guideline = await agent.create_guideline(
    condition="客户询问价格",
    action="提供 VIP 专属折扣",
    dependencies=[vip_observation]
)
```

### 8.4 构建与部署

在命令行中指定要构建的 Agent 文件夹名称，即可完成单个完全隔离 Agent的独立构建与启动，示例：

```bash
# 构建医疗客服 Agent（完全隔离）
python automation/build_agent.py medical_customer_service_agent

# 构建航空客服 Agent（完全隔离，与医疗无任何交互）
python automation/build_agent.py airline_customer_service_agent
```

### 8.4 版本管理

- 每个 Agent 的修改单独提交 PR，提交信息明确标注 Agent 名称与修改内容；
- 单个 Agent 的回滚仅需恢复该 Agent 的文件夹，不影响其他任何 Agent；
- Git 历史可按单个 Agent 文件夹过滤，变更追溯精准。

---

## 九、Parlant 官方文档对照索引

为方便查阅 Parlant 官方文档，本方案涉及的核心概念与官方文档的对照关系如下：

### 9.1 核心概念对应

| 本方案配置 | Parlant 官方概念 | 官方文档路径 |
|------------|------------------|--------------|
| Guidelines（指南） | Guidelines | `docs/concepts/customization/guidelines.md` |
| Observations（观测） | Observational Guidelines | `docs/concepts/customization/relationships.md` |
| Journeys（旅程/SOP） | Journeys | `docs/concepts/customization/journeys.md` |
| Tools（工具） | Tools | `docs/concepts/customization/tools.md` |
| Relationships（关系） | Relationships | `docs/concepts/customization/relationships.md` |
| Canned Responses（模板话术） | Canned Responses | `docs/concepts/customization/canned-responses.md` |
| Glossary（术语表） | Glossary | `docs/concepts/customization/glossary.md` |
| Variables（变量） | Variables | `docs/concepts/customization/variables.md` |
| Tags（标签） | Tags | `docs/concepts/customization/tags.md` |
| Customers（客户） | Customers | `docs/concepts/entities/customers.md` |
| Agents（智能体） | Agents | `docs/concepts/entities/agents.md` |

### 9.2 关系类型对应

| 本方案术语 | Parlant 官方术语 | 说明 |
|------------|------------------|------|
| 排除关系 | Priority / `prioritize_over` | 当 S 和 T 同时激活时，只有 S 激活 |
| 依赖关系 | Dependency / `depend_on` | 当 S 激活时，除非 T 也激活否则关闭 |
| 蕴含关系 | Entailment / `entail` | 当 S 激活时，T 也应该始终激活 |
| 消歧义关系 | Disambiguation / `disambiguate` | 当 S 激活且多个 T 激活时，请客户澄清 |

### 9.3 重要设计理念引用

1. **Guidelines vs Journeys 的区别**（来自 `guidelines.md`）：
   - Journeys：理想的 step-by-step 交互流程，适合复杂的多步骤交互
   - Guidelines：提供 contextual nudges（上下文推动），适合简单、特定场景的调整

2. **Journey 的灵活性**（来自 `journeys.md`）：
   - Journeys 不是 rigidly followed（严格遵循），而是作为 guiding framework（指导框架）
   - Agent 会 adaptive approach（适应性方法），可以 skip states、revisit previous states、jump ahead

3. **Observation 的本质**（来自 `relationships.md`）：
   - Observation 本质上是**没有 action 的 Guideline**
   - 主要用于通过关系激活/停用其他 Guidelines 或 Journeys

4. **ARQs 强制执行机制**（来自 `explainability.md`）：
   - ARQs（Attentive Reasoning Queries）是结构化推理蓝图
   - 确保指南被遵循，产生可解释的推理日志
   - 相关论文：[Attentive Reasoning Queries](https://arxiv.org/abs/2503.03669)

---

## 十、总结

本方案是一套**完全贴合 Parlant 原生特性、多 Agent 完全隔离、面向生产环境**的工程化配置管理体系，核心价值在于：

1. ✅ **Agent 完全物理隔离**：每个 Agent 独立文件夹，100% 内聚所有配置，完美满足合规要求
2. ✅ **职责完全解耦**：流程、规则、观测、工具四大模块彻底拆分，多人协作零干扰
3. ✅ **关系严格合规**：完整实现 Parlant 原生的排除/依赖关系，语境始终狭窄聚焦
4. ✅ **人工维护友好**：结构扁平、职责清晰，新增 Agent 零成本
5. ✅ **全流程可审计**：支持 Git 版本管理，单个 Agent 变更独立追溯
6. ✅ **用户画像支持**：内置用户分群与画像配置，支持基于群体特征的个性化服务

方案已覆盖 Parlant 官方文档的所有核心概念，包括 Guidelines、Journeys、Tools、Relationships、Canned Responses、Glossary、**Customers（用户画像）**等，并严格遵循官方 API 设计规范，可直接用于金融、医疗、电商等行业的生产级 Agent 落地。
