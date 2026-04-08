# Mining Agents 项目 Scaffolding 实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 创建 mining_agents 项目的基础结构，包括目录结构、配置文件、入口脚本和基础工具类。

**Architecture:** 采用模块化设计，分离核心组件（Agents、Tools、Managers）、配置管理、和输出产物。遵循 AgentScope 框架的最佳实践，支持 MCP 协议集成。

**Tech Stack:** 
- Python 3.11
- AgentScope (多 Agent 协作框架)
- pip (包管理)
- DashScope LLM (模型提供商)
- Tavily MCP (搜索服务)
- json_repair (JSON 校验)
- pyyaml (配置文件解析)

---

## Task 1: 创建项目目录结构

**Files:**
- Create: `src/mining_agents/__init__.py`
- Create: `src/mining_agents/agents/__init__.py`
- Create: `src/mining_agents/managers/__init__.py`
- Create: `src/mining_agents/tools/__init__.py`
- Create: `src/mining_agents/config/__init__.py`
- Create: `src/mining_agents/utils/__init__.py`
- Create: `output/.gitkeep`
- Create: `input/.gitkeep`
- Create: `logs/.gitkeep`

**Step 1: 创建核心目录结构**

```bash
mkdir -p src/mining_agents/{agents,managers,tools,config,utils}
mkdir -p output input logs
```

**Step 2: 创建 __init__.py 文件**

```python
# src/mining_agents/__init__.py
"""Mining Agents - Parlant 配置挖掘系统"""

__version__ = "0.1.0"
__author__ = "System Team"
```

**Step 3: 创建子模块 __init__.py**

```python
# src/mining_agents/agents/__init__.py
"""Agent 模块 - 包含所有专业 Agent 实现"""
```

```python
# src/mining_agents/managers/__init__.py
"""管理器模块 - 包含 StepManager 和 AgentOrchestrator"""
```

```python
# src/mining_agents/tools/__init__.py
"""工具模块 - 包含 MCP 工具封装和本地工具"""
```

```python
# src/mining_agents/config/__init__.py
"""配置模块 - 包含配置加载和验证"""
```

```python
# src/mining_agents/utils/__init__.py
"""工具函数模块 - 包含日志、文件操作等辅助函数"""
```

**Step 4: 创建占位文件**

```bash
echo "" > output/.gitkeep
echo "" > input/.gitkeep
echo "" > logs/.gitkeep
```

**Step 5: 验证目录结构**

```bash
tree -L 3 src output input logs
```

Expected: 显示完整的目录树结构

**Step 6: 提交**

```bash
git add src/ output/ input/ logs/
git commit -m "feat(scaffold): 创建项目基础目录结构"
```

---

## Task 2: 创建系统配置文件

**Files:**
- Create: `config/system_config.yaml`
- Create: `config/agents/base_agent.yaml`
- Create: `scripts/validate_config.py`

**Step 1: 创建主配置文件**

```yaml
# config/system_config.yaml
# 系统级配置

# 并发控制
max_parallel_agents: 4        # 最大并发 Agent 数（1=串行）

# 步骤控制
start_step: 1                 # 起始步骤（1-8）
end_step: 8                   # 结束步骤（1-8）
force_rerun: false            # 是否强制重跑已完成的步骤
continue_on_error: false      # 错误时是否继续执行

# 输出配置
output_base_dir: "./output"   # 输出目录
enable_version_control: true  # 是否启用 Git 版本管理

# 私域对话数据（可选）
private_data:
  enabled: false              # 默认禁用，需要时开启
  excel_file_path: null       # Excel 文件路径
  auto_skip_if_missing: true  # 如果文件不存在，自动跳过 Step 6

# MCP 客户端配置
mcp_clients:
  tavily_search:
    enabled: true
    api_key_env: TAVILY_API_KEY
  embedding_service:
    type: SentenceTransformer
    model_name: paraphrase-multilingual-MiniLM-L12-v2

# JSON 校验配置
json_validation:
  max_retries: 3              # JSON 校验最大重试次数
  auto_fix: true              # 是否启用自动修复

# 日志配置
logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: logs/mining_agents.log
```

