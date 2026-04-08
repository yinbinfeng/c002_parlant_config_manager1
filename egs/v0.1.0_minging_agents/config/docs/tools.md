# Tools（工具）概念说明

## 一、概念定义

Tools（工具）是 Parlant 框架中用于实现**业务逻辑执行**的机制。它允许 Agent 调用外部函数来执行特定操作，如查询数据库、调用 API、执行业务逻辑等。

### 核心设计理念

Parlant 采用**引导式工具调用**方法，工具始终与特定的 Guideline 关联。工具只有在关联的 Guideline 被匹配时才会执行，这创建了一个清晰的意图链：Guideline 决定何时、为何使用工具，而不是依赖 LLM 的判断。

### 业务逻辑与表现分离

- **业务逻辑**: 在工具中用代码实现，开发者完全控制
- **表现层**: 用户界面行为由 Guideline 控制，业务专家定义

## 二、工具结构

### 2.1 基本结构

```python
import parlant_sdk as p

@p.tool
async def tool_name(context: p.ToolContext, param1: str, param2: int) -> p.ToolResult:
    """工具描述（多行）
    Agent 可读取此描述，帮助决定是否/何时运行此工具
    """
    # 业务逻辑
    return p.ToolResult(data=result)
```

### 2.2 配置文件格式

**目录结构**:
```
03_tools/
├── tool_get_upcoming_slots/
│   ├── tool_meta.json      # 工具元信息
│   └── tool_impl.py        # 工具实现代码
└── tool_schedule_appt/
    ├── tool_meta.json
    └── tool_impl.py
```

**tool_meta.json 示例**:
```json
{
  "tool_id": "medical_tool_get_upcoming_slots",
  "tool_name": "get_upcoming_slots",
  "tool_description": "查询指定科室未来 7 天可预约的医生、职称、可预约时段",
  "timeout": 3,
  "implementation_file": "./tool_impl.py",
  "use_scenarios": [
    "用户进入预约挂号 SOP，选择科室后",
    "用户询问某科室的可预约医生"
  ],
  "input_params": [
    {
      "param_name": "department",
      "param_type": "string",
      "required": true,
      "default": "",
      "description": "科室名称，如'内科''外科'"
    },
    {
      "param_name": "doctor_name",
      "param_type": "string",
      "required": false,
      "default": "",
      "description": "医生姓名，用于精准筛选"
    }
  ],
  "output_params": [
    {
      "field_name": "doctors",
      "field_type": "array",
      "description": "可预约医生数组"
    }
  ]
}
```

