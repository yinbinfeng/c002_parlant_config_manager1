#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parlant Agent 配置构建脚本
支持指定单个 Agent 独立构建，将配置文件加载到 Parlant 框架中

使用方法:
    # 构建单个 Agent
    python build_agent.py --agent medical_customer_service_agent
    
    # 构建所有 Agents
    python build_agent.py --all
    
    # 查看帮助
    python build_agent.py --help
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any


class AgentConfigBuilder:
    """Agent 配置构建器"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.base_dir = Path(__file__).parent
        self.agent_dir = self.base_dir / "agents" / agent_name
        
        if not self.agent_dir.exists():
            raise ValueError(f"Agent 目录不存在：{self.agent_dir}")
        
        # 配置文件路径
        self.config_paths = {
            'metadata': self.agent_dir / "00_agent_base" / "agent_metadata.json",
            'observability': self.agent_dir / "00_agent_base" / "agent_observability.json",
            'glossary_dir': self.agent_dir / "00_agent_base" / "glossary",
            'observations': self.agent_dir / "01_agent_rules" / "agent_observations.json",
            'canned_responses': self.agent_dir / "01_agent_rules" / "agent_canned_responses.json",
            'guidelines': self.agent_dir / "01_agent_rules" / "agent_guidelines.json",
            'journeys_dir': self.agent_dir / "02_journeys",
            'tools_dir': self.agent_dir / "03_tools"
        }
    
    def load_json(self, file_path: Path) -> Dict[str, Any]:
        """加载 JSON 文件"""
        if not file_path.exists():
            print(f"⚠️  警告：文件不存在 {file_path}")
            return {}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_all_glossary(self) -> List[Dict[str, Any]]:
        """加载所有术语表"""
        glossary_dir = self.config_paths['glossary_dir']
        if not glossary_dir.exists():
            return []
        
        glossaries = []
        for json_file in glossary_dir.glob("*.json"):
            glossary_data = self.load_json(json_file)
            if glossary_data:
                glossaries.append(glossary_data)
        
        return glossaries
    
    def load_all_journeys(self) -> List[Dict[str, Any]]:
        """加载所有 SOP 旅程"""
        journeys_dir = self.config_paths['journeys_dir']
        if not journeys_dir.exists():
            return []
        
        journeys = []
        for journey_dir in journeys_dir.iterdir():
            if not journey_dir.is_dir():
                continue
            
            # 加载 SOP 核心文件
            sop_file = journey_dir / "sop.json"
            if sop_file.exists():
                sop_data = self.load_json(sop_file)
                
                # 加载 SOP 专属观测
                obs_file = journey_dir / "sop_observations.json"
                if obs_file.exists():
                    sop_data['sop_observations'] = self.load_json(obs_file)
                
                # 加载 SOP 专属规则
                guidelines_file = journey_dir / "sop_guidelines.json"
                if guidelines_file.exists():
                    sop_data['sop_guidelines'] = self.load_json(guidelines_file)
                
                journeys.append(sop_data)
        
        return journeys
    
    def load_all_tools(self) -> List[Dict[str, Any]]:
        """加载所有工具"""
        tools_dir = self.config_paths['tools_dir']
        if not tools_dir.exists():
            return []
        
        tools = []
        for tool_dir in tools_dir.iterdir():
            if not tool_dir.is_dir():
                continue
            
            # 加载工具元信息
            meta_file = tool_dir / "tool_meta.json"
            if meta_file.exists():
                tool_data = self.load_json(meta_file)
                tool_data['impl_path'] = str(tool_dir / "tool_impl.py")
                tools.append(tool_data)
        
        return tools
    
    def build(self) -> Dict[str, Any]:
        """构建完整的 Agent 配置"""
        print(f"\n🚀 开始构建 Agent: {self.agent_name}")
        
        config = {
            'agent_name': self.agent_name,
            'metadata': self.load_json(self.config_paths['metadata']),
            'observability': self.load_json(self.config_paths['observability']),
            'glossaries': self.load_all_glossary(),
            'observations': self.load_json(self.config_paths['observations']),
            'canned_responses': self.load_json(self.config_paths['canned_responses']),
            'guidelines': self.load_json(self.config_paths['guidelines']),
            'journeys': self.load_all_journeys(),
            'tools': self.load_all_tools()
        }
        
        # 统计信息
        print(f"✅ 基础配置加载完成")
        print(f"   - 术语表：{len(config['glossaries'])} 个")
        print(f"   - 全局观测：{len(config['observations'].get('agent_observations', []))} 个")
        print(f"   - 全局话术：{len(config['canned_responses'].get('agent_canned_responses', []))} 个")
        print(f"   - 全局规则：{len(config['guidelines'].get('agent_guidelines', []))} 个")
        print(f"   - SOP 旅程：{len(config['journeys'])} 个")
        print(f"   - 工具：{len(config['tools'])} 个")
        
        return config
    
    def validate(self, config: Dict[str, Any]) -> bool:
        """验证配置完整性"""
        print(f"\n🔍 验证配置完整性...")
        
        errors = []
        
        # 检查必填字段
        if not config.get('metadata'):
            errors.append("缺少 metadata 配置")
        
        # 检查 SOP 配置
        for journey in config.get('journeys', []):
            if not journey.get('sop_id'):
                errors.append(f"SOP 缺少 sop_id")
            if not journey.get('sop_states'):
                errors.append(f"SOP {journey.get('sop_id')} 缺少状态机配置")
        
        # 检查工具配置
        for tool in config.get('tools', []):
            if not tool.get('tool_id'):
                errors.append(f"工具缺少 tool_id")
            if not tool.get('implementation_file'):
                errors.append(f"工具 {tool.get('tool_id')} 缺少实现文件")
        
        if errors:
            print("❌ 配置验证失败:")
            for error in errors:
                print(f"   - {error}")
            return False
        
        print("✅ 配置验证通过")
        return True


def build_single_agent(agent_name: str):
    """构建单个 Agent"""
    try:
        builder = AgentConfigBuilder(agent_name)
        config = builder.build()
        
        # 验证配置
        if not builder.validate(config):
            sys.exit(1)
        
        # 输出配置摘要
        print(f"\n📦 Agent 配置构建完成!")
        print(f"   Agent ID: {config['metadata'].get('agent_id', 'N/A')}")
        print(f"   Agent 名称：{config['metadata'].get('agent_name', 'N/A')}")
        print(f"   端口号：{config['metadata'].get('playground_port', 'N/A')}")
        
        # TODO: 在这里添加将配置加载到 Parlant 框架的逻辑
        # 例如：调用 Parlant SDK 的 API 注册 Agent、SOP、工具等
        print(f"\n💡 下一步：将配置加载到 Parlant 框架中")
        
        return config
        
    except Exception as e:
        print(f"❌ 构建失败：{str(e)}")
        sys.exit(1)


def build_all_agents():
    """构建所有 Agent"""
    base_dir = Path(__file__).parent
    agents_dir = base_dir / "agents"
    
    if not agents_dir.exists():
        print("❌ Agents 目录不存在")
        sys.exit(1)
    
    agent_names = [d.name for d in agents_dir.iterdir() if d.is_dir()]
    
    if not agent_names:
        print("❌ 未找到任何 Agent")
        sys.exit(1)
    
    print(f"📊 找到 {len(agent_names)} 个 Agent: {', '.join(agent_names)}\n")
    
    for agent_name in agent_names:
        build_single_agent(agent_name)
        print("\n" + "="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='Parlant Agent 配置构建脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python build_agent.py --agent medical_customer_service_agent  # 构建医疗客服 Agent
  python build_agent.py --all                                   # 构建所有 Agent
        """
    )
    
    parser.add_argument(
        '--agent',
        type=str,
        help='指定要构建的 Agent 名称（文件夹名）'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='构建所有可用的 Agent'
    )
    
    args = parser.parse_args()
    
    if args.agent:
        build_single_agent(args.agent)
    elif args.all:
        build_all_agents()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
