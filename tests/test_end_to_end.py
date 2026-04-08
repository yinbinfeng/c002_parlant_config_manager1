#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端集成测试套件
测试完整的 8 步工作流程
"""

import pytest
import asyncio
from pathlib import Path
import tempfile
import shutil
import json
import yaml
from datetime import datetime


# ============================================================================
# 端到端完整流程测试
# ============================================================================

class TestEndToEndWorkflow:
    """端到端工作流测试"""
    
    @pytest.fixture
    def temp_workspace(self):
        """创建临时工作空间"""
        tmpdir = tempfile.mkdtemp()
        workspace = {
            "root": Path(tmpdir),
            "output": Path(tmpdir) / "output",
            "config": Path(tmpdir) / "config",
            "input": Path(tmpdir) / "input",
        }
        
        for dir_path in workspace.values():
            dir_path.mkdir(parents=True, exist_ok=True)
        
        yield workspace
        shutil.rmtree(tmpdir)
    
    @pytest.fixture
    def test_business_context(self):
        """测试业务上下文"""
        return {
            "business_desc": "电商客服 Agent，处理订单查询、退换货、商品咨询和投诉建议",
            "industry": "电子商务",
            "target_users": "网购消费者",
            "key_features": [
                "订单状态查询",
                "退换货处理",
                "商品信息咨询",
                "投诉建议受理",
            ],
        }
    
    @pytest.mark.asyncio
    async def test_complete_8_step_workflow(self, temp_workspace, test_business_context):
        """测试完整的 8 步工作流程"""
        
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
        
        output_dir = temp_workspace["output"]
        
        # 初始化 Orchestrator
        orchestrator = AgentOrchestrator(config={"mock_mode": True})
        orchestrator.register_tool("deep_research", DeepResearchTool(config={}, mock_mode=True))
        orchestrator.register_tool("json_validator", JsonValidator())
        
        context = {
            "business_desc": test_business_context["business_desc"],
            "mock_mode": True,
            "output_dir": str(output_dir),
            "step_outputs": {},
        }
        
        step_results = {}
        
        try:
            # ========== Step 1: 需求分析 ==========
            print("\n[Step 1/8] 需求分析...")
            agent1 = RequirementAnalystAgent(name="RequirementAnalyst", orchestrator=orchestrator)
            result1 = await agent1.execute(
                task="分析业务需求并生成澄清问题",
                context=context
            )
            await agent1.close()
            step_results["step1"] = result1
            context["step_outputs"]["step1"] = result1
            
            assert "questions" in result1
            assert len(result1["questions"]) > 0
            print(f"  ✓ 生成了 {len(result1['questions'])} 个澄清问题")
            
            # ========== Step 2: 多 Agent 辩论 ==========
            print("\n[Step 2/8] 多 Agent 辩论...")
            
            agent2a = DomainExpertAgent(name="DomainExpert", orchestrator=orchestrator)
            agent2b = CustomerAdvocateAgent(name="CustomerAdvocate", orchestrator=orchestrator)
            
            result2a, result2b = await asyncio.gather(
                agent2a.execute(task="从领域专家角度分析", context=context),
                agent2b.execute(task="从客户角度分析", context=context)
            )
            
            await agent2a.close()
            await agent2b.close()
            
            step_results["step2"] = {
                "domain_expert": result2a,
                "customer_advocate": result2b,
            }
            context["step_outputs"]["step2"] = result2a
            context["step_outputs"]["step2b"] = result2b
            
            print(f"  ✓ 完成领域专家和客户倡导双视角分析")
            
            # ========== Step 3: 任务分解 ==========
            print("\n[Step 3/8] 任务分解...")
            agent3 = CoordinatorAgent(name="Coordinator", orchestrator=orchestrator)
            result3 = await agent3.execute(
                task="整合前序结果并分解为对话流程",
                context=context
            )
            await agent3.close()
            step_results["step3"] = result3
            context["step_outputs"]["step3"] = result3
            
            assert "tasks" in result3 or "workflows" in result3
            print(f"  ✓ 生成任务分解方案")
            
            # ========== Step 4: 全局规则设计 ==========
            print("\n[Step 4/8] 全局规则设计...")
            agent4 = RuleEngineerAgent(name="RuleEngineer", orchestrator=orchestrator)
            result4 = await agent4.execute(
                task="设计全局对话规则和边界条件",
                context=context
            )
            await agent4.close()
            step_results["step4"] = result4
            context["step_outputs"]["step4"] = result4
            
            assert "rules" in result4 or "guidelines" in result4
            print(f"  ✓ 生成全局规则集")
            
            # ========== Step 5: 专项配置 ==========
            print("\n[Step 5/8] 专项配置...")
            agent5 = DomainSpecialistAgent(name="DomainSpecialist", orchestrator=orchestrator)
            result5 = await agent5.execute(
                task="定义领域特定工具和术语表",
                context=context
            )
            await agent5.close()
            step_results["step5"] = result5
            context["step_outputs"]["step5"] = result5
            
            assert "tools" in result5 or "glossary" in result5
            print(f"  ✓ 生成领域专项配置")
            
            # ========== Step 6: 私域数据挖掘 ==========
            print("\n[Step 6/8] 私域数据挖掘...")
            agent6 = UserPortraitMinerAgent(name="UserPortraitMiner", orchestrator=orchestrator)
            result6 = await agent6.execute(
                task="挖掘用户画像和对话模式",
                context=context
            )
            await agent6.close()
            step_results["step6"] = result6
            context["step_outputs"]["step6"] = result6
            
            assert "user_portraits" in result6 or "patterns" in result6
            print(f"  ✓ 完成用户画像挖掘")
            
            # ========== Step 7: 质量检查 ==========
            print("\n[Step 7/8] 质量检查...")
            agent7 = QAModeratorAgent(name="QAModerator", orchestrator=orchestrator)
            result7 = await agent7.execute(
                task="全面质量评估",
                context=context
            )
            await agent7.close()
            step_results["step7"] = result7
            context["step_outputs"]["step7"] = result7
            
            assert "quality_report" in result7 or "score" in result7
            print(f"  ✓ 完成质量评估")
            
            # ========== Step 8: 配置生成 ==========
            print("\n[Step 8/8] 配置生成...")
            agent8 = ConfigAssemblerAgent(name="ConfigAssembler", orchestrator=orchestrator)
            result8 = await agent8.execute(
                task="组装最终 Parlant 配置",
                context=context
            )
            await agent8.close()
            step_results["step8"] = result8
            context["step_outputs"]["step8"] = result8
            
            assert "config" in result8 or "parlant_config" in result8
            print(f"  ✓ 生成最终配置")
            
            # ========== 验证最终输出 ==========
            print("\n验证最终输出...")
            
            # 检查输出文件
            output_files = []
            for step_name, result in step_results.items():
                if "output_files" in result:
                    output_files.extend(result["output_files"])
            
            print(f"  总输出文件数：{len(output_files)}")
            
            # 验证配置文件存在
            config_files = [f for f in output_files 
                          if f.endswith(('.json', '.yaml', '.yml'))]
            print(f"  配置文件数：{len(config_files)}")
            
            # 验证至少有一个配置文件
            assert len(config_files) > 0, "未生成配置文件"
            
            # 验证配置文件内容
            for config_file in config_files[:1]:  # 检查第一个配置文件
                config_path = Path(config_file)
                assert config_path.exists(), f"配置文件不存在：{config_file}"
                
                if config_file.endswith('.json'):
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                    assert isinstance(config_data, dict)
                elif config_file.endswith(('.yaml', '.yml')):
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_data = yaml.safe_load(f)
                    assert isinstance(config_data, dict)
            
            print(f"  ✓ 配置文件验证通过")
            
            # ========== 生成测试报告 ==========
            report = {
                "test_name": "test_complete_8_step_workflow",
                "timestamp": datetime.now().isoformat(),
                "status": "passed",
                "steps_completed": 8,
                "total_output_files": len(output_files),
                "config_files": config_files,
                "step_summary": {
                    step_name: {
                        "status": "completed",
                        "output_count": len(result.get("output_files", []))
                    }
                    for step_name, result in step_results.items()
                }
            }
            
            report_file = output_dir / "test_report.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"\n✅ 完整工作流测试通过！")
            print(f"测试报告：{report_file}")
            
        except Exception as e:
            # 测试失败时保存错误报告
            error_report = {
                "test_name": "test_complete_8_step_workflow",
                "timestamp": datetime.now().isoformat(),
                "status": "failed",
                "error": str(e),
            }
            
            error_file = output_dir / "test_error.json"
            with open(error_file, 'w', encoding='utf-8') as f:
                json.dump(error_report, f, indent=2, ensure_ascii=False)
            
            raise
        
        finally:
            await orchestrator.cleanup()


# ============================================================================
# 分阶段集成测试
# ============================================================================

class TestPhasedIntegration:
    """分阶段集成测试"""
    
    @pytest.fixture
    def temp_dir(self):
        tmpdir = tempfile.mkdtemp()
        yield Path(tmpdir)
        shutil.rmtree(tmpdir)
    
    @pytest.mark.asyncio
    async def test_phase1_analysis(self, temp_dir):
        """阶段 1: 需求分析 + 多视角辩论"""
        from mining_agents.agents import (
            RequirementAnalystAgent,
            DomainExpertAgent,
            CustomerAdvocateAgent,
        )
        from mining_agents.managers.agent_orchestrator import AgentOrchestrator
        from mining_agents.tools.deep_research import DeepResearchTool
        from mining_agents.tools.json_validator import JsonValidator
        
        orchestrator = AgentOrchestrator(config={"mock_mode": True})
        orchestrator.register_tool("deep_research", DeepResearchTool(config={}, mock_mode=True))
        orchestrator.register_tool("json_validator", JsonValidator())
        
        context = {
            "business_desc": "测试业务",
            "mock_mode": True,
            "output_dir": str(temp_dir),
        }
        
        try:
            # Step 1
            agent1 = RequirementAnalystAgent(name="Analyst", orchestrator=orchestrator)
            result1 = await agent1.execute(task="分析需求", context=context)
            await agent1.close()
            
            # Step 2
            agent2a = DomainExpertAgent(name="Expert", orchestrator=orchestrator)
            agent2b = CustomerAdvocateAgent(name="Advocate", orchestrator=orchestrator)
            
            results = await asyncio.gather(
                agent2a.execute(task="领域分析", context=context),
                agent2b.execute(task="客户分析", context=context)
            )
            
            await agent2a.close()
            await agent2b.close()
            
            # 验证
            assert "questions" in result1
            assert len(results) == 2
            
        finally:
            await orchestrator.cleanup()
    
    @pytest.mark.asyncio
    async def test_phase2_planning(self, temp_dir):
        """阶段 2: 任务分解 + 规则设计"""
        from mining_agents.agents import (
            CoordinatorAgent,
            RuleEngineerAgent,
        )
        from mining_agents.managers.agent_orchestrator import AgentOrchestrator
        from mining_agents.tools.deep_research import DeepResearchTool
        from mining_agents.tools.json_validator import JsonValidator
        
        orchestrator = AgentOrchestrator(config={"mock_mode": True})
        orchestrator.register_tool("deep_research", DeepResearchTool(config={}, mock_mode=True))
        orchestrator.register_tool("json_validator", JsonValidator())
        
        context = {
            "business_desc": "测试业务",
            "mock_mode": True,
            "output_dir": str(temp_dir),
            "step_outputs": {
                "step1": {"questions": ["测试问题"]},
                "step2": {"analysis": "测试分析"},
            },
        }
        
        try:
            # Step 3
            agent3 = CoordinatorAgent(name="Coordinator", orchestrator=orchestrator)
            result3 = await agent3.execute(task="分解任务", context=context)
            await agent3.close()
            
            # Step 4
            agent4 = RuleEngineerAgent(name="RuleEngineer", orchestrator=orchestrator)
            result4 = await agent4.execute(task="设计规则", context=context)
            await agent4.close()
            
            # 验证
            assert result3 is not None
            assert result4 is not None
            
        finally:
            await orchestrator.cleanup()
    
    @pytest.mark.asyncio
    async def test_phase3_configuration(self, temp_dir):
        """阶段 3: 专项配置 + 数据挖掘"""
        from mining_agents.agents import (
            DomainSpecialistAgent,
            UserPortraitMinerAgent,
        )
        from mining_agents.managers.agent_orchestrator import AgentOrchestrator
        from mining_agents.tools.deep_research import DeepResearchTool
        from mining_agents.tools.json_validator import JsonValidator
        
        orchestrator = AgentOrchestrator(config={"mock_mode": True})
        orchestrator.register_tool("deep_research", DeepResearchTool(config={}, mock_mode=True))
        orchestrator.register_tool("json_validator", JsonValidator())
        
        context = {
            "business_desc": "测试业务",
            "mock_mode": True,
            "output_dir": str(temp_dir),
            "step_outputs": {
                f"step{i}": {"data": f"step{i}"}
                for i in range(1, 5)
            },
        }
        
        try:
            # Step 5
            agent5 = DomainSpecialistAgent(name="Specialist", orchestrator=orchestrator)
            result5 = await agent5.execute(task="专项配置", context=context)
            await agent5.close()
            
            # Step 6
            agent6 = UserPortraitMinerAgent(name="Miner", orchestrator=orchestrator)
            result6 = await agent6.execute(task="数据挖掘", context=context)
            await agent6.close()
            
            # 验证
            assert result5 is not None
            assert result6 is not None
            
        finally:
            await orchestrator.cleanup()
    
    @pytest.mark.asyncio
    async def test_phase4_finalization(self, temp_dir):
        """阶段 4: 质量检查 + 配置生成"""
        from mining_agents.agents import (
            QAModeratorAgent,
            ConfigAssemblerAgent,
        )
        from mining_agents.managers.agent_orchestrator import AgentOrchestrator
        from mining_agents.tools.deep_research import DeepResearchTool
        from mining_agents.tools.json_validator import JsonValidator
        
        orchestrator = AgentOrchestrator(config={"mock_mode": True})
        orchestrator.register_tool("deep_research", DeepResearchTool(config={}, mock_mode=True))
        orchestrator.register_tool("json_validator", JsonValidator())
        
        context = {
            "business_desc": "测试业务",
            "mock_mode": True,
            "output_dir": str(temp_dir),
            "step_outputs": {
                f"step{i}": {"data": f"step{i}"}
                for i in range(1, 9)
            },
        }
        
        try:
            # Step 7
            agent7 = QAModeratorAgent(name="Moderator", orchestrator=orchestrator)
            result7 = await agent7.execute(task="质量检查", context=context)
            await agent7.close()
            
            # Step 8
            agent8 = ConfigAssemblerAgent(name="Assembler", orchestrator=orchestrator)
            result8 = await agent8.execute(task="配置生成", context=context)
            await agent8.close()
            
            # 验证配置生成
            assert result7 is not None
            assert result8 is not None
            
            # 验证有配置文件生成
            config_files = [f for f in result8.get("output_files", [])
                          if f.endswith(('.json', '.yaml'))]
            assert len(config_files) > 0
            
        finally:
            await orchestrator.cleanup()


# ============================================================================
# 数据流测试
# ============================================================================

class TestDataFlow:
    """数据流测试"""
    
    @pytest.fixture
    def temp_dir(self):
        tmpdir = tempfile.mkdtemp()
        yield Path(tmpdir)
        shutil.rmtree(tmpdir)
    
    @pytest.mark.asyncio
    async def test_data_propagation(self, temp_dir):
        """测试数据在 8 个步骤中的传递"""
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
        
        orchestrator = AgentOrchestrator(config={"mock_mode": True})
        orchestrator.register_tool("deep_research", DeepResearchTool(config={}, mock_mode=True))
        orchestrator.register_tool("json_validator", JsonValidator())
        
        initial_context = {
            "business_desc": "数据流测试业务",
            "mock_mode": True,
            "output_dir": str(temp_dir),
            "step_outputs": {},
        }
        
        agents_sequence = [
            ("Step1", RequirementAnalystAgent),
            ("Step2a", DomainExpertAgent),
            ("Step2b", CustomerAdvocateAgent),
            ("Step3", CoordinatorAgent),
            ("Step4", RuleEngineerAgent),
            ("Step5", DomainSpecialistAgent),
            ("Step6", UserPortraitMinerAgent),
            ("Step7", QAModeratorAgent),
            ("Step8", ConfigAssemblerAgent),
        ]
        
        context = initial_context.copy()
        context["step_outputs"] = {}
        
        agents_instances = []
        
        try:
            for step_name, agent_class in agents_sequence:
                # 更新上下文
                context["current_step"] = step_name
                
                # 创建并执行 Agent
                agent = agent_class(name=step_name, orchestrator=orchestrator)
                agents_instances.append(agent)
                
                result = await agent.execute(
                    task=f"执行{step_name}",
                    context=context
                )
                
                # 存储结果到上下文供下一步使用
                step_key = step_name.replace("Step", "step").lower()
                context["step_outputs"][step_key] = result
                
                # 验证当前步骤输出
                assert result is not None, f"{step_name} 未返回结果"
            
            # 验证所有步骤的输出都已传递
            assert len(context["step_outputs"]) == 8
            
            # 验证最终配置包含所有步骤的信息
            final_result = context["step_outputs"]["step8"]
            assert "config" in final_result or "parlant_config" in final_result
            
        finally:
            # 清理所有 Agents
            for agent in agents_instances:
                await agent.close()
            
            await orchestrator.cleanup()


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
