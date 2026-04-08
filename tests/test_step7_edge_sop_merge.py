#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证 Step7 组装阶段会合并 Step6 产出的边缘子 SOP。
"""

import json
from pathlib import Path

import pytest

from mining_agents.steps.config_assembly import config_assembly_handler


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


@pytest.mark.asyncio
async def test_config_assembly_merges_step6_edge_sops(tmp_path: Path):
    output_base = tmp_path / "output"
    step7_dir = output_base / "step7_config_assembly"
    step3_dir = output_base / "step3_global_rules_and_glossary"
    step4_dir = output_base / "step4_user_profile"

    # Step3 最小主 SOP 产物
    _write_json(
        step3_dir / "step3_journeys_retention.json",
        {
            "journeys": [
                {
                    "sop_id": "retention_main_001",
                    "sop_title": "主流程",
                    "sop_states": [
                        {"state_id": "state_000", "transitions": [], "is_end_state": True}
                    ],
                }
            ]
        },
    )
    _write_json(step3_dir / "step3_profiles_user.json", {"profiles": []})

    # Step4 最小规则产物
    _write_json(step4_dir / "step4_global_rules.json", {"rules": []})
    _write_json(step4_dir / "step4_compatibility_report.json", {"passed": True})

    # Step6 子 SOP 输入（通过 context 传递）
    edge_sops = [
        {
            "sop_id": "edge_node_000_user_hesitation_001",
            "sop_title": "边缘场景 SOP",
            "sop_states": [
                {"state_id": "edge_state_000", "transitions": [], "is_end_state": True}
            ],
        }
    ]

    context = {
        "output_dir": str(step7_dir),
        "output_base_dir": str(output_base),
        "business_desc": "日本共荣保险外呼挽留",
        "step6_edge_case_sops": edge_sops,
    }

    await config_assembly_handler(context=context, orchestrator=None)

    agent_root = output_base / "parlant_agent_config" / "agents" / "kyoroei_insurance_retention"
    edge_sop_file = agent_root / "02_journeys" / "edge_node_000_user_hesitation_001" / "sop.json"

    assert edge_sop_file.exists(), "Step6 的边缘子 SOP 未被合并到最终产物"
