# Mining Agents MVP 版本设计文档

**版本**: v1.0 (MVP 版)  
**创建日期**: 2026-03-20  
**最后更新**: 2026-03-20  

---

## 一、MVP 目标

### 1.1 核心目标

实现一个最小可行版本（MVP），验证系统架构的可行性，重点完成：

1. **工具服务层** - 基于 AgentScope 的 DeepResearchAgent 封装
2. **核心管理器** - StepManager 和 AgentOrchestrator
3. **Step 1 示例** - RequirementAnalystAgent 完整流程

### 1.2 不包含的内容

- Step 2-8 的 Agent 实现
- 实际的 LLM API 调用（使用 Mock）
- 多 Agent 辩论机制
- 边缘情况分析
- 用户画像挖掘
- 复杂的并发控制

---

## 二、系统架构

### 2.1 MVP 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      用户输入层                               │
│  ┌─────────────┐    ┌──────────────┐                        │
│  │ 业务描述文本 │    │ 配置参数 YAML │                        │
│  └─────────────┘    └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   AgentScope 编排层                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              StepManager                              │  │
│  │   - 步骤调度  - 状态持久化  - 断点续跑                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                              ↓                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           AgentOrchestrator                           │  │
│  │   - Agent 初始化  - 任务分发  - 结果收集               │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Agent 协作层（仅 Step 1）                   │
│                                                              │
│  Step 1: RequirementAnalystAgent                             │
│  - 需求分析 + Deep Research 搜索                              │
│  - 输出待澄清问题清单                                         │
│  - 人工确认环节（Mock）                                       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    工具服务层                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │DeepSearch│  │FileSystem│  │JsonRepair│                  │
│  │(AgentScope)│ │(本地文件) │ │(格式校验) │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    输出产物层                                 │
│  - step1_clarification_questions.md                         │
│  - step1_user_feedback.json (Mock)                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 三、核心组件设计

### 3.1 工具服务层

#### 3.1.1 DeepResearchAgent 封装

**文件**: `src/mining_agents/tools/deep_research.py`

```python
from agentscope.agent import DeepResearchAgent
from agentscope.model import DashScopeChatModel
from agentscope.memory import InMemoryMemory
from agentscope.mcp import StdIOStatefulClient

class DeepResearchTool:
    """Deep Research 工具封装"""
    
    def __init__(self, config: dict):
        """初始化工具
        
        Args:
            config: 配置字典，包含：
                - dashscope_api_key: DashScope API Key
                - tavily_api_key: Tavily API Key
                - max_depth: 最大搜索深度（默认 3）
                - max_iters: 最大迭代次数（默认 30）
        """
        # 初始化 DashScope 模型
        self.model = DashScopeChatModel(
            model_name="qwen3-max",
            api_key=config.get("dashscope_api_key"),
            temperature=0.7,
        )
        
        # 初始化 Tavily MCP 客户端
        self.tavily_client = StdIOStatefulClient(
            name="tavily_mcp",
            command="npx",
            args=["-y", "tavily-mcp@latest"],
            env={"TAVILY_API_KEY": config.get("tavily_api_key")},
        )
        await self.tavily_client.connect()
        
        # 初始化 DeepResearchAgent
        self.agent = DeepResearchAgent(
            name="DeepResearchWorker",
            model=self.model,
            memory=InMemoryMemory(),
            search_mcp_client=self.tavily_client,
            max_depth=config.get("max_depth", 3),
            max_iters=config.get("max_iters", 30),
        )
    
    async def search(self, query: str) -> str:
        """执行深度搜索
        
        Args:
            query: 搜索查询
            
        Returns:
            综合研究报告（结构化文本）
        """
        result = await self.agent(Msg("user", query, "user"))
        return result.get_text_content()
    
    async def close(self):
        """关闭资源"""
        await self.tavily_client.disconnect()
```

#### 3.1.2 JSON 校验工具

**文件**: `src/mining_agents/tools/json_validator.py`

