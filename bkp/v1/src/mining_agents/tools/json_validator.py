#!/usr/bin/env python3
"""JSON 校验工具 - 基于 json_repair 库"""

import json
from typing import Any, Tuple, List
from pathlib import Path
from ..utils.logger import logger


class JsonValidator:
    """JSON 格式校验工具
    
    提供 JSON 验证、修复和保存功能。
    支持自动修复常见的 JSON 格式错误。
    """
    
    def __init__(self):
        """初始化工具"""
        self.logger = logger
    
    def get_tool_schema(self) -> dict:
        """获取工具 Schema（用于 ReActAgent 注册）
        
        Returns:
            JSON Schema 定义
        """
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["validate", "save", "load"],
                    "description": "操作类型：validate（验证）、save（保存）、load（加载）"
                },
                "json_string": {
                    "type": "string",
                    "description": "要验证的 JSON 字符串（validate 操作需要）"
                },
                "data": {
                    "type": "object",
                    "description": "要保存的数据对象（save 操作需要）"
                },
                "file_path": {
                    "type": "string",
                    "description": "文件路径（save/load 操作需要）"
                }
            },
            "required": ["action"]
        }
    
    async def execute(self, action: str, **kwargs) -> str:
        """执行工具（统一接口）
        
        Args:
            action: 操作类型 (validate/save/load)
            kwargs: 其他参数
            
        Returns:
            执行结果
        """
        if action == "validate":
            json_string = kwargs.get("json_string", "")
            success, data, msg = self.validate(json_string)
            if success:
                return f"JSON validation successful: {data}"
            else:
                return f"JSON validation failed: {msg}"
        
        elif action == "save":
            data = kwargs.get("data")
            file_path = kwargs.get("file_path")
            if not data or not file_path:
                return "Error: data and file_path required for save action"
            success = self.save_json(data, file_path)
            return f"JSON save {'successful' if success else 'failed'} to {file_path}"
        
        elif action == "load":
            file_path = kwargs.get("file_path", "")
            success, data, msg = self.load_json(file_path)
            if success:
                return f"JSON loaded from {file_path}: {data}"
            else:
                return f"JSON load failed: {msg}"
        
        else:
            return f"Error: unknown action '{action}'"
    
    def validate(self, json_string: str) -> Tuple[bool, Any, str]:
        """验证并修复 JSON 字符串
        
        Args:
            json_string: JSON 字符串
            
        Returns:
            (是否成功，解析后的对象，错误/警告信息)
            
        Examples:
            >>> validator = JsonValidator()
            >>> success, data, msg = validator.validate('{"key": "value"}')
            >>> assert success and data == {"key": "value"}
        """
        try:
            # 尝试直接解析
            data = json.loads(json_string)
            self.logger.debug("JSON validation successful")
            return True, data, ""
        
        except json.JSONDecodeError as e:
            self.logger.warning(f"JSON decode error: {e}")
            
            # 尝试修复
            try:
                repaired = self._repair_json(json_string)
                data = json.loads(repaired)
                warning_msg = f"JSON was malformed but repaired successfully. Original error: {str(e)}"
                self.logger.info(warning_msg)
                return True, data, warning_msg
            
            except Exception as repair_error:
                error_msg = f"JSON validation failed: {str(e)}, repair also failed: {str(repair_error)}"
                self.logger.error(error_msg)
                return False, None, error_msg
    
    def _repair_json(self, json_string: str) -> str:
        """修复 JSON 字符串
        
        Args:
            json_string: JSON 字符串
            
        Returns:
            修复后的 JSON 字符串
        """
        try:
            from json_repair import repair_json
            return repair_json(json_string)
        
        except ImportError:
            self.logger.warning("json_repair not installed, using basic repair")
            return self._basic_repair(json_string)
    
    def _basic_repair(self, json_string: str) -> str:
        """基础 JSON 修复（不依赖 json_repair 库）
        
        Args:
            json_string: JSON 字符串
            
        Returns:
            修复后的 JSON 字符串
        """
        # 移除末尾的逗号
        import re
        json_string = re.sub(r',\s*}', '}', json_string)
        json_string = re.sub(r',\s*]', ']', json_string)
        
        # 确保双引号
        json_string = json_string.replace("'", '"')
        
        # 移除注释（// 开头的行）
        lines = json_string.split('\n')
        cleaned_lines = [line for line in lines if not line.strip().startswith('//')]
        json_string = '\n'.join(cleaned_lines)
        
        return json_string.strip()
    
    def save_json(
        self, 
        data: Any, 
        file_path: str, 
        indent: int = 2, 
        ensure_ascii: bool = False
    ) -> bool:
        """保存 JSON 文件
        
        Args:
            data: 数据对象
            file_path: 文件路径
            indent: 缩进空格数（默认 2）
            ensure_ascii: 是否转义非 ASCII 字符（默认 False）
            
        Returns:
            是否成功
            
        Examples:
            >>> validator = JsonValidator()
            >>> success = validator.save_json({"key": "值"}, "output.json")
            >>> assert success
        """
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
            
            self.logger.info(f"JSON saved to {file_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to save JSON: {e}")
            return False
    
    def load_json(self, file_path: str) -> Tuple[bool, Any, str]:
        """加载 JSON 文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            (是否成功，数据对象，错误信息)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.logger.info(f"JSON loaded from {file_path}")
            return True, data, ""
        
        except Exception as e:
            self.logger.error(f"Failed to load JSON: {e}")
            return False, None, str(e)
    
    def validate_schema(
        self, 
        data: Any, 
        schema: dict, 
        required_fields: List[str] = None
    ) -> Tuple[bool, str]:
        """验证数据结构
        
        Args:
            data: 数据对象
            schema: 数据类型定义（简化版）
            required_fields: 必需字段列表
            
        Returns:
            (是否通过，错误信息)
        """
        errors = []
        
        # 检查必需字段
        if required_fields:
            for field in required_fields:
                if field not in data:
                    errors.append(f"Missing required field: {field}")
        
        # 检查类型
        for field, expected_type in schema.items():
            if field in data:
                if not isinstance(data[field], expected_type):
                    errors.append(f"Field '{field}' should be {expected_type.__name__}, got {type(data[field]).__name__}")
        
        if errors:
            error_msg = "; ".join(errors)
            self.logger.warning(f"Schema validation failed: {error_msg}")
            return False, error_msg
        
        self.logger.info("Schema validation passed")
        return True, ""
