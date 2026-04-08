#!/usr/bin/env python3
"""MVP 版本测试套件"""

import pytest
import asyncio
import os
import sys
from pathlib import Path
import tempfile
import shutil


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
def sample_config():
    """示例配置"""
    return {
        "max_parallel_agents": 4,
        "start_step": 1,
        "end_step": 8,
        "force_rerun": False,
        "continue_on_error": False,
        "output_base_dir": "./output",
    }


@pytest.fixture
def sample_business_desc():
    """示例业务描述"""
    return "电商客服 Agent，处理订单查询、退换货和商品咨询"


# ============================================================================
# Test Tools
# ============================================================================

class TestJsonValidator:
    """测试 JSON 校验工具"""
    
    def test_validate_valid_json(self):
        """测试验证有效的 JSON"""
        from mining_agents.tools.json_validator import JsonValidator
        
        validator = JsonValidator()
        success, data, msg = validator.validate('{"key": "value", "number": 123}')
        
        assert success is True
        assert data == {"key": "value", "number": 123}
        assert msg == ""
    
    def test_validate_invalid_json(self):
        """测试验证无效的 JSON"""
        from mining_agents.tools.json_validator import JsonValidator
        
        validator = JsonValidator()
        # 缺少闭合括号
        success, data, msg = validator.validate('{"key": "value"')
        
        # 应该能够修复或报错
        assert isinstance(success, bool)
    
    def test_save_and_load_json(self, temp_dir):
        """测试保存和加载 JSON"""
        from mining_agents.tools.json_validator import JsonValidator
        
        validator = JsonValidator()
        test_data = {"name": "测试", "value": 123}
        file_path = temp_dir / "test.json"
        
        # 保存
        success = validator.save_json(test_data, str(file_path))
        assert success is True
        assert file_path.exists()
        
        # 加载
        success, loaded_data, msg = validator.load_json(str(file_path))
        assert success is True
        assert loaded_data == test_data
    
    def test_validate_schema(self):
        """测试 Schema 验证"""
        from mining_agents.tools.json_validator import JsonValidator
        
        validator = JsonValidator()
        data = {"name": "test", "age": 25}
        schema = {"name": str, "age": int}
        required_fields = ["name", "age"]
        
        success, msg = validator.validate_schema(data, schema, required_fields)
        assert success is True
        assert msg == ""
        
        # 缺少必需字段
        data_incomplete = {"name": "test"}
        success, msg = validator.validate_schema(data_incomplete, schema, required_fields)
        assert success is False
        assert "Missing required field" in msg


class TestDeepResearchTool:
    """测试 Deep Research 工具"""
    
    @pytest.mark.asyncio
    async def test_mock_search(self):
        """测试 Mock 搜索"""
        from mining_agents.tools.deep_research import DeepResearchTool
        
        tool = DeepResearchTool(config={}, mock_mode=True)
        result = await tool.search("测试查询")
        
        assert isinstance(result, str)
        assert "测试查询" in result or "Mock" in result
        assert len(result) > 50  # 应该返回一定长度的报告
        
        await tool.close()
    
    @pytest.mark.asyncio
    async def test_mock_mode_initialization(self):
        """测试 Mock 模式初始化"""
        from mining_agents.tools.deep_research import DeepResearchTool
        
        tool = DeepResearchTool(config={}, mock_mode=True)
        
        assert tool.mock_mode is True
        assert tool.config == {}
        
        await tool.close()

    def test_force_utf8_stdio_on_init(self, monkeypatch):
        """初始化时应强制配置 UTF-8 I/O，避免 Windows GBK 编码崩溃。"""
        from mining_agents.tools.deep_research import DeepResearchTool

        class _FakeStream:
            def __init__(self):
                self.calls = []

            def reconfigure(self, **kwargs):
                self.calls.append(kwargs)

        fake_stdout = _FakeStream()
        fake_stderr = _FakeStream()
        monkeypatch.setattr(sys, "stdout", fake_stdout)
        monkeypatch.setattr(sys, "stderr", fake_stderr)
        monkeypatch.delenv("PYTHONUTF8", raising=False)
        monkeypatch.delenv("PYTHONIOENCODING", raising=False)

        _ = DeepResearchTool(config={}, mock_mode=True)

        assert os.environ["PYTHONUTF8"] == "1"
        assert os.environ["PYTHONIOENCODING"] == "utf-8"
        assert fake_stdout.calls[-1] == {
            "encoding": "utf-8",
            "errors": "backslashreplace",
        }
        assert fake_stderr.calls[-1] == {
            "encoding": "utf-8",
            "errors": "backslashreplace",
        }

    def test_extract_text_from_blocks_handles_dict_and_object(self):
        """DeepResearchAgent 应兼容 dict/TextBlock 两种返回结构。"""
        from mining_agents.tools.deep_research_agent.deep_research_agent import (
            DeepResearchAgent,
        )

        class _BlockObj:
            def __init__(self, text: str):
                self.text = text

        assert (
            DeepResearchAgent._extract_text_from_blocks(
                [{"type": "text", "text": "dict-text"}],
            )
            == "dict-text"
        )
        assert (
            DeepResearchAgent._extract_text_from_blocks(
                [_BlockObj("obj-text")],
            )
            == "obj-text"
        )


