#!/usr/bin/env python3
"""文件服务管理器 - 基于 AgentScope 内置工具"""

from typing import Any, Dict, List, Optional
from pathlib import Path
import json
import yaml
import os
import platform

from ..utils.logger import logger

# 尝试导入 AgentScopeToolkit，如果失败则使用 Mock 实现
try:
    from .agentscope_tools import AgentScopeToolkit
    HAS_AGENTSCOPE = True
except ImportError:
    HAS_AGENTSCOPE = False


class MockToolkit:
    """Mock 工具包，用于替代 AgentScopeToolkit
    
    实现与 AgentScopeToolkit 相同的接口，但使用 Python 内置的文件操作函数。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logger
        self.logger.info("MockToolkit initialized")
    
    async def read_file(self, file_path: str) -> str:
        """读取文本文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    async def write_file(self, file_path: str, content: str, overwrite: bool = True) -> bool:
        """写入文本文件"""
        # 确保目录存在
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    
    async def create_dir(self, dir_path: str) -> bool:
        """创建目录"""
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        return True
    
    async def list_directory(self, dir_path: str) -> List[str]:
        """列出目录内容"""
        return [item.name for item in Path(dir_path).iterdir()]
    
    async def delete(self, file_path: str) -> bool:
        """删除文件"""
        if Path(file_path).exists():
            Path(file_path).unlink()
            return True
        return False
    
    async def move(self, src_path: str, dst_path: str) -> bool:
        """移动文件"""
        # 确保目标目录存在
        Path(dst_path).parent.mkdir(parents=True, exist_ok=True)
        # 移动文件
        Path(src_path).rename(dst_path)
        return True
    
    async def copy(self, src_path: str, dst_path: str) -> bool:
        """复制文件"""
        # 确保目标目录存在
        Path(dst_path).parent.mkdir(parents=True, exist_ok=True)
        # 复制文件
        import shutil
        shutil.copy2(src_path, dst_path)
        return True
    
    async def execute_shell(self, command: str) -> str:
        """执行 Shell 命令"""
        import subprocess
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        return result.stdout + result.stderr
    
    async def close(self):
        """清理资源"""
        pass


