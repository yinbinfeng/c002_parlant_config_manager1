#!/usr/bin/env python3
"""
step_extract_canned_obs.py
文件格式: Python 源码

Step 6.5: Canned Response 和 Observation 提取步骤
- 从 Step3 全局 guidelines 和 Step5 局部 guidelines 中提取 canned response 和 observation
- 生成独立的 parlant 格式文件
- 更新原 guideline JSON 中的引用映射

执行顺序：在 Step6（边缘场景）之后、Step7（配置组装）之前执行
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json
import traceback

from json_repair import repair_json

from ..utils.logger import logger


def _ensure_list(x: Any) -> List[Any]:
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]


def _load_json_file(path: Path) -> Tuple[Optional[dict], Optional[str]]:
    """加载JSON文件"""
    try:
        raw = path.read_text(encoding="utf-8")
        return repair_json(raw, return_objects=True), None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def _save_json_file(path: Path, data: dict) -> None:
    """保存JSON文件"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _extract_canned_responses_from_guidelines(
    guidelines_data: dict,
    scope: str = "global",
    prefix: str = "",
) -> Tuple[List[dict], dict]:
    """从guidelines数据中提取canned responses
    
    Args:
        guidelines_data: guidelines JSON数据
        scope: 作用域（global/sop_only）
        prefix: ID前缀
        
    Returns:
        (提取的canned responses列表, 更新后的guidelines数据)
    """
    if not isinstance(guidelines_data, dict):
        return [], guidelines_data
    
    canned_responses = []
    updated_data = dict(guidelines_data)
    
    if scope == "global":
        guidelines_key = "agent_guidelines"
        canned_key = "agent_canned_responses"
    else:
        guidelines_key = "sop_scoped_guidelines"
        canned_key = "sop_canned_responses"
    
    existing_canned = _ensure_list(guidelines_data.get(canned_key, []))
    
    for cr in existing_canned:
        if not isinstance(cr, dict):
            continue
        cr_id = cr.get("canned_response_id", "")
        if cr_id:
            canned_responses.append({
                "canned_response_id": cr_id,
                "content": cr.get("content", ""),
                "language": cr.get("language", "zh-CN"),
                "bind_guideline_ids": cr.get("bind_guideline_ids", []),
            })
    
    guidelines_list = _ensure_list(guidelines_data.get(guidelines_key, []))
    for gl in guidelines_list:
        if not isinstance(gl, dict):
            continue
        bind_cr_ids = gl.get("bind_canned_response_ids", [])
        if not bind_cr_ids:
            continue
        for cr_id in bind_cr_ids:
            if not any(cr.get("canned_response_id") == cr_id for cr in canned_responses):
                canned_responses.append({
                    "canned_response_id": cr_id,
                    "content": "",
                    "language": "zh-CN",
                    "bind_guideline_ids": [gl.get("guideline_id", "")],
                    "extraction_note": "从guideline的bind_canned_response_ids提取，需要补充content",
                })
    
    updated_data[canned_key] = []
    
    return canned_responses, updated_data


