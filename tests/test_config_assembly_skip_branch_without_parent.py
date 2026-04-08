#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回归测试：分支 SOP（子）如果缺少 parent 关联，必须不生成（不落盘）。
"""

import asyncio
import json
from pathlib import Path

from src.mining_agents.steps.config_assembly import config_assembly_handler


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def test_step5_skips_branch_without_parent(tmp_path: Path):
    output_base = tmp_path / "output"
    step5_dir = output_base / "step7_config_assembly"
    step3_dir = output_base / "step3_global_rules_and_glossary"
    step4_dir = output_base / "step4_user_profile"

    # Step2 主干（父）可用
    step2_backbone = {
        "sop_id": "main_sop_backbone_v2",
        "sop_type": "main",
        "frozen": True,
        "main_sop_nodes": [{"node_id": "node_000", "node_name": "初访待对接"}],
    }

    # Step3 产物（同名，但缺少 parent 字段，且 sop_type 也不对）
    bad_branch = {
        "sop_id": "retention_sop_001",
        "sop_title": "错误的分支 SOP",
        "sop_states": [{"state_id": "state_000", "transitions": [], "is_end_state": True}],
    }
    _write_json(
        step3_dir / "node_node_000" / "process_agent" / "step3_journeys_retention.json",
        {"journeys": [bad_branch]},
    )
    _write_json(step3_dir / "step3_profiles_user.json", {"profiles": []})
    _write_json(step4_dir / "global_rules.json", {"rules": []})
    _write_json(step4_dir / "compatibility_report.json", {"passed": True})

    ctx = {
        "output_dir": str(step5_dir),
        # 触发 _derive_agent_id 的稳定命名：kyoroei_insurance_retention
        "business_desc": "我是日本共荣保险的外呼挽留营销客服（测试：必须跳过无 parent 的分支）",
        "step6_edge_case_sops": [],
        "main_sop_backbone": step2_backbone,
    }
    asyncio.run(config_assembly_handler(context=ctx, orchestrator=None))

    agent_root = output_base / "parlant_agent_config" / "agents" / "kyoroei_insurance_retention" / "02_journeys"
    sop_files = sorted(agent_root.rglob("sop.json"))

    # 只应生成主干 retention/sop.json；坏分支必须被跳过
    assert len(sop_files) == 1
    sop = json.loads(sop_files[0].read_text(encoding="utf-8"))
    assert sop.get("sop_id") == "retention_sop_001"