class FileServiceManager:
    """文件服务管理器
    
    基于 AgentScope 内置工具提供高级文件操作服务。
    支持：
    - 文件读写（文本、JSON、YAML）
    - 目录管理
    - 文件搜索
    - 批量操作
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化文件服务管理器
        
        Args:
            config: 配置字典（可选）
        """
        self.config = config or {}
        self.logger = logger
        
        # 初始化工具包
        if HAS_AGENTSCOPE:
            self.toolkit = AgentScopeToolkit(config=self.config)
            self.logger.info("FileServiceManager initialized with AgentScopeToolkit")
        else:
            self.toolkit = MockToolkit(config=self.config)
            self.logger.warning("AgentScopeToolkit 导入失败，将在 Mock 模式下运行")
            self.logger.info("FileServiceManager initialized with MockToolkit")
    
    async def read_text(self, file_path: str) -> str:
        """读取文本文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件内容
        """
        return await self.toolkit.read_file(file_path)
    
    async def write_text(
        self, 
        file_path: str, 
        content: str,
        overwrite: bool = True
    ) -> bool:
        """写入文本文件
        
        Args:
            file_path: 文件路径
            content: 文件内容
            overwrite: 是否覆盖已存在的文件
            
        Returns:
            是否成功
        """
        return await self.toolkit.write_file(file_path, content, overwrite)
    
    async def read_json(self, file_path: str) -> Any:
        """读取 JSON 文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            解析后的数据
        """
        content = await self.toolkit.read_file(file_path)
        return json.loads(content)
    
    async def write_json(
        self, 
        file_path: str, 
        data: Any,
        indent: int = 2,
        ensure_ascii: bool = False
    ) -> bool:
        """写入 JSON 文件
        
        Args:
            file_path: 文件路径
            data: 数据对象
            indent: 缩进空格数
            ensure_ascii: 是否转义非 ASCII 字符
            
        Returns:
            是否成功
        """
        content = json.dumps(data, indent=indent, ensure_ascii=ensure_ascii)
        return await self.toolkit.write_file(file_path, content)
    
    async def read_yaml(self, file_path: str) -> Any:
        """读取 YAML 文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            解析后的数据
        """
        content = await self.toolkit.read_file(file_path)
        return yaml.safe_load(content)
    
    async def write_yaml(
        self, 
        file_path: str, 
        data: Any,
        allow_unicode: bool = True
    ) -> bool:
        """写入 YAML 文件
        
        Args:
            file_path: 文件路径
            data: 数据对象
            allow_unicode: 是否允许 Unicode 字符
            
        Returns:
            是否成功
        """
        content = yaml.dump(
            data, 
            allow_unicode=allow_unicode,
            default_flow_style=False,
            sort_keys=False
        )
        return await self.toolkit.write_file(file_path, content)
    
    async def create_directory(self, dir_path: str) -> bool:
        """创建目录（包括父目录）
        
        Args:
            dir_path: 目录路径
            
        Returns:
            是否成功
        """
        return await self.toolkit.create_dir(dir_path)
    
    async def list_directory(self, dir_path: str) -> List[str]:
        """列出目录内容
        
        Args:
            dir_path: 目录路径
            
        Returns:
            文件和目录名称列表
        """
        return await self.toolkit.list_directory(dir_path)
    
    async def delete_file(self, file_path: str) -> bool:
        """删除文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否成功
        """
        return await self.toolkit.delete(file_path)
    
    async def move_file(self, src_path: str, dst_path: str) -> bool:
        """移动文件
        
        Args:
            src_path: 源文件路径
            dst_path: 目标文件路径
            
        Returns:
            是否成功
        """
        return await self.toolkit.move(src_path, dst_path)
    
    async def copy_file(self, src_path: str, dst_path: str) -> bool:
        """复制文件
        
        Args:
            src_path: 源文件路径
            dst_path: 目标文件路径
            
        Returns:
            是否成功
        """
        return await self.toolkit.copy(src_path, dst_path)
    
    async def ensure_directory(self, dir_path: str) -> bool:
        """确保目录存在，如不存在则创建
        
        Args:
            dir_path: 目录路径
            
        Returns:
            是否成功
        """
        path = Path(dir_path)
        if path.exists():
            return True
        return await self.create_directory(dir_path)
    
    async def get_file_size(self, file_path: str) -> int:
        """获取文件大小（字节）
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件大小
        """
        # 使用 shell 命令获取文件大小
        import platform
        system = platform.system()
        
        if system == "Windows":
            command = f'powershell -Command "(Get-Item \'{file_path}\').Length"'
        else:
            command = f"stat -c %s {file_path}"
        
        result = await self.toolkit.execute_shell(command)
        return int(result.strip())
    
    async def file_exists(self, file_path: str) -> bool:
        """检查文件是否存在
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否存在
        """
        try:
            # 尝试读取文件，如果成功则存在
            await self.toolkit.read_file(file_path)
            return True
        except Exception:
            return False
    
    async def directory_exists(self, dir_path: str) -> bool:
        """检查目录是否存在
        
        Args:
            dir_path: 目录路径
            
        Returns:
            是否存在
        """
        try:
            # 尝试列出目录，如果成功则存在
            await self.toolkit.list_directory(dir_path)
            return True
        except Exception:
            return False
    
    async def search_files(
        self, 
        dir_path: str, 
        pattern: str = "*.py",
        recursive: bool = True
    ) -> List[str]:
        """搜索文件
        
        Args:
            dir_path: 目录路径
            pattern: 文件名模式（支持通配符）
            recursive: 是否递归搜索子目录
            
        Returns:
            匹配的文件路径列表
        """
        import platform
        system = platform.system()
        
        if system == "Windows":
            if recursive:
                command = f'dir /s /b "{dir_path}\\{pattern}"'
            else:
                command = f'dir /b "{dir_path}\\{pattern}"'
        else:
            if recursive:
                command = f'find {dir_path} -name "{pattern}"'
            else:
                command = f'ls -d {dir_path}/{pattern}'
        
        result = await self.toolkit.execute_shell(command)
        
        # 解析结果
        files = []
        for line in result.strip().split('\n'):
            line = line.strip()
            if line:
                files.append(line)
        
        return files
    
    async def get_directory_structure(
        self, 
        dir_path: str,
        max_depth: int = 3,
        current_depth: int = 0
    ) -> Dict[str, Any]:
        """获取目录结构
        
        Args:
            dir_path: 目录路径
            max_depth: 最大深度
            current_depth: 当前深度
            
        Returns:
            目录结构字典
        """
        if current_depth >= max_depth:
            return {"type": "directory", "name": Path(dir_path).name, "truncated": True}
        
        items = await self.list_directory(dir_path)
        
        structure = {
            "type": "directory",
            "name": Path(dir_path).name,
            "children": [],
        }
        
        for item in items:
            item_path = Path(dir_path) / item
            
            # 跳过隐藏文件和目录
            if item.startswith('.'):
                continue
            
            try:
                # 尝试列出，如果是目录则递归
                sub_items = await self.list_directory(str(item_path))
                child_structure = await self.get_directory_structure(
                    str(item_path),
                    max_depth,
                    current_depth + 1
                )
                structure["children"].append(child_structure)
            except Exception:
                # 是文件
                structure["children"].append({
                    "type": "file",
                    "name": item,
                })
        
        return structure
    
    async def cleanup(self):
        """清理资源"""
        self.logger.info("FileServiceManager closing")
        await self.toolkit.close()
