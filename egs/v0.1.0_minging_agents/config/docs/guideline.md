# Guideline（指南）概念说明

## 一、概念定义

Guideline（指南）是 Parlant 框架中**塑造 Agent 行为的核心机制**，用于在特定上下文中引导 Agent 的响应方式。它允许我们定义 Agent 在特定场景下应该如何响应，覆盖其默认行为，确保其行为符合业务预期。

### 核心理念

Parlant 的核心理念是 **"Stop Fighting Prompts, Teach Principles"** —— 彻底颠覆传统"写超长系统提示词碰运气"的 Agent 开发模式，通过结构化的规则定义，确保 LLM Agent 严格遵循业务要求。

## 二、基本结构

每个 Guideline 由两部分组成：

| 组成部分 | 说明 |
|---------|------|
| **Condition（条件）** | 定义何时触发该规则，描述触发场景 |
| **Action（动作）** | 定义触发后应该执行什么行为 |

### 示例

```json
{
  "guideline_id": "medical_greet_001",
  "condition": "用户首次对话、向代理打招呼（如你好、哈喽、早上好）",
  "action": "用友好的语气回应用户，主动询问用户的医疗相关需求，保持简洁不超过 2 句话"
}
```

## 三、配置文件格式

### 3.1 全局 Guideline 配置

**文件路径**: `agents/{agent_name}/01_agent_rules/agent_guidelines.json`

```json
{
  "agent_id": "medical_customer_service_agent_001",
  "remark": "医疗客服 Agent 专属全局 Guideline",
  "agent_guidelines": [
    {
      "guideline_id": "medical_greet_001",
      "scope": "agent_global",
      "condition": "用户首次对话、向代理打招呼",
      "action": "用友好的语气回应用户，主动询问用户的医疗相关需求",
      "priority": 3,
      "composition_mode": "FLUID",
      "bind_canned_response_ids": ["medical_cr_greet_001"],
      "exclusions": [],
      "dependencies": []
    }
  ]
}
```

### 3.2 SOP 专属 Guideline 配置

**文件路径**: `agents/{agent_name}/02_journeys/{journey_name}/sop_guidelines.json`

```json
{
  "sop_id": "schedule_appt_001",
  "sop_title": "预约挂号全流程 SOP",
  "sop_scoped_guidelines": [
    {
      "guideline_id": "schedule_appt_dept_guide_001",
      "scope": "sop_only",
      "condition": "用户未明确选择科室",
      "action": "使用科室列表模板话术引导用户选择",
      "priority": 4,
      "composition_mode": "FLUID",
      "bind_canned_response_ids": ["schedule_appt_cr_dept_list_001"],
      "exclusions": [],
      "dependencies": []
    }
  ]
}
```

## 四、核心字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `guideline_id` | string | ✅ | 规则唯一标识 |
| `scope` | string | ✅ | 作用域：`agent_global`（全局）或 `sop_only`（SOP 专属） |
| `condition` | string | ✅ | 触发条件，描述何时激活该规则 |
| `action` | string | ✅ | 执行动作，描述应该做什么 |
| `priority` | integer | ❌ | 优先级，数值越大优先级越高 |
| `composition_mode` | string | ❌ | 组合模式：`FLUID`（灵活）或 `STRICT`（严格） |
| `bind_canned_response_ids` | array | ❌ | 绑定的模板话术 ID 列表 |
| `exclusions` | array | ❌ | 排除关系，该规则激活时排除的其他规则 ID |
| `dependencies` | array | ❌ | 依赖关系，该规则激活所依赖的 Observation ID |

## 五、作用域说明

### 5.1 全局 Guideline（agent_global）

- **定义位置**: `01_agent_rules/agent_guidelines.json`
- **生效范围**: 跨所有 SOP 生效，适用于 Agent 的所有对话场景
- **典型用途**: 问候、安抚、合规红线、转人工等通用规则

### 5.2 SOP 专属 Guideline（sop_only）

- **定义位置**: `02_journeys/{journey_name}/sop_guidelines.json`
- **生效范围**: 仅在对应 SOP 激活时生效
- **典型用途**: 特定业务流程中的分支处理、状态引导

## 六、组合模式

### FLUID（灵活模式）

- Agent 可以灵活组合多个 FLUID 规则
- 适用于一般性指导，允许 Agent 根据上下文调整

### STRICT（严格模式）

- Agent 必须严格遵循该规则，不允许偏离
- 适用于合规红线、关键业务逻辑

## 七、关系类型

### 7.1 排除关系（exclusions）

当规则 S 激活时，排除规则 T：

```json
{
  "guideline_id": "medical_soothe_001",
  "exclusions": ["medical_greet_001"]
}
```

**使用场景**: 避免规则冲突，确保语境聚焦

### 7.2 依赖关系（dependencies）

规则 S 激活的前提是 Observation T 也激活：

```json
{
  "guideline_id": "medical_soothe_001",
  "dependencies": ["medical_obs_user_angry_001"]
}
```

**使用场景**: 建立规则触发层级，确保上下文正确

## 八、编写最佳实践

### 8.1 条件编写原则

**DON'T** - 过于模糊：
```
"condition": "Customer is unhappy"
```

**DO** - 具体且可判断：
```
"condition": "用户表达不满、愤怒、抱怨，使用负面情绪词汇，如'投诉''没用''垃圾'"
```

### 8.2 动作编写原则

**DON'T** - 过于宽泛：
```
"action": "Make them feel better"
```

**DO** - 具体且可执行：
```
"action": "先使用医疗专属安抚模板话术安抚用户情绪，再询问用户的具体问题"
```

### 8.3 平衡原则

- **过粗**: 规则过于模糊，Agent 无法准确执行
- **过细**: 规则过于死板，Agent 无法灵活应对
- **适中**: 规则清晰明确，同时保留一定灵活性

## 九、Guideline vs Journey

| 特性 | Guideline | Journey |
|------|-----------|---------|
| **用途** | 提供上下文推动（contextual nudges） | 提供结构化的步骤流程 |
| **适用场景** | 简单、特定场景的调整 | 复杂的多步骤交互 |
| **灵活性** | 更灵活，可随时激活/停用 | 有明确的状态流转 |
| **复杂度** | 单条规则，简单直接 | 状态机，复杂但有序 |

## 十、注意事项

1. **避免过度指定**: 不要试图覆盖所有可能的场景，让 Agent 保持一定的适应性
2. **优先级设计**: 合理设置优先级，确保关键规则优先生效
3. **关系管理**: 正确使用排除和依赖关系，避免规则冲突
4. **版本管理**: 每次修改都应记录变更原因和影响范围
5. **测试验证**: 新增或修改规则后，务必进行充分测试

## 十一、相关文档

- [Observation（观测）说明](./observation.md)
- [Journey（旅程）说明](./journey.md)
- [Canned Responses（模板话术）说明](./canned_responses.md)
