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
