#!/usr/bin/env python3
"""
performance_tracker.py
文件格式: Python 源码

性能追踪器 - 统计Agent执行时间、模型调用次数等性能指标
"""

import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path
import json

from .logger import logger


@dataclass
class AgentStats:
    """Agent统计信息"""
    name: str
    total_time: float = 0.0
    call_count: int = 0
    llm_call_count: int = 0
    tavily_call_count: int = 0
    execution_times: List[float] = field(default_factory=list)
    start_time: Optional[float] = None
    
    @property
    def avg_time(self) -> float:
        """平均执行时间"""
        return self.total_time / self.call_count if self.call_count > 0 else 0.0
    
    @property
    def min_time(self) -> float:
        """最小执行时间"""
        return min(self.execution_times) if self.execution_times else 0.0
    
    @property
    def max_time(self) -> float:
        """最大执行时间"""
        return max(self.execution_times) if self.execution_times else 0.0


@dataclass
class StepStats:
    """步骤统计信息"""
    step_num: int
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    duration: float = 0.0
    status: str = "pending"
    agent_calls: List[str] = field(default_factory=list)


class PerformanceTracker:
    """性能追踪器 - 统计Agent执行时间、模型调用次数等性能指标
    
    使用单例模式，确保全局只有一个实例
    """
    
    _instance: Optional['PerformanceTracker'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化性能追踪器"""
        if self._initialized:
            return
        
        self._initialized = True
        self.logger = logger
        
        self.agent_stats: Dict[str, AgentStats] = {}
        self.step_stats: Dict[int, StepStats] = {}
        
        self.global_start_time: Optional[float] = None
        self.global_end_time: Optional[float] = None
        
        self.total_llm_calls: int = 0
        self.total_tavily_calls: int = 0
        self.total_agent_calls: int = 0
    
    def reset(self):
        """重置所有统计数据"""
        self.agent_stats.clear()
        self.step_stats.clear()
        self.global_start_time = None
        self.global_end_time = None
        self.total_llm_calls = 0
        self.total_tavily_calls = 0
        self.total_agent_calls = 0
        self.logger.info("Performance tracker reset")
    
    def start_global_tracking(self):
        """开始全局追踪"""
        self.global_start_time = time.time()
        self.logger.info("Performance tracking started")
    
    def end_global_tracking(self):
        """结束全局追踪"""
        self.global_end_time = time.time()
        self.logger.info("Performance tracking ended")
    
    def start_step(self, step_num: int):
        """开始步骤追踪
        
        Args:
            step_num: 步骤编号
        """
        if step_num not in self.step_stats:
            self.step_stats[step_num] = StepStats(step_num=step_num)
        
        self.step_stats[step_num].start_time = time.time()
        self.step_stats[step_num].status = "running"
        self.logger.debug(f"Step {step_num} tracking started")
    
    def end_step(self, step_num: int, status: str = "completed"):
        """结束步骤追踪
        
        Args:
            step_num: 步骤编号
            status: 步骤状态
        """
        if step_num not in self.step_stats:
            self.logger.warning(f"Step {step_num} not found in tracking")
            return
        
        step_stat = self.step_stats[step_num]
        step_stat.end_time = time.time()
        step_stat.duration = step_stat.end_time - (step_stat.start_time or step_stat.end_time)
        step_stat.status = status
        self.logger.debug(f"Step {step_num} tracking ended: {step_stat.duration:.2f}s")
    
    def start_agent(self, agent_name: str):
        """开始Agent执行追踪
        
        Args:
            agent_name: Agent名称
        """
        if agent_name not in self.agent_stats:
            self.agent_stats[agent_name] = AgentStats(name=agent_name)
        
        self.agent_stats[agent_name].start_time = time.time()
        self.total_agent_calls += 1
        self.logger.debug(f"Agent '{agent_name}' execution started")
    
    def end_agent(self, agent_name: str):
        """结束Agent执行追踪
        
        Args:
            agent_name: Agent名称
        """
        if agent_name not in self.agent_stats:
            self.logger.warning(f"Agent '{agent_name}' not found in tracking")
            return
        
        agent_stat = self.agent_stats[agent_name]
        end_time = time.time()
        
        if agent_stat.start_time:
            duration = end_time - agent_stat.start_time
            agent_stat.total_time += duration
            agent_stat.execution_times.append(duration)
            agent_stat.call_count += 1
            agent_stat.start_time = None
            
            self.logger.debug(
                f"Agent '{agent_name}' execution ended: {duration:.2f}s "
                f"(total: {agent_stat.total_time:.2f}s, calls: {agent_stat.call_count})"
            )
    
    def record_llm_call(self, agent_name: str):
        """记录LLM调用
        
        Args:
            agent_name: Agent名称
        """
        self.record_llm_calls(agent_name, 1)

    def record_llm_calls(self, agent_name: str, count: int):
        """记录多次 LLM 推理（例如 ReAct 多轮）。"""
        c = max(0, int(count))
        if c == 0:
            return
        if agent_name not in self.agent_stats:
            self.agent_stats[agent_name] = AgentStats(name=agent_name)
        self.agent_stats[agent_name].llm_call_count += c
        self.total_llm_calls += c
        self.logger.debug(
            "LLM calls +{} for agent '{}' (agent_total={}, global_total={})",
            c,
            agent_name,
            self.agent_stats[agent_name].llm_call_count,
            self.total_llm_calls,
        )

    def record_tavily_call(self, agent_name: str):
        """记录一次 Tavily（Deep Research）HTTP 搜索成功调用。"""
        if agent_name not in self.agent_stats:
            self.agent_stats[agent_name] = AgentStats(name=agent_name)
        self.agent_stats[agent_name].tavily_call_count += 1
        self.total_tavily_calls += 1
        self.logger.debug(
            "Tavily call recorded for '{}' (agent_total={}, global_total={})",
            agent_name,
            self.agent_stats[agent_name].tavily_call_count,
            self.total_tavily_calls,
        )
    
    def record_step_agent_call(self, step_num: int, agent_name: str):
        """记录步骤中的Agent调用
        
        Args:
            step_num: 步骤编号
            agent_name: Agent名称
        """
        if step_num not in self.step_stats:
            self.step_stats[step_num] = StepStats(step_num=step_num)
        
        self.step_stats[step_num].agent_calls.append(agent_name)
    
    def get_global_duration(self) -> float:
        """获取全局执行时长
        
        Returns:
            执行时长（秒）
        """
        if self.global_start_time and self.global_end_time:
            return self.global_end_time - self.global_start_time
        elif self.global_start_time:
            return time.time() - self.global_start_time
        return 0.0
    
    def generate_report(self) -> Dict[str, Any]:
        """生成性能统计报告
        
        Returns:
            统计报告字典
        """
        report = {
            "summary": {
                "total_duration": self.get_global_duration(),
                "total_agent_calls": self.total_agent_calls,
                "total_llm_calls": self.total_llm_calls,
                "total_tavily_calls": self.total_tavily_calls,
                "total_agents": len(self.agent_stats),
                "total_steps": len(self.step_stats),
                "generated_at": datetime.now().isoformat(),
            },
            "agent_statistics": {},
            "step_statistics": {},
            "performance_ranking": {
                "by_total_time": [],
                "by_avg_time": [],
                "by_llm_calls": [],
                "by_tavily_calls": [],
            }
        }
        
        for agent_name, stats in self.agent_stats.items():
            report["agent_statistics"][agent_name] = {
                "total_time": round(stats.total_time, 2),
                "avg_time": round(stats.avg_time, 2),
                "min_time": round(stats.min_time, 2),
                "max_time": round(stats.max_time, 2),
                "call_count": stats.call_count,
                "llm_call_count": stats.llm_call_count,
                "tavily_call_count": stats.tavily_call_count,
            }
        
        for step_num, stats in self.step_stats.items():
            report["step_statistics"][str(step_num)] = {
                "duration": round(stats.duration, 2),
                "status": stats.status,
                "agent_calls": stats.agent_calls,
                "agent_call_count": len(stats.agent_calls),
            }
        
        sorted_by_time = sorted(
            self.agent_stats.items(),
            key=lambda x: x[1].total_time,
            reverse=True
        )
        report["performance_ranking"]["by_total_time"] = [
            {"agent": name, "total_time": round(stats.total_time, 2)}
            for name, stats in sorted_by_time
        ]
        
        sorted_by_avg = sorted(
            self.agent_stats.items(),
            key=lambda x: x[1].avg_time,
            reverse=True
        )
        report["performance_ranking"]["by_avg_time"] = [
            {"agent": name, "avg_time": round(stats.avg_time, 2)}
            for name, stats in sorted_by_avg
        ]
        
        sorted_by_llm = sorted(
            self.agent_stats.items(),
            key=lambda x: x[1].llm_call_count,
            reverse=True
        )
        report["performance_ranking"]["by_llm_calls"] = [
            {"agent": name, "llm_call_count": stats.llm_call_count}
            for name, stats in sorted_by_llm
        ]

        sorted_by_tv = sorted(
            self.agent_stats.items(),
            key=lambda x: x[1].tavily_call_count,
            reverse=True,
        )
        report["performance_ranking"]["by_tavily_calls"] = [
            {"agent": name, "tavily_call_count": stats.tavily_call_count}
            for name, stats in sorted_by_tv
        ]
        
        return report

    def save_step_performance_snapshot(self, step_num: int, step_dir: str) -> Optional[str]:
        """将截至当前的累计性能指标切片写入对应 step 目录（便于审计）。"""
        report = self.generate_report()
        step_key = str(step_num)
        step_info = report["step_statistics"].get(step_key, {})
        agents = step_info.get("agent_calls", [])
        agents_stats = {
            a: report["agent_statistics"][a]
            for a in agents
            if a in report["agent_statistics"]
        }
        payload = {
            "step": step_num,
            "step_statistics": step_info,
            "agents_invoked_in_step": agents,
            "agent_metrics_for_step_agents": agents_stats,
            "global_totals": report["summary"],
            "full_agent_statistics": report["agent_statistics"],
        }
        out = Path(step_dir) / "performance_stats.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        self.logger.info("Step {} performance snapshot: {}", step_num, out)
        return str(out)
    
    def save_report(self, output_path: str) -> str:
        """保存性能统计报告到文件
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            保存的文件路径
        """
        report = self.generate_report()
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Performance report saved to: {output_file}")
        return str(output_file)
    
    def print_summary(self):
        """打印性能统计摘要"""
        report = self.generate_report()
        
        self.logger.info("")
        self.logger.info("=" * 80)
        self.logger.info("性能统计报告")
        self.logger.info("=" * 80)
        
        summary = report["summary"]
        self.logger.info(f"总执行时长: {summary['total_duration']:.2f} 秒")
        self.logger.info(f"总Agent调用次数: {summary['total_agent_calls']}")
        self.logger.info(f"总LLM调用次数: {summary['total_llm_calls']}")
        self.logger.info(f"总Tavily调用次数: {summary.get('total_tavily_calls', 0)}")
        self.logger.info(f"涉及Agent数量: {summary['total_agents']}")
        self.logger.info(f"涉及步骤数量: {summary['total_steps']}")
        
        self.logger.info("")
        self.logger.info("-" * 80)
        self.logger.info("Agent执行统计（按总时间排序）:")
        self.logger.info("-" * 80)
        
        for item in report["performance_ranking"]["by_total_time"]:
            agent_name = item["agent"]
            stats = report["agent_statistics"][agent_name]
            self.logger.info(
                f"  {agent_name:30s} | "
                f"总时间: {stats['total_time']:7.2f}s | "
                f"平均: {stats['avg_time']:6.2f}s | "
                f"调用: {stats['call_count']:3d}次 | "
                f"LLM: {stats['llm_call_count']:3d}次 | "
                f"Tavily: {stats.get('tavily_call_count', 0):3d}次"
            )
        
        self.logger.info("")
        self.logger.info("-" * 80)
        self.logger.info("步骤执行统计:")
        self.logger.info("-" * 80)
        
        for step_num in sorted(report["step_statistics"].keys(), key=int):
            stats = report["step_statistics"][step_num]
            self.logger.info(
                f"  Step {step_num}: {stats['duration']:7.2f}s | "
                f"状态: {stats['status']:10s} | "
                f"Agent调用: {stats['agent_call_count']}次"
            )
        
        self.logger.info("=" * 80)


def get_performance_tracker() -> PerformanceTracker:
    """获取性能追踪器单例
    
    Returns:
        PerformanceTracker实例
    """
    return PerformanceTracker()
