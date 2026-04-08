#!/usr/bin/env python3
"""测试多模型辩论功能"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.mining_agents.steps.dimension_analysis import (
    _load_debate_config,
    _build_debate_roles_from_config,
    _run_agentscope_debate,
    _generate_mock_debate_transcript,
)


async def test_debate_config_loading():
    """测试配置加载"""
    print("=" * 60)
    print("测试 1: 配置加载")
    print("=" * 60)
    
    config = _load_debate_config()
    
    if not config:
        print("[FAIL] 配置加载失败")
        return False
    
    print("[OK] 配置加载成功")
    print(f"  - debate_roles: {list(config.get('debate_roles', {}).keys())}")
    print(f"  - moderator: {config.get('moderator', {}).get('name', 'N/A')}")
    print(f"  - max_rounds: {config.get('debate_config', {}).get('max_rounds', 3)}")
    print(f"  - max_iters_per_agent: {config.get('debate_config', {}).get('max_iters_per_agent', 3)}")
    
    return True


async def test_build_debate_roles():
    """测试构建辩论角色"""
    print("\n" + "=" * 60)
    print("测试 2: 构建辩论角色")
    print("=" * 60)
    
    config = _load_debate_config()
    business_desc = "这是一个电商客服Agent系统，需要处理用户咨询、订单查询、投诉处理等业务场景。"
    
    roles = _build_debate_roles_from_config(config, business_desc)
    
    if not roles:
        print("[FAIL] 角色构建失败")
        return False
    
    print(f"[OK] 构建了 {len(roles)} 个辩论角色:")
    for role in roles:
        print(f"  - {role['display_name']} ({role['name']})")
        print(f"    视角: {role['perspective']}")
        print(f"    关注点: {', '.join(role['focus'])}")
    
    return True


async def test_mock_debate():
    """测试 Mock 辩论"""
    print("\n" + "=" * 60)
    print("测试 3: Mock 辩论生成")
    print("=" * 60)
    
    config = _load_debate_config()
    business_desc = "这是一个电商客服Agent系统，需要处理用户咨询、订单查询、投诉处理等业务场景。"
    
    roles = _build_debate_roles_from_config(config, business_desc)
    
    output_dir = Path("./output/test_debate")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    result = _generate_mock_debate_transcript(business_desc, roles, config)
    transcript = result.get("transcript", [])
    
    transcript_file = output_dir / "mock_debate_transcript.md"
    with open(transcript_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(transcript))
    
    print("[OK] Mock 辩论记录生成成功")
    print(f"  - 行数: {len(transcript)}")
    print(f"  - 输出文件: {transcript_file}")

    # 关键断言：达到最大轮数仍未一致时，应由“终局裁决”给出最终结论（而非预置兜底）
    final_decisions = result.get("final_decisions", [])
    assert final_decisions and isinstance(final_decisions[0], str)
    assert ("最大轮数" in final_decisions[0]) or ("达到最大轮数" in final_decisions[0])
    assert any("终局裁决" in line for line in transcript)
    
    return True


async def test_real_debate():
    """测试真实辩论（需要 API Key）"""
    print("\n" + "=" * 60)
    print("测试 4: 真实辩论执行")
    print("=" * 60)
    
    import os
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[SKIP] 跳过真实辩论测试: 未设置 OPENAI_API_KEY")
        return True
    
    config = _load_debate_config()
    business_desc = "这是一个电商客服Agent系统，需要处理用户咨询、订单查询、投诉处理等业务场景。"
    
    roles = _build_debate_roles_from_config(config, business_desc)
    
    output_dir = Path("./output/test_debate")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"开始执行真实辩论...")
    print(f"  - 角色: {[r['name'] for r in roles]}")
    print(f"  - 最大轮数: {config.get('debate_config', {}).get('max_rounds', 3)}")
    
    try:
        result = await _run_agentscope_debate(
            business_desc=business_desc,
            structured_requirements={"test": "data"},
            debate_roles=roles,
            deep_research_results="",
            output_dir=output_dir,
            debate_config=config
        )
        
        print("[OK] 真实辩论执行成功")
        print(f"  - 轮数: {result['rounds']}")
        print(f"  - 过程日志: {result.get('process_log', 'N/A')}")
        
        transcript_file = output_dir / "real_debate_transcript.md"
        with open(transcript_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(result['transcript']))
        print(f"  - 辩论记录: {transcript_file}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] 真实辩论执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """运行所有测试"""
    print(f"\n{'=' * 60}")
    print(f"多模型辩论功能测试")
    print(f"时间: {datetime.now().isoformat()}")
    print(f"{'=' * 60}\n")
    
    results = []
    
    results.append(("配置加载", await test_debate_config_loading()))
    results.append(("构建角色", await test_build_debate_roles()))
    results.append(("Mock辩论", await test_mock_debate()))
    results.append(("真实辩论", await test_real_debate()))
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for name, passed in results:
        status = "[OK] 通过" if passed else "[FAIL] 失败"
        print(f"  {name}: {status}")
    
    all_passed = all(r[1] for r in results)
    print("\n" + ("=" * 60))
    if all_passed:
        print("所有测试通过!")
    else:
        print("部分测试失败，请检查日志")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    asyncio.run(main())
