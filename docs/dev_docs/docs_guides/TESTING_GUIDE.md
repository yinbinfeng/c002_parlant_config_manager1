# 测试执行指南

## 概述

本文档说明如何运行 mining_agents 项目的完整功能验证测试。

## 快速开始

### Windows 用户

**方法 1: 双击运行（推荐）**

1. 双击 `RUN_VERIFICATION.bat` 文件
2. 等待测试完成
3. 查看生成的报告

**方法 2: 命令行运行**

```cmd
cd E:\cursorworkspace\c002_parlant_config_manager1
python generate_test_report.py
```

### Linux/Mac 用户

```bash
cd /path/to/mining_agents
python3 generate_test_report.py
```

## 测试输出

测试执行后会生成以下文件：

1. **VERIFICATION_REPORT_FINAL.txt** - 文本格式的验证报告
2. **verification_results.json** - JSON 格式的详细结果

## 测试覆盖范围

测试包含以下 6 个类别：

### 1. Agent 实现 (9 个文件)
- ✓ requirement_analyst_agent.py (Step 1)
- ✓ domain_expert_agent.py (Step 2a)
- ✓ customer_advocate_agent.py (Step 2b)
- ✓ coordinator_agent.py (Step 3)
- ✓ rule_engineer_agent.py (Step 4)
- ✓ domain_specialist_agent.py (Step 5)
- ✓ user_portrait_miner_agent.py (Step 6)
- ✓ qa_moderator_agent.py (Step 7)
- ✓ config_assembler_agent.py (Step 8)

### 2. Agent 导出配置
- 检查 __init__.py 是否正确导出所有 9 个 Agent 类

### 3. Managers 模块 (2 个文件)
- ✓ step_manager.py - 步骤调度管理器
- ✓ agent_orchestrator.py - Agent 编排器

### 4. Tools 模块 (4 个文件)
- ✓ json_validator.py - JSON 校验工具
- ✓ deep_research.py - 深度研究工具
- ✓ file_service.py - 文件服务工具
- ✓ agentscope_tools.py - AgentScope 工具集

### 5. CLI 模块
- ✓ cli.py - 命令行接口

### 6. 版本化管理结构 (v0.4.0_complete)
- ✓ main.py - 主入口
- ✓ config/system_config.yaml - 系统配置
- ✓ config/agents/base_agent.yaml - Agent 模板
- ✓ scripts/run_all_steps.bat - Windows 启动脚本
- ✓ scripts/run_all_steps.sh - Linux/Mac 启动脚本
- ✓ scripts/verify_output.py - 验证脚本
- ✓ README.md - 使用文档

## 预期结果

如果所有测试通过，您将看到：

```
================================================================================
验证结果汇总
================================================================================
  通过：XX
  失败：0
  总计：XX
  成功率：100.0%

🎉 恭喜！所有验证通过！系统功能完整！
```

## 故障排除

### Python 未找到

错误信息：`[错误] 未找到 Python`

解决方案：
1. 安装 Python 3.8+
2. 将 Python 添加到系统 PATH
3. 或修改批处理文件使用完整的 Python 路径

### 导入错误

如果遇到导入错误，请确保：
1. 已安装所有依赖：`pip install -r requirements.txt`
2. 在正确的项目目录中运行测试

## 手动运行单个测试

如果需要运行特定的测试文件：

```bash
# 运行 MVP 测试
pytest tests/test_mvp.py -v

# 运行 AgentScope 工具测试
pytest tests/test_agentscope_tools.py -v

# 运行 Step 2-3 Agent 测试
pytest tests/test_step2_step3_agents.py -v
```

## 联系支持

如有问题，请查看：
- 项目文档：`prj/v0.4.0_complete/README.md`
- 验证报告：`VERIFICATION_REPORT_FINAL.txt`

---

最后更新：2026-03-20
