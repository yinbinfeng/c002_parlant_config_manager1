# 嵌套 Journey 使用指南

在 Parlant 中，**Journey 嵌套**允许您在主 journey 中调用子 journey，将复杂的对话流程分解为模块化、可复用的组件。

## 核心概念

### 什么是嵌套 Journey？

嵌套 Journey（也称为子 Journey）允许一个 journey 在执行过程中调用另一个 journey。当状态转换到子 journey 时，父 journey 会暂停，等待子 journey 执行完成后自动恢复。

### 工作原理

1. **进入子 journey**：通过 `transition_to()` 方法的 `journey` 参数触发
2. **执行子 journey**：父 journey 暂停，子 journey 开始执行
3. **自动返回**：子 journey 到达叶子节点（无后续转换的状态）时，自动返回父 journey
4. **继续执行**：通过 `.target` 访问子 journey 完成后的下一个状态

## 基本用法

### 简单示例

```python
import parlant.sdk as p

async with p.Server() as server:
    agent = await server.create_agent(
        name="Customer Service Agent",
        description="Handles customer support requests",
    )
    
    # 创建技术支持子 journey
    tech_support = await agent.create_journey(
        title="Technical Support",
        conditions=[],
        description="Handle technical support requests",
    )
    
    await tech_support.initial_state.transition_to(
        chat_state="Greet customer and ask for technical issue details",
    )
    
    # 创建主客户服务 journey
    main_journey = await agent.create_journey(
        title="Customer Service",
        conditions=["Customer needs support"],
        description="Route customers to appropriate support channels",
    )
    
    # 带条件地转换到子 journey
    await main_journey.initial_state.transition_to(
        condition="if customer needs technical support",
        journey=tech_support,  # 调用子 journey
    )
```

## 高级用法

### 条件路由到多个子 Journey

根据用户输入动态路由到不同的子 journey：

```python
# 创建多个子 journey
tech_support = await agent.create_journey(
    title="Technical Support",
    conditions=[],
    description="Handle technical issues",
)

billing_support = await agent.create_journey(
    title="Billing Support",
    conditions=[],
    description="Handle billing inquiries",
)

# 主 journey - 初始询问
service_inquiry = await main_journey.initial_state.transition_to(
    chat_state="What type of service do you need: technical support or billing help?",
)

# 根据客户回答路由到不同子 journey
await service_inquiry.target.transition_to(
    condition="if customer needs technical support",
    journey=tech_support,
)

await service_inquiry.target.transition_to(
    condition="if customer needs billing help",
    journey=billing_support,
)
```

### 链式调用子 Journey

按顺序链接多个子 journey：

```python
# Journey 1: 收集姓名
journey1 = await agent.create_journey(
    title="Name Collection",
    conditions=[],
    description="Collect customer name",
)
await journey1.initial_state.transition_to(
    chat_state="Please tell me your name.",
)

# Journey 2: 收集偏好
journey2 = await agent.create_journey(
    title="Preference Collection",
    conditions=[],
    description="Collect preferences",
)
await journey2.initial_state.transition_to(
    chat_state="What's your favorite color?",
)

# Journey 3: 完成
journey3 = await agent.create_journey(
    title="Completion",
    conditions=[],
    description="Finalize the process",
)
await journey3.initial_state.transition_to(
    chat_state="All done! Thank you.",
)

# 主 journey - 链式调用
main_journey = await agent.create_journey(
    title="Main Process",
    conditions=["Customer wants to start"],
    description="Complete multi-step process",
)

# 进入第一个子 journey
link1 = await main_journey.initial_state.transition_to(
    journey=journey1,
)

# journey1 完成后，自动进入 journey2
link2 = await link1.target.transition_to(
    journey=journey2,
)

# journey2 完成后，自动进入 journey3
link3 = await link2.target.transition_to(
    journey=journey3,
)
```

### 完整示例：客户支持路由系统

