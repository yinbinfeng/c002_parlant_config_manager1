# Parlant Agent 工程化配置管理方案（关系设计合规版）
## 一、完整设计说明（补充关系设计合规性说明）
### 1. 方案总览
本方案是面向**Parlant框架**的多Agent工程化配置管理方案，专为人工维护、多业务线隔离、版本可控的生产场景设计。方案在原有基础上**严格遵循Parlant框架的「关系设计」要求**，完整实现了**排除关系（Exclusion）**和**依赖关系（Dependency）**，确保Agent的语境始终「狭窄且聚焦」，彻底解决了规则冲突、冗余激活的问题。

### 2. 核心设计目标（补充关系设计目标）
| 目标 | 详细说明 |
|------|----------|
| 多Agent彻底隔离 | 一个独立文件夹对应一个完整的业务Agent，Agent之间配置完全物理隔离，互不干扰 |
| 职责完全解耦 | 流程（SOP）、规则（Guideline）、观测（Observation）、工具（Tool）四大核心模块彻底拆分 |
| **关系设计严格合规** | **完整实现Parlant的排除关系与依赖关系，确保语境狭窄聚焦，避免规则冲突与冗余激活** |
| 人工维护友好 | 配置结构扁平、职责清晰，关系定义直观，人工维护无需写代码 |
| 高可扩展性 | 新增Agent、SOP、规则、观测、工具均为「新增文件夹/文件」模式 |

### 3. 关系设计合规性说明（核心补充）
本方案严格遵循Parlant框架的关系设计要求，具体实现如下：
#### （1）排除关系（Exclusion）
- **设计目的**：当两个Guideline的条件同时匹配（冲突）时，让其中一个Guideline不生效，保持语境聚焦，避免Agent同时遵循冲突的规则。
- **实现方式**：在Guideline配置中增加`exclusions`字段，指定需要排除的其他Guideline ID；构建脚本中调用Parlant SDK的`await guideline_a.exclude(guideline_b)`方法，确保冲突时只有优先级高的Guideline生效。
- **示例场景**：
  - 专家导向规则（`for_experts`）：用户使用专业术语时，用技术深度回复
  - 新手导向规则（`for_beginners`）：用户看起来是新手时，简化回复并用具体例子
  - 冲突处理：`await for_beginners.exclude(for_experts)`，当两个规则同时匹配时，新手导向规则生效，排除专家导向规则

#### （2）依赖关系（Dependency）
- **设计目的**：一个Guideline只有在另一个Guideline或Observation已经激活（铺垫）的情况下才会激活，建立基于主题的指导层级，避免规则过早或错误激活，保持语境狭窄。
- **实现方式**：
  1. 补充**Observation配置**：在Agent全局配置和SOP配置中增加`observations`字段，定义观测条件；
  2. 在Guideline配置中增加`dependencies`字段，指定依赖的Guideline ID或Observation ID；
  3. 构建脚本中调用Parlant SDK的`await guideline.add_dependencies([...])`方法，确保Guideline只有在依赖项激活后才会生效。
- **示例场景**：
  - 欺诈嫌疑观测（`suspects_fraud`）：用户怀疑银行卡有未授权交易
  - 交易处置规则（`handle_transaction`）：用户想要对交易采取行动
  - 依赖处理：`dependencies=[suspects_fraud]`，只有在欺诈嫌疑观测激活后，交易处置规则才会生效

### 4. 整体架构分层逻辑（补充观测层）
本方案采用6层分层架构，从底层到上层依次为：
1. **全局基础层（00_agent_base）**：所有Agent共享的底层基础配置。
2. **全局规则层（01_global_rules）**：所有Agent共享的通用规则、观测。
3. **Agent业务层（02_agents）**：方案核心层，每个子文件夹对应一个独立的业务Agent，内聚该Agent的专属基础信息、全局规则、观测、所有业务SOP。
4. **SOP业务层（Agent内的journeys）**：每个SOP子文件夹内聚该SOP的专属流程、规则、观测。
5. **公共工具层（03_common_tools）**：所有Agent共享的工具库。
6. **自动化构建层（automation）**：仅保留核心构建脚本，支持指定单个Agent独立构建，**完整实现关系绑定逻辑**。

