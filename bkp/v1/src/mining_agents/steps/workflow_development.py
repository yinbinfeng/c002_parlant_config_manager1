#!/usr/bin/env python3
"""Step 3: 工作流并行开发"""

from pathlib import Path
from ..utils.logger import logger
import asyncio
import os


async def workflow_development_handler(context, orchestrator):
    """工作流并行开发"""
    from ..agents.process_agent import ProcessAgent
    from ..agents.glossary_agent import GlossaryAgent
    from ..agents.quality_agent import QualityAgent
    
    logger.info("Starting Workflow Parallel Development...")
    
    # 检查前置条件
    if not context.get("atomic_tasks"):
        # 尝试从 Step 2 的结果中加载
        step2_output_dir = Path(context.get("step2_output_dir", "./output/dimension_analysis"))
        result_file = step2_output_dir / "result.json"
        if result_file.exists():
            import json
            with open(result_file, 'r', encoding='utf-8') as f:
                step2_result = json.load(f)
            context["atomic_tasks"] = step2_result.get("atomic_tasks", [])
            context["structured_requirements"] = step2_result.get("structured_requirements", {})
        else:
            raise ValueError("Dimension analysis must be completed before workflow development")
    
    output_dir = Path(context.get("output_dir", "./output/workflow_development"))
    output_dir.mkdir(parents=True, exist_ok=True)

    # 并发控制：严格遵循 max_parallel_agents（1=完全串行）
    max_parallel_agents = (
        (context.get("config") or {}).get("max_parallel_agents")
        or getattr(orchestrator, "config", {}).get("max_parallel_agents")
        or 1
    )
    try:
        max_parallel_agents = int(max_parallel_agents)
    except Exception:
        max_parallel_agents = 1
    
    # 初始化需要的 Agent
    await orchestrator.initialize_agent(
        agent_type="ProcessAgent",
        agent_name="ProcessAgent"
    )
    await orchestrator.initialize_agent(
        agent_type="GlossaryAgent",
        agent_name="GlossaryAgent"
    )
    await orchestrator.initialize_agent(
        agent_type="QualityAgent",
        agent_name="QualityAgent"
    )
    
    # 并行执行三个 Agent
    # 提取核心目标和行业参数
    business_desc = context.get("business_desc", "")
    core_goal = context.get("core_goal", business_desc[:200] if business_desc else "")
    industry = context.get("industry", "通用")
    
    tasks = [
        {
            "agent_name": "ProcessAgent",
            "task": "设计业务流程和状态机，生成 journey 配置，包含完整的分支条件和状态转换",
            "context": {
                "business_desc": context.get("business_desc", ""),
                "atomic_tasks": context.get("atomic_tasks", []),
                "structured_requirements": context.get("structured_requirements", {}),
                "core_goal": core_goal,
                "industry": industry,
                "mock_mode": context.get("mock_mode", True),
                # 资源隔离：每个 Agent 独立输出目录，避免并发写冲突
                "output_dir": str(output_dir / "process_agent"),
            }
        },
        {
            "agent_name": "GlossaryAgent",
            "task": "提取和定义专业术语体系，生成 glossary 配置，建立术语之间的关联关系",
            "context": {
                "business_desc": context.get("business_desc", ""),
                "atomic_tasks": context.get("atomic_tasks", []),
                "structured_requirements": context.get("structured_requirements", {}),
                "core_goal": core_goal,
                "industry": industry,
                "mock_mode": context.get("mock_mode", True),
                "output_dir": str(output_dir / "glossary_agent"),
            }
        },
        {
            "agent_name": "QualityAgent",
            "task": "对设计内容进行质量检查，生成 qa 报告，检查规则之间的冲突和状态机的死循环",
            "context": {
                "business_desc": context.get("business_desc", ""),
                "atomic_tasks": context.get("atomic_tasks", []),
                "structured_requirements": context.get("structured_requirements", {}),
                "core_goal": core_goal,
                "industry": industry,
                "mock_mode": context.get("mock_mode", True),
                "output_dir": str(output_dir / "quality_agent"),
            }
        },
    ]
    
    # 执行策略：max_parallel_agents=1 → 串行；否则限流并发
    if max_parallel_agents <= 1:
        results = []
        for t in tasks:
            results.append(await orchestrator.execute_agent(t["agent_name"], t["task"], t.get("context", {})))
    else:
        sem = asyncio.Semaphore(max_parallel_agents)

        async def _run_one(tinfo: dict) -> dict:
            async with sem:
                return await orchestrator.execute_agent(
                    agent_name=tinfo["agent_name"],
                    task=tinfo["task"],
                    context=tinfo.get("context", {}),
                )

        gathered = await asyncio.gather(*[_run_one(t) for t in tasks], return_exceptions=True)
        results = []
        for r in gathered:
            if isinstance(r, Exception):
                logger.error(f"Workflow agent execution failed: {r}")
                results.append({"error": str(r)})
            else:
                results.append(r)
    
    # 提取结果
    output_files = []
    journey_files = []
    glossary_files = []
    qa_files = []
    
    for i, result in enumerate(results):
        if isinstance(result, dict):
            # 收集输出文件
            if "output_files" in result:
                output_files.extend(result.get("output_files", []))
            
            # 分类文件类型
            if "journey_files" in result:
                journey_files.extend(result.get("journey_files", []))
            if "glossary_files" in result:
                glossary_files.extend(result.get("glossary_files", []))
            if "qa_files" in result:
                qa_files.extend(result.get("qa_files", []))
    
    # 保存结果到上下文
    context["workflow_output_files"] = output_files
    context["journey_files"] = journey_files
    context["glossary_files"] = glossary_files
    context["qa_files"] = qa_files

    # 校验输出文件确实存在，避免“仅返回路径未落盘”
    missing = [p for p in output_files if p and isinstance(p, str) and not os.path.exists(p)]
    if missing:
        raise FileNotFoundError(f"Step3 reported output files but missing on disk: {missing[:5]}")
    
    # 生成修正历史记录
    correction_history = {
        "process_agent_corrections": [],
        "glossary_agent_corrections": [],
        "quality_agent_corrections": []
    }
    
    # 保存修正历史
    correction_file = output_dir / "step3_correction_history.json"
    with open(correction_file, 'w', encoding='utf-8') as f:
        import json
        json.dump(correction_history, f, ensure_ascii=False, indent=2)
    
    output_files.append(str(correction_file))
    
    logger.info(f"Workflow development completed. Output files: {len(output_files)}")
    logger.info(f"  - Journey files: {len(journey_files)}")
    logger.info(f"  - Glossary files: {len(glossary_files)}")
    logger.info(f"  - QA files: {len(qa_files)}")
    
    return {
        "output_files": output_files,
        "journey_files": journey_files,
        "glossary_files": glossary_files,
        "qa_files": qa_files,
    }
