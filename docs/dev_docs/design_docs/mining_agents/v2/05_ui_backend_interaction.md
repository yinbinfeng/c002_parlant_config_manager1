# 会话流程规则挖掘系统 - UI 与后端交互设计文档 (v2 / 8 步法)

**版本**: v2.0 (8 步法架构版)  
**创建日期**: 2026-03-31  
**最后更新**: 2026-03-31  
**文档类型**: 系统交互设计文档（纯设计，无代码）

---

## 一、目标与范围

本文件描述 **Streamlit UI** 与后端 **SessionManager/CoreEngine** 的交互契约，面向 v2 的 **8 步流程**：

- Step1：需求澄清 + 人工确认
- Step2：目标对齐 & 主 SOP 主干挖掘
- Step3：全局规则 & 术语挖掘
- Step4：用户画像挖掘
- Step5：分支 SOP 并行挖掘
- Step6：边缘场景挖掘（子弹 SOP）
- Step7：配置组装
- Step8：最终校验与输出（含 journey schema / 状态机 / 冲突检测）

---

## 二、核心交互对象

### 2.1 SessionManager（UI 直接调用）

UI 通过方法调用（而非 HTTP）驱动后端：

- `create_session(description, data_agent_file, category) -> session_id`
- `submit_task(session_id) -> bool`
- `get_status(session_id) -> session_state`
- `get_clarification(session_id) -> clarification`
- `add_user_question(session_id, question, answer) -> question_id`
- `update_answer(session_id, question_id, answer) -> bool`
- `submit_clarification(session_id) -> bool`
- `skip_clarification(session_id) -> bool`
- `get_result(session_id) -> output`
- `export_config(session_id, output_path=None) -> zip_path`

---

## 三、会话状态结构（核心字段）

```yaml
session:
  session_id: "uuid"
  status: "PENDING|ANALYZING|CLARIFICATION_REQUIRED|GENERATING|COMPLETED|FAILED"
  current_step: 0..8

  progress:
    overall_percent: 0..100
    current_action: "..."
    step_details:
      step1: { status: pending|running|completed|failed, percent: 0..100 }
      step2: { status: pending|running|completed|failed, percent: 0..100 }
      step3: { status: pending|running|completed|failed, percent: 0..100 }
      step4: { status: pending|running|completed|failed, percent: 0..100 }
      step5: { status: pending|running|completed|failed, percent: 0..100 }
      step6: { status: pending|running|completed|failed, percent: 0..100 }
      step7: { status: pending|running|completed|failed, percent: 0..100 }
      step8: { status: pending|running|completed|failed, percent: 0..100 }

  output:
    config_package_path: "/abs/path/to/parlant_agent_config"

    # Step8 校验摘要（可选，但 v2 UI 建议展示）
    validation:
      json_files_checked: 31
      json_parse_errors: 0
      schema_errors: 0
      journey_schema_errors: 14
      state_machine_issues: 0
      conflict_issues: 0

    # Step8 校验详情文件（可选，UI 可用于展开显示）
    validation_report_path: "/abs/path/to/step8_validation_report.md"
    compliance_certificate_path: "/abs/path/to/step8_compliance_certificate.json"
```

---

## 四、UI 页面与交互流程

### 4.1 页面结构（与 `run_ui.py` 对齐）

- **页面 1**：输入（创建会话并提交）
- **页面 2**：Step1 等待（轮询 `get_status`）
- **页面 3**：澄清（`get_clarification` + `update_answer` + `submit/skip`）
- **页面 4**：Step2-8 统一等待（轮询 `get_status`，展示 `step_details`）
- **页面 5**：结果（`get_result` + 导出 + 校验摘要/详情展开）

### 4.2 关键 UX 约束

- UI 只轮询状态，不直接读取 step 目录中间产物（除 Step8 报告“只读展示”场景）
- 结果页默认展示 **校验摘要**；校验详情放在折叠面板中，避免信息过载
- mock 模式需提供：
  - 8 步的 `step_details`
  - `output.validation` 的示例统计

---

## 五、错误与降级策略

- 后端 `status=FAILED` 时 UI 跳转失败页，展示 `last_error.message/traceback`
- Step8 若校验不通过：
  - `status` 仍可为 `COMPLETED`（允许产出“未通过证书”）
  - UI 通过 `output.validation` 与 `validation_report_path` 告知原因与定位入口

---

**维护者**: System Team

