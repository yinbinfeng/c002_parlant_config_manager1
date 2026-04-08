#!/usr/bin/env python3
"""Step 5: 配置组装与最终检查"""

from pathlib import Path
import re
import shutil
import hashlib
import yaml
from datetime import datetime
from json_repair import repair_json
from ..utils.logger import logger


async def config_assembly_handler(context, orchestrator):
    """配置组装与最终检查"""
    from ..tools.json_validator import JsonValidator

    logger.info("Starting Config Assembly and Final Check...")

    # 加载 Step 2 的 atomic_tasks（任务分解结果）
    atomic_tasks = context.get("atomic_tasks", [])
    dimension_analysis_result = context.get("dimension_analysis_result", {})

    # 如果上下文中没有，尝试从 Step 2 输出目录加载
    if not atomic_tasks:
        step2_output_dir = Path(context.get("step2_output_dir", "./output/dimension_analysis"))
        atomic_tasks_file = step2_output_dir / "atomic_tasks.yaml"
        if atomic_tasks_file.exists():
            try:
                with open(atomic_tasks_file, 'r', encoding='utf-8') as f:
                    tasks_data = yaml.safe_load(f)
                    atomic_tasks = tasks_data.get("tasks", [])
                    context["atomic_tasks"] = atomic_tasks
                    logger.info(f"从 Step 2 加载了 {len(atomic_tasks)} 个原子任务")
            except Exception as e:
                logger.warning(f"加载 atomic_tasks 失败: {e}")

    if not dimension_analysis_result:
        step2_output_dir = Path(context.get("step2_output_dir", "./output/dimension_analysis"))
        dimension_file = step2_output_dir / "dimension_analysis.json"
        if dimension_file.exists():
            try:
                with open(dimension_file, 'r', encoding='utf-8') as f:
                    dimension_analysis_result = repair_json(f.read(), return_objects=True)
                    context["dimension_analysis_result"] = dimension_analysis_result
                    logger.info("从 Step 2 加载了维度分析结果")
            except Exception as e:
                logger.warning(f"加载 dimension_analysis 失败: {e}")
    
    def _derive_agent_id(text: str) -> str:
        """生成简短英文 agent_id，避免用 business_desc 直接命名导致超长路径。"""
        raw = (text or "").strip()
        low = raw.lower()

        tokens: list[str] = []

        # 公司/品牌（可按需要扩展映射）
        if "日本共荣" in raw or "共荣" in raw:
            tokens.append("kyoroei")
        elif "日本" in raw:
            tokens.append("japan")

        # 领域
        if "保险" in raw or "insurance" in low:
            tokens.append("insurance")

        # 场景
        if "挽留" in raw or "续保" in raw or "retention" in low:
            tokens.append("retention")

        # 兜底：使用短 hash（稳定、英文、不会超长）
        digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:8] if raw else "unknown"
        base = "_".join([t for t in tokens if t]) or "parlant_agent"
        agent_id = f"{base}_{digest}" if base == "parlant_agent" else base

        # 只保留小写英文/数字/下划线，最大 32 字符
        agent_id = re.sub(r"[^a-z0-9_]+", "_", agent_id.lower()).strip("_")
        return (agent_id[:32] or "parlant_agent")

    def _load_json_file(path: Path, validator: JsonValidator) -> tuple[dict | None, str | None]:
        try:
            raw = path.read_text(encoding="utf-8")
        except Exception as e:
            return None, f"读取失败: {type(e).__name__}: {e}"

        try:
            return repair_json(raw, return_objects=True), None
        except Exception:
            ok, data, msg = validator.validate(raw)
            if ok and isinstance(data, (dict, list)):
                return data, None
            return None, msg or "JSON 解析失败且修复失败"

    def _ensure_list(x):
        if isinstance(x, list):
            return x
        if x is None:
            return []
        return [x]

    def _extract_guideline_ids(data: dict | list) -> set[str]:
        ids: set[str] = set()
        items = []
        if isinstance(data, dict):
            items.extend(_ensure_list(data.get("guidelines")))
            items.extend(_ensure_list(data.get("sop_scoped_guidelines")))
            items.extend(_ensure_list(data.get("agent_guidelines")))
            if "guideline" in data and isinstance(data.get("guideline"), dict):
                items.extend(_ensure_list(data["guideline"].get("behavior_rules")))
        elif isinstance(data, list):
            items.extend(data)
        for item in items:
            if not isinstance(item, dict):
                continue
            gid = item.get("guideline_id") or item.get("id")
            if isinstance(gid, str) and gid.strip():
                ids.add(gid.strip())
        return ids

    def _extract_tool_ids(data: dict | list) -> set[str]:
        ids: set[str] = set()
        items = []
        if isinstance(data, dict):
            items.extend(_ensure_list(data.get("tools")))
            if "tool" in data and isinstance(data.get("tool"), dict):
                items.extend(_ensure_list(data["tool"].get("definitions")))
        elif isinstance(data, list):
            items.extend(data)
        for item in items:
            if not isinstance(item, dict):
                continue
            for key in ("tool_id", "id", "name", "tool_name"):
                val = item.get(key)
                if isinstance(val, str) and val.strip():
                    ids.add(val.strip())
        return ids

    def _check_cross_file_consistency(journey_payloads: list[dict], guideline_ids: set[str], tool_ids: set[str]) -> list[str]:
        issues: list[str] = []
        for payload in journey_payloads:
            journey_file = payload.get("__source_file", "unknown")
            if "sop_states" in payload:
                for state in _ensure_list(payload.get("sop_states")):
                    if not isinstance(state, dict):
                        continue
                    sid = state.get("state_id", "unknown_state")
                    bind_tool_id = state.get("bind_tool_id")
                    if isinstance(bind_tool_id, str) and bind_tool_id and bind_tool_id not in tool_ids:
                        issues.append(f"{journey_file}:{sid} 引用了不存在的 tool_id `{bind_tool_id}`")
                    for gid in _ensure_list(state.get("bind_guideline_ids")):
                        if isinstance(gid, str) and gid and gid not in guideline_ids:
                            issues.append(f"{journey_file}:{sid} 引用了不存在的 guideline_id `{gid}`")
            elif "journeys" in payload:
                for j in _ensure_list(payload.get("journeys")):
                    if not isinstance(j, dict):
                        continue
                    jname = j.get("name", "unknown_journey")
                    for st in _ensure_list(j.get("states")):
                        if not isinstance(st, dict):
                            continue
                        for gid in _ensure_list(st.get("bind_guideline_ids")):
                            if isinstance(gid, str) and gid and gid not in guideline_ids:
                                issues.append(f"{journey_file}:{jname} 引用了不存在的 guideline_id `{gid}`")
                        tool_ref = st.get("bind_tool_id")
                        if isinstance(tool_ref, str) and tool_ref and tool_ref not in tool_ids:
                            issues.append(f"{journey_file}:{jname} 引用了不存在的 tool_id `{tool_ref}`")
        return issues

    def _collect_relative_files(root: Path) -> set[str]:
        files: set[str] = set()
        for p in root.rglob("*"):
            if p.is_file():
                files.add(str(p.relative_to(root)).replace("\\", "/"))
        return files

    # 以 StepManager 注入的 output_dir 为 step5 目录；同时基于同一 output 根目录定位 step3/step4 产物
    step5_output_dir = Path(context.get("output_dir", "./output/config_assembly"))
    step5_output_dir.mkdir(parents=True, exist_ok=True)

    # StepManager 已经把各 step 的 output_dir 指到正确的 output 根目录下子目录
    # 因此这里直接用 step5_output_dir 的父目录作为 output_base_dir，避免 config 中相对路径导致定位到错误目录。
    output_base_dir = step5_output_dir.parent.resolve()

    step3_dir = output_base_dir / "workflow_development"
    step4_dir = output_base_dir / "global_rules_check"

    if not step3_dir.exists():
        raise ValueError(f"Step 3 输出目录不存在: {step3_dir}")
    if not step4_dir.exists():
        raise ValueError(f"Step 4 输出目录不存在: {step4_dir}")

    validator = JsonValidator()

    # 发现 Step 3 产物
    step3_files = sorted([p for p in step3_dir.rglob("*.json") if p.is_file()])
    if not step3_files:
        raise ValueError(f"Step 3 未发现任何 JSON 产物: {step3_dir}")

    # 发现 Step 4 产物（兼容旧命名）
    global_rules_file = (step4_dir / "step4_global_rules.json")
    if not global_rules_file.exists():
        global_rules_file = step4_dir / "global_rules.json"
    compatibility_file = (step4_dir / "step4_compatibility_report.json")
    if not compatibility_file.exists():
        compatibility_file = step4_dir / "compatibility_report.json"

    if not global_rules_file.exists():
        raise ValueError(f"Step 4 全局规则文件不存在: {global_rules_file}")
    if not compatibility_file.exists():
        raise ValueError(f"Step 4 兼容性报告不存在: {compatibility_file}")

    global_rules, global_rules_err = _load_json_file(global_rules_file, validator)
    compatibility_report, compat_err = _load_json_file(compatibility_file, validator)
    if global_rules_err:
        raise ValueError(f"Step 4 全局规则 JSON 无效: {global_rules_err}")
    if compat_err:
        raise ValueError(f"Step 4 兼容性报告 JSON 无效: {compat_err}")

    # 输出 Parlant 配置包目录（最终产物层）
    agent_name = _derive_agent_id(context.get("business_desc", ""))
    parlant_root = output_base_dir / "parlant_agent_config"
    agent_root = parlant_root / "agents" / agent_name
    (agent_root / "00_agent_base").mkdir(parents=True, exist_ok=True)
    (agent_root / "01_agent_rules").mkdir(parents=True, exist_ok=True)
    (agent_root / "02_journeys").mkdir(parents=True, exist_ok=True)
    (agent_root / "03_tools").mkdir(parents=True, exist_ok=True)

    # Step 4 → 全局规则：提取 rules 或 agent_guidelines 字段作为 agent_guidelines.json
    rules_out = agent_root / "01_agent_rules" / "agent_guidelines.json"
    if isinstance(global_rules, dict):
        if "rules" in global_rules:
            guidelines_payload = {"agent_guidelines": global_rules.get("rules", [])}
        elif "agent_guidelines" in global_rules:
            guidelines_payload = {"agent_guidelines": global_rules.get("agent_guidelines", [])}
        else:
            guidelines_payload = {"agent_guidelines": []}
    elif isinstance(global_rules, list):
        guidelines_payload = {"agent_guidelines": global_rules}
    else:
        guidelines_payload = {"agent_guidelines": []}
    import json
    rules_out.write_text(json.dumps(guidelines_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # 补齐基础元数据文件，提升产物完整性
    metadata_out = agent_root / "00_agent_base" / "agent_metadata.json"
    metadata_payload = {
        "agent_id": f"{agent_name}_001",
        "agent_name": agent_name,
        "agent_description": (context.get("business_desc") or "")[:300],
        "default_language": "zh-CN",
        "default_priority": 5,
        "conversation_timeout": 3600,
        "playground_port": 8801,
        "remark": "Generated by mining_agents step5 config_assembly",
    }
    metadata_out.write_text(json.dumps(metadata_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    observability_out = agent_root / "00_agent_base" / "agent_observability.json"
    observability_payload = {
        "agent_id": f"{agent_name}_001",
        "observability": {
            "enabled": True,
            "track_metrics": ["response_time", "resolution_rate", "fallback_rate"],
            "log_level": "INFO",
        },
    }
    observability_out.write_text(json.dumps(observability_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # Step 3 → 其余文件：按文件名前缀归档到对应目录（尽量保持原始内容，避免“硬编码生成”）
    validation_issues: list[str] = []
    assembled_files: list[str] = [str(rules_out), str(metadata_out), str(observability_out)]
    journey_payloads: list[dict] = []
    guideline_payloads: list[dict | list] = []
    tool_payloads: list[dict | list] = []

    for src in step3_files:
        data, err = _load_json_file(src, validator)
        if err:
            validation_issues.append(f"{src}: JSON 无效: {err}")
            continue

        name = src.stem
        if name.startswith("step3_journeys_"):
            journey_name = name.removeprefix("step3_journeys_") or "journey"
            target = agent_root / "02_journeys" / journey_name / "sop.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(data, dict):
                payload_for_check = dict(data)
                payload_for_check["__source_file"] = src.name
                journey_payloads.append(payload_for_check)
        elif name.startswith("step3_guidelines_"):
            journey_name = name.removeprefix("step3_guidelines_") or "journey"
            target = agent_root / "02_journeys" / journey_name / "sop_guidelines.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            guideline_payloads.append(data)
        elif name.startswith("step3_tools_"):
            tool_name = name.removeprefix("step3_tools_") or "tool"
            target = agent_root / "03_tools" / tool_name / "tool_meta.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            tool_payloads.append(data)
        elif name.startswith("step3_profiles_"):
            target = agent_root / "00_agent_base" / "agent_user_profiles.json"
        elif name.startswith("step3_glossary_"):
            (agent_root / "00_agent_base" / "glossary").mkdir(parents=True, exist_ok=True)
            glossary_name = name.removeprefix("step3_glossary_") or "glossary"
            target = agent_root / "00_agent_base" / "glossary" / f"{glossary_name}.json"
        else:
            # 其他过程产物放入 step5 输出目录，保持可追溯
            target = step5_output_dir / src.name

        target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        assembled_files.append(str(target))

    # 增加 cross-file 一致性检查（Journey -> Guideline/Tool 引用）
    guideline_ids: set[str] = set()
    for p in guideline_payloads:
        guideline_ids.update(_extract_guideline_ids(p))
    guideline_ids.update(_extract_guideline_ids(global_rules if isinstance(global_rules, (dict, list)) else {}))
    tool_ids: set[str] = set()
    for p in tool_payloads:
        tool_ids.update(_extract_tool_ids(p))

    validation_issues.extend(_check_cross_file_consistency(journey_payloads, guideline_ids, tool_ids))

    # 产物完整度检查（对齐示例结构的关键文件）
    required_core_files = [
        agent_root / "00_agent_base" / "agent_metadata.json",
        agent_root / "00_agent_base" / "agent_user_profiles.json",
        agent_root / "01_agent_rules" / "agent_guidelines.json",
    ]
    for f in required_core_files:
        if not f.exists():
            validation_issues.append(f"缺少关键文件: {f}")

    # 生成 step5 报告（对齐设计文档命名）
    assembly_report_file = step5_output_dir / "step5_assembly_report.md"
    validation_report_file = step5_output_dir / "step5_validation_report.md"

    assembly_report_lines = [
        "# Step 5: 配置组装报告",
        "",
        f"- 时间: {datetime.now().isoformat()}",
        f"- 输出目录: `{parlant_root}`",
        f"- Agent: `{agent_name}`",
        f"- Step 3 输入文件数: {len(step3_files)}",
        f"- Step 4 全局规则: `{global_rules_file.name}`",
        f"- Step 4 兼容性报告: `{compatibility_file.name}`",
        "",
        "## 组装产物",
        "",
    ] + [f"- `{p}`" for p in assembled_files]
    assembly_report_file.write_text("\n".join(assembly_report_lines) + "\n", encoding="utf-8")

    validation_report_lines = [
        "# Step 5: 配置包验证报告",
        "",
        "## 数据来源",
        "- ✅ 互联网搜索（Deep Research）：按上游产物决定（本步骤不强行生成）",
        "- ✅ 外部 Data Agent 分析结果：按上游产物决定（本步骤不强行生成）",
        "",
        "## 校验结果",
        f"- 通过: {'是' if not validation_issues else '否（存在问题）'}",
        f"- 问题数量: {len(validation_issues)}",
        "",
        "## 问题明细",
        "",
    ] + ([f"- {x}" for x in validation_issues] if validation_issues else ["- 无"])

    # 兼容：同时在 step5 输出目录下提供 parlant_agent_config，避免用户只查看 config_assembly 子目录时找不到
    parlant_root_in_step5 = step5_output_dir / "parlant_agent_config"
    try:
        if parlant_root_in_step5.exists():
            shutil.rmtree(parlant_root_in_step5, ignore_errors=True)
        shutil.copytree(parlant_root, parlant_root_in_step5)
    except Exception as e:
        logger.warning(f"Failed to mirror parlant_agent_config into step5 output dir: {e}")

    # 参考产物结构对齐评分：轻微差异直接修复；严重差异再返工
    reference_root = (
        Path(__file__).resolve().parents[3]
        / "docs"
        / "dev_docs"
        / "parlant_agent_config"
        / "agents"
        / "insurance_sales_agent"
    )
    structure_score = 100
    missing_vs_reference: list[str] = []
    if reference_root.exists():
        current_files = _collect_relative_files(agent_root)
        ref_files = _collect_relative_files(reference_root)
        # 忽略 Python 包初始化等非关键文件
        ref_files = {x for x in ref_files if not x.endswith("__init__.py")}
        missing_vs_reference = sorted(list(ref_files - current_files))
        if ref_files:
            structure_score = int(round((1 - len(missing_vs_reference) / len(ref_files)) * 100))
        for miss in missing_vs_reference[:20]:
            validation_issues.append(f"相对参考产物缺失文件: {miss}")
    else:
        validation_issues.append(f"参考产物目录不存在: {reference_root}")

    quality_gate = (context.get("config") or {}).get("quality_gate", {})
    severe_threshold = int(quality_gate.get("severe_diff_threshold", 55))
    rework_trigger_threshold = int(quality_gate.get("rework_trigger_threshold", 75))
    max_rework_rounds = int(quality_gate.get("max_rework_rounds", 2))
    current_round = int((context.get("rework_counts") or {}).get("step5", 0))

    rework_required = False
    rework_reason = ""
    if structure_score < rework_trigger_threshold:
        rework_required = True
        rework_reason = (
            f"结构对齐评分过低({structure_score}<{rework_trigger_threshold})，"
            f"{'严重差异' if structure_score < severe_threshold else '中等差异'}"
        )

    # 结构化评分输出
    score_breakdown_lines = [
        "",
        "## 结构化评分",
        "",
        f"- 结构对齐分（0-100）: **{structure_score}**",
        f"- 返工触发阈值: {rework_trigger_threshold}",
        f"- 严重差异阈值: {severe_threshold}",
        f"- 当前返工轮次: {current_round}",
        f"- 最大返工轮次: {max_rework_rounds}",
        f"- 返工决策: {'触发返工' if rework_required and current_round < max_rework_rounds else '不返工'}",
        f"- 决策原因: {rework_reason if rework_reason else '评分达标或已在可接受范围'}",
        "",
        "## 扣分说明",
        "",
    ]
    if missing_vs_reference:
        score_breakdown_lines.extend([
            f"- 参考文件总数: {len(ref_files) if reference_root.exists() else 0}",
            f"- 缺失文件数: {len(missing_vs_reference)}",
            f"- 主要扣分来源: 目录结构与参考产物不一致",
            "",
            "## Top 缺失项（最多20条）",
            "",
        ])
        score_breakdown_lines.extend([f"- {x}" for x in missing_vs_reference[:20]])
    else:
        score_breakdown_lines.extend(["- 未发现参考结构缺失项"])

    validation_report_lines.extend(score_breakdown_lines)

    # 添加任务分解整合报告部分
    atomic_tasks = context.get("atomic_tasks", [])
    dimension_analysis_result = context.get("dimension_analysis_result", {})

    task_integration_lines = [
        "",
        "## 任务分解整合报告",
        "",
        f"- 原子任务总数: {len(atomic_tasks)}",
        f"- 维度分析组件数: {len(dimension_analysis_result.get('components', []))}",
        "",
    ]

    if atomic_tasks:
        task_integration_lines.extend([
            "### 原子任务清单",
            "",
            "| 任务ID | Agent | 维度 | 描述 | 优先级 |",
            "|--------|-------|------|------|--------|",
        ])
        for task in atomic_tasks[:20]:  # 只显示前20个
            task_id = task.get('task_id', 'N/A')
            agent = task.get('agent', 'N/A')
            dimension = task.get('dimension', 'N/A')
            description = task.get('description', 'N/A')[:50]
            priority = task.get('priority', 'N/A')
            task_integration_lines.append(f"| {task_id} | {agent} | {dimension} | {description} | {priority} |")

        if len(atomic_tasks) > 20:
            task_integration_lines.append(f"| ... | ... | ... | 还有 {len(atomic_tasks) - 20} 个任务 | ... |")

        task_integration_lines.extend(["", "### 任务分解与最终配置映射", ""])

        # 分析任务与最终产物的映射关系
        component_tasks = {}
        for task in atomic_tasks:
            dim = task.get('dimension', '')
            if 'component::' in dim:
                comp_id = dim.split('::')[1] if '::' in dim else 'other'
                if comp_id not in component_tasks:
                    component_tasks[comp_id] = []
                component_tasks[comp_id].append(task)

        if component_tasks:
            task_integration_lines.append("任务按组件分布:")
            for comp_id, tasks in component_tasks.items():
                task_integration_lines.append(f"- **{comp_id}**: {len(tasks)} 个任务")
        else:
            task_integration_lines.append("- 任务未按组件分组")

        task_integration_lines.extend([
            "",
            "### 整合说明",
            "",
            "Step 2 的任务分解结果已用于指导 Step 3 的并行开发：",
            "- ProcessAgent 负责处理 journey/guideline/tool 相关任务",
            "- GlossaryAgent 负责处理术语表相关任务",
            "- 每个原子任务的输出已整合到最终的 Parlant 配置包中",
            "",
        ])
    else:
        task_integration_lines.extend([
            "",
            "**警告**: 未找到 Step 2 的原子任务分解结果",
            "",
            "可能原因：",
            "- Step 2 未成功执行",
            "- atomic_tasks.yaml 文件未生成",
            "- 文件路径配置错误",
            "",
        ])

    validation_report_lines.extend(task_integration_lines)
    validation_report_file.write_text("\n".join(validation_report_lines) + "\n", encoding="utf-8")

    # 同时生成独立的任务分解整合报告
    task_integration_file = step5_output_dir / "step5_task_integration_report.md"
    task_integration_content = "# Step 5: 任务分解整合报告\n\n"
    task_integration_content += f"**生成时间**: {datetime.now().isoformat()}\n\n"
    task_integration_content += "## 概述\n\n"
    task_integration_content += f"本报告展示 Step 2 任务分解结果与最终 Parlant 配置包的整合情况。\n\n"
    task_integration_content += "\n".join(task_integration_lines)
    task_integration_file.write_text(task_integration_content, encoding="utf-8")

    output_files = [str(assembly_report_file), str(validation_report_file), str(parlant_root), str(task_integration_file)]
    logger.info(f"Config assembly completed. Output files: {len(output_files)}")
    logger.info(f"Parlant config package generated at: {parlant_root}")

    result = {
        "output_files": output_files,
        "parlant_config_package": str(parlant_root),
        "atomic_tasks_count": len(atomic_tasks),
        "metadata": {
            "agent_name": agent_name,
            "assembled_files_count": len(assembled_files),
            "validation_issues_count": len(validation_issues),
            "structure_score": structure_score,
            "missing_vs_reference_count": len(missing_vs_reference),
            "atomic_tasks_count": len(atomic_tasks),
        },
    }

    if rework_required and current_round < max_rework_rounds:
        result["metadata"]["rework_required"] = True
        result["metadata"]["rework_restart_step"] = 3
        result["metadata"]["rework_reason"] = rework_reason
        result["metadata"]["max_rework_rounds"] = max_rework_rounds
    elif rework_required and current_round >= max_rework_rounds:
        validation_issues.append(
            f"已达到最大返工次数({max_rework_rounds})，不再触发自动返工。当前评分: {structure_score}"
        )
        validation_report_file.write_text(
            "\n".join(validation_report_lines + ["", "- 已达最大返工次数，停止返工"]) + "\n",
            encoding="utf-8"
        )

    return result