---

## 二、完整目录结构（补充观测配置）
```
parlant_agent_config/
├── 00_agent_base/                # 全局基础层
│   ├── global_observability.json
│   └── global_glossary/
│       ├── core_terms.json
│       └── industry_terms.json
├── 01_global_rules/               # 全局规则层（补充观测配置）
│   ├── global_guidelines.json     # 全局Guideline（含排除/依赖关系）
│   ├── global_observations.json   # 【新增】全局Observation
│   └── global_canned_responses.json
├── 02_agents/                     # Agent业务层
│   ├── medical_customer_service_agent/
│   │   ├── agent_metadata.json
│   │   ├── agent_global_guidelines.json # Agent全局Guideline（含关系）
│   │   ├── agent_global_observations.json # 【新增】Agent全局Observation
│   │   ├── agent_canned_responses.json
│   │   └── journeys/
│   │       ├── schedule_appt/
│   │       │   ├── sop.json       # SOP流程
│   │       │   ├── sop_guidelines.json # SOP专属Guideline（含关系）
│   │       │   └── sop_observations.json # 【新增】SOP专属Observation
│   │       ├── lab_results_query/
│   │       │   ├── sop.json
│   │       │   ├── sop_guidelines.json
│   │       │   └── sop_observations.json
│   │       └── cancel_appt/
│   │           ├── sop.json
│   │           ├── sop_guidelines.json
│   │           └── sop_observations.json
│   └── airline_customer_service_agent/
│       ├── agent_metadata.json
│       ├── agent_global_guidelines.json
│       ├── agent_global_observations.json
│       ├── agent_canned_responses.json
│       └── journeys/
│           ├── book_flight/
│           │   ├── sop.json
│           │   ├── sop_guidelines.json
│           │   └── sop_observations.json
│           └── change_flight/
│               ├── sop.json
│               ├── sop_guidelines.json
│               └── sop_observations.json
├── 03_common_tools/               # 公共工具层
│   ├── tool_get_upcoming_slots/
│   │   ├── tool_meta.json
│   │   └── tool_impl.py
│   ├── tool_get_lab_results/
│   │   ├── tool_meta.json
│   │   └── tool_impl.py
│   └── tool_load_flight_deals/
│       ├── tool_meta.json
│       └── tool_impl.py
└── automation/                     # 自动化构建层（补充关系绑定逻辑）
    └── build_agent.py             # 【核心优化】完整实现排除/依赖关系绑定
```

---

## 三、核心配置文件格式定义（补充关系与观测配置）
### 1. 全局观测配置
**文件路径**：`01_global_rules/global_observations.json`
> 定义所有Agent共享的观测条件，用于Guideline的依赖关系，避免规则过早激活。
```json
{
  "remark": "所有Agent共享的全局观测",
  "global_observations": [
    {
      "observation_id": "global_obs_user_angry_001",
      "condition": "用户表达不满、愤怒、抱怨，使用负面情绪词汇",
      "remark": "观测用户是否处于负面情绪状态，用于后续安抚规则的依赖"
    },
    {
      "observation_id": "global_obs_user_requests_human_001",
      "condition": "用户要求转人工、找客服、对自动回复不满意",
      "remark": "观测用户是否有转人工需求，用于后续转人工规则的依赖"
    }
  ]
}
```

