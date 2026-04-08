#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parlant Agent 完全隔离式构建脚本
================================

功能说明:
    本脚本用于构建完全隔离的 Parlant Agent，支持以下核心功能:
    1. 单个 Agent 独立构建，与其他Agent 完全物理隔离
    2. 加载 Agent专属的所有配置 (基础配置、规则、工具、术语表)
    3. 完整实现 Parlant 原生的排除关系与依赖关系绑定
    4. 支持多 SOP(Journey)的状态机构建与规则映射
    5. 动态导入 Agent专属的工具实现代码

使用方式:
    python build_agent.py [agent_folder_name]
    
示例:
    python build_agent.py medical_customer_service_agent
    python build_agent.py airline_customer_service_agent

目录结构要求:
    agents/
    ├── medical_customer_service_agent/
    │   ├── 00_agent_base/          # 基础配置
    │   │   ├── agent_metadata.json
    │   │   ├── agent_observability.json
    │   │   └── glossary/
    │   ├── 01_agent_rules/         # 全局规则
    │   │   ├── agent_guidelines.json
    │   │   ├── agent_observations.json
    │   │   └── agent_canned_responses.json
    │   ├── 02_journeys/            # 业务 SOP
    │   │   └── schedule_appt/
    │   │       ├── sop.json
    │   │       ├── sop_guidelines.json
    │   │       └── sop_observations.json
    │   └── 03_tools/               # 专属工具
    │       └── tool_get_upcoming_slots/
    │           ├── tool_meta.json
    │           └── tool_impl.py
    automation/
    └── build_agent.py              # 本构建脚本

作者：Parlant Agent Config Manager
版本：1.0.0
创建时间：2026-03-09
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from parlant import sdk as p


# ============================================================================
# 全局常量定义
# ============================================================================

# 项目根目录路径 (自动化脚本所在目录的上级目录)
ROOT_PATH = Path(__file__).parent.parent.resolve()

# 配置文件编码格式
CONFIG_ENCODING = "utf-8"

# 资产类型枚举
ASSET_TYPES = ["tools", "canned_responses", "observations", "guidelines", "journeys"]


# ============================================================================
# 工具函数
# ============================================================================

def read_config(file_path: Path) -> Dict[str, Any]:
    """
    读取 JSON 配置文件
    
    Args:
        file_path: 配置文件路径
        
    Returns:
        解析后的 JSON 数据字典
        
    Raises:
        FileNotFoundError: 当配置文件不存在时抛出
        json.JSONDecodeError: 当 JSON 格式不正确时抛出
        
    Example:
        >>> config = read_config(Path("agents/medical/00_agent_base/agent_metadata.json"))
        >>> print(config["agent_name"])
        '智慧医疗客服 Agent'
    """
    full_path = Path(file_path).resolve()
    
    # 文件存在性校验
    if not full_path.exists():
        raise FileNotFoundError(f"❌ 配置文件不存在：{full_path}")
    
    # 读取并解析 JSON
    with open(full_path, "r", encoding=CONFIG_ENCODING) as f:
        return json.load(f)


def validate_agent_folder(agent_folder_path: Path) -> bool:
    """
    验证 Agent 文件夹结构是否完整
    
    Args:
        agent_folder_path: Agent 文件夹路径
        
    Returns:
        True 如果文件夹结构有效，否则 False
        
    验证内容:
        1. 文件夹必须存在
        2. 必须包含 00_agent_base 目录
        3. 必须包含 agent_metadata.json 文件
    """
    # 检查文件夹是否存在
    if not agent_folder_path.exists() or not agent_folder_path.is_dir():
        return False
    
    # 检查基础配置文件是否存在
    metadata_path = agent_folder_path / "00_agent_base" / "agent_metadata.json"
    if not metadata_path.exists():
        return False
    
    return True


# ============================================================================
# 核心构建类
# ============================================================================

