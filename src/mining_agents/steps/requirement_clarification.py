#!/usr/bin/env python3
"""Step 1: 需求澄清与人工确认"""

from pathlib import Path
from datetime import datetime
import asyncio
import sys
from ..utils.logger import logger


async def requirement_clarification_handler(context, orchestrator):
    """需求澄清与人工确认"""
    from ..agents.requirement_analyst_agent import RequirementAnalystAgent
    
    logger.info("Starting Requirement Clarification...")
    
    # 初始化 Agent
    agent = await orchestrator.initialize_agent(
        agent_type="RequirementAnalystAgent",
        agent_name="RequirementAnalyst"
    )
    
    # Step1: 强制调用 Deep Research，用于生成更贴近业务的澄清问题（若工具可用）
    output_dir = Path(context.get("output_dir", "./output/requirement_clarification"))
    output_dir.mkdir(parents=True, exist_ok=True)

    mock_mode = context.get("mock_mode", True)
    deep_research_tool = (
        orchestrator.get_tool("deep_research")
        if hasattr(orchestrator, "list_tools") and "deep_research" in (orchestrator.list_tools() or [])
        else None
    )
    research_results = {}
    if deep_research_tool:
        try:
            business_desc = (context.get("business_desc") or "").strip()
            business_desc_for_query = " ".join(business_desc.split())
            query_templates = [
                f"日本 保险 外呼 营销 合规 要求 禁止用语 信息披露 关键点 {business_desc_for_query}",
                f"外呼营销 续保/挽留 话术 合规 最佳实践 日本 保险 {business_desc_for_query}",
                f"电话营销 客户拒绝/挂断 意向识别 判定标准 合规 挽留策略 {business_desc_for_query}",
            ]
            deep_research_cfg = ((context.get("config") or {}).get("deep_research") or {})
            # Step1 默认只执行 1 条查询，避免串行多轮导致耗时过长。
            step1_query_count = int(deep_research_cfg.get("step1_query_count", 1))
            step1_query_count = max(1, min(step1_query_count, len(query_templates)))
            queries = query_templates[:step1_query_count]
            # DeepResearchAgent 非并发安全，默认串行；可按配置启用小并发（建议 <= 2）。
            max_parallel = int(deep_research_cfg.get("step1_max_parallel_queries", 1))
            max_parallel = max(1, min(max_parallel, len(queries)))
            semaphore = asyncio.Semaphore(max_parallel)

            async def _run_query(idx: int, q: str):
                async with semaphore:
                    try:
                        rep = await deep_research_tool.search(
                            q,
                            audit_output_dir=str(output_dir),
                            caller_agent="Step1_RequirementClarification",
                            query_tag=f"step1_q{idx}",
                        )
                        return idx, q, rep, None
                    except Exception as e:
                        return idx, q, None, e

            reports = await asyncio.gather(
                *[_run_query(idx, q) for idx, q in enumerate(queries, start=1)],
                return_exceptions=False,
            )
            reports_dir = output_dir / "step1_research_reports"
            reports_dir.mkdir(parents=True, exist_ok=True)

            for idx, q, rep, err in reports:
                if err is not None:
                    logger.warning(f"Deep Research failed for query[{idx}]: {q}. err={err}")
                    research_results[f"q{idx}"] = {"query": q, "error": str(err), "report_path": None}
                    continue
                fp = reports_dir / f"report_{idx:02d}.md"
                fp.write_text(str(rep), encoding="utf-8")
                research_results[f"q{idx}"] = {"query": q, "report_path": str(fp), "excerpt": str(rep)[:1200]}
        except Exception as e:
            import traceback

            logger.warning(f"Deep Research execution failed in Step1: {e}")
            logger.warning(f"Traceback: {traceback.format_exc()}")

    # 执行 Agent（将研究结果注入，便于基于 Deep Research 产出澄清问题）
    result = await orchestrator.execute_agent(
        agent_name="RequirementAnalyst",
        task="分析需求并生成澄清问题，包含结构化需求规格说明",
        context={
            "business_desc": context.get("business_desc", ""),
            "mock_mode": context.get("mock_mode", True),
            "output_dir": str(output_dir),
            "step_num": context.get("step_num"),
            "research_results": research_results,
        }
    )
    
    # 保存结果到上下文，供后续步骤使用
    clarification_questions = result.get("questions", [])
    context["clarification_questions"] = clarification_questions
    context["requirement_output"] = result
    context["structured_requirements"] = result.get("structured_requirements", {})
    
    # 保存输出文件
    # 按设计文档命名，便于断点续跑与可追溯
    clarification_questions_file = output_dir / "step1_clarification_questions.md"
    structured_requirements_file = output_dir / "step1_structured_requirements.md"

    # 说明：
    # - RequirementAnalystAgent 自身会在 output_dir 下写入 `step1_clarification_questions.md`。
    # - 这里避免在缺少 markdown 字段时用兜底内容覆盖掉 Agent 已生成的文件。
    if not clarification_questions_file.exists():
        questions_lines = ["# 待澄清问题", ""]
        if clarification_questions:
            for q in clarification_questions:
                qid = q.get("id", "")
                qq = q.get("question", "")
                cat = q.get("category", "")
                pr = q.get("priority", "")
                questions_lines.extend(
                    [
                        f"## {qid}: {qq}",
                        "",
                        f"- 类别: `{cat}`",
                        f"- 优先级: `{pr}`",
                        "",
                        "### 您的回答",
                        "",
                        "```",
                        "（请填写）",
                        "```",
                        "",
                        "---",
                        "",
                    ]
                )
        else:
            questions_lines.append("暂无问题")
        with open(clarification_questions_file, "w", encoding="utf-8") as f:
            f.write("\n".join(questions_lines))

    # 结构化需求：如果 Agent 未提供，则生成最小可用版本，确保后续步骤有输入
    should_write_structured = not structured_requirements_file.exists()
    if structured_requirements_file.exists():
        try:
            existing = structured_requirements_file.read_text(encoding="utf-8").strip()
            if existing in {"# 结构化需求\n\n暂无需求", "# 结构化需求\n\n暂无需求\n", "# 结构化需求", "暂无需求"}:
                should_write_structured = True
        except Exception:
            # 读取失败时不覆盖，避免误伤
            should_write_structured = False

    if should_write_structured:
        business_desc = (context.get("business_desc") or "").strip()
        sr_lines = [
            "# 结构化需求",
            "",
            "## 业务描述（原文）",
            "",
            business_desc or "（未提供）",
            "",
            "## 目标与范围",
            "",
            "- 主要目标: （待补充）",
            "- 适用范围/边界: （待补充）",
            "",
            "## 关键场景（初版）",
            "",
            "- 场景: 日本共荣保险营销挽留/续保挽留",
            "- 触发: 客户表达退保/不续保意向",
            "- 目标: 合规沟通 + 澄清原因 + 提供可选方案 + 尽量挽留",
            "",
            "## 合规与约束",
            "",
            "- 金融保险合规: （待补充具体条款/禁语/必须告知事项）",
            "- 隐私与数据: （待补充）",
            "",
            "## 待澄清问题（引用）",
            "",
        ]
        if clarification_questions:
            for q in clarification_questions:
                sr_lines.append(f"- {q.get('id', '')}: {q.get('question', '')}")
        else:
            sr_lines.append("- （无）")
        sr_lines.append("")
        with open(structured_requirements_file, "w", encoding="utf-8") as f:
            f.write("\n".join(sr_lines))
    
    # Human-in-the-Loop 人工确认
    logger.info("\n" + "=" * 60)
    logger.info("需求澄清完成！")
    logger.info("=" * 60)
    logger.info(f"已生成问题清单：{clarification_questions_file.absolute()}")
    logger.info(f"已生成结构化需求：{structured_requirements_file.absolute()}")
    logger.info("")
    
    # UI 模式：不在 Step 1 内阻塞等待人工确认，交由上层（如 Streamlit UI）收集回答后再继续。
    if bool(context.get("ui_mode", False)):
        confirmation_status = "pending"
        use_clarification = False
        feedback_text = "UI 模式：等待用户在界面中完成澄清后再继续执行。"

        user_feedback_file = output_dir / "user_feedback.md"
        with open(user_feedback_file, "w", encoding="utf-8") as f:
            f.write(
                "# 用户反馈\n\n"
                f"- 时间: {datetime.now().isoformat()}\n"
                f"- 确认状态: {confirmation_status}\n"
                f"- 说明: {feedback_text}\n"
            )

        result["clarification_questions"] = clarification_questions
        result["clarification_questions_file"] = str(clarification_questions_file)
        result["structured_requirements_file"] = str(structured_requirements_file)
        result["user_confirmation"] = confirmation_status
        result["use_clarification"] = use_clarification
        result["output_files"] = [str(clarification_questions_file), str(structured_requirements_file), str(user_feedback_file)]
        return result

    # CLI 跳过澄清等待：仍生成问题，但不进入等待确认环节；同时不注入到后续提示词（use_clarification=false）
    if bool(context.get("skip_clarification", False)):
        confirmation_status = "skipped"
        use_clarification = False
        feedback_text = "通过 --skip-clarification 参数跳过澄清等待环节，继续执行后续步骤（仍生成澄清问题，但不注入后续提示词）。"

        user_feedback_file = output_dir / "user_feedback.md"
        with open(user_feedback_file, "w", encoding="utf-8") as f:
            f.write(
                "# 用户反馈\n\n"
                f"- 时间: {datetime.now().isoformat()}\n"
                f"- 确认状态: {confirmation_status}\n"
                f"- 说明: {feedback_text}\n"
            )
        logger.info(f"用户反馈已保存：{user_feedback_file}")
        logger.info(feedback_text)

        result["clarification_questions"] = clarification_questions
        result["clarification_questions_file"] = str(clarification_questions_file)
        result["structured_requirements_file"] = str(structured_requirements_file)
        result["user_confirmation"] = confirmation_status
        result["use_clarification"] = use_clarification
        result["output_files"] = [str(clarification_questions_file), str(structured_requirements_file), str(user_feedback_file)]
        return result
    
    # 等待用户在命令行确认：yes/no；超时则自动跳过澄清
    if True:
        timeout_minutes = (
            (((context.get("config") or {}).get("human_in_loop") or {}).get("clarification_timeout_minutes"))
            or 30
        )
        timeout_seconds = int(timeout_minutes) * 60

        logger.info("请在问题清单中补充/修改答案，然后在命令行输入 yes/no。")
        logger.info(f"- yes: 已完成澄清，后续步骤将使用澄清内容")
        logger.info(f"- no : 跳过澄清，后续步骤不使用澄清内容")
        logger.info(f"- 超时({timeout_minutes}分钟): 自动跳过澄清")

        # 非交互式运行（例如自动化/管道/IDE 后台运行）时，默认继续执行，避免卡死在 input()
        if not sys.stdin.isatty():
            user_confirmation = "timeout"
            logger.info("检测到非交互式环境，默认跳过澄清注入（use_clarification=false）并继续执行。")
        else:
            user_confirmation = None
            try:
                user_confirmation = await asyncio.wait_for(
                    asyncio.to_thread(input, "确认继续执行？(yes/no): "),
                    timeout=timeout_seconds,
                )
            except asyncio.TimeoutError:
                user_confirmation = "timeout"

        normalized = (user_confirmation or "").strip().lower()
        if normalized in {"y", "yes"}:
            confirmation_status = "yes"
            use_clarification = True
            feedback_text = "用户确认已完成澄清，继续执行后续步骤，并使用澄清内容。"
        elif normalized in {"n", "no"}:
            confirmation_status = "no"
            use_clarification = False
            feedback_text = "用户选择跳过澄清，继续执行后续步骤，不使用澄清内容。"
        else:
            confirmation_status = "timeout"
            use_clarification = False
            feedback_text = "用户未在超时时间内确认，系统自动跳过澄清并继续执行后续步骤。"

        # 记录反馈
        user_feedback_file = output_dir / "user_feedback.md"
        with open(user_feedback_file, 'w', encoding='utf-8') as f:
            f.write(
                "# 用户反馈\n\n"
                f"- 时间: {datetime.now().isoformat()}\n"
                f"- 确认状态: {confirmation_status}\n"
                f"- 说明: {feedback_text}\n"
            )
        logger.info(f"用户反馈已保存：{user_feedback_file}")
    
    logger.info(f"Requirement clarification completed. Output files: {clarification_questions_file}, {structured_requirements_file}, {user_feedback_file}")
    
    # 在返回的结果中包含文件路径
    result["clarification_questions"] = clarification_questions
    result["clarification_questions_file"] = str(clarification_questions_file)
    result["structured_requirements_file"] = str(structured_requirements_file)
    result["user_confirmation"] = confirmation_status
    result["use_clarification"] = use_clarification
    result["output_files"] = [str(clarification_questions_file), str(structured_requirements_file), str(user_feedback_file)]
    
    return result
