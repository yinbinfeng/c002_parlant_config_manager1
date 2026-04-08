# Mining Agents MVP 使用指南

## 概述

Mining Agents MVP 版本实现了基于 AgentScope 框架的多 Agent 协作系统的基础框架，包括：

- ✅ 工具服务层（DeepResearchAgent 封装、JSON 校验）
- ✅ 核心管理器（StepManager、AgentOrchestrator）
- ✅ Step 1 Agent（RequirementAnalystAgent - 需求分析）
- ✅ Mock 测试支持

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

**必需依赖**：
- `agentscope>=1.0.0` - AgentScope 框架
- `json-repair>=0.25.0` - JSON 修复和校验
- `pyyaml>=6.0` - YAML 配置解析

### 2. 运行 Step 1（Mock 模式）

```bash
cd E:\cursorworkspace\c002_parlant_config_manager1

python -m mining_agents.main \
  --business-desc "电商客服 Agent，处理订单查询和退换货" \
  --mock-mode
```

**输出示例**：
```
🚀 初始化 Mining Agents 系统...
ℹ️  使用 Mock 模式（测试用）
📋 执行业务描述：电商客服 Agent，处理订单查询和退换货...
🔧 执行步骤：1 → 1

✅ Step 1 完成！问题清单已保存到：
   e:\...\output\step1\step1_clarification_questions.md

下一步操作：
  1. 查看并回答问题清单中的问题
  2. 继续执行后续步骤（待实现）
```

### 3. 查看生成的问题清单

打开 `output/step1/step1_clarification_questions.md` 文件，您将看到类似以下内容：

```markdown
# Step 1: 需求澄清问题清单

感谢您使用 Mining Agents 系统！请回答以下问题以帮助我们更准确地生成 Parlant Agent 配置。

---

### 🔴 Q1: 您的客服 Agent 主要服务于哪些客户群体？（如：个人消费者、企业客户、混合）

**类别**: `target_audience`

**为什么问这个问题**: 明确目标用户群体有助于设计合适的对话流程和话术风格

**您的回答**:
```
（请填写您的回答）
```

---
```

## 命令行参数说明

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--business-desc` | `-b` | **必需**，业务描述文本 | - |
| `--config` | `-c` | 配置文件路径 | `config/system_config.yaml` |
| `--start-step` | - | 起始步骤（1-8） | `1` |
| `--end-step` | - | 结束步骤（1-8） | `8` |
| `--mock-mode` | - | 使用 Mock 模式（不实际调用 LLM） | `True` |
| `--real-mode` | - | 使用真实模式（需要 API Key） | `False` |
| `--force-rerun` | - | 强制重跑已完成的步骤 | `False` |
| `--verbose` | `-v` | 启用详细日志 | `False` |
| `--max-parallel` | - | 最大并发 Agent 数 | `4` |

## 运行模式

### Mock 模式（推荐用于测试）

```bash
python -m mining_agents.main -b "业务描述" --mock-mode
```

**特点**：
- ✅ 不需要 API Key
- ✅ 快速响应
- ✅ 适合开发和测试
- ❌ 不生成真实的 Deep Research 报告

### 真实模式（生产环境）

```bash
export DASHSCOPE_API_KEY="your_key_here"
export TAVILY_API_KEY="your_key_here"

python -m mining_agents.main -b "业务描述" --real-mode
```

**特点**：
- ✅ 生成真实的研究报告
- ✅ 更接近生产环境
- ❌ 需要有效的 API Key
- ❌ 响应较慢

## 运行测试

```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 运行所有测试
pytest tests/test_mvp.py -v

# 运行特定测试
pytest tests/test_mvp.py::TestJsonValidator -v

# 运行覆盖率测试
pytest tests/test_mvp.py --cov=mining_agents --cov-report=html
```

## 项目结构

```
mining_agents/
├── src/mining_agents/           # 源代码
│   ├── agents/                  # Agent 实现
│   │   └── requirement_analyst_agent.py  # 需求分析 Agent
│   ├── managers/                # 管理器
│   │   ├── step_manager.py      # 步骤管理器
│   │   └── agent_orchestrator.py # Agent 编排器
│   ├── tools/                   # 工具
│   │   ├── deep_research.py     # Deep Research 工具
│   │   └── json_validator.py    # JSON 校验工具
│   ├── utils/                   # 工具函数
│   │   ├── logger.py            # 日志
│   │   └── file_utils.py        # 文件操作
│   ├── cli.py                   # 命令行接口
│   └── main.py                  # 主入口
├── tests/                       # 测试
│   └── test_mvp.py              # MVP 测试
├── output/                      # 输出目录
│   └── step1/                   # Step 1 输出
├── config/                      # 配置
│   └── system_config.yaml       # 系统配置
└── docs/plans/                  # 文档
    └── 2026-03-20-mining-agents-mvp-design.md  # 设计文档
```

## 下一步开发计划

当前 MVP 版本仅实现了 Step 1 的完整流程。后续将实现：

### Phase 2: Step 2-3
- Multi-Agent Debate Framework（多 Agent 辩论）
- CoordinatorAgent（任务分解）

### Phase 3: Step 4-5
- RuleEngineerAgent（全局规则制定）
- EdgeCaseAnalysisAgent（边缘情况分析）
- UserPortraitMinerAgent（用户画像挖掘）

### Phase 4: Step 6-8
- Data Extraction Agent（Excel 对话解析）
- QAModeratorAgent（质量检查）
- ConfigAssemblerAgent（配置包生成）

## 常见问题

### Q: Mock 模式和真实模式有什么区别？

**A**: 
- **Mock 模式**使用预设的示例数据，不实际调用 LLM API，适合快速测试和开发。
- **真实模式**会调用 DashScope 和 Tavily API，生成真实的研究报告，但需要有效的 API Key。

### Q: 如何查看详细的执行日志？

**A**: 添加 `--verbose` 或 `-v` 参数：
```bash
python -m mining_agents.main -b "业务描述" -v
```

### Q: 如何跳过已完成的步骤？

**A**: 系统会自动检测已完成的步骤并跳过。如果需要强制重跑，使用 `--force-rerun` 参数：
```bash
python -m mining_agents.main -b "业务描述" --force-rerun
```

### Q: 输出文件在哪里？

**A**: 默认在 `./output/` 目录下，每个步骤有独立的子目录：
- Step 1: `output/step1/step1_clarification_questions.md`
- Step 2: `output/step2/...`（待实现）

### Q: 如何修改配置？

**A**: 编辑 `config/system_config.yaml` 文件，或创建自定义配置文件并使用 `--config` 参数指定：
```bash
python -m mining_agents.main -b "业务描述" --config my_config.yaml
```

## 技术支持

如有问题，请查阅：
- 设计文档：`docs/plans/2026-03-20-mining-agents-mvp-design.md`
- AgentScope 官方文档：`agentscope_docs/`