```python
import json
from json_repair import repair_json
from typing import Any, Tuple

class JsonValidator:
    """JSON 格式校验工具"""
    
    @staticmethod
    def validate(json_string: str) -> Tuple[bool, Any, str]:
        """验证并修复 JSON 字符串
        
        Args:
            json_string: JSON 字符串
            
        Returns:
            (是否成功，解析后的对象，错误信息)
        """
        try:
            # 尝试直接解析
            data = json.loads(json_string)
            return True, data, ""
        except json.JSONDecodeError as e:
            # 尝试修复
            try:
                repaired = repair_json(json_string)
                data = json.loads(repaired)
                return True, data, "JSON was malformed but repaired successfully"
            except Exception as repair_error:
                return False, None, f"JSON validation failed: {str(e)}, repair also failed: {str(repair_error)}"
    
    @staticmethod
    def save_json(data: Any, file_path: str, indent: int = 2) -> bool:
        """保存 JSON 文件
        
        Args:
            data: 数据对象
            file_path: 文件路径
            indent: 缩进空格数
            
        Returns:
            是否成功
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Failed to save JSON: {e}")
            return False
```

### 3.2 核心管理器

#### 3.2.1 StepManager

**文件**: `src/mining_agents/managers/step_manager.py`

```python
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from ..utils.logger import setup_logger, get_step_logger
from ..utils.file_utils import write_json, read_json, write_markdown, ensure_dir

class StepManager:
    """步骤管理器 - 负责步骤调度与状态管理"""
    
    def __init__(self, config_path: str, output_base_dir: str):
        """初始化步骤管理器
        
        Args:
            config_path: 配置文件路径
            output_base_dir: 输出基础目录
        """
        self.config_path = Path(config_path)
        self.output_base_dir = Path(output_base_dir)
        self.logger = setup_logger("StepManager", verbose=True)
        
        # 确保输出目录存在
        ensure_dir(str(self.output_base_dir))
        
        # 步骤状态存储
        self.step_status: Dict[int, str] = {}  # step_num -> status
    
    def get_step_output_dir(self, step_num: int) -> Path:
        """获取步骤输出目录"""
        return ensure_dir(self.output_base_dir / f"step{step_num}")
    
    def is_step_completed(self, step_num: int) -> bool:
        """检查步骤是否已完成
        
        Args:
            step_num: 步骤编号
            
        Returns:
            是否已完成
        """
        # 检查是否存在该步骤的输出文件
        step_dir = self.get_step_output_dir(step_num)
        status_file = step_dir / "status.json"
        
        if not status_file.exists():
            return False
        
        status_data = read_json(str(status_file))
        return status_data.get("status") == "completed"
    
    def mark_step_started(self, step_num: int):
        """标记步骤已开始"""
        step_dir = self.get_step_output_dir(step_num)
        status_file = step_dir / "status.json"
        
        status_data = {
            "step_num": step_num,
            "status": "running",
            "started_at": datetime.now().isoformat(),
        }
        write_json(status_data, str(status_file))
        self.step_status[step_num] = "running"
        self.logger.info(f"Step {step_num} started")
    
    def mark_step_completed(self, step_num: int, output_files: list = None):
        """标记步骤已完成
        
        Args:
            step_num: 步骤编号
            output_files: 输出文件列表
        """
        step_dir = self.get_step_output_dir(step_num)
        status_file = step_dir / "status.json"
        
        status_data = {
            "step_num": step_num,
            "status": "completed",
            "started_at": read_json(str(status_file)).get("started_at") if status_file.exists() else None,
            "completed_at": datetime.now().isoformat(),
            "output_files": output_files or [],
        }
        write_json(status_data, str(status_file))
        self.step_status[step_num] = "completed"
        self.logger.info(f"Step {step_num} completed")
    
    def mark_step_failed(self, step_num: int, error_message: str):
        """标记步骤失败"""
        step_dir = self.get_step_output_dir(step_num)
        status_file = step_dir / "status.json"
        error_file = step_dir / "error.log"
        
        # 写入错误日志
        with open(error_file, 'w', encoding='utf-8') as f:
            f.write(error_message)
        
        # 更新状态
        status_data = {
            "step_num": step_num,
            "status": "failed",
            "started_at": read_json(str(status_file)).get("started_at") if status_file.exists() else None,
            "failed_at": datetime.now().isoformat(),
            "error_message": error_message,
        }
        write_json(status_data, str(status_file))
        self.step_status[step_num] = "failed"
        self.logger.error(f"Step {step_num} failed: {error_message}")
    
    async def run_step(self, step_num: int, step_handler, *args, **kwargs):
        """运行步骤
        
        Args:
            step_num: 步骤编号
            step_handler: 步骤处理函数（异步）
            *args, **kwargs: 传递给处理函数的参数
            
        Returns:
            步骤执行结果
        """
        # 检查是否已完成（支持断点续跑）
        if self.is_step_completed(step_num):
            self.logger.info(f"Step {step_num} already completed, skipping")
            return self._load_step_result(step_num)
        
        # 标记开始
        self.mark_step_started(step_num)
        
        try:
            # 执行步骤
            result = await step_handler(*args, **kwargs)
            
            # 标记完成
            output_files = result.get("output_files", [])
            self.mark_step_completed(step_num, output_files)
            
            return result
        
        except Exception as e:
            # 标记失败
            self.mark_step_failed(step_num, str(e))
            raise
    
    def _load_step_result(self, step_num: int) -> dict:
        """加载已完成的步骤结果"""
        step_dir = self.get_step_output_dir(step_num)
        status_file = step_dir / "status.json"
        return read_json(str(status_file))
```

