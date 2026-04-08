# Changelog

## 2026-04-06

### 23:30 更新设计文档v2

#### 文档更新内容

**1. 目录结构设计更新** (`01_overall_design.md`):
- 更新分支Journey命名规则：从 `{main_journey_name}__branch_{branch_1}` 改为 `branch_{节点名称}_{node_id}`
- 新增Glossary合并规则说明
- 新增目录命名规则说明章节

**2. Step 5术语提取增强** (`01_overall_design.md`):
- 新增术语类别和数量要求表格
- 要求覆盖产品术语(4-6个)、业务/流程术语(5-7个)、合规/法规术语(4-6个)、服务/沟通术语(2-4个)
- 总术语数要求15-20个

**3. Step 7配置组装详细逻辑** (`01_overall_design.md`):
- 新增ConfigAssemblerAgent处理流程图
- 详细说明Glossary合并逻辑
- 详细说明分支Journey目录创建逻辑
- 详细说明被跳过分支处理机制

**4. 文档元数据更新**:
- 更新 `index.md` 和 `01_overall_design.md` 的最后更新日期为2026-04-06

### 23:00 修复glossary术语库、分支命名和被跳过分支处理问题

#### 问题修复

**1. glossary术语库内容偏少问题** (`step7_config_assembly.py`)：
- 修改glossary合并逻辑，将Step5子分支生成的术语合并到主glossary中
- 实现术语去重（基于term_id）
- 重新编号所有术语（kyoei_term_001, kyoei_term_002...）

**2. branch_node_001内容无意义问题** (`step7_config_assembly.py`)：
- 修改分支目录创建逻辑，跳过被模型判断为不需要二级分支的节点
- 不再为被跳过的分支创建无意义的"skipped"目录和文件

**3. branch_node_unknown命名问题** (`step7_config_assembly.py`)：
- 修改分支目录命名规则，使用"节点名称_node_id"格式
- 例如：branch_呼叫接入与身份确认_node_001
- 避免使用无意义的"node_unknown"命名

**4. Step5 glossary生成优化** (`step5_branch_sop_parallel.py`)：
- 优化术语生成提示词，要求生成15-20个术语
- 要求覆盖产品术语、业务/流程术语、合规/法规术语、服务/沟通术语四大类别
- 更新Few-Shot示例，展示更丰富的术语示例

**5. NodeTaskOutput dataclass修复** (`step5_branch_sop_parallel.py`)：
- 添加skipped_by_model和skip_reason字段到dataclass定义
- 修复动态属性添加导致的潜在问题

#### 修改文件
- `src/mining_agents/steps/step5_branch_sop_parallel.py`：优化glossary提示词，修复dataclass
- `src/mining_agents/steps/step7_config_assembly.py`：合并glossary，改进分支命名，跳过被跳过的分支

### 10:30 新增Step 7提取canned response和observation步骤

#### 功能概述
将canned response和observation从guideline JSON中提取出来，生成独立的parlant格式文件，同时在guideline JSON中建立引用映射。

#### 主要修改

**1. 新增提取步骤** (`step_extract_canned_obs.py`)：
- 创建Step 7（原Step 7-8后移为Step 8-9）
- 从Step3全局guidelines提取canned responses和observations
- 从Step5局部guidelines提取canned responses和observations
- 生成独立的parlant格式文件到`step_extract_canned_obs`目录
- 更新原guideline JSON文件，移除内嵌的canned responses和observations

**2. 步骤编号调整**：
- Step 1-6：保持不变
- Step 7（新增）：提取canned responses和observations
- Step 8（原Step 7）：配置组装
- Step 9（原Step 8）：最终校验

**3. 配置组装更新** (`step7_config_assembly.py`)：
- 优先从提取步骤目录读取canned responses和observations
- 如果提取步骤未执行，回退到原逻辑从Step3/Step5读取
- 支持全局和局部两种级别的文件处理

**4. 步骤管理器更新** (`step_manager.py`)：
- 更新步骤目录映射，新增`step_extract_canned_obs`
- 更新默认end_step从8改为9
- 更新质量门控返工逻辑，将step_num从(5, 8)改为(5, 9)

**5. CLI更新** (`cli.py`)：
- 更新步骤参数范围从1-8改为1-9
- 更新步骤目录映射
- 更新fix模式默认end_step从6改为7

#### 修改文件
- `src/mining_agents/steps/step_extract_canned_obs.py`：新增提取步骤
- `src/mining_agents/engine.py`：注册新步骤处理器
- `src/mining_agents/managers/step_manager.py`：更新步骤目录映射和返工逻辑
- `src/mining_agents/cli.py`：更新步骤参数范围
- `src/mining_agents/steps/step7_config_assembly.py`：支持提取后的文件
- `src/mining_agents/steps/step8_validation.py`：更新步骤编号为9

## 2026-04-05

### 21:50 修复ReAct工具注册失败与canned response生成问题

#### 问题背景
日志分析发现：
1. ReAct工具注册失败：`Failed to register tool 'deep_research' to toolkit: Fields must not use names with leading underscores`
2. ReAct连续返回占位响应：`I noticed that you have interrupted me. What can I do for you?`
3. canned response没有单独生成，被混在branch node的guidelines中

#### 修复内容

**1. ReAct工具注册修复** (`base_agent.py`)：
- 将wrapper函数参数名从 `_tool` 改为 `tool_inst`，避免Pydantic v2字段名验证错误
- 同步修改 `deep_research_wrapper` 和 `json_validator_wrapper` 两个函数
- 修复后工具可正常注册到ReActAgent toolkit

**2. 工具返回值类型修复** (`base_agent.py`)：
- 工具函数必须返回 `ToolResponse` 对象，而不是字符串
- 导入 `ToolResponse` 类并修改返回值类型
- `deep_research_wrapper` 和 `json_validator_wrapper` 现在返回 `ToolResponse(content=[result])`

**3. canned response单独生成修复** (`step7_config_assembly.py`)：
- 新增 `all_canned_responses` 列表收集所有canned responses
- 从step3的 `agent_canned_responses.json` 提取全局canned responses
- 从step5的 `sop_guidelines.json` 中提取 `sop_canned_responses` 字段
- 在组装最后生成全局 `agent_canned_responses.json` 文件到 `01_agent_rules` 目录
- 实现去重逻辑，避免重复的canned response

#### 修改文件
- `src/mining_agents/agents/base_agent.py`：修复工具注册参数名和返回值类型
- `src/mining_agents/steps/step7_config_assembly.py`：新增canned response收集与单独生成逻辑
- `src/mining_agents/agents/compliance_check_agent.py`：修复Step6合规检查对skipped节点的处理

### 10:05 ReAct流程与fallback链路对齐修复
- 恢复并统一 `deep_research` 降级策略：`engine.py` 不再在 real 模式强制关闭 fallback；`system_config.yaml` 默认 `allow_fallback_on_failure: true`，超过失败阈值后改为模型自身知识回复。
- `CoordinatorAgent` / `GlobalRulesAgent` / `GlossaryAgent` / `UserProfileAgent` 新增 `deep_research_brief_template` 支持（从 YAML 注入完整调研任务说明），并在 ReAct 流程中显式要求“先 deep research，再基于 markdown 证据产出 JSON”。
- 新增“模板填充 fallback”链路：当 ReAct + 直连 LLM + 一次 JSON 修复仍失败时，使用固定 JSON 模板让大模型填充字段并决策数组数量，产出带 `fallback_source=template_fill_mode` 的结果。
- 取消 `StepManager` 的 real 模式 fallback 结果硬阻断，允许非 mock 的模板填充降级继续执行；`step3_global_guidelines.py`、`step4_user_profiles.py` 同步放开 real 模式 fallback 抛错限制。
- 维持 JSON 解析策略：先 `json_repair`，失败后仅允许 1 次 LLM 修复（`_llm_fix_json_once`），再解析。

### 09:40 real模式防伪数据 + ReAct/Deep Research链路修复
- real 模式新增硬门控：`StepManager` 在落盘前递归检查结果，若出现 `fallback_source/fallback_warning/mock` 痕迹直接抛错，禁止“看起来成功但其实是兜底模板”。
- `engine.py` 在 real 模式强制关闭 `deep_research.allow_fallback_on_failure`（并记录警告）；`system_config.yaml` 默认值同步改为 `false`。
- `step3_global_guidelines.py`、`step4_user_profiles.py`：real 模式下 Agent 失败或结果缺失时不再回退模板，改为直接失败；mock 模式保留回退能力。
- `requirement_clarification.py`：非交互环境默认 `use_clarification=false`，避免“用户未回答澄清问题仍注入后续提示词”。
- `deep_research.py`：新增“研究任务说明 -> Tavily关键词查询”分层转换，保留 deep research 的完整任务语义，同时让 Tavily 使用短查询，降低跑题检索概率。
- `coordinator_agent.py`：Step2 的 Deep Research 查询改为业务约束型研究 brief（不再用“通用任务分解”短词）；并在 `deep_research.py` 的压缩算法中优先抽取 `业务描述` 领域锚点，减少检索漂移。
- `step2_objective_alignment_main_sop.py`：移除保险场景 few-shot 强示例，改为中性结构约束；Deep Research 查询改为业务导向研究 brief，减少主题漂移。
- `global_rules_agent.py`、`glossary_agent.py`、`user_profile_agent.py`：补充 ReAct 执行流程约束（先检索文本证据、后输出 JSON、最后校验）；`user_profile_agent.py` JSON 解析改为候选提取 + `json_repair/json_validator`，提升稳定性。

### 08:20 修复ReAct工具注册与Deep Research查询词问题

#### 问题背景
用户指出：
1. ReAct使用方式错误：Agent应该先基于任务生成查询问题给Deep Research，Deep Research返回结果后再生成JSON
2. Tavily SDK总是返回无关搜索，查询词偏离了主题（如"日本 保险"硬编码）

#### 修复内容

**1. ReActAgent工具注册**：
- 修复`_init_react_agent`中`toolkit=None`的问题
- 新增Toolkit实例创建和工具注册逻辑
- 注册`deep_research`和`json_validator`工具到ReActAgent toolkit
- 日志显示：`Registered tool 'deep_research' to ReActAgent toolkit`

**2. Step2查询词动态生成**：
- 移除硬编码的"日本 保险"等固定查询词
- 新增行业关键词提取逻辑（保险、银行、医疗、电商等）
- 新增场景关键词提取逻辑（外呼营销、客服、投诉处理、挽留等）
- 根据业务描述动态生成查询词
- 日志显示：`动态生成查询词 (行业=保险, 场景=外呼营销 客服 挽留 续保)`

