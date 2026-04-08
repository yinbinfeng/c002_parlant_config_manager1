# Journey（旅程/SOP）概念说明

## 一、概念定义

Journey（旅程/SOP）是 Parlant 框架中用于定义**结构化对话流程**的机制。它允许我们设计 Agent 应该遵循的特定对话流程，如预订机票、故障排查、引导用户完成特定任务等。

### 核心特点

- **状态机模型**: Journey 基于**状态机**设计，每个节点代表一个状态，边代表状态转换
- **灵活适应**: Journey 不是刚性流程，Agent 可以跳过状态、回溯状态或提前进入后续状态
- **指导框架**: Journey 作为指导框架，而非严格脚本，Agent 会尽力遵循流程同时保持适应性

## 二、Journey 结构组成

Journey 包含 4 个核心组件：

| 组件 | 说明 |
|------|------|
| **Title（标题）** | Journey 的简短描述性名称 |
| **Conditions（条件）** | 决定何时激活该 Journey 的上下文查询 |
| **Description（描述）** | Journey 的性质说明，包含动机或导向性注释 |
| **States & Transitions（状态与转换）** | 状态图，定义理想的对话流程 |

## 三、配置文件格式

### 3.1 目录结构

```
02_journeys/
├── schedule_appt/                    # 一级主 SOP
│   ├── sop.json                      # SOP 流程定义
│   ├── sop_guidelines.json           # SOP 专属规则
│   └── sop_observations.json         # SOP 专属观测
├── schedule_appt__branch_dept_select/    # 二级分支 SOP
│   ├── sop.json
│   ├── sop_guidelines.json
│   └── sop_observations.json
└── schedule_appt__edge_user_change_mind/ # 三级子弹 SOP
    ├── sop.json
    ├── sop_guidelines.json
    └── sop_observations.json
```

### 3.2 SOP 核心配置文件

**文件路径**: `agents/{agent_name}/02_journeys/{journey_name}/sop.json`

```json
{
  "sop_id": "schedule_appt_001",
  "sop_title": "预约挂号全流程 SOP",
  "sop_description": "引导用户完成科室选择、医生选择、时段选择、信息确认、预约提交的全流程",
  "trigger_conditions": [
    "用户想要预约挂号",
    "用户询问门诊可预约时间",
    "用户想要找医生就诊"
  ],
  "timeout": 1800,
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
          "condition": "用户已明确选择具体科室"
        }
      ]
    },
    {
      "state_id": "state_001",
      "state_name": "加载可预约医生",
      "state_type": "tool",
      "bind_tool_id": "medical_tool_get_upcoming_slots",
      "instruction": "调用门诊可预约时间查询工具",
      "transitions": [
        {
          "target_state_id": "state_002",
          "condition": "工具返回可预约医生与时段信息后"
        }
      ]
    },
    {
      "state_id": "state_005",
      "state_name": "预约完成",
      "state_type": "chat",
      "instruction": "告知用户预约结果，发送预约号、就诊信息",
      "bind_canned_response_ids": ["schedule_appt_cr_success_001"],
      "is_end_state": true
    }
  ]
}
```

## 四、状态类型

### 4.1 Chat State（对话状态）

Agent 在此状态下与用户对话，由状态指令引导。Agent 可能在此状态停留多轮对话。

```json
{
  "state_id": "state_000",
  "state_name": "科室选择",
  "state_type": "chat",
  "instruction": "询问用户想要预约哪个科室的号"
}
```

### 4.2 Tool State（工具状态）

Agent 在此状态下调用外部工具执行操作，并将结果加载到上下文中。工具状态后必须跟随对话状态。

```json
{
  "state_id": "state_001",
  "state_name": "加载可预约医生",
  "state_type": "tool",
  "bind_tool_id": "medical_tool_get_upcoming_slots",
  "instruction": "调用门诊可预约时间查询工具"
}
```

### 4.3 Fork State（分支状态）

用于显式分支对话流程，使流程更清晰、有序。

```json
{
  "state_id": "fork_001",
  "state_name": "判断用户意图",
  "state_type": "fork",
  "transitions": [
    {"target_state_id": "state_a", "condition": "用户选择 A"},
    {"target_state_id": "state_b", "condition": "用户选择 B"}
  ]
}
```

## 五、转换类型

### 5.1 Direct Transition（直接转换）

无条件转换，总是执行。

```json
{
  "target_state_id": "state_001"
}
```

### 5.2 Conditional Transition（条件转换）

只有满足条件时才执行。

```json
{
  "target_state_id": "state_002",
  "condition": "用户已明确选择具体科室"
}
```

## 六、三层 SOP 架构

### 6.1 架构概述

```
第一层：一级主 SOP（主干层）
├─ 5-9 个节点，无分支
├─ 定义业务的核心流程骨架
├─ 冻结后禁止修改
└─ 数量限制：最多 10 个

第二层：二级分支 SOP（适配层）
├─ 依附于主 SOP 节点
├─ 命名格式：{main_journey}__branch_{branch_name}
├─ 处理主流程中的业务分支场景
└─ 数量限制：最多 10 个

第三层：三级子弹 SOP（补全层）
├─ 边缘异常场景原子化补全
├─ 命名格式：{main_journey}__edge_{edge_name}
├─ 处理异常、边缘、降级等场景
└─ 数量限制：最多 30 个
```

