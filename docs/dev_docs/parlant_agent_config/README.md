# Parlant Agent 配置管理项目

## 项目概述

本项目实现了基于 Parlant 框架的多 Agent 配置管理系统，支持多个业务线 Agent 的完全隔离配置管理。

## 目录结构

```
parlant_agent_config/
├── agents/                         # 所有独立 Agent 的存放目录
│   ├── medical_customer_service_agent/  # 医疗客服 Agent
│   │   ├── 00_agent_base/              # Agent 基础配置
│   │   ├── 01_agent_rules/             # Agent 全局规则
│   │   ├── 02_journeys/                # SOP 业务流程
│   │   └── 03_tools/                   # Agent 专属工具
│   └── airline_customer_service_agent/  # 航空客服 Agent
│       ├── 00_agent_base/
│       ├── 01_agent_rules/
│       ├── 02_journeys/
│       └── 03_tools/
└── automation/                     # 自动化构建脚本
    └── build_agent.py             # Agent 配置构建工具
```

## 快速开始

### 1. 构建单个 Agent

```bash
cd parlant_agent_config/automation
python build_agent.py --agent medical_customer_service_agent
```

### 2. 构建所有 Agent

```bash
cd parlant_agent_config/automation
python build_agent.py --all
```

### 3. 查看帮助

```bash
python build_agent.py --help
```

## Agent 配置说明

### 00_agent_base/ - Agent 基础配置

- `agent_metadata.json`: Agent 元信息（ID、名称、描述、端口等）
- `agent_observability.json`: 可观测性配置（日志、追踪等）
- `glossary/`: 领域术语表（医疗术语、航空术语等）

### 01_agent_rules/ - Agent 全局规则

- `agent_observations.json`: 全局观测条件（用户情绪、转人工需求等）
- `agent_canned_responses.json`: 全局模板话术（问候、安抚、拒绝等）
- `agent_guidelines.json`: 全局行为规则（含排除/依赖关系）

### 02_journeys/ - SOP 业务流程

每个 SOP 一个独立子文件夹，包含：
- `sop.json`: SOP 核心流程（状态机、转移条件）
- `sop_observations.json`: SOP 专属观测条件
- `sop_guidelines.json`: SOP 专属行为规则

示例 SOP：
- 医疗：预约挂号全流程
- 航空：预订机票全流程

### 03_tools/ - Agent 专属工具

每个工具一个独立子文件夹，包含：
- `tool_meta.json`: 工具元信息（输入输出参数定义）
- `tool_impl.py`: 工具实现代码（Python async 函数）

示例工具：
- 医疗：门诊查询、挂号提交
- 航空：航班查询、机票预订

## 配置文件规范

### 1. Guideline 排除/依赖关系

```json
{
  "guideline_id": "medical_soothe_001",
  "exclusions": ["medical_greet_001"],  // 排他关系：触发此规则时不触发被排除的规则
  "dependencies": ["medical_obs_user_angry_001"]  // 依赖关系：依赖此观测条件作为触发前提
}
```

### 2. SOP 状态机设计

```json
{
  "state_type": "chat",  // 对话状态
  "transitions": [
    {
      "target_state_id": "state_001",
      "condition": "用户已明确选择具体科室"
    }
  ]
}
```

```json
{
  "state_type": "tool",  // 工具调用状态
  "bind_tool_id": "medical_tool_get_upcoming_slots",
  "transitions": [
    {
      "target_state_id": "state_002",
      "condition": "工具返回可预约医生与时段信息后"
    }
  ]
}
```

### 3. 工具定义规范

```json
{
  "tool_id": "medical_tool_get_upcoming_slots",
  "input_params": [
    {
      "param_name": "department",
      "param_type": "string",
      "required": true,
      "description": "科室名称"
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

## 多业务线隔离特性

### ✅ 完全隔离

- 每个 Agent 拥有独立的文件夹，配置互不干扰
- 不同业务线的术语、规则、SOP、工具完全独立
- 无共享配置文件，避免跨 Agent 影响

### ✅ 内聚设计

- 单个 Agent 的所有配置都在其文件夹内
- 修改单个文件仅影响对应功能
- 易于扩展新业务线

### ✅ 合规适配

- 支持不同业务线的严格合规要求
- 数据、配置、逻辑物理隔离
- 适合金融、医疗等强监管行业

## 扩展新 Agent

### 步骤 1: 复制目录结构

```bash
cp -r medical_customer_service_agent new_business_agent
```

### 步骤 2: 修改配置文件

- 更新 `agent_metadata.json` 中的 agent_id、agent_name
- 替换 `glossary/` 中的领域术语
- 调整 `01_agent_rules/` 中的全局规则和话术
- 设计 `02_journeys/` 中的业务流程
- 实现 `03_tools/` 中的专属工具

### 步骤 3: 运行构建脚本

```bash
python build_agent.py --agent new_business_agent
```

## 技术栈

- **框架**: Parlant (Agent 开发框架)
- **语言**: Python 3.8+
- **配置格式**: JSON
- **工具实现**: Python async/await

## 最佳实践

### 1. 命名规范

- `agent_id`: `{business}_customer_service_agent_{version}`
- `guideline_id`: `{business}_{function}_{seq}`
- `tool_id`: `{business}_tool_{function}`
- `sop_id`: `{business_action}_{seq}`

### 2. 优先级设置

- 全局问候：priority=3
- SOP 引导：priority=4-6
- 情绪安抚：priority=8
- 转人工：priority=10
- 合规红线：priority=12

### 3. 状态机设计

- 每个 SOP 控制在 5-8 个状态
- 使用 `is_end_state: true` 标记终止状态
- 提供回退路径（如修改信息返回上一步）

### 4. 工具超时设置

- 简单查询：timeout=3s
- 复杂操作：timeout=5s
- 外部接口：根据实际响应时间调整

## 常见问题

### Q1: 如何调试 Agent 配置？

A: 运行构建脚本时会输出详细的配置加载信息和验证结果。

### Q2: 如何实现 Agent 之间的配置共享？

A: 本设计采用完全隔离模式，不建议共享。如需复用，可通过代码生成或模板复制。

### Q3: 如何测试工具实现？

A: 在 `tool_impl.py` 中编写单元测试，或使用 Parlant 框架提供的测试工具。

## 许可证

MIT License

## 联系方式

如有问题，请联系项目维护者。