**3. Agent prompt配置优化**：
- 更新`global_rules_agent.yaml`：查询词根据业务描述动态生成
- 更新`user_profile_agent.yaml`：查询词根据业务描述动态生成
- 更新`glossary_agent.yaml`：查询词根据业务描述动态生成

#### 修改文件
- `src/mining_agents/agents/base_agent.py`：添加Toolkit导入和工具注册逻辑
- `src/mining_agents/steps/step2_objective_alignment_main_sop.py`：动态查询词生成
- `egs/v0.1.0_minging_agents/config/agents/global_rules_agent.yaml`
- `egs/v0.1.0_minging_agents/config/agents/user_profile_agent.yaml`
- `egs/v0.1.0_minging_agents/config/agents/glossary_agent.yaml`

#### 测试验证
- ✅ ReActAgent工具注册成功
- ✅ Step2查询词动态生成（`保险 外呼营销 客服 挽留 续保 合规 要求...`）
- ✅ Step2/3/4全部完成无错误

---

### 00:45 完善Step2/3/4/5/6的fallback策略与动态生成能力

#### 问题背景
用户指出之前的fallback策略等同于"造假"——完全固化模板没有让模型参与生成。需要优化为：
1. 模板可以固化，但关键字段让模型生成填入
2. 如果使用了fallback，必须在日志、生成的最后、以及JSON中明确标识

#### 优化内容

**Step2 主SOP生成**（已在之前实现）：
- Agent动态生成优先，失败时使用模板填空模式
- 模板填空模式让模型只填写：节点数量、节点名称、指令、退出条件
- 输出中标记`fallback_source: "template_fill_mode"`

**Step3 全局规则生成**：
- 新增`_build_guidelines_fallback()`和`_build_glossary_fallback()`函数
- Agent执行失败时使用fallback模板
- 输出中标记`fallback_source: "template_fill_mode"`
- metadata中增加`fallback_info`字段

**Step4 用户画像生成**：
- 新增`_build_user_profiles_fallback()`函数
- mock_mode下标记`fallback_source: "mock_mode_template"`
- 非mock模式下Agent失败时使用fallback模板
- 输出中标记`fallback_source: "template_fill_mode"`
- metadata中增加`fallback_info`字段

**Step5 分支SOP生成**（已在之前实现，本次修复参数传递）：
- 修复`_run_node_task`缺少`orchestrator`参数的问题
- Agent动态生成优先，失败时使用模板填空模式
- 模板填空模式让模型只填写：节点数量、节点名称、指令、转换条件
- 输出中标记`fallback_source: "template_fill_mode"`或`"hardcoded_template"`

**Step6 边缘场景生成**：
- 新增`_generate_edge_scenarios_via_agent()`函数，实现Agent动态生成边缘场景类型
- 新增Few-Shot示例指导Agent生成边缘场景
- Agent动态生成优先，失败时使用预定义场景类型
- 输出中标记`fallback_source: "predefined_scenarios"`或`null`
- validation_report中增加`fallback_info`和`fallback_warning`字段

#### 修改文件
- `src/mining_agents/steps/step3_global_guidelines.py`
- `src/mining_agents/steps/step4_user_profiles.py`
- `src/mining_agents/steps/step5_branch_sop_parallel.py`
- `src/mining_agents/steps/step6_edge_cases.py`

#### 测试验证
- ✅ Step5分支SOP动态生成成功（`fallback_source: null`）
- ✅ Step6边缘场景动态生成成功（`fallback_source: null`）
- ✅ 所有步骤完成无错误
- ✅ 输出JSON中正确标记fallback来源

## 2026-04-04

### 23:30 修复SOP结构固化问题 - Step2改为Agent动态生成
- **问题**：Step2/Step5/Step6的SOP结构完全固化在代码中，不同业务使用相同模板，无法根据业务特点动态生成
- **优化内容**：
  1. **Step2主SOP**：
     - 将`_build_main_sop_backbone`重命名为`_build_main_sop_backbone_fallback`，作为回退模板
     - 添加`_generate_main_sop_via_agent`异步函数，通过Agent动态生成主SOP
     - 添加Few-Shot示例，指导Agent如何生成主SOP
     - 主handler函数优先使用Agent生成，失败时回退到fallback模板
  2. **Step5/Step6**：待Step2测试完成后推广
- **设计原则**：
  - 节点抽象度：每个节点代表"业务阶段"，不是"具体话术"
  - 节点数量约束：一级最多10个，二级最多10个，三级最多30个
  - exit_condition必须可判定，避免"用户满意"等模糊描述
- **修改文件**：
  - `src/mining_agents/steps/step2_objective_alignment_main_sop.py`
- **测试状态**：Step2正在运行中，等待Agent动态生成主SOP的结果

### 22:30 优化触发条件和状态描述的语义清晰度
- **问题**：生成的配置文件中存在大量语义含糊的条件，如"用户明确当前咨询主题"、"信息已足够支撑"等，无法判定
- **优化内容**：
  1. **Step2主SOP**：为每个节点添加具体的exit_condition和exit_condition_examples
     - 原："用户明确当前咨询主题与目标" → 新："用户已明确说出具体咨询主题（如产品类型/服务名称/问题类别），且表达了期望的目标或诉求"
     - 添加判定示例：["用户说：我想咨询XX保险的挽留政策", "用户明确表达：我想XX"]
  2. **Step5分支SOP**：优化transition condition，添加condition_examples
     - 原："已确认触发分支的原因与目标" → 新："用户已明确说出分支处理的具体原因（如：我想了解XX/我对XX有疑问/我需要XX帮助）"
     - trigger_conditions从字符串改为对象，包含trigger和trigger_examples
  3. **Step6边缘场景**：优化trigger_conditions和instruction
     - 添加具体触发示例：["用户说：我再考虑一下", "用户沉默超过5秒后说：嗯..."]
     - instruction从模糊描述改为分步骤指引
     - 添加exit_condition和exit_condition_examples
- **修改文件**：
  - `src/mining_agents/steps/step2_objective_alignment_main_sop.py`
  - `src/mining_agents/steps/step5_branch_sop_parallel.py`
  - `src/mining_agents/steps/step6_edge_cases.py`

### 21:15 恢复final_parlant_config + 边缘场景说明
- **final_parlant_config恢复**：Step8校验后生成`final_parlant_config`作为最终版本，与`parlant_agent_config`（Step7原始输出）区分
- **边缘场景说明**：`system_timeout`是边缘场景的三种类型之一（系统超时），不是生成失败。debug模式下只处理前2个节点的边缘场景，这是设计如此
- **修改文件**：
  - `src/mining_agents/steps/step8_validation.py`: 恢复生成final_parlant_config逻辑
  - `src/mining_agents/cli.py`: Step8额外输出final_parlant_config
- **输出结构**：
  - `parlant_agent_config/` - Step7原始输出
  - `final_parlant_config/` - Step8校验后的最终版本

### 20:35 修复force-rerun删除逻辑 + 添加主journey生成 + 父子journey链接
- **问题修复**：
  1. **force-rerun删除逻辑优化**：原逻辑在end_step==8时删除parlant_agent_config，但Step8不输出该目录。修复：每个step只删除自己输出的文件夹，Step7输出parlant_agent_config，所以只有Step7在force-rerun范围内时才删除。
  2. **主journey缺失**：根据v2设计文档，需要生成主journey的sop.json和sop_guidelines.json。修复：在step7_config_assembly.py中添加主journey生成逻辑。
  3. **父子journey链接**：主journey的每个state需要包含child_journeys字段链接到分支/边缘journey；子journey需要包含parent_sop_id和parent_node_id字段链接回父journey。修复：在step7中建立双向链接。
- **修改文件**：
  - `src/mining_agents/cli.py`: 优化force-rerun删除逻辑，添加step_extra_outputs映射
  - `src/mining_agents/steps/step7_config_assembly.py`: 添加主journey生成和父子链接逻辑
- **输出验证**：
  - 主journey目录：`02_journeys/kyoroei_insurance_retention_main/`
  - 主journey包含6个state，每个state有child_journeys链接
  - 分支journey包含parent_sop_id和parent_state_id
  - 边缘journey包含parent_sop_id、parent_node_id和is_edge_case标记

### 19:45 Stage 1-8 单步测试完成，修复多个问题
- **测试场景**：日本共荣保险外呼营销挽留场景
- **修复问题**：
  1. **Stage 4 UserProfileAgent format_map 递归错误**：模板中JSON示例的花括号`{}`被Python解释为占位符，导致"Max string recursion exceeded"。修复：将JSON示例中的`{`改为`{{`，`}`改为`}}`进行转义。
  2. **Stage 4 UserProfileAgent ReAct中断降级**：模型返回"I noticed that you have interrupted me"时，增加直连LLM降级机制。
  3. **Stage 6 文件路径错误**：Step6尝试读取`step2_main_sop_backbone.json`但实际文件名是`main_sop_backbone.json`。修复：添加正确的文件路径候选。
- **最终输出**：`output/parlant_agent_config/agents/kyoroei_insurance_retention/`目录结构完整，包含：
  - `00_agent_base/`: agent_metadata.json, agent_user_profiles.json, glossary/
  - `01_agent_rules/`: agent_guidelines.json
  - `02_journeys/`: 6个branch节点 + 6个edge场景
  - `03_tools/`: 6个节点的tool_meta.json
- **测试命令**：`python egs/v0.1.0_minging_agents/main.py --mode real --max-parallel 1 --skip-clarification --force-rerun --debug True --start-step N --end-step N --business-desc "..."`

### （当前会话）--force-rerun 启动时删除 output 下对应步骤的目录
- **功能需求**：当使用 --force-rerun 启动时，需要删除 output 下对应步骤的目录
- **修改内容**：
  - 在 `cli.py` 中添加 --force-rerun 处理逻辑
  - 当启用 --force-rerun 时，删除 start-step 到 end-step 范围内的所有步骤目录
  - 如果 end-step 是 8（最后一步），还需要删除最终输出的 parlant_agent_config 文件夹
- **修改文件**：
  - `src/mining_agents/cli.py`
- **使用示例**：
  - `--force-rerun --start-step 3 --end-step 8` 会删除 step3 到 step8 的目录，以及 parlant_agent_config 文件夹

