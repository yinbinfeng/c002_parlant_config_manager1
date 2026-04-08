"""
Mining Agents System

用于生成 Parlant Agent 配置的多步骤挖掘系统

核心功能:
1. 需求分析 - 生成待澄清问题
2. 多 Agent 辩论 - 整合不同视角的意见
3. 任务分解 - 生成平衡的任务分解方案
4. 全局规则设计 - 设计系统规则和约束条件
5. 领域配置 - 专项 Agent 配置
6. 私域数据抽取 - 用户画像和对话模式分析
7. 质量检查 - 全面质量验证
8. 配置组装 - 生成最终 Parlant 配置

目录结构:
├── mining_agents/  # 主要模块
│   ├── agents/     # Agent 实现
│   ├── managers/   # 管理器
│   ├── tools/      # 工具
│   └── utils/      # 工具函数
"""

__version__ = "1.0.0"
__author__ = "Mining Agents Team"

__all__ = []
