# Workflow Mining System - 对话工作流挖掘系统

基于论文《Turning Conversations into Workflows: A Framework to Extract and Evaluate Dialog Workflows for Service AI Agents》实现的完整框架。

## 📋 功能特性

### 核心模块

1. **程序元素检索 (Proc-Sim)**
   - 基于 SMST-DBSCAN 聚类的对话选择
   - 自动发现任意形状的簇，无需预设簇数量
   - 有效识别并过滤噪声点（异常对话）
   - 基于密度可达性，适合高维向量空间

2. **QA-CoT 工作流提取**
   - Guide-Implementer 问答交互
   - Single-Pass 策略（高效、稳定）
   - 自动识别前置条件、决策点、分支逻辑

3. **E2E 评估框架**
   - Bot 模拟对话评估
   - Macro/Micro Accuracy 指标计算
   - 与人类评估高度一致（κ=0.92）

## 🏗️ 目录结构

```
src/
├── retrieval/          # 对话检索模块
│   ├── procedure_extractor.py    # 程序元素提取
│   ├── proc_sim_retriever.py     # SMST-DBSCAN 检索器
│   └── embeddings.py             # Embedding 管理
├── extraction/         # 工作流提取模块
│   ├── guide_agent.py            # Guide Agent
│   ├── implementer_agent.py      # Implementer Agent
│   ├── qa_cot_generator.py       # QA-CoT 生成器
│   └── workflow_generator.py     # 工作流生成器
├── evaluation/         # E2E 评估模块
│   ├── scenario_decomposer.py    # 场景分解器
│   ├── bot_info_generator.py     # Bot 信息生成
│   ├── customer_bot.py           # 客户模拟器
│   ├── agent_bot.py              # 客服模拟器
│   └── success_evaluator.py      # 成功评估器
├── prompts/            # Prompt 模板管理
│   └── prompt_manager.py         # Prompt 管理器
└── utils/              # 工具函数
    ├── data_loader.py            # 数据加载器
    └── metrics.py                # 指标计算器
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install openai numpy asyncio
pip install sentence-transformers  # 如果使用本地 Embedding
pip install pandas openpyxl        # 如果需要处理 Excel
```

### 2. 配置系统

编辑 `config/system_config.yaml`:

```yaml
llm:
  provider: "openai"
  model: "gpt-4o"
  api_key_env: "OPENAI_API_KEY"

embedding:
  provider: "openai"
  model: "text-embedding-3-small"

retrieval:
  clustering_algorithm: "smst-dbscan"
  smst_dbscan:
    epsilon: 0.4
    min_pts: 5
  top_k: 75
```

### 3. 使用示例

#### 程序元素提取

```python
from src.retrieval import ProcedureExtractor, EmbeddingManager

# 初始化
embedding_mgr = EmbeddingManager(config)
extractor = ProcedureExtractor(llm_client)

# 提取单个对话
conversation = """
Customer: Hi, I'd like to return an item.
Agent: I can help with that. Can you provide your order ID?
Customer: Sure, it's 123456.
...
"""

element = await extractor.extract(conversation, conv_id="001")
print(f"Intent: {element.intent}")
print(f"Steps: {element.resolution_steps}")
```

#### SMST-DBSCAN 聚类检索

```python
from src.retrieval import ProcSimRetriever, SMSTDBSCANConfig

# 配置
config = SMSTDBSCANConfig(
    epsilon=0.4,
    min_pts=5,
    top_k=75
)

# 初始化检索器
retriever = ProcSimRetriever(embedding_mgr, config)

# 执行聚类
clusters = retriever.fit(embeddings)

# 选择代表性样本
representative_indices = retriever.select_representative_samples(
    embeddings, clusters, top_k=75
)
```

#### QA-CoT 工作流提取

```python
from src.extraction import QACoTGenerator, WorkflowGenerator

# 初始化
qa_generator = QACoTGenerator(llm_client=llm_client)
workflow_generator = WorkflowGenerator(llm_client=llm_client)

# Single-Pass 策略生成 QA-CoT
qa_result = await qa_generator.generate_single_pass(
    conversations=retrieved_conversations,
    max_questions=25
)

# 从 QA-CoT 生成工作流
workflow = await workflow_generator.generate_workflow(
    qa_result=qa_result,
    conversations=retrieved_conversations,
    intent="return_item"
)

# 保存工作流
workflow.save_to_file("output/workflow_return_item.json")
```

#### E2E 评估

```python
from src.evaluation import (
    ScenarioDecomposer,
    BotInfoGenerator,
    CustomerBot,
    AgentBot,
    SuccessEvaluator
)

# 1. 场景分解
decomposer = ScenarioDecomposer(llm_client)
scenarios = await decomposer.decompose_workflow(workflow.to_dict(), "return_item")

# 2. 生成 Bot 信息
bot_info_gen = BotInfoGenerator(llm_client)
bot_infos = await bot_info_gen.generate_batch(workflow.to_dict(), scenarios)

# 3. 对话模拟
customer_bot = CustomerBot(llm_client)
agent_bot = AgentBot(llm_client)

for scenario, bot_info in zip(scenarios, bot_infos):
    # 初始化 Bots
    customer_bot.initialize(bot_info.user_information)
    agent_bot.initialize(workflow.to_dict(), bot_info.system_information)
    
    # 模拟对话
    conversation = []
    while True:
        # Customer 发起请求
        customer_msg = await customer_bot.respond(agent_last_msg, conversation)
        conversation.append({"speaker": "customer", "text": customer_msg})
        
        # Agent 回应
        agent_msg = await agent_bot.respond(conversation)
        conversation.append({"speaker": "agent", "text": agent_msg})
        
        # 检查是否结束
        if "DONE" in agent_msg.upper():
            break
    
    # 4. 评估成功
    evaluator = SuccessEvaluator(llm_client)
    result = await evaluator.evaluate(
        workflow.to_dict(),
        bot_info.success_criteria,
        conversation
    )
    
    print(f"Scenario {scenario.scenario_id}: {'✓' if result.successful else '✗'}")
```

## 📊 预期性能

基于论文明 Table 1 的结果：

| Method | GPT-4o (ABCD) | GPT-4o (SynthABCD) |
|--------|---------------|--------------------|
| Basic | 46.74% | 68.91% |
| **QA-CoT (Ours)** | **58.55%** | **86.53%** |
| Improvement | +11.81% | +17.62% |

## 🔧 配置说明

### SMST-DBSCAN 参数调优

| 参数 | 推荐范围 | 说明 |
|------|----------|------|
| `epsilon` | 0.3-0.5 | 邻域半径，越大簇越多 |
| `min_pts` | 5-10 | 最小点数，越小簇越多 |
| `top_k` | 50-100 | 每个簇选择的代表性样本数 |

### LLM 选择建议

- **GPT-4o**: 最佳性能，适合生产环境
- **Sonnet-3.5**: 性价比高，推荐
- **DeepSeek-R1**: 经济实惠，适合实验

## 📝 License

MIT License

## 🙏 Acknowledgments

基于 Salesforce AI Research 的论文实现：
- Paper: [Turning Conversations into Workflows](https://arxiv.org/abs/2502.17321)
- Authors: Prafulla Kumar Choubey et al.