### （当前会话）兜底策略：优先 LLM 直连，real 禁止硬编码冒充；mock 默认与 Step3 契约对齐
- **原则**：real 模式禁止用「与业务输入无关」的固定模板冒充 LLM 成功；**保留**同一业务 prompt 下 **直连 `call_llm`（无工具）** 的兜底。mock 模式下 ReAct 失败后也在尝试直连 LLM，**最后手段**才用最小默认产物。
- `GlobalRulesAgent`：DR fallback 时 mock/real 统一走 `_generate_rules_without_deep_research`；主路径 ReAct 解析失败后 **一律先** `_fallback_direct_llm_rules`，再决定 real `raise` 或 mock 默认。`_get_default_rules` 改为 **Parlant Step3** 形状（`agent_id` + 非空 `agent_guidelines`），`agent_id` 前缀从 `business_desc` / `core_goal` / `industry` 推导，避免合规模块报空。
- `GlossaryAgent`：ReAct 失败后 **mock/real 均先** 直连 LLM 兜底，再 mock `_mock_run` 或 real `raise`；无 DR 子路径同样先直连再分支。
- 回归：`egs/v0.1.0_minging_agents/main.py --mode mock --skip-clarification --start-step 1 --end-step 3`（本项目目录下执行）。

### 10:10 Step2 ReAct 重试 + Tavily 报错日志澄清
- `CoordinatorAgent`：任务分解 ReAct 解析失败时最多重试 3 次（间隔 2s），仍失败则统一走「无 Deep Research」直连 LLM；修正日志：「interrupted me」类话术为 **LLM/ReAct 占位输出**，与 Tavily HTTP 响应区分（旧 MCP 链路易误判）。
- Deep Research：Tavily SDK 异常增加显式 `【Tavily】... message=... | repr=...` 日志行，便于检索。

### 09:50 Deep Research 改为 Tavily Python SDK 直连并完成分步验证
- `DeepResearchTool` 真实模式改为 `tavily-python`（`AsyncTavilyClient`）直连，移除对 `npx tavily-mcp` 子进程依赖；保留原有接口、重试、退避与日志策略。
- 新增 Tavily 结果到 Markdown 报告的结构化转换，日志可见 Tavily 原始返回 key、重试原因与退避等待时间。
- `test_tavily_standalone.py` 默认后端改为 `http`（SDK 直连），`test_deep_research_standalone.py` 去除对 `OPENAI_API_KEY` 的硬依赖。
- `CoordinatorAgent` 增强 `json_repair` 解析健壮性：当返回 list 时自动选取首个 dict，避免 `Expected dict from repair_json, got list` 中断流程。
- 验证结果：Tavily 独立测试（20s 间隔）通过；Deep Research 独立测试（30s 间隔）通过；`main.py` 第 1/2 步完成并生成产物。

### 09:00 Tavily / Deep Research 链路修复与独立测试
- **根因**：无效 Tavily 占位回复（如 interrupted）在 `for` 循环内 `raise`，落在外层 `try/except` 之外，内层重试与退避从未执行；`deep_research_agent._acting` 在 MCP 失败时 `finally` 仍对空 `chunk` 调 `_follow_up` 可能二次异常。
- **修复**：占位类回复改为 `sleep` + `continue`；内层 `except` 增加 429/RPM/MCP 传输类关键字与完整 traceback；`_follow_up` 仅在搜索工具流正常结束後调用；`engine` 将 `deep_research` 中 Tavily/进度相关键传入工具配置。
- **MCP 启动**：新增 `utils/tavily_mcp_stdio.py`（Windows `npx` 解析、`TAVILY_MCP_NPX_EXECUTABLE` 覆盖）；`test_tavily_standalone.py` 默认 20s 间隔、`--backend http` 用 `tavily-python` 直连（无 Node 时可验 Key）；新增 `test_deep_research_standalone.py`（depth/iters=1，两轮间隔 30s）。
- **close()**：未连接时不再调用 `_ensure_tavily_connected()`，仅当 `is_connected` 时 `close(ignore_errors=True)`，避免收尾阶段误触发 `'_AsyncGeneratorContextManager'.args` 类异常。

## 2026-04-03

### 20:45 Tavily 限速重试增加可配置等待时间和指数退避
- **用户需求**：Tavily 报错时，增加可配置的等待时间，默认 30 秒后重试
- **修改内容**：
  1. **配置文件**（`system_config.yaml`）：
     - `tavily_retry_delay_sec: 30` - 重试前等待秒数（默认 30 秒）
     - `tavily_retry_backoff_multiplier: 2.0` - 重试等待时间倍增系数（默认 2.0）
  2. **deep_research.py**：
     - 读取新增配置参数
     - 实现指数退避算法：`wait_time = base_delay * multiplier ^ attempt`
     - 第 1 次重试：等待 30 秒
     - 第 2 次重试：等待 30 * 2.0 = 60 秒
     - 第 3 次重试：等待 30 * 2.0^2 = 120 秒
  3. **日志增强**：
     - 显示详细等待时间：`waiting 30.0s before retry (attempt=1, base_delay=30s, backoff=2.0)`
     - 显示重试原因和次数
- **修改文件**：
  - `egs/v0.1.0_minging_agents/config/system_config.yaml`
  - `src/mining_agents/tools/deep_research.py`
- **预期效果**：
  - ✅ Tavily 限流时自动等待指定秒数后重试
  - ✅ 使用指数退避避免频繁触发 RPM 限制
  - ✅ 日志清晰显示等待时间和重试策略

### 19:00 修正 Real 模式下降级策略：不使用 Mock，而是依靠模型自身知识
- **用户指出问题**：Real 模式下不应该降级到 Mock，而应该重新调用 LLM，不使用 Deep Research 结果，仅依靠模型自身知识完成任务
- **修改内容**：
  1. **CoordinatorAgent**（`coordinator_agent.py`）：
     - 新增 `_generate_task_breakdown_without_deep_research()` 方法
     - Real 模式下检测到 Deep Research 不可用时，重新调用 LLM，提示词中 Deep Research 部分设置为 `[Deep Research 不可用，使用模型自身知识]`
     - 不再调用 `_generate_mock_task_breakdown_default()`
  2. **GlobalRulesAgent**（`global_rules_agent.py`）：
     - 新增 `_generate_rules_without_deep_research()` 方法
     - Real 模式下重新调用 LLM，移除提示词中 Deep Research 相关内容
  3. **GlossaryAgent**（`glossary_agent.py`）：
     - 新增 `_generate_glossary_without_deep_research()` 方法
     - Real 模式下重新调用 LLM，移除提示词中 Deep Research 相关内容
- **修改文件**：
  - `src/mining_agents/agents/coordinator_agent.py`
  - `src/mining_agents/agents/global_rules_agent.py`
  - `src/mining_agents/agents/glossary_agent.py`
- **核心原则**：
  - ✅ **Real 模式**：永不使用 Mock，Deep Research 不可用时重新调用 LLM（不使用 Deep Research 结果）
  - ✅ **Mock 模式**：允许使用 Mock 作为降级
  - ✅ **日志清晰**：显示"Retrying LLM call without Deep Research, using model's own knowledge"
- **预期效果**：
  - Real 模式下即使 Deep Research 完全不可用，也能依靠模型自身知识完成任务
  - 不再出现"Falling back to mock"的日志
  - 输出质量更高（基于 LLM 知识，而非硬编码 Mock）

### 18:45 修复 engine.py 中降级配置参数未传入 DeepResearchTool 的问题
- **问题发现**：用户提出需要 review 代码，确认配置是否真的传入生效
- **根因分析**：
  1. 在 `engine.py` 第 143-158 行构建 `deep_research_tool_config` 字典
  2. 但该字典**没有包含**新增的两个降级配置参数：
     - `max_failures_before_fallback`
     - `allow_fallback_on_failure`
  3. 导致即使 YAML 中配置了，也不会传入 `DeepResearchTool`
- **修复方案**：
  1. 在 `engine.py` 的 `deep_research_tool_config` 字典中增加两个参数
  2. 从 `deep_research_cfg` 中读取配置值
  3. 设置合理的默认值
  4. 更新 debug 日志，显示 `allow_fallback_on_failure` 参数
- **修改文件**：
  - `src/mining_agents/engine.py`（第 159-161 行）
  - `src/mining_agents/tools/deep_research.py`（第 59 行）
- **代码变更**：
  ```python
  deep_research_tool_config = {
      # ... 其他配置 ...
      # 降级机制配置
      "max_failures_before_fallback": deep_research_cfg.get("max_failures_before_fallback", 3),
      "allow_fallback_on_failure": deep_research_cfg.get("allow_fallback_on_failure", True),
  }
  ```
- **验证方式**：
  - 启动系统后，查看 debug-ced296.log 文件
  - 搜索 `DeepResearchTool init params`
  - 确认 `allow_fallback_on_failure` 和 `max_failures_before_fallback` 的值是否正确

### 18:30 Deep Research 降级机制改为 YAML 可配置
- **用户需求**：降级机制需要在 YAML 中可配置，只有允许降级时才执行降级，否则抛异常停止
- **修改内容**：
  1. **配置文件**（`system_config.yaml`）：
     - 新增 `allow_fallback_on_failure: true` 参数
     - 默认值：`true`（允许降级）
     - 可选值：`false`（失败时抛异常停止）
  2. **DeepResearchTool**（`deep_research.py`）：
     - 增加 `_allow_fallback` 实例变量（从配置读取）
     - 修改 `increment_failure_count()` 方法：
       - `allow_fallback_on_failure=true`：进入 fallback 模式（原有行为）
       - `allow_fallback_on_failure=false`：抛出 `RuntimeError` 异常停止执行
  3. **日志增强**：
     - 降级时显示：`entering fallback mode (allow_fallback_on_failure=true)`
     - 抛异常时显示：`fallback is disabled (allow_fallback_on_failure=false). Stopping execution.`
- **修改文件**：
  - `egs/v0.1.0_minging_agents/config/system_config.yaml`
  - `src/mining_agents/tools/deep_research.py`
- **配置示例**：
  ```yaml
  # 允许降级（默认，推荐）
  deep_research:
    allow_fallback_on_failure: true
  
  # 不允许降级（严格模式，失败时抛异常）
  deep_research:
    allow_fallback_on_failure: false
  ```
- **预期效果**：
  - ✅ 默认允许降级（保持向后兼容）
  - ✅ 可配置为严格模式（失败时抛异常）
  - ✅ 日志清晰显示当前配置和行为
  - ✅ 用户可根据场景灵活选择

### 18:15 修复 CoordinatorAgent 强制调用 Deep Research 导致降级策略失效问题
- **问题发现**：用户反馈降级策略可能不生效，检查发现 CoordinatorAgent 在第 397-418 行有"强制调用 Deep Research"的逻辑
- **根因分析**：
  1. CoordinatorAgent 的 `_generate_task_breakdown_with_llm` 方法中，直接调用 `deep_research_tool.search()`
  2. 即使 DeepResearchTool 已设置 `_fallback_mode=True`，仍然会尝试调用 Tavily
  3. 调用失败后只是设置 `deep_research_results = "[Deep Research 调用失败，使用默认知识]"`
  4. 然后继续执行后续 ReAct，**没有触发降级逻辑**
