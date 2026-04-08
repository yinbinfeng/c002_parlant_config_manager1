# Step8 规则去重方案（Guideline Dedup）

## 背景
当前 `step8_validation.py` 已包含：
- JSON 可解析性校验
- schema 校验
- `dependencies / exclusions` 的自依赖与环路检查

但尚未对规则重复进行显式检测，可能导致：
- 同一规则重复输出（相同 `guideline_id`）
- 语义重复规则堆叠（`condition + action` 实质相同）
- 后续执行冲突、质量分被高估

## 目标
在 Step8 增加“规则去重校验”，优先实现“检测并报错”，后续可扩展为“自动修复”。

## 适用范围
1. `agents/*/01_agent_rules/agent_guidelines.json` 的 `agent_guidelines`
2. `agents/*/02_journeys/*/sop_guidelines.json` 的 `sop_scoped_guidelines`

## 去重判定规则
### R1（强规则）
`guideline_id` 重复 => 判定重复（高优先级问题）

### R2（弱规则）
`condition + action` 规范化后相同 => 判定语义重复  
规范化建议：
- `strip()`
- `lower()`
- 压缩连续空白为单空格

### R3（可选增强）
若 `condition + action + dependencies + exclusions` 全部相同，标记为“完全重复”。

## 实施位置
文件：`src/mining_agents/steps/step8_validation.py`

### 插入点 A（journey 规则）
在 `sop_guidelines.json` 解析后、现有冲突检查同一逻辑块内：
- 当前已有：自依赖、自排除、环路检测
- 新增：ID 去重 + 语义去重，结果写入 `conflict_issues`

### 插入点 B（全局规则）
在 `agent_guidelines.json` schema 校验通过后：
- 对 `agent_guidelines` 执行同样去重逻辑
- 重复项写入 `conflict_issues`

## 运行策略
### 阶段 1（推荐）
仅检测，不改文件：
- 发现重复即写入 `conflict_issues`
- `passed` 判定自然失败（沿用现有流程）

### 阶段 2（可选）
自动修复（受配置开关控制）：
- 当 `step8_auto_fix_json.enabled=true` 时，执行去重并回写
- 记录被删除规则到报告中，确保可审计

## 伪代码（核心逻辑）
```python
def norm_text(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"\\s+", " ", s)
    return s

def detect_duplicates(guidelines: list[dict], file_path: str) -> list[str]:
    issues = []
    seen_id = set()
    seen_sig = {}  # sig -> first_guideline_id

    for g in guidelines:
        if not isinstance(g, dict):
            continue
        gid = str(g.get("guideline_id", "")).strip()
        cond = norm_text(str(g.get("condition", "")))
        act = norm_text(str(g.get("action", "")))
        sig = f"{cond}||{act}"

        if gid:
            if gid in seen_id:
                issues.append(f"{file_path}: duplicate guideline_id `{gid}`")
            else:
                seen_id.add(gid)

        if cond and act:
            if sig in seen_sig:
                issues.append(
                    f"{file_path}: duplicate condition+action `{gid or '<no_id>'}` ~= `{seen_sig[sig]}`"
                )
            else:
                seen_sig[sig] = gid or "<no_id>"

    return issues
```

## 报告输出
在 `step9_validation_report.md` 的 `Guideline Conflict Issues` 中体现：
- 重复类型（ID重复 / 语义重复）
- 文件路径
- 涉及 guideline_id

## 验收标准
1. 人工构造同 `guideline_id` 两条规则，Step8 报告出现重复告警
2. 人工构造不同 `guideline_id` 但同 `condition+action`，报告出现语义重复告警
3. 无重复样本时，不新增误报
4. `passed` 与质量分逻辑保持兼容，不破坏现有门控

## 风险与缓解
- 风险：语义重复仅靠字符串规范化，可能漏报/误报  
  缓解：先用保守规则（完全相同），后续再引入近似匹配
- 风险：自动修复可能误删  
  缓解：默认关闭自动修复，仅检测；开启时必须输出删除清单

## 里程碑
- M1：实现检测 + 报告（0.5 天）
- M2：补充测试样本（0.5 天）
- M3：可选自动修复（0.5 天）
