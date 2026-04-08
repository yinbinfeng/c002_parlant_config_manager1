# Observation（观测）概念说明

## 一、概念定义

Observation（观测）是 Parlant 框架中一种特殊的 Guideline，它**只有条件（Condition）没有动作（Action）**。Observation 主要用于建立规则之间的依赖关系，确保特定规则只在正确的上下文中激活。

### 核心特点

- **无动作**: Observation 本身不执行任何操作
- **条件驱动**: 仅用于判断特定条件是否满足
- **关系建立**: 通过依赖/排除关系控制其他规则的激活

## 二、Observation 的本质

Observation 本质上是**没有 action 的 Guideline**：

```python
# 等价于创建一个没有 action 的 Guideline
observation = await agent.create_observation(
    condition="用户表达不满、愤怒、抱怨"
)
```

等价于：

```python
guideline = await agent.create_guideline(
    condition="用户表达不满、愤怒、抱怨",
    action=""  # 空动作
)
```

## 三、配置文件格式

### 3.1 全局 Observation 配置

**文件路径**: `agents/{agent_name}/01_agent_rules/agent_observations.json`

```json
{
  "agent_id": "medical_customer_service_agent_001",
  "remark": "医疗客服 Agent 专属全局观测，作为规则依赖的前置触发条件",
  "agent_observations": [
    {
      "observation_id": "medical_obs_user_angry_001",
      "condition": "用户表达不满、愤怒、抱怨，使用负面情绪词汇，如'投诉''没用''垃圾''生气'",
      "remark": "观测用户是否处于负面情绪状态，用于后续安抚规则的依赖"
    },
    {
      "observation_id": "medical_obs_user_requests_human_001",
      "condition": "用户要求转人工、找客服、对自动回复不满意、要求真人对接",
      "remark": "观测用户是否有转人工需求，用于后续转人工规则的依赖"
    },
    {
      "observation_id": "medical_obs_user_asks_medical_advice_001",
      "condition": "用户询问疾病原因、治疗方法、用药建议、病情诊断",
      "remark": "观测用户是否有医疗诊断需求，用于合规红线规则的依赖"
    }
  ]
}
```

### 3.2 SOP 专属 Observation 配置

**文件路径**: `agents/{agent_name}/02_journeys/{journey_name}/sop_observations.json`

```json
{
  "sop_id": "schedule_appt_001",
  "sop_title": "预约挂号全流程 SOP",
  "remark": "仅预约挂号 SOP 生效的专属观测",
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
    }
  ]
}
```

## 四、核心字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `observation_id` | string | ✅ | 观测唯一标识 |
| `condition` | string | ✅ | 观测条件，描述何时激活该观测 |
| `remark` | string | ❌ | 备注说明，描述该观测的用途 |

## 五、Observation 的使用方式

### 5.1 作为依赖条件

Guideline 可以依赖 Observation，只有当 Observation 也激活时，Guideline 才会激活：

```json
{
  "guideline_id": "medical_soothe_001",
  "condition": "用户处于负面情绪状态",
  "action": "先使用医疗专属安抚模板话术安抚用户情绪",
  "dependencies": ["medical_obs_user_angry_001"]
}
```

**逻辑**: 只有当 `medical_obs_user_angry_001` 观测激活（用户确实表达负面情绪）时，安抚规则才会激活。

### 5.2 用于排除其他规则

Observation 可以排除其他 Guideline：

```python
# 当用户处于负面情绪时，排除常规问候规则
await observation_angry.prioritize_over(guideline_greet)
```

### 5.3 用于消歧义

当多个规则可能同时激活时，使用 Observation 消歧义：

```python
ambiguous_limits = await agent.create_observation(
    condition="用户询问限额但不清楚是哪种类型"
)

await ambiguous_limits.disambiguate([
    fetch_atm_limits,
    fetch_credit_card_limits
])
```

## 六、依赖关系详解

### 6.1 依赖关系的作用

