#!/usr/bin/env python3
"""
简单语法检查脚本 - 用于检查 mining_agents 目录中所有 Python 文件的语法
"""

import os
import sys
from pathlib import Path


def check_file_syntax(file_path):
    """检查单个文件的语法"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        compile(code, file_path, 'exec')
        return True, None
    except SyntaxError as e:
        return False, f"SyntaxError: {e.msg} at line {e.lineno}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def main():
    """主函数"""
    # 定义目录路径
    mining_agents_dir = Path('src') / 'mining_agents'
    
    if not mining_agents_dir.exists():
        print(f"Error: Directory {mining_agents_dir} does not exist")
        sys.exit(1)
    
    # 收集所有 Python 文件
    python_files = []
    for root, dirs, files in os.walk(mining_agents_dir):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    print(f"Found {len(python_files)} Python files to check")
    print("=" * 60)
    
    # 检查每个文件
    errors = []
    for file_path in python_files:
        is_valid, error_msg = check_file_syntax(file_path)
        if is_valid:
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path}")
            print(f"  {error_msg}")
            errors.append((file_path, error_msg))
    
    print("=" * 60)
    if errors:
        print(f"Found {len(errors)} files with syntax errors:")
        for file_path, error_msg in errors:
            print(f"- {file_path}: {error_msg}")
    else:
        print("All files have valid syntax!")


if __name__ == "__main__":
    main()