class IsolatedAgentBuilder:
    """
    完全隔离式 Agent 构建器
    
    职责:
        1. 加载单个 Agent 的所有专属配置
        2. 创建 Parlant Agent 实例
        3. 注册所有资产 (术语、观测、规则、工具、SOP)
        4. 绑定规则间的排除/依赖关系
        5. 构建 Journey 状态机
        
    特性:
        - 完全隔离：仅加载指定 Agent 的配置，不影响其他Agent
        - 关系完整：支持排除、依赖、蕴含等所有 Parlant 原生关系
        - 错误处理：完善的错误检测与友好的错误提示
        - 日志追踪：详细的构建日志，便于调试与审计
    
    Usage:
        builder = IsolatedAgentBuilder()
        await builder.build("medical_customer_service_agent")
    """
    
    def __init__(self):
        """初始化构建器"""
        self.instance_pool: Dict[str, Dict] = {
            "tools": {},
            "canned_responses": {},
            "observations": {},
            "guidelines": {},
            "journeys": {}
        }
        self.current_agent = None
        self.agent_meta = None
    
    def _reset_pool(self):
        """重置资产实例池，确保不同 Agent 之间完全隔离"""
        self.instance_pool = {asset_type: {} for asset_type in ASSET_TYPES}
    
    async def build(self, agent_folder_name: str):
        """
        构建单个完全隔离 Agent 的主入口
        
        Args:
            agent_folder_name: Agent 文件夹名称 (位于 agents/目录下)
            
        Raises:
            SystemExit: 当 Agent 文件夹不存在时退出程序
        """
        # ========== 阶段 1: 前置校验 ==========
        agent_folder_path = ROOT_PATH / "agents" / agent_folder_name
        
        if not validate_agent_folder(agent_folder_path):
            print(f"❌ Agent 文件夹不存在或结构不完整：{agent_folder_name}")
            print(f"💡 请确保 Agent 文件夹位于：{ROOT_PATH / 'agents'}")
            print(f"💡 文件夹必须包含 00_agent_base/agent_metadata.json")
            sys.exit(1)
        
        print(f"\n{'='*60}")
        print(f"🚀 开始构建完全隔离 Agent: {agent_folder_name}")
        print(f"{'='*60}")
        
        # 重置资产池，确保完全隔离
        self._reset_pool()
        
        # ========== 阶段 2: 加载基础信息 ==========
        self.agent_meta = read_config(
            agent_folder_path / "00_agent_base" / "agent_metadata.json"
        )
        print(f"✅ 加载 Agent 基础信息完成：{self.agent_meta['agent_name']}")
        
        # ========== 阶段 3: 初始化 Parlant Server ==========
        async with p.Server(port=self.agent_meta.get("playground_port", 8800)) as server:
            self.current_agent = await server.create_agent(
                name=self.agent_meta["agent_name"],
                description=self.agent_meta["agent_description"]
            )
            print(f"✅ Agent 实例创建成功（完全隔离）")
            
            # ========== 阶段 4: 加载基础资产 ==========
            await self._load_glossary(agent_folder_path)
            await self._load_global_observations(agent_folder_path)
            await self._load_global_guidelines(agent_folder_path)
            await self._load_tools(agent_folder_path)
            
            # ========== 阶段 5: 加载业务 SOP ==========
            await self._load_journeys(agent_folder_path)
            
            # ========== 阶段 6: 构建完成 ==========
            print(f"\n{'='*60}")
            print(f"🎉 完全隔离 Agent {self.agent_meta['agent_name']} 构建完成！")
            print(f"🔗 测试地址：http://localhost:{self.agent_meta.get('playground_port', 8800)}")
            print(f"{'='*60}\n")
            
            # 保持服务运行
            await asyncio.Event().wait()
    
    async def _load_glossary(self, agent_folder_path: Path):
        """
        加载 Agent专属的领域术语表
        
        Args:
            agent_folder_path: Agent 文件夹路径
            
        术语表作用:
            - 帮助 Agent 精准理解领域专用术语
            - 支持同义词扩展，提升语义理解能力
            - 每个 Agent 独立维护自己的术语表
        """
        glossary_folder = agent_folder_path / "00_agent_base" / "glossary"
        
        if not glossary_folder.exists():
            print(f"⚠️  未找到术语表文件夹，跳过加载")
            return
        
        glossary_files = glossary_folder.glob("*.json")
        term_count = 0
        
        for glossary_file in glossary_files:
            try:
                glossary_config = read_config(glossary_file)
                terms = glossary_config.get("terms", [])
                
                for term in terms:
                    await self.current_agent.create_term(
                        name=term["name"],
                        description=term["description"],
                        synonyms=term.get("synonyms", [])
                    )
                    term_count += 1
                
                print(f"📚 加载术语表：{glossary_file.name} ({len(terms)}个术语)")
            except Exception as e:
                print(f"⚠️  加载术语表失败 {glossary_file.name}: {str(e)}")
        
        print(f"✅ 加载 Agent专属领域术语表完成，共 {term_count} 个术语")
    
    async def _load_global_observations(self, agent_folder_path: Path):
        """
        加载 Agent专属的全局观测
        
        Args:
            agent_folder_path: Agent 文件夹路径
            
        观测作用:
            - 检测对话中的特定状态或条件
            - 作为规则依赖的前置触发条件
            - 本质是"没有 action 的 Guideline"
        """
        obs_config_path = agent_folder_path / "01_agent_rules" / "agent_observations.json"
        
        if not obs_config_path.exists():
            print(f"⚠️  未找到全局观测配置文件，跳过加载")
            return
        
        agent_obs_config = read_config(obs_config_path)
        observations = agent_obs_config.get("agent_observations", [])
        
        for obs in observations:
            obs_id = obs["observation_id"]
            obs_instance = await self.current_agent.create_observation(
                condition=obs["condition"]
            )
            self.instance_pool["observations"][obs_id] = obs_instance
        
        print(f"✅ 加载 Agent专属全局观测完成，共 {len(observations)} 个观测")
    
    async def _load_global_guidelines(self, agent_folder_path: Path):
        """
        加载 Agent专属的全局 Guideline(含关系绑定)
        
        Args:
            agent_folder_path: Agent 文件夹路径
            
        加载流程:
            1. 先加载所有 Canned Responses(模板话术)
            2. 再加载所有 Guidelines(暂不绑定关系)
            3. 最后绑定排除关系与依赖关系
            
        设计原因:
            - 分阶段加载确保所有依赖对象已创建
            - 避免循环依赖导致的实例化失败
        """
        rules_config_path = agent_folder_path / "01_agent_rules" / "agent_guidelines.json"
        
        if not rules_config_path.exists():
            print(f"⚠️  未找到全局规则配置文件，跳过加载")
            return
        
        agent_rules_config = read_config(rules_config_path)
        
        # --- 步骤 1: 加载全局模板话术 ---
        canned_responses = agent_rules_config.get("agent_canned_responses", [])
        for cr in canned_responses:
            cr_id = cr["canned_response_id"]
            cr_instance = await self.current_agent.create_canned_response(
                content=cr["content"],
                language=cr.get("language", "zh-CN")
            )
            self.instance_pool["canned_responses"][cr_id] = cr_instance
        
        print(f"✅ 加载 Agent专属全局模板话术完成，共 {len(canned_responses)} 个话术")
        
        # --- 步骤 2: 加载所有 Guideline(暂不绑定关系) ---
        guidelines = agent_rules_config.get("agent_guidelines", [])
        
        for guideline in guidelines:
            guideline_id = guideline["guideline_id"]
            
            # 准备关联的模板话术
            canned_responses_list = [
                self.instance_pool["canned_responses"][cr_id]
                for cr_id in guideline.get("bind_canned_response_ids", [])
                if cr_id in self.instance_pool["canned_responses"]
            ]
            
            # 准备关联的工具
            tools_list = [
                self.instance_pool["tools"][tool_id]
                for tool_id in guideline.get("bind_tool_ids", [])
                if tool_id in self.instance_pool["tools"]
            ]
            
            # 创建 Guideline 实例
            guideline_instance = await self.current_agent.create_guideline(
                condition=guideline["condition"],
                action=guideline["action"],
                priority=guideline.get("priority", self.agent_meta["default_priority"]),
                composition_mode=getattr(p.CompositionMode, guideline["composition_mode"]),
                canned_responses=canned_responses_list,
                tools=tools_list
            )
            
            self.instance_pool["guidelines"][guideline_id] = guideline_instance
        
        print(f"✅ 加载 Agent专属全局 Guideline 完成，共 {len(guidelines)} 个规则")
        
        # --- 步骤 3: 绑定排除关系与依赖关系 ---
        bound_exclusions = 0
        bound_dependencies = 0
        
        for guideline in guidelines:
            guideline_id = guideline["guideline_id"]
            guideline_instance = self.instance_pool["guidelines"][guideline_id]
            
            # 绑定排除关系（优先级关系）
            for exclude_id in guideline.get("exclusions", []):
                exclude_instance = self.instance_pool["guidelines"].get(exclude_id)
                if exclude_instance:
                    await guideline_instance.prioritize_over(exclude_instance)
                    print(f"🔗 绑定 Agent 优先级关系：{guideline_id} > {exclude_id}")
                    bound_exclusions += 1
                        
            # 绑定依赖关系（支持依赖 Guideline 或 Observation）
            dependencies = []
            for dep_id in guideline.get("dependencies", []):
                dep_instance = (
                    self.instance_pool["guidelines"].get(dep_id) or 
                    self.instance_pool["observations"].get(dep_id)
                )
                if dep_instance:
                    dependencies.append(dep_instance)
                        
            if dependencies:
                await guideline_instance.depend_on(dependencies)
                dep_ids = [d for d in guideline.get('dependencies', [])]
                print(f"🔗 绑定 Agent 依赖关系：{guideline_id} → {dep_ids}")
                bound_dependencies += len(dependencies)
        
        print(f"✅ 加载 Agent专属全局规则完成 (排除关系:{bound_exclusions}, 依赖关系:{bound_dependencies})")
    
    async def _load_tools(self, agent_folder_path: Path):
        """
        加载 Agent专属的工具库
        
        Args:
            agent_folder_path: Agent 文件夹路径
        
        工具加载流程:
            1. 遍历 tools 文件夹下的所有子文件夹
            2. 读取每个工具的元信息配置
            3. 动态导入工具实现代码
            4. 创建观测绑定工具的触发场景
        
        动态导入原理:
            - 根据工具文件夹路径动态生成模块名
            - 使用__import__导入模块
            - 获取工具函数并注册到实例池
        """
        tools_folder = agent_folder_path / "03_tools"
        
        if not tools_folder.exists():
            print(f"⚠️  未找到工具文件夹，跳过加载")
            return
        
        tool_folders = [f for f in tools_folder.iterdir() if f.is_dir()]
        loaded_tools = []
        
        for tool_folder in tool_folders:
            try:
                print(f"\n🔧 正在加载 Agent专属工具：{tool_folder.name}")
                
                # 读取工具元信息
                meta_config = read_config(tool_folder / "tool_meta.json")
                tool_id = meta_config["tool_id"]
                impl_path = tool_folder / meta_config["implementation_file"]
                
                # 动态导入工具实现
                module_name = impl_path.stem
                module_path = str(impl_path.parent).replace(
                    str(ROOT_PATH), ""
                ).replace("/", ".").strip(".")
                
                tool_module = __import__(
                    f"{module_path}.{module_name}",
                    fromlist=[meta_config["tool_name"]]
                )
                
                tool_func = getattr(tool_module, meta_config["tool_name"])
                self.instance_pool["tools"][tool_id] = tool_func
                
                # 为每个工具创建触发 Guideline（符合官方规范）
                use_scenarios = meta_config.get("use_scenarios", [])
                if use_scenarios:
                    # 方式 1: 使用 create_guideline + tools 参数（推荐）
                    await self.current_agent.create_guideline(
                        condition=" | ".join(use_scenarios),
                        action=f"Call the {meta_config['tool_name']} tool to handle this request",
                        tools=[tool_func]
                    )
                    # 方式 2: 或使用 attach_tool（更简洁，如果工具描述足够清晰）
                    # await self.current_agent.attach_tool(
                    #     condition=" | ".join(use_scenarios),
                    #     tool=tool_func
                    # )
                
                loaded_tools.append(tool_id)
                print(f"✅ 工具 {tool_id} 加载成功")
                
            except Exception as e:
                print(f"⚠️  加载工具 {tool_folder.name} 失败：{str(e)}")
                import traceback
                traceback.print_exc()
        
        print(f"\n✅ 加载 Agent专属工具完成，共加载 {len(loaded_tools)} 个工具：{loaded_tools}")
    
    async def _load_journeys(self, agent_folder_path: Path):
        """
        加载 Agent 的所有业务 SOP(Journeys)
        
        Args:
            agent_folder_path: Agent 文件夹路径
        
        加载流程:
            1. 遍历 journeys 文件夹下的所有 SOP 子文件夹
            2. 对每个 SOP:
               a. 加载 SOP 专属观测
               b. 加载 SOP 专属 Guideline 和模板话术
               c. 绑定 SOP 内的排除/依赖关系
               d. 创建 Journey 实例并绑定全局 Guideline
               e. 构建 Journey 状态机
        
        Journey 状态机构建:
            - 按照 sop_states 数组顺序构建状态
            - 第一个状态为初始状态
            - 根据 transitions 构建状态转移
            - 标记结束状态并绑定 END_JOURNEY
        """
        journeys_folder = agent_folder_path / "02_journeys"
        
        if not journeys_folder.exists():
            print(f"⚠️  未找到 Journeys 文件夹，跳过加载")
            return
        
        sop_folders = [f for f in journeys_folder.iterdir() if f.is_dir()]
        
        for sop_folder in sop_folders:
            print(f"\n{'-'*60}")
            print(f"📋 开始处理 Agent专属业务 SOP: {sop_folder.name}")
            print(f"{'-'*60}")
            
            # --- 步骤 1: 加载 SOP 专属观测 ---
            sop_obs_map = await self._load_sop_observations(sop_folder)
            
            # --- 步骤 2: 加载 SOP 专属 Guideline ---
            sop_guideline_map, sop_cr_map = await self._load_sop_guidelines(
                sop_folder, sop_obs_map
            )
            
            # --- 步骤 3: 加载 SOP 流程文件并创建 Journey ---
            await self._create_journey_and_build_state_machine(
                sop_folder, sop_guideline_map, sop_cr_map
            )
    
    async def _load_sop_observations(self, sop_folder: Path) -> Dict[str, Any]:
        """
        加载 SOP 专属的观测
        
        Args:
            sop_folder: SOP 文件夹路径
            
        Returns:
            观测 ID 到实例的映射字典
        """
        sop_obs_path = sop_folder / "sop_observations.json"
        sop_obs_map = {}
        
        if not sop_obs_path.exists():
            print(f"⚠️  未找到 SOP 观测配置文件，跳过加载")
            return sop_obs_map
        
        try:
            sop_obs_config = read_config(sop_obs_path)
            
            for obs in sop_obs_config.get("sop_observations", []):
                obs_id = obs["observation_id"]
                obs_instance = await self.current_agent.create_observation(
                    condition=obs["condition"]
                )
                self.instance_pool["observations"][obs_id] = obs_instance
                sop_obs_map[obs_id] = obs_instance
            
            print(f"✅ SOP 专属观测加载完成，共 {len(sop_obs_map)} 个观测")
            
        except Exception as e:
            print(f"⚠️  加载 SOP 观测失败：{str(e)}")
        
        return sop_obs_map
    
    async def _load_sop_guidelines(
        self, 
        sop_folder: Path, 
        sop_obs_map: Dict[str, Any]
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        加载 SOP 专属的 Guideline 和模板话术
        
        Args:
            sop_folder: SOP 文件夹路径
            sop_obs_map: SOP 观测映射字典
            
        Returns:
            (Guideline 映射字典，Canned Response 映射字典)
        """
        sop_guideline_config_path = sop_folder / "sop_guidelines.json"
        
        if not sop_guideline_config_path.exists():
            print(f"⚠️  未找到 SOP 规则配置文件，跳过加载")
            return {}, {}
        
        try:
            sop_guideline_config = read_config(sop_guideline_config_path)
            sop_id = sop_guideline_config.get("sop_id", "unknown")
            
            # --- 加载 SOP 专属模板话术 ---
            sop_cr_map = {}
            for cr in sop_guideline_config.get("sop_canned_responses", []):
                cr_id = cr["canned_response_id"]
                cr_instance = await self.current_agent.create_canned_response(
                    content=cr["content"],
                    language=cr.get("language", "zh-CN")
                )
                self.instance_pool["canned_responses"][cr_id] = cr_instance
                sop_cr_map[cr_id] = cr_instance
            
            print(f"✅ SOP {sop_id} 专属模板话术加载完成，共 {len(sop_cr_map)} 个话术")
            
            # --- 加载 SOP 专属 Guideline(暂不绑定关系) ---
            sop_guideline_map = {}
            
            for guideline in sop_guideline_config.get("sop_scoped_guidelines", []):
                guideline_id = guideline["guideline_id"]
                
                # 准备关联的模板话术 (优先使用 SOP 专属，回退到全局)
                canned_responses_list = [
                    sop_cr_map.get(cr_id) or self.instance_pool["canned_responses"][cr_id]
                    for cr_id in guideline.get("bind_canned_response_ids", [])
                    if sop_cr_map.get(cr_id) or cr_id in self.instance_pool["canned_responses"]
                ]
                
                # 准备关联的工具
                tools_list = [
                    self.instance_pool["tools"][tool_id]
                    for tool_id in guideline.get("bind_tool_ids", [])
                    if tool_id in self.instance_pool["tools"]
                ]
                
                # 创建 Guideline 实例
                guideline_instance = await self.current_agent.create_guideline(
                    condition=guideline["condition"],
                    action=guideline["action"],
                    priority=guideline.get("priority", self.agent_meta["default_priority"]),
                    composition_mode=getattr(p.CompositionMode, guideline["composition_mode"]),
                    canned_responses=canned_responses_list,
                    tools=tools_list
                )
                
                self.instance_pool["guidelines"][guideline_id] = guideline_instance
                sop_guideline_map[guideline_id] = guideline_instance
            
            print(f"✅ SOP {sop_id} 专属 Guideline 加载完成，共 {len(sop_guideline_map)} 个规则")
            
            # --- 绑定 SOP 专属 Guideline 的关系 (内联实现) ---
            bound_exclusions = 0
            bound_dependencies = 0
            
            for guideline in sop_guideline_config.get("sop_scoped_guidelines", []):
                guideline_id = guideline["guideline_id"]
                guideline_instance = sop_guideline_map[guideline_id]
                
                # 绑定优先级关系（原"排除关系"）
                for exclude_id in guideline.get("exclusions", []):
                    exclude_instance = (
                        sop_guideline_map.get(exclude_id) or 
                        self.instance_pool["guidelines"].get(exclude_id)
                    )
                    if exclude_instance:
                        await guideline_instance.prioritize_over(exclude_instance)
                        print(f"🔗 绑定 SOP 优先级关系：{guideline_id} > {exclude_id}")
                        bound_exclusions += 1
                
                # 绑定依赖关系（支持 SOP 内、全局 Guideline、SOP 观测）
                dependencies = []
                for dep_id in guideline.get("dependencies", []):
                    dep_instance = (
                        sop_guideline_map.get(dep_id) or 
                        self.instance_pool["guidelines"].get(dep_id) or 
                        self.instance_pool["observations"].get(dep_id)
                    )
                    if dep_instance:
                        dependencies.append(dep_instance)
                
                if dependencies:
                    await guideline_instance.depend_on(dependencies)
                    dep_ids = [d for d in guideline.get('dependencies', [])]
                    print(f"🔗 绑定 SOP 依赖关系：{guideline_id} → {dep_ids}")
                    bound_dependencies += len(dependencies)
            
            print(f"✅ SOP {sop_id} 专属规则关系绑定完成 (优先级:{bound_exclusions}, 依赖:{bound_dependencies})")
            
            return sop_guideline_map, sop_cr_map
            
        except Exception as e:
            print(f"⚠️  加载 SOP Guideline 失败：{str(e)}")
            import traceback
            traceback.print_exc()
            return {}, {}
    
    
    
    async def _create_journey_and_build_state_machine(
        self,
        sop_folder: Path,
        sop_guideline_map: Dict[str, Any],
        sop_cr_map: Dict[str, Any]
    ):
        """
        创建 Journey 实例并构建状态机
        
        Args:
            sop_folder: SOP 文件夹路径
            sop_guideline_map: SOP Guideline 映射
            sop_cr_map: SOP 模板话术映射
        """
        sop_config_path = sop_folder / "sop.json"
        
        if not sop_config_path.exists():
            print(f"⚠️  未找到 SOP 流程配置文件，跳过创建 Journey")
            return
        
        try:
            sop_config = read_config(sop_config_path)
            sop_id = sop_config.get("sop_id", "unknown")
            sop_title = sop_config.get("sop_title", "Unknown SOP")
            
            # --- 创建 Journey 实例 ---
            journey = await self.current_agent.create_journey(
                title=sop_config["sop_title"],
                description=sop_config["sop_description"],
                conditions=sop_config.get("trigger_conditions", [])
            )
            self.instance_pool["journeys"][sop_id] = journey
            
            # --- 绑定 SOP 全局 Guideline ---
            bind_guideline_ids = sop_config.get("sop_guideline_mapping", {}).get(
                "sop_global_bind_guideline_ids", []
            )
            
            for guideline_id in bind_guideline_ids:
                guideline = sop_guideline_map.get(guideline_id)
                if guideline:
                    await journey.add_guideline(guideline)
            
            print(f"✅ SOP {sop_id} 规则绑定完成，共绑定 {len(bind_guideline_ids)} 个全局规则")
            
            # --- 构建 Journey 状态机 ---
            await self._build_journey_state_machine(
                sop_config, sop_guideline_map, sop_cr_map, journey
            )
            
            print(f"🎉 SOP {sop_title} 状态机构建完成")
            
        except Exception as e:
            print(f"⚠️  创建 Journey 失败：{str(e)}")
            import traceback
            traceback.print_exc()
    
    async def _build_journey_state_machine(
        self,
        sop_config: Dict[str, Any],
        sop_guideline_map: Dict[str, Any],
        sop_cr_map: Dict[str, Any],
        journey: Any
    ):
        """
        构建 Journey 的状态机
        
        Args:
            sop_config: SOP 配置
            sop_guideline_map: SOP Guideline 映射
            sop_cr_map: SOP 模板话术映射
            journey: Journey 实例
        
        状态机构建逻辑:
            1. 从 sop_states 数组读取所有状态配置
            2. 第一个状态作为初始状态
            3. 依次处理后续状态，根据 transitions 构建状态转移
            4. 遇到 is_end_state=True 的状态，绑定 END_JOURNEY
        """
        sop_states = sop_config.get("sop_states", [])
        
        if not sop_states:
            print(f"⚠️  SOP 未定义任何状态，跳过状态机构建")
            return
        
        state_map: Dict[str, Any] = {}
        
        # --- 处理初始状态 ---
        initial_state_config = sop_states[0]
        initial_guidelines = [
            sop_guideline_map.get(gid)
            for gid in initial_state_config.get("bind_guideline_ids", [])
            if sop_guideline_map.get(gid)
        ]
        
        current_state = await journey.initial_state.transition_to(
            chat_state=(
                initial_state_config["instruction"] 
                if initial_state_config["state_type"] == "chat" 
                else None
            ),
            tool_state=(
                self.instance_pool["tools"].get(initial_state_config.get("bind_tool_id")) 
                if initial_state_config["state_type"] == "tool" 
                else None
            ),
            guidelines=initial_guidelines
        )
        
        state_map[initial_state_config["state_id"]] = current_state
        print(f"📍 创建初始状态：{initial_state_config['state_name']}")
        
        # --- 处理后续状态 ---
        for state_config in sop_states[1:]:
            state_id = state_config["state_id"]
            state_name = state_config.get("state_name", f"State {state_id}")
            
            # 处理所有转移到当前状态的转移
            for transition in state_config.get("transitions", []):
                source_state_id = transition.get("target_state_id")
                source_state = state_map.get(source_state_id)
                
                if not source_state:
                    print(f"⚠️  状态 {state_id} 引用的源状态 {source_state_id} 不存在，跳过")
                    continue
                
                # 准备当前状态的 Guideline 和模板话术
                state_guidelines = [
                    sop_guideline_map.get(gid)
                    for gid in state_config.get("bind_guideline_ids", [])
                    if sop_guideline_map.get(gid)
                ]
                
                state_canned = [
                    sop_cr_map.get(cid) or self.instance_pool["canned_responses"].get(cid)
                    for cid in state_config.get("bind_canned_response_ids", [])
                    if sop_cr_map.get(cid) or cid in self.instance_pool["canned_responses"]
                ]
                
                # 创建状态转移
                new_state = await source_state.transition_to(
                    chat_state=(
                        state_config["instruction"] 
                        if state_config["state_type"] == "chat" 
                        else None
                    ),
                    tool_state=(
                        self.instance_pool["tools"].get(state_config.get("bind_tool_id")) 
                        if state_config["state_type"] == "tool" 
                        else None
                    ),
                    condition=transition.get("condition"),
                    guidelines=state_guidelines,
                    canned_responses=state_canned
                )
                
                state_map[state_id] = new_state
            
            print(f"📍 创建状态：{state_name}")
            
            # --- 处理结束状态 ---
            if state_config.get("is_end_state", False):
                end_state = state_map.get(state_id)
                if end_state:
                    await end_state.transition_to(state=p.END_JOURNEY)
                    print(f"🏁 标记结束状态：{state_name}")


# ============================================================================
# 主函数入口
# ============================================================================

async def main():
    """
    主函数入口
    
    命令行参数:
        sys.argv[1]: Agent 文件夹名称
        
    使用示例:
        python build_agent.py medical_customer_service_agent
        python build_agent.py airline_customer_service_agent
    """
    if len(sys.argv) > 1:
        agent_name = sys.argv[1]
        builder = IsolatedAgentBuilder()
        await builder.build(agent_name)
    else:
        # 显示使用说明
        print("\n" + "="*60)
        print("❌ 请指定要构建的完全隔离 Agent 文件夹名称")
        print("="*60)
        print("\n使用示例:")
        print("   python build_agent.py medical_customer_service_agent")
        print("   python build_agent.py airline_customer_service_agent")
        
        # 列出可用的 Agent
        agents_root = ROOT_PATH / "agents"
        if agents_root.exists():
            agent_folders = [f.name for f in agents_root.iterdir() if f.is_dir()]
            if agent_folders:
                print(f"\n💡 当前可用的 Agent:")
                for agent_name in agent_folders:
                    print(f"   - {agent_name}")
            else:
                print(f"\n⚠️  agents 目录下暂无可用的 Agent 文件夹")
        
        print("\n" + "="*60 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 检测到用户中断，正在退出...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 构建过程中发生错误：{str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
