#!/usr/bin/env python3
"""步骤管理器 - 负责步骤调度与状态管理"""

import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, Callable, Awaitable
from datetime import datetime
import yaml
import traceback

from ..utils.logger import logger
from ..utils.file_utils import write_json, read_json, write_markdown, ensure_dir


class StepManager:
    """步骤管理器 - 负责步骤调度与状态管理
    
    主要职责：
    - 步骤调度：按顺序或并行执行各个步骤
    - 状态持久化：每步的执行状态落盘存储
    - 断点续跑：支持从特定步骤恢复执行
    - 结果加载：加载已完成的步骤结果
    """
    
    def __init__(self, config_path: str, output_base_dir: str):
        """初始化步骤管理器
        
        Args:
            config_path: 配置文件路径
            output_base_dir: 输出基础目录
        """
        self.config_path = Path(config_path)
        self.logger = logger
        
        # 从配置中获取输出目录
        config = self._load_config()
        config_output_dir = config.get("output_base_dir", output_base_dir)
        
        # 处理相对路径
        if not Path(config_output_dir).is_absolute():
            # 如果是相对路径，相对于配置文件所在目录
            config_output_dir = self.config_path.parent.parent / config_output_dir
        
        self.output_base_dir = Path(config_output_dir).resolve()
        
        # 确保输出目录存在
        ensure_dir(str(self.output_base_dir))
        
        # 保存配置
        self.config = config
        
        # 步骤状态存储
        self.step_status: Dict[int, str] = {}  # step_num -> status
        
        # 步骤处理器注册表
        self.step_handlers: Dict[int, Callable] = {}
    
    def _load_config(self) -> dict:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            self.logger.info(f"Config loaded from {self.config_path}")
            return config
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            # 返回默认配置
            return {
                "max_parallel_agents": 4,
                "start_step": 1,
                "end_step": 5,
                "force_rerun": False,
                "continue_on_error": False,
            }
    
    def get_step_output_dir(self, step_num: int) -> Path:
        """获取步骤输出目录"""
        # 步骤目录名称映射
        step_dir_map = {
            1: "requirement_clarification",
            2: "dimension_analysis",
            3: "workflow_development",
            4: "global_rules_check",
            5: "config_assembly"
        }
        
        # 获取目录名称，如果不存在则使用默认格式
        dir_name = step_dir_map.get(step_num, f"step{step_num}")
        return ensure_dir(self.output_base_dir / dir_name)
    
    def is_step_completed(self, step_num: int, context: dict = None) -> bool:
        """检查步骤是否已完成
        
        Args:
            step_num: 步骤编号
            context: 上下文信息，包含 force_rerun 等参数
            
        Returns:
            是否已完成
        """
        # 如果强制重跑，直接返回 False
        force_rerun = context.get("force_rerun", False) if context else False
        if not force_rerun:
            force_rerun = self.config.get("force_rerun", False)
        if force_rerun:
            return False
        
        # 检查是否存在该步骤的输出文件
        step_dir = self.get_step_output_dir(step_num)
        status_file = step_dir / "status.json"
        
        if not status_file.exists():
            return False
        
        status_data = read_json(str(status_file))
        return status_data.get("status") == "completed"
    
    def mark_step_started(self, step_num: int):
        """标记步骤已开始"""
        step_dir = self.get_step_output_dir(step_num)
        status_file = step_dir / "status.json"
        
        status_data = {
            "step_num": step_num,
            "status": "running",
            "started_at": datetime.now().isoformat(),
        }
        write_json(status_data, str(status_file))
        self.step_status[step_num] = "running"
        self.logger.info(f"Step {step_num} started")
    
    def mark_step_completed(self, step_num: int, output_files: list = None, metadata: dict = None):
        """标记步骤已完成
        
        Args:
            step_num: 步骤编号
            output_files: 输出文件列表
            metadata: 额外元数据
        """
        step_dir = self.get_step_output_dir(step_num)
        status_file = step_dir / "status.json"
        
        # 读取开始时间
        started_at = None
        if status_file.exists():
            started_at = read_json(str(status_file)).get("started_at")
        
        status_data = {
            "step_num": step_num,
            "status": "completed",
            "started_at": started_at,
            "completed_at": datetime.now().isoformat(),
            "output_files": output_files or [],
            "metadata": metadata or {},
        }
        write_json(status_data, str(status_file))
        self.step_status[step_num] = "completed"
        self.logger.info(f"Step {step_num} completed with {len(output_files or [])} output files")
    
    def mark_step_failed(self, step_num: int, error_message: str, tb: str = ""):
        """标记步骤失败（落盘错误与 traceback）"""
        step_dir = self.get_step_output_dir(step_num)
        status_file = step_dir / "status.json"
        error_file = step_dir / "error.log"
        step_error_file = step_dir / f"step{step_num}_error.log"
        
        # 写入错误日志
        error_text = (
            f"Error at {datetime.now().isoformat()}\n"
            f"{error_message}\n\n"
            "Traceback:\n"
            f"{tb or '(no traceback captured)'}\n"
        )
        with open(error_file, 'w', encoding='utf-8') as f:
            f.write(error_text)
        with open(step_error_file, 'w', encoding='utf-8') as f:
            f.write(error_text)
        
        # 更新状态
        started_at = None
        if status_file.exists():
            started_at = read_json(str(status_file)).get("started_at")
        
        status_data = {
            "step_num": step_num,
            "status": "failed",
            "started_at": started_at,
            "failed_at": datetime.now().isoformat(),
            "error_message": error_message,
        }
        write_json(status_data, str(status_file))
        self.step_status[step_num] = "failed"
        self.logger.error(f"Step {step_num} failed: {error_message}")
    
    def register_step_handler(self, step_num: int, handler: Callable):
        """注册步骤处理器
        
        Args:
            step_num: 步骤编号
            handler: 处理函数（异步）
        """
        self.step_handlers[step_num] = handler
        self.logger.info(f"Step {step_num} handler registered")
    
    async def run_step(self, step_num: int, context: dict = None) -> Optional[dict]:
        """运行步骤
        
        Args:
            step_num: 步骤编号
            context: 上下文信息
            
        Returns:
            步骤执行结果
        """
        # 检查是否已注册处理器
        if step_num not in self.step_handlers:
            self.logger.warning(f"No handler registered for step {step_num}, skipping")
            return None
        
        # 检查是否已完成（支持断点续跑）
        if self.is_step_completed(step_num, context):
            self.logger.info(f"Step {step_num} already completed, skipping")
            # 断点续跑场景：补齐内存态状态，便于摘要统计与后续逻辑判断
            self.step_status[step_num] = "completed"
            return self._load_step_result(step_num)
        
        # 标记开始
        self.mark_step_started(step_num)
        
        try:
            # 获取处理器
            handler = self.step_handlers[step_num]
            
            # 准备上下文
            if context is None:
                context = {}
            context["step_num"] = step_num
            context["output_dir"] = str(self.get_step_output_dir(step_num))
            context["config"] = self.config
            
            # 执行步骤
            self.logger.info(f"Executing step {step_num}...")
            result = await handler(context)
            
            # 保存步骤执行结果
            if result and isinstance(result, dict):
                step_dir = self.get_step_output_dir(step_num)
                result_file = step_dir / "result.json"
                write_json(result, str(result_file))
                self.logger.info(f"Step {step_num} result saved to {result_file}")
            
            # 标记完成
            output_files = result.get("output_files", []) if result else []
            metadata = result.get("metadata", {}) if result else {}
            self.mark_step_completed(step_num, output_files, metadata)
            
            return result
        
        except Exception as e:
            # 标记失败
            error_message = f"{type(e).__name__}: {str(e)}"
            self.mark_step_failed(step_num, error_message, tb=traceback.format_exc())
            
            # 根据配置决定是否继续
            if self.config.get("continue_on_error", False):
                self.logger.warning(f"Step {step_num} failed, but continue_on_error is enabled")
                return None
            else:
                raise
    
    def _load_step_result(self, step_num: int) -> dict:
        """加载已完成的步骤结果"""
        step_dir = self.get_step_output_dir(step_num)
        
        # 首先尝试加载步骤的执行结果文件
        result_file = step_dir / "result.json"
        if result_file.exists():
            return read_json(str(result_file))
        
        # 如果没有执行结果文件，再加载状态文件
        status_file = step_dir / "status.json"
        if status_file.exists():
            return read_json(str(status_file))
        
        # 如果都没有，返回空字典
        return {}
    
    async def run_steps(self, start_step: int = None, end_step: int = None, context: dict = None):
        """运行多个步骤
        
        Args:
            start_step: 起始步骤（默认从配置读取）
            end_step: 结束步骤（默认从配置读取）
            context: 上下文信息
        """
        # 从配置读取范围
        if start_step is None:
            start_step = self.config.get("start_step", 1)
        if end_step is None:
            end_step = self.config.get("end_step", 8)
        
        self.logger.info(f"Running steps {start_step} to {end_step}")
        
        # 确保上下文存在
        if context is None:
            context = {}
        
        # 依次执行每个步骤（支持基于质量门控的有限返工）
        step_num = start_step
        while step_num <= end_step:
            self.logger.info(f"Processing step {step_num}...")
            result = await self.run_step(step_num, context)
            
            # 更新上下文，将步骤结果传递给下一个步骤
            if result and isinstance(result, dict):
                # 直接更新上下文，将步骤结果的所有键值对添加到上下文中
                context.update(result)

                # Step5 质量门控：轻微差异已在步骤内修复；严重差异触发有限返工
                metadata = result.get("metadata", {}) or {}
                if (
                    step_num == 5
                    and metadata.get("rework_required")
                ):
                    restart_step = int(metadata.get("rework_restart_step", 3))
                    rework_counts = context.setdefault("rework_counts", {})
                    current = int(rework_counts.get("step5", 0)) + 1
                    rework_counts["step5"] = current
                    max_rounds = int(metadata.get("max_rework_rounds", 2))
                    if current <= max_rounds:
                        self.logger.warning(
                            f"Step5 requested rework (round {current}/{max_rounds}), restarting from step {restart_step}. "
                            f"reason={metadata.get('rework_reason', '')}"
                        )
                        # 强制重跑返工区间
                        context["force_rerun"] = True
                        step_num = restart_step
                        continue
                    else:
                        self.logger.warning(
                            f"Step5 rework rounds exceeded ({current}>{max_rounds}), continue without further rework."
                        )
            
            if result is None and not self.config.get("continue_on_error", False):
                self.logger.error(f"Step {step_num} failed, stopping execution")
                break
            step_num += 1
        
        self.logger.info("All steps completed")
    
    def get_execution_summary(self) -> dict:
        """获取执行摘要
        
        Returns:
            执行摘要信息
        """
        summary = {
            "total_steps": len(self.step_status),
            "completed": sum(1 for s in self.step_status.values() if s == "completed"),
            "failed": sum(1 for s in self.step_status.values() if s == "failed"),
            "running": sum(1 for s in self.step_status.values() if s == "running"),
            "details": self.step_status,
        }
        return summary