def _extract_observations_from_guidelines(
    guidelines_data: dict,
    scope: str = "global",
    prefix: str = "",
) -> Tuple[List[dict], dict]:
    """从guidelines数据中提取observations
    
    Args:
        guidelines_data: guidelines JSON数据
        scope: 作用域（global/sop_only）
        prefix: ID前缀
        
    Returns:
        (提取的observations列表, 更新后的guidelines数据)
    """
    if not isinstance(guidelines_data, dict):
        return [], guidelines_data
    
    observations = []
    updated_data = dict(guidelines_data)
    
    if scope == "global":
        obs_key = "agent_observations"
        guidelines_key = "agent_guidelines"
    else:
        obs_key = "sop_observations"
        guidelines_key = "sop_scoped_guidelines"
    
    existing_obs = _ensure_list(guidelines_data.get(obs_key, []))
    
    for obs in existing_obs:
        if not isinstance(obs, dict):
            continue
        obs_id = obs.get("observation_id", "")
        if obs_id:
            observations.append({
                "observation_id": obs_id,
                "condition": obs.get("condition", ""),
                "remark": obs.get("remark", ""),
            })
    
    guidelines_list = _ensure_list(guidelines_data.get(guidelines_key, []))
    for gl in guidelines_list:
        if not isinstance(gl, dict):
            continue
        dependencies = gl.get("dependencies", [])
        if not dependencies:
            continue
        for dep_id in dependencies:
            if not any(obs.get("observation_id") == dep_id for obs in observations):
                observations.append({
                    "observation_id": dep_id,
                    "condition": "",
                    "remark": f"从guideline {gl.get('guideline_id', '')} 的dependencies提取，需要补充condition",
                    "extraction_note": "从guideline的dependencies提取，需要补充condition",
                })
    
    updated_data[obs_key] = []
    
    return observations, updated_data


def _extract_global_canned_and_observations(
    step3_dir: Path,
    output_dir: Path,
) -> Dict[str, Any]:
    """从Step3全局guidelines中提取canned responses和observations
    
    Args:
        step3_dir: Step3输出目录
        output_dir: 本步骤输出目录
        
    Returns:
        提取结果统计
    """
    logger.info("提取全局 canned responses 和 observations...")
    
    result = {
        "global_canned_count": 0,
        "global_observations_count": 0,
        "files_updated": [],
    }
    
    global_guidelines_file = step3_dir / "agent_guidelines.json"
    if not global_guidelines_file.exists():
        logger.warning(f"Step3全局guidelines文件不存在: {global_guidelines_file}")
        return result
    
    data, err = _load_json_file(global_guidelines_file)
    if err or not isinstance(data, dict):
        logger.error(f"加载Step3全局guidelines失败: {err}")
        return result
    
    agent_id = data.get("agent_id", "agent_001")
    
    canned_responses, updated_data = _extract_canned_responses_from_guidelines(
        data, scope="global", prefix=agent_id
    )
    
    observations, updated_data = _extract_observations_from_guidelines(
        updated_data, scope="global", prefix=agent_id
    )
    
    if canned_responses:
        canned_file = output_dir / "global_canned_responses.json"
        canned_payload = {
            "agent_id": agent_id,
            "remark": "从Step3全局guidelines提取的canned responses",
            "extraction_source": "step3_global_guidelines",
            "extraction_time": datetime.now().isoformat(),
            "agent_canned_responses": canned_responses,
        }
        _save_json_file(canned_file, canned_payload)
        result["global_canned_count"] = len(canned_responses)
        result["files_updated"].append(str(canned_file))
        logger.info(f"提取全局canned responses: {len(canned_responses)} 条 -> {canned_file}")
    
    if observations:
        obs_file = output_dir / "global_observations.json"
        obs_payload = {
            "agent_id": agent_id,
            "remark": "从Step3全局guidelines提取的observations",
            "extraction_source": "step3_global_guidelines",
            "extraction_time": datetime.now().isoformat(),
            "agent_observations": observations,
        }
        _save_json_file(obs_file, obs_payload)
        result["global_observations_count"] = len(observations)
        result["files_updated"].append(str(obs_file))
        logger.info(f"提取全局observations: {len(observations)} 条 -> {obs_file}")
    
    _save_json_file(global_guidelines_file, updated_data)
    result["files_updated"].append(str(global_guidelines_file))
    logger.info(f"更新Step3全局guidelines，移除内嵌的canned responses和observations")
    
    return result


