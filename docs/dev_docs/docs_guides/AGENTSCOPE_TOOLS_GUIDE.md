# AgentScope 内置工具集成指南

**日期**: 2026-03-20  
**版本**: v0.2.0 (工具增强版)

---

## 概述

在 MVP 版本的基础上，我们集成了 AgentScope 框架提供的内置工具函数，提供更强大的文件操作、代码执行和系统管理能力。

### 新增工具

1. **AgentScopeToolkit** - AgentScope 内置工具的统一接口
2. **FileServiceManager** - 基于 AgentScope 工具的高级文件服务

---

## AgentScope 内置工具

AgentScope 框架提供以下内置工具函数：

### 1. 代码执行

- **execute_python_code**: 执行 Python 代码字符串
- **execute_shell_command**: 执行 Shell 命令

### 2. 文件操作

- **read_text_file**: 读取文本文件
- **write_text_file**: 写入文本文件
- **list_dir**: 列出目录内容
- **create_directory**: 创建目录
- **delete_file**: 删除文件
- **move_file**: 移动文件
- **copy_file**: 复制文件

### 3. 特性

- ✅ 支持同步和异步调用
- ✅ 支持流式响应
- ✅ 支持工具中断
- ✅ 统一的 JSON Schema 管理
- ✅ 动态扩展工具参数

---

## 使用示例

### AgentScopeToolkit 基本用法

```python
from mining_agents.tools.agentscope_tools import AgentScopeToolkit

# 初始化工具包
toolkit = AgentScopeToolkit()

# 获取所有可用工具
tools = toolkit.get_available_tools()
print(f"Available tools: {tools}")

# 执行 Python 代码
result = await toolkit.execute_python(
    code="print('Hello World!'); result = 2 + 3; print(f'Result: {result}')"
)
print(result)
# 输出:
# Hello World!
# Result: 5

# 执行 Shell 命令
shell_result = await toolkit.execute_shell("ls -la")
print(shell_result)

# 读取文件
content = await toolkit.read_file("/path/to/file.txt")
print(content)

# 写入文件
success = await toolkit.write_file("/path/to/output.txt", "文件内容")
print(success)

# 清理资源
await toolkit.close()
```

### FileServiceManager 高级用法

```python
from mining_agents.tools.file_service import FileServiceManager

# 初始化文件服务管理器
manager = FileServiceManager()

# 读写文本文件
await manager.write_text("output.txt", "这是测试内容")
content = await manager.read_text("output.txt")

# 读写 JSON 文件
data = {"name": "测试", "value": 123}
await manager.write_json("data.json", data)
loaded_data = await manager.read_json("data.json")

# 读写 YAML 文件
config = {"debug": True, "timeout": 30}
await manager.write_yaml("config.yaml", config)
loaded_config = await manager.read_yaml("config.yaml")

# 目录管理
await manager.create_directory("output/subdir")
items = await manager.list_directory("output")

# 文件操作
await manager.copy_file("src.txt", "dst.txt")
await manager.move_file("old_path.txt", "new_path.txt")
await manager.delete_file("unwanted.txt")

# 文件搜索
py_files = await manager.search_files("./src", "*.py", recursive=True)

# 获取目录结构
structure = await manager.get_directory_structure("./src", max_depth=3)

# 检查文件存在性
exists = await manager.file_exists("important.txt")
dir_exists = await manager.directory_exists("config")

# 清理资源
await manager.cleanup()
```

---

## 完整示例：项目脚手架生成器

```python
#!/usr/bin/env python3
"""使用 AgentScope 工具生成项目脚手架"""

import asyncio
from mining_agents.tools.file_service import FileServiceManager


async def generate_project_scaffold(project_name: str):
    """生成项目脚手架
    
    Args:
        project_name: 项目名称
    """
    manager = FileServiceManager()
    
    # 1. 创建项目目录结构
    print(f"Creating project structure for {project_name}...")
    
    await manager.create_directory(f"{project_name}/src")
    await manager.create_directory(f"{project_name}/tests")
    await manager.create_directory(f"{project_name}/docs")
    await manager.create_directory(f"{project_name}/output")
    
    # 2. 创建 requirements.txt
    requirements_content = """# Project Requirements
agentscope>=1.0.0
pyyaml>=6.0
json-repair>=0.25.0
"""
    await manager.write_text(
        f"{project_name}/requirements.txt",
        requirements_content
    )
    
    # 3. 创建 README.md
    readme_content = f"""# {project_name}

Auto-generated project scaffold.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```python
from src import main
```
"""
    await manager.write_text(
        f"{project_name}/README.md",
        readme_content
    )
    
    # 4. 创建配置文件
    config = {
        "project_name": project_name,
        "version": "0.1.0",
        "settings": {
            "debug": True,
            "timeout": 30,
            "max_retries": 3,
        }
    }
    await manager.write_yaml(
        f"{project_name}/config.yaml",
        config
    )
    
    # 5. 创建测试文件
    test_code = """
import pytest


def test_example():
    assert True


def test_addition():
    assert 2 + 2 == 4
"""
    await manager.write_text(
        f"{project_name}/tests/test_basic.py",
        test_code
    )
    
    # 6. 验证生成的结构
    print("\nGenerated structure:")
    structure = await manager.get_directory_structure(
        project_name,
        max_depth=3
    )
    print_structure(structure)
    
    # 7. 搜索 Python 文件
    py_files = await manager.search_files(project_name, "*.py")
    print(f"\nPython files found: {len(py_files)}")
    for f in py_files:
        print(f"  - {f}")
    
    await manager.cleanup()
    print("\nProject scaffold generated successfully!")


def print_structure(structure, indent=0):
    """打印目录结构"""
    prefix = "  " * indent
    if structure["type"] == "directory":
        print(f"{prefix}📁 {structure['name']}/")
        for child in structure.get("children", []):
            print_structure(child, indent + 1)
    else:
        print(f"{prefix}📄 {structure['name']}")


if __name__ == "__main__":
    asyncio.run(generate_project_scaffold("my_new_project"))
```

