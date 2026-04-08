# Variable（变量）概念说明

## 一、概念定义

Variable（变量）是 Parlant 框架中用于**丰富客户上下文**的机制。它为 Agent 提供关于客户的额外信息，帮助 Agent 个性化其服务，就像一位体贴的客服代表知道并记住每位客户的重要细节一样。

### 核心作用

当客户与 Agent 交互时，其变量会自动加载到 Agent 的上下文中，使 Agent 能够根据客户的具体情况定制响应。

## 二、变量的类型

### 2.1 手动设置变量

由管理员手动设置客户变量的值：

```python
variable = await agent.create_variable(
    name="subscription_plan",
    description="客户的订阅计划类型",
)

await variable.set_value_for_customer(
    customer=customer_instance,
    value="Premium Plan",
)
```

### 2.2 工具驱动变量

与工具关联，自动根据工具输出更新变量值：

```python
@p.tool
async def get_subscription_plan(context: ToolContext) -> ToolResult:
    return ToolResult(await get_plan_from_database(context.customer_id))

variable = await agent.create_variable(
    name="subscription_plan",
    description="客户的订阅计划类型",
    tool=get_subscription_plan,
)
```

## 三、配置文件格式

### 3.1 用户画像配置

**文件路径**: `agents/{agent_name}/00_agent_base/agent_user_profiles.json`

```json
{
  "agent_id": "medical_customer_service_agent_001",
  "remark": "医疗客服 Agent 专属用户画像配置",
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
        "tags": ["price_sensitive", "budget_conscious"]
      },
      "custom_variables": {
        "price_sensitivity_score": 0.8,
        "coupon_usage_rate": 0.65
      }
    }
  ]
}
```

## 四、核心字段说明

### 4.1 变量定义字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | ✅ | 变量名称 |
| `description` | string | ✅ | 变量描述 |
| `tool` | function | ❌ | 关联的工具函数 |
| `freshness_rules` | string | ❌ | 刷新规则（cron 表达式） |

### 4.2 用户分群字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `segment_id` | string | ✅ | 分群唯一标识 |
| `segment_name` | string | ✅ | 分群名称 |
| `description` | string | ✅ | 分群描述 |
| `definition.tags` | array | ✅ | 用于识别该分群的标签 |
| `definition.metadata_rules` | object | ❌ | 基于元数据的规则 |
| `custom_variables` | object | ❌ | 该分群的自定义变量 |

## 五、变量值设置方式

### 5.1 为单个客户设置

```python
await variable.set_value_for_customer(
    customer=customer_instance,
    value="Premium Plan",
)
```

### 5.2 为客户群体设置

```python
await variable.set_value_for_tag(
    tag="vip",
    value="Premium Plan",
)
```

### 5.3 设置默认值

```python
await variable.set_value_for_customer(
    customer=Customer.guest(),
    value="Free Plan",  # 未注册客户的默认值
)
```

## 六、刷新规则（Freshness Rules）

对于工具驱动变量，可以控制刷新频率：

```python
variable = await agent.create_variable(
    name="subscription_plan",
    description="客户的订阅计划类型",
    tool=get_subscription_plan,
    freshness_rules="0 * * * *",  # 每小时刷新
)
```

刷新规则使用 **cron 表达式**：
- `* * * * *` - 每分钟
- `0 * * * *` - 每小时
- `0 0 * * *` - 每天
- `0 0 * * 0` - 每周日

## 七、变量与 Guideline 结合

### 7.1 条件中使用变量

```python
await agent.create_guideline(
    condition="客户的 account_tier 是 'basic' 且询问即时国际转账",
    action="强调我们的同日国内转账免费，然后提及高级层级支持即时全球支付",
)
```

### 7.2 实际应用示例

**场景**: 数字银行支持 Agent

**变量定义**:
```python
account_tier = await agent.create_variable(
    name="account_tier",
    description="客户的账户等级",
    tool=get_account_tier,
)
```

**Guideline 定义**:
```python
await agent.create_guideline(
    condition="客户的 account_tier 是 'basic' AND 他们询问即时国际转账",
    action="强调我们的同日国内转账免费，然后提及高级层级支持即时全球支付且费用更低",
)
```