# ============================================================================
# Test Managers
# ============================================================================

class TestStepManager:
    """测试 StepManager"""
    
    def test_initialization(self, temp_dir, sample_config):
        """测试初始化"""
        from mining_agents.managers.step_manager import StepManager
        import yaml
        
        # 创建临时配置文件
        config_file = temp_dir / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(sample_config, f)
        
        output_dir = temp_dir / "output"
        manager = StepManager(str(config_file), str(output_dir))
        
        assert manager.config_path == config_file
        assert manager.output_base_dir == output_dir
        assert manager.config["max_parallel_agents"] == 4
    
    def test_step_status_tracking(self, temp_dir, sample_config):
        """测试步骤状态跟踪"""
        from mining_agents.managers.step_manager import StepManager
        import yaml
        
        # 创建临时配置文件
        config_file = temp_dir / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(sample_config, f)
        
        output_dir = temp_dir / "output"
        manager = StepManager(str(config_file), str(output_dir))
        
        # 初始状态应为未完成
        assert not manager.is_step_completed(1)
        
        # 标记开始
        manager.mark_step_started(1)
        assert manager.step_status[1] == "running"
        
        # 标记完成
        manager.mark_step_completed(1, ["file1.md", "file2.json"])
        assert manager.step_status[1] == "completed"
        assert manager.is_step_completed(1)
        
        # 验证状态文件
        status_file = output_dir / "step1" / "status.json"
        assert status_file.exists()
    
    def test_rerun_skip_logic(self, temp_dir, sample_config):
        """测试重跑跳过逻辑"""
        from mining_agents.managers.step_manager import StepManager
        import yaml
        
        # 创建临时配置文件
        config_file = temp_dir / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(sample_config, f)
        
        output_dir = temp_dir / "output"
        manager = StepManager(str(config_file), str(output_dir))
        
        # 第一次运行
        manager.mark_step_started(1)
        manager.mark_step_completed(1)
        
        # 第二次运行应跳过
        assert manager.is_step_completed(1)
        
        # 强制重跑模式
        manager.config["force_rerun"] = True
        assert not manager.is_step_completed(1)  # 应返回 False
    
    @pytest.mark.asyncio
    async def test_run_step_with_handler(self, temp_dir, sample_config):
        """测试运行步骤"""
        from mining_agents.managers.step_manager import StepManager
        import yaml
        
        # 创建临时配置文件
        config_file = temp_dir / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(sample_config, f)
        
        output_dir = temp_dir / "output"
        manager = StepManager(str(config_file), str(output_dir))
        
        # 注册处理器
        async def mock_handler(context):
            return {
                "output_files": ["test.md"],
                "metadata": {"test": True}
            }
        
        manager.register_step_handler(1, mock_handler)
        
        # 运行步骤
        context = {"business_desc": "测试业务"}
        result = await manager.run_step(1, context)
        
        assert result is not None
        assert "test.md" in result["output_files"]
        assert manager.step_status[1] == "completed"


