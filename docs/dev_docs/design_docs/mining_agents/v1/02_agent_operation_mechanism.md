# Parlant Agent 配置挖掘系统 - 详细 Agent 运作机制

**版本**: v5.0 (架构设计版)  
**创建日期**: 2026-03-13  
**最后更新**: 2026-03-22  
**文档类型**: 系统架构设计（纯架构，无代码）

---

## 三、多 Agent 协作流程设计

### 3.1 多步协作流程总览（优化版）

```
【Step 1】需求澄清 + 人工确认
    结合人工提供的业务描述文档和 Data Agent 分析结果 → 生成待澄清问题 → 用户确认 → 记录反馈
    ↓
【Step 2】多维度分析与原子化拆解
    多 Agent 辩论 + Deep Research → 分析用户角色/业务场景/边缘情况 → 原子化任务列表
    ↓
【Step 3】工作流并行开发
    三 Agent 协作：流程 Agent + 词汇 Agent + 质检 Agent → 输出各工作流配置
    ↓
【Step 4】全局规则检查与优化
    全局规则 Agent → 兼容性检查 + 规则精简 → 输出全局规则配置
    ↓
【Step 5】配置组装与最终检查
    组装所有内容 → 格式校验 → 输出完整 Parlant 配置包
```

### 3.2 各步骤详细设计

#### Step 1: 需求澄清与人工确认

**定位**: Step 1 是**连接外部分析与在线交互的桥梁**，结合人工提供的业务描述文档和外部 Data Agent 分析生成的私域对话数据结果，生成待澄清问题，等待用户确认。

**输入文件格式要求**:
- **业务描述文档**：Markdown 格式，包含业务背景、流程描述、目标客群、服务边界等信息
- **Data Agent 分析结果**：JSON 格式，包含每个流程 journey 文件的名称与描述字段，结构如下：
  ```json
  {
    "journeys": [
      {
        "name": "预约挂号",
        "description": "用户预约医院门诊挂号的完整流程"
      }
    ]
  }
  ```

**处理逻辑**:
1. **需求分析**：分析人工提供的业务描述文档，识别关键信息缺口
   - 业务目标和范围
   - 目标客户群体
   - 核心业务流程
   - 服务边界和约束

2. **结合 Data Agent 分析结果**：
   - 分析 Data Agent 提供的流程 journey 文件名称与描述
   - 对比业务描述文档与 Data Agent 分析结果的一致性
   - 识别需要用户确认的差异点
   - 补充业务描述中未提及但重要的细节

3. **生成澄清问题**：
   - 针对模糊或不完整的业务需求提出问题
   - 针对 Data Agent 分析发现的潜在流程寻求确认
   - 针对边缘情况和异常处理征询意见

4. **人工确认**（Human-in-the-Loop）：
   - 暂停流程，等待用户回复
   - 生成 `step1_clarification_questions.md` 文件，包含待澄清问题列表
   - 引导用户在该文件中直接录入澄清答案
   - 支持用户修改或补充问题
   - 超时处理（默认超时时间可配置）
   - **用户输入处理**：
     - 用户在命令行窗口输入 `yes`：表示已完成澄清，继续执行后续步骤
     - 用户在命令行窗口输入 `no`：表示跳过澄清，继续执行后续步骤
     - 如果用户未回复（超时）：自动跳过澄清，继续执行后续步骤
   - **澄清问题处理**：
     - 如果用户在 `step1_clarification_questions.md` 中提供了澄清答案：保留澄清内容，并在后续步骤中使用
     - 如果用户输入 `no` 或超时：在后续步骤中不使用澄清问题

5. **文件输出**：
   - 写入 `step1_clarification_questions.md`（包含生成的问题和用户反馈）
   - 写入 `step1_structured_requirements.md`（结构化的需求规格说明）

**输出**: 
- 待澄清问题文件（Markdown 格式）
- 用户需求反馈记录（Markdown 格式）
- 结构化需求规格说明（Markdown 格式）

**React 模式使用**:
- **推理**：分析输入文档，识别信息缺口、矛盾点和模糊表述
- **行动**：生成待澄清问题列表，确保问题覆盖所有关键信息缺口
- **反思**：自我检查问题的合理性、完整性和清晰度，确保问题表述准确、无歧义
- **循环**：如果自我检查发现问题，重新生成澄清问题，直到满足要求
- **行动**：调用人工确认工具，提交待澄清问题
- **反思**：根据用户反馈调整需求理解，重新分析业务需求

