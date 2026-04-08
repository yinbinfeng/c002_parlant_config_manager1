# 测试套件文档

## 📋 概述

本测试套件提供完整的测试覆盖，包括：
- **单个 Agent 测试**: 独立测试每个 Agent 的功能
- **端到端集成测试**: 测试完整 8 步工作流程
- **数据流测试**: 验证数据在步骤间的传递
- **性能测试**: 测试响应时间和资源使用

## 🗂️ 测试文件结构

```
tests/
├── README.md                      # 本文档
├── test_single_agents.py          # 单个 Agent 测试
├── test_end_to_end.py             # 端到端集成测试
├── test_data_generator.py         # 测试数据生成器
├── test_runner.py                 # 测试运行器
└── conftest.py                    # pytest 配置
```

## 🚀 快速开始

### 方法 1: 使用测试运行器（推荐）

```bash
# 运行所有测试
python tests/test_runner.py --all

# 只运行单个 Agent 测试
python tests/test_runner.py --single

# 只运行端到端测试
python tests/test_runner.py --e2e

# 显示详细输出
python tests/test_runner.py --all --verbose
```

### 方法 2: 直接使用 pytest

```bash
# 运行单个 Agent 测试
pytest tests/test_single_agents.py -v

# 运行端到端测试
pytest tests/test_end_to_end.py -v

# 运行特定测试类
pytest tests/test_single_agents.py::TestRequirementAnalystAgent -v

# 运行特定测试方法
pytest tests/test_single_agents.py::TestRequirementAnalystAgent::test_execute_basic -v

# 生成覆盖率报告
pytest tests/ --cov=mining_agents --cov-report=html
```

### 方法 3: 生成测试数据后运行

```bash
# 1. 生成测试数据
python tests/test_data_generator.py --output-dir ./test_data

# 2. 运行测试
pytest tests/test_single_agents.py -v
```

## 📊 测试类别详解

### 1. 单个 Agent 测试 (`test_single_agents.py`)

测试每个 Agent 的独立功能：

| 测试类 | 测试内容 | Steps |
|--------|---------|-------|
| `TestRequirementAnalystAgent` | 需求分析、问题生成、Markdown 格式 | Step 1 |
| `TestDomainExpertAgent` | 领域专家视角分析 | Step 2a |
| `TestCustomerAdvocateAgent` | 客户倡导视角分析 | Step 2b |
| `TestCoordinatorAgent` | 任务分解、流程设计 | Step 3 |
| `TestRuleEngineerAgent` | 全局规则设计 | Step 4 |
| `TestDomainSpecialistAgent` | 领域工具定义、术语表 | Step 5 |
| `TestUserPortraitMinerAgent` | 用户画像挖掘、痛点识别 | Step 6 |
| `TestQAModeratorAgent` | 质量检查、评分系统 | Step 7 |
| `TestConfigAssemblerAgent` | 配置组装、Parlant 格式转换 | Step 8 |

**关键测试点**:
- ✅ Agent 初始化
- ✅ execute() 方法执行
- ✅ 输出结构验证
- ✅ 文件格式检查
- ✅ Mock 模式支持

### 2. 端到端集成测试 (`test_end_to_end.py`)

测试完整的工作流程：

| 测试类 | 测试内容 |
|--------|---------|
| `TestEndToEndWorkflow::test_complete_8_step_workflow` | 完整 8 步流程测试 |
| `TestPhasedIntegration::test_phase1_analysis` | 阶段 1: 需求分析 |
| `TestPhasedIntegration::test_phase2_planning` | 阶段 2: 规划分解 |
| `TestPhasedIntegration::test_phase3_configuration` | 阶段 3: 专项配置 |
| `TestPhasedIntegration::test_phase4_finalization` | 阶段 4: 最终配置 |
| `TestDataFlow::test_data_propagation` | 数据流传递测试 |

**关键测试点**:
- ✅ 步骤间数据传递
- ✅ 上下文一致性
- ✅ 配置文件生成
- ✅ 错误处理和恢复

### 3. 测试数据生成器 (`test_data_generator.py`)

生成各种测试场景所需数据：

```python
from test_data_generator import TestDataGenerator
from pathlib import Path

generator = TestDataGenerator(Path("./test_data"))

# 生成所有测试数据
generator.generate_all()

# 或单独生成特定数据
generator.generate_business_descriptions()    # 业务描述
generator.generate_mock_conversations(50)     # 模拟对话
generator.generate_user_portraits(20)         # 用户画像
generator.generate_domain_knowledge()         # 领域知识
generator.generate_quality_check_scenarios()  # 质检场景
generator.generate_excel_sample()             # Excel 示例
```

**生成的数据类型**:
- 📝 业务描述（5 个行业场景）
- 💬 模拟对话记录（50+ 条）
- 👤 用户画像（20+ 个）
- 📚 领域知识库
- ✅ 质量检查场景
- 📊 Excel/CSV 示例数据

