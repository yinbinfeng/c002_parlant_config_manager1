#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回归测试：即使 step3_journeys_* 不是 branch（旧产物），Step5 也必须基于 Step2 主干生成二级分支 SOP。
"""

import asyncio
import json
from pathlib import Path

from src.mining_agents.steps.config_assembly import config_assembly_handler


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def test_step5_generates_branch_sops_from_step2_backbone(tmp_path: Path):
    output_base = tmp_path / "output"
    step5_dir = output_base / "step7_config_assembly"
    step3_dir = output_base / "step3_global_rules_and_glossary"
    step4_dir = output_base / "step4_user_profile"

    backbone = {
        "sop_id": "main_sop_backbone_v2",
        "sop_type": "main",
        "frozen": True,
        "main_sop_nodes": [
            {"node_id": "node_000", "node_name": "初访待对接"},
            {"node_id": "node_001", "node_name": "需求澄清中"},
        ],
    }

    # 上游 step3 journey 是“主流程样式”（非 branch）
    _write_json(
        step3_dir / "node_node_000" / "process_agent" / "step3_journeys_retention.json",
        {"journeys": {"sop_id": "retention_sop_001", "sop_states": [{"state_id": "state_000", "is_end_state": True}]}},
    )
    _write_json(step3_dir / "step3_profiles_user.json", {"profiles": []})
    _write_json(step4_dir / "global_rules.json", {"rules": []})
    _write_json(step4_dir / "compatibility_report.json", {"passed": True})

    ctx = {
        "output_dir": str(step5_dir),
        "business_desc": "我是日本共荣保险的外呼挽留营销客服（测试：Step2 自动生成分支）",
        "main_sop_backbone": backbone,
        "step6_edge_case_sops": [],
    }
    asyncio.run(config_assembly_handler(context=ctx, orchestrator=None))

    journeys_root = output_base / "parlant_agent_config" / "agents" / "kyoroei_insurance_retention" / "02_journeys"
    # 必须有父 retention/sop.json + 2 个 branch sop.json
    sop_files = sorted(journeys_root.rglob("sop.json"))
    assert len(sop_files) == 3