**工具调用**:
- `read_text_file`：读取业务描述文档
- `read_text_file`：读取 Data Agent 分析结果
- `write_text_file`：写入澄清问题和结构化需求
- `human_in_loop`：进行人工确认和反馈收集

**目标**:
- 确保业务需求被充分理解和澄清
- 解决业务描述与数据分析结果之间的差异
- 为后续步骤提供清晰、结构化的需求规格说明

**关键决策点**:
- 问题数量的控制（避免过多问题导致用户疲劳）
- 问题优先级的排序（先问核心问题，再问细节）
- 人工确认的超时策略（默认 30 分钟，可配置）
- Data Agent 分析结果的权重（数据分析 vs 人工描述的优先级）

**Parlant 规范符合性检查**:
- 结构化需求必须映射到 Parlant 配置元素
- 所有模糊表述必须被澄清为精确的条件判定
- 用户反馈必须被完整记录并追踪

---

#### Step 2: 多维度分析与原子化拆解（CoordinatorAgent）

**定位**: 从 Step 2 开始，进入**详细的执行阶段**，将结构化的需求分解为原子化的任务单元。

**输入**: 
- `step1_structured_requirements.md`（结构化的需求规格说明）
- `step1_clarification_questions.md`（含用户反馈，可选）

**对前一步输出的处理**:
1. 读取并分析 `step1_structured_requirements.md`，提取关键信息
2. **检查 `step1_clarification_questions.md`**：
   - 如果文件存在且包含用户反馈：分析用户反馈，了解需求澄清情况
   - 如果文件不存在或用户输入 `no` 或超时：跳过澄清问题分析
3. **综合处理**：
   - 如果有澄清信息：将澄清内容整合到需求理解中
   - 如果无澄清信息：仅基于 `step1_structured_requirements.md` 形成需求理解
4. **提示词处理**：
   - 如果有澄清信息：在 Step 2 的具体需求分析文档输出过程中，提示词中包含澄清问题和用户反馈
   - 如果无澄清信息：在 Step 2 的具体需求分析文档输出过程中，提示词中不包含澄清问题

**处理逻辑**:
1. **维度拆解**：按照"用户画像 × 业务流程"矩阵生成任务组合
   - 识别所有用户角色类型
   - 识别所有业务流程节点
   - 生成用户角色与流程的组合矩阵

2. **Deep Research 增强**（可选）：
   - 针对每个维度调用 Deep Research 搜索行业最佳实践
   - 收集类似业务的常见场景和边缘情况
   - 补充用户需求中未明确但重要的维度

3. **多 Agent 辩论**（Multi-Agent Debate）：
   - 不同角色的 Agent 代表不同的视角（如：用户体验视角、业务效率视角、合规视角）
   - 对任务分解的合理性进行辩论
   - 记录辩论过程和最终决策理由

4. **任务分配**：为每个任务指定执行 Agent、依赖关系、预期输出
   - 确定任务的执行顺序（哪些可以并行，哪些必须串行）
   - 为每个任务分配合适的专业 Agent
   - 定义任务的输入输出规范

5. **文件输出**：写入 `step2_atomic_tasks.yaml`
   - task_id: 任务唯一标识
   - agent: 执行 Agent 名称
   - dimension: 所属维度（用户画像×业务流程）
   - description: 任务详细描述
   - dependencies: 依赖的任务 ID 列表
   - expected_output: 预期输出格式

**输出**: 
- 任务分解文件（YAML 格式）
- 维度分析报告（JSON 格式）
- 多 Agent 辩论记录（Markdown 格式）

**关键决策点**:
- 任务粒度的控制（过粗导致执行困难，过细增加协调成本）
- 任务依赖关系的确定（基于数据依赖和执行顺序）
- Agent 选择的策略（根据任务类型匹配最合适的 Agent）
- 辩论终止条件（达成一致或达到最大轮数）

---

#### Step 3: 工作流并行开发（ProcessAgent + GlossaryAgent）