### 4. 测试运行器 (`test_runner.py`)

统一管理测试执行和报告生成：

```bash
# 基本用法
python tests/test_runner.py --all

# 高级选项
python tests/test_runner.py \
  --single \
  --verbose \
  --output-dir ./my_test_results
```

**功能特性**:
- ✅ 自动发现测试
- ✅ 并行执行支持
- ✅ JSON/TXT 报告生成
- ✅ 超时保护（5 分钟）
- ✅ 错误捕获和日志

## 📁 测试输出

### 测试结果目录

```
test_results/
├── execution_summary.json       # 执行汇总（JSON）
├── execution_summary.txt        # 执行汇总（文本）
├── pytest_result.log            # pytest 日志
├── test_single_agents_report.json   # 单个 Agent 测试详情
└── test_end_to_end_report.json      # 端到端测试详情
```

### 测试报告示例

**JSON 报告结构**:
```json
{
  "test_execution_summary": {
    "timestamp": "2026-03-20T10:30:00",
    "total_tests": 2,
    "passed": 2,
    "failed": 0
  },
  "details": {
    "single_agents": {
      "status": "passed",
      "returncode": 0
    },
    "end_to_end": {
      "status": "passed",
      "returncode": 0
    }
  }
}
```

## 🔧 配置选项

### pytest.ini (项目根目录)

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
asyncio_mode = auto
```

### conftest.py Fixtures

提供的共享 fixtures:

```python
@pytest.fixture
def temp_dir():
    """临时目录"""

@pytest.fixture
async def orchestrator(temp_dir):
    """Agent Orchestrator 实例"""

@pytest.fixture
def business_context():
    """基础业务上下文"""
```

## 🎯 测试最佳实践

### 1. 编写新测试

```python
import pytest
from mining_agents.agents import YourAgent

class TestYourAgent:
    
    @pytest.mark.asyncio
    async def test_your_feature(self, orchestrator, temp_dir):
        """测试你的功能"""
        context = {
            "business_desc": "测试业务",
            "mock_mode": True,
            "output_dir": str(temp_dir),
        }
        
        agent = YourAgent(name="TestAgent", orchestrator=orchestrator)
        result = await agent.execute(task="测试任务", context=context)
        
        # 验证结果
        assert "expected_field" in result
        await agent.close()
```

### 2. 使用 Mock 模式

所有测试默认使用 Mock 模式，无需真实 API 调用：

```python
context["mock_mode"] = True  # 启用 Mock
```

### 3. 测试异步代码

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

### 4. 参数化测试

```python
@pytest.mark.parametrize("industry", [
    "ecommerce",
    "banking",
    "travel",
])
@pytest.mark.asyncio
async def test_multiple_industries(industry, orchestrator):
    context = {"business_desc": f"{industry} 客服"}
    # 测试逻辑...
```

## 🐛 故障排除

### 常见问题

**Q: 测试超时**
```bash
# 增加超时时间
pytest tests/test_end_to_end.py -v --timeout=600
```

**Q: 导入错误**
```bash
# 确保在项目根目录运行
cd /path/to/mining_agents
pytest tests/
```

**Q: Async 错误**
```ini
# 确保 pytest.ini 中有
[pytest]
asyncio_mode = auto
```

**Q: 内存不足**
```bash
# 逐个运行测试文件
pytest tests/test_single_agents.py -v
pytest tests/test_end_to_end.py -v
```

### 调试技巧

1. **显示输出**:
   ```bash
   pytest tests/test_single_agents.py -v -s
   ```

2. **断点调试**:
   ```python
   def test_debug():
       import pdb; pdb.set_trace()
       # 你的代码
   ```

3. **详细日志**:
   ```bash
   pytest tests/ -vvv --log-cli-level=DEBUG
   ```

4. **失败后停止**:
   ```bash
   pytest tests/ -x  # 第一次失败后停止
   ```

## 📈 覆盖率统计

生成覆盖率报告：

```bash
# HTML 格式
pytest tests/ --cov=mining_agents --cov-report=html

# 终端显示
pytest tests/ --cov=mining_agents --cov-report=term-missing

# XML 格式（用于 CI）
pytest tests/ --cov=mining_agents --cov-report=xml
```

查看 `htmlcov/index.html` 获取详细覆盖率信息。

## 🔄 CI/CD 集成

### GitHub Actions 示例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      
      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt
      
      - name: Run tests
        run: |
          python tests/test_runner.py --all
      
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: test-results
          path: test_results/
```

## 📞 支持与反馈

如有问题或建议，请：
1. 查看本文档
2. 检查 `test_results/` 中的详细报告
3. 联系开发团队

---

**最后更新**: 2026-03-20  
**维护者**: Mining Agents Team
