# Step2 Debate Final Decision Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 当 Step2 多模型辩论在最大轮数内仍未达成一致时，追加一次主持人“终局裁决”，输出并记录最终结论，避免使用预置兜底导致偏离主题目标。

**Architecture:** 在现有 `_run_agentscope_debate()` 循环结束后检测“未 finished 且未给出 final_decision”的状态；若触发则调用主持人一次，提示其基于已汇总的共识/分歧与各方摘要给出强制最终结论，并写入 transcript 及返回结构。保持“未一致则进入下一轮”的原有行为不变。

**Tech Stack:** Python, AgentScope `ReActAgent`, `json_repair`, `logrus` logger（项目内 `src/mining_agents/utils/logger.py`）

---

### Task 1: 明确现状与插入点

**Files:**
- Modify: `src/mining_agents/steps/dimension_analysis.py`（函数 `_run_agentscope_debate`）
- Reference: `egs/v0.1.0_minging_agents/config/agents/debate_prompts.yaml`

**Step 1: 阅读并确认现有判断逻辑**
- 确认每轮主持人判断的 JSON 解析入口 `_parse_judge_response()` 与 `finished` 分支。
- 确认循环退出条件：仅 `finished=True` 提前退出，否则跑到 `max_rounds`。
- 确认循环结束后的“最终决策”生成逻辑：当前 `final_decision` 为空时使用 `debate_summary.final_decisions` 兜底。

**Step 2: 定义触发条件**
- 触发终局裁决条件（建议）：
  - 达到 `max_rounds`（循环自然结束）
  - `final_decision is None`（主持人未输出决策）
  - 且最后一次主持人判断 `finished=False`（需记录 last_finished）

---

### Task 2: 增加主持人“终局裁决”调用

**Files:**
- Modify: `src/mining_agents/steps/dimension_analysis.py`

**Step 1: 写一个新的终局裁决提示词构造**
- 新增内部 helper（或内联）构造 prompt：
  - 输入：`round_num`, `max_rounds`, `_summarize_round(solver_agents)`, `final_consensus`, `final_divergence`
  - 输出：要求“仅输出 JSON”，字段包含：
    - `final_decision`（必填）
    - 可选：`consensus_points`, `divergence_points`（若主持人愿意也可补充）
- 解析：复用 `_parse_judge_response()`；若解析不到 `final_decision`，再用 `json_repair` 进行修复解析；仍失败则记录 warning 并回退到“明确标注的软兜底”（不改变现有配置兜底，但在 transcript 标注来源）。

**Step 2: 将终局裁决写入 transcript**
- 在 “辩论总结” 前插入一个小节，例如：
  - `### 终局裁决（达到最大轮数）`
  - 写入主持人 `final_decision` 文本

**Step 3: 返回结构对齐**
- 返回的 `final_decisions` 应优先使用主持人终局裁决的 `final_decision`（列表形式）。
- 保持字段名与现有调用方兼容：`transcript`, `rounds`, `process_log`, `final_consensus`, `final_divergence`, `final_decisions`。

---

### Task 3: 测试覆盖（最小但有效）

**Files:**
- Modify: `tests/test_debate_function.py` 或新增更细的单元测试文件（优先复用现有）
- Modify (if needed): `src/mining_agents/steps/dimension_analysis.py`（让 Mock 模式能覆盖终局裁决路径）

**Step 1: 写一个能稳定触发“终局裁决”的测试**
- 在 Mock 路径中（`_generate_mock_debate_transcript` 或 mock debate runner）构造：
  - 每轮主持人 `finished=False`，且不提供 `final_decision`
  - 触发达到 `max_rounds`
  - 断言最终 `final_decisions` 来自“终局裁决”而非 `debate_summary.final_decisions`

**Step 2: 运行测试**
- Run: `python -m pytest -q`
- 或 Run: `python tests/test_debate_function.py`（如果 pytest 环境未配置）
- 期望：新增断言通过；不引入新 lint/语法错误。

---

### Task 4: 文档与变更记录

**Files:**
- Modify: `changelog.md`

**Step 1: 增加 2026-04-01 的小标题（含时间）**
- 要点记录（简洁）：
  - Step2 辩论未一致时继续下一轮（保持）
  - 达到最大轮数仍未一致：新增主持人终局裁决生成最终结论
  - transcript/返回结构包含裁决来源