**Step 2: 创建 Agent 基础配置模板**

```yaml
# config/agents/base_agent.yaml
# Agent 基础配置模板

agent_name: BaseAgent
base_class: ReActAgent
description: "基础 Agent 模板"

model:
  type: DashScopeChatModel
  config:
    model_name: qwen3-max
    temperature: 0.7
    max_tokens: 4096

tools: []

system_prompt_template: null
output_schema: null
```

**Step 3: 创建配置验证脚本**

```python
#!/usr/bin/env python3
"""验证系统配置文件的正确性"""

import yaml
import sys
from pathlib import Path

def validate_system_config(config_path: str) -> bool:
    """验证 system_config.yaml"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 检查必需字段
        required_fields = ['max_parallel_agents', 'start_step', 'end_step', 'output_base_dir']
        for field in required_fields:
            if field not in config:
                print(f"❌ 缺少必需字段：{field}")
                return False
        
        # 检查值范围
        if not (1 <= config['max_parallel_agents'] <= 10):
            print("❌ max_parallel_agents 必须在 1-10 之间")
            return False
        
        if not (1 <= config['start_step'] <= 8):
            print("❌ start_step 必须在 1-8 之间")
            return False
        
        if not (1 <= config['end_step'] <= 8):
            print("❌ end_step 必须在 1-8 之间")
            return False
        
        if config['start_step'] > config['end_step']:
            print("❌ start_step 不能大于 end_step")
            return False
        
        print("✅ 配置验证通过")
        return True
    
    except Exception as e:
        print(f"❌ 配置验证失败：{e}")
        return False

if __name__ == "__main__":
    config_file = Path(__file__).parent.parent / "config" / "system_config.yaml"
    success = validate_system_config(str(config_file))
    sys.exit(0 if success else 1)
```

**Step 4: 运行配置验证**

```bash
python scripts/validate_config.py
```

Expected: 输出 "✅ 配置验证通过"

**Step 5: 提交**

```bash
git add config/ scripts/validate_config.py
git commit -m "feat(scaffold): 添加系统配置文件和验证脚本"
```

---

## Task 3: 创建项目入口脚本

**Files:**
- Create: `src/mining_agents/main.py`
- Create: `src/mining_agents/cli.py`

**Step 1: 创建命令行接口**

```python
#!/usr/bin/env python3
"""Mining Agents 命令行接口"""

import argparse
import sys
from pathlib import Path

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="Parlant Agent 配置挖掘系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 从第 1 步执行到第 8 步
  python -m mining_agents.main --business-desc "电商客服 Agent"
  
  # 从特定步骤开始（断点续跑）
  python -m mining_agents.main --start-step 5 --business-desc "..."
  
  # 强制重跑所有步骤
  python -m mining_agents.main --force-rerun --business-desc "..."
        """
    )
    
    parser.add_argument(
        "--business-desc", "-b",
        type=str,
        required=True,
        help="业务描述文本"
    )
    
    parser.add_argument(
        "--excel-file", "-e",
        type=str,
        default=None,
        help="私域对话数据 Excel 文件路径（可选）"
    )
    
    parser.add_argument(
        "--config", "-c",
        type=str,
        default="config/system_config.yaml",
        help="配置文件路径（默认：config/system_config.yaml）"
    )
    
    parser.add_argument(
        "--start-step",
        type=int,
        default=1,
        choices=range(1, 9),
        help="起始步骤（1-8，默认：1）"
    )
    
    parser.add_argument(
        "--end-step",
        type=int,
        default=8,
        choices=range(1, 9),
        help="结束步骤（1-8，默认：8）"
    )
    
    parser.add_argument(
        "--force-rerun",
        action="store_true",
        help="强制重跑已完成的步骤"
    )
    
    parser.add_argument(
        "--max-parallel",
        type=int,
        default=4,
        choices=range(1, 11),
        help="最大并发 Agent 数（1-10，默认：4）"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="启用详细日志"
    )
    
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_args()
    
    # 验证配置文件
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"❌ 配置文件不存在：{config_path}")
        sys.exit(1)
    
    # 验证 Excel 文件（如果提供）
    if args.excel_file:
        excel_path = Path(args.excel_file)
        if not excel_path.exists():
            print(f"⚠️  Excel 文件不存在：{excel_path}，将跳过 Step 6")
    
    # TODO: 初始化并运行系统
    print(f"✅ 参数验证通过")
    print(f"📝 业务描述：{args.business_desc[:50]}...")
    print(f"🔧 执行步骤：{args.start_step} → {args.end_step}")
    print(f"⚙️  并发数：{args.max_parallel}")
    
    # TODO: 调用 StepManager 执行流程
    # from .managers.step_manager import StepManager
    # manager = StepManager(config_path, args)
    # await manager.run(args.business_desc)
    
    print("🚀 系统初始化完成（待实现）")

if __name__ == "__main__":
    main()
```

