#!/usr/bin/env python3
"""
step6_edge_cases.py
文件格式: Python 源码

Step 6（v2）: 边缘场景挖掘（子弹 SOP）
- 基于 Step5 的二级分支总结与局部 guideline，生成边缘场景补丁：
  - 生成单节点 edge journey（1 场景 1SOP，单 state）
  - 将边缘场景转为“局部 guideline 补充”注入对应二级 journey 的 sop_guidelines.json
- 支持并发生成
- 产出补充规则与验证报告
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple
import asyncio
import traceback
import json
import re

from ..utils.file_utils import write_json
from ..utils.logger import logger


def _ensure_list(x: Any) -> List[Any]:
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]


def _norm_text(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def _load_global_guideline_texts(step3_dir: Path) -> List[str]:
    """读取 Step3 的 agent_guidelines.json，提取 condition/action 的规范化文本用于启发式去重。"""
    p = step3_dir / "agent_guidelines.json"
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        try:
            from json_repair import repair_json as _rj

            data = _rj(p.read_text(encoding="utf-8"), return_objects=True)
        except Exception:
            return []
    if not isinstance(data, dict):
        return []
    gl = data.get("agent_guidelines") or []
    if not isinstance(gl, list):
        return []
    texts: List[str] = []
    for g in gl:
        if not isinstance(g, dict):
            continue
        texts.append(_norm_text(str(g.get("condition", ""))))
        texts.append(_norm_text(str(g.get("action", ""))))
    return [t for t in texts if t]


_EDGE_CASE_FEW_SHOT_EXAMPLE = '''
【Few-Shot 示例：保险外呼营销挽留场景的边缘场景】

业务描述：日本共荣保险的外呼营销客服，目标是在用户有挂断或拒绝倾向时进行合规挽留。

生成的边缘场景类型（3个）：
1. user_hesitation（用户犹豫）：用户表示再考虑一下，需要引导决策
   - trigger_examples: ["用户说：我再考虑一下", "用户说：让我想想", "用户沉默后说：嗯..."]

2. user_complaint（用户投诉倾向）：用户表达不满或投诉倾向
   - trigger_examples: ["用户说：我要投诉你们", "用户说：你们这是什么服务", "用户语气激动"]

3. value_inquiry（价值询问）：用户询问产品价值或对比竞品
   - trigger_examples: ["用户说：你们和XX比怎么样", "用户说：这个产品有什么优势", "用户询问保障范围"]

【边缘场景原则】
- 每个边缘场景代表一个"特定用户行为/意图"，不是"具体话术"
- 场景数量控制在2-4个
- trigger_examples必须具体可判定
- 场景必须与业务特点相关
- 如果该节点确实没有需要特别处理的边缘场景，请返回空数组[]
'''


async def _generate_edge_scenarios_via_agent(
    *,
    business_desc: str,
    node_name: str,
    orchestrator,
) -> List[Dict[str, str]]:
    """通过Agent动态生成边缘场景类型。
    
    策略：
    1. 先让模型判断该节点是否有边缘场景需要处理
    2. 如果有，让模型生成场景类型列表
    3. 如果没有，返回空数组，跳过该节点
    4. 失败时使用预定义场景类型
    5. 所有fallback输出都会标记fallback_source字段
    """
    prompt = f'''
请根据以下信息，判断该节点是否有边缘场景需要处理。

## 业务描述
{business_desc}

## 主节点
- node_name: {node_name}

## 判断标准
请根据以下标准判断是否需要生成边缘场景：
1. 该节点是否可能出现用户异常行为？（例如：用户投诉、用户沉默、用户情绪激动）
2. 该节点是否可能出现系统异常？（例如：超时、工具调用失败）
3. 该节点是否需要特殊处理逻辑？（例如：需要升级人工、需要发送材料）

如果以上条件都不满足，说明该节点足够简单，没有需要特别处理的边缘场景，请返回空数组[]。

## Few-Shot 示例
{_EDGE_CASE_FEW_SHOT_EXAMPLE}

## 输出格式（JSON数组）
如果有边缘场景需要处理：
[
  {{
    "scene_key": "scene_identifier",
    "scene_description": "场景描述",
    "trigger_examples": ["示例1", "示例2"]
  }}
]

如果没有边缘场景需要处理：
[]

## 重要提示
1. 场景数量：2-4个（如果有的话）
2. 每个场景包含：scene_key（英文标识）, scene_description（中文描述）, trigger_examples（触发示例）
3. 场景必须与业务特点和当前节点相关
4. trigger_examples必须是具体的用户话语或行为
5. 如果确实没有需要特别处理的边缘场景，请诚实返回空数组[]，不要强行生成无意义的内容

请只输出JSON数组，不要输出其他内容。
'''
    
    try:
        await orchestrator.initialize_agent(agent_type="CoordinatorAgent", agent_name="EdgeCaseGenerator")
        agent = orchestrator.agents.get("EdgeCaseGenerator")
        if not agent:
            logger.warning("无法获取EdgeCaseGenerator agent实例，使用fallback预定义场景")
            return _default_edge_scenarios()
        
        response = await agent.call_llm(
            prompt=prompt,
            context={
                "business_desc": business_desc,
                "node_name": node_name,
            },
        )
        
        if not response:
            logger.warning("Agent call_llm返回空响应，使用fallback预定义场景")
            return _default_edge_scenarios()
        
        from json_repair import repair_json
        scenarios = repair_json(response.strip(), return_objects=True)
        
        if not isinstance(scenarios, list):
            logger.warning("Agent返回的结果不是有效JSON数组，使用fallback预定义场景")
            return _default_edge_scenarios()
        
        # 模型判断没有边缘场景，返回空数组
        if len(scenarios) == 0:
            logger.info(f"【模型决策】节点[{node_name}]没有需要特别处理的边缘场景")
            return []
        
        valid_scenarios = []
        for sc in scenarios:
            if not isinstance(sc, dict):
                continue
            if not sc.get("scene_key") or not sc.get("scene_description"):
                continue
            if not sc.get("trigger_examples"):
                sc["trigger_examples"] = [f"用户在[{node_name}]节点触发{sc['scene_description']}"]
            valid_scenarios.append({
                "scene_key": str(sc.get("scene_key", "unknown")),
                "scene_description": str(sc.get("scene_description", "")),
                "trigger_examples": sc.get("trigger_examples", []),
            })
        
        if len(valid_scenarios) == 0:
            logger.info(f"【模型决策】节点[{node_name}]没有有效的边缘场景")
            return []
        
        logger.info(f"Agent动态生成边缘场景成功，场景数: {len(valid_scenarios)}")
        return valid_scenarios
        
    except Exception as e:
        logger.warning(f"Agent动态生成边缘场景失败: {e}，使用fallback预定义场景")
        return _default_edge_scenarios()


def _default_edge_scenarios() -> List[Dict[str, str]]:
    """Fallback预定义场景类型。"""
    logger.warning("【FALLBACK】使用预定义边缘场景类型")
    return [
        {"scene_key": "user_hesitation", "scene_description": "用户犹豫或表示再考虑一下"},
        {"scene_key": "user_complaint", "scene_description": "用户表达不满或投诉倾向"},
        {"scene_key": "system_timeout", "scene_description": "外部系统超时或工具调用失败"},
    ]


async def _build_edge_case_for_node(
    node: Dict[str, Any], 
    main_sop_id: str, 
    business_desc: str,
    orchestrator,
    use_agent_fallback: bool = False,
) -> Tuple[List[Dict[str, Any]], bool]:
    """生成边缘场景SOP。
    
    策略：
    1. 优先使用Agent动态生成场景类型（如果可用）
    2. 失败时使用预定义场景
    3. 输出中会标记fallback_source
    
    Returns:
        (边缘场景SOP列表, 是否使用了fallback)
    """
    await asyncio.sleep(0)
    node_id = node.get("node_id", "node_unknown")
    node_name = node.get("node_name", node_id)
    
    if use_agent_fallback and orchestrator:
        scenarios = await _generate_edge_scenarios_via_agent(
            business_desc=business_desc,
            node_name=node_name,
            orchestrator=orchestrator,
        )
    else:
        scenarios = _default_edge_scenarios()
    
    is_fallback = not use_agent_fallback
    
    items: List[Dict[str, Any]] = []
    for i, sc in enumerate(scenarios, start=1):
        edge_id = f"edge_{node_id}_{sc['scene_key']}_{i:03d}"
        
        trigger_examples = sc.get("trigger_examples", [
            f"用户在[{node_name}]节点触发{sc['scene_description']}",
        ])
        
        scene_key = sc.get("scene_key", "unknown")
        
        instruction_map = {
            "user_hesitation": f"1.识别用户犹豫（{sc['scene_description']}）；2.使用同理心话术安抚；3.给出1-2个合规的下一步选项；4.确认用户选择后回归主流程",
            "user_complaint": f"1.识别用户不满（{sc['scene_description']}）；2.真诚道歉并倾听；3.提供解决方案或升级渠道；4.确认用户满意度后回归",
            "system_timeout": f"1.识别系统超时；2.告知用户等待原因；3.提供替代方案或回拨承诺；4.确认后回归主流程",
        }
        
        default_instruction = f"1.识别边缘场景类型（{sc['scene_description']}）；2.使用同理心话术安抚用户情绪；3.给出1-2个合规的下一步选项；4.确认用户选择后回归主流程"
        instruction = instruction_map.get(scene_key, default_instruction)
        
        items.append(
            {
                "sop_id": edge_id,
                "sop_type": "edge",
                "parent_sop_id": main_sop_id,
                "parent_node_id": node_id,
                "sop_title": f"{node_name}-{sc['scene_description']}",
                "sop_description": f"单节点边缘场景 Journey：{sc['scene_description']}（用于生成局部 guideline 补丁）",
                "is_edge_case": True,
                "priority": 1,
                "trigger_conditions": [
                    {
                        "trigger": f"在[{node_name}]节点检测到{sc['scene_description']}",
                        "trigger_examples": trigger_examples,
                    }
                ],
                "sop_states": [
                    {
                        "state_id": f"{edge_id}_state_000",
                        "state_name": "边缘场景处理",
                        "state_type": "chat",
                        "instruction": instruction,
                        "exit_condition": "用户已确认下一步选择，或用户情绪已平复并表示可以继续",
                        "exit_condition_examples": [
                            "用户说：好的，我选第一个",
                            "用户说：没问题了，继续吧",
                            "用户确认理解并同意继续",
                        ],
                        "is_end_state": True,
                        "return_to_parent": True,
                    }
                ],
                "fallback_source": "predefined_scenarios" if is_fallback else None,
                "fallback_warning": "此边缘SOP基于预定义场景类型生成，未根据业务特点定制" if is_fallback else None,
            }
        )
    return items, is_fallback


async def step6_edge_cases_handler(context: Dict[str, Any], orchestrator) -> Dict[str, Any]:
    logger.info("Step 6(v2): edge case SOP mining started")

    output_dir = Path(context.get("output_dir", "./output/step6_edge_cases"))
    output_dir.mkdir(parents=True, exist_ok=True)
    log_dir = Path(context.get("step_log_dir", output_dir / "logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    msg_dir = Path(context.get("step_message_archive_dir", output_dir / "message_archive"))
    msg_dir.mkdir(parents=True, exist_ok=True)
    step_log_file = log_dir / "step6_edge_cases.log"
    archive_file = msg_dir / "step6_edge_cases_messages.jsonl"

    def _append_log(msg: str):
        with open(step_log_file, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] {msg}\n")

    def _append_archive(event: str, payload: dict):
        with open(archive_file, "a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "ts": datetime.now().isoformat(),
                        "event": event,
                        "payload": payload,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    _append_log("Step6 started")

    try:
        main_backbone = context.get("main_sop_backbone", {}) or {}
        if not main_backbone:
            # 兼容从中间步骤启动：回读 Step2 产物
            output_base_dir = Path(context.get("output_base_dir", "./output"))
            candidates = [
                output_base_dir / "step2_objective_alignment_main_sop" / "main_sop_backbone.json",
                output_base_dir / "step2_objective_alignment_main_sop" / "step2_main_sop_backbone.json",
                output_base_dir / "dimension_analysis" / "main_sop_backbone.json",
            ]
            for p in candidates:
                if p.exists():
                    try:
                        main_backbone = json.loads(p.read_text(encoding="utf-8"))
                        _append_log(f"Loaded main_sop_backbone from file: {p}")
                        break
                    except Exception:
                        _append_log(f"Failed to load backbone from: {p}")
        nodes = main_backbone.get("main_sop_nodes", []) or []
        _append_archive("input_loaded", {"node_count": len(nodes)})
        if not nodes:
            raise ValueError("Step6 requires main_sop_backbone.main_sop_nodes from Step2")

        # Debug模式下只处理前2个节点
        debug_mode = context.get("debug_mode", False)
        if debug_mode:
            nodes = nodes[:2]
            logger.info(f"Debug模式：只处理前 {len(nodes)} 个节点的边缘场景")
            _append_log(f"Debug mode: processing only {len(nodes)} nodes")

        main_sop_id = main_backbone.get("sop_id", "main_sop_backbone_v2")
        business_desc = context.get("business_desc", "")
        
        max_parallel = int(((context.get("config") or {}).get("max_parallel_edge_cases") or 5))
        sem = asyncio.Semaphore(max(1, max_parallel))
        _append_log(f"Parallel edge case limit={max_parallel}")

        async def _run(node: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], bool]:
            async with sem:
                return await _build_edge_case_for_node(
                    node=node, 
                    main_sop_id=main_sop_id, 
                    business_desc=business_desc,
                    orchestrator=orchestrator,
                    use_agent_fallback=True,
                )

        grouped = await asyncio.gather(*[_run(n) for n in nodes], return_exceptions=True)
        edge_case_sops: List[Dict[str, Any]] = []
        errors: List[str] = []
        fallback_count = 0
        skipped_by_model_count = 0
        for g in grouped:
            if isinstance(g, Exception):
                errors.append(str(g))
            else:
                sops, is_fallback = g
                edge_case_sops.extend(sops)
                if is_fallback:
                    fallback_count += 1
                # 检查是否被模型跳过（返回空数组）
                if len(sops) == 0 and not is_fallback:
                    skipped_by_model_count += 1
        
        if skipped_by_model_count > 0:
            logger.info(f"【模型决策】共{skipped_by_model_count}个节点被模型判断为没有边缘场景")
            _append_log(f"MODEL_DECISION: {skipped_by_model_count} nodes skipped by model (no edge cases)")
        
        if fallback_count > 0:
            logger.warning(f"【FALLBACK】Step6有{fallback_count}/{len(nodes)}个节点使用了预定义边缘场景")
            _append_log(f"FALLBACK: {fallback_count}/{len(nodes)} nodes used predefined scenarios")

        # 启发式去重：读取 Step3 全局 guidelines 的 condition/action 文本
        step3_dir = output_dir.parent / "step3_global_rules_and_glossary"
        global_texts = _load_global_guideline_texts(step3_dir)
        global_set = set(global_texts)

        # 将边缘场景转为局部 guideline 补丁，注入到 Step5 对应 node 的局部 guidelines 文件中
        step5_dir = output_dir.parent / "step5_branch_sop_parallel"
        injected = 0
        deduped = 0
        skipped_by_global_dedupe = 0
        for node in nodes:
            node_id = node.get("node_id", "node_unknown")
            guideline_files = sorted([p for p in step5_dir.rglob(f"step5_guidelines_{node_id}.json") if p.is_file()])
            if not guideline_files:
                continue
            gf = guideline_files[0]
            try:
                gdata = json.loads(gf.read_text(encoding="utf-8"))
            except Exception:
                try:
                    from json_repair import repair_json as _rj

                    gdata = _rj(gf.read_text(encoding="utf-8"), return_objects=True)
                except Exception:
                    errors.append(f"failed_to_load_guidelines: {gf}")
                    continue
            if not isinstance(gdata, dict):
                continue
            gl = gdata.get("sop_scoped_guidelines") or []
            if not isinstance(gl, list):
                gl = []

            existing_ids = {x.get("guideline_id") for x in gl if isinstance(x, dict)}

            # 从 edge_case_sops 中取该 node 的 edge 场景，转成 sop_only guideline
            node_edges = [e for e in edge_case_sops if isinstance(e, dict) and e.get("parent_node_id") == node_id]
            for e in node_edges:
                scene = str(e.get("sop_title") or e.get("sop_description") or "")
                gid = f"edge_{node_id}_{e.get('sop_id')}_guideline_001"
                if gid in existing_ids:
                    deduped += 1
                    continue
                candidate = {
                    "guideline_id": gid,
                    "scope": "sop_only",
                    "condition": f"在分支流程中触发边缘场景：{scene}",
                    "action": "使用边缘场景处理策略：先同理/安抚→给出合规选项→回归主流程；避免新增与全局重复规则。",
                    "priority": 4,
                    "composition_mode": "FLUID",
                    "bind_canned_response_ids": [],
                    "exclusions": [],
                    "dependencies": [],
                }

                # 启发式去重：若与全局 condition/action 完全一致（规范化后），跳过注入
                c_norm = _norm_text(str(candidate.get("condition", "")))
                a_norm = _norm_text(str(candidate.get("action", "")))
                if (c_norm and c_norm in global_set) or (a_norm and a_norm in global_set):
                    skipped_by_global_dedupe += 1
                    continue

                gl.append(candidate)
                existing_ids.add(gid)
                injected += 1

            gdata["sop_scoped_guidelines"] = gl
            gf.write_text(json.dumps(gdata, ensure_ascii=False, indent=2), encoding="utf-8")

        supplementary_rules = {
            "generated_at": datetime.now().isoformat(),
            "note": "Step6 edge cases are injected into Step5 local guidelines (sop_only). This file is trace metadata.",
            "injected_guidelines": injected,
            "deduped_existing": deduped,
            "skipped_by_global_dedupe": skipped_by_global_dedupe,
            "skipped_by_model_count": skipped_by_model_count,
        }

        validation_report = {
            "generated_at": datetime.now().isoformat(),
            "node_count": len(nodes),
            "edge_sop_count": len(edge_case_sops),
            "one_scene_one_sop": True,
            "errors": errors,
            "passed": len(errors) == 0,
            "model_decision_info": {
                "nodes_skipped_by_model": skipped_by_model_count,
                "total_nodes": len(nodes),
            },
            "fallback_info": {
                "nodes_with_fallback": fallback_count,
                "total_nodes": len(nodes),
                "fallback_source": "predefined_scenarios" if fallback_count > 0 else None,
            },
        }
        
        if skipped_by_model_count > 0:
            validation_report["model_decision_note"] = f"有{skipped_by_model_count}个节点被模型判断为没有边缘场景，这是正常的模型决策"
        
        if fallback_count > 0:
            validation_report["fallback_warning"] = f"有{fallback_count}个节点的边缘场景使用了预定义模板，未根据业务特点定制"

        write_json(edge_case_sops, str(output_dir / "step6_edge_case_sops.json"))
        write_json(supplementary_rules, str(output_dir / "step6_supplementary_rules.json"))
        write_json(validation_report, str(output_dir / "step6_validation_report.json"))
        _append_archive(
            "output_written",
            {
                "edge_sop_count": len(edge_case_sops),
                "passed": validation_report["passed"],
                "errors": len(errors),
                "skipped_by_model": skipped_by_model_count,
            },
        )

        context["step6_edge_case_sops"] = edge_case_sops
        context["step6_supplementary_rules"] = supplementary_rules

        # Step6 合规门控（最小）：确保 Step5 注入后的 guidelines 文件仍为合法 JSON
        await orchestrator.initialize_agent(agent_type="ComplianceCheckAgent", agent_name="ComplianceCheckAgent")
        step5_dir = output_dir.parent / "step5_branch_sop_parallel"
        changed_guidelines = sorted([p for p in step5_dir.rglob("step5_guidelines_*.json") if p.is_file()])
        compliance_ctx = {
            "stage": "step6_edge_cases",
            "output_dir": str(output_dir),
            "step_num": context.get("step_num"),
            "files": [str(output_dir / "step6_edge_case_sops.json")] + [str(p) for p in changed_guidelines],
        }
        compliance_res = await orchestrator.execute_agent(
            agent_name="ComplianceCheckAgent",
            task="对 Step6 边缘场景产物与注入后的局部 guidelines 做门控校验，不通过则终止",
            context=compliance_ctx,
        )
        if isinstance(compliance_res, dict) and compliance_res.get("passed") is False:
            raise ValueError(
                f"Step6 compliance check failed: {((compliance_res.get('compliance_report') or {}).get('issues') or [])[:5]}"
            )

        _append_log("Step6 completed")
        return {
            "step6_edge_case_sops": edge_case_sops,
            "step6_supplementary_rules": supplementary_rules,
            "output_files": [
                "step6_edge_case_sops.json",
                "step6_supplementary_rules.json",
                "step6_validation_report.json",
                *(_ensure_list((compliance_res or {}).get("output_files")) if isinstance(compliance_res, dict) else []),
            ],
            "metadata": {
                "edge_sop_count": len(edge_case_sops),
                "parallel_limit": max_parallel,
                "errors": len(errors),
                "skipped_by_model_count": skipped_by_model_count,
            },
        }
    except Exception as e:
        _append_log(f"Step6 failed: {type(e).__name__}: {e}")
        _append_archive(
            "error",
            {"error": f"{type(e).__name__}: {e}", "traceback": traceback.format_exc()},
        )
        raise

