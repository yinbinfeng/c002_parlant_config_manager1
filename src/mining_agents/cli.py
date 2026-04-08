#!/usr/bin/env python3
"""
Mining Agents 命令行接口
文件格式: Python 源码
"""

import argparse
import sys
import asyncio
from typing import Dict, List
from pathlib import Path
import os
from dotenv import load_dotenv
from .utils.logger import logger, configure_logging
from .engine import build_core_engine
from .utils.performance_tracker import get_performance_tracker


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="Parlant Agent 配置挖掘系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 从第 1 步执行到第 9 步
  python -m mining_agents.main --business-desc "电商客服 Agent"
  
  # 从特定步骤开始（断点续跑）
  python -m mining_agents.main --start-step 3 --business-desc "..."
  
  # 强制重跑所有步骤
  python -m mining_agents.main --force-rerun --business-desc "..."
        """
    )
    
    parser.add_argument(
        "--business-desc", "-b",
        type=str,
        # required=True,
        help="业务描述文本"
    )
    
    parser.add_argument(
        "--excel-file", "-e",
        type=str,
        default=None,
        help="私域对话数据 Excel 文件路径（可选）"
    )

    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default="./output",
        help="输出目录（默认：./output）"
    )
    
    parser.add_argument(
        "--config", "-c",
        type=str,
        default=Path(__file__).parent.parent.parent / "egs" / "v0.1.0_minging_agents" / "config" / "system_config.yaml",
        help="配置文件路径"
    )

    parser.add_argument(
        "--env-file",
        type=str,
        default=None,
        help="环境变量文件路径（可选）。传入则从文件加载，否则仅从系统环境变量读取",
    )
    
    parser.add_argument(
        "--start-step",
        type=int,
        default=1,
        choices=range(1, 10),
        help="起始步骤（1-9，默认：1）"
    )
    
    parser.add_argument(
        "--end-step",
        type=int,
        default=5,
        choices=range(1, 10),
        help="结束步骤（1-9，默认：5）"
    )
    
    parser.add_argument(
        "--force-rerun",
        action="store_true",
        help="强制重跑已完成的步骤（默认：否）"
    )

    parser.add_argument(
        "--clean-output",
        action="store_true",
        help="执行前删除输出目录（默认：否，谨慎使用）"
    )
    
    parser.add_argument(
        "--max-parallel",
        type=int,
        default=1,
        choices=range(1, 11),
        help="最大并发 Agent 数（1-10，默认：1）"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="启用详细日志"
    )

    parser.add_argument(
        "--debug",
        # action="store_true",
        default=False,
        help="启用调试模式（使用内置业务描述与固化参数）"
    )
    
    parser.add_argument(
        "--mode",
        type=str,
        choices=["mock", "real", "fix"],
        default="real",
        help="运行模式：mock（不实际调用 LLM API）、real（需要配置 API Key）或 fix（使用固化配置）"
    )
    
    parser.add_argument(
        "--skip-clarification",
        action="store_true",
        help="跳过人工澄清环节，直接执行后续步骤"
    )
    
    return parser.parse_args()


async def run_system(args):
    """运行系统
    
    Args:
        args: 命令行参数
    """
    logger.info("初始化 Mining Agents 系统...")
    
    performance_tracker = get_performance_tracker()
    performance_tracker.reset()
    performance_tracker.start_global_tracking()

    # 确定模式
    mock_mode = args.mode == "mock"
    if args.mode == "real":
        logger.info("使用真实模式（需要有效的 API Key）")
    elif args.mode == "fix":
        logger.info("使用固化配置模式（使用内置业务描述与固化参数）")
    else:
        logger.info("使用 Mock 模式（测试用）")
        logger.warning("当前为 Mock 模式，产物深度与真实性会显著降低，仅建议用于链路联调。")

    debug_mode = args.debug
    if debug_mode:
        logger.info("启用调试模式")

    step_manager, orchestrator = build_core_engine(
        config_path=str(Path(args.config)),
        output_dir=str(args.output_dir),
        mode=str(args.mode),
        max_parallel=int(args.max_parallel),
        debug_mode=bool(debug_mode),
    )
    
    # 处理 --clean-output：删除输出目录
    if args.clean_output:
        output_path = Path(args.output_dir)
        if output_path.exists():
            logger.warning(f"--clean-output 已启用，正在删除输出目录: {output_path}")
            import shutil
            try:
                shutil.rmtree(output_path)
                logger.info(f"输出目录已删除: {output_path}")
            except Exception as e:
                logger.error(f"删除输出目录失败: {e}")
                raise

    # 处理 --force-rerun：删除指定步骤的目录
    if args.force_rerun:
        import shutil
        output_base_path = Path(args.output_dir)
        if output_base_path.exists():
            # v2（9 步法）步骤目录名称映射
            step_dir_map = {
                1: "step1_requirement_clarification",
                2: "step2_objective_alignment_main_sop",
                3: "step3_global_rules_and_glossary",
                4: "step4_user_profile",
                5: "step5_branch_sop_parallel",
                6: "step6_edge_cases",
                7: "step_extract_canned_obs",
                8: "step7_config_assembly",
                9: "step8_validation",
            }
            
            # 每个步骤额外输出的文件夹（除了step目录外）
            step_extra_outputs = {
                8: ["parlant_agent_config"],  # Step8 输出 parlant_agent_config
                9: ["final_parlant_config"],   # Step9 输出 final_parlant_config（校验后的最终版本）
            }
            
            # 删除指定步骤的目录
            for step_num in range(args.start_step, args.end_step + 1):
                dir_name = step_dir_map.get(step_num, f"step{step_num}")
                step_dir = output_base_path / dir_name
                if step_dir.exists():
                    logger.warning(f"--force-rerun 已启用，正在删除 Step {step_num} 输出目录: {step_dir}")
                    try:
                        shutil.rmtree(step_dir)
                        logger.info(f"Step {step_num} 输出目录已删除: {step_dir}")
                    except Exception as e:
                        logger.error(f"删除 Step {step_num} 输出目录失败: {e}")
                
                # 删除该步骤额外输出的文件夹
                extra_dirs = step_extra_outputs.get(step_num, [])
                for extra_dir_name in extra_dirs:
                    extra_dir = output_base_path / extra_dir_name
                    if extra_dir.exists():
                        logger.warning(f"--force-rerun 已启用，正在删除 Step {step_num} 额外输出目录: {extra_dir}")
                        try:
                            shutil.rmtree(extra_dir)
                            logger.info(f"Step {step_num} 额外输出目录已删除: {extra_dir}")
                        except Exception as e:
                            logger.error(f"删除 Step {step_num} 额外输出目录失败: {e}")

    # 准备上下文
    context = {
        "business_desc": args.business_desc,
        "mock_mode": mock_mode,
        "debug_mode": debug_mode,
        "force_rerun": args.force_rerun,
        "skip_clarification": args.skip_clarification,
    }
    
    # 运行步骤
    if args.business_desc:
        desc_preview = args.business_desc[:50] + "..." if len(args.business_desc) > 50 else args.business_desc
        logger.info(f"执行业务描述：{desc_preview}")
    else:
        logger.info("未提供业务描述，将在需求澄清步骤中生成")
    logger.info(f"执行步骤：{args.start_step} -> {args.end_step}")
    logger.info("")
    
    try:
        # 运行指定范围的步骤
        await step_manager.run_steps(
            start_step=args.start_step,
            end_step=args.end_step,
            context=context
        )
        
        # 输出执行摘要
        summary = step_manager.get_execution_summary()
        logger.info("")
        logger.info("=" * 60)
        logger.info("执行完成！摘要信息：")
        logger.info(f"  总步骤数：{summary['total_steps']}")
        logger.info(f"  已完成：{summary['completed']}")
        logger.info(f"  失败：{summary['failed']}")
        logger.info(f"  进行中：{summary['running']}")
        logger.info("=" * 60)
        
        # 如果有需求澄清的输出，显示提示
        if step_manager.is_step_completed(1):
            requirement_clarification_dir = step_manager.get_step_output_dir(1)
            questions_file = requirement_clarification_dir / "clarification_questions.md"
            if questions_file.exists():
                logger.info("")
                logger.info("需求澄清完成！问题清单已保存到：")
                logger.info(f"   {questions_file.absolute()}")
                logger.info("")
                logger.info("下一步操作：")
                logger.info("  1. 查看并回答问题清单中的问题")
                if args.business_desc:
                    logger.info(f"  2. 继续执行后续步骤:")
                    logger.info(f"     python -m mining_agents.main --business-desc \"{args.business_desc}\" --start-step 2")
                else:
                    logger.info(f"  2. 补充业务描述后继续执行后续步骤:")
                    logger.info(f"     python -m mining_agents.main --business-desc \"<您的业务描述>\" --start-step 2")
        
    except Exception as e:
        logger.error("")
        try:
            err_text = str(e)
        except Exception:
            err_text = repr(e)
        logger.error(f"执行失败：{err_text}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return False
    
    finally:
        performance_tracker.end_global_tracking()
        
        performance_tracker.print_summary()
        
        report_path = Path(args.output_dir) / "performance_report.json"
        performance_tracker.save_report(str(report_path))
        
        await orchestrator.cleanup()
    
    return True


def _generate_debate_summary(
    expert_opinions: List[Dict], 
    user_concerns: List[Dict], 
    requirement_defense: List[Dict]
) -> str:
    """生成辩论摘要
    
    Args:
        expert_opinions: 专家意见列表
        user_concerns: 用户关切列表
        requirement_defense: 需求辩护意见列表
        
    Returns:
        Markdown 格式的辩论摘要
    """
    lines = [
        "# Step 2: 多 Agent 辩论摘要",
        "",
        "**辩论参与方**:",
        "- **领域专家**: 关注技术可行性和行业最佳实践",
        "- **客户倡导者**: 关注用户体验和可接受性",
        "- **需求分析师**: 关注需求完整性和业务目标达成",
        "",
        "---",
        "",
    ]
    
    # 专家观点摘要
    lines.append("## 领域专家核心观点")
    lines.append("")
    if expert_opinions:
        for opinion in expert_opinions[:3]:  # 只显示前 3 个
            confidence_label = "HIGH" if opinion.get("confidence") == "high" else "LOW"
            lines.append(f"[{confidence_label}] **{opinion.get('title', 'N/A')}**")
            lines.append(f"> {opinion.get('opinion', 'N/A')[:100]}...")
            lines.append("")
    else:
        lines.append("*暂无专家意见*")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # 用户关切摘要
    lines.append("## 客户倡导者核心关切")
    lines.append("")
    if user_concerns:
        for concern in user_concerns[:3]:  # 只显示前 3 个
            impact_label = "HIGH" if concern.get("impact") == "high" else ("MEDIUM" if concern.get("impact") == "medium" else "LOW")
            lines.append(f"[{impact_label}] **{concern.get('title', 'N/A')}**")
            lines.append(f"> {concern.get('concern', 'N/A')[:100]}...")
            lines.append("")
    else:
        lines.append("*暂无用户关切*")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # 需求辩护摘要
    lines.append("## 需求分析师辩护要点")
    lines.append("")
    if requirement_defense:
        for defense in requirement_defense[:3]:  # 只显示前 3 个
            priority_label = "HIGH" if defense.get("priority") == "high" else ("MEDIUM" if defense.get("priority") == "medium" else "LOW")
            lines.append(f"[{priority_label}] **{defense.get('point', defense.get('question', 'N/A'))[:50]}**")
            lines.append(f"> {defense.get('explanation', 'N/A')[:100]}...")
            lines.append("")
    else:
        lines.append("*暂无需求辩护意见*")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # 共识和分歧点
    lines.append("## 共识与分歧")
    lines.append("")
    lines.append("### 共识点")
    lines.append("")
    lines.append("1. 系统需要遵循行业标准以确保可靠性")
    lines.append("2. 用户体验应该简单易用")
    lines.append("3. 数据安全和隐私保护至关重要")
    lines.append("")
    lines.append("### 待协调的分歧")
    lines.append("")
    lines.append("1. **技术复杂性 vs 使用简洁性**: 专家建议的模块化架构可能增加用户学习成本")
    lines.append("2. **功能完整性 vs 快速上线**: 需求完整性要求与 MVP 策略之间的平衡")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # 下一步（v2）
    lines.append("## 下一步：Step 3 - 全局规则与术语库挖掘")
    lines.append("")
    lines.append("系统将基于 Step 2 的宏观目标与主干产物，生成 Parlant 所需的全局规则与全局术语库：")
    lines.append("")
    lines.append("- **GlossaryAgent**: 提取和定义专业术语体系")
    lines.append("- **GlobalRulesAgent**: 生成精简的全局 Guideline（agent-level）")
    lines.append("")
    
    return "\n".join(lines)


def main():
    """主函数"""
    args = parse_args()

    # 环境变量加载策略：
    # - 传入 --env-file：从文件加载
    # - 未传入：仅从系统环境变量读取（符合密钥不落盘策略）
    if getattr(args, "env_file", None):
        try:
            if Path(args.env_file).exists():
                load_dotenv(args.env_file)
                logger.info(f"已加载环境变量文件：{args.env_file}")
            else:
                logger.warning(f"环境变量文件不存在，将仅使用系统环境变量：{args.env_file}")
        except Exception as e:
            logger.error(f"加载环境变量文件失败：{type(e).__name__}: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()

    # 固化配置模式（fix模式）
    if args.mode == "fix":
        logger.info("Fix Mode On - 使用固化配置")
        if not args.business_desc:
            args.business_desc = """作为一个共荣保险的外呼营销客服，我的主要目标是打电话推销我们的保险，我会确认用户身份，\
            确认用户需求，给用户进行推销，如果用户不愿意继续接听，我会想办法进行挽留，当挽留住用户后，\
            我会开始按照用户需求介绍产品，并解答任何疑问，之后跟进用户下一步动作。其中，一些注意事项，\
            是挽留是最难的，如果挽留不住用户，后面的流程都不回被提及。另外，你需要遵守日本的相关保险行业的要求。\
            开场和结束你需要使用固定话术，同时，你对用户最多只能一次挽留。你还要避免用户投诉，这回造成巨大的风险。       
                 """
        args.output_dir = "./output"
        args.verbose = True
        args.force_rerun = True
        args.max_parallel = 1
        args.start_step = 1
        args.end_step = 7

    # 调试模式下的特殊处理
    if args.debug:
        logger.info("Debug Mode On - 二级SOP只扩展2个节点")
        args.debug = True

    # 验证配置文件
    config_path = Path(args.config)
    if not config_path.exists():
        logger.error(f"配置文件不存在：{config_path}")
        sys.exit(1)
    
    # 验证 Excel 文件（如果提供）
    if hasattr(args, 'excel_file') and args.excel_file:
        excel_path = Path(args.excel_file)
        if not excel_path.exists():
            logger.warning(f"Excel 文件不存在：{excel_path}，将跳过 Step 6")
    
    # 运行系统
    success = asyncio.run(run_system(args))
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