**交互示例**:

> **Mark（basic 层级）**: 我想给我在国外留学的女儿汇款
>
> **Agent**: 我可以帮您使用我们的标准国际转账服务今天完成汇款。另外，我们的高级账户可以即时完成国际转账且费用更低，您想了解更多吗？

## 八、用户画像设计

### 8.1 典型画像结构

```json
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
    "我需要最私密的就诊环境"
  ],
  "parlant_mapping": {
    "tags": ["vip", "time_sensitive", "premium_service"],
    "variables": ["response_time_preference", "privacy_level"],
    "journeys": ["vip_fast_track_booking"],
    "guidelines": ["skip_price_discussion", "offer_premium_options"]
  }
}
```

### 8.2 画像字段说明

| 字段 | 说明 |
|------|------|
| `persona_id` | 画像唯一标识 |
| `persona_name` | 画像名称（拟人化） |
| `segment_id` | 所属分群 ID |
| `demographics` | 人口统计学特征 |
| `goals` | 用户核心目标 |
| `pain_points` | 用户痛点 |
| `behavior_patterns` | 典型行为模式 |
| `typical_dialogues` | 典型对话示例 |
| `parlant_mapping` | 与 Parlant 元素的映射关系 |

## 九、Parlant 中的应用方式

### 9.1 完整应用流程

```
1. Tags + Variables → 客户细分识别
2. Observations → 基于代码的 matcher 检查客户标签
3. Guidelines → 群体特定指南激活
4. Journeys → 个性化旅程引导
5. Tools → 动态计算用户变量值
6. Canned Responses → 预设分群专属话术
```

### 9.2 代码实现示例

```python
# 1. 定义用户分群
user_profiles = {
    "user_segments": [
        {
            "segment_id": "vip_customers",
            "definition": {"tags": ["vip"]}
        }
    ]
}

# 2. 使用 Observation 检查客户标签
async def is_vip_matcher(
    ctx: GuidelineMatchingContext,
    guideline: Guideline
) -> GuidelineMatch:
    matched = vip_tag.id in Customer.current.tags
    return GuidelineMatch(
        id=guideline.id,
        matched=matched,
        rationale="Customer has VIP tag" if matched else "No VIP tag"
    )

# 3. 创建仅对特定群体激活的指南
vip_observation = await agent.create_observation(matcher=is_vip_matcher)
vip_guideline = await agent.create_guideline(
    condition="客户询问价格",
    action="提供 VIP 专属折扣",
    dependencies=[vip_observation]
)
```

## 十、最佳实践

### 10.1 何时需要配置用户画像

- ✅ **多客户群体服务场景**: 同时服务 VIP、普通、特殊群体客户
- ✅ **差异化服务策略**: 不同客户群体需要不同的服务流程、话术、优惠策略
- ✅ **个性化体验需求**: 需要根据客户特征提供定制化推荐、专属旅程
- ✅ **精细化运营**: 需要追踪不同客户群体的行为模式、转化率、满意度

### 10.2 用户分群设计原则

- **基于可识别的特征**: 使用 Tags 和 Metadata 进行明确区分
- **行为模式清晰**: 每个分群应有明确的行为特征描述
- **专属指南具体**: 为每个分群设计特定的 Guidelines

### 10.3 画像设计技巧

- **拟人化命名**: 给画像起一个具体的名字
- **详细人口统计学特征**: 包含年龄、职业、收入等信息
- **典型对话示例**: 提供 3-5 个该画像的典型对话
- **映射到 Parlant 元素**: 明确指定对应的 Tags、Variables、Journeys、Guidelines

## 十一、注意事项

1. **变量值验证**: 确保变量值符合预期格式
2. **刷新频率**: 合理设置工具驱动变量的刷新频率
3. **默认值**: 为未注册或未知客户提供合理的默认值
4. **隐私合规**: 确保变量数据的使用符合隐私法规
5. **性能考虑**: 避免过于频繁的工具调用

## 十二、相关文档

- [Guideline（指南）说明](./guideline.md)
- [Observation（观测）说明](./observation.md)
- [Tools（工具）说明](./tools.md)
- [Glossary（术语表）说明](./glossary.md)
