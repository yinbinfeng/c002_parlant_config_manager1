"""测试项目基础结构"""

from pathlib import Path
import sys

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_project_structure():
    """测试项目目录结构"""
    root = Path(__file__).parent.parent
    
    # 检查核心目录
    assert (root / "src" / "mining_agents").exists()
    assert (root / "src" / "mining_agents" / "agents").exists()
    assert (root / "src" / "mining_agents" / "managers").exists()
    assert (root / "src" / "mining_agents" / "tools").exists()
    assert (root / "src" / "mining_agents" / "config").exists()
    assert (root / "src" / "mining_agents" / "utils").exists()
    
    # 检查功能目录
    assert (root / "output").exists()
    assert (root / "input").exists()
    assert (root / "logs").exists()
    assert (root / "config").exists()


def test_init_files():
    """测试__init__.py 文件存在"""
    root = Path(__file__).parent.parent / "src" / "mining_agents"
    
    assert (root / "__init__.py").exists()
    assert (root / "agents" / "__init__.py").exists()
    assert (root / "managers" / "__init__.py").exists()
    assert (root / "tools" / "__init__.py").exists()
    assert (root / "config" / "__init__.py").exists()
    assert (root / "utils" / "__init__.py").exists()


def test_config_files():
    """测试配置文件存在"""
    root = Path(__file__).parent.parent
    
    assert (root / "config" / "system_config.yaml").exists()
    assert (root / "config" / "agents" / "base_agent.yaml").exists()


def test_requirements_files():
    """测试依赖文件存在"""
    root = Path(__file__).parent.parent
    
    assert (root / "requirements.txt").exists()
    assert (root / "requirements-dev.txt").exists()
    assert (root / "README.md").exists()


def test_cli_import():
    """测试 CLI 可以导入"""
    from mining_agents.cli import parse_args, main
    assert parse_args is not None
    assert main is not None


def test_utils_import():
    """测试工具函数可以导入"""
    from mining_agents.utils import (
        setup_logger,
        get_step_logger,
        write_json,
        read_json,
        write_yaml,
        read_yaml
    )
    assert setup_logger is not None
    assert write_json is not None