---

## 工具对比

### 原始工具 vs AgentScope 工具

| 功能 | 原始实现 | AgentScope 工具 |
|------|---------|----------------|
| 文件读取 | `open()` | `read_text_file()` |
| 文件写入 | `open()` | `write_text_file()` |
| JSON 读写 | `json` 模块 | `read/write_text_file()` + 解析 |
| YAML 读写 | `yaml` 模块 | `read/write_text_file()` + 解析 |
| 目录列表 | `os.listdir()` | `list_dir()` |
| 创建目录 | `os.makedirs()` | `create_directory()` |
| 删除文件 | `os.remove()` | `delete_file()` |
| 移动文件 | `shutil.move()` | `move_file()` |
| 复制文件 | `shutil.copy()` | `copy_file()` |
| 代码执行 | `subprocess` | `execute_python_code()` |
| Shell 命令 | `subprocess` | `execute_shell_command()` |

### AgentScope 工具的优势

1. **统一接口**: 所有工具通过 Toolkit 统一管理
2. **异步支持**: 原生支持异步调用
3. **流式响应**: 支持流式返回结果
4. **工具中断**: 支持取消长时间运行的任务
5. **JSON Schema**: 自动化工具描述生成
6. **沙箱执行**: 可选的沙箱环境执行代码

---

## 最佳实践

### 1. 错误处理

```python
from mining_agents.tools.file_service import FileServiceManager

manager = FileServiceManager()

try:
    content = await manager.read_text("nonexistent.txt")
except Exception as e:
    print(f"Error reading file: {e}")
    # 使用默认内容
    content = "Default content"

await manager.cleanup()
```

### 2. 批量操作

```python
# 批量创建目录
directories = ["output/logs", "output/cache", "output/temp"]
for dir_path in directories:
    await manager.create_directory(dir_path)

# 批量写入文件
files = {
    "config.yaml": {"debug": True},
    "data.json": {"items": [1, 2, 3]},
    "readme.md": "# Project",
}
for filename, content in files.items():
    if filename.endswith(".yaml"):
        await manager.write_yaml(filename, content)
    elif filename.endswith(".json"):
        await manager.write_json(filename, content)
    else:
        await manager.write_text(filename, str(content))
```

### 3. 资源清理

```python
# 使用 try-finally 确保资源清理
manager = FileServiceManager()
try:
    # 执行操作
    await manager.write_text("output.txt", "content")
finally:
    await manager.cleanup()

# 或使用 async with（如果实现了上下文管理器）
async with FileServiceManager() as manager:
    await manager.write_text("output.txt", "content")
```

---

## 性能考虑

### 并发执行

```python
import asyncio
from mining_agents.tools.file_service import FileServiceManager

async def concurrent_operations():
    manager = FileServiceManager()
    
    # 并发写入多个文件
    tasks = [
        manager.write_text(f"file_{i}.txt", f"Content {i}")
        for i in range(10)
    ]
    results = await asyncio.gather(*tasks)
    print(f"Created {sum(results)} files")
    
    await manager.cleanup()

asyncio.run(concurrent_operations())
```

### 超时控制

```python
from mining_agents.tools.agentscope_tools import AgentScopeToolkit

# 设置全局超时
toolkit = AgentScopeToolkit(config={"timeout": 30})

# 或为单个操作设置超时
try:
    result = await asyncio.wait_for(
        toolkit.execute_python(slow_code),
        timeout=10
    )
except asyncio.TimeoutError:
    print("Operation timed out")
```

---

## 测试

运行 AgentScope 工具测试：

```bash
# 安装依赖
pip install -r requirements-dev.txt

# 运行测试
pytest tests/test_agentscope_tools.py -v

# 运行特定测试
pytest tests/test_agentscope_tools.py::TestFileServiceManager -v

# 查看覆盖率
pytest tests/test_agentscope_tools.py --cov=mining_agents.tools
```

---

## 故障排除

### 常见问题

**Q: 工具执行超时怎么办？**

A: 增加超时时间或使用更小的数据块：
```python
toolkit = AgentScopeToolkit(config={"timeout": 60})
```

**Q: 如何处理大文件？**

A: 分块读取或使用流式 API：
```python
# 分批处理大文件
chunk_size = 1000
for i in range(0, len(data), chunk_size):
    chunk = data[i:i+chunk_size]
    await manager.write_text(f"part_{i}.txt", str(chunk))
```

**Q: 代码执行失败怎么办？**

A: 检查代码语法错误和权限问题：
```python
try:
    result = await toolkit.execute_python(code)
except Exception as e:
    print(f"Execution error: {e}")
    # 尝试调试模式
    debug_code = f"""
try:
    {code}
except Exception as e:
    print(f'Error: {{e}}')
    import traceback
    traceback.print_exc()
"""
    result = await toolkit.execute_python(debug_code)
```

---

## 下一步

计划集成的其他 AgentScope 工具：

- [ ] Bing Search 工具
- [ ] Google Scholar 工具
- [ ] Wikipedia 工具
- [ ] 数据库连接工具
- [ ] HTTP 请求工具
- [ ] 图像生成工具

---

**更新完成！** 🎉

现在您的项目已经集成了 AgentScope 的内置工具，可以使用更强大的文件操作和系统管理功能。