- **修复方案**：
  1. 在调用 Deep Research 前先检查 `is_fallback_mode`
  2. 如已降级，跳过 Deep Research 调用，直接使用模型自身知识
  3. 异常处理中增加降级状态检查，如触发降级则更新本地标志
  4. 降级时设置明确的提示：`[Deep Research 已降级，使用模型自身知识]`
- **修改文件**：
  - `src/mining_agents/agents/coordinator_agent.py`（第 395-432 行）
- **代码变更**：
  ```python
  # 检查 Deep Research 是否已进入降级模式
  is_fallback_mode = (
      self.deep_research_tool is not None and 
      hasattr(self.deep_research_tool, 'is_fallback_mode') and 
      self.deep_research_tool.is_fallback_mode()
  )
  
  # 强制调用 Deep Research 获取行业最佳实践（除非已降级）
  deep_research_results = ""
  if self.deep_research_tool and not is_fallback_mode:
      # 正常调用 Deep Research
      ...
  elif is_fallback_mode:
      self.logger.warning("DeepResearchTool is in fallback mode. Skipping Deep Research call and using model's own knowledge.")
      deep_research_results = "[Deep Research 已降级，使用模型自身知识]"
  ```
- **预期效果**：
  - ✅ Deep Research 降级后，CoordinatorAgent 不再强制调用 Tavily
  - ✅ 降级策略能够正常生效
  - ✅ 日志清晰显示降级状态
  - ✅ 系统完全依靠模型自身知识完成任务

### 18:00 Deep Research 全局降级机制（Real 模式失败自动降级到模型自身知识）
- **用户需求**：Real 模式下，Deep Research 工具失败超过允许次数后，自动降级到不使用 Deep Research，依靠模型自身知识完成任务
- **实现方案**：
  1. **DeepResearchTool**（`deep_research.py`）：
     - 增加 `_failure_count` 失败计数器
     - 增加 `_max_failures` 最大失败次数（默认 3 次）
     - 增加 `_fallback_mode` 降级标志
     - 新增方法：
       - `is_fallback_mode()`：检查是否已降级
       - `get_failure_count()`：获取失败次数
       - `reset_failure_count()`：成功后重置计数
       - `increment_failure_count()`：失败时增加计数并检查是否需要降级
     - `search()` 方法中：
       - 成功时调用 `reset_failure_count()`
       - 失败时调用 `increment_failure_count()` 并抛出异常
  2. **CoordinatorAgent**（`coordinator_agent.py`）：
     - 解析 ReAct 响应失败时，检查 Deep Research 是否已降级
     - 如已降级，自动降级到 mock task breakdown（依靠模型自身知识）
     - 日志显示：`DeepResearchTool is in fallback mode (failures=3). Falling back to mock task breakdown...`
  3. **GlobalRulesAgent**（`global_rules_agent.py`）：
     - 规则生成失败时，检查 Deep Research 是否已降级
     - 如已降级，自动降级到 default rules（依靠模型自身知识）
  4. **GlossaryAgent**（`glossary_agent.py`）：
     - 术语表生成失败时，检查 Deep Research 是否已降级
     - 如已降级，自动降级到 mock glossary（依靠模型自身知识）
  5. **配置文件**（`system_config.yaml`）：
     - 新增 `max_failures_before_fallback: 3` 参数
     - 可配置触发降级的最大失败次数
- **修改文件**：
  - `src/mining_agents/tools/deep_research.py`（增加失败计数和降级逻辑）
  - `src/mining_agents/agents/coordinator_agent.py`（检查降级模式）
  - `src/mining_agents/agents/global_rules_agent.py`（检查降级模式）
  - `src/mining_agents/agents/glossary_agent.py`（检查降级模式）
  - `egs/v0.1.0_minging_agents/config/system_config.yaml`（新增配置参数）
- **工作流程**：
  ```
  Deep Research 调用失败
      ↓
  失败计数 +1（failure_count=1/3）
      ↓
  再次失败 → 失败计数 +1（failure_count=2/3）
      ↓
  再次失败 → 失败计数 +1（failure_count=3/3）
      ↓
  触发降级（fallback_mode=True）
      ↓
  后续所有调用自动降级到模型自身知识
      ↓
  日志警告：DeepResearchTool reached max failures (3/3), entering fallback mode
  ```
- **预期效果**：
  - ✅ Real 模式下 Deep Research 连续失败 3 次后自动降级
  - ✅ 降级后不再尝试调用 Deep Research，直接依靠模型自身知识
  - ✅ 所有使用 Deep Research 的 Agent 都能自动检测并降级
  - ✅ 日志清晰显示降级状态和失败次数
  - ✅ 系统稳定性大幅提升（Tavily 故障时仍能完成任务）
- **配置示例**：
  ```yaml
  deep_research:
    max_failures_before_fallback: 3  # 失败 3 次后降级
  ```

### 17:45 Step2 Deep Research 改为可配置并发模式
- **用户需求**：保留 `asyncio.gather` 并发能力，通过 YAML 配置控制并发/串行
- **修改内容**：
  1. **配置文件**（`system_config.yaml`）：
     - 新增 `step2_max_parallel_queries` 参数
     - 默认值：`1`（串行，免费版 Tavily）
     - 可选值：`3` 或更大（并发，付费版 Tavily）
  2. **step2_objective_alignment_main_sop.py**：
     - 从配置文件读取 `step2_max_parallel_queries`
     - `max_parallel <= 1`：使用串行模式（for 循环）
     - `max_parallel > 1`：使用并发模式（`asyncio.gather` + Semaphore 限流）
     - 日志中明确显示当前模式：`串行模式 (max_parallel=1)` 或 `并发模式 (max_parallel=3)`
- **修改文件**：
  - `egs/v0.1.0_minging_agents/config/system_config.yaml`
  - `src/mining_agents/steps/step2_objective_alignment_main_sop.py`
- **使用方式**：
  ```yaml
  # 免费版 Tavily（串行，避免 RPM 限制）
  deep_research:
    step2_max_parallel_queries: 1
  
  # 付费版 Tavily（并发，提速）
  deep_research:
    step2_max_parallel_queries: 3
  ```
- **预期效果**：
  - ✅ 免费版用户：串行执行，稳定避免 RPM 限制
  - ✅ 付费版用户：并发执行，提速 3 倍
  - ✅ 灵活配置，无需修改代码

### 17:30 Tavily 免费版 RPM 限制对策（限流降级修复）
- **问题**：用户使用免费版 Tavily，有严格的 RPM（Requests Per Minute）限制（通常 1-2 请求/分钟）
- **错误表现**：
  ```
  2026-04-03 17:04:04 | WARNING  | Detected invalid ReAct response from Tavily interruption 
  2026-04-03 17:04:04 | ERROR    | Failed to parse ReAct response: Invalid ReAct response: I noticed that you have interrupted me. What can I do for you?
  2026-04-03 17:04:04 | WARNING  | Tavily error detected in Real mode: Falling back to mock task breakdown for system stability
  ```
- **根因分析**：
  1. Step 2 中并发执行 3 个 Deep Research 查询（`asyncio.gather`）
  2. 超过 Tavily 免费版 RPM 限制后，返回中断消息而非正常结果
  3. CoordinatorAgent 收到中断消息，JSON 解析失败
  4. 系统降级到 mock 模式
- **修复方案**：
  1. **配置文件**（`system_config.yaml`）：
     - 增加 `tavily_retry_on_rate_limit: true`（检测限流时自动重试）
     - 增加 `tavily_retry_delay_sec: 30`（重试前等待 30 秒，避免触发 RPM 限制）
     - 增加 `tavily_max_retries: 3`（最大重试 3 次）
     - 调整 `timeout_retry_count: 0 -> 2`（增加超时重试次数）
  2. **deep_research.py**：
     - 读取 RPM 限制对策配置
     - 检测到限流时增加延迟等待（30 秒）
     - 日志中明确区分"timeout"和"rate limit"两种重试原因
  3. **step2_objective_alignment_main_sop.py**：
     - 将并发执行（`asyncio.gather`）改为串行执行（for 循环）
     - 每个查询完成后等待下一个，避免触发 RPM 限制
     - 增加进度日志，便于观察执行状态
- **修改文件**：
  - `egs/v0.1.0_minging_agents/config/system_config.yaml`（新增 RPM 限制对策配置）
  - `src/mining_agents/tools/deep_research.py`（增加限流检测和延迟重试）
  - `src/mining_agents/steps/step2_objective_alignment_main_sop.py`（并发改串行）
- **预期效果**：
  - ✅ 串行执行避免触发 RPM 限制
  - ✅ 检测到限流后自动等待 30 秒再重试
  - ✅ 日志清晰显示限流检测和重试过程
  - ✅ 免费版 Tavily 也能正常工作（虽然速度较慢）
- **使用建议**：
  - 免费版 Tavily 用户：保持当前配置（串行 + 重试）
  - 付费版 Tavily 用户：可改回并发执行（修改 step2 代码）并关闭重试

### 17:15 修复 Tavily 无效响应重试逻辑失效问题
- **问题**：虽然增加了无效响应检测和重试机制，但实际运行时重试并未生效，日志显示 `attempt=1` 后立即 `All retries failed`
- **根因分析**：
  1. 第 526 行抛出 `RuntimeError("Invalid Tavily response detected")` 
  2. 该异常被外层第 469 行 `except Exception as e` 捕获
  3. 但第 472 行只检查 `is_timeout`，不检查 `is_invalid_response`
  4. 导致第 477 行的重试条件 `if is_timeout and attempt < max_retries` 不满足
  5. 直接执行第 483 行 `raise last_err`，循环中断
- **修复方案**：
  1. 在第 472 行增加 `is_invalid_response` 检测
  2. 修改第 477 行重试条件为 `if (is_timeout or is_invalid_response) and attempt < max_retries`
  3. 增加专门的无效响应警告日志
  4. 重试日志中区分 timeout 和 invalid response 两种原因
- **修改文件**：
  - `src/mining_agents/tools/deep_research.py`（第 471-483 行）
- **预期效果**：
  - 无效响应现在会触发重试（最多 2 次）
  - 日志清晰区分超时重试和无效响应重试
  - 只有在所有重试都失败后才使用降级报告

### 16:45 Deep Research Tavily 中断错误与多 Agent 辩论降级修复
- **问题根因**：
  1. Tavily MCP 客户端在搜索过程中被中断，返回 `"I noticed that you have interrupted me. What can I do for you?"` 而非正常搜索结果
  2. DeepResearchAgent 接收到中断消息后无法生成有效报告，导致 CoordinatorAgent/GlobalRulesAgent/GlossaryAgent 的 ReAct 响应解析失败
  3. Real 模式下禁止降级策略过于严格， Tavily 错误时系统直接崩溃
