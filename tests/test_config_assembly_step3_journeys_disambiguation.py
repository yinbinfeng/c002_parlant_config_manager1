#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回归测试：Step5 配置组装阶段必须遵循“先父后子”的 3 层 SOP 规范：
- 先生成主干 SOP（父）：02_journeys/retention/sop.json（state_id 使用 node_id）
- 分支 SOP（子）必须带 sop_type=branch 且包含合法 parent_sop_id/parent_state_id
- 缺少 parent 的分支产物必须被跳过（不生成）
"""

import json
import asyncio
from pathlib import Path

from src.mining_agents.steps.config_assembly import config_assembly_handler


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def test_step5_does_not_overwrite_step3_journeys_between_nodes(tmp_path: Path):
    output_base = tmp_path / "output"
    step7_dir = output_base / "step7_config_assembly"

    step3_dir = output_base / "step3_global_rules_and_glossary"
    step4_dir = output_base / "step4_user_profile"

    # Step2 主干（父）来源：Step5 会据此生成主干 SOP，并要求分支必须挂载到 parent_state_id=node_id
    step2_backbone = {
        "sop_id": "main_sop_backbone_v2",
        "sop_type": "main",
        "frozen": True,
        "main_sop_nodes": [
            {"node_id": "node_000", "node_name": "初访待对接"},
            {"node_id": "node_001", "node_name": "需求澄清中"},
        ],
    }

    # 两个 node 输出同名文件：step3_journeys_retention.json
    # 这两个文件本质上是“分支 SOP（子）”，必须包含 parent 信息。
    node_000_branch = {
        "sop_id": "retention__branch_node_000_sop_001",
        "sop_type": "branch",
        "parent_sop_id": "retention_sop_001",
        "parent_state_id": "node_000",
        "sop_title": "node_000 分支 SOP",
        "sop_states": [{"state_id": "branch_state_000", "transitions": [], "is_end_state": True, "return_to_parent": True}],
    }
    node_001_branch = {
        "sop_id": "retention__branch_node_001_sop_001",
        "sop_type": "branch",
        "parent_sop_id": "retention_sop_001",
        "parent_state_id": "node_001",
        "sop_title": "node_001 分支 SOP",
        "sop_states": [{"state_id": "branch_state_000", "transitions": [], "is_end_state": True, "return_to_parent": True}],
    }

    _write_json(
        step3_dir / "node_node_000" / "process_agent" / "step3_journeys_retention.json",
        {"journeys": [node_000_branch]},
    )
    _write_json(
        step3_dir / "node_node_001" / "process_agent" / "step3_journeys_retention.json",
        {"journeys": [node_001_branch]},
    )

    # Step3 profiles（只需要确保必备文件存在）
    _write_json(step3_dir / "step3_profiles_user.json", {"profiles": []})

    # Step4 全局规则（只需要确保 agent_guidelines.json 存在）
    _write_json(step4_dir / "step4_global_rules.json", {"rules": []})
    _write_json(step4_dir / "step4_compatibility_report.json", {"passed": True})

    context = {
        "output_dir": str(step7_dir),
        "business_desc": "我是日本共荣保险的外呼挽留营销客服（测试用）",
        "step6_edge_case_sops": [],
        "main_sop_backbone": step2_backbone,
    }

    asyncio.run(config_assembly_handler(context=context, orchestrator=None))

    agent_root = (
        output_base
        / "parlant_agent_config"
        / "agents"
        / "kyoroei_insurance_retention"
    )

    # 期望：1 个主干 + 2 个分支
    sop_files = sorted((agent_root / "02_journeys").rglob("sop.json"))
    assert len(sop_files) == 3, f"期望 1 主干 + 2 分支 sop.json，但实际为 {len(sop_files)}"

    sop_ids = set()
    for f in sop_files:
        data = json.loads(f.read_text(encoding="utf-8"))
        sop_ids.add(data.get("sop_id"))

    assert "retention_sop_001" in sop_ids  # 主干 sop_id
    assert node_000_branch["sop_id"] in sop_ids
    assert node_001_branch["sop_id"] in sop_ids