def _extract_local_canned_and_observations(
    step5_dir: Path,
    output_dir: Path,
) -> Dict[str, Any]:
    """从Step5局部guidelines中提取canned responses和observations
    
    Args:
        step5_dir: Step5输出目录
        output_dir: 本步骤输出目录
        
    Returns:
        提取结果统计
    """
    logger.info("提取局部 canned responses 和 observations...")
    
    result = {
        "local_canned_count": 0,
        "local_observations_count": 0,
        "nodes_processed": 0,
        "files_updated": [],
    }
    
    if not step5_dir.exists():
        logger.warning(f"Step5目录不存在: {step5_dir}")
        return result
    
    local_canned_dir = output_dir / "local_canned_responses"
    local_obs_dir = output_dir / "local_observations"
    
    guidelines_files = sorted(step5_dir.rglob("step5_guidelines_*.json"))
    observations_files = sorted(step5_dir.rglob("sop_observations_*.json"))
    
    for gf in guidelines_files:
        node_id = gf.stem.replace("step5_guidelines_", "")
        
        data, err = _load_json_file(gf)
        if err or not isinstance(data, dict):
            logger.warning(f"加载Step5局部guidelines失败: {gf} - {err}")
            continue
        
        if data.get("skipped") is True:
            continue
        
        sop_id = data.get("sop_id", f"branch_{node_id}")
        
        canned_responses, updated_data = _extract_canned_responses_from_guidelines(
            data, scope="sop_only", prefix=sop_id
        )
        
        if canned_responses:
            canned_file = local_canned_dir / f"sop_canned_responses_{node_id}.json"
            canned_payload = {
                "sop_id": sop_id,
                "sop_title": data.get("sop_title", f"分支 {node_id}"),
                "remark": f"从Step5局部guidelines提取的canned responses (节点: {node_id})",
                "extraction_source": "step5_local_guidelines",
                "extraction_time": datetime.now().isoformat(),
                "sop_canned_responses": canned_responses,
            }
            _save_json_file(canned_file, canned_payload)
            result["local_canned_count"] += len(canned_responses)
            result["files_updated"].append(str(canned_file))
            logger.debug(f"提取局部canned responses: {len(canned_responses)} 条 -> {canned_file}")
        
        _save_json_file(gf, updated_data)
        result["files_updated"].append(str(gf))
        result["nodes_processed"] += 1
    
    for of in observations_files:
        node_id = of.stem.replace("sop_observations_", "")
        
        data, err = _load_json_file(of)
        if err or not isinstance(data, dict):
            logger.warning(f"加载Step5 observations失败: {of} - {err}")
            continue
        
        if data.get("skipped") is True:
            continue
        
        sop_id = data.get("sop_id", f"branch_{node_id}")
        observations = _ensure_list(data.get("sop_observations", []))
        
        if observations:
            obs_file = local_obs_dir / f"sop_observations_{node_id}.json"
            obs_payload = {
                "sop_id": sop_id,
                "sop_title": data.get("sop_title", f"分支 {node_id}"),
                "remark": f"从Step5提取的observations (节点: {node_id})",
                "extraction_source": "step5_sop_observations",
                "extraction_time": datetime.now().isoformat(),
                "sop_observations": observations,
            }
            _save_json_file(obs_file, obs_payload)
            result["local_observations_count"] += len(observations)
            result["files_updated"].append(str(obs_file))
            logger.debug(f"提取局部observations: {len(observations)} 条 -> {obs_file}")
        
        updated_data = dict(data)
        updated_data["sop_observations"] = []
        updated_data["extraction_note"] = "observations已提取到独立文件"
        _save_json_file(of, updated_data)
    
    logger.info(
        f"局部提取完成: {result['nodes_processed']} 个节点, "
        f"{result['local_canned_count']} 条canned responses, "
        f"{result['local_observations_count']} 条observations"
    )
    
    return result