**输入**: 
- `step1_structured_requirements.md`（结构化的需求规格说明）
- `step2_atomic_tasks.yaml`（原子化任务列表）

**参与 Agent**:
- **ProcessAgent**（流程设计）：设计具体业务流程、制定相关规约、选择适用工具、构建用户画像
- **GlossaryAgent**（词汇体系设计）：提取和定义专业术语体系

**处理逻辑**:

1. **并行开发**：
   - ProcessAgent 设计业务流程和状态机
   - GlossaryAgent 提取和定义专业术语

2. **流程设计**（ProcessAgent）：
   - 基于 Step 2 的原子化任务列表，设计具体的业务流程
   - 制定相关规约和规则
   - 选择适用的工具
   - 构建用户画像
   - 确保流程的原子化设计，每个流程聚焦单一核心目标
   - **Loop 检查和修正**：
     - 对设计结果进行自检，检查是否符合 Parlant 规范
     - 如果发现问题，自动进行修正
     - 最多修正次数：可配置（默认 3 次）
     - 记录修正历史和决策依据

3. **词汇体系设计**（GlossaryAgent）：
   - 从业务描述和 Data Agent 分析结果中提取专业术语
   - 定义术语的标准含义和使用场景
   - 建立术语之间的关联关系
   - **Loop 检查和修正**：
     - 对词汇定义进行自检，检查准确性和一致性
     - 如果发现问题，自动进行修正
     - 最多修正次数：可配置（默认 3 次）
     - 记录修正历史和决策依据

4. **文件输出**：
   - `step3_journeys_*.json`（流程定义，符合 Parlant Journey 格式）
   - `step3_guidelines_*.json`（规约定义，符合 Parlant Guideline 格式）
   - `step3_tools_*.json`（工具定义，符合 Parlant Tool 格式）
   - `step3_profiles_*.json`（用户画像定义，符合 Parlant Customer 格式）
   - `step3_glossary_*.json`（词汇定义，符合 Parlant Glossary 格式）
   - `step3_correction_history.json`（修正历史记录）

**输出**: 
- 各专项配置（规则、词汇、工具、旅程）
- 用户画像分群及行为模式（JSON 格式）
- 画像到规则的映射关系（JSON 格式）
- 修正历史记录（JSON 格式）

**关键决策点**:
- 并发数的控制（受 `max_parallel_agents` 限制）
- 目标一致性的维护（如何防止 Agent 偏离总目标）
- 冲突检测（不同画像的专属规则是否冲突）
- 用户画像特征的提取精度（基于规则 vs 基于 Embedding 聚类）
- 旅程原子化的粒度（单一目标 vs 复合目标）
- 分支条件的完备性（覆盖所有可能的用户行为）
- 修正次数的配置（默认 3 次，可根据需求调整）
- 修正策略的选择（自动修正 vs 人工介入）

**Parlant 规范符合性检查**:
- 所有 guideline 必须包含 `chat_state` 字段
- journey 的每个节点必须定义清晰的进入/退出条件
- 状态转换必须形成 DAG，避免死循环
- 工具定义必须包含 input_schema 和 output_schema

---

#### Step 4: 全局规则检查与优化（GlobalRulesAgent）

**输入**: 
- `step1_structured_requirements.md`（结构化的需求规格说明）
- `step3_journeys_*.json`（流程定义）
- `step3_guidelines_*.json`（规约定义）

**参与 Agent**:
- **GlobalRulesAgent**（主责）：全局规则检查与优化

**处理逻辑**:

1. **全局规则检查**：
   - 检查全局规则与各子流程规约的兼容性
   - 确保全局规则的精简性和一致性
   - 识别并解决规则冲突

2. **规则优化**：
   - 精简冗余规则
   - 优化规则优先级
   - 确保规则的可执行性和准确性

3. **兼容性检查**：
   - 检查不同流程之间的规则兼容性
   - 确保规则在不同场景下的一致性
   - 验证规则与 Parlant 规范的符合性

4. **文件输出**：
   - `step4_global_rules.json`（全局规则配置）
   - `step4_compatibility_report.json`（兼容性检查报告）

**输出**: 
- 全局规则配置（JSON 格式，符合 Parlant schema）
- 兼容性检查报告（JSON 格式）