### 2. 全局Guideline配置（补充排除/依赖关系）
**文件路径**：`01_global_rules/global_guidelines.json`
> 定义所有Agent共享的通用规则，**完整实现排除关系与依赖关系**，确保语境狭窄聚焦。
```json
{
  "remark": "所有Agent共享的全局Guideline（含排除/依赖关系）",
  "global_canned_responses": [
    {
      "canned_response_id": "global_cr_greet_001",
      "content": "您好～很高兴为您服务，请问您有什么需求呢？",
      "language": "zh-CN"
    },
    {
      "canned_response_id": "global_cr_soothe_001",
      "content": "非常抱歉给您带来不好的体验，您先消消气，我会尽力帮您解决问题的。",
      "language": "zh-CN"
    },
    {
      "canned_response_id": "global_cr_transfer_human_001",
      "content": "理解您的需求，您可以拨打我们的人工客服热线：400-XXXX-XXXX，服务时间：周一至周日 9:00-18:00。",
      "language": "zh-CN"
    }
  ],
  "global_guidelines": [
    {
      "guideline_id": "global_greet_001",
      "scope": "global",
      "condition": "用户首次对话、向代理打招呼（如你好、哈喽、早上好）",
      "action": "用友好的语气回应用户，主动询问用户的需求，保持简洁不超过2句话",
      "priority": 3,
      "composition_mode": "FLUID",
      "bind_canned_response_ids": ["global_cr_greet_001"],
      "exclusions": [],
      "dependencies": []
    },
    {
      "guideline_id": "global_soothe_001",
      "scope": "global",
      "condition": "用户处于负面情绪状态",
      "action": "先使用安抚模板话术安抚用户情绪，再询问用户的具体问题",
      "priority": 8,
      "composition_mode": "FLUID",
      "bind_canned_response_ids": ["global_cr_soothe_001"],
      "exclusions": ["global_greet_001"],
      "dependencies": ["global_obs_user_angry_001"]
    },
    {
      "guideline_id": "global_transfer_human_001",
      "scope": "global",
      "condition": "用户有转人工需求",
      "action": "使用转人工模板话术告知用户人工客服的联系方式",
      "priority": 10,
      "composition_mode": "STRICT",
      "bind_canned_response_ids": ["global_cr_transfer_human_001"],
      "exclusions": ["global_greet_001", "global_soothe_001"],
      "dependencies": ["global_obs_user_requests_human_001"]
    }
  ]
}
```

### 3. SOP专属观测配置
**文件路径**：`02_agents/medical_customer_service_agent/journeys/schedule_appt/sop_observations.json`
> 定义仅该SOP生效的观测条件，用于SOP专属Guideline的依赖关系。
```json
{
  "sop_id": "schedule_appt_001",
  "remark": "仅预约挂号SOP生效的专属观测",
  "sop_observations": [
    {
      "observation_id": "schedule_appt_obs_user_has_dept_001",
      "condition": "用户已明确选择具体科室",
      "remark": "观测用户是否已选择科室，用于后续医生推荐规则的依赖"
    },
    {
      "observation_id": "schedule_appt_obs_user_has_doctor_001",
      "condition": "用户已明确选择具体医生",
      "remark": "观测用户是否已选择医生，用于后续时段选择规则的依赖"
    }
  ]
}
```

