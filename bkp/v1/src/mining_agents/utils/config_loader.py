#!/usr/bin/env python3
"""配置加载器 - 用于加载和管理代理配置"""

from typing import Dict, Any, Optional
from pathlib import Path
import os
import yaml
import json
import time
import re
from .logger import logger


class ConfigLoader:
    """配置加载器类"""
    
    def __init__(self, config_dir: str):
        """初始化配置加载器
        
        Args:
            config_dir: 配置目录路径
        """
        self.config_dir = Path(config_dir)
        self.logger = logger
        self._cache = {}

    def _debug_log(self, run_id: str, hypothesis_id: str, location: str, message: str, data: Dict[str, Any]):
        # region agent log
        try:
            log_path = Path(__file__).resolve().parents[3] / "debug-ced296.log"
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "sessionId": "ced296",
                    "runId": run_id,
                    "hypothesisId": hypothesis_id,
                    "location": location,
                    "message": message,
                    "data": data,
                    "timestamp": int(time.time() * 1000),
                }, ensure_ascii=False) + "\n")
        except Exception:
            pass
        # endregion

    def _to_snake_case(self, name: str) -> str:
        return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
    
    def load_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """加载代理配置
        
        Args:
            agent_name: 代理名称
            
        Returns:
            代理配置字典
        """
        normalized = self._to_snake_case(agent_name)
        candidate_names = [
            f"{agent_name.lower()}.yaml",
            f"{normalized}.yaml",
            f"{normalized}_agent.yaml",
        ]
        config_file = None
        for candidate in candidate_names:
            p = self.config_dir / candidate
            if p.exists():
                config_file = p
                break
        if config_file is None:
            config_file = self.config_dir / candidate_names[0]
        self._debug_log(
            run_id="post-fix",
            hypothesis_id="H1",
            location="config_loader.py:49",
            message="Resolving agent config file path",
            data={
                "agent_name": agent_name,
                "candidate_names": candidate_names,
                "resolved_config_file": str(config_file),
                "config_exists": config_file.exists(),
            },
        )
        
        if config_file in self._cache:
            return self._cache[config_file]
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            self._debug_log(
                run_id="post-fix",
                hypothesis_id="H1",
                location="config_loader.py:70",
                message="Agent config loaded",
                data={
                    "agent_name": agent_name,
                    "top_level_keys": list((config or {}).keys()),
                },
            )
            
            self.logger.info(f"Loaded config for agent: {agent_name}")
            self._cache[config_file] = config
            return config
        except FileNotFoundError:
            self.logger.warning(f"Config file not found for agent: {agent_name}")
            return self._get_default_config(agent_name)
        except Exception as e:
            self.logger.error(f"Failed to load config for agent {agent_name}: {e}")
            return self._get_default_config(agent_name)
    
    def _get_default_config(self, agent_name: str) -> Dict[str, Any]:
        """获取最小化默认配置
        
        Args:
            agent_name: 代理名称
            
        Returns:
            默认配置字典
        """
        return {
            'agent_name': agent_name,
            'model': {
                'model_name': 'Qwen/Qwen3.5-27B',
                'temperature': 0.7
            },
            'tools': []
        }
    
    def load_system_config(self) -> Dict[str, Any]:
        """加载系统配置
        
        Returns:
            系统配置字典
        """
        config_file = self.config_dir.parent / "system_config.yaml"
        
        if config_file in self._cache:
            return self._cache[config_file]
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            self.logger.info("Loaded system config")
            self._cache[config_file] = config
            return config
        except FileNotFoundError:
            self.logger.warning("System config file not found")
            return self._get_default_system_config()
        except Exception as e:
            self.logger.error(f"Failed to load system config: {e}")
            return self._get_default_system_config()
    
    def load_prompt_template(self, template_path: str) -> str:
        """加载提示词模板
        
        Args:
            template_path: 提示词模板路径
            
        Returns:
            提示词模板内容
        """
        template_file = self.config_dir.parent / template_path
        
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.logger.info(f"Loaded prompt template: {template_path}")
            return content
        except FileNotFoundError:
            self.logger.warning(f"Prompt template not found: {template_path}")
            return ""
        except Exception as e:
            self.logger.error(f"Failed to load prompt template: {e}")
            return ""
    
    def _get_default_system_config(self) -> Dict[str, Any]:
        """获取默认系统配置
        
        Returns:
            默认系统配置字典
        """
        return {
            'max_parallel_agents': 1,
            'start_step': 1,
            'end_step': 5,
            'force_rerun': False,
            'continue_on_error': False,
            'output_base_dir': '../../output',
            'enable_version_control': True,
            'private_data': {
                'enabled': False,
                'excel_file_path': None,
                'auto_skip_if_missing': True
            },
            'mcp_clients': {
                'tavily_search': {
                    'enabled': True,
                    # 默认只允许环境变量名，禁止写明文 Key
                    'api_key_env': 'TAVILY_API_KEY'
                },
                'embedding_service': {
                    'type': 'OpenAI',  # 使用 OpenAI API 进行 Embedding
                    'model_name': 'text-embedding-v3'  # OpenAI Embedding 模型
                }
            },
            'openai': {
                'enabled': False,
                # 仅允许环境变量名，禁止写明文 Key
                'api_key_env': 'OPENAI_API_KEY',
                'base_url_env': 'OPENAI_BASE_URL'
            },
            'prompts': {
                'templates_dir': 'prompts'
            },
            'json_validation': {
                'max_retries': 3,
                'auto_fix': True
            },
            'logging': {
                'level': 'INFO'
            },
            'version': {
                'name': 'v0.1.0',
                'description': 'Default configuration',
                'release_date': '2026-03-21',
                'features': []
            }
        }


# 全局配置加载器实例
_config_loader = None


def get_config_loader(config_dir: str = None) -> ConfigLoader:
    """获取配置加载器实例
    
    Args:
        config_dir: 配置目录路径（可选，可通过环境变量 MINING_AGENTS_CONFIG_DIR 指定）
        
    Returns:
        配置加载器实例
    """
    global _config_loader
    if _config_loader is None:
        if config_dir is None:
            # 优先级：环境变量 > 默认路径
            env_config_dir = os.getenv('MINING_AGENTS_CONFIG_DIR')
            if env_config_dir:
                config_dir = env_config_dir
                _config_loader = ConfigLoader(env_config_dir)
                _config_loader.logger.info(f"Loaded config from environment: {env_config_dir}")
            else:
                # 默认配置目录
                default_config_dir = Path(__file__).parent.parent.parent.parent / "egs" / "v0.1.0_minging_agents" / "config" / "agents"
                _config_loader = ConfigLoader(str(default_config_dir))
        else:
            _config_loader = ConfigLoader(config_dir)
    return _config_loader