#### 3.2.2 AgentOrchestrator

**文件**: `src/mining_agents/managers/agent_orchestrator.py`

```python
from typing import Dict, Any, List, Optional
from ..utils.logger import setup_logger

class AgentOrchestrator:
    """Agent 编排器 - 负责 Agent 初始化、任务分发和结果收集"""
    
    def __init__(self, config: dict):
        """初始化 Agent 编排器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.logger = setup_logger("AgentOrchestrator", verbose=True)
        
        # 已初始化的 Agent 实例
        self.agents: Dict[str, Any] = {}
        
        # 工具实例
        self.tools: Dict[str, Any] = {}
    
    def register_tool(self, tool_name: str, tool_instance):
        """注册工具
        
        Args:
            tool_name: 工具名称
            tool_instance: 工具实例
        """
        self.tools[tool_name] = tool_instance
        self.logger.info(f"Tool '{tool_name}' registered")
    
    def get_tool(self, tool_name: str):
        """获取工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            工具实例
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not registered")
        return self.tools[tool_name]
    
    async def initialize_agent(self, agent_type: str, agent_name: str, **kwargs) -> Any:
        """初始化 Agent
        
        Args:
            agent_type: Agent 类型（如 "RequirementAnalystAgent"）
            agent_name: Agent 实例名称
            **kwargs: 初始化参数
            
        Returns:
            Agent 实例
        """
        # 动态导入 Agent 类
        module_name = f"..agents.{self._get_agent_module_name(agent_type)}"
        module = __import__(module_name, fromlist=[agent_type])
        agent_class = getattr(module, agent_type)
        
        # 初始化 Agent
        agent = agent_class(name=agent_name, orchestrator=self, **kwargs)
        self.agents[agent_name] = agent
        
        self.logger.info(f"Agent '{agent_name}' ({agent_type}) initialized")
        return agent
    
    def _get_agent_module_name(self, agent_type: str) -> str:
        """根据 Agent 类型获取模块名
        
        Args:
            agent_type: Agent 类型
            
        Returns:
            模块名（不含 .py）
        """
        # 简单映射，可以根据需要扩展
        mapping = {
            "RequirementAnalystAgent": "requirement_analyst_agent",
            "DomainExpertAgent": "domain_expert_agent",
            "CustomerAdvocateAgent": "customer_advocate_agent",
            "CoordinatorAgent": "coordinator_agent",
            "RuleEngineerAgent": "rule_engineer_agent",
            "EdgeCaseAnalysisAgent": "edge_case_analysis_agent",
            "QAModeratorAgent": "qa_moderator_agent",
            "ConfigAssemblerAgent": "config_assembler_agent",
        }
        return mapping.get(agent_type, agent_type.lower())
    
    async def execute_agent(self, agent_name: str, task: str, context: dict = None) -> dict:
        """执行 Agent 任务
        
        Args:
            agent_name: Agent 实例名称
            task: 任务描述
            context: 上下文信息
            
        Returns:
            Agent 执行结果
        """
        if agent_name not in self.agents:
            raise ValueError(f"Agent '{agent_name}' not initialized")
        
        agent = self.agents[agent_name]
        
        self.logger.info(f"Executing agent '{agent_name}' with task: {task[:50]}...")
        
        # 调用 Agent 的 execute 方法
        result = await agent.execute(task, context or {})
        
        self.logger.info(f"Agent '{agent_name}' execution completed")
        
        return result
    
    async def cleanup(self):
        """清理资源"""
        self.logger.info("Cleaning up resources...")
        
        # 关闭所有 Agent
        for agent_name, agent in self.agents.items():
            if hasattr(agent, 'close'):
                await agent.close()
        
        # 关闭所有工具
        for tool_name, tool in self.tools.items():
            if hasattr(tool, 'close'):
                await tool.close()
        
        self.logger.info("Cleanup completed")
```