### 4. SOP专属Guideline配置（补充排除/依赖关系）
**文件路径**：`02_agents/medical_customer_service_agent/journeys/schedule_appt/sop_guidelines.json`
> 定义仅该SOP生效的规则，**完整实现排除关系与依赖关系**，确保语境始终聚焦在预约挂号流程上。
```json
{
  "sop_id": "schedule_appt_001",
  "remark": "仅预约挂号SOP生效的专属规则（含排除/依赖关系）",
  "sop_canned_responses": [
    {
      "canned_response_id": "schedule_appt_cr_dept_list_001",
      "content": "我们医院目前开放预约的科室有：内科、外科、儿科、妇科、眼科、口腔科、皮肤科、耳鼻喉科，请问您想要预约哪个科室的号呢？",
      "language": "zh-CN",
      "bind_guideline_ids": ["schedule_appt_dept_guide_001"]
    },
    {
      "canned_response_id": "schedule_appt_cr_doctor_recommend_001",
      "content": "为您推荐{dept}科室的以下医生：{doctor_list}，请问您想要预约哪位医生的号呢？",
      "language": "zh-CN",
      "bind_guideline_ids": ["schedule_appt_doctor_recommend_001"]
    },
    {
      "canned_response_id": "schedule_appt_cr_success_001",
      "content": "🎉 您的预约已成功！预约号：{appt_id}，就诊时间：{appt_time}，就诊科室：{dept}，就诊医生：{doctor_name}。请您在就诊当天携带有效身份证件，提前30分钟到医院门诊大厅取号，祝您就诊顺利！",
      "language": "zh-CN"
    }
  ],
  "sop_scoped_guidelines": [
    {
      "guideline_id": "schedule_appt_dept_guide_001",
      "scope": "sop_only",
      "condition": "用户进入本SOP后，未明确选择科室、选择的科室不存在、科室名称表述模糊",
      "action": "使用科室列表模板话术引导用户选择，若科室不存在，建议用户选择相近科室或拨打人工客服咨询",
      "priority": 4,
      "composition_mode": "FLUID",
      "bind_canned_response_ids": ["schedule_appt_cr_dept_list_001"],
      "exclusions": [],
      "dependencies": []
    },
    {
      "guideline_id": "schedule_appt_doctor_recommend_001",
      "scope": "sop_only",
      "condition": "用户已选择科室，需要推荐医生",
      "action": "使用医生推荐模板话术，优先推荐职称高、可预约时段多的医生",
      "priority": 5,
      "composition_mode": "FLUID",
      "bind_canned_response_ids": ["schedule_appt_cr_doctor_recommend_001"],
      "exclusions": ["schedule_appt_dept_guide_001"],
      "dependencies": ["schedule_appt_obs_user_has_dept_001"]
    },
    {
      "guideline_id": "schedule_appt_time_verify_001",
      "scope": "sop_only",
      "condition": "用户选择的预约时段已约满、不在可预约范围内、医院停诊",
      "action": "友好告知用户该时段无法预约，推荐其他可预约时段",
      "priority": 6,
      "composition_mode": "FLUID",
      "exclusions": ["schedule_appt_doctor_recommend_001"],
      "dependencies": ["schedule_appt_obs_user_has_doctor_001"]
    }
  ]
}
```

---