**关键决策点**:
- 搜索角度的选择（覆盖全局规则的各个维度）
- 优先级设定（priority 范围 1-15）
- 排除/依赖关系的设计（避免循环依赖）
- chat_state 的粒度控制（过粗导致规则冲突，过细增加复杂度）
- condition 判定的精确性（避免模糊匹配导致的误触发）

**Parlant 规范符合性检查**:
- 所有 guideline 必须包含明确的 `chat_state` 字段
- condition 必须使用标准布尔表达式（支持 AND/OR/NOT）
- 状态转换必须形成有向无环图（DAG），避免死循环

---

#### Step 5: 配置组装与最终检查（ConfigAssemblerAgent）

**输入文件格式要求**:
- **step3_journeys_*.json**：JSON 格式，符合 Parlant Journey 格式，包含流程定义和状态机
- **step3_guidelines_*.json**：JSON 格式，符合 Parlant Guideline 格式，包含规约定义
- **step3_tools_*.json**：JSON 格式，符合 Parlant Tool 格式，包含工具定义
- **step3_profiles_*.json**：JSON 格式，符合 Parlant Customer 格式，包含用户画像定义
- **step3_glossary_*.json**：JSON 格式，符合 Parlant Glossary 格式，包含词汇定义
- **step4_global_rules.json**：JSON 格式，符合 Parlant schema，包含全局规则配置

**对前一步输出的处理**:
1. 读取并分析所有 Step 3 和 Step 4 的输出文件
2. 按照 Parlant 官方要求的目录结构组织文件
3. 对所有配置文件进行格式校验和质量检查
4. 检测并解决冲突和问题

**参与 Agent**:
- **ConfigAssemblerAgent**（主责）：配置组装与最终检查

**处理逻辑**:

1. **目录组装**：
   - 按照 Parlant 官方要求的目录结构组织文件
   - 确保所有配置文件放在正确的目录中

2. **格式校验**：
   - 使用 json_repair 库检查 JSON 格式
   - 确保所有配置文件符合 Parlant schema

3. **质量检查**：
   - 检查规则之间的排除关系是否循环依赖
   - 检查 Journey 状态机的转移是否有死胡同
   - 检查工具调用的输入输出是否匹配
   - 检查 chat_state 定义是否一致、无歧义
   - 检查 condition 判定逻辑是否存在矛盾

4. **冲突检测**：
   - 检查同一场景下是否存在矛盾的规则
   - 检查全局规则与流程专属规则是否冲突

5. **最终组装**：
   - 整合所有配置文件
   - 生成完整的 Parlant 配置包

6. **文件输出**：
   - `step5_assembly_report.md`（组装报告）
   - `step5_validation_report.md`（验证报告）
   - 完整的 Parlant 配置包（目录结构符合官方规范）

**输出**: Parlant 配置包（目录结构符合官方规范）

**React 模式使用**:
- **推理**：分析所有配置文件，识别格式问题和冲突
- **行动**：修复格式问题，解决冲突，组装配置包
- **反思**：检查组装后的配置包是否符合 Parlant 规范和业务需求

**工具调用**:
- `read_text_file`：读取所有输入文件
- `write_text_file`：写入组装报告和验证报告
- `repair_json`：修复 JSON 格式问题
- `write_text_file`：写入配置包文件

**目标**:
- 按照 Parlant 官方要求的目录结构组织配置文件
- 确保所有配置文件符合 Parlant schema
- 检测并解决配置文件中的冲突和问题
- 生成完整、合规的 Parlant 配置包

**关键决策点**:
- 校验失败的修正策略（自动修复 vs Agent 修正）
- 重试次数的上限（避免无限循环）

---

## Parlant 配置文件样例与字段说明

### Agent 基础配置

**文件路径**: `agents/{agent_name}/00_agent_base/agent_metadata.json`

```json
{
  "agent_id": "medical_customer_service_agent_001",
  "agent_name": "智慧医疗客服 Agent",
  "agent_description": "专业的医疗客服代理，为用户提供预约挂号、化验结果查询、预约取消、就诊咨询等全流程服务",
  "default_language": "zh-CN",
  "default_priority": 5,
  "conversation_timeout": 3600,
  "playground_port": 8801,
  "remark": "医疗业务线专属 Agent，完全独立配置，与其他 Agent 无任何共享"
}
```