### 3.3 Step 1 Agent

#### 3.3.1 RequirementAnalystAgent

**文件**: `src/mining_agents/agents/requirement_analyst_agent.py`

```python
from typing import Dict, Any, List
from ..utils.logger import setup_logger

class RequirementAnalystAgent:
    """需求分析 Agent - 负责需求澄清和问题生成"""
    
    def __init__(self, name: str, orchestrator, **kwargs):
        """初始化 Agent
        
        Args:
            name: Agent 名称
            orchestrator: Agent 编排器
            **kwargs: 其他参数
        """
        self.name = name
        self.orchestrator = orchestrator
        self.logger = setup_logger(f"Agent.{name}", verbose=True)
        
        # 从编排器获取工具
        self.deep_research_tool = orchestrator.get_tool("deep_research")
        self.json_validator = orchestrator.get_tool("json_validator")
    
    async def execute(self, task: str, context: dict) -> dict:
        """执行任务
        
        Args:
            task: 任务描述
            context: 上下文信息，包含：
                - business_desc: 业务描述
                - mock_mode: 是否使用 Mock 模式（默认 True）
                
        Returns:
            执行结果，包含：
                - questions: 待澄清问题列表
                - output_files: 输出文件列表
        """
        self.logger.info(f"Starting requirement analysis for: {context.get('business_desc', '')[:50]}...")
        
        # 检查是否为 Mock 模式
        mock_mode = context.get("mock_mode", True)
        
        if mock_mode:
            self.logger.info("Running in MOCK mode - using predefined questions")
            questions = self._generate_mock_questions(context.get("business_desc", ""))
        else:
            self.logger.info("Running in REAL mode - using Deep Research")
            questions = await self._generate_questions_with_research(context.get("business_desc", ""))
        
        # 生成 Markdown 格式的问题清单
        markdown_content = self._format_questions_to_markdown(questions)
        
        # 写入文件
        output_file = context.get("output_dir") / "step1_clarification_questions.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        self.logger.info(f"Questions written to {output_file}")
        
        return {
            "questions": questions,
            "output_files": [str(output_file)],
            "mock_mode": mock_mode,
        }
    
    def _generate_mock_questions(self, business_desc: str) -> List[Dict[str, str]]:
        """生成 Mock 问题（用于测试）
        
        Args:
            business_desc: 业务描述
            
        Returns:
            问题列表
        """
        # 根据业务描述生成一些示例问题
        return [
            {
                "id": "Q1",
                "question": "您的客服 Agent 主要服务于哪些客户群体？（如：个人消费者、企业客户、混合）",
                "category": "target_audience",
                "priority": "high",
            },
            {
                "id": "Q2",
                "question": "客服 Agent 需要处理哪些核心业务流程？（如：订单查询、退换货、产品咨询、投诉处理）",
                "category": "core_processes",
                "priority": "high",
            },
            {
                "id": "Q3",
                "question": "是否有现有的术语表或专有词汇需要提供？（如：产品名称、内部术语、行业缩写）",
                "category": "glossary",
                "priority": "medium",
            },
            {
                "id": "Q4",
                "question": "是否需要与其他系统集成？（如：CRM、ERP、订单管理系统）",
                "category": "integrations",
                "priority": "medium",
            },
            {
                "id": "Q5",
                "question": "有哪些特定的合规要求或话术规范需要遵循？",
                "category": "compliance",
                "priority": "high",
            },
        ]
    
    async def _generate_questions_with_research(self, business_desc: str) -> List[Dict[str, str]]:
        """使用 Deep Research 生成问题
        
        Args:
            business_desc: 业务描述
            
        Returns:
            问题列表
        """
        # 构造搜索查询
        query = f"客服 Agent 需求分析 - {business_desc}"
        
        # 调用 Deep Research
        research_report = await self.deep_research_tool.search(query)
        
        # 基于研究报告生成问题（这里简化处理，实际应该用 LLM 分析）
        questions = [
            {
                "id": "Q1",
                "question": f"基于行业最佳实践，您的{business_desc}场景下，最关键的 3 个客户服务痛点是什么？",
                "category": "pain_points",
                "priority": "high",
            },
            # ... 更多问题
        ]
        
        return questions
    
    def _format_questions_to_markdown(self, questions: List[Dict[str, str]]) -> str:
        """将问题格式化为 Markdown
        
        Args:
            questions: 问题列表
            
        Returns:
            Markdown 格式的文本
        """
        lines = [
            "# Step 1: 需求澄清问题清单",
            "",
            "请回答以下问题以帮助我们更准确地生成 Parlant Agent 配置：",
            "",
        ]
        
        for q in questions:
            priority_icon = "🔴" if q["priority"] == "high" else "🟡"
            lines.append(f"### {priority_icon} {q['id']}: {q['question']}")
            lines.append("")
            lines.append(f"**类别**: {q['category']}")
            lines.append("")
            lines.append("**您的回答**: （请填写）")
            lines.append("")
            lines.append("---")
            lines.append("")
        
        lines.append("## 下一步")
        lines.append("")
        lines.append("填写完成后，请运行以下命令继续：")
        lines.append("")
        lines.append("```bash")
        lines.append("python -m mining_agents.main --business-desc \"...\" --start-step 2")
        lines.append("```")
        lines.append("")
        
        return "\n".join(lines)
    
    async def close(self):
        """关闭资源"""
        self.logger.info("RequirementAnalystAgent closing")
