# 测试套件使用指南

## 📦 已创建的测试文件

### 核心测试文件

| 文件 | 类型 | 行数 | 描述 |
|------|------|------|------|
| `tests/test_single_agents.py` | 单元测试 | ~450 行 | 9 个 Agent 的独立功能测试 |
| `tests/test_end_to_end.py` | 集成测试 | ~500 行 | 完整 8 步流程的端到端测试 |
| `tests/test_data_generator.py` | 工具脚本 | ~300 行 | 测试数据生成器 |
| `tests/test_runner.py` | 工具脚本 | ~200 行 | 测试运行器和报告生成器 |
| `tests/conftest.py` | 配置文件 | ~350 行 | pytest fixtures 和配置 |
| `tests/README.md` | 文档 | ~400 行 | 详细测试文档 |
| `pytest.ini` | 配置文件 | - | pytest 配置 |
| `run_tests.bat` | 启动脚本 | - | Windows 快速启动器 |

## 🚀 快速开始

### 方法 1: 双击运行（Windows，推荐）

```bash
双击 run_tests.bat
```

会出现交互式菜单：
```
================================================================================
Mining Agents - 测试套件启动器
================================================================================

请选择要运行的测试:

[1] 单个 Agent 测试 (Step 1-8)
[2] 端到端集成测试 (完整流程)
[3] 运行所有测试
[4] 生成测试数据
[5] 查看测试文档
[Q] 退出

请输入选项 (1-5 或 Q):
```

### 方法 2: 命令行运行

```bash
# 运行所有测试
python tests/test_runner.py --all --verbose

# 只运行单个 Agent 测试
python tests/test_runner.py --single

# 只运行端到端测试
python tests/test_runner.py --e2e

# 生成测试数据
python tests/test_data_generator.py --output-dir ./test_data
```

### 方法 3: 直接使用 pytest

```bash
# 运行特定测试文件
pytest tests/test_single_agents.py -v

# 运行特定测试类
pytest tests/test_single_agents.py::TestRequirementAnalystAgent -v

# 运行特定测试方法
pytest tests/test_single_agents.py::TestRequirementAnalystAgent::test_execute_basic -v

# 生成覆盖率报告
pytest tests/ --cov=mining_agents --cov-report=html
```

## 📊 测试覆盖详情

### 单个 Agent 测试 (test_single_agents.py)

**9 个测试类，25+ 个测试用例：**

```
TestRequirementAnalystAgent     # Step 1 - 需求分析
  ✓ test_execute_basic          # 基本执行
  ✓ test_question_categories    # 问题分类
  ✓ test_output_markdown_format # Markdown 格式

TestDomainExpertAgent           # Step 2a - 领域专家
  ✓ test_domain_analysis        # 领域分析

TestCustomerAdvocateAgent       # Step 2b - 客户倡导
  ✓ test_customer_perspective   # 客户视角

TestCoordinatorAgent            # Step 3 - 任务分解
  ✓ test_task_breakdown         # 任务分解

TestRuleEngineerAgent           # Step 4 - 全局规则
  ✓ test_rule_generation        # 规则生成

TestDomainSpecialistAgent       # Step 5 - 专项配置
  ✓ test_domain_tools_definition # 工具定义

TestUserPortraitMinerAgent      # Step 6 - 私域数据
  ✓ test_mock_data_extraction   # 数据提取
  ✓ test_pain_point_identification # 痛点识别

TestQAModeratorAgent            # Step 7 - 质量检查
  ✓ test_completeness_check     # 完整性检查
  ✓ test_quality_scoring        # 质量评分

TestConfigAssemblerAgent        # Step 8 - 配置生成
  ✓ test_config_assembly        # 配置组装
  ✓ test_parlant_format_conversion # 格式转换

TestAgentIntegration            # 集成测试
  ✓ test_step1_to_step3_flow    # Step 1-3 流程
  ✓ test_all_agents_initialization # 初始化测试

TestAgentPerformance            # 性能测试
  ✓ test_agent_response_time    # 响应时间
```

### 端到端测试 (test_end_to_end.py)

**3 个测试类，8+ 个测试用例：**

```
TestEndToEndWorkflow            # 完整工作流
  ✓ test_complete_8_step_workflow # 8 步完整流程

TestPhasedIntegration           # 分阶段集成
  ✓ test_phase1_analysis        # 需求分析阶段
  ✓ test_phase2_planning        # 规划分解阶段
  ✓ test_phase3_configuration   # 专项配置阶段
  ✓ test_phase4_finalization    # 最终配置阶段

TestDataFlow                    # 数据流测试
  ✓ test_data_propagation       # 数据传递测试
```

### 测试数据生成器 (test_data_generator.py)

**6 种数据类型：**

```python
generator = TestDataGenerator(Path("./test_data"))

generator.generate_business_descriptions()    # 5 个行业业务描述
generator.generate_mock_conversations(50)     # 50 条模拟对话
generator.generate_user_portraits(20)         # 20 个用户画像
generator.generate_domain_knowledge()         # 领域知识库
generator.generate_quality_check_scenarios()  # 质检场景
generator.generate_excel_sample()             # Excel 示例
```