```python
import parlant.sdk as p
from parlant.core.tools import ToolContext, ToolResult

async def create_support_system(server: p.Server):
    agent = await server.create_agent(
        name="Multi-Support Agent",
        description="Routes to appropriate support channel",
        composition_mode=p.CompositionMode.STRICT,
    )
    
    # 预定义回复模板
    service_type_response = await server.create_canned_response(
        template="What type of service do you need: technical support or billing help?"
    )
    tech_greeting = await server.create_canned_response(
        template="Welcome to technical support! Please describe your issue."
    )
    billing_greeting = await server.create_canned_response(
        template="Welcome to billing support! How can I help with your account?"
    )
    
    # 技术支持工具
    @p.tool
    async def resolve_tech_issue(context: ToolContext, issue_description: str) -> p.ToolResult:
        return p.ToolResult(data={"status": "resolved", "solution": "Issue fixed"})
    
    # 账单支持工具
    @p.tool
    async def resolve_billing_issue(context: ToolContext, billing_question: str) -> p.ToolResult:
        return p.ToolResult(data={"status": "resolved", "account_updated": True})
    
    # 创建技术支持子 journey
    tech_support = await agent.create_journey(
        title="Technical Support",
        conditions=[],
        description="Handle technical support requests",
    )
    
    tech_greeting_state = await tech_support.initial_state.transition_to(
        chat_state="Greet customer and ask for technical issue details",
        canned_responses=[tech_greeting],
    )
    
    tech_resolution = await tech_greeting_state.target.transition_to(
        tool_instruction="Resolve the technical issue",
        tool_state=resolve_tech_issue,
    )
    
    await tech_resolution.target.transition_to(
        chat_state="Confirm technical issue resolution",
    )
    
    # 创建账单支持子 journey
    billing_support = await agent.create_journey(
        title="Billing Support",
        conditions=[],
        description="Handle billing and account inquiries",
    )
    
    billing_greeting_state = await billing_support.initial_state.transition_to(
        chat_state="Greet customer and ask for billing question",
        canned_responses=[billing_greeting],
    )
    
    billing_resolution = await billing_greeting_state.target.transition_to(
        tool_instruction="Resolve the billing issue",
        tool_state=resolve_billing_issue,
    )
    
    await billing_resolution.target.transition_to(
        chat_state="Confirm billing issue resolution",
    )
    
    # 创建主客户服务 journey
    main_journey = await agent.create_journey(
        title="Customer Service",
        conditions=["Customer needs support"],
        description="Route customers to appropriate support channels",
    )
    
    # 初始状态：询问需要什么服务
    service_inquiry = await main_journey.initial_state.transition_to(
        chat_state="Ask customer what type of service they need",
        canned_responses=[service_type_response],
    )
    
    # 条件路由到不同子 journey
    await service_inquiry.target.transition_to(
        condition="if customer needs technical support",
        journey=tech_support,
    )
    
    await service_inquiry.target.transition_to(
        condition="if customer needs billing help",
        journey=billing_support,
    )
    
    return main_journey
```

## 退出机制

### 自动退出（默认行为）

子 journey 在以下情况下会**自动退出**并返回父 journey：

- 到达**叶子节点**（没有 outgoing transitions 的状态）
- 引擎会自动创建到 merge fork 状态的转换

```python
# 子 journey 的最后一个状态
final_state = await some_state.transition_to(
    chat_state="Final message to customer",
)
# 没有后续转换 → 自动返回父 journey
```

### 显式退出

您也可以明确定义退出行为：

#### 1. 结束整个流程

```python
await some_state.transition_to(
    condition="process completed",
    state=p.END_JOURNEY,  # 完全结束所有流程
)
```

#### 2. 转到另一个子 journey

```python
await leaf_state.transition_to(
    condition="escalate to manager",
    journey=escalation_journey,  # 转到升级流程
)
```

#### 3. 返回父 journey 的特定状态

```python
# 在子 journey 中
await some_state.transition_to(
    condition="return to main flow",
    state=parent_journey_state,  # 返回父 journey 的某个状态
)
```

## 关键特性

### 1. 自动返回机制

当子 journey 完成时，控制权会自动返回到父 journey 的下一个可用状态（通过 `.target` 访问）。

```python
# 进入子 journey
transition = await parent_state.transition_to(
    journey=sub_journey,
)

# transition.target 是子 journey 完成后的状态（fork 状态）
next_state = transition.target
```

### 2. 模块化设计

子 journey 是自包含的，可以在多个父 journey 中复用：

```python
# 同一个子 journey 可以被多个父 journey 使用
await journey_a.initial_state.transition_to(
    journey=reusable_sub_journey,
)

await journey_b.initial_state.transition_to(
    journey=reusable_sub_journey,  # 相同的子 journey
)
```

### 3. 上下文保持

父 journey 的上下文在子 journey 执行期间会被保留：

- 父 journey 的已执行状态不会丢失
- 会话变量和记忆保持不变
- 子 journey 可以访问父 journey 的上下文信息

### 4. 深度嵌套

子 journey 本身也可以包含子 journey，实现多层嵌套：

```python
# 主 journey
main_journey → sub_journey_1 → sub_sub_journey
```

### 5. Fork 状态作为汇聚点

每个子 journey 都会创建一个 **fork 状态**，作为：
- **入口点**：从父 journey 进入子 journey
- **出口点**：子 journey 完成后返回父 journey

```python
# 内部实现：每个子 journey 都有一个关联的 fork 状态
metadata={"sub_journey_id": journey.id}
```

## 最佳实践

### ✅ 推荐做法

1. **保持子 journey 聚焦**
   - 每个子 journey 应该处理特定的任务或决策分支
   - 避免创建过于复杂的大型子 journey

2. **使用描述性标题**
   ```python
   # 好的命名
   "Technical Support - Level 1"
   "Billing - Refund Processing"
   "Onboarding - Account Setup"
   
   # 避免模糊命名
   "Support Journey 1"
   "Process Flow"
   ```