**Step 2: 创建主入口模块**

```python
#!/usr/bin/env python3
"""Mining Agents 主入口"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from .cli import main

if __name__ == "__main__":
    main()
```

**Step 3: 测试 CLI**

```bash
python -m mining_agents.main --help
```

Expected: 显示帮助信息

**Step 4: 测试基本参数**

```bash
python -m mining_agents.main --business-desc "测试电商客服 Agent"
```

Expected: 输出 "✅ 参数验证通过" 和 "🚀 系统初始化完成（待实现）"

**Step 5: 提交**

```bash
git add src/mining_agents/main.py src/mining_agents/cli.py
git commit -m "feat(scaffold): 添加 CLI 入口和参数解析"
```

---

## Task 4: 创建日志配置工具

**Files:**
- Create: `src/mining_agents/utils/logger.py`
- Create: `src/mining_agents/utils/file_utils.py`

**Step 1: 创建日志工具**

```python
#!/usr/bin/env python3
"""日志配置工具"""

import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logger(
    name: str,
    log_file: str = None,
    level: int = logging.INFO,
    verbose: bool = False
) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        log_file: 日志文件路径（可选）
        level: 日志级别
        verbose: 是否启用 DEBUG 级别
    
    Returns:
        配置好的 Logger 对象
    """
    if verbose:
        level = logging.DEBUG
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加 handler
    if logger.handlers:
        return logger
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器（如果指定）
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_step_logger(step_num: int, verbose: bool = False) -> logging.Logger:
    """获取特定步骤的日志记录器"""
    log_file = f"logs/step{step_num}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    return setup_logger(f"Step{step_num}", log_file=log_file, verbose=verbose)
```

**Step 2: 创建文件操作工具**

```python
#!/usr/bin/env python3
"""文件操作工具"""

import json
import yaml
from pathlib import Path
from typing import Any, Dict

def ensure_dir(path: str) -> Path:
    """确保目录存在，如不存在则创建"""
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path

def write_json(data: Any, file_path: str, indent: int = 2, ensure_ascii: bool = False) -> Path:
    """写入 JSON 文件"""
    path = Path(file_path)
    ensure_dir(path.parent)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
    return path

def read_json(file_path: str) -> Any:
    """读取 JSON 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_yaml(data: Dict, file_path: str, ensure_ascii: bool = False) -> Path:
    """写入 YAML 文件"""
    path = Path(file_path)
    ensure_dir(path.parent)
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=ensure_ascii, default_flow_style=False)
    return path

def read_yaml(file_path: str) -> Dict:
    """读取 YAML 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def write_markdown(content: str, file_path: str) -> Path:
    """写入 Markdown 文件"""
    path = Path(file_path)
    ensure_dir(path.parent)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    return path

def file_exists(file_path: str) -> bool:
    """检查文件是否存在"""
    return Path(file_path).exists()

def get_output_dir(output_base: str, step_num: int) -> Path:
    """获取步骤输出目录"""
    return ensure_dir(Path(output_base) / f"step{step_num}")
```

**Step 3: 创建工具模块 __init__.py**