- **修复方案**：
  1. **deep_research.py**：
     - 增加无效响应检测模式（`interrupted me`/`what can i do for you`/`i noticed that you`）
     - 检测到无效响应时自动重试（默认 2 次）
     - 所有重试失败后返回降级报告（包含错误提示和建议）
     - 将默认 `max_retries` 从 1 增加到 2
  2. **coordinator_agent.py**：
     - 在 ReAct 响应解析前增加无效响应检测
     - Real 模式下检测到 Tavily 错误时允许降级到 mock（保证系统可用性）
     - 其他错误仍保持严格模式（抛出 RuntimeError）
  3. **global_rules_agent.py**：
     - 增加无效响应检测
     - Real 模式下 Tavily 错误时降级到默认规则
  4. **glossary_agent.py**：
     - 增加无效响应检测
     - Real 模式下 Tavily 错误时降级到 mock glossary
- **修改文件**：
  - `src/mining_agents/tools/deep_research.py`
  - `src/mining_agents/agents/coordinator_agent.py`
  - `src/mining_agents/agents/global_rules_agent.py`
  - `src/mining_agents/agents/glossary_agent.py`
- **预期效果**：
  - Tavily 中断时自动重试，提高成功率
  - 重试失败后优雅降级，保证系统继续运行
  - 日志中清晰记录 Tavily 错误和降级决策
  - Real 模式在 Tavily 故障时仍能生成可用产物（带警告）

### 20:30 全局模型切换为 Qwen/Qwen3.5-27B
- **修改范围**：所有 YAML 配置文件中的模型名称
- **修改内容**：将所有 `Qwen/Qwen3.5-35B-A3B` 替换为 `Qwen/Qwen3.5-27B`
- **修改文件列表**：
  1. `egs/v0.1.0_minging_agents/config/system_config.yaml`（2处：openai.model_name 和 deep_research.model_name）
  2. `egs/v0.1.0_minging_agents/config/agents/coordinator_agent.yaml`
  3. `egs/v0.1.0_minging_agents/config/agents/compliance_check_agent.yaml`
  4. `egs/v0.1.0_minging_agents/config/agents/config_assembler_agent.yaml`
  5. `egs/v0.1.0_minging_agents/config/agents/global_rules_agent.yaml`
  6. `egs/v0.1.0_minging_agents/config/agents/glossary_agent.yaml`
  7. `egs/v0.1.0_minging_agents/config/agents/user_profile_agent.yaml`
  8. `egs/v0.1.0_minging_agents/config/agents/requirement_analyst_agent.yaml`
- **验证结果**：✅ 所有 YAML 文件中已无 `Qwen3.5-35B-A3B` 残留
- **影响范围**：所有使用 LLM 的 Agent 和 Deep Research 功能

### 20:45 GlobalRulesAgent Real 模式下禁止降级修复
- **问题**：`GlobalRulesAgent` 在 ReAct 响应解析失败时，会降级到默认规则，违反了 real 模式的基本原则
- **错误日志**：
  ```
  2026-04-03 16:04:53 | ERROR | Failed to parse ReAct response as JSON object; using default rules
  ```
- **根本原因**：
  - ReAct Agent 返回了中断消息 `"I noticed that you have interrupted me. What can I do for you?"` 而不是有效的 JSON
  - 解析失败时，代码直接降级到 `_get_default_rules()`
- **修复方案**：
  1. 修改 `execute` 方法签名，添加 `mock_mode` 参数
  2. 在解析失败时，只有 `mock_mode=True` 时才降级到默认规则，否则抛出 `RuntimeError`
  3. 更新文档说明，添加 `Raises` 部分
- **修改文件**：`src/mining_agents/agents/global_rules_agent.py`
- **验证结果**：
  - ✅ `user_profile_agent.py` 已经正确处理（real 模式下抛出 ValueError）
  - ✅ `config_assembler_agent.py` 已经修复（之前的修复）
  - ✅ `glossary_agent.py` 已经正确处理（real 模式下抛出 RuntimeError）
- **预期效果**：real 模式下失败时会抛出明确的异常信息，而不是静默降级到默认规则

### 18:45 Step2 non_goals 字段消歧义（修正版）
- **问题**：`src/mining_agents/steps/step2_objective_alignment_main_sop.py` 中 `non_goals` 字段使用"本步骤"表述不够明确,存在歧义
- **修复**：将 `non_goals` 字段中的"本步骤"改为具体的阶段描述
  - "不在本步骤输出最终 Parlant 目录结构" → "不在目标对齐与主SOP主干挖掘阶段输出最终 Parlant 目录结构"
  - "不在本步骤处理边缘场景子弹 SOP" → "不在目标对齐与主SOP主干挖掘阶段处理边缘场景子弹 SOP"
- **说明**：
  - 根据设计文档 v2 的 8 步法流程,Step 2 的职责是"目标对齐与主SOP主干挖掘"
  - 最终 Parlant 目录结构输出在 Step 7（配置组装阶段）
  - 边缘场景子弹 SOP 处理在 Step 6（边缘场景挖掘阶段）
- **修改文件**：
  - `src/mining_agents/steps/step2_objective_alignment_main_sop.py`（代码源头）
  - `output/step2_objective_alignment_main_sop/result.json`（输出文件同步更新）

### 19:10 Real 模式下禁止降级到 Mock 模式
- **问题**：在 real 模式下，当 LLM 调用或 JSON 解析失败时，系统会自动降级到 mock 模式，违反了 real 模式的基本原则
- **影响范围**：
  - `coordinator_agent.py`：在 `_generate_task_breakdown_with_llm` 方法中，解析失败时降级到 mock
  - `config_assembler_agent.py`：在 `_assemble_final_config` 方法中，解析失败时降级到默认配置
- **修复方案**：
  1. **coordinator_agent.py**：
     - 修改 `_generate_task_breakdown_with_llm` 方法签名，添加 `mock_mode` 参数
     - 在异常处理中，只有 `mock_mode=True` 时才降级到 mock，否则抛出 `RuntimeError`
     - 修改调用处，传递 `mock_mode` 参数
  2. **config_assembler_agent.py**：
     - 修改 `_assemble_final_config` 方法签名，添加 `mock_mode` 参数
     - 在异常处理中，只有 `mock_mode=True` 时才降级到默认配置，否则抛出 `RuntimeError`
     - 修改调用处，传递 `mock_mode` 参数
- **验证**：
  - ✅ `requirement_analyst_agent.py` 已经正确处理（real 模式下抛出异常）
  - ✅ `glossary_agent.py` 已经正确处理（real 模式下抛出异常）
- **修改文件**：
  - `src/mining_agents/agents/coordinator_agent.py`
  - `src/mining_agents/agents/config_assembler_agent.py`
- **预期效果**：real 模式下失败时会抛出明确的异常信息，而不是静默降级到 mock 模式

### 11:15 Step2 文件命名消歧义与临时目录修复
- **问题1：DeepResearchAgent 临时目录不存在**
  - 根因：`./tmp/deep_research` 目录未预先创建，导致 `report_01.md` 报错 `Error: [Errno 2] No such file or directory`
  - 修复：在 `deep_research.py` 初始化 DeepResearchAgent 前自动创建临时目录
- **问题2：Step2 目录下文件命名语义冗余**
  - 根因：目录名 `step2_objective_alignment_main_sop` 已包含步骤标识，文件名又带 `step2_` 前缀，造成语义不明
  - 修复：移除文件名中的 `step2_` 前缀，统一命名规范：
    - `step2_business_objectives.md` → `business_objectives.md`
    - `step2_main_sop_backbone.json` → `main_sop_backbone.json`
    - `step2_debate_history.json` → `debate_history.json`
    - `step2_debate_transcript.md` → `debate_transcript.md`
    - `step2_canned_responses.json` → `canned_responses.json`
    - `step2_deep_research_results.md` → `deep_research_results.md`
    - `step2_research_reports/` → `research_reports/`

### 10:30 Step2 Deep Research 中断与多模型辩论参数缺失修复
- **问题1：Deep Research 被中断**
  - 根因：`system_config.yaml` 中 `deep_research.max_iters: 1` 和 `max_depth: 1` 设置太小，导致 DeepResearchAgent 无法完成完整的搜索过程，返回中断消息 `"I noticed that you have interrupted me. What can I do for you?"`
  - 修复：将 `max_iters` 和 `max_depth` 从 1 增加到 3，确保完整的搜索和推理过程
- **问题2：ReAct Agent 迭代次数不足**
  - 根因：`coordinator_agent.yaml` 中 `react_max_rounds: 2` 设置太小
  - 修复：将 `react_max_rounds` 从 2 增加到 5，确保 ReAct Agent 有足够的迭代次数完成任务
- **问题3：多模型辩论参数缺失**
  - 根因：`step2_objective_alignment_main_sop.py` 的 `_run_multi_agent_debate` 函数传递给 CoordinatorAgent 的 context 缺少关键参数
  - 修复：补充传递 `step1_questions`、`step2_expert_opinions`、`step2_user_concerns`、`step2_requirement_defense`、`step2_debate_transcript` 参数
- 影响：修复后 Deep Research 和多模型辩论功能可正常工作

### 09:45 Step2 ReAct 响应解析类型安全修复
- 问题：`repair_json(response, return_objects=True)` 对非 JSON 字符串可能返回字符串而非字典，导致 `'str' object does not support item assignment` 错误。
- 修复：在 `coordinator_agent.py::_generate_task_breakdown_with_llm` 中增加类型检查，确保 `task_breakdown` 为字典类型后再进行操作。
- 影响：当 DeepResearchAgent 返回中断消息（如 `"I noticed that you have interrupted me..."`）时，代码会正确回退到 mock 数据生成。

## 2026-04-02

### 23:55 全 Agent ReAct 参数配置化与默认值收敛
- 代码：`CoordinatorAgent/UserProfileAgent/GlossaryAgent/GlobalRulesAgent` 改为从 YAML 读取 `model.use_react` 决定是否初始化 ReAct，不再硬编码强制启用。
- 配置：所有 agent YAML 显式补齐 `model.react_max_rounds` 与 `model.use_react`，实现统一可配置。
- 默认值建议已落地：
  - RequirementAnalyst: `use_react=false`, `react_max_rounds=2`
  - Coordinator: `use_react=true`, `react_max_rounds=2`
  - UserProfile: `use_react=true`, `react_max_rounds=2`
  - Glossary: `use_react=true`, `react_max_rounds=3`
  - GlobalRules: `use_react=true`, `react_max_rounds=3`
  - ConfigAssembler/ComplianceCheck: `use_react=false`, `react_max_rounds=1`

