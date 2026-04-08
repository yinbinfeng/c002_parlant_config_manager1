#!/usr/bin/env python3
"""
语法检查脚本 - 用于检查 mining_agents 目录中所有 Python 文件的语法
"""

import os
import sys
import ast
from pathlib import Path


def check_python_syntax(file_path):
    """检查 Python 文件的语法
    
    Args:
        file_path: Python 文件路径
        
    Returns:
        tuple: (是否有语法错误, 错误信息)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 使用 ast 模块检查语法
        ast.parse(content)
        return False, None
    except SyntaxError as e:
        return True, f"SyntaxError: {e.msg} at line {e.lineno}, column {e.offset}"
    except Exception as e:
        return True, f"Error: {str(e)}"


def traverse_directory(directory):
    """遍历目录中的所有 Python 文件
    
    Args:
        directory: 目录路径
        
    Returns:
        list: Python 文件路径列表
    """
    python_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files


def main():
    """主函数"""
    # 检查 mining_agents 目录
    mining_agents_dir = Path(__file__).parent / "src" / "mining_agents"
    
    if not mining_agents_dir.exists():
        print(f"Error: Directory {mining_agents_dir} does not exist")
        sys.exit(1)
    
    # 获取所有 Python 文件
    python_files = traverse_directory(mining_agents_dir)
    
    print(f"Found {len(python_files)} Python files to check")
    print("=" * 80)
    
    # 检查每个文件的语法
    error_count = 0
    for file_path in python_files:
        has_error, error_msg = check_python_syntax(file_path)
        if has_error:
            error_count += 1
            print(f"❌ {file_path}")
            print(f"   {error_msg}")
            print("-" * 80)
        else:
            print(f"✅ {file_path}")
    
    print("=" * 80)
    if error_count == 0:
        print("🎉 All files passed syntax check!")
    else:
        print(f"❌ {error_count} files have syntax errors")


if __name__ == "__main__":
    main()