**字段说明**：
- `agent_id`：Agent 唯一标识
- `agent_name`：Agent 名称
- `agent_description`：Agent 描述
- `default_language`：默认语言
- `default_priority`：默认优先级
- `conversation_timeout`：对话超时时间（秒）
- `playground_port`：测试端口
- `remark`：配置备注

### 用户画像配置

**文件路径**: `agents/{agent_name}/00_agent_base/agent_user_profiles.json`

```json
{
  "agent_id": "medical_customer_service_agent_001",
  "remark": "医疗客服 Agent专属用户画像配置，用于实现差异化、个性化医疗服务",
  "user_segments": [
    {
      "segment_id": "vip_customers",
      "segment_name": "VIP 客户",
      "description": "高价值客户，享受优先服务和专属优惠",
      "definition": {
        "tags": ["vip", "high_value"],
        "metadata_rules": {
          "total_purchase_amount": ">10000",
          "subscription_plan": "enterprise"
        }
      },
      "behavior_patterns": [
        "偏好高效、私密的服务",
        "愿意为优质服务支付溢价",
        "注重隐私和时间效率"
      ],
      "preferred_journeys": ["vip_fast_track_booking", "premium_consultation"],
      "special_guidelines": [
        {
          "guideline_id": "vip_exclusive_discount",
          "condition": "VIP 客户询问价格",
          "action": "提供 VIP 专属 9 折优惠",
          "priority": 8
        }
      ],
      "custom_variables": {
        "response_time_preference": "fast",
        "privacy_level": "high",
        "price_sensitivity_score": 0.2
      }
    }
  ],
  "personas": [
    {
      "persona_id": "persona_vip_001",
      "persona_name": "高端商务人士张总",
      "segment_id": "vip_customers",
      "demographics": "40-50 岁，企业高管，年收入 200 万+",
      "goals": "高效、私密、定制化医疗服务",
      "pain_points": "时间宝贵，厌恶繁琐流程",
      "behavior_patterns": [
        "偏好一对一专属服务",
        "注重隐私和效率",
        "愿意为优质服务支付溢价"
      ],
      "typical_dialogues": [
        "帮我安排最快的方案，价格不是问题",
        "我需要最私密的就诊环境",
        "直接给我最好的专家号"
      ],
      "parlant_mapping": {
        "tags": ["vip", "time_sensitive", "premium_service"],
        "variables": ["response_time_preference", "privacy_level"],
        "journeys": ["vip_fast_track_booking"],
        "guidelines": ["skip_price_discussion", "offer_premium_options"]
      }
    }
  ]
}
```

**字段说明**：
- `agent_id`：Agent 唯一标识
- `remark`：配置备注
- `user_segments`：用户分群列表
  - `segment_id`：分群唯一标识
  - `segment_name`：分群名称
  - `description`：分群描述
  - `definition`：分群定义（包含 tags 和 metadata_rules）
  - `behavior_patterns`：行为模式
  - `preferred_journeys`：偏好的业务旅程
  - `special_guidelines`：专属指南
  - `custom_variables`：自定义变量
- `personas`：典型用户画像列表
  - `persona_id`：画像唯一标识
  - `persona_name`：画像名称
  - `segment_id`：所属分群 ID
  - `demographics`：人口统计学特征
  - `goals`：用户目标
  - `pain_points`：用户痛点
  - `behavior_patterns`：行为模式
  - `typical_dialogues`：典型对话
  - `parlant_mapping`：与 Parlant 元素的映射

### 全局规则配置

**文件路径**: `agents/{agent_name}/01_agent_rules/agent_guidelines.json`

```json
{
  "agent_id": "medical_customer_service_agent_001",
  "remark": "医疗客服 Agent专属的全局 Guideline（含排除/依赖关系）",
  "agent_guidelines": [
    {
      "guideline_id": "medical_greet_001",
      "scope": "agent_global",
      "condition": "用户首次对话、向代理打招呼（如你好、哈喽、早上好）",
      "action": "用友好的语气回应用户，主动询问用户的医疗相关需求，保持简洁不超过 2 句话",
      "priority": 3,
      "composition_mode": "FLUID",
      "bind_canned_response_ids": ["medical_cr_greet_001"],
      "exclusions": [],
      "dependencies": []
    }
  ]
}
```

