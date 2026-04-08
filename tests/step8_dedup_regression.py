#!/usr/bin/env python3
"""
step8_dedup_regression.py
文件格式: Python 源码

一键回归脚本：
1) 向 agent_guidelines.json 注入重复规则
2) 运行 Step9 校验
3) 检查报告是否出现 duplicate 告警
4) 自动回滚测试注入
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: Dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _build_duplicate_rule_from_first(guidelines: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not guidelines:
        raise RuntimeError("agent_guidelines is empty, cannot build duplicate test case")
    first = dict(guidelines[0])
    # 仅调整少量字段，保留 guideline_id + condition + action 不变，触发双重重复检测
    first["priority"] = int(first.get("priority", 1)) + 1
    return first


def run() -> int:
    parser = argparse.ArgumentParser(description="Step8 guideline 去重回归脚本")
    parser.add_argument(
        "--python",
        default=r"C:\Users\40166\.conda\envs\python3.11\python.exe",
        help="用于运行主流程的 python 路径",
    )
    parser.add_argument(
        "--root",
        default=r"E:\cursorworkspace\c002_parlant_config_manager1",
        help="项目根目录",
    )
    parser.add_argument(
        "--business-desc",
        default="我是日本共荣保险的外呼营销客服，目标是在用户有挂断或拒绝倾向时进行一次合规挽留，挽留成功后继续介绍保险产品并推进后续转化，同时严格遵守日本保险营销合规要求，避免投诉与误导。",
        help="回归时传入的业务描述",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    target = (
        root
        / "output"
        / "parlant_agent_config"
        / "agents"
        / "kyoroei_insurance_retention"
        / "01_agent_rules"
        / "agent_guidelines.json"
    )
    report = root / "output" / "step8_validation" / "step9_validation_report.md"

    if not target.exists():
        raise FileNotFoundError(f"target file not found: {target}")

    original_text = target.read_text(encoding="utf-8")
    try:
        data = _load_json(target)
        guidelines = data.get("agent_guidelines") or []
        if not isinstance(guidelines, list):
            raise RuntimeError("agent_guidelines is not a list")

        duplicate = _build_duplicate_rule_from_first(guidelines)
        guidelines.append(duplicate)
        data["agent_guidelines"] = guidelines
        _save_json(target, data)
        print(f"[inject] duplicate guideline appended -> {target}")

        cmd = [
            args.python,
            "egs/v0.1.0_minging_agents/main.py",
            "--mode",
            "mock",
            "--max-parallel",
            "1",
            "--skip-clarification",
            "--force-rerun",
            "--start-step",
            "9",
            "--end-step",
            "9",
            "--business-desc",
            args.business_desc,
        ]
        proc = subprocess.run(cmd, cwd=str(root), check=False)
        if proc.returncode != 0:
            print(f"[run] step9 failed, returncode={proc.returncode}")
            return proc.returncode

        if not report.exists():
            print(f"[check] report missing: {report}")
            return 2

        report_text = report.read_text(encoding="utf-8")
        has_dup_id = "duplicate guideline_id" in report_text
        has_dup_sig = "duplicate condition+action" in report_text

        print(f"[check] duplicate guideline_id found: {has_dup_id}")
        print(f"[check] duplicate condition+action found: {has_dup_sig}")
        if has_dup_id and has_dup_sig:
            print("[result] PASS: dedup validator triggered correctly")
            return 0
        print("[result] FAIL: expected dedup issues were not found")
        return 3
    finally:
        target.write_text(original_text, encoding="utf-8")
        print(f"[restore] original file restored -> {target}")


if __name__ == "__main__":
    raise SystemExit(run())