## 四、核心优化后的构建脚本（完整实现关系绑定）
**文件路径**：`automation/build_agent.py`
> 核心优化：
> 1. 新增Observation加载逻辑；
> 2. **完整实现排除关系绑定**：调用`await guideline_a.exclude(guideline_b)`；
> 3. **完整实现依赖关系绑定**：调用`await guideline.add_dependencies([...])`；
> 4. 支持依赖Guideline或Observation。
```python
import asyncio
import json
import sys
from pathlib import Path
from parlant import sdk as p

# 根目录路径
ROOT_PATH = Path(__file__).parent.parent.resolve()
sys.path.append(str(ROOT_PATH))

# 读取JSON配置文件
def read_config(file_path):
    full_path = Path(file_path).resolve()
    if not full_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {full_path}")
    with open(full_path, "r", encoding="utf-8") as f:
        return json.load(f)

# 构建单个Agent的核心逻辑
async def build_single_agent(agent_folder_name):
    # 校验Agent文件夹是否存在
    agent_folder_path = ROOT_PATH / "02_agents" / agent_folder_name
    if not agent_folder_path.exists() or not agent_folder_path.is_dir():
        print(f"❌ Agent文件夹不存在: {agent_folder_name}")
        sys.exit(1)
    
    print(f"\n===== 开始构建Agent: {agent_folder_name} =====")
    
    # 资产实例池：存储当前Agent的所有资产实例
    instance_pool = {
        "tools": {},
        "canned_responses": {},
        "observations": {},
        "guidelines": {},
        "journeys": {}
    }

    # 1. 加载Agent专属基础信息
    agent_meta = read_config(agent_folder_path / "agent_metadata.json")
    print(f"✅ 加载Agent基础信息完成: {agent_meta['agent_name']}")

    # 2. 初始化Parlant Server与Agent实例
    async with p.Server(port=agent_meta.get("playground_port", 8800)) as server:
        agent = await server.create_agent(
            name=agent_meta["agent_name"],
            description=agent_meta["agent_description"]
        )
        print("✅ Agent实例创建成功")

        # 3. 加载全局共享基础资产
        # 3.1 加载全局领域术语表
        global_glossary_files = (ROOT_PATH / "00_agent_base/global_glossary").glob("*.json")
        for glossary_file in global_glossary_files:
            glossary_config = read_config(glossary_file)
            for term in glossary_config["terms"]:
                await agent.create_term(
                    name=term["name"],
                    description=term["description"],
                    synonyms=term.get("synonyms", [])
                )
        print("✅ 加载全局领域术语表完成")

        # 3.2 加载全局观测
        global_obs_config = read_config(ROOT_PATH / "01_global_rules/global_observations.json")
        for obs in global_obs_config["global_observations"]:
            obs_id = obs["observation_id"]
            obs_instance = await agent.create_observation(
                condition=obs["condition"]
            )
            instance_pool["observations"][obs_id] = obs_instance
        print("✅ 加载全局观测完成")

        # 3.3 加载全局通用规则
        global_rules_config = read_config(ROOT_PATH / "01_global_rules/global_guidelines.json")
        # 加载全局模板话术
        for cr in global_rules_config["global_canned_responses"]:
            cr_id = cr["canned_response_id"]
            cr_instance = await agent.create_canned_response(
                content=cr["content"],
                language=cr.get("language", "zh-CN")
            )
            instance_pool["canned_responses"][cr_id] = cr_instance
        # 先加载所有全局Guideline（暂不绑定关系）
        for guideline in global_rules_config["global_guidelines"]:
            guideline_id = guideline["guideline_id"]
            canned_responses = [
                instance_pool["canned_responses"][cr_id]
                for cr_id in guideline.get("bind_canned_response_ids", [])
                if cr_id in instance_pool["canned_responses"]
            ]
            tools = [
                instance_pool["tools"][tool_id]
                for tool_id in guideline.get("bind_tool_ids", [])
                if tool_id in instance_pool["tools"]
            ]
            guideline_instance = await agent.create_guideline(
                condition=guideline["condition"],
                action=guideline["action"],
                priority=guideline.get("priority", agent_meta["default_priority"]),
                composition_mode=getattr(p.CompositionMode, guideline["composition_mode"]),
                canned_responses=canned_responses,
                tools=tools
            )
            instance_pool["guidelines"][guideline_id] = guideline_instance
        # 【核心优化】绑定全局Guideline的排除关系与依赖关系
        for guideline in global_rules_config["global_guidelines"]:
            guideline_id = guideline["guideline_id"]
            guideline_instance = instance_pool["guidelines"][guideline_id]
            # 绑定排除关系
            for exclude_id in guideline.get("exclusions", []):
                exclude_instance = instance_pool["guidelines"].get(exclude_id)
                if exclude_instance:
                    await guideline_instance.exclude(exclude_instance)
                    print(f"🔗 绑定排除关系: {guideline_id} → {exclude_id}")
            # 绑定依赖关系（支持依赖Guideline或Observation）
            dependencies = []
            for dep_id in guideline.get("dependencies", []):
                dep_instance = instance_pool["guidelines"].get(dep_id) or instance_pool["observations"].get(dep_id)
                if dep_instance:
                    dependencies.append(dep_instance)
            if dependencies:
                await guideline_instance.add_dependencies(dependencies)
                print(f"🔗 绑定依赖关系: {guideline_id} → {[d for d in guideline.get('dependencies', [])]}")
        print("✅ 加载全局通用规则完成（含关系绑定）")

        # 3.4 加载公共共享工具
        tools_root = ROOT_PATH / "03_common_tools"
        tool_folders = [f for f in tools_root.iterdir() if f.is_dir()]
        for tool_folder in tool_folders:
            print(f"🔧 加载工具: {tool_folder.name}")
            meta_config = read_config(tool_folder / "tool_meta.json")
            tool_id = meta_config["tool_id"]
            impl_path = tool_folder / meta_config["implementation_file"]
            module_name = impl_path.stem
            module_path = str(impl_path.parent).replace(str(ROOT_PATH), "").replace("/", ".").strip(".")
            tool_module = __import__(
                f"{module_path}.{module_name}",
                fromlist=[meta_config["tool_name"]]
            )
            tool_func = getattr(tool_module, meta_config["tool_name"])
            instance_pool["tools"][tool_id] = tool_func
            await agent.create_observation(
                condition=" | ".join(meta_config["use_scenarios"]),
                tools=[tool_func]
            )
        print(f"✅ 加载公共工具完成，共加载 {len(instance_pool['tools'])} 个工具")

        # 4. 加载Agent专属全局配置
        # 4.1 加载Agent专属全局观测
        agent_obs_config = read_config(agent_folder_path / "agent_global_observations.json")
        for obs in agent_obs_config["agent_global_observations"]:
            obs_id = obs["observation_id"]
            obs_instance = await agent.create_observation(
                condition=obs["condition"]
            )
            instance_pool["observations"][obs_id] = obs_instance
        # 4.2 加载Agent专属全局规则
        agent_global_config = read_config(agent_folder_path / "agent_global_guidelines.json")
        for cr in agent_global_config["agent_global_canned_responses"]:
            cr_id = cr["canned_response_id"]
            cr_instance = await agent.create_canned_response(
                content=cr["content"],
                language=cr.get("language", "zh-CN")
            )
            instance_pool["canned_responses"][cr_id] = cr_instance
        # 先加载所有Agent专属Guideline（暂不绑定关系）
        for guideline in agent_global_config["agent_global_guidelines"]:
            guideline_id = guideline["guideline_id"]
            canned_responses = [
                instance_pool["canned_responses"][cr_id]
                for cr_id in guideline.get("bind_canned_response_ids", [])
                if cr_id in instance_pool["canned_responses"]
            ]
            tools = [
                instance_pool["tools"][tool_id]
                for tool_id in guideline.get("bind_tool_ids", [])
                if tool_id in instance_pool["tools"]
            ]
            guideline_instance = await agent.create_guideline(
                condition=guideline["condition"],
                action=guideline["action"],
                priority=guideline.get("priority", agent_meta["default_priority"]),
                composition_mode=getattr(p.CompositionMode, guideline["composition_mode"]),
                canned_responses=canned_responses,
                tools=tools
            )
            instance_pool["guidelines"][guideline_id] = guideline_instance
        # 【核心优化】绑定Agent专属Guideline的排除关系与依赖关系
        for guideline in agent_global_config["agent_global_guidelines"]:
            guideline_id = guideline["guideline_id"]
            guideline_instance = instance_pool["guidelines"][guideline_id]
            for exclude_id in guideline.get("exclusions", []):
                exclude_instance = instance_pool["guidelines"].get(exclude_id)
                if exclude_instance:
                    await guideline_instance.exclude(exclude_instance)
                    print(f"🔗 绑定Agent排除关系: {guideline_id} → {exclude_id}")
            dependencies = []
            for dep_id in guideline.get("dependencies", []):
                dep_instance = instance_pool["guidelines"].get(dep_id) or instance_pool["observations"].get(dep_id)
                if dep_instance:
                    dependencies.append(dep_instance)
            if dependencies:
                await guideline_instance.add_dependencies(dependencies)
                print(f"🔗 绑定Agent依赖关系: {guideline_id} → {[d for d in guideline.get('dependencies', [])]}")
        print("✅ 加载Agent专属全局配置完成（含关系绑定）")

        # 5. 加载Agent的所有业务SOP
        journeys_root = agent_folder_path / "journeys"
        sop_folders = [f for f in journeys_root.iterdir() if f.is_dir()]
        for sop_folder in sop_folders:
            print(f"\n📋 处理业务SOP: {sop_folder.name}")
            # 5.1 加载SOP专属观测
            sop_obs_config = read_config(sop_folder / "sop_observations.json")
            sop_obs_map = {}
            for obs in sop_obs_config["sop_observations"]:
                obs_id = obs["observation_id"]
                obs_instance = await agent.create_observation(
                    condition=obs["condition"]
                )
                instance_pool["observations"][obs_id] = obs_instance
                sop_obs_map[obs_id] = obs_instance
            # 5.2 加载SOP专属Guideline
            sop_guideline_config = read_config(sop_folder / "sop_guidelines.json")
            sop_id = sop_guideline_config["sop_id"]
            sop_cr_map = {}
            for cr in sop_guideline_config["sop_canned_responses"]:
                cr_id = cr["canned_response_id"]
                cr_instance = await agent.create_canned_response(
                    content=cr["content"],
                    language=cr.get("language", "zh-CN")
                )
                instance_pool["canned_responses"][cr_id] = cr_instance
                sop_cr_map[cr_id] = cr_instance
            # 先加载所有SOP专属Guideline（暂不绑定关系）
            sop_guideline_map = {}
            for guideline in sop_guideline_config["sop_scoped_guidelines"]:
                guideline_id = guideline["guideline_id"]
                canned_responses = [
                    sop_cr_map.get(cr_id) or instance_pool["canned_responses"][cr_id]
                    for cr_id in guideline.get("bind_canned_response_ids", [])
                    if sop_cr_map.get(cr_id) or cr_id in instance_pool["canned_responses"]
                ]
                tools = [
                    instance_pool["tools"][tool_id]
                    for tool_id in guideline.get("bind_tool_ids", [])
                    if tool_id in instance_pool["tools"]
                ]
                guideline_instance = p.Guideline(
                    condition=guideline["condition"],
                    action=guideline["action"],
                    priority=guideline.get("priority", agent_meta["default_priority"]),
                    composition_mode=getattr(p.CompositionMode, guideline["composition_mode"]),
                    canned_responses=canned_responses,
                    tools=tools
                )
                instance_pool["guidelines"][guideline_id] = guideline_instance
                sop_guideline_map[guideline_id] = guideline_instance
            # 【核心优化】绑定SOP专属Guideline的排除关系与依赖关系
            for guideline in sop_guideline_config["sop_scoped_guidelines"]:
                guideline_id = guideline["guideline_id"]
                guideline_instance = sop_guideline_map[guideline_id]
                for exclude_id in guideline.get("exclusions", []):
                    exclude_instance = sop_guideline_map.get(exclude_id) or instance_pool["guidelines"].get(exclude_id)
                    if exclude_instance:
                        await guideline_instance.exclude(exclude_instance)
                        print(f"🔗 绑定SOP排除关系: {guideline_id} → {exclude_id}")
                dependencies = []
                for dep_id in guideline.get("dependencies", []):
                    dep_instance = sop_guideline_map.get(dep_id) or instance_pool["guidelines"].get(dep_id) or instance_pool["observations"].get(dep_id)
                    if dep_instance:
                        dependencies.append(dep_instance)
                if dependencies:
                    await guideline_instance.add_dependencies(dependencies)
                    print(f"🔗 绑定SOP依赖关系: {guideline_id} → {[d for d in guideline.get('dependencies', [])]}")
            print(f"✅ SOP {sop_id} 专属规则加载完成（含关系绑定）")

            # 5.3 加载SOP流程文件，创建Journey实例
            sop_config = read_config(sop_folder / "sop.json")
            journey = await agent.create_journey(
                title=sop_config["sop_title"],
                description=sop_config["sop_description"],
                conditions=sop_config["trigger_conditions"]
            )
            instance_pool["journeys"][sop_id] = journey
            bind_guideline_ids = sop_config["sop_guideline_mapping"]["sop_global_bind_guideline_ids"]
            for guideline_id in bind_guideline_ids:
                guideline = sop_guideline_map.get(guideline_id)
                if guideline:
                    await journey.add_guideline(guideline)
            print(f"✅ SOP {sop_id} 规则绑定完成")

            # 5.4 构建SOP状态机
            sop_states = sop_config["sop_states"]
            state_map = {}
            initial_state_config = sop_states[0]
            initial_guidelines = [
                sop_guideline_map.get(gid)
                for gid in initial_state_config.get("bind_guideline_ids", [])
                if sop_guideline_map.get(gid)
            ]
            current_state = await journey.initial_state.transition_to(
                chat_state=initial_state_config["instruction"] if initial_state_config["state_type"] == "chat" else None,
                tool_state=instance_pool["tools"].get(initial_state_config.get("bind_tool_id")) if initial_state_config["state_type"] == "tool" else None,
                guidelines=initial_guidelines
            )
            state_map[initial_state_config["state_id"]] = current_state

            for state_config in sop_states[1:]:
                for transition in state_config.get("transitions", []):
                    source_state = state_map.get(transition["target_state_id"])
                    if not source_state:
                        print(f"⚠️  SOP {sop_id} 状态 {state_config['state_id']} 引用的源状态不存在，跳过")
                        continue
                    state_guidelines = [
                        sop_guideline_map.get(gid)
                        for gid in state_config.get("bind_guideline_ids", [])
                        if sop_guideline_map.get(gid)
                    ]
                    state_canned = [
                        instance_pool["canned_responses"].get(cid)
                        for cid in state_config.get("bind_canned_response_ids", [])
                        if instance_pool["canned_responses"].get(cid)
                    ]
                    new_state = await source_state.transition_to(
                        chat_state=state_config["instruction"] if state_config["state_type"] == "chat" else None,
                        tool_state=instance_pool["tools"].get(state_config.get("bind_tool_id")) if state_config["state_type"] == "tool" else None,
                        condition=transition["condition"],
                        guidelines=state_guidelines,
                        canned_responses=state_canned
                    )
                    state_map[state_config["state_id"]] = new_state
                if state_config.get("is_end_state", False):
                    end_state = state_map.get(state_config["state_id"])
                    if end_state:
                        await end_state.transition_to(state=p.END_JOURNEY)
            print(f"✅ SOP {sop_config['sop_title']} 状态机构建完成")

        # 构建完成，保持服务运行
        print(f"\n🎉 Agent {agent_meta['agent_name']} 构建完成！")
        print(f"🔗 测试地址: http://localhost:{agent_meta.get('playground_port', 8800)}")
        await asyncio.Event().wait()

# 主函数入口
if __name__ == "__main__":
    if len(sys.argv) > 1:
        asyncio.run(build_single_agent(sys.argv[1]))
    else:
        print("❌ 请指定要构建的Agent文件夹名称，示例：")
        print("   python automation/build_agent.py medical_customer_service_agent")
        sys.exit(1)
```