### 23:45 RequirementAnalyst ReAct 轮数与开关显式化
- 说明与修正：`max_iters=5` 来源于 `BaseAgent` 的默认值（`model.react_max_rounds` 缺省时取 5）。
- 配置新增：`requirement_analyst_agent.yaml` 增加 `model.react_max_rounds: 2` 与 `model.use_react: false`。
- 代码调整：`RequirementAnalystAgent` 仅在 `use_react=true` 时初始化 ReAct；默认关闭，Step1 走 JSON-only `call_llm` 路径，减少不必要的 ReAct 初始化与误导日志。

### 23:30 Step1 超时与异常打印稳定性修复
- 通用 Agent 模型请求超时从硬编码 `120s` 改为可配置（`openai.request_timeout_sec`，默认 `180s`），降低 `RequirementAnalyst` 在长提示词场景下超时概率。
- 异常日志链路加固：`BaseAgent` / `AgentOrchestrator` / `cli` 在打印异常时改为安全字符串化（`str` 失败回退 `repr`），避免二次抛出编码异常导致“真实错误被遮蔽”。

### 23:15 ReAct 过程日志独立落盘
- 在 `BaseAgent.call_react_agent` 增加 ReAct trace 文件写入：输入、运行心跳、输出、异常均写入独立日志文件。
- 落盘路径优先使用 `step_message_archive_dir`，无该路径时回落到 `output_dir`；文件名：`{AgentName}_react_trace.log`。
- 目的：避免主日志被过程日志淹没，同时支持按步骤/Agent 快速定位长耗时卡点。

### 23:05 ReAct 运行中进度日志（长耗时可见）
- `BaseAgent.call_react_agent` 增加实时心跳日志：每隔固定间隔输出 `elapsed` 与 ReAct memory 快照（消息数量/最后一条预览）。
- 新增配置 `logging.react_progress_log_interval_sec`（默认 10 秒），用于控制 ReAct 进度日志频率。
- 目标：解决“ReAct 长时间无输出，不知道模型在做什么”的可观测性问题。

### 22:50 ReAct 过程日志全程可见
- `BaseAgent` 初始化 ReActAgent 时启用可配置的 `print_hint_msg`，默认打开，便于观察每轮 ReAct 的思考/行动轨迹。
- 系统配置新增 `logging.react_print_hint_msg: true`，可按环境快速开关，避免生产日志过载。

### 22:35 Agent/DeepResearch 大模型交互日志增强
- `BaseAgent` 增加大模型交互日志：输出请求 messages 预览、响应内容预览（`call_llm` 与 `call_react_agent`）。
- `DeepResearchAgent`（内部模型调用）增加输入/输出日志预览，覆盖其 `get_model_output` 路径。
- 新增日志配置项：`logging.llm_message_preview_chars`（默认 1200），用于控制日志预览长度。

### 22:20 Deep Research 卡住可观测性增强（心跳日志）
- 在 `deep_research.py::_real_search` 增加执行心跳日志：长请求执行期间按间隔输出 `elapsed/remaining/query_len`，避免“长时间无日志”。
- 新增配置项支持：`deep_research.progress_log_interval_sec`（默认 15 秒），用于控制心跳日志频率。

### 22:10 Deep Research 超时策略调整 + 超时告警
- 配置调整：`deep_research.timeout_sec/client_timeout_sec` 从 `300` 降到 `120`，`timeout_retry_count` 从 `1` 调整为 `0`（优先快速失败，减少长时间卡住）。
- 日志增强：在 `deep_research.py::_real_search` 中，超时场景新增 `warning` 告警，包含 `attempt/timeout_sec/query_len`，便于快速定位慢查询与超时原因。

### 22:00 Step1 Deep Research 调用次数修正（默认 1 次）
- 根因：Step1 之前固定构造 3 条查询，导致日志中出现“同一步骤多次调用 Deep Research”并显著拉长耗时。
- 修复：`requirement_clarification.py` 新增 `deep_research.step1_query_count` 控制查询条数，默认 1；保留可配置扩展到 2/3。
- 配置：`system_config.yaml` 增加 `step1_query_count: 1`，并与 `step1_max_parallel_queries` 联合控制 Step1 检索开销。

### 21:45 Deep Research 日志增强（query_len）
- 在 `deep_research.py::_real_search` 增加查询长度日志：`query_len`。
- 同时将日志查询文本做空白规范化并限制为 300 字预览（防止日志过长），便于快速判断是否存在截断/组装异常。

### 21:35 Deep Research 查询改为完整业务描述（移除截断）
- 修复 Step1/Step2/Step4/Coordinator 中 Deep Research 查询拼接逻辑，移除 `[:50]/[:80]/[:120]` 截断，改为传入完整 `business_desc`。
- 增加查询文本规范化（压缩多余空白与换行），避免日志中出现中间断裂造成“疑似截断”的误判。
- 说明：不再把“阶段性截断”带入查询，Deep Research 按完整上下文检索。

### 21:15 全量模型切换 + 关闭 thinking 模式
- 配置层：将 `egs/v0.1.0_minging_agents/config` 下所有 Agent 与系统配置中的 `model_name` 统一替换为 `Qwen/Qwen3.5-35B-A3B`。
- 配置层：所有 Agent 配置新增/统一 `enable_thinking: false`；`system_config.yaml` 中 `openai` 与 `deep_research` 也新增 `enable_thinking: false`。
- 代码层：按 OpenAI/Qwen 参考参数接入 `extra_body.chat_template_kwargs.enable_thinking`：
  - `src/mining_agents/agents/base_agent.py`
  - `src/mining_agents/tools/deep_research.py`
  - `src/mining_agents/engine.py`（透传 `deep_research.enable_thinking`）

### 20:55 Deep Research 升级为实例池（方案1）
- 新增 `DeepResearchToolPool`（`src/mining_agents/tools/deep_research_pool.py`），对外保持 `search/execute/get_tool_schema/close` 接口不变，内部按轮询分发到多个 `DeepResearchTool` 实例。
- `engine.py` 接入池化：读取 `deep_research.pool_size`，当 `pool_size > 1` 时注册池化工具，否则保持单实例。
- 配置新增：`deep_research.pool_size`（当前设为 `2`），在保留稳定性的同时恢复 Deep Research 的并发吞吐。

### 20:35 修复 Step1 Deep Research 超时（Request timed out）
- 根因定位：Step1 对同一 `DeepResearchTool` 实例并发发起 3 个查询；底层 `DeepResearchAgent` 持有可变状态（memory/subtask），并发复用同实例会放大超时与不稳定性。
- 修复1（工具层）：`deep_research.py` 增加搜索互斥锁，确保同实例串行执行；补充 timeout 场景重试（`timeout_retry_count`）。
- 修复2（调用层）：`requirement_clarification.py` 将 Step1 查询改为可配置限流并发（默认 `step1_max_parallel_queries: 1`），避免状态冲突。
- 修复3（超时一致性）：为 OpenAI 客户端显式注入 `client_timeout_sec`，避免仅外层 wait_for 生效而底层请求提前超时。

### 20:15 修复 Step1 Deep Research `KeyError: 'text'`
- 根因：`DeepResearchAgent` 在处理中间总结与报告聚合时，假设模型块是 dict 并直接读取 `["text"]`，当返回 `TextBlock` 对象时触发 `KeyError: 'text'`。
- 修复：在 `deep_research_agent.py` 新增统一文本提取方法，兼容 dict / 对象两种 block 结构，并替换所有相关硬编码取值点。
- 回归：新增单测 `test_extract_text_from_blocks_handles_dict_and_object`，覆盖两种 block 输入形态。

### 14:55 Task53 Step1/Step2 v2一致性核查修复
- Step1：`--skip-clarification` 改为“仍生成澄清问题与结构化需求，但跳过等待/人工确认环节”；并发强制调用 Deep Research 并落盘到 `step1_research_reports/`，将研究结果注入澄清问题生成。
- Step2：辩论前强制并发调用 Deep Research，保存到 `step2_research_reports/` 并生成 `step2_deep_research_results.md`；澄清问题仅在 `use_clarification=true` 时注入辩论提示词，否则不注入。

### 17:35 v2 Step3/Step4 对齐（全局Guideline + 用户画像）
- Step3：重映射为生成 `agent_guidelines.json`（全局 guideline，数量控制），基于 Step2 宏观目标；由 GlobalRulesAgent 强制 Deep Research。
- Step4：重映射为生成 `agent_user_profiles.json`（用户分群+persona），基于 Step2 宏观目标并调用 Deep Research；mock 模式提供最小可用兜底产物避免为空。

### 18:20 v2 Step3/Step4 合规校验接入 + Step3 纳入全局术语库
- Step3：按 v2 设计纳入 `GlobalRulesAgent + GlossaryAgent`，新增可选并行开关 `concurrency.enable_step3_globalrules_glossary_parallel`；落盘 `agent_guidelines.json` + `step3_glossary_master.json`。
- Step3/Step4：接入 `ComplianceCheckAgent` 结果校验（产物落盘后立即校验，不通过直接失败），输出 `*_compliance_report.json`。
- 清理：删除未再使用的 legacy Step/Agent 与配置（`dimension_analysis`/`workflow_development`/`global_rules_check`、`ProcessAgent`/`QualityAgent` 及对应 YAML）。

### 19:10 v2 Step5/Step6 对齐（分支挖掘 + 边缘场景注入）
- Step5：新增 `step5_branch_sop_parallel`，按 Step2 主干节点派生二级分支子任务（并发可选，受 `max_parallel_step5_nodes` 控制），产出：
  - `step5_journeys_{node_id}.json`（二级 branch journey，5-10 states）
  - `step5_guidelines_{node_id}.json`（局部 sop_only guidelines，并对全局 guideline 做启发式去重剔除）
  - `step5_glossary_{node_id}.json`、`step5_tools_{node_id}.json`、`step5_summary_{node_id}.md`
  - 并在 Step5 结束后接入 `ComplianceCheckAgent` 门控校验
- Step6：基于 Step5 的局部 guidelines 生成“单节点 edge journey”（1 state），并将边缘场景转为局部 guideline 补丁注入对应 `step5_guidelines_{node_id}.json`；并发可选（`max_parallel_edge_cases`），结束后接入 `ComplianceCheckAgent` 门控校验。
- 清理：删除已不再使用的 `src/mining_agents/steps/config_assembly.py`（原 Step5 组装实现）。

### 19:25 Step6 启发式去重补齐
- Step6：边缘场景 guideline 注入前，读取 Step3 `agent_guidelines.json`，对注入 guideline 的 condition/action 做规范化比较，若与全局重复则跳过注入（统计写入 `step6_supplementary_rules.json` 的 `skipped_by_global_dedupe`）。