```

---

## 四、数据流设计

### 4.1 Step 1 执行流程

```
用户输入业务描述
    ↓
StepManager.run_step(1, handler)
    ↓
标记 Step 1 开始
    ↓
AgentOrchestrator.initialize_agent("RequirementAnalystAgent")
    ↓
AgentOrchestrator.execute_agent(
    agent_name="RequirementAnalyst",
    task="分析需求并生成澄清问题",
    context={
        "business_desc": "电商客服 Agent",
        "mock_mode": True,
        "output_dir": "./output/step1"
    }
)
    ↓
RequirementAnalystAgent.execute()
    ├─ 生成 Mock 问题
    ├─ 格式化为 Markdown
    └─ 写入 step1_clarification_questions.md
    ↓
标记 Step 1 完成
    ↓
返回结果
```

### 4.2 Mock 数据结构

**step1_clarification_questions.md**:
```markdown
# Step 1: 需求澄清问题清单

请回答以下问题以帮助我们更准确地生成 Parlant Agent 配置：

---

### 🔴 Q1: 您的客服 Agent 主要服务于哪些客户群体？（如：个人消费者、企业客户、混合）

**类别**: target_audience

**您的回答**: （请填写）

---

### 🔴 Q2: 客服 Agent 需要处理哪些核心业务流程？（如：订单查询、退换货、产品咨询、投诉处理）

**类别**: core_processes

**您的回答**: （请填写）

---

...（更多问题）
```

---

## 五、测试策略

### 5.1 单元测试

**文件**: `tests/test_mvp.py`

```python
import pytest
from pathlib import Path
import tempfile

class TestStepManager:
    """测试 StepManager"""
    
    def test_step_status_tracking(self, temp_dir):
        """测试步骤状态跟踪"""
        manager = StepManager(config_path="config/system_config.yaml", output_base_dir=str(temp_dir))
        
        # 初始状态应为未完成
        assert not manager.is_step_completed(1)
        
        # 标记开始
        manager.mark_step_started(1)
        assert manager.step_status[1] == "running"
        
        # 标记完成
        manager.mark_step_completed(1, ["file1.md"])
        assert manager.step_status[1] == "completed"
        assert manager.is_step_completed(1)
    
    def test_rerun_skip_logic(self, temp_dir):
        """测试重跑跳过逻辑"""
        manager = StepManager(config_path="config/system_config.yaml", output_base_dir=str(temp_dir))
        
        # 第一次运行
        manager.mark_step_started(1)
        manager.mark_step_completed(1)
        
        # 第二次运行应跳过
        assert manager.is_step_completed(1)

class TestAgentOrchestrator:
    """测试 AgentOrchestrator"""
    
    @pytest.mark.asyncio
    async def test_tool_registration(self):
        """测试工具注册"""
        orchestrator = AgentOrchestrator(config={})
        
        # 注册 Mock 工具
        mock_tool = MockDeepResearchTool()
        orchestrator.register_tool("deep_research", mock_tool)
        
        # 获取工具
        tool = orchestrator.get_tool("deep_research")
        assert tool == mock_tool
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """测试 Agent 初始化"""
        orchestrator = AgentOrchestrator(config={})
        orchestrator.register_tool("deep_research", MockDeepResearchTool())
        orchestrator.register_tool("json_validator", MockJsonValidator())
        
        # 初始化 Agent
        agent = await orchestrator.initialize_agent(
            agent_type="RequirementAnalystAgent",
            agent_name="TestAnalyst"
        )
        
        assert agent.name == "TestAnalyst"
        assert "TestAnalyst" in orchestrator.agents

