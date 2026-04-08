#!/usr/bin/env python3
"""Step 2 & Step 3 Agents 测试套件"""

import pytest
import asyncio
from pathlib import Path
import sys

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from mining_agents.agents.domain_expert_agent import DomainExpertAgent
from mining_agents.agents.customer_advocate_agent import CustomerAdvocateAgent
from mining_agents.agents.coordinator_agent import CoordinatorAgent
from mining_agents.tools.json_validator import JsonValidator


class MockOrchestrator:
    """Mock Orchestrator for testing"""
    
    def __init__(self):
        self.tools = {
            "json_validator": JsonValidator(),
        }
    
    def get_tool(self, tool_name):
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not registered")
        return self.tools[tool_name]


class TestDomainExpertAgent:
    """测试领域专家 Agent"""
    
    @pytest.fixture
    def orchestrator(self):
        return MockOrchestrator()
    
    @pytest.fixture
    def agent(self, orchestrator):
        return DomainExpertAgent(name="TestDomainExpert", orchestrator=orchestrator)
    
    @pytest.mark.asyncio
    async def test_init(self, agent):
        """测试 Agent 初始化"""
        assert agent.name == "TestDomainExpert"
        assert agent.orchestrator is not None
        assert agent.json_validator is not None
    
    @pytest.mark.asyncio
    async def test_execute_mock(self, agent):
        """测试 Mock 模式执行"""
        context = {
            "business_desc": "电商客服 Agent",
            "step1_questions": [
                {"id": "Q1", "question": "目标用户是谁？", "category": "users"}
            ],
            "mock_mode": True,
            "output_dir": "./output/test_step2",
        }
        
        result = await agent.execute(
            task="从行业最佳实践角度提供专业建议",
            context=context
        )
        
        # 验证结果结构
        assert "expert_opinions" in result
        assert "output_files" in result
        assert "metadata" in result
        
        # 验证专家意见
        expert_opinions = result["expert_opinions"]
        assert len(expert_opinions) > 0
        assert all("id" in op for op in expert_opinions)
        assert all("title" in op for op in expert_opinions)
        assert all("opinion" in op for op in expert_opinions)
        
        # 验证输出文件
        output_files = result["output_files"]
        assert len(output_files) >= 1
        assert any(".md" in f for f in output_files)
    
    @pytest.mark.asyncio
    async def test_generate_mock_opinions(self, agent):
        """测试生成 Mock 专家意见"""
        business_desc = "智能医疗咨询 Agent"
        step1_questions = [
            {"id": "Q1", "question": "目标用户？", "category": "users"},
            {"id": "Q2", "question": "核心功能？", "category": "features"},
            {"id": "Q3", "question": "合规要求？", "category": "compliance"},
            {"id": "Q4", "question": "集成需求？", "category": "integrations"},
            {"id": "Q5", "question": "数据隐私？", "category": "privacy"},
            {"id": "Q6", "question": "特殊场景？", "category": "edge_cases"},
        ]
        
        opinions = agent._generate_mock_expert_opinions(business_desc, step1_questions)
        
        # 验证问题数量（超过 5 个问题应该生成额外的 EXP6）
        assert len(opinions) >= 5
        
        # 验证类别覆盖
        categories = [op["category"] for op in opinions]
        assert "industry_standard" in categories
        assert "technical_architecture" in categories
        assert "data_governance" in categories


class TestCustomerAdvocateAgent:
    """测试客户倡导者 Agent"""
    
    @pytest.fixture
    def orchestrator(self):
        return MockOrchestrator()
    
    @pytest.fixture
    def agent(self, orchestrator):
        return CustomerAdvocateAgent(name="TestCustomerAdvocate", orchestrator=orchestrator)
    
    @pytest.mark.asyncio
    async def test_init(self, agent):
        """测试 Agent 初始化"""
        assert agent.name == "TestCustomerAdvocate"
        assert agent.orchestrator is not None
    
    @pytest.mark.asyncio
    async def test_execute_mock(self, agent):
        """测试 Mock 模式执行"""
        context = {
            "business_desc": "教育助手 Agent",
            "step1_questions": [{"id": "Q1", "question": "目标学生群体？"}],
            "expert_opinions": [
                {"id": "EXP1", "title": "技术架构建议", "category": "technical"}
            ],
            "mock_mode": True,
            "output_dir": "./output/test_step2",
        }
        
        result = await agent.execute(
            task="从最终用户角度质疑和评估方案",
            context=context
        )
        
        # 验证结果结构
        assert "user_concerns" in result
        assert "output_files" in result
        
        # 验证用户关切
        user_concerns = result["user_concerns"]
        assert len(user_concerns) > 0
        assert all("id" in c for c in user_concerns)
        assert all("title" in c for c in user_concerns)
        assert all("concern" in c for c in user_concerns)
        assert all("impact" in c for c in user_concerns)
    
    @pytest.mark.asyncio
    async def test_user_concern_categories(self, agent):
        """测试用户关切类别覆盖"""
        concerns = agent._generate_mock_user_concerns(
            "客服 Agent",
            [],
            [{"category": "technical_architecture"}]
        )
        
        categories = [c["category"] for c in concerns]
        
        # 验证核心类别
        assert "usability" in categories
        assert "trust" in categories
        assert "privacy" in categories