---

## 五、关系设计合规性验证
本方案完全符合Parlant框架的关系设计要求，具体验证如下：
### 1. 排除关系验证
- **配置方式**：在Guideline配置中增加`exclusions`字段，指定需要排除的其他Guideline ID。
- **构建实现**：在构建脚本中调用`await guideline_a.exclude(guideline_b)`，确保冲突时只有优先级高的Guideline生效。
- **示例验证**：
  - 全局安抚规则（`global_soothe_001`）的`exclusions`字段包含`global_greet_001`，当用户处于负面情绪时，安抚规则生效，排除问候规则，避免Agent同时问候和安抚，保持语境聚焦。
  - 完全符合Parlant原始文档中的排除关系示例。

### 2. 依赖关系验证
- **配置方式**：
  1. 补充Observation配置，定义观测条件；
  2. 在Guideline配置中增加`dependencies`字段，指定依赖的Guideline ID或Observation ID。
- **构建实现**：在构建脚本中调用`await guideline.add_dependencies([...])`，支持依赖Guideline或Observation，确保Guideline只有在依赖项激活后才会生效。
- **示例验证**：
  - 全局安抚规则（`global_soothe_001`）的`dependencies`字段包含`global_obs_user_angry_001`，只有在观测到用户处于负面情绪后，安抚规则才会生效，避免规则过早激活，保持语境狭窄。
  - 完全符合Parlant原始文档中的依赖关系示例。

### 3. 语境狭窄聚焦验证
通过排除关系和依赖关系的组合使用，Agent的语境始终保持「狭窄且聚焦」：
- 排除关系避免了冲突规则同时生效；
- 依赖关系避免了规则过早或错误激活；
- 所有规则的激活都基于当前的对话语境，确保Agent的行为符合预期。