依赖关系确保 Guideline 只在正确的上下文中激活：

```
Observation A 激活 ─────┐
                        ├──> Guideline B 激活
Condition C 满足 ───────┘
```

### 6.2 配置示例

```json
{
  "agent_guidelines": [
    {
      "guideline_id": "medical_soothe_001",
      "condition": "用户处于负面情绪状态",
      "action": "安抚用户情绪",
      "dependencies": ["medical_obs_user_angry_001"]
    }
  ],
  "agent_observations": [
    {
      "observation_id": "medical_obs_user_angry_001",
      "condition": "用户表达不满、愤怒、抱怨"
    }
  ]
}
```

**激活逻辑**:
1. Parlant 检测到用户表达不满
2. `medical_obs_user_angry_001` 观测激活
3. `medical_soothe_001` 规则的条件满足
4. 由于依赖的观测已激活，规则激活
5. Agent 执行安抚动作

## 七、Observation vs Guideline

| 特性 | Observation | Guideline |
|------|-------------|-----------|
| **Condition** | ✅ 有 | ✅ 有 |
| **Action** | ❌ 无 | ✅ 有 |
| **主要用途** | 建立上下文依赖 | 定义行为规则 |
| **激活效果** | 不产生行为 | 产生行为 |

## 八、使用场景

### 8.1 场景一：情绪检测

```json
{
  "observation_id": "obs_user_angry",
  "condition": "用户表达不满、愤怒、抱怨"
}
```

用于：
- 触发安抚规则
- 排除常规问候规则
- 优先处理用户问题

### 8.2 场景二：意图识别

```json
{
  "observation_id": "obs_user_wants_human",
  "condition": "用户要求转人工、找客服"
}
```

用于：
- 触发转人工规则
- 跳过自动回复流程

### 8.3 场景三：合规检测

```json
{
  "observation_id": "obs_user_asks_diagnosis",
  "condition": "用户询问疾病诊断、治疗方案"
}
```

用于：
- 触发合规拒绝规则
- 引导用户咨询专业医生

### 8.4 场景四：流程状态

```json
{
  "observation_id": "obs_user_selected_dept",
  "condition": "用户已明确选择具体科室"
}
```

用于：
- 触发医生推荐规则
- 推进预约流程

## 九、最佳实践

### 9.1 条件编写原则

**DON'T** - 过于模糊：
```json
{
  "condition": "用户不开心"
}
```

**DO** - 具体可判断：
```json
{
  "condition": "用户表达不满、愤怒、抱怨，使用负面情绪词汇，如'投诉''没用''垃圾''生气'"
}
```

### 9.2 命名规范

建议使用描述性命名：
- `obs_user_angry` - 用户愤怒观测
- `obs_user_wants_human` - 用户转人工观测
- `obs_user_selected_dept` - 用户已选科室观测

### 9.3 作用域管理

- **全局 Observation**: 放在 `01_agent_rules/agent_observations.json`
- **SOP 专属 Observation**: 放在 `02_journeys/{journey}/sop_observations.json`

## 十、关系类型总结

| 关系类型 | 方法 | 说明 |
|----------|------|------|
| **依赖** | `guideline.depend_on(observation)` | Guideline 激活需要 Observation 也激活 |
| **排除** | `observation.prioritize_over(guideline)` | Observation 激活时排除 Guideline |
| **消歧义** | `observation.disambiguate([g1, g2])` | 澄清用户意图，选择正确的 Guideline |

## 十一、注意事项

1. **Observation 没有动作**: 不要在 Observation 中定义 action
2. **条件要具体**: 确保条件可以明确判断
3. **依赖关系要合理**: 避免循环依赖
4. **作用域要明确**: 区分全局观测和 SOP 专属观测
5. **及时更新**: 业务变更时同步更新观测条件

## 十二、相关文档

- [Guideline（指南）说明](./guideline.md)
- [Journey（旅程）说明](./journey.md)
- [Tools（工具）说明](./tools.md)
