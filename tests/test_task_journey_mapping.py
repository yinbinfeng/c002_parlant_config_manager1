#!/usr/bin/env python3
"""测试脚本：验证任务分解与journey数量对应关系"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import json
import yaml
from src.mining_agents.steps.dimension_analysis import (
    _extract_user_segments,
    _extract_business_scenarios,
    _extract_edge_cases,
)
from src.mining_agents.agents.process_agent import ProcessAgent


def test_extract_functions():
    """测试提取函数"""
    test_text = """
    业务描述：日本共荣保险客户营销与留存挽留
    
    用户群体：VIP用户、新用户、活跃用户、高价值用户
    
    业务流程：
    - 咨询流程
    - 办理流程
    - 投诉处理
    - 续保流程
    
    异常情况：超时处理、操作失败、用户投诉、数据异常
    """
    
    user_segments = _extract_user_segments(test_text)
    scenarios = _extract_business_scenarios(test_text)
    edge_cases = _extract_edge_cases(test_text)
    
    print("=" * 60)
    print("提取结果测试")
    print("=" * 60)
    print(f"用户人群 ({len(user_segments)}): {user_segments}")
    print(f"业务场景 ({len(scenarios)}): {scenarios}")
    print(f"边缘情况 ({len(edge_cases)}): {edge_cases}")
    
    combos_count = len(user_segments) * len(scenarios) * len(edge_cases)
    print(f"\n组合数量: {combos_count}")
    
    return user_segments, scenarios, edge_cases


def test_process_agent_journey_generation():
    """测试 ProcessAgent 的 journey 生成逻辑"""
    
    class MockOrchestrator:
        def get_tool(self, name):
            return None
        def list_tools(self):
            return []
    
    mock_atomic_tasks = [
        {
            "task_id": "COMP1_MAIN",
            "dimension": "component::COMP1",
            "description": "Journey设计：预约挂号流程",
            "priority": "high"
        },
        {
            "task_id": "MATRIX_001",
            "dimension": "user_segment_x_scenario_x_edge_case",
            "description": "用户人群[VIP用户] × 业务场景[咨询流程] × 边缘情况[超时处理] 组合设计",
            "priority": "high"
        },
        {
            "task_id": "MATRIX_002",
            "dimension": "user_segment_x_scenario_x_edge_case",
            "description": "用户人群[新用户] × 业务场景[办理流程] × 边缘情况[正常流程] 组合设计",
            "priority": "medium"
        },
        {
            "task_id": "MATRIX_003",
            "dimension": "user_segment_x_scenario_x_edge_case",
            "description": "用户人群[活跃用户] × 业务场景[投诉处理] × 边缘情况[用户投诉] 组合设计",
            "priority": "high"
        },
    ]
    
    print("\n" + "=" * 60)
    print("ProcessAgent Journey 生成测试")
    print("=" * 60)
    
    output_dir = Path("./output/test_process_agent")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    agent = ProcessAgent("TestProcessAgent", MockOrchestrator())
    
    context = {
        "atomic_tasks": mock_atomic_tasks,
        "business_desc": "测试业务描述",
        "output_dir": str(output_dir),
        "mock_mode": True,
    }
    
    result = agent._mock_run("测试任务", context)
    
    print(f"生成的 Journey 文件数: {len(result.get('journey_files', []))}")
    print(f"处理的原子任务数: {result.get('atomic_tasks_processed', 0)}")
    print(f"消息: {result.get('message', '')}")
    
    journey_files = result.get('journey_files', [])
    for jf in journey_files[:5]:
        print(f"  - {Path(jf).name}")
    if len(journey_files) > 5:
        print(f"  - ... 还有 {len(journey_files) - 5} 个文件")
    
    if journey_files:
        sample_file = Path(journey_files[0])
        if sample_file.exists():
            with open(sample_file, 'r', encoding='utf-8') as f:
                sample_data = json.load(f)
            print(f"\n示例 Journey 文件内容预览 ({sample_file.name}):")
            print(f"  - source_task_id: {sample_data.get('source_task_id')}")
            print(f"  - journeys count: {len(sample_data.get('journeys', []))}")
            if sample_data.get('journeys'):
                j = sample_data['journeys'][0]
                print(f"  - sop_id: {j.get('sop_id')}")
                print(f"  - sop_title: {j.get('sop_title')}")
                print(f"  - states count: {len(j.get('sop_states', []))}")
    
    return result


def test_dimension_analysis_combination():
    """测试维度分析的组合矩阵生成"""
    
    print("\n" + "=" * 60)
    print("维度分析组合矩阵测试")
    print("=" * 60)
    
    user_segments = ["VIP用户", "新用户", "活跃用户", "流失风险用户"]
    scenarios = ["咨询流程", "办理流程", "投诉处理", "续保流程"]
    edge_cases = ["正常流程", "超时处理", "操作失败", "用户投诉"]
    
    combos = []
    for u in user_segments[:4]:
        for s in scenarios[:5]:
            for e in edge_cases[:4]:
                combos.append((u, s, e))
                if len(combos) >= 30:
                    break
            if len(combos) >= 30:
                break
        if len(combos) >= 30:
            break
    
    print(f"用户人群: {user_segments}")
    print(f"业务场景: {scenarios}")
    print(f"边缘情况: {edge_cases}")
    print(f"\n生成的组合数量: {len(combos)}")
    
    print("\n前 10 个组合:")
    for i, (u, s, e) in enumerate(combos[:10], 1):
        print(f"  {i}. {u} × {s} × {e}")
    
    return combos


def main():
    print("=" * 60)
    print("任务分解与 Journey 数量对应关系测试")
    print("=" * 60)
    
    test_extract_functions()
    test_process_agent_journey_generation()
    test_dimension_analysis_combination()
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