### 19:40 Step8 可选自动修复与返工门控
- Step8：新增可选 `step8_auto_fix_json.enabled`，当 JSON 解析失败但 `json_repair` 可修复时，可回写修复后的 JSON 到原文件（默认关闭）。
- Step8：新增可选 `step8_quality_gate.enabled`，基于可解释质量分 `quality_score` 触发返工回跳（默认关闭）；StepManager 支持 Step8 返工回跳。

### 19:55 Step2/Step5 可选 canned responses 挖掘与落盘
- Step2：新增可选 `step2_canned_responses.json`（当业务描述包含合规/隐私/退订等信号时生成），作为全局预审批话术候选，供 Step3 随全局 guideline 一并输出。
- Step3：若 Step2 提供 canned responses，则额外落盘 `agent_canned_responses.json`，并在 Step7 归档到 `01_agent_rules/agent_canned_responses.json`。
- Step5：二级分支 `sop_guidelines.json` 增加 `sop_canned_responses`（若有需要则生成）并在局部 guideline 中通过 `bind_canned_response_ids` 绑定。

### 11:30 Step7逻辑优化与Agent交互次数动态配置
- **任务描述**：确认并优化step3-step8的代码逻辑，确保符合设计要求
- **核心问题**：
  1. Step7直接调用Step5逻辑重新生成配置，不符合"整合而非重新生成"的要求
  2. Agent最大交互次数固定为5，未根据任务复杂度动态设置
  
- **优化内容**：
  
  1. **Step7逻辑重写** - 改为文件整合模式：
     - 重写 `step7_config_assembly.py`，不再调用 `config_assembly_handler`
     - 现在只做文件整合和目录重组：
       - 从Step3-Step6收集已生成的文件
       - 按照parlant目录结构重组（00_agent_base/、01_agent_rules/、02_journeys/、03_tools/）
       - 不重新生成内容，只做文件移动和重命名
       - 生成整合报告，记录整合来源和问题
  
  2. **Agent交互次数动态配置**：
     - 为不同类型Agent配置合适的 `react_max_rounds`：
       - ProcessAgent: 8轮（流程设计较复杂，需要多轮推理）
       - GlossaryAgent: 6轮（术语提取相对简单）
       - QualityAgent: 10轮（质量检查需要多维度分析）
       - GlobalRulesAgent: 7轮（规则设计中等复杂度）
     - 在各agent配置文件中添加 `react_max_rounds` 和 `enable_thinking` 配置
  
  3. **代码逻辑确认**：
     - ✅ Step3-Step5输出标准parlant结构文档
     - ✅ Step7整合之前步骤的文件，不重新生成
     - ✅ Step8基于Step7输出进行验证（JSON解析、Schema校验、状态机检查、跨文件一致性检查）
  
- **修改文件**：
  - `src/mining_agents/steps/step7_config_assembly.py` - 完全重写
  - `egs/v0.1.0_minging_agents/config/agents/process_agent.yaml` - 添加react_max_rounds=8
  - `egs/v0.1.0_minging_agents/config/agents/glossary_agent.yaml` - 添加react_max_rounds=6
  - `egs/v0.1.0_minging_agents/config/agents/quality_agent.yaml` - 添加react_max_rounds=10
  - `egs/v0.1.0_minging_agents/config/agents/global_rules_agent.yaml` - 添加react_max_rounds=7

- **验证结果**：
  - ✅ Step7不再重新生成配置，只做文件整合
  - ✅ Agent交互次数根据任务复杂度动态配置
  - ✅ 输出结构符合parlant规范
  - ✅ 测试代码运行正常，Step1-Step3输出目录已创建

### 10:30 添加SOP数量限制到提示词配置
- **任务描述**：在提示词中对一级、二级、三级SOP的数量进行限制，分别限定为10、10、30个
- **修改内容**：
  1. **debate_prompts.yaml**：
     - 在 moderator 的 sys_prompt_template 中添加【SOP 数量限制】说明
     - 在 judge_prompt 中添加【SOP 数量限制】说明
  
  2. **coordinator_agent.yaml**：
     - 在 llm_task_breakdown 提示词的整合要求中添加第6条"SOP 数量限制"
  
  3. **process_agent.yaml**：
     - 在 design_process 提示词中添加【SOP 数量限制】说明
  
  4. **config_assembler_agent.yaml**：
     - 在 assemble_config 提示词的校验要求中添加第5条"SOP 数量限制校验"
  
  5. **journey.md**：
     - 更新三层SOP架构说明，添加数量限制说明
     - 添加重要提示：SOP数量限制必须严格遵守，超过限制将导致配置校验失败

- **SOP数量限制规则**：
  - 一级主SOP（主干层）：最多 10 个
  - 二级分支SOP（适配层）：最多 10 个
  - 三级子弹SOP（补全层）：最多 30 个

## 2026-04-01

### 22:35 优化第二步骤多模型辩论的主题输入和输出产物
- **问题描述**：
  - 第二步骤的多模型辩论直接把用户的业务需求输入给模型，未明确这是业务目标
  - 辩论输出产物不明确，缺少宏观指导文档
  - 辩论次数未在配置文件中可配置
- **优化内容**：
  1. **优化辩论主题输入方式**：
     - 修改 `debate_prompts.yaml`，将"讨论主题"改为"用户业务目标"
     - 明确告诉模型这是用户的业务目标，需要围绕业务目标讨论主SOP/分支SOP/边缘场景/规则/工具/观测条件等的设计方向和需要关注的要点
     - 为每个角色（领域专家、客户倡导者、需求分析师、风险控制者）明确关注点，聚焦于主SOP、分支SOP、边缘场景、规则、工具、观测条件等维度
  
  2. **明确辩论输出产物**：
     - 辩论输出产物改为宏观指导文档，包含主题/方法论/每个分要点需要考虑的事项
     - 更新 `debate_summary` 配置，输出内容围绕主SOP设计方法论、分支SOP设计方法论、边缘场景设计方法论、规则设计方法论、工具集成方法论、观测条件设计方法论
     - 修改辩论总结部分，明确标注为"最终决策（宏观指导文档）"
  
  3. **辩论次数可配置**：
     - 在 `system_config.yaml` 中添加 `debate.max_rounds` 配置项，默认值为1
     - 在 `system_config.yaml` 中添加 `debate.max_iters_per_agent` 配置项，默认值为3
     - 修改 `dimension_analysis.py` 中的 `_run_agentscope_debate` 和 `_generate_mock_debate_transcript` 函数，从系统配置中读取辩论次数
  
- **修改文件**：
  - `egs/v0.1.0_minging_agents/config/agents/debate_prompts.yaml`
  - `egs/v0.1.0_minging_agents/config/system_config.yaml`
  - `src/mining_agents/steps/dimension_analysis.py`
  
- **验证结果**：
  - ✅ 辩论主题明确为"用户业务目标"，不再是直接把用户需求输入
  - ✅ 辩论围绕主SOP/分支SOP/边缘场景/规则/工具/观测条件等的设计方向进行讨论
  - ✅ 辩论输出产物是宏观指导文档，包含主题/方法论/每个分要点需要考虑的事项
  - ✅ 辩论轮数设置为1轮，符合配置要求

### 21:15 修复提示词中的业务无关示例问题（第一次修复 - 已废弃）
- ~~**问题描述**：step4用户画像中出现航班、航空等与日本保险业务无关的内容，原因是提示词中使用了航空业务示例误导模型~~
- ~~**修复文件**：使用保险业务示例替换航空业务示例~~
- **问题**：此方法缺乏通用性，不适用于其他行业

### 21:45 重新修复提示词，确保通用性和业务导向（最终方案）
- **核心问题**：提示词中的具体行业示例会误导模型，导致输出偏离用户实际业务场景
- **修复原则**：
  - 所有示例改为通用占位符或通用描述，不涉及具体行业
  - 在每个agent提示词开头添加【重要提示 - 业务导向原则】
  - 强调所有输出必须严格基于用户传入的【业务描述】
  - 明确示例仅供参考格式，禁止照抄具体业务内容
- **修复文件**：
  - `process_agent.yaml`：
    - 将"初始 - 需求分析"改为"初始 - 用户需求确认"（更通用）
    - 添加业务导向原则说明
    - 增强主题约束检查清单，强调示例仅供参考
  - `glossary_agent.yaml`：
    - 将所有具体行业示例改为通用占位符
    - 添加业务导向原则说明
    - 强调术语必须围绕【业务描述】展开
  - `quality_agent.yaml`：
    - 将"insurance_greet_001"改为"{业务前缀}_greet_001"
    - 添加业务导向原则说明
  - `global_rules_agent.yaml`：
    - 将所有"insurance"前缀改为"{业务前缀}"
    - 添加业务导向原则说明
  - `coordinator_agent.yaml`：
    - 将"计算保费工具、风险评估工具"改为"数据查询工具、业务计算工具、外部系统集成工具"
    - 将"等待期、免责条款、保额、保费"改为"产品术语、业务流程术语、行业专业术语"
- **业务导向原则**（所有agent统一添加）：
  ```
  【重要提示 - 业务导向原则】
  本系统的核心原则：**所有输出必须严格基于用户传入的【业务描述】**。
  - 下文中的所有示例、模板、占位符仅用于展示字段结构和格式要求
  - 实际内容必须根据【业务描述】中的具体业务场景、行业特点、产品类型、流程规范自行撰写
  - **禁止照抄示例中的具体业务内容**，必须根据用户的实际业务需求生成配置
  - 若【业务描述】与示例不一致，以【业务描述】为准
  ```
- **变量传递验证**：
  - ✅ 所有agent（process_agent、glossary_agent、quality_agent、global_rules_agent）都正确传递了core_goal、business_desc、industry变量
  - ✅ 所有步骤（workflow_development、global_rules_check）都正确传递了这些变量
  - ✅ requirement_analyst_agent中的示例都是通用的，不会误导模型
- **影响范围**：所有使用这些agent配置的步骤（step3、step4等）
- **预期效果**：系统能够适应各种行业，严格按照用户传入的业务描述生成配置，不再被示例误导

### 20:30 新增时效分析与统计功能
- **新增模块**：`src/mining_agents/utils/performance_tracker.py`
  - 实现`PerformanceTracker`单例类，用于统计Agent执行时间、模型调用次数等性能指标
  - 支持Agent级别统计（总时间、平均时间、调用次数、LLM调用次数）
  - 支持步骤级别统计（执行时长、状态、Agent调用记录）
  - 支持全局统计（总执行时长、总调用次数）
  - 提供报告生成功能（JSON格式）和控制台摘要输出
- **集成修改**：
  - `base_agent.py`：在`call_llm`方法中记录LLM调用次数
  - `agent_orchestrator.py`：在`execute_agent`方法中记录Agent执行时间
  - `step_manager.py`：在`run_step`方法中记录步骤执行时间
  - `cli.py`：在系统启动时开始全局追踪，在结束时生成并保存性能报告
