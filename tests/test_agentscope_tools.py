#!/usr/bin/env python3
"""测试 AgentScope 内置工具"""

import pytest
import asyncio
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def temp_dir():
    """创建临时目录"""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)


class TestAgentScopeToolkit:
    """测试 AgentScopeToolkit"""
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """测试初始化"""
        from mining_agents.tools.agentscope_tools import AgentScopeToolkit
        
        toolkit = AgentScopeToolkit()
        
        # 获取可用工具列表
        tools = toolkit.get_available_tools()
        assert len(tools) > 0
        print(f"Available tools: {tools}")
        
        await toolkit.close()
    
    @pytest.mark.asyncio
    async def test_get_schemas(self):
        """测试获取工具 Schema"""
        from mining_agents.tools.agentscope_tools import AgentScopeToolkit
        
        toolkit = AgentScopeToolkit()
        schemas = toolkit.get_tool_schemas()
        
        assert isinstance(schemas, dict)
        assert len(schemas) > 0
        
        # 检查是否包含预期的工具
        tool_names = list(schemas.keys())
        print(f"Tool names: {tool_names}")
        
        await toolkit.close()
    
    @pytest.mark.asyncio
    async def test_execute_python(self):
        """测试执行 Python 代码"""
        from mining_agents.tools.agentscope_tools import AgentScopeToolkit
        
        toolkit = AgentScopeToolkit(config={"timeout": 10})
        
        code = "print('Hello from Python!'); result = 2 + 3; print(f'Result: {result}')"
        result = await toolkit.execute_python(code)
        
        assert isinstance(result, str)
        assert "Hello from Python!" in result
        assert "Result: 5" in result
        
        await toolkit.close()
    
    @pytest.mark.asyncio
    async def test_execute_shell(self):
        """测试执行 Shell 命令"""
        from mining_agents.tools.agentscope_tools import AgentScopeToolkit
        
        toolkit = AgentScopeToolkit(config={"timeout": 10})
        
        import platform
        system = platform.system()
        
        if system == "Windows":
            command = "echo Hello from Windows"
        else:
            command = "echo 'Hello from Linux'"
        
        result = await toolkit.execute_shell(command)
        
        assert isinstance(result, str)
        assert "Hello" in result
        
        await toolkit.close()