**重要提示**：SOP数量限制必须严格遵守，超过限制将导致配置校验失败。

### 6.2 二级分支 SOP 配置

```json
{
  "sop_id": "branch_dept_select_001",
  "sop_type": "branch",
  "parent_sop_id": "schedule_appt_001",
  "parent_state_id": "state_000",
  "sop_title": "科室推荐分支 SOP",
  "sop_description": "当用户不确定选择哪个科室时，引导用户描述症状，智能推荐合适的科室"
}
```

### 6.3 三级子弹 SOP 配置

```json
{
  "sop_id": "edge_user_change_mind_001",
  "sop_type": "edge",
  "parent_sop_id": "schedule_appt_001",
  "sop_title": "用户改变主意场景 SOP",
  "is_edge_case": true,
  "priority": 1
}
```

## 七、核心字段说明

### sop.json 字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `sop_id` | string | ✅ | SOP 唯一标识 |
| `sop_title` | string | ✅ | SOP 标题 |
| `sop_description` | string | ❌ | SOP 描述 |
| `trigger_conditions` | array | ✅ | 触发条件列表 |
| `timeout` | integer | ❌ | 超时时间（秒） |
| `sop_type` | string | ❌ | 类型：`main`/`branch`/`edge` |
| `parent_sop_id` | string | ❌ | 父级 SOP ID（分支/子弹 SOP 必填） |
| `parent_state_id` | string | ❌ | 父级 SOP 中触发该子 SOP 的状态节点 ID |
| `is_edge_case` | boolean | ❌ | 是否为边缘场景 SOP |
| `sop_states` | array | ✅ | 状态列表 |

### 状态字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `state_id` | string | ✅ | 状态唯一标识 |
| `state_name` | string | ✅ | 状态名称 |
| `state_type` | string | ✅ | 状态类型：`chat`/`tool`/`fork` |
| `instruction` | string | ✅ | 状态指令 |
| `bind_guideline_ids` | array | ❌ | 绑定的 Guideline ID 列表 |
| `bind_tool_id` | string | ❌ | 绑定的工具 ID（tool 状态必填） |
| `bind_canned_response_ids` | array | ❌ | 绑定的模板话术 ID 列表 |
| `transitions` | array | ❌ | 转换列表 |
| `is_end_state` | boolean | ❌ | 是否为结束状态 |

## 八、设计原则

### 8 大核心设计原则

| 原则 | 说明 |
|------|------|
| **主干唯一不可逆** | 主 SOP 是单一权威主干，所有分支必须明确标注"偏离主干" |
| **维度分层锁死** | 严格区分主 SOP、分支 SOP、子弹 SOP，层级之间禁止跨越 |
| **合规全链路前置** | 所有合规相关规则必须在全局规则层统一定义 |
| **全局-局部协同** | 全局规则与分支 SOP 规则必须明确优先级和排除关系 |
| **粒度解耦可控** | 主 SOP 节点聚焦单一核心目标 |
| **目标对齐防偏离** | 子 Journey 必须有明确的父级关联 |
| **并发安全与隔离** | 子 Journey 之间相互独立，可并行加载和执行 |
| **过程可追溯** | 子 Journey 配置独立存储，支持独立版本管理 |

### 10 条避坑红线

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

## 九、Journey vs Task Automation

### 正确用法

Journey 用于**对话协议**，引导用户完成流程：

```
[*] --> 询问订单号 --> 获取订单详情 --> 处理退款 --> [*]
```

### 错误用法

Journey 不应用于**任务自动化流程**：

```
[*] --> 查找用户 ID --> 加载偏好设置 --> 发送邮件 --> [*]
```

**原因**: 业务逻辑应由工具处理，Journey 只负责对话流程。

## 十、Journey-Scoped Guidelines

可以为 Journey 添加专属 Guideline，仅在该 Journey 激活时生效：

```json
{
  "sop_id": "schedule_appt_001",
  "sop_scoped_guidelines": [
    {
      "guideline_id": "schedule_appt_dept_guide_001",
      "scope": "sop_only",
      "condition": "用户未明确选择科室",
      "action": "使用科室列表模板话术引导用户选择"
    }
  ]
}
```

## 十一、注意事项

1. **工具状态后必须是对话状态**: 工具状态不能直接转换到另一个工具状态
2. **条件转换与直接转换互斥**: 如果有条件转换，就不能有直接转换
3. **状态数量控制**: 主 SOP 节点控制在 5-9 个
4. **分支数量控制**: 单个节点内分支不超过 5 个
5. **优先级管理**: 子弹 SOP 通常设置为最低优先级

## 十二、相关文档

- [Guideline（指南）说明](./guideline.md)
- [Tools（工具）说明](./tools.md)
- [Observation（观测）说明](./observation.md)