class TestCoordinatorAgent:
    """测试协调员 Agent"""
    
    @pytest.fixture
    def orchestrator(self):
        return MockOrchestrator()
    
    @pytest.fixture
    def agent(self, orchestrator):
        return CoordinatorAgent(name="TestCoordinator", orchestrator=orchestrator)
    
    @pytest.mark.asyncio
    async def test_init(self, agent):
        """测试 Agent 初始化"""
        assert agent.name == "TestCoordinator"
        assert agent.orchestrator is not None
    
    @pytest.mark.asyncio
    async def test_execute_mock(self, agent):
        """测试 Mock 模式执行"""
        context = {
            "business_desc": "电商客服 Agent",
            "step1_questions": [{"id": "Q1", "question": "目标用户？"}],
            "step2_expert_opinions": [{"id": "EXP1", "title": "专家建议"}],
            "step2_user_concerns": [{"id": "USR1", "title": "用户关切"}],
            "step2_requirement_defense": [{"id": "REQ1", "question": "需求辩护"}],
            "mock_mode": True,
            "output_dir": "./output/test_step3",
        }
        
        result = await agent.execute(
            task="整合各方意见并生成任务分解方案",
            context=context
        )
        
        # 验证结果结构
        assert "task_breakdown" in result
        assert "output_files" in result
        assert "metadata" in result
        
        # 验证任务分解
        task_breakdown = result["task_breakdown"]
        assert "summary" in task_breakdown
        assert "components" in task_breakdown
        assert "implementation_phases" in task_breakdown
        
        # 验证组件数量
        components = task_breakdown["components"]
        assert len(components) >= 4  # Journey, Guideline, Tool, Glossary
        
        # 验证组件 ID
        component_ids = [c["id"] for c in components]
        assert "COMP1" in component_ids
        assert "COMP2" in component_ids
    
    @pytest.mark.asyncio
    async def test_task_breakdown_structure(self, agent):
        """测试任务分解结构完整性"""
        breakdown = agent._generate_mock_task_breakdown(
            "测试业务",
            [], [], [], []
        )
        
        # 验证摘要
        assert "title" in breakdown["summary"]
        assert "vision" in breakdown["summary"]
        assert "mvp_focus" in breakdown["summary"]
        
        # 验证实施阶段
        phases = breakdown["implementation_phases"]
        assert len(phases) >= 3
        assert all("phase" in p for p in phases)
        assert all("duration" in p for p in phases)
        assert all("deliverables" in p for p in phases)
        
        # 验证风险缓解
        risks = breakdown["risk_mitigation"]
        assert len(risks) > 0
        assert all("risk" in r for r in risks)
        assert all("mitigation" in r for r in risks)


class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_step2_to_step3_flow(self):
        """测试 Step 2 到 Step 3 的数据流"""
        from mining_agents.utils.file_utils import ensure_dir
        
        # 准备测试输出目录
        output_dir = Path("./output/integration_test")
        ensure_dir(str(output_dir))
        
        orchestrator = MockOrchestrator()
        
        # 执行 Step 2 Agents
        domain_expert = DomainExpertAgent(name="DE", orchestrator=orchestrator)
        customer_advocate = CustomerAdvocateAgent(name="CA", orchestrator=orchestrator)
        
        step2_context = {
            "business_desc": "集成测试 Agent",
            "step1_questions": [{"id": "Q1", "question": "测试问题？"}],
            "mock_mode": True,
            "output_dir": str(output_dir / "step2"),
        }
        
        # 并行执行 Step 2 Agents
        de_result = await domain_expert.execute("DE task", step2_context)
        ca_result = await customer_advocate.execute("CA task", step2_context)
        
        # 准备 Step 3 上下文
        step3_context = {
            "business_desc": "集成测试 Agent",
            "step1_questions": step2_context["step1_questions"],
            "step2_expert_opinions": de_result["expert_opinions"],
            "step2_user_concerns": ca_result["user_concerns"],
            "step2_requirement_defense": [],
            "mock_mode": True,
            "output_dir": str(output_dir / "step3"),
        }
        
        # 执行 Step 3
        coordinator = CoordinatorAgent(name="Coord", orchestrator=orchestrator)
        step3_result = await coordinator.execute("Coord task", step3_context)
        
        # 验证数据流
        assert len(de_result["expert_opinions"]) > 0
        assert len(ca_result["user_concerns"]) > 0
        assert step3_result["task_breakdown"]["summary"]["title"] is not None
        
        # 清理
        import shutil
        if output_dir.exists():
            shutil.rmtree(output_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