class TestFileServiceManager:
    """测试 FileServiceManager"""
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """测试初始化"""
        from mining_agents.tools.file_service import FileServiceManager
        
        manager = FileServiceManager()
        assert manager.toolkit is not None
        
        await manager.cleanup()
    
    @pytest.mark.asyncio
    async def test_read_write_text(self, temp_dir):
        """测试文本文件读写"""
        from mining_agents.tools.file_service import FileServiceManager
        
        manager = FileServiceManager()
        
        # 写入文件
        test_file = temp_dir / "test.txt"
        content = "这是测试内容\n第二行"
        success = await manager.write_text(str(test_file), content)
        assert success is True
        
        # 读取文件
        read_content = await manager.read_text(str(test_file))
        assert read_content.strip() == content.strip()
        
        await manager.cleanup()
    
    @pytest.mark.asyncio
    async def test_read_write_json(self, temp_dir):
        """测试 JSON 文件读写"""
        from mining_agents.tools.file_service import FileServiceManager
        
        manager = FileServiceManager()
        
        # 写入 JSON
        test_file = temp_dir / "test.json"
        data = {"name": "测试", "value": 123, "nested": {"key": "value"}}
        success = await manager.write_json(str(test_file), data)
        assert success is True
        
        # 读取 JSON
        read_data = await manager.read_json(str(test_file))
        assert read_data == data
        
        await manager.cleanup()
    
    @pytest.mark.asyncio
    async def test_read_write_yaml(self, temp_dir):
        """测试 YAML 文件读写"""
        from mining_agents.tools.file_service import FileServiceManager
        
        manager = FileServiceManager()
        
        # 写入 YAML
        test_file = temp_dir / "test.yaml"
        data = {"name": "测试", "value": 123, "list": [1, 2, 3]}
        success = await manager.write_yaml(str(test_file), data)
        assert success is True
        
        # 读取 YAML
        read_data = await manager.read_yaml(str(test_file))
        assert read_data == data
        
        await manager.cleanup()
    
    @pytest.mark.asyncio
    async def test_create_directory(self, temp_dir):
        """测试创建目录"""
        from mining_agents.tools.file_service import FileServiceManager
        
        manager = FileServiceManager()
        
        # 创建目录
        new_dir = temp_dir / "subdir1" / "subdir2"
        success = await manager.create_directory(str(new_dir))
        assert success is True
        assert new_dir.exists()
        
        await manager.cleanup()
    
    @pytest.mark.asyncio
    async def test_list_directory(self, temp_dir):
        """测试列出目录"""
        from mining_agents.tools.file_service import FileServiceManager
        
        manager = FileServiceManager()
        
        # 创建测试文件
        (temp_dir / "file1.txt").touch()
        (temp_dir / "file2.txt").touch()
        (temp_dir / "subdir").mkdir()
        
        # 列出目录
        items = await manager.list_directory(str(temp_dir))
        assert len(items) >= 3  # 至少 3 个项目
        
        await manager.cleanup()
    
    @pytest.mark.asyncio
    async def test_file_exists(self, temp_dir):
        """测试文件存在性检查"""
        from mining_agents.tools.file_service import FileServiceManager
        
        manager = FileServiceManager()
        
        # 创建测试文件
        test_file = temp_dir / "exists.txt"
        test_file.touch()
        
        # 检查存在
        exists = await manager.file_exists(str(test_file))
        assert exists is True
        
        # 检查不存在
        not_exists = await manager.file_exists(str(temp_dir / "not_exists.txt"))
        assert not_exists is False
        
        await manager.cleanup()
    
    @pytest.mark.asyncio
    async def test_copy_move_delete(self, temp_dir):
        """测试复制、移动、删除文件"""
        from mining_agents.tools.file_service import FileServiceManager
        
        manager = FileServiceManager()
        
        # 创建源文件
        src_file = temp_dir / "source.txt"
        src_file.write_text("源文件内容")
        
        # 复制文件
        dst_file = temp_dir / "destination.txt"
        copy_success = await manager.copy_file(str(src_file), str(dst_file))
        assert copy_success is True
        assert dst_file.exists()
        
        # 移动文件
        moved_file = temp_dir / "moved.txt"
        move_success = await manager.move_file(str(dst_file), str(moved_file))
        assert move_success is True
        assert moved_file.exists()
        assert not dst_file.exists()
        
        # 删除文件
        delete_success = await manager.delete_file(str(moved_file))
        assert delete_success is True
        assert not moved_file.exists()
        
        await manager.cleanup()
    
    @pytest.mark.asyncio
    async def test_search_files(self, temp_dir):
        """测试搜索文件"""
        from mining_agents.tools.file_service import FileServiceManager
        
        manager = FileServiceManager()
        
        # 创建测试文件
        (temp_dir / "test1.py").touch()
        (temp_dir / "test2.py").touch()
        (temp_dir / "test.txt").touch()
        
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        (subdir / "test3.py").touch()
        
        # 搜索 .py 文件
        py_files = await manager.search_files(str(temp_dir), "*.py", recursive=True)
        assert len(py_files) >= 3
        
        await manager.cleanup()
    
    @pytest.mark.asyncio
    async def test_directory_structure(self, temp_dir):
        """测试获取目录结构"""
        from mining_agents.tools.file_service import FileServiceManager
        
        manager = FileServiceManager()
        
        # 创建测试目录结构
        (temp_dir / "file1.txt").touch()
        subdir1 = temp_dir / "subdir1"
        subdir1.mkdir()
        (subdir1 / "file2.txt").touch()
        
        subdir2 = subdir1 / "subdir2"
        subdir2.mkdir()
        (subdir2 / "file3.txt").touch()
        
        # 获取目录结构
        structure = await manager.get_directory_structure(str(temp_dir), max_depth=3)
        
        assert structure["type"] == "directory"
        assert structure["name"] == temp_dir.name
        assert len(structure["children"]) > 0
        
        await manager.cleanup()


class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, temp_dir):
        """测试完整工作流程"""
        from mining_agents.tools.file_service import FileServiceManager
        
        manager = FileServiceManager()
        
        # 1. 创建目录
        output_dir = temp_dir / "output"
        await manager.create_directory(str(output_dir))
        
        # 2. 写入配置文件
        config_file = output_dir / "config.yaml"
        config_data = {
            "name": "测试项目",
            "version": "1.0.0",
            "settings": {
                "debug": True,
                "timeout": 30,
            }
        }
        await manager.write_yaml(str(config_file), config_data)
        
        # 3. 读取并验证
        loaded_config = await manager.read_yaml(str(config_file))
        assert loaded_config == config_data
        
        # 4. 写入 JSON 数据
        data_file = output_dir / "data.json"
        data = {"items": [1, 2, 3, 4, 5]}
        await manager.write_json(str(data_file), data)
        
        # 5. 列出目录
        files = await manager.list_directory(str(output_dir))
        assert len(files) == 2
        
        # 6. 搜索文件
        yaml_files = await manager.search_files(str(output_dir), "*.yaml")
        assert len(yaml_files) == 1
        
        # 7. 获取目录结构
        structure = await manager.get_directory_structure(str(output_dir))
        assert structure["type"] == "directory"
        
        await manager.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
