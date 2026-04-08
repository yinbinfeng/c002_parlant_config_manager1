#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试运行器 - 统一管理测试执行和报告生成
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime
import json


class TestRunner:
    """测试运行器"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.tests_dir = project_root / "tests"
        self.results_dir = project_root / "test_results"
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def run_single_agent_tests(self, verbose=False):
        """运行单个 Agent 测试"""
        print("\n" + "="*80)
        print("运行单个 Agent 测试")
        print("="*80)
        
        test_file = self.tests_dir / "test_single_agents.py"
        return self._run_pytest(test_file, verbose)
    
    def run_end_to_end_tests(self, verbose=False):
        """运行端到端测试"""
        print("\n" + "="*80)
        print("运行端到端集成测试")
        print("="*80)
        
        test_file = self.tests_dir / "test_end_to_end.py"
        return self._run_pytest(test_file, verbose)
    
    def run_all_tests(self, verbose=False):
        """运行所有测试"""
        print("\n" + "="*80)
        print("运行完整测试套件")
        print("="*80)
        
        results = {
            "single_agents": self.run_single_agent_tests(verbose),
            "end_to_end": self.run_end_to_end_tests(verbose),
        }
        
        return results
    
    def _run_pytest(self, test_file: Path, verbose=False):
        """运行 pytest"""
        if not test_file.exists():
            print(f"❌ 测试文件不存在：{test_file}")
            return {"status": "failed", "error": "File not found"}
        
        # 构建 pytest 命令
        cmd = [
            sys.executable, "-m", "pytest",
            str(test_file),
            "-v",
            "--tb=short",
            f"--resultlog={self.results_dir / 'pytest_result.log'}",
        ]
        
        if verbose:
            cmd.append("-s")  # 显示输出
        
        # 添加 JSON 报告
        json_report_file = self.results_dir / f"{test_file.stem}_report.json"
        cmd.extend([
            "--json-report",
            f"--json-report-file={json_report_file}",
        ])
        
        print(f"\n执行命令：{' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=False,
                encoding='utf-8',
                timeout=300  # 5 分钟超时
            )
            
            return {
                "status": "passed" if result.returncode == 0 else "failed",
                "returncode": result.returncode,
                "test_file": str(test_file),
            }
            
        except subprocess.TimeoutExpired:
            print(f"❌ 测试超时 (5 分钟)")
            return {"status": "timeout", "test_file": str(test_file)}
        except Exception as e:
            print(f"❌ 测试执行失败：{e}")
            return {"status": "error", "error": str(e), "test_file": str(test_file)}
    
    def generate_summary_report(self, results: dict):
        """生成汇总报告"""
        report = {
            "test_execution_summary": {
                "timestamp": datetime.now().isoformat(),
                "total_tests": len(results),
                "passed": sum(1 for r in results.values() if r.get("status") == "passed"),
                "failed": sum(1 for r in results.values() if r.get("status") in ["failed", "error"]),
            },
            "details": results
        }
        
        report_file = self.results_dir / "execution_summary.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 生成文本报告
        text_report = self._generate_text_report(report)
        text_report_file = self.results_dir / "execution_summary.txt"
        with open(text_report_file, 'w', encoding='utf-8') as f:
            f.write(text_report)
        
        print(f"\n📄 测试报告已生成:")
        print(f"  - JSON: {report_file}")
        print(f"  - Text: {text_report_file}")
        
        return report
    
    def _generate_text_report(self, report: dict) -> str:
        """生成文本格式报告"""
        lines = []
        lines.append("="*80)
        lines.append("测试执行汇总报告")
        lines.append(f"执行时间：{report['test_execution_summary']['timestamp']}")
        lines.append("="*80)
        lines.append("")
        
        summary = report["test_execution_summary"]
        lines.append(f"总测试数：{summary['total_tests']}")
        lines.append(f"通过：{summary['passed']}")
        lines.append(f"失败：{summary['failed']}")
        lines.append("")
        
        lines.append("详细结果:")
        lines.append("-"*80)
        
        for test_name, result in report["details"].items():
            status_icon = "✅" if result.get("status") == "passed" else "❌"
            lines.append(f"{status_icon} {test_name}: {result.get('status', 'unknown')}")
        
        lines.append("")
        lines.append("="*80)
        
        if summary["failed"] == 0:
            lines.append("🎉 所有测试通过！")
        else:
            lines.append(f"⚠️  有 {summary['failed']} 个测试失败")
        
        return "\n".join(lines)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="运行测试套件")
    parser.add_argument(
        "--single",
        action="store_true",
        help="只运行单个 Agent 测试"
    )
    parser.add_argument(
        "--e2e",
        action="store_true",
        help="只运行端到端测试"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="运行所有测试（默认）"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示详细输出"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="结果输出目录"
    )
    
    args = parser.parse_args()
    
    # 确定项目根目录
    project_root = Path(__file__).parent.parent.resolve()
    
    # 创建运行器
    runner = TestRunner(project_root)
    
    if args.output_dir:
        runner.results_dir = Path(args.output_dir)
        runner.results_dir.mkdir(parents=True, exist_ok=True)
    
    # 执行测试
    if args.single:
        results = runner.run_single_agent_tests(args.verbose)
    elif args.e2e:
        results = runner.run_end_to_end_tests(args.verbose)
    else:
        results = runner.run_all_tests(args.verbose)
    
    # 生成报告
    if isinstance(results, dict):
        runner.generate_summary_report(results)
    
    # 返回退出码
    if isinstance(results, dict):
        all_passed = all(r.get("status") == "passed" for r in results.values())
        sys.exit(0 if all_passed else 1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