```python
# src/mining_agents/utils/__init__.py
"""工具函数模块"""

from .logger import setup_logger, get_step_logger
from .file_utils import (
    ensure_dir,
    write_json,
    read_json,
    write_yaml,
    read_yaml,
    write_markdown,
    file_exists,
    get_output_dir
)

__all__ = [
    'setup_logger',
    'get_step_logger',
    'ensure_dir',
    'write_json',
    'read_json',
    'write_yaml',
    'read_yaml',
    'write_markdown',
    'file_exists',
    'get_output_dir'
]
```

**Step 4: 测试工具函数**

```bash
python -c "
from src.mining_agents.utils import setup_logger, write_json
logger = setup_logger('test')
logger.info('测试日志')
write_json({'test': 'data'}, 'output/test.json')
print('✅ 工具函数测试通过')
"
```

**Step 5: 提交**

```bash
git add src/mining_agents/utils/
git commit -m "feat(scaffold): 添加日志和文件操作工具"
```

---

## Task 5: 创建依赖配置文件

**Files:**
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `README.md`

**Step 1: 创建主依赖文件**

```txt
# requirements.txt
# Mining Agents 核心依赖

# AgentScope 框架
agentscope>=1.0.0

# LLM 提供商
dashscope>=1.14.0

# MCP 客户端
mcp>=0.1.0

# 搜索服务
tavily-python>=0.3.0

# 配置解析
pyyaml>=6.0

# JSON 校验
json-repair>=0.25.0
jsonschema>=4.19.0

# Embedding
sentence-transformers>=2.2.2

# 数据处理
pandas>=2.0.0
openpyxl>=3.1.0  # Excel 支持

# 工具库
python-dotenv>=1.0.0
aiohttp>=3.9.0
```

**Step 2: 创建开发依赖**

```txt
# requirements-dev.txt
# 开发环境依赖

-r requirements.txt

# 代码质量
black>=23.0.0
flake8>=6.0.0
mypy>=1.5.0
isort>=5.12.0

# 测试
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0

# 调试
ipdb>=0.13.0

# 文档
mkdocs>=1.5.0
mkdocs-material>=9.4.0
```

**Step 3: 创建项目 README**

```markdown
# Mining Agents - Parlant 配置挖掘系统

基于 AgentScope 框架的多 Agent 协作系统，用于自动化生成 Parlant 客服 Agent 的完整配置包。

## 功能特性

- 🤖 **多 Agent 协作**: 8 个专业 Agent 分工协作，模拟人类咨询团队工作模式
- 🔍 **深度研究**: 集成 Deep Research Agent，从互联网挖掘行业最佳实践
- 📊 **私域数据挖掘**: 支持从 Excel 对话数据中提取企业特有实践
- ✅ **质量保障**: 内置 json_repair 校验和边缘情况覆盖检查
- ⚡ **灵活并发**: 支持串行/并行模式切换，可配置并发数
- 🔄 **断点续跑**: 每步独立存储，支持从特定步骤恢复执行

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 设置环境变量

```bash
export DASHSCOPE_API_KEY="your_dashscope_api_key"
export TAVILY_API_KEY="your_tavily_api_key"
```

### 运行系统

```bash
python -m mining_agents.main \
  --business-desc "电商客服 Agent，处理订单查询和退换货" \
  --config config/system_config.yaml
```

### 高级用法

```bash
# 从特定步骤开始（断点续跑）
python -m mining_agents.main \
  --business-desc "..." \
  --start-step 5 \
  --end-step 8

# 使用私域对话数据
python -m mining_agents.main \
  --business-desc "..." \
  --excel-file ./input/conversations.xlsx

# 强制重跑所有步骤
python -m mining_agents.main \
  --business-desc "..." \
  --force-rerun \
  --max-parallel 2
```

## 项目结构

```
mining_agents/
├── src/mining_agents/       # 源代码
│   ├── agents/             # Agent 实现
│   ├── managers/           # 步骤和编排管理器
│   ├── tools/              # MCP 工具封装
│   ├── config/             # 配置管理
│   └── utils/              # 工具函数
├── config/                  # 配置文件
│   ├── system_config.yaml  # 系统配置
│   └── agents/             # Agent 配置
├── output/                  # 输出产物
├── input/                   # 输入数据
├── logs/                    # 日志文件
└── docs/                    # 文档
    ├── plans/              # 实现计划
    └── design_docs/        # 设计文档