## 📁 输出结构

### 测试结果目录

```
test_results/
├── execution_summary.json       # 执行汇总（JSON）
├── execution_summary.txt        # 执行汇总（文本）
├── pytest_result.log            # pytest 日志
├── test_single_agents_report.json   # 单个 Agent 测试详情
└── test_end_to_end_report.json      # 端到端测试详情
```

### 测试数据目录

```
test_data/
├── business_descriptions.json   # 业务描述
├── mock_conversations.json      # 模拟对话
├── user_portraits.json          # 用户画像
├── ecommerce_knowledge.json     # 领域知识
├── quality_check_scenarios.json # 质检场景
└── sample_conversations.csv     # Excel 示例
```

## 🎯 典型测试场景

### 场景 1: 验证单个 Agent 功能

```bash
# 测试 RequirementAnalystAgent
pytest tests/test_single_agents.py::TestRequirementAnalystAgent -v

# 输出示例：
# tests/test_single_agents.py::TestRequirementAnalystAgent::test_execute_basic PASSED
# tests/test_single_agents.py::TestRequirementAnalystAgent::test_question_categories PASSED
# tests/test_single_agents.py::TestRequirementAnalystAgent::test_output_markdown_format PASSED
```

### 场景 2: 验证完整流程

```bash
# 测试 8 步完整流程
pytest tests/test_end_to_end.py::TestEndToEndWorkflow::test_complete_8_step_workflow -v -s

# 输出将显示每一步的执行情况：
# [Step 1/8] 需求分析...
#   ✓ 生成了 5 个澄清问题
# [Step 2/8] 多 Agent 辩论...
#   ✓ 完成领域专家和客户倡导双视角分析
# ...
# ✅ 完整工作流测试通过！
```

### 场景 3: 生成并使用测试数据

```bash
# 1. 生成测试数据
python tests/test_data_generator.py --output-dir ./test_data

# 2. 查看生成的数据
ls test_data/
# business_descriptions.json
# mock_conversations.json
# user_portraits.json
# ...

# 3. 在测试中使用数据
# （测试会自动使用 Mock 数据）
```

### 场景 4: 生成测试报告

```bash
# 运行测试并生成报告
python tests/test_runner.py --all --verbose

# 查看报告
cat test_results/execution_summary.txt
```

**报告示例：**
```
================================================================================
测试执行汇总报告
执行时间：2026-03-20T15:30:00
================================================================================

总测试数：2
通过：2
失败：0

详细结果:
--------------------------------------------------------------------------------
✅ single_agents: passed
✅ end_to_end: passed

================================================================================
🎉 所有测试通过！
```

## 🔧 高级用法

### 并行测试

```bash
# 使用 pytest-xdist 并行执行
pip install pytest-xdist
pytest tests/ -n auto  # 自动检测 CPU 核心数
```

### 覆盖率统计

```bash
# 生成 HTML 覆盖率报告
pytest tests/ --cov=mining_agents --cov-report=html

# 在浏览器中查看
open htmlcov/index.html  # Mac/Linux
start htmlcov\\index.html  # Windows
```

### 选择性测试

```bash
# 只运行快速测试（排除慢速测试）
pytest tests/ -m "not slow"

# 只运行集成测试
pytest tests/ -m integration

# 只运行 e2e 测试
pytest tests/ -m e2e
```

### 调试模式

```bash
# 显示详细输出
pytest tests/test_single_agents.py -v -s

# 失败后停止
pytest tests/ -x

# 进入调试器
pytest tests/test_single_agents.py --pdb
```

## 📈 测试统计

### 代码统计

| 指标 | 数量 |
|------|------|
| 测试文件 | 7 个 |
| 测试类 | 15+ 个 |
| 测试用例 | 35+ 个 |
| Fixtures | 20+ 个 |
| 代码行数 | ~2,000 行 |

### 覆盖范围

| 模块 | 覆盖率目标 |
|------|-----------|
| Agents (9 个) | 100% |
| Managers | 95% |
| Tools | 90% |
| CLI | 85% |

## 🐛 常见问题

### Q: 测试超时怎么办？

```bash
# 增加超时时间
pytest tests/test_end_to_end.py --timeout=600
```

### Q: 如何跳过某些测试？

```bash
# 跳过慢速测试
pytest tests/ -m "not slow"

# 跳过特定标记的测试
pytest tests/ -m "not integration"
```

### Q: 如何查看测试进度？

```bash
# 显示进度条
pytest tests/ --progress

# 显示每个测试的开始时间
pytest tests/ -vv
```

### Q: 如何保存测试输出？

```bash
# 重定向到文件
pytest tests/ > test_output.txt 2>&1

# 或使用 pytest 的日志功能
pytest tests/ --log-file=test_output.log
```

## 📞 支持与反馈

如有问题：
1. 查看 `tests/README.md` 详细文档
2. 检查 `test_results/` 中的测试报告
3. 联系开发团队

---

**创建日期**: 2026-03-20  
**维护者**: Mining Agents Team  
**版本**: 1.0.0
