#!/usr/bin/env python3
"""Agent 编排器 - 负责 Agent 初始化、任务分发和结果收集"""

from typing import Dict, Any, List, Optional, Type
from pathlib import Path
import importlib
import asyncio

from ..utils.logger import logger


class AgentOrchestrator:
    """Agent 编排器 - 负责 Agent 初始化、任务分发和结果收集
    
    主要职责：
    - Agent 初始化：根据配置动态加载和初始化 Agent 实例
    - 工具管理：注册和管理所有可用工具
    - 任务分发：将任务分发给对应的 Agent 执行
    - 结果收集：收集和管理 Agent 执行结果
    """
    
    def __init__(self, config: dict):
        """初始化 Agent 编排器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.logger = logger
        
        # 已初始化的 Agent 实例
        self.agents: Dict[str, Any] = {}
        
        # 工具实例
        self.tools: Dict[str, Any] = {}
        
        # Agent 类型到模块名的映射
        # TODO: 这个命名外部一旦一改，这里就失效了，得考虑其它方案映射
        self.agent_module_map = {
            "RequirementAnalystAgent": "requirement_analyst_agent",
            "CoordinatorAgent": "coordinator_agent",
            "ProcessAgent": "process_agent",
            "GlossaryAgent": "glossary_agent",
            "QualityAgent": "quality_agent",
            "GlobalRulesAgent": "global_rules_agent",
            "ConfigAssemblerAgent": "config_assembler_agent",
        }
    
    def register_tool(self, tool_name: str, tool_instance: Any):
        """注册工具
        
        Args:
            tool_name: 工具名称
            tool_instance: 工具实例
        """
        self.tools[tool_name] = tool_instance
        self.logger.info(f"Tool '{tool_name}' registered")
    
    def get_tool(self, tool_name: str) -> Any:
        """获取工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            工具实例
            
        Raises:
            ValueError: 工具未注册
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not registered")
        return self.tools[tool_name]
    
    def list_tools(self) -> List[str]:
        """列出所有已注册的工具
        
        Returns:
            工具名称列表
        """
        return list(self.tools.keys())
    
    async def initialize_agent(
        self, 
        agent_type: str, 
        agent_name: str, 
        **kwargs
    ) -> Any:
        """初始化 Agent
        
        Args:
            agent_type: Agent 类型（如 "RequirementAnalystAgent"）
            agent_name: Agent 实例名称
            **kwargs: 初始化参数
            
        Returns:
            Agent 实例
            
        Raises:
            ImportError: Agent 类不存在
            ValueError: Agent 类型未知
        """
        self.logger.info(f"Initializing agent '{agent_name}' ({agent_type})...")
        
        # 获取模块名
        module_name = self.agent_module_map.get(agent_type)
        if not module_name:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        # 动态导入模块
        try:
            module_path = f"..agents.{module_name}"
            module = importlib.import_module(module_path, package=__package__)
        except ImportError as e:
            self.logger.error(f"Failed to import module: {e}")
            raise
        
        # 获取 Agent 类
        agent_class = getattr(module, agent_type, None)
        if not agent_class:
            raise ImportError(f"Class {agent_type} not found in module {module_path}")
        
        # 初始化 Agent
        try:
            agent = agent_class(name=agent_name, orchestrator=self, **kwargs)
            self.agents[agent_name] = agent
            self.logger.info(f"Agent '{agent_name}' ({agent_type}) initialized successfully")
            return agent
        except Exception as e:
            self.logger.error(f"Failed to initialize agent: {e}")
            raise
    
    async def execute_agent(
        self, 
        agent_name: str, 
        task: str, 
        context: dict = None
    ) -> dict:
        """执行 Agent 任务
        
        Args:
            agent_name: Agent 实例名称
            task: 任务描述
            context: 上下文信息
            
        Returns:
            Agent 执行结果
            
        Raises:
            ValueError: Agent 未初始化
        """
        if agent_name not in self.agents:
            raise ValueError(f"Agent '{agent_name}' not initialized")
        
        agent = self.agents[agent_name]
        
        self.logger.info(f"Executing agent '{agent_name}' with task: {task[:50]}...")
        
        # 调用 Agent 的 execute 方法
        try:
            result = await agent.execute(task, context or {})
            self.logger.info(f"Agent '{agent_name}' execution completed")
            return result
        except Exception as e:
            self.logger.error(f"Agent '{agent_name}' execution failed: {e}")
            raise
    
    async def execute_agents_parallel(
        self, 
        tasks: List[Dict[str, Any]]
    ) -> List[dict]:
        """并行执行多个 Agent 任务
        
        Args:
            tasks: 任务列表，每项包含：
                - agent_name: Agent 名称
                - task: 任务描述
                - context: 上下文信息（可选）
            
        Returns:
            Agent 执行结果列表
        """
        self.logger.info(f"Executing {len(tasks)} agents in parallel")
        
        # 创建所有任务
        coroutines = []
        for task_info in tasks:
            coro = self.execute_agent(
                agent_name=task_info["agent_name"],
                task=task_info["task"],
                context=task_info.get("context", {})
            )
            coroutines.append(coro)
        
        # 并行执行
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        
        # 处理结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Task {i} failed: {result}")
                processed_results.append({"error": str(result)})
            else:
                processed_results.append(result)
        
        return processed_results
    
    def list_agents(self) -> List[str]:
        """列出所有已初始化的 Agent
        
        Returns:
            Agent 名称列表
        """
        return list(self.agents.keys())
    
    async def cleanup(self):
        """清理资源"""
        self.logger.info("Cleaning up resources...")
        
        # 关闭所有 Agent
        for agent_name, agent in self.agents.items():
            if hasattr(agent, 'close'):
                try:
                    await agent.close()
                    self.logger.info(f"Agent '{agent_name}' closed")
                except Exception as e:
                    self.logger.error(f"Error closing agent '{agent_name}': {e}")
        
        # 关闭所有工具
        for tool_name, tool in self.tools.items():
            if hasattr(tool, 'close'):
                try:
                    await tool.close()
                    self.logger.info(f"Tool '{tool_name}' closed")
                except Exception as e:
                    self.logger.error(f"Error closing tool '{tool_name}': {e}")
        
        self.logger.info("Cleanup completed")