**tool_impl.py 示例**:
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
    医疗客服 Agent 专属：门诊可预约时间查询工具
    对应元信息 ID：medical_tool_get_upcoming_slots
    """
    doctors = await query_available_doctors(department, doctor_name)
    
    return ToolResult(
        data=doctors,
        guidelines=[
            {"action": "优先展示职称更高、可预约时段更多的医生", "priority": 4}
        ]
    )
```

## 三、ToolResult 属性

ToolResult 包含五个属性：

| 属性 | 说明 | 必填 |
|------|------|------|
| `data` | 工具的主要输出，JSON 可序列化 | ✅ |
| `metadata` | 附加信息，Agent 不可见，供前端使用 | ❌ |
| `control` | 控制指令，如会话模式、生命周期 | ❌ |
| `canned_responses` | 供考虑的模板响应 | ❌ |
| `canned_response_fields` | 模板响应替换字段 | ❌ |

### 3.1 Data（数据）

主要输出，Agent 用于理解交互历史：

```python
return ToolResult(data={
    "doctors": [
        {"name": "张建国", "title": "主任医师", "slots": [...]}
    ]
})
```

### 3.2 Metadata（元数据）

附加信息，供前端使用：

```python
return ToolResult(
    data="利润率为 20%",
    metadata={
        "generated_chart_url": "https://example.com/chart.png",
        "sources": [{"url": "...", "title": "..."}]
    }
)
```

### 3.3 Control（控制）

控制指令：

```python
# 转人工：暂停 Agent 自动响应
return ToolResult(
    data="正在转接人工客服",
    control={"mode": "manual"}
)

# 临时结果：仅在当前响应中可用
return ToolResult(
    data="查询出错",
    control={"lifespan": "response"}
)
```

## 四、工具与 Guideline 关联

### 4.1 基本关联

```python
await agent.create_guideline(
    condition="用户询问最新款笔记本电脑",
    action="首先推荐最新的 Mac 笔记本",
    tools=[find_products_in_stock],
)
```

### 4.2 简化关联

当工具本身隐含动作时：

```python
await agent.attach_tool(
    condition="用户需要查询产品库存",
    tool=find_products_in_stock
)
```

## 五、ToolContext 上下文

ToolContext 提供上下文信息和工具：

| 属性/方法 | 说明 |
|-----------|------|
| `agent_id` | 调用工具的 Agent ID |
| `customer_id` | 当前交互的客户 ID |
| `session_id` | 当前会话 ID |
| `emit_message(message)` | 向客户发送消息（长任务进度报告） |
| `emit_status(status)` | 更新会话状态 |

### 访问服务器对象

```python
@p.tool
async def my_tool(context: ToolContext) -> ToolResult:
    server = ToolContextAccessor(context).server
    
    agent = await server.get_agent(id=context.agent_id)
    customer = await server.get_customer(id=context.customer_id)
    
    return ToolResult(...)
```

## 六、参数选项（ToolParameterOptions）

### 6.1 基本用法

```python
from typing import Annotated

@p.tool
async def transfer_money(
    context: ToolContext,
    amount: Annotated[float, ToolParameterOptions(
        source="customer",  # 只有客户能提供
    )],
    recipient: Annotated[str, ToolParameterOptions(
        source="customer",
    )]
) -> ToolResult:
    ...
```

### 6.2 参数选项字段

| 字段 | 说明 |
|------|------|
| `hidden` | 隐藏参数，不向客户暴露 |
| `precedence` | 分组优先级，控制提示顺序 |
| `source` | 参数来源：`customer`/`context`/`any` |
| `description` | 参数描述，帮助 Agent 正确提取 |
| `significance` | 客户可见的参数重要性说明 |
| `examples` | 示例值，帮助格式化 |
| `adapter` | 类型转换函数 |
| `choice_provider` | 动态选项提供函数 |

## 七、参数值约束

### 7.1 枚举参数

```python
class ProductCategory(enum.Enum):
    LAPTOPS = "laptops"
    PERIPHERALS = "peripherals"
    MONITORS = "monitors"

@p.tool
async def get_products(
    context: ToolContext,
    category: ProductCategory,
) -> ToolResult:
    ...
```

### 7.2 动态选项

```python
async def get_last_order_ids(context: ToolContext) -> list[str]:
    return await load_last_order_ids(customer_id=context.customer_id)

@p.tool
async def load_order(
    context: ToolContext,
    order_id: Annotated[Optional[str], ToolParameterOptions(
        choice_provider=get_last_order_ids,
    )],
) -> ToolResult:
    ...
```

### 7.3 Pydantic 模型

```python
from pydantic import BaseModel

class ProductSearchQuery(BaseModel):
    category: str
    price_range: tuple[float, float]

@p.tool
async def search_products(
    context: ToolContext,
    query: ProductSearchQuery,
) -> ToolResult:
    ...
```

## 八、Guideline 重新评估

工具结果可能影响其他 Guideline 的激活：

```python
# 工具调用后重新评估此 Guideline
await guideline.reevaluate_after(my_tool)
```

**示例场景**：
- 用户请求转账
- 工具查询余额返回低于 $500
- 低余额 Guideline 激活，提示用户可能产生透支费用

## 九、最佳实践

### 9.1 业务逻辑放在工具中

**DON'T** - 在 Guideline 中写复杂逻辑：
```json
{
  "action": "如果用户提到运动，检查购买历史。如果买过跑步装备，推荐高端鞋。如果是新用户，推荐入门套装。"
}
```

**DO** - 逻辑放在工具中：
```json
{
  "action": "提供个性化推荐",
  "tools": ["get_personalized_recommendations"]
}
```

### 9.2 安全数据访问

**DON'T** - 让 LLM 识别用户：
```python
@p.tool
async def get_transactions(context: ToolContext, user_name: str) -> ToolResult:
    # 不安全：依赖 LLM 识别用户
    ...
```

**DO** - 使用 ToolContext：
```python
@p.tool
async def get_transactions(context: ToolContext) -> ToolResult:
    # 安全：使用注册的客户 ID
    transactions = await DB.get_transactions(context.customer_id)
    return ToolResult(transactions)
```

### 9.3 工具结果生命周期

- **session（默认）**: 结果保存到会话，后续可用
- **response**: 结果仅在当前响应中可用

```python
# 错误信息不需要保存
return ToolResult(
    data="查询出错",
    control={"lifespan": "response"}
)
```

## 十、配置文件字段说明

### tool_meta.json 字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `tool_id` | string | ✅ | 工具唯一标识 |
| `tool_name` | string | ✅ | 工具函数名 |
| `tool_description` | string | ✅ | 工具描述 |
| `timeout` | integer | ❌ | 超时时间（秒） |
| `implementation_file` | string | ✅ | 实现文件路径 |
| `use_scenarios` | array | ❌ | 使用场景描述 |
| `input_params` | array | ✅ | 输入参数列表 |
| `output_params` | array | ❌ | 输出参数列表 |

## 十一、注意事项

1. **工具状态后必须是对话状态**: 在 Journey 中，工具状态后必须跟随对话状态
2. **避免顺序工具状态**: 不要使用连续的工具状态，合并为一个工具状态
3. **参数验证**: 使用枚举、Pydantic 模型确保参数有效性
4. **超时设置**: 为可能耗时的操作设置合理的超时时间
5. **错误处理**: 在工具中妥善处理异常，返回有意义的错误信息

## 十二、相关文档

- [Guideline（指南）说明](./guideline.md)
- [Journey（旅程）说明](./journey.md)
- [Variable（变量）说明](./variable.md)