class TestRequirementAnalystAgent:
    """测试 RequirementAnalystAgent"""
    
    @pytest.mark.asyncio
    async def test_mock_question_generation(self, temp_dir):
        """测试 Mock 问题生成"""
        orchestrator = MockOrchestrator()
        agent = RequirementAnalystAgent(name="TestAgent", orchestrator=orchestrator)
        
        result = await agent.execute(
            task="Generate questions",
            context={
                "business_desc": "电商客服 Agent",
                "mock_mode": True,
                "output_dir": temp_dir
            }
        )
        
        assert len(result["questions"]) > 0
        assert len(result["output_files"]) == 1
        assert Path(result["output_files"][0]).exists()
```

### 5.2 Mock 工具类

```python
class MockDeepResearchTool:
    """Mock Deep Research 工具"""
    
    async def search(self, query: str) -> str:
        return f"Mock research report for: {query}"
    
    async def close(self):
        pass

class MockJsonValidator:
    """Mock JSON 校验工具"""
    
    @staticmethod
    def validate(json_string: str):
        return True, {"mock": "data"}, ""
    
    @staticmethod
    def save_json(data, file_path, indent=2):
        return True

class MockOrchestrator:
    """Mock AgentOrchestrator"""
    
    def __init__(self):
        self.tools = {
            "deep_research": MockDeepResearchTool(),
            "json_validator": MockJsonValidator(),
        }
    
    def get_tool(self, tool_name: str):
        return self.tools[tool_name]
```

---

## 六、文件清单

### 6.1 新增文件

| 文件路径 | 说明 | 行数预估 |
|---------|------|---------|
| `src/mining_agents/tools/deep_research.py` | DeepResearchAgent 封装 | ~80 |
| `src/mining_agents/tools/json_validator.py` | JSON 校验工具 | ~50 |
| `src/mining_agents/managers/step_manager.py` | 步骤管理器 | ~150 |
| `src/mining_agents/managers/agent_orchestrator.py` | Agent 编排器 | ~150 |
| `src/mining_agents/agents/requirement_analyst_agent.py` | 需求分析 Agent | ~150 |
| `tests/test_mvp.py` | MVP 测试 | ~150 |

### 6.2 修改文件

| 文件路径 | 修改内容 |
|---------|---------|
| `src/mining_agents/utils/__init__.py` | 导出新工具函数 |
| `requirements.txt` | 添加 agentscope 依赖 |

---

## 七、实施计划

### Phase 1: 工具服务层 (Task 1-2)

1. 创建 `deep_research.py` - DeepResearchAgent 封装
2. 创建 `json_validator.py` - JSON 校验工具
3. 更新 `requirements.txt` - 添加 agentscope 依赖

### Phase 2: 核心管理器 (Task 3-4)

4. 创建 `step_manager.py` - 步骤管理器
5. 创建 `agent_orchestrator.py` - Agent 编排器
6. 更新 managers `__init__.py` - 导出新类

### Phase 3: Step 1 Agent (Task 5-6)

7. 创建 `requirement_analyst_agent.py` - 需求分析 Agent
8. 更新 agents `__init__.py` - 导出新类
9. 更新 CLI - 添加 Step 1 调用逻辑

### Phase 4: 测试验证 (Task 7-8)

10. 创建 `test_mvp.py` - MVP 测试
11. 运行测试验证
12. 编写使用文档

---

## 八、验收标准

### 8.1 功能验收

- [ ] StepManager 能正确跟踪步骤状态
- [ ] AgentOrchestrator 能正确初始化和执行 Agent
- [ ] RequirementAnalystAgent 能生成 Mock 问题并写入文件
- [ ] 支持 Mock 模式，不实际调用 LLM API
- [ ] 支持断点续跑（已完成的步骤可跳过）

### 8.2 代码质量

- [ ] 所有代码通过 flake8 检查
- [ ] 所有代码通过 black 格式化
- [ ] 单元测试覆盖率 > 80%
- [ ] 所有测试通过

### 8.3 文档完整性

- [ ] README.md 更新 MVP 使用说明
- [ ] 代码注释完整
- [ ] 提供 Mock 测试示例

---

**设计文档完成，等待用户批准后进入实现阶段。**

请审阅以上设计文档，确认：
1. 架构设计是否合理？
2. 组件职责是否清晰？
3. Mock 测试策略是否可行？
4. 是否批准开始实现？