3. **利用条件路由**
   ```python
   # 清晰的条件定义
   await state.transition_to(
       condition="if customer reports technical issue",
       journey=tech_support,
   )
   ```

4. **设计可复用的子 journey**
   ```python
   # 通用验证流程
   verification_journey = await agent.create_journey(
       title="Identity Verification",
       description="Verify customer identity - reusable across all flows",
   )
   ```

### ❌ 避免的做法

1. **过度嵌套**
   - 避免超过 3 层的嵌套深度
   - 过深的嵌套会使调试变得困难

2. **循环依赖**
   ```python
   # 错误：A 调用 B，B 又调用 A
   journey_a → journey_b → journey_a  # 避免！
   ```

3. **隐式退出导致混淆**
   - 确保子 journey 的退出点是明确的
   - 在复杂场景中使用显式退出

## 实际应用场景

### 场景 1：多层客户支持

```
主旅程：客户支持
├─ 子旅程：技术支持
│  ├─ 初级诊断
│  └─ 高级故障排除
├─ 子旅程：账单支持
│  ├─ 付款问题
│  └─ 退款处理
└─ 子旅程：账户管理
   ├─ 密码重置
   └─ 信息更新
```

### 场景 2：用户引导流程

```
主旅程：新用户引导
├─ 子旅程：账户设置（顺序执行）
│  ├─ 基本信息收集
│  ├─ 邮箱验证
│  └─ 密码设置
├─ 子旅程：偏好配置
│  ├─ 通知设置
│  └─ 主题选择
└─ 子旅程：功能导览
   ├─ 核心功能介绍
   └─ 快捷操作教学
```

### 场景 3：故障诊断系统

```
主旅程：问题诊断
├─ 子旅程：初步评估
│  └─ 问题分类
├─ 子旅程：详细诊断（根据分类选择）
│  ├─ 网络问题诊断
│  ├─ 软件问题诊断
│  └─ 硬件问题诊断
└─ 子旅程：解决方案
   ├─ 自动修复
   └─ 人工支持转接
```

### 场景 4：多步骤表单处理

```
主旅程：贷款申请
├─ 子旅程：个人信息
│  ├─ 基本资料
│  └─ 联系方式
├─ 子旅程：财务信息
│  ├─ 收入证明
│  ├─ 资产状况
│  └─ 负债情况
├─ 子旅程：贷款详情
│  ├─ 贷款金额
│  ├─ 期限选择
│  └─ 还款方式
└─ 子旅程：文档上传
   ├─ 身份证明
   ├─ 收入证明
   └─ 其他材料
```

## 调试技巧

### 1. 可视化 Journey 结构

```bash
# 访问 journeys 页面查看结构
http://localhost:8800/journeys

# 获取 Mermaid 图表代码
http://localhost:8800/journeys/<JOURNEY_ID>/mermaid
```

将生成的 Mermaid 代码粘贴到 [Mermaid Live Editor](https://mermaid.live/) 进行可视化。

### 2. 检查子 Journey 元数据

```python
from parlant.core.journeys import JourneyStore

journey_store = container[JourneyStore]

# 读取 journey 节点
node = await journey_store.read_node(node_id)

# 检查是否属于子 journey
if "sub_journey_id" in node.metadata:
    print(f"This node belongs to sub-journey: {node.metadata['sub_journey_id']}")
```

### 3. 追踪执行流程

使用 OpenTelemetry 追踪：

```python
# 每个子 journey 的激活都会在 trace 中记录
# 查看 "journey.state.activate" 事件
# 注意 sub_journey_id 属性
```

## 常见问题

### Q: 子 journey 如何返回值给父 journey？

**A:** 通过上下文变量或共享状态：

```python
# 在子 journey 中设置变量
await context_variables.set_value(
    key="collected_data",
    value=data,
)

# 在父 journey 中读取
data = await context_variables.get_value(key="collected_data")
```

### Q: 可以让子 journey 并行执行吗？

**A:** 当前不支持并行执行。子 journey 按顺序执行，前一个完成后才会进入下一个。

### Q: 如何在子 journey 中使用父 journey 的工具？

**A:** 子 journey 可以访问所有已启用的工具，无需特殊配置：

```python
# 在父 journey 中启用工具
@p.tool
async def shared_tool(context: ToolContext) -> p.ToolResult:
    ...

# 该工具在所有子 journey 中都可用
```

### Q: 子 journey 的数量有限制吗？

**A:** 没有硬性限制，但建议：
- 单个父 journey 的子 journey 数量控制在 5-7 个以内
- 嵌套深度不超过 3 层
- 保持整体结构的清晰和可维护性

## 相关资源

- [Journeys 基础文档](docs/concepts/customization/journeys.md) - 了解 journey 的基本概念
- [Tools 文档](docs/concepts/customization/tools.md) - 学习如何在 journey 中使用工具
- [Canned Responses 文档](docs/concepts/customization/canned-responses.md) - 为 journey 添加预定义回复
- [Relationships 文档](docs/concepts/customization/relationships.md) - 管理 journey 之间的关系
