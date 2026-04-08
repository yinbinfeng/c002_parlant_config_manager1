"""工具模块 - 包含 MCP 工具封装和本地工具"""

from .deep_research import DeepResearchTool
from .json_validator import JsonValidator
from .file_service import FileServiceManager

# 尝试导入 AgentScopeToolkit，如果失败则跳过
# 这样在 Mock 模式下可以不依赖 agentscope 模块
try:
    from .agentscope_tools import AgentScopeToolkit
    __all__ = [
        'DeepResearchTool',
        'JsonValidator',
        'AgentScopeToolkit',
        'FileServiceManager',
    ]
except ImportError:
    __all__ = [
        'DeepResearchTool',
        'JsonValidator',
        'FileServiceManager',
    ]
