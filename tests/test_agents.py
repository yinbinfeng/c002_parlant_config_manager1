#!/usr/bin/env python3
"""测试所有Agent实现"""

import asyncio
import pytest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.mining_agents.agents.process_agent import ProcessAgent
from src.mining_agents.agents.glossary_agent import GlossaryAgent
from src.mining_agents.agents.quality_agent import QualityAgent
from src.mining_agents.agents.global_rules_agent import GlobalRulesAgent
from src.mining_agents.agents.config_assembler_agent import ConfigAssemblerAgent


class MockOrchestrator:
    """Mock orchestrator for testing"""
    
    def __init__(self):
        self.tools = {}
    
    def register_tool(self, tool_name, tool_instance):
        self.tools[tool_name] = tool_instance
    
    def get_tool(self, tool_name):
        if tool_name in self.tools:
            return self.tools[tool_name]
        raise ValueError(f"Tool {tool_name} not found")


class MockTool:
    """Mock tool for testing"""
    
    def __init__(self, name):
        self.name = name
    
    async def run(self, *args, **kwargs):
        return f"Mock result from {self.name}"


@pytest.fixture
def mock_orchestrator():
    """Create a mock orchestrator"""
    orchestrator = MockOrchestrator()
    orchestrator.register_tool("deep_research", MockTool("deep_research"))
    orchestrator.register_tool("json_validator", MockTool("json_validator"))
    return orchestrator


@pytest.mark.asyncio
async def test_process_agent():
    """测试ProcessAgent"""
    # 创建Agent实例
    agent = ProcessAgent(mock_mode=True)
    
    # 测试run方法
    task = "设计电商客服流程"
    context = {
        "business_desc": "电商客服系统",
        "step2_atomic_tasks": [],
        "step1_structured_requirements": {},
        "output_dir": "./output"
    }
    
    result = await agent.run(task, context)
    
    # 验证结果
    assert isinstance(result, dict)
    assert "journey_files" in result
    assert "guideline_files" in result
    assert "tool_files" in result
    assert "profile_files" in result
    assert "output_files" in result
    assert "message" in result
    assert len(result["journey_files"]) > 0
    assert len(result["guideline_files"]) > 0
    assert len(result["tool_files"]) > 0
    assert len(result["profile_files"]) > 0
    assert "Process design completed successfully" in result["message"]


@pytest.mark.asyncio
async def test_glossary_agent():
    """测试GlossaryAgent"""
    # 创建Agent实例
    agent = GlossaryAgent(mock_mode=True)
    
    # 测试run方法
    task = "提取电商客服专业术语"
    context = {
        "business_desc": "电商客服系统",
        "step2_atomic_tasks": [],
        "step1_structured_requirements": {},
        "output_dir": "./output"
    }
    
    result = await agent.run(task, context)
    
    # 验证结果
    assert isinstance(result, dict)
    assert "glossary_files" in result
    assert "output_files" in result
    assert "message" in result
    assert len(result["glossary_files"]) > 0
    assert "Glossary design completed successfully" in result["message"]


@pytest.mark.asyncio
async def test_quality_agent():
    """测试QualityAgent"""
    # 创建Agent实例
    agent = QualityAgent(mock_mode=True)
    
    # 测试run方法
    task = "检查电商客服流程质量"
    context = {
        "business_desc": "电商客服系统",
        "step2_atomic_tasks": [],
        "step1_structured_requirements": {},
        "output_dir": "./output"
    }
    
    result = await agent.run(task, context)
    
    # 验证结果
    assert isinstance(result, dict)
    assert "qa_files" in result
    assert "output_files" in result
    assert "message" in result
    assert len(result["qa_files"]) > 0
    assert "Quality check completed successfully" in result["message"]


@pytest.mark.asyncio
async def test_global_rules_agent(mock_orchestrator):
    """测试GlobalRulesAgent"""
    # 创建Agent实例
    agent = GlobalRulesAgent("GlobalRulesAgent", mock_orchestrator)
    
    # 测试execute方法
    task = "检查全局规则与各子流程规约的兼容性"
    context = {
        "business_desc": "电商客服系统",
        "step3_output_files": [],
        "step3_journey_files": [],
        "step3_glossary_files": [],
        "step1_structured_requirements": {},
        "mock_mode": True,
        "output_dir": "./output"
    }
    
    result = await agent.execute(task, context)
    
    # 验证结果
    assert isinstance(result, dict)
    assert "global_rules" in result
    assert "compatibility_report" in result
    assert "message" in result
    assert isinstance(result["global_rules"], dict)
    assert isinstance(result["compatibility_report"], dict)
    assert "Global rules check completed successfully" in result["message"]


@pytest.mark.asyncio
async def test_config_assembler_agent(mock_orchestrator):
    """测试ConfigAssemblerAgent"""
    # 创建Agent实例
    agent = ConfigAssemblerAgent("ConfigAssemblerAgent", mock_orchestrator)
    
    # 测试execute方法
    task = "组装电商客服Agent配置"
    context = {
        "business_desc": "电商客服系统",
        "step1_output": {"questions": []},
        "step2_expert_opinions": [],
        "step2_user_concerns": [],
        "step2_requirement_defense": [],
        "step3_task_breakdown": {"components": []},
        "step4_global_rules": {"rule_categories": {}, "all_rules": [], "conflict_resolution": {}},
        "step5_domain_config": {"journey_designs": [], "guideline_designs": [], "tool_definitions": [], "glossary": []},
        "step6_user_portraits": {"user_portraits": {}, "conversation_patterns": [], "common_issues": [], "pain_points": [], "optimization_suggestions": []},
        "step7_quality_report": {"overall_score": 0, "quality_level": "N/A", "issues_found": [], "recommendations": []},
        "mock_mode": True,
        "output_dir": "./output"
    }
    
    result = await agent.execute(task, context)
    
    # 验证结果
    assert isinstance(result, dict)
    assert "final_config" in result
    assert "config_files" in result
    assert "validation_result" in result
    assert "usage_guide" in result
    assert "output_files" in result
    assert "metadata" in result
    assert isinstance(result["final_config"], dict)
    assert isinstance(result["config_files"], list)
    assert isinstance(result["validation_result"], dict)
    assert isinstance(result["usage_guide"], str)
    assert isinstance(result["output_files"], list)
    assert isinstance(result["metadata"], dict)


if __name__ == "__main__":
    # 运行所有测试
    asyncio.run(test_process_agent())
    asyncio.run(test_glossary_agent())
    asyncio.run(test_quality_agent())
    asyncio.run(test_global_rules_agent(MockOrchestrator()))
    asyncio.run(test_config_assembler_agent(MockOrchestrator()))
    print("All tests passed!")