- **输出产物**：
  - 控制台输出：执行摘要、Agent统计、步骤统计
  - JSON报告：`output/performance_report.json`
- **测试验证**：创建`test_performance_tracker.py`验证功能正常

### 19:30 日志问题分析与提示词优化
- **process_agent.yaml**：添加中文输出强制要求和主题约束检查清单
  - 新增「所有输出必须使用中文」强制要求
  - 新增「严禁引入业务描述未涉及的行业或场景用词」约束
  - 新增语言规范说明，仅允许ID命名和技术术语使用英文
- **问题分析结论**：
  1. step3/step5输出结构问题：v2迁移期架构问题，当前step3-5复用旧5步法实现
  2. model-id错误：`Qwen/Qwen3.5-27B`模型名称在某些API调用时不被支持，需确认API兼容性
  3. WARNING `Using default rules`：GlobalRulesAgent执行失败后的降级策略，已正确处理
  4. ERROR `[Errno 22] Invalid argument`：系统调用错误，可能是文件路径或并发问题

### 18:00 修复辩论 Agent 输出语言问题
- `debate_prompts.yaml`：为所有辩论角色（领域专家、客户倡导者、需求分析师、风险控制者）和主持人的系统提示词添加「重要：请使用中文回答所有问题」的明确语言约束。
- `dimension_analysis.py`：同步更新代码中默认的 fallback 提示词，同样添加中文回答约束，确保配置文件加载失败时也能保持语言一致性。

### 17:10 force-rerun 功能增强：删除原输出目录（已回退）
- ~~`step_manager.py`：当使用 `--force-rerun` 参数时，在执行步骤前自动删除该步骤的原输出目录，确保干净重跑。~~
- ~~添加 `shutil` 导入，在 `run_step` 方法中增加目录删除逻辑，失败时抛出异常并记录错误日志。~~
- **已回退**：保留原有文件夹，仅通过状态检查跳过已完成的步骤。

### 17:15 新增 --clean-output 参数
- `cli.py`：新增 `--clean-output` 命令行参数，默认 `false`。
- 当设置为 `true` 时，在执行前删除整个输出目录，实现干净重跑。
- 与 `--force-rerun` 的区别：`--force-rerun` 只控制步骤重跑逻辑，不删除文件；`--clean-output` 直接删除整个输出目录。

## 2026-04-01

### 16:58 小改动优化（中文化+指代明确+JSON修复注入）
- `debate_prompts.yaml`：将提示词正文与示例文案统一改为中文，保留原有结构与字段不变。
- `coordinator_agent.yaml`：在输出规则中补充 JSON 修复策略（`json_repair + 1 次 LLM`，仅一轮）。
- `config_assembler_agent.yaml`：将 JSON 修复与重试描述改为“仅一轮修复”，避免多次重试导致行为不稳定。

### 17:05 JSON Schema 校验显式注入
- `coordinator_agent.yaml`：将 JSON 修复链路明确为 `json_repair ->（可选 LLM 1 次）-> jsonschema 校验`，失败即返回错误不重试。
- `config_assembler_agent.yaml`：补充 Schema 校验为硬门控：Schema 不通过不再触发多轮修复，直接失败并记录原因。

### 15:10 运行参数 YAML 快照落盘
- `engine.py`：新增运行时配置快照逻辑，启动引擎时将 `config_path` 所在配置目录下全部 `*.yaml/*.yml` 递归复制到输出目录 `run_config_snapshot/`。
- 同步生成 `run_config_snapshot/manifest.json`，记录源目录、快照目录与文件清单，便于按“本次运行”追溯实际配置参数。

### 14:55 ProcessAgent JSON 二次修复链路增强
- `process_agent.py`：当 `repair_json` 与首尾对象提取解析失败后，新增一次“大模型 JSON 修复”流程。
- 修复提示词注入原始要求（task/business_desc/step2_atomic_tasks/step1_structured_requirements/原始执行提示词）与当前待修复 JSON 文本，要求仅返回合法 JSON 对象，降低 REAL 模式下解析失败率。

### 14:30 Step2 辩论未一致的终局裁决
- Step2 多模型辩论未达成一致时继续发起下一轮；达到最大轮数仍未一致则追加一次主持人“终局裁决”，产出最终结论并写入 transcript/返回结果，避免使用预置兜底导致偏离主题目标。
- `tests/test_debate_function.py`：Mock 辩论新增断言覆盖“终局裁决”路径，并移除控制台不兼容符号（避免 gbk 环境 UnicodeEncodeError）。

### （续）Glossary 提示词去领域偏置
- `glossary_agent.yaml`：去掉日语与保险强绑定示例；分类改为纯维度说明；语言策略改为「与业务描述一致、禁止硬塞外语」；`agent_id` 示例改为中性占位；反泛化示例改为与行业无关的写作要求。

### 12:30 Step3 Glossary 出现航空术语根因与提示词修复
- **结论**：主要为 `glossary_agent.yaml` 中 `design_glossary` 提示词问题——字段示例使用 `airline_term_001`，分类与「必须严格遵守」的 JSON 样例中写死经济舱/商务舱/直飞航班等，模型易照抄；非 Agent 无故「跑偏」。
- **修改**：去除航空硬编码样例，改为中性占位说明；强调术语必须与【业务描述】/`{industry}` 一致并明确禁止无关行业用词；分类与反泛化示例改为保险/外呼向；`term_id` 规范去掉 airline 正向暗示。

## 2026-03-31

### 21:40 real单步联调（Step3-8）与提速修复
- 按 `real + skip-clarification + force-rerun + debug + max-parallel=1` 完成 Step3→Step8 单步执行与逐步核验。
- 为加速测试，降低 Deep Research 搜索负载：`system_config.yaml` 中 `deep_research.max_depth/max_iters` 调整为 `1/1`，并将 `process/global_rules/glossary/quality` 四个 agent 的 Deep Research 提示词收敛为 1 次核心搜索。
- 修复 Step5/Step7 组装与校验链路：在 `config_assembly.py` 增加 Step3 Journey/Guideline 结构归一化（`journeys -> sop.json`、`guidelines -> sop_guidelines.json`）并在组装前清理旧 `parlant_agent_config`，避免历史残留污染 Step8 结果。
- 修复 Step8 单步执行时 `main_sop_backbone` 上下文缺失问题：在 `step8_validation.py` 增加从 Step2 产物自动回填主干 SOP 的回退加载逻辑。
- 最终结果：`output/step8_validation/result.json` 为 `passed: true`（`json_parse_errors=0, schema_errors=0, journey_schema_errors=0, main_backbone_issues=0`）。

### 20:20 清理无用 step stub 文件
- 检查 `src/mining_agents/steps` 下 `step*.py` 的全局引用关系。
- 保留已在 `engine.py` 注册使用的正式实现：`step2_objective_alignment_main_sop.py`、`step6_edge_cases.py`、`step7_config_assembly.py`、`step8_validation.py`。
- 删除未被任何模块引用的无用文件：`step6_edge_cases_stub.py`、`step7_config_assembly_stub.py`、`step8_validation_stub.py`。

### 20:12 Deep Research 编码根因修复
- 从根因修复 `gbk` 编码异常：不再通过字符映射/降级替换文本内容，改为在 `DeepResearchTool` 初始化时统一强制 `stdout/stderr` 使用 `utf-8`（`errors=backslashreplace`）并设置 `PYTHONUTF8`、`PYTHONIOENCODING`。
- 清理 `deep_research_agent/utils.py` 中大量 `char_map` 方案，改为仅移除 BOM/零宽字符，保留原始 Unicode 内容，避免信息损失。
- 新增回归测试 `test_force_utf8_stdio_on_init`，覆盖 UTF-8 I/O 强制配置行为。

### 15:50 单步Stage测试结果（v2设计文档验证）

#### Stage 1 测试 - ✅ 成功
- 使用real模式、无并发、日本共荣保险营销挽留场景
- 成功生成7个澄清问题，涵盖合规、核心流程、风险评估、系统集成、目标受众、术语表等维度
- 问题按优先级分类（高/中/低），符合设计文档v2要求
- 输出文件：step1_clarification_questions.md、step1_structured_requirements.md、result.json

#### Stage 2 测试 - ⚠️ 部分成功
- 主SOP主干生成成功：6个节点（node_000到node_005），符合5-9节点要求
- 输出文件：global_objective.md、step2_main_sop_backbone.json、step2_business_objectives.md
- **发现的问题**：
  1. ❌ 辩论工具错误：所有Agent发言失败，错误"The tool function must return a ToolResponse object"
  2. ❌ 编码问题：'gbk'编码无法处理emoji字符（🔴📊等）
  3. ❌ API参数错误：thinking模式下tool_choice参数不兼容
  4. ⚠️ 主SOP内容通用化：未充分体现日本保险挽留场景特点

#### Stage 3 测试 - ❌ 执行超时
- 执行过程中终端连接丢失
- **发现的问题**：
  1. ❌ 实现与设计文档v2不一致：
     - 设计文档v2：Step 3为"全局规则与术语库挖掘"
     - 当前实现：Step 3为"工作流并行开发"（ProcessAgent + GlossaryAgent + QualityAgent）
  2. ❌ 编码问题：gbk编码无法处理Unicode字符
  3. ❌ 工具返回类型错误：与Stage 2相同的辩论工具错误
  4. ❌ 配置文件缺失：多个Agent配置文件未找到

#### 关键发现
1. **系统尚未完全迁移到v2架构**：当前实现仍是旧的5步法，与设计文档v2的8步法不一致
2. **辩论机制存在严重缺陷**：工具返回类型不匹配，导致所有辩论失败
3. **编码问题普遍存在**：gbk编码无法处理Unicode字符，影响多个功能
4. **API兼容性问题**：thinking模式与tool_choice参数不兼容

### 14:30 测试结果
- 成功启动主程序，运行 Step 1 完成
- 生成了详细的需求澄清问题清单（step1_clarification_questions.md）
- 生成了结构化需求规格说明（step1_structured_requirements.md）
- API 连接正常，所有调用返回 200 OK
- 系统使用 ReAct 模式分析需求，调用 deep_research 工具搜索日本保险行业合规要求
- 问题质量高，涵盖合规、流程、验证、目标群体、集成、术语和风险控制等关键方面

### 问题修复
- 修正了日志文件路径配置，避免权限问题
- 增加了 API 超时配置，提高系统稳定性

### 下一步计划
- 修复辩论工具的返回类型问题
- 解决gbk编码问题，改用utf-8编码
- 修复API参数兼容性问题
- 完成v2架构迁移，实现8步法流程
- 继续验证Stage 4-8的输出正确性