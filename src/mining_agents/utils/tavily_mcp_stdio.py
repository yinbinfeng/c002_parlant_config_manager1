# -*- coding: utf-8 -*-
"""Tavily MCP（stdio）子进程启动命令。

Windows 下 MCP 通过 asyncio 拉起子进程时，直接 executable=`npx` 常触发
WinError 2（找不到文件），因 `npx` 多为 `npx.cmd`。优先解析绝对路径，其次 cmd /c。

环境变量（可选）：
- TAVILY_MCP_NPX_EXECUTABLE: npx 可执行文件绝对路径（含 npx.cmd）

文件格式: Python 源码
"""

from __future__ import annotations

import os
import shutil
import sys
from typing import Tuple

_TAVILY_MCP_PACKAGE = ["-y", "tavily-mcp@latest"]


def tavily_mcp_command_and_args() -> Tuple[str, list[str]]:
    """返回 (command, args) 供 StdIOStatefulClient 使用。"""
    override = (os.environ.get("TAVILY_MCP_NPX_EXECUTABLE") or "").strip()
    if override:
        return override, list(_TAVILY_MCP_PACKAGE)

    if sys.platform == "win32":
        for cand in ("npx.cmd", "npx.exe", "npx"):
            resolved = shutil.which(cand)
            if resolved:
                return resolved, list(_TAVILY_MCP_PACKAGE)
        return "cmd.exe", ["/d", "/s", "/c", "npx", *list(_TAVILY_MCP_PACKAGE)]

    resolved = shutil.which("npx")
    if resolved:
        return resolved, list(_TAVILY_MCP_PACKAGE)
    return "npx", list(_TAVILY_MCP_PACKAGE)