**字段说明**：
- `agent_id`：Agent 唯一标识
- `remark`：配置备注
- `agent_guidelines`：全局规则列表
  - `guideline_id`：规则唯一标识
  - `scope`：规则作用范围
  - `condition`：触发条件
  - `action`：执行动作
  - `priority`：优先级（1-15）
  - `composition_mode`：组合模式
  - `bind_canned_response_ids`：绑定的模板话术 ID
  - `exclusions`：排除的规则 ID
  - `dependencies`：依赖的观测 ID

### 流程配置

**文件路径**: `agents/{agent_name}/02_journeys/{journey_name}/sop.json`

```json
{
  "sop_id": "schedule_appt_001",
  "sop_title": "预约挂号全流程 SOP",
  "sop_description": "引导用户完成科室选择、医生选择、时段选择、信息确认、预约提交的全流程，严格遵循医院预约挂号业务规范",
  "trigger_conditions": [
    "用户想要预约挂号",
    "用户询问门诊可预约时间",
    "用户想要找医生就诊",
    "用户需要挂某个科室的号"
  ],
  "timeout": 1800,
  "sop_guideline_mapping": {
    "sop_guideline_file": "./sop_guidelines.json",
    "sop_global_bind_guideline_ids": [
      "schedule_appt_dept_guide_001",
      "schedule_appt_doctor_recommend_001",
      "schedule_appt_time_verify_001"
    ]
  },
  "sop_states": [
    {
      "state_id": "state_000",
      "state_name": "初始 - 科室选择",
      "state_type": "chat",
      "instruction": "友好问候用户，询问用户想要预约哪个科室的号",
      "bind_guideline_ids": ["schedule_appt_dept_guide_001"],
      "transitions": [
        {
          "target_state_id": "state_001",
          "condition": "用户已明确选择具体科室，科室在医院开放列表内"
        }
      ]
    }
  ]
}
```

**字段说明**：
- `sop_id`：SOP 唯一标识
- `sop_title`：SOP 标题
- `sop_description`：SOP 描述
- `trigger_conditions`：触发条件
- `timeout`：超时时间（秒）
- `sop_guideline_mapping`：规则映射
- `sop_states`：状态列表
  - `state_id`：状态唯一标识
  - `state_name`：状态名称
  - `state_type`：状态类型
  - `instruction`：状态指令
  - `bind_guideline_ids`：绑定的规则 ID
  - `transitions`：状态转换
    - `target_state_id`：目标状态 ID
    - `condition`：转换条件

### 工具配置

**文件路径**: `agents/{agent_name}/03_tools/{tool_name}/tool_meta.json`

```json
{
  "tool_id": "medical_tool_get_upcoming_slots",
  "tool_name": "get_upcoming_slots",
  "tool_description": "查询指定科室未来 7 天可预约的医生、职称、可预约时段，支持按科室、医生姓名筛选",
  "timeout": 3,
  "implementation_file": "./tool_impl.py",
  "use_scenarios": [
    "用户进入预约挂号SOP，选择科室后",
    "用户询问某科室的可预约医生",
    "用户询问某医生的可预约时段"
  ],
  "input_params": [
    {
      "param_name": "department",
      "param_type": "string",
      "required": true,
      "default": "",
      "description": "科室名称，如\"内科\"\"外科\""
    }
  ],
  "output_params": [
    {
      "field_name": "doctors",
      "field_type": "array",
      "description": "可预约医生数组"
    }
  ]
}
```

**字段说明**：
- `tool_id`：工具唯一标识
- `tool_name`：工具名称
- `tool_description`：工具描述
- `timeout`：超时时间（秒）
- `implementation_file`：实现文件路径
- `use_scenarios`：使用场景
- `input_params`：输入参数
  - `param_name`：参数名称
  - `param_type`：参数类型
  - `required`：是否必填
  - `default`：默认值
  - `description`：参数描述
- `output_params`：输出参数
  - `field_name`：字段名称
  - `field_type`：字段类型
  - `description`：字段描述

---

**最后更新**: 2026-03-22  
**维护者**: System Team