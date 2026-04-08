# Glossary（术语表）概念说明

## 一、概念定义

Glossary（术语表）是 Parlant 框架中用于定义 Agent **领域专用词汇**的机制。它就像 Agent 的专业词典，包含特定业务或服务上下文的术语集合。

### 核心作用

1. **帮助 Agent 理解用户**: 当用户使用特定术语或同义词时，Agent 能准确理解其含义
2. **帮助 Agent 解释规则**: Agent 能正确理解 Guideline 中使用的术语，准确执行规则

## 二、术语结构

每个术语条目包含三个组成部分：

| 组成部分 | 说明 |
|---------|------|
| **Term（术语）** | 被定义的词或短语 |
| **Description（描述）** | 该术语在特定上下文中的含义 |
| **Synonyms（同义词）** | 用户可能使用的替代表述方式 |

## 三、配置文件格式

### 3.1 目录位置

**文件路径**: `agents/{agent_name}/00_agent_base/glossary/`

```
00_agent_base/
└── glossary/
    ├── core_terms.json        # 核心术语
    ├── medical_terms.json     # 医疗领域术语
    └── industry_terms.json    # 行业术语
```

### 3.2 配置示例

```json
{
  "agent_id": "medical_customer_service_agent_001",
  "remark": "医疗客服 Agent 专属领域术语，确保 Agent 精准理解医疗相关表述",
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

## 四、核心字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `term_id` | string | ✅ | 术语唯一标识 |
| `name` | string | ✅ | 术语名称 |
| `description` | string | ✅ | 术语描述，定义其在特定上下文中的含义 |
| `synonyms` | array | ❌ | 同义词列表，用户可能使用的替代表述 |
| `language` | string | ❌ | 语言代码，如 `zh-CN`、`en-US` |

## 五、使用场景

### 5.1 场景一：用户理解

当用户说："我想挂个专家门诊"

Agent 通过术语表理解：
- "专家门诊" 是 "专家号" 的同义词
- "专家号" 是副主任医师及以上职称的医生出诊的号源

### 5.2 场景二：规则解释

定义规则：
```json
{
  "condition": "用户询问 Ocean View 房间",
  "action": "解释 Sunrise Package 的优惠"
}
```

定义术语：
```json
{
  "name": "Ocean View",
  "description": "位于 15-20 层面向大西洋的优质房间",
  "synonyms": ["海景房", "海边房间", "海滩景观"]
}
```

当用户问："你们有什么面向大西洋的房间吗？"

Agent 通过术语表理解：
- "面向大西洋的房间" 对应 "Ocean View"
- 规则条件满足，执行解释 Sunrise Package 的动作

## 六、Glossary vs Guidelines vs Agent Description

| 组件 | 作用 | 示例 | 数量限制 |
|------|------|------|----------|
| **Glossary** | 教会 Agent "事物是什么" | "Club Member 是入住超过 5 次的客人" | 无限制 |
| **Guidelines** | 教会 Agent "在场景中如何行动" | "与 Club Member 对话时，确认其会员状态" | 无限制 |
| **Agent Description** | 提供整体上下文和个性 | "你是 Boogie Nights 酒店的热心预订助手" | 单一固定 |

**类比理解**:
- Glossary 构建 Agent 的**词汇库**
- Guidelines 塑造 Agent 的**行为模式**
- Agent Description 设定 Agent 的**角色定位**

## 七、Glossary vs Tools

| 特性 | Glossary | Tools |
|------|----------|-------|
| **数据类型** | 静态知识 | 动态数据访问 |
| **用途** | 定义概念含义 | 查询实时数据 |
| **示例** | "Club Member 是入住超过 5 次的客人" | `check_member_status(user_id)` |

### 示例对比

**Glossary Term**:
```json
{
  "name": "Club Member",
  "description": "入住超过 5 次的客人",
  "synonyms": ["忠诚客户", "老客户"]
}
```

**Tool**:
```python
@p.tool
async def check_member_status(context: ToolContext, user_id: str) -> ToolResult:
    return ToolResult(await db.get_member_info(user_id))
```

**区别**:
- Glossary 提供 Club Member 的**定义**
- Tool 提供 Club Member 的**实时状态查询**

## 八、最佳实践

### 8.1 术语定义原则

**DON'T** - 定义过于宽泛：
```json
{
  "name": "VIP",
  "description": "重要客户"
}
```

**DO** - 定义具体明确：
```json
{
  "name": "VIP",
  "description": "年度消费超过 10000 元或订阅企业版套餐的客户，享受优先服务和专属折扣",
  "synonyms": ["贵宾", "VIP客户", "高级会员"]
}
```

### 8.2 同义词设计

- 覆盖用户常用的各种表述方式
- 包含口语化表达和书面语表达
- 考虑不同地区/文化的表述差异

### 8.3 术语分类

建议按业务领域分类存储：
```
glossary/
├── core_terms.json        # 核心业务术语
├── product_terms.json     # 产品相关术语
├── service_terms.json     # 服务相关术语
└── industry_terms.json    # 行业专业术语
```

## 九、注意事项

1. **避免重复定义**: 同一术语不要在多个文件中重复定义
2. **保持一致性**: 术语描述应与业务文档保持一致
3. **及时更新**: 业务变更时同步更新术语表
4. **同义词覆盖**: 确保同义词列表覆盖用户常见表述
5. **语言标注**: 多语言场景下标注语言代码

## 十、相关文档

- [Guideline（指南）说明](./guideline.md)
- [Tools（工具）说明](./tools.md)
- [Variable（变量）说明](./variable.md)
