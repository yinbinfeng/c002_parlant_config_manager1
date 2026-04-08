#!/usr/bin/env python3
"""AgentScope 内置工具封装

集成 AgentScope 框架提供的内置工具函数，包括：
- execute_python_code: Python 代码执行
- execute_shell_command: Shell 命令执行
- read_text_file: 文本文件读取
- write_text_file: 文本文件写入
- list_dir: 目录列表
- create_directory: 创建目录
- delete_file: 删除文件
- move_file: 移动文件
- copy_file: 复制文件
"""

import asyncio
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from agentscope.tool import (
    Toolkit,
    ToolResponse,
    execute_python_code,
    execute_shell_command,
    read_text_file,
    write_text_file,
    list_dir,
    create_directory,
    delete_file,
    move_file,
    copy_file,
)

from ..utils.logger import logger


class AgentScopeToolkit:
    """AgentScope 内置工具封装
    
    提供统一的接口访问 AgentScope 框架的内置工具函数。
    支持同步和异步调用，支持流式响应。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化工具包
        
        Args:
            config: 配置字典（可选），包含：
                - timeout: 工具执行超时时间（秒）
                - max_retries: 最大重试次数
                - sandbox: 是否启用沙箱模式
        """
        self.config = config or {}
        self.logger = logger
        
        # 创建 Toolkit 实例
        self.toolkit = Toolkit()
        
        # 注册所有内置工具
        self._register_builtin_tools()
        
        self.logger.info("AgentScopeToolkit initialized")
    
    def _register_builtin_tools(self):
        """注册内置工具函数"""
        # Python 代码执行
        self.toolkit.register_tool_function(execute_python_code)
        self.logger.debug("Registered: execute_python_code")
        
        # Shell 命令执行
        self.toolkit.register_tool_function(execute_shell_command)
        self.logger.debug("Registered: execute_shell_command")
        
        # 文件读取
        self.toolkit.register_tool_function(read_text_file)
        self.logger.debug("Registered: read_text_file")
        
        # 文件写入
        self.toolkit.register_tool_function(write_text_file)
        self.logger.debug("Registered: write_text_file")
        
        # 目录列表
        self.toolkit.register_tool_function(list_dir)
        self.logger.debug("Registered: list_dir")
        
        # 创建目录
        self.toolkit.register_tool_function(create_directory)
        self.logger.debug("Registered: create_directory")
        
        # 删除文件
        self.toolkit.register_tool_function(delete_file)
        self.logger.debug("Registered: delete_file")
        
        # 移动文件
        self.toolkit.register_tool_function(move_file)
        self.logger.debug("Registered: move_file")
        
        # 复制文件
        self.toolkit.register_tool_function(copy_file)
        self.logger.debug("Registered: copy_file")
    
    def get_available_tools(self) -> List[str]:
        """获取所有可用的工具名称
        
        Returns:
            工具名称列表
        """
        schemas = self.toolkit.get_json_schemas()
        return list(schemas.keys())
    
    async def execute_python(
        self, 
        code: str, 
        timeout: int = None
    ) -> str:
        """执行 Python 代码
        
        Args:
            code: Python 代码字符串
            timeout: 超时时间（秒），默认使用配置值
            
        Returns:
            执行结果（标准输出）
        """
        timeout = timeout or self.config.get("timeout", 30)
        
        try:
            from agentscope.message import ToolUseBlock
            
            res = await self.toolkit.call_tool_function(
                ToolUseBlock(
                    type="tool_use",
                    id="exec_python",
                    name="execute_python_code",
                    input={"code": code},
                ),
            )
            
            result_text = ""
            async for tool_response in res:
                for block in tool_response.content:
                    if hasattr(block, 'text'):
                        result_text += block.text
            
            self.logger.info(f"Python code executed, output length: {len(result_text)}")
            return result_text
        
        except Exception as e:
            self.logger.error(f"Python code execution failed: {e}")
            raise
    
    async def execute_shell(
        self, 
        command: str, 
        timeout: int = None
    ) -> str:
        """执行 Shell 命令
        
        Args:
            command: Shell 命令字符串
            timeout: 超时时间（秒），默认使用配置值
            
        Returns:
            执行结果（标准输出和错误输出）
        """
        timeout = timeout or self.config.get("timeout", 30)
        
        try:
            from agentscope.message import ToolUseBlock
            
            res = await self.toolkit.call_tool_function(
                ToolUseBlock(
                    type="tool_use",
                    id="exec_shell",
                    name="execute_shell_command",
                    input={"command": command},
                ),
            )
            
            result_text = ""
            async for tool_response in res:
                for block in tool_response.content:
                    if hasattr(block, 'text'):
                        result_text += block.text
            
            self.logger.info(f"Shell command executed: {command[:50]}...")
            return result_text
        
        except Exception as e:
            self.logger.error(f"Shell command execution failed: {e}")
            raise
    
    async def read_file(self, file_path: str) -> str:
        """读取文本文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件内容
        """
        try:
            from agentscope.message import ToolUseBlock
            
            res = await self.toolkit.call_tool_function(
                ToolUseBlock(
                    type="tool_use",
                    id="read_file",
                    name="read_text_file",
                    input={"file_path": file_path},
                ),
            )
            
            content = ""
            async for tool_response in res:
                for block in tool_response.content:
                    if hasattr(block, 'text'):
                        content += block.text
            
            self.logger.info(f"File read: {file_path}")
            return content
        
        except Exception as e:
            self.logger.error(f"File read failed: {e}")
            raise
    
    async def write_file(
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
        try:
            from agentscope.message import ToolUseBlock
            
            res = await self.toolkit.call_tool_function(
                ToolUseBlock(
                    type="tool_use",
                    id="write_file",
                    name="write_text_file",
                    input={
                        "file_path": file_path,
                        "content": content,
                        "overwrite": overwrite,
                    },
                ),
            )
            
            success = False
            async for tool_response in res:
                # 检查响应中是否包含成功标志
                for block in tool_response.content:
                    if hasattr(block, 'text'):
                        if "successfully" in block.text.lower():
                            success = True
            
            self.logger.info(f"File written: {file_path}, success: {success}")
            return success
        
        except Exception as e:
            self.logger.error(f"File write failed: {e}")
            return False
    
    async def list_directory(self, dir_path: str) -> List[str]:
        """列出目录内容
        
        Args:
            dir_path: 目录路径
            
        Returns:
            文件和目录名称列表
        """
        try:
            from agentscope.message import ToolUseBlock
            
            res = await self.toolkit.call_tool_function(
                ToolUseBlock(
                    type="tool_use",
                    id="list_dir",
                    name="list_dir",
                    input={"path": dir_path},
                ),
            )
            
            items = []
            async for tool_response in res:
                for block in tool_response.content:
                    if hasattr(block, 'text'):
                        # 解析返回的文本，提取文件列表
                        lines = block.text.strip().split('\n')
                        items.extend([line.strip() for line in lines if line.strip()])
            
            self.logger.info(f"Directory listed: {dir_path}, found {len(items)} items")
            return items
        
        except Exception as e:
            self.logger.error(f"Directory listing failed: {e}")
            raise
    
    async def create_dir(self, dir_path: str) -> bool:
        """创建目录
        
        Args:
            dir_path: 目录路径
            
        Returns:
            是否成功
        """
        try:
            from agentscope.message import ToolUseBlock
            
            res = await self.toolkit.call_tool_function(
                ToolUseBlock(
                    type="tool_use",
                    id="create_dir",
                    name="create_directory",
                    input={"path": dir_path},
                ),
            )
            
            success = False
            async for tool_response in res:
                for block in tool_response.content:
                    if hasattr(block, 'text'):
                        if "successfully" in block.text.lower() or "created" in block.text.lower():
                            success = True
            
            self.logger.info(f"Directory created: {dir_path}, success: {success}")
            return success
        
        except Exception as e:
            self.logger.error(f"Directory creation failed: {e}")
            return False
    
    async def delete(self, file_path: str) -> bool:
        """删除文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否成功
        """
        try:
            from agentscope.message import ToolUseBlock
            
            res = await self.toolkit.call_tool_function(
                ToolUseBlock(
                    type="tool_use",
                    id="delete_file",
                    name="delete_file",
                    input={"path": file_path},
                ),
            )
            
            success = False
            async for tool_response in res:
                for block in tool_response.content:
                    if hasattr(block, 'text'):
                        if "successfully" in block.text.lower() or "deleted" in block.text.lower():
                            success = True
            
            self.logger.info(f"File deleted: {file_path}, success: {success}")
            return success
        
        except Exception as e:
            self.logger.error(f"File deletion failed: {e}")
            return False
    
    async def move(self, src_path: str, dst_path: str) -> bool:
        """移动文件
        
        Args:
            src_path: 源文件路径
            dst_path: 目标文件路径
            
        Returns:
            是否成功
        """
        try:
            from agentscope.message import ToolUseBlock
            
            res = await self.toolkit.call_tool_function(
                ToolUseBlock(
                    type="tool_use",
                    id="move_file",
                    name="move_file",
                    input={
                        "src": src_path,
                        "dst": dst_path,
                    },
                ),
            )
            
            success = False
            async for tool_response in res:
                for block in tool_response.content:
                    if hasattr(block, 'text'):
                        if "successfully" in block.text.lower() or "moved" in block.text.lower():
                            success = True
            
            self.logger.info(f"File moved: {src_path} -> {dst_path}, success: {success}")
            return success
        
        except Exception as e:
            self.logger.error(f"File move failed: {e}")
            return False
    
    async def copy(self, src_path: str, dst_path: str) -> bool:
        """复制文件
        
        Args:
            src_path: 源文件路径
            dst_path: 目标文件路径
            
        Returns:
            是否成功
        """
        try:
            from agentscope.message import ToolUseBlock
            
            res = await self.toolkit.call_tool_function(
                ToolUseBlock(
                    type="tool_use",
                    id="copy_file",
                    name="copy_file",
                    input={
                        "src": src_path,
                        "dst": dst_path,
                    },
                ),
            )
            
            success = False
            async for tool_response in res:
                for block in tool_response.content:
                    if hasattr(block, 'text'):
                        if "successfully" in block.text.lower() or "copied" in block.text.lower():
                            success = True
            
            self.logger.info(f"File copied: {src_path} -> {dst_path}, success: {success}")
            return success
        
        except Exception as e:
            self.logger.error(f"File copy failed: {e}")
            return False
    
    def get_tool_schemas(self) -> Dict[str, Any]:
        """获取所有工具的 JSON Schema
        
        Returns:
            工具 Schema 字典
        """
        return self.toolkit.get_json_schemas()
    
    async def close(self):
        """清理资源"""
        self.logger.info("AgentScopeToolkit closing")
        # Toolkit 不需要特殊清理