def _update_step3_canned_responses_file(
    step3_dir: Path,
    output_dir: Path,
) -> None:
    """更新Step3的agent_canned_responses.json文件
    
    如果Step3已经有agent_canned_responses.json，需要更新它以引用提取后的文件
    """
    step3_canned_file = step3_dir / "agent_canned_responses.json"
    if step3_canned_file.exists():
        data, err = _load_json_file(step3_canned_file)
        if not err and isinstance(data, dict):
            data["extraction_note"] = "此文件将在Step7组装时与提取的canned responses合并"
            _save_json_file(step3_canned_file, data)
            logger.info(f"更新Step3 canned responses文件: {step3_canned_file}")


async def step_extract_canned_obs_handler(context: Dict[str, Any], orchestrator) -> Dict[str, Any]:
    """Step 6.5: Canned Response 和 Observation 提取步骤
    
    从Step3全局guidelines和Step5局部guidelines中提取canned response和observation，
    生成独立的parlant格式文件，并更新原guideline JSON中的引用映射。
    
    Args:
        context: 执行上下文
        orchestrator: Agent编排器
        
    Returns:
        执行结果
    """
    logger.info("Step 6.5: 开始提取 canned responses 和 observations...")
    
    output_base_dir = Path(context.get("output_base_dir", Path(context.get("output_dir", "./output")).parent))
    output_dir = Path(context.get("output_dir", output_base_dir / "step_extract_canned_obs"))
    output_dir.mkdir(parents=True, exist_ok=True)
    
    log_dir = Path(context.get("step_log_dir", output_dir / "logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    
    step_log_file = log_dir / "step_extract_canned_obs.log"
    
    def _append_log(msg: str):
        with open(step_log_file, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] {msg}\n")
    
    _append_log("Step 6.5 started")
    
    try:
        step3_dir = output_base_dir / "step3_global_rules_and_glossary"
        step5_dir = output_base_dir / "step5_branch_sop_parallel"
        
        if not step3_dir.exists():
            raise ValueError(f"Step3输出目录不存在: {step3_dir}")
        
        global_result = _extract_global_canned_and_observations(step3_dir, output_dir)
        
        local_result = {"local_canned_count": 0, "local_observations_count": 0, "nodes_processed": 0, "files_updated": []}
        if step5_dir.exists():
            local_result = _extract_local_canned_and_observations(step5_dir, output_dir)
        
        _update_step3_canned_responses_file(step3_dir, output_dir)
        
        extraction_report = {
            "generated_at": datetime.now().isoformat(),
            "step": "6.5",
            "description": "Canned Response 和 Observation 提取",
            "global": {
                "canned_responses_count": global_result["global_canned_count"],
                "observations_count": global_result["global_observations_count"],
            },
            "local": {
                "canned_responses_count": local_result["local_canned_count"],
                "observations_count": local_result["local_observations_count"],
                "nodes_processed": local_result["nodes_processed"],
            },
            "total": {
                "canned_responses_count": global_result["global_canned_count"] + local_result["local_canned_count"],
                "observations_count": global_result["global_observations_count"] + local_result["local_observations_count"],
            },
            "output_files": global_result["files_updated"] + local_result["files_updated"],
        }
        
        report_file = output_dir / "extraction_report.json"
        _save_json_file(report_file, extraction_report)
        
        _append_log(f"Extraction completed: {extraction_report['total']}")
        logger.info(
            f"Step 6.5 完成: 提取 {extraction_report['total']['canned_responses_count']} 条canned responses, "
            f"{extraction_report['total']['observations_count']} 条observations"
        )
        
        return {
            "extraction_report": extraction_report,
            "output_files": [str(report_file)] + extraction_report["output_files"],
            "metadata": {
                "step": "6.5",
                "global_canned_count": global_result["global_canned_count"],
                "global_observations_count": global_result["global_observations_count"],
                "local_canned_count": local_result["local_canned_count"],
                "local_observations_count": local_result["local_observations_count"],
            },
        }
        
    except Exception as e:
        _append_log(f"Step 6.5 failed: {type(e).__name__}: {e}")
        logger.error(f"Step 6.5 执行失败: {e}")
        traceback.print_exc()
        raise
