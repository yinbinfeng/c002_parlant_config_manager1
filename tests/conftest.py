#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pytest 共享 fixtures 和配置
"""

import pytest
import asyncio
from pathlib import Path
import tempfile
import shutil
import sys

# 添加项目路径
project_root = Path(__file__).parent.parent.resolve()
src_dir = project_root / "src"
sys.path.insert(0, str(src_dir))


# ============================================================================
# 目录 Fixtures
# ============================================================================

@pytest.fixture
def temp_dir():
    """
    创建临时目录
    
    Usage:
        def test_something(temp_dir):
            # temp_dir 是 Path 对象
            test_file = temp_dir / "test.txt"
    """
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)


@pytest.fixture
def temp_workspace():
    """
    创建临时工作空间（包含多个子目录）
    
    Usage:
        def test_workflow(temp_workspace):
            output_dir = temp_workspace["output"]
            config_dir = temp_workspace["config"]
    """
    tmpdir = tempfile.mkdtemp()
    workspace = {
        "root": Path(tmpdir),
        "output": Path(tmpdir) / "output",
        "config": Path(tmpdir) / "config",
        "input": Path(tmpdir) / "input",
        "logs": Path(tmpdir) / "logs",
    }
    
    for dir_path in workspace.values():
        dir_path.mkdir(parents=True, exist_ok=True)
    
    yield workspace
    shutil.rmtree(tmpdir)


# ============================================================================
# Agent Fixtures
# ============================================================================

@pytest.fixture
async def orchestrator(temp_dir):
    """
    创建 AgentOrchestrator 实例（Mock 模式）
    
    Usage:
        @pytest.mark.asyncio
        async def test_agent(orchestrator):
            agent = SomeAgent(name="Test", orchestrator=orchestrator)
    """
    from mining_agents.managers.agent_orchestrator import AgentOrchestrator
    from mining_agents.tools.deep_research import DeepResearchTool
    from mining_agents.tools.json_validator import JsonValidator
    
    orch = AgentOrchestrator(config={"mock_mode": True})
    orch.register_tool("deep_research", DeepResearchTool(config={}, mock_mode=True))
    orch.register_tool("json_validator", JsonValidator())
    
    yield orch
    
    await orch.cleanup()


@pytest.fixture
def business_context():
    """
    基础业务上下文
    
    Usage:
        def test_something(business_context):
            context = business_context.copy()
            context["output_dir"] = "/path/to/output"
    """
    return {
        "business_desc": "电商客服 Agent，处理订单查询、退换货和商品咨询",
        "mock_mode": True,
        "output_dir": None,
        "step_outputs": {},
    }


@pytest.fixture
def step1_mock_result():
    """Step 1 Mock 结果"""
    return {
        "questions": [
            {
                "id": "q1",
                "question": "您的主要业务流程是什么？",
                "category": "业务流程",
                "priority": "high"
            },
            {
                "id": "q2",
                "question": "目标用户群体是谁？",
                "category": "用户群体",
                "priority": "high"
            },
        ],
        "output_files": ["step1_questions.md"],
        "metadata": {
            "question_count": 2,
            "mock_mode": True
        }
    }


@pytest.fixture
def step2_mock_results():
    """Step 2 Mock 结果（双视角）"""
    return {
        "domain_expert": {
            "analysis": "领域专家分析结果",
            "perspectives": ["视角 1", "视角 2"],
        },
        "customer_advocate": {
            "customer_needs": ["需求 1", "需求 2"],
            "pain_points": ["痛点 1", "痛点 2"],
        }
    }


@pytest.fixture
def complete_step_outputs():
    """完整的 8 步 Mock 输出"""
    return {
        f"step{i}": {
            "data": f"step{i}_data",
            "output_files": [f"step{i}_output.md"]
        }
        for i in range(1, 9)
    }


# ============================================================================
# Tool Fixtures
# ============================================================================

@pytest.fixture
def json_validator():
    """JsonValidator 实例"""
    from mining_agents.tools.json_validator import JsonValidator
    return JsonValidator()


@pytest.fixture
def deep_research_tool():
    """DeepResearchTool 实例（Mock 模式）"""
    from mining_agents.tools.deep_research import DeepResearchTool
    return DeepResearchTool(config={}, mock_mode=True)


@pytest.fixture
def file_service():
    """FileServiceManager 实例"""
    from mining_agents.tools.file_service import FileServiceManager
    manager = FileServiceManager()
    yield manager
    # 清理已在 close 中完成


# ============================================================================
# Agent Class Fixtures
# ============================================================================

@pytest.fixture
def requirement_analyst_agent(orchestrator):
    """RequirementAnalystAgent 实例"""
    from mining_agents.agents import RequirementAnalystAgent
    agent = RequirementAnalystAgent(name="TestFixture", orchestrator=orchestrator)
    yield agent
    
    # 清理
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(agent.close())
        else:
            loop.run_until_complete(agent.close())
    except:
        pass


@pytest.fixture
def coordinator_agent(orchestrator):
    """CoordinatorAgent 实例"""
    from mining_agents.agents import CoordinatorAgent
    agent = CoordinatorAgent(name="TestFixture", orchestrator=orchestrator)
    yield agent
    
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(agent.close())
        else:
            loop.run_until_complete(agent.close())
    except:
        pass


@pytest.fixture
def qa_moderator_agent(orchestrator):
    """QAModeratorAgent 实例"""
    from mining_agents.agents import QAModeratorAgent
    agent = QAModeratorAgent(name="TestFixture", orchestrator=orchestrator)
    yield agent
    
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(agent.close())
        else:
            loop.run_until_complete(agent.close())
    except:
        pass


@pytest.fixture
def config_assembler_agent(orchestrator):
    """ConfigAssemblerAgent 实例"""
    from mining_agents.agents import ConfigAssemblerAgent
    agent = ConfigAssemblerAgent(name="TestFixture", orchestrator=orchestrator)
    yield agent
    
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(agent.close())
        else:
            loop.run_until_complete(agent.close())
    except:
        pass


# ============================================================================
# 数据 Fixtures
# ============================================================================

@pytest.fixture
def sample_excel_data(temp_dir):
    """生成示例 Excel 数据（CSV 格式）"""
    try:
        import pandas as pd
        
        data = {
            "对话 ID": [f"conv_{i:04d}" for i in range(1, 51)],
            "日期": ["2026-01-01"] * 50,
            "用户类型": ["新客户"] * 25 + ["老客户"] * 25,
            "问题类型": ["订单查询"] * 10 + ["退换货"] * 10 + ["商品咨询"] * 10 + ["投诉"] * 20,
            "满意度": [3, 4, 5, 2, 1] * 10,
        }
        
        df = pd.DataFrame(data)
        csv_file = temp_dir / "sample_conversations.csv"
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        
        return str(csv_file)
        
    except ImportError:
        return None


@pytest.fixture
def sample_business_descriptions():
    """示例业务描述列表"""
    return [
        "电商客服 Agent，处理订单查询、退换货、商品咨询和投诉建议",
        "银行客服 Agent，处理账户查询、转账汇款、信用卡业务和理财咨询",
        "旅游预订 Agent，处理机票预订、酒店预订、行程规划和退改签服务",
        "医疗健康咨询 Agent，提供科室导诊、医生排班查询、健康科普和预约挂号",
        "教育咨询 Agent，提供课程推荐、学习规划、考试安排和证书查询",
    ]


# ============================================================================
# 工具函数 Fixtures
# ============================================================================

@pytest.fixture
def capture_output():
    """捕获 stdout/stderr"""
    import io
    from contextlib import redirect_stdout, redirect_stderr
    
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    
    with redirect_stdout(stdout_capture) as out_ctx, redirect_stderr(stderr_capture) as err_ctx:
        yield {
            "stdout": lambda: stdout_capture.getvalue(),
            "stderr": lambda: stderr_capture.getvalue(),
        }


@pytest.fixture
def mock_llm_response():
    """Mock LLM 响应"""
    class MockLLMResponse:
        def __init__(self, text="Mock response"):
            self.text = text
        
        def __str__(self):
            return self.text
    
    return MockLLMResponse()


# ============================================================================
# pytest 钩子
# ============================================================================

def pytest_configure(config):
    """pytest 配置时的钩子"""
    # 注册自定义标记
    config.addinivalue_line(
        "markers", "slow: marks tests as slow"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )


def pytest_collection_modifyitems(config, items):
    """修改收集到的测试项"""
    # 自动为测试添加标记
    for item in items:
        # 根据文件名添加标记
        if "end_to_end" in item.fspath.basename:
            item.add_marker(pytest.mark.e2e)
        elif "single_agent" in item.fspath.basename:
            item.add_marker(pytest.mark.unit)


# ============================================================================
# 异步测试支持
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
