#!/usr/bin/env python3
"""
Mining Agents v0.1.0 - 5-Step Pipeline
Main Entry Point

Usage:
    # From project root directory
    python egs/v0.1.0_minging_agents/main.py --business-desc "Your business description"
    
    # Or use the run scripts
    Windows: egs\\v0.1.0_minging_agents\\scripts\\run_all_steps.bat
    Linux/Mac: bash egs/v0.1.0_minging_agents/scripts/run_all_steps.sh
"""

import sys
from pathlib import Path
import os

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.mining_agents.cli import main

if __name__ == "__main__":
    # 默认从指定 env 文件加载（如存在），实际加载逻辑在 src/mining_agents/cli.py 中统一处理
    env_file_path = r"E:\cursorworkspace\c002_parlant_config_manager1\.env"
    if "--env-file" not in sys.argv and os.path.exists(env_file_path):
        sys.argv.extend(["--env-file", env_file_path])
    main()