```

## 开发指南

### 运行测试

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

### 代码格式化

```bash
black src/ tests/
isort src/ tests/
flake8 src/ tests/
```

## 许可证

MIT License
```

**Step 4: 提交**

```bash
git add requirements.txt requirements-dev.txt README.md
git commit -m "feat(scaffold): 添加依赖配置和项目文档"
```

---

## Task 6: 创建基础测试框架

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/test_scaffolding.py`
- Create: `pytest.ini`

**Step 1: 创建 pytest 配置**

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts = -v --tb=short
```

**Step 2: 创建测试夹具**

```python
# tests/conftest.py
"""pytest 测试夹具"""

import pytest
from pathlib import Path
import tempfile
import shutil

@pytest.fixture
def temp_dir():
    """创建临时目录"""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)

@pytest.fixture
def sample_business_desc():
    """示例业务描述"""
    return "电商客服 Agent，处理订单查询、退换货和商品咨询"

@pytest.fixture
def sample_config_dict():
    """示例配置字典"""
    return {
        "max_parallel_agents": 4,
        "start_step": 1,
        "end_step": 8,
        "output_base_dir": "./output",
        "private_data": {
            "enabled": False,
            "excel_file_path": None,
            "auto_skip_if_missing": True
        }
    }
```

**Step 3: 创建基础测试**

```python
# tests/test_scaffolding.py
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
```

**Step 4: 运行测试**

```bash
pip install -r requirements-dev.txt
pytest tests/test_scaffolding.py -v
```

Expected: 所有测试通过

**Step 5: 提交**

```bash
git add tests/ pytest.ini
git commit -m "feat(scaffold): 添加测试框架和基础测试"
```

---

## Task 7: 创建.gitignore 文件

**Files:**
- Create: `.gitignore`
- Create: `.env.example`

**Step 1: 创建.gitignore**

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# 虚拟环境
venv/
env/
ENV/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# 环境变量
.env
.env.local

# 敏感数据
*.pem
*.key
credentials.json

# 输出和日志
output/*.json
output/*.md
output/*.yaml
logs/*.log
logs/*.txt
!output/.gitkeep
!logs/.gitkeep

# 临时文件
*.tmp
.tmp/
.cache/

# 测试
.pytest_cache/
.coverage
htmlcov/
.tox/

# Jupyter
.ipynb_checkpoints

# OS
.DS_Store
Thumbs.db
```

**Step 2: 创建环境变量示例**

```bash
# .env.example
# 复制此文件为 .env 并填入实际值

# LLM 提供商 API Key
DASHSCOPE_API_KEY=your_dashscope_api_key_here

# 搜索服务 API Key
TAVILY_API_KEY=your_tavily_api_key_here

# 可选：Embedding 服务配置
EMBEDDING_MODEL_NAME=paraphrase-multilingual-MiniLM-L12-v2

# 可选：自定义输出目录
OUTPUT_BASE_DIR=./output
```

**Step 3: 提交**

```bash
git add .gitignore .env.example
git commit -m "feat(scaffold): 添加.gitignore 和环境变量示例"
```

---

## 完成检查清单

完成所有任务后，验证以下内容：

```bash
# 1. 检查目录结构
tree -L 3 -I '__pycache__|*.pyc'

# 2. 运行配置验证
python scripts/validate_config.py

# 3. 测试 CLI
python -m mining_agents.main --help
python -m mining_agents.main --business-desc "测试"

# 4. 运行测试
pytest tests/ -v

# 5. 检查代码质量
flake8 src/ tests/
black --check src/ tests/

# 6. 查看 git 状态
git status
git log --oneline
```

---

## 下一步

Scaffolding 完成后，继续实现以下核心组件：

1. **StepManager** - 步骤调度与状态管理
2. **AgentOrchestrator** - Agent 编排与并发控制
3. **RequirementAnalystAgent** - 需求分析 Agent（Step 1）
4. **DeepResearchAgent 封装** - 深度研究工具集成

---

**Plan complete and saved to `docs/plans/2026-03-20-mining-agents-scaffolding.md`. Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
