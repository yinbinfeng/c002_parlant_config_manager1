#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单个 Agent 测试套件
测试每个 Agent 的独立功能
"""

import pytest
import asyncio
from pathlib import Path
import tempfile
import shutil
import json
from datetime import datetime

# 导入 Agents
from mining_agents.agents import (
    RequirementAnalystAgent,
    DomainExpertAgent,
    CustomerAdvocateAgent,
    CoordinatorAgent,
    RuleEngineerAgent,
    DomainSpecialistAgent,
    UserPortraitMinerAgent,
    QAModeratorAgent,
    ConfigAssemblerAgent,
)

from mining_agents.managers.agent_orchestrator import AgentOrchestrator
from mining_agents.tools.deep_research import DeepResearchTool
from mining_agents.tools.json_validator import JsonValidator


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_dir():
    """创建临时目录"""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)


@pytest.fixture
async def orchestrator(temp_dir):
    """创建 Orchestrator 实例"""
    orch = AgentOrchestrator(config={"mock_mode": True})
    orch.register_tool("deep_research", DeepResearchTool(config={}, mock_mode=True))
    orch.register_tool("json_validator", JsonValidator())
    yield orch
    await orch.cleanup()


@pytest.fixture
def business_context():
    """基础业务上下文"""
    return {
        "business_desc": "电商客服 Agent，处理订单查询、退换货和商品咨询",
        "mock_mode": True,
        "output_dir": None,  # 将在测试中设置
    }


# ============================================================================
# Step 1: RequirementAnalystAgent 测试
# ============================================================================

class TestRequirementAnalystAgent:
    """Step 1 - 需求分析 Agent 测试"""
    
    @pytest.mark.asyncio
    async def test_execute_basic(self, orchestrator, temp_dir, business_context):
        """测试基本执行"""
        business_context["output_dir"] = str(temp_dir)
        
        agent = RequirementAnalystAgent(name="TestAnalyst", orchestrator=orchestrator)
        result = await agent.execute(
            task="分析需求并生成澄清问题",
            context=business_context
        )
        
        # 验证结果结构
        assert "questions" in result
        assert len(result["questions"]) > 0
        assert "output_files" in result
        assert len(result["output_files"]) >= 1
        
        # 验证问题格式
        for question in result["questions"]:
            assert "id" in question
            assert "question" in question
            assert "category" in question
            assert "priority" in question
            assert question["priority"] in ["high", "medium", "low"]
        
        # 验证文件创建
        for file_path in result["output_files"]:
            assert Path(file_path).exists()
        
        await agent.close()
    
    @pytest.mark.asyncio
    async def test_question_categories(self, orchestrator, temp_dir, business_context):
        """测试问题分类覆盖"""
        business_context["output_dir"] = str(temp_dir)
        
        agent = RequirementAnalystAgent(name="TestAnalyst", orchestrator=orchestrator)
        result = await agent.execute(
            task="分析需求",
            context=business_context
        )
        
        categories = set(q["category"] for q in result["questions"])
        
        # 应包含多个类别
        assert len(categories) >= 3
        
        await agent.close()
    
    @pytest.mark.asyncio
    async def test_output_markdown_format(self, orchestrator, temp_dir, business_context):
        """测试 Markdown 输出格式"""
        business_context["output_dir"] = str(temp_dir)
        
        agent = RequirementAnalystAgent(name="TestAnalyst", orchestrator=orchestrator)
        result = await agent.execute(
            task="生成问题清单",
            context=business_context
        )
        
        # 读取 Markdown 文件
        md_file = Path(result["output_files"][0])
        content = md_file.read_text(encoding='utf-8')
        
        # 验证 Markdown 格式
        assert "# Step 1:" in content or "# 需求" in content
        assert "您的回答" in content or "回答：" in content
        
        await agent.close()


# ============================================================================
# Step 2: Domain Expert & Customer Advocate 测试
# ============================================================================

class TestDomainExpertAgent:
    """Step 2a - 领域专家 Agent 测试"""
    
    @pytest.mark.asyncio
    async def test_domain_analysis(self, orchestrator, temp_dir, business_context):
        """测试领域分析"""
        business_context["output_dir"] = str(temp_dir)
        
        agent = DomainExpertAgent(name="TestExpert", orchestrator=orchestrator)
        result = await agent.execute(
            task="从领域专家角度分析问题",
            context=business_context
        )
        
        assert "analysis" in result or "perspectives" in result
        assert "output_files" in result
        
        await agent.close()


class TestCustomerAdvocateAgent:
    """Step 2b - 客户倡导 Agent 测试"""
    
    @pytest.mark.asyncio
    async def test_customer_perspective(self, orchestrator, temp_dir, business_context):
        """测试客户视角分析"""
        business_context["output_dir"] = str(temp_dir)
        
        agent = CustomerAdvocateAgent(name="TestAdvocate", orchestrator=orchestrator)
        result = await agent.execute(
            task="从客户角度分析问题",
            context=business_context
        )
        
        assert "customer_needs" in result or "pain_points" in result
        assert "output_files" in result
        
        await agent.close()


# ============================================================================
# Step 3: CoordinatorAgent 测试
# ============================================================================

class TestCoordinatorAgent:
    """Step 3 - 任务分解协调 Agent 测试"""
    
    @pytest.mark.asyncio
    async def test_task_breakdown(self, orchestrator, temp_dir, business_context):
        """测试任务分解"""
        business_context["output_dir"] = str(temp_dir)
        
        # 先获取 Step 1 的结果
        step1_agent = RequirementAnalystAgent(name="Step1", orchestrator=orchestrator)
        step1_result = await step1_agent.execute(
            task="分析需求",
            context=business_context
        )
        await step1_agent.close()
        
        # 传递给 Coordinator
        business_context["step1_output"] = step1_result
        
        agent = CoordinatorAgent(name="TestCoordinator", orchestrator=orchestrator)
        result = await agent.execute(
            task="分解任务为对话流程",
            context=business_context
        )
        
        assert "tasks" in result or "workflows" in result
        assert "output_files" in result
        
        # 验证任务结构
        if "tasks" in result:
            for task in result["tasks"]:
                assert "name" in task or "description" in task
        
        await agent.close()


# ============================================================================
# Step 4: RuleEngineerAgent 测试
# ============================================================================

class TestRuleEngineerAgent:
    """Step 4 - 全局规则设计 Agent 测试"""
    
    @pytest.mark.asyncio
    async def test_rule_generation(self, orchestrator, temp_dir, business_context):
        """测试规则生成"""
        business_context["output_dir"] = str(temp_dir)
        
        agent = RuleEngineerAgent(name="TestRuleEngineer", orchestrator=orchestrator)
        result = await agent.execute(
            task="设计全局对话规则",
            context=business_context
        )
        
        assert "rules" in result or "guidelines" in result
        assert "output_files" in result
        
        # 验证规则结构
        if "rules" in result:
            assert len(result["rules"]) > 0
        
        await agent.close()


# ============================================================================
# Step 5: DomainSpecialistAgent 测试
# ============================================================================

class TestDomainSpecialistAgent:
    """Step 5 - 专项配置 Agent 测试"""
    
    @pytest.mark.asyncio
    async def test_domain_tools_definition(self, orchestrator, temp_dir, business_context):
        """测试领域工具定义"""
        business_context["output_dir"] = str(temp_dir)
        
        agent = DomainSpecialistAgent(name="TestSpecialist", orchestrator=orchestrator)
        result = await agent.execute(
            task="定义领域特定工具和术语",
            context=business_context
        )
        
        assert "tools" in result or "glossary" in result
        assert "output_files" in result
        
        await agent.close()


# ============================================================================
# Step 6: UserPortraitMinerAgent 测试
# ============================================================================

class TestUserPortraitMinerAgent:
    """Step 6 - 私域数据挖掘 Agent 测试"""
    
    @pytest.mark.asyncio
    async def test_mock_data_extraction(self, orchestrator, temp_dir, business_context):
        """测试 Mock 数据提取"""
        business_context["output_dir"] = str(temp_dir)
        business_context["excel_file"] = None  # 使用 Mock 模式
        
        agent = UserPortraitMinerAgent(name="TestMiner", orchestrator=orchestrator)
        result = await agent.execute(
            task="挖掘用户画像和对话模式",
            context=business_context
        )
        
        assert "user_portraits" in result or "patterns" in result
        assert "output_files" in result
        
        # 验证输出内容
        if "user_portraits" in result:
            assert len(result["user_portraits"]) > 0
        
        await agent.close()
    
    @pytest.mark.asyncio
    async def test_pain_point_identification(self, orchestrator, temp_dir, business_context):
        """测试痛点识别"""
        business_context["output_dir"] = str(temp_dir)
        
        agent = UserPortraitMinerAgent(name="TestMiner", orchestrator=orchestrator)
        result = await agent.execute(
            task="识别用户痛点和常见问题",
            context=business_context
        )
        
        # 验证痛点识别
        has_pain_points = (
            "pain_points" in result or 
            "common_issues" in result or
            "problems" in result
        )
        assert has_pain_points
        
        await agent.close()


# ============================================================================
# Step 7: QAModeratorAgent 测试
# ============================================================================

class TestQAModeratorAgent:
    """Step 7 - 质量检查 Agent 测试"""
    
    @pytest.mark.asyncio
    async def test_completeness_check(self, orchestrator, temp_dir, business_context):
        """测试完整性检查"""
        business_context["output_dir"] = str(temp_dir)
        
        # 提供模拟的步骤输出
        business_context["step_outputs"] = {
            "step1": {"questions": ["问题 1", "问题 2"]},
            "step2": {"analysis": "分析结果"},
            "step3": {"tasks": ["任务 1"]},
        }
        
        agent = QAModeratorAgent(name="TestModerator", orchestrator=orchestrator)
        result = await agent.execute(
            task="检查配置完整性",
            context=business_context
        )
        
        assert "quality_report" in result or "score" in result
        assert "output_files" in result
        
        # 验证评分系统
        if "score" in result:
            assert 0 <= result["score"] <= 100
        
        await agent.close()
    
    @pytest.mark.asyncio
    async def test_quality_scoring(self, orchestrator, temp_dir, business_context):
        """测试质量评分"""
        business_context["output_dir"] = str(temp_dir)
        business_context["step_outputs"] = {
            f"step{i}": {"data": f"step{i}_data"} 
            for i in range(1, 9)
        }
        
        agent = QAModeratorAgent(name="TestModerator", orchestrator=orchestrator)
        result = await agent.execute(
            task="全面质量评估",
            context=business_context
        )
        
        # 验证质量等级
        quality_checks = [
            "completeness_score" in result,
            "consistency_score" in result,
            "accuracy_score" in result,
            "executability_score" in result,
        ]
        
        assert any(quality_checks)
        
        await agent.close()


# ============================================================================
# Step 8: ConfigAssemblerAgent 测试
# ============================================================================

class TestConfigAssemblerAgent:
    """Step 8 - 配置生成 Agent 测试"""
    
    @pytest.mark.asyncio
    async def test_config_assembly(self, orchestrator, temp_dir, business_context):
        """测试配置组装"""
        business_context["output_dir"] = str(temp_dir)
        
        # 提供完整的步骤输出
        business_context["step_outputs"] = {
            f"step{i}": {"data": f"step{i}_data"} 
            for i in range(1, 9)
        }
        
        agent = ConfigAssemblerAgent(name="TestAssembler", orchestrator=orchestrator)
        result = await agent.execute(
            task="组装最终 Parlant 配置",
            context=business_context
        )
        
        assert "config" in result or "parlant_config" in result
        assert "output_files" in result
        
        # 验证配置文件生成
        config_files = [f for f in result["output_files"] 
                       if f.endswith(('.json', '.yaml', '.yml'))]
        assert len(config_files) > 0
        
        await agent.close()
    
    @pytest.mark.asyncio
    async def test_parlant_format_conversion(self, orchestrator, temp_dir, business_context):
        """测试 Parlant 格式转换"""
        business_context["output_dir"] = str(temp_dir)
        business_context["step_outputs"] = {
            f"step{i}": {"data": f"step{i}_data"} 
            for i in range(1, 9)
        }
        
        agent = ConfigAssemblerAgent(name="TestAssembler", orchestrator=orchestrator)
        result = await agent.execute(
            task="转换为 Parlant 格式",
            context=business_context
        )
        
        # 验证输出文件格式
        json_files = [f for f in result["output_files"] if f.endswith('.json')]
        yaml_files = [f for f in result["output_files"] if f.endswith('.yaml') or f.endswith('.yml')]
        
        # 至少应有 JSON 或 YAML 文件
        assert len(json_files) > 0 or len(yaml_files) > 0
        
        await agent.close()


# ============================================================================
# 跨 Agent 集成测试
# ============================================================================

class TestAgentIntegration:
    """Agent 集成测试"""
    
    @pytest.mark.asyncio
    async def test_step1_to_step3_flow(self, orchestrator, temp_dir, business_context):
        """测试 Step 1 -> Step 2 -> Step 3 流程"""
        business_context["output_dir"] = str(temp_dir)
        
        # Step 1
        step1_agent = RequirementAnalystAgent(name="Step1", orchestrator=orchestrator)
        step1_result = await step1_agent.execute(
            task="分析需求",
            context=business_context
        )
        await step1_agent.close()
        
        # Step 2 (并行)
        domain_expert = DomainExpertAgent(name="Expert", orchestrator=orchestrator)
        customer_advocate = CustomerAdvocateAgent(name="Advocate", orchestrator=orchestrator)
        
        step2_results = await asyncio.gather(
            domain_expert.execute(task="领域分析", context=business_context),
            customer_advocate.execute(task="客户分析", context=business_context)
        )
        
        await domain_expert.close()
        await customer_advocate.close()
        
        # Step 3
        business_context["step1_output"] = step1_result
        business_context["step2_output"] = step2_results
        
        coordinator = CoordinatorAgent(name="Coordinator", orchestrator=orchestrator)
        step3_result = await coordinator.execute(
            task="整合并分解任务",
            context=business_context
        )
        await coordinator.close()
        
        # 验证流程连贯性
        assert step1_result is not None
        assert step2_results is not None
        assert step3_result is not None
    
    @pytest.mark.asyncio
    async def test_all_agents_initialization(self, orchestrator):
        """测试所有 Agents 初始化"""
        agents_classes = [
            RequirementAnalystAgent,
            DomainExpertAgent,
            CustomerAdvocateAgent,
            CoordinatorAgent,
            RuleEngineerAgent,
            DomainSpecialistAgent,
            UserPortraitMinerAgent,
            QAModeratorAgent,
            ConfigAssemblerAgent,
        ]
        
        agents = []
        for agent_class in agents_classes:
            agent = agent_class(
                name=f"Test{agent_class.__name__}",
                orchestrator=orchestrator
            )
            agents.append(agent)
            assert agent is not None
        
        # 清理
        for agent in agents:
            await agent.close()


# ============================================================================
# 性能测试
# ============================================================================

class TestAgentPerformance:
    """Agent 性能测试"""
    
    @pytest.mark.asyncio
    async def test_agent_response_time(self, orchestrator, temp_dir, business_context):
        """测试 Agent 响应时间"""
        business_context["output_dir"] = str(temp_dir)
        
        import time
        
        agent = RequirementAnalystAgent(name="PerfTest", orchestrator=orchestrator)
        
        start_time = time.time()
        result = await agent.execute(
            task="快速测试",
            context=business_context
        )
        elapsed = time.time() - start_time
        
        await agent.close()
        
        # Mock 模式下应在合理时间内完成
        assert elapsed < 10.0  # 10 秒上限
        print(f"响应时间：{elapsed:.2f}秒")


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