class TestAgentOrchestrator:
    """测试 AgentOrchestrator"""
    
    @pytest.mark.asyncio
    async def test_tool_registration(self):
        """测试工具注册"""
        from mining_agents.managers.agent_orchestrator import AgentOrchestrator
        
        orchestrator = AgentOrchestrator(config={})
        
        # 注册 Mock 工具
        mock_tool = {"name": "mock_tool"}
        orchestrator.register_tool("mock", mock_tool)
        
        # 获取工具
        tool = orchestrator.get_tool("mock")
        assert tool == mock_tool
        
        # 列出工具
        tools = orchestrator.list_tools()
        assert "mock" in tools
    
    @pytest.mark.asyncio
    async def test_get_unregistered_tool(self):
        """测试获取未注册的工具"""
        from mining_agents.managers.agent_orchestrator import AgentOrchestrator
        
        orchestrator = AgentOrchestrator(config={})
        
        with pytest.raises(ValueError, match="not registered"):
            orchestrator.get_tool("nonexistent")
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, temp_dir):
        """测试 Agent 初始化"""
        from mining_agents.managers.agent_orchestrator import AgentOrchestrator
        from mining_agents.tools.deep_research import DeepResearchTool
        from mining_agents.tools.json_validator import JsonValidator
        
        orchestrator = AgentOrchestrator(config={"mock_mode": True})
        
        # 注册必需的工具
        orchestrator.register_tool("deep_research", DeepResearchTool(config={}, mock_mode=True))
        orchestrator.register_tool("json_validator", JsonValidator())
        
        # 初始化 Agent
        agent = await orchestrator.initialize_agent(
            agent_type="RequirementAnalystAgent",
            agent_name="TestAnalyst"
        )
        
        assert agent.name == "TestAnalyst"
        assert "TestAnalyst" in orchestrator.agents
        
        # 清理
        await orchestrator.cleanup()
    
    @pytest.mark.asyncio
    async def test_execute_agent(self, temp_dir):
        """测试执行 Agent"""
        from mining_agents.managers.agent_orchestrator import AgentOrchestrator
        from mining_agents.tools.deep_research import DeepResearchTool
        from mining_agents.tools.json_validator import JsonValidator
        
        orchestrator = AgentOrchestrator(config={"mock_mode": True})
        
        # 注册工具
        orchestrator.register_tool("deep_research", DeepResearchTool(config={}, mock_mode=True))
        orchestrator.register_tool("json_validator", JsonValidator())
        
        # 初始化 Agent
        await orchestrator.initialize_agent(
            agent_type="RequirementAnalystAgent",
            agent_name="TestAnalyst"
        )
        
        # 执行任务
        result = await orchestrator.execute_agent(
            agent_name="TestAnalyst",
            task="生成澄清问题",
            context={
                "business_desc": "测试业务",
                "mock_mode": True,
                "output_dir": str(temp_dir)
            }
        )
        
        assert "questions" in result
        assert "output_files" in result
        assert len(result["questions"]) > 0
        
        # 清理
        await orchestrator.cleanup()


# ============================================================================
# Test Agents
# ============================================================================

class TestRequirementAnalystAgent:
    """测试 RequirementAnalystAgent"""
    
    @pytest.mark.asyncio
    async def test_mock_question_generation(self, temp_dir):
        """测试 Mock 问题生成"""
        from mining_agents.agents.requirement_analyst_agent import RequirementAnalystAgent
        from mining_agents.managers.agent_orchestrator import AgentOrchestrator
        from mining_agents.tools.deep_research import DeepResearchTool
        from mining_agents.tools.json_validator import JsonValidator
        
        # 设置 Orchestrator
        orchestrator = AgentOrchestrator(config={"mock_mode": True})
        orchestrator.register_tool("deep_research", DeepResearchTool(config={}, mock_mode=True))
        orchestrator.register_tool("json_validator", JsonValidator())
        
        # 创建 Agent
        agent = RequirementAnalystAgent(name="TestAgent", orchestrator=orchestrator)
        
        # 执行任务
        result = await agent.execute(
            task="Generate questions",
            context={
                "business_desc": "电商客服 Agent",
                "mock_mode": True,
                "output_dir": str(temp_dir)
            }
        )
        
        # 验证结果
        assert len(result["questions"]) > 0
        assert len(result["output_files"]) >= 1
        assert result["metadata"]["question_count"] > 0
        assert result["metadata"]["mock_mode"] is True
        
        # 验证文件已创建
        for file_path in result["output_files"]:
            assert Path(file_path).exists()
        
        # 清理
        await agent.close()
    
    @pytest.mark.asyncio
    async def test_question_format(self, temp_dir):
        """测试问题格式"""
        from mining_agents.agents.requirement_analyst_agent import RequirementAnalystAgent
        from mining_agents.managers.agent_orchestrator import AgentOrchestrator
        from mining_agents.tools.deep_research import DeepResearchTool
        from mining_agents.tools.json_validator import JsonValidator
        
        # 设置 Orchestrator
        orchestrator = AgentOrchestrator(config={"mock_mode": True})
        orchestrator.register_tool("deep_research", DeepResearchTool(config={}, mock_mode=True))
        orchestrator.register_tool("json_validator", JsonValidator())
        
        # 创建 Agent
        agent = RequirementAnalystAgent(name="TestAgent", orchestrator=orchestrator)
        
        # 执行任务
        result = await agent.execute(
            task="Generate questions",
            context={
                "business_desc": "测试业务描述",
                "mock_mode": True,
                "output_dir": str(temp_dir)
            }
        )
        
        # 验证问题结构
        for question in result["questions"]:
            assert "id" in question
            assert "question" in question
            assert "category" in question
            assert "priority" in question
            assert question["priority"] in ["high", "medium", "low"]
        
        # 验证 Markdown 文件格式
        md_file = Path(result["output_files"][0])
        content = md_file.read_text(encoding='utf-8')
        assert "# Step 1: 需求澄清问题清单" in content
        assert "您的回答" in content
        
        # 清理
        await agent.close()


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_step1(self, temp_dir):
        """测试端到端的 Step 1 流程"""
        from mining_agents.managers.step_manager import StepManager
        from mining_agents.managers.agent_orchestrator import AgentOrchestrator
        from mining_agents.tools.deep_research import DeepResearchTool
        from mining_agents.tools.json_validator import JsonValidator
        import yaml
        
        # 创建配置文件
        config = {
            "max_parallel_agents": 4,
            "start_step": 1,
            "end_step": 1,
            "force_rerun": False,
        }
        config_file = temp_dir / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        output_dir = temp_dir / "output"
        
        # 创建 StepManager
        step_manager = StepManager(str(config_file), str(output_dir))
        
        # 创建 Orchestrator
        orchestrator = AgentOrchestrator(config={"mock_mode": True})
        orchestrator.register_tool("deep_research", DeepResearchTool(config={}, mock_mode=True))
        orchestrator.register_tool("json_validator", JsonValidator())
        
        # 注册 Step 1 处理器
        async def step1_handler(context):
            from mining_agents.agents.requirement_analyst_agent import RequirementAnalystAgent
            
            agent = await orchestrator.initialize_agent(
                agent_type="RequirementAnalystAgent",
                agent_name="RequirementAnalyst"
            )
            
            result = await orchestrator.execute_agent(
                agent_name="RequirementAnalyst",
                task="分析需求并生成澄清问题",
                context={
                    "business_desc": context.get("business_desc", ""),
                    "mock_mode": True,
                }
            )
            
            return result
        
        step_manager.register_step_handler(1, step1_handler)
        
        # 运行步骤
        context = {"business_desc": "电商客服 Agent"}
        result = await step_manager.run_step(1, context)
        
        # 验证
        assert result is not None
        assert step_manager.is_step_completed(1)
        
        # 验证输出文件
        step1_dir = step_manager.get_step_output_dir(1)
        questions_file = step1_dir / "step1_clarification_questions.md"
        assert questions_file.exists()
        
        content = questions_file.read_text(encoding='utf-8')
        assert "需求澄清问题清单" in content
        assert "电商客服 Agent" in content
        
        # 清理
        await orchestrator.cleanup()


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
