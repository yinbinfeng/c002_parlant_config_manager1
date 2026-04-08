# Workflow Mining 项目完成总结

## 项目概述

基于论文《Turning Conversations into Workflows》实现的完整对话工作流挖掘系统，使用 AgentScope 框架构建多 Agent 协作系统。

**版本**: v1.0.0  
**完成日期**: 2026-03-20  
**核心特性**: SMST-DBSCAN 密度聚类 + QA-CoT 工作流提取

---

## ✅ 已完成功能模块

### 1. 设计文档 (Design Docs)

| 文件 | 大小 | 内容 |
|------|------|------|
| [`design_docs/mining_agents/01_project_overview.md`](design_docs/mining_agents/01_project_overview.md) | 52.9 KB | 项目概述、8 步流程设计、整体架构 |
| [`design_docs/mining_agents/02_system_architecture.md`](design_docs/mining_agents/02_system_architecture.md) | 50.7 KB | 详细系统架构、SMST-DBSCAN 算法推导、Prompt 中译 |

**核心内容**:
- ✅ SMST-DBSCAN 算法数学形式化（ε-邻域、核心样本、密度可达性）
- ✅ 参数配置建议表（epsilon: 0.3-0.5, min_pts: 5-10）
- ✅ 10 个 Prompt 模板中文翻译（Fig. 10-26）
- ✅ Guide-Implementer 多 Agent 协作模式设计

---

### 2. 源代码实现 (Source Code)

#### 2.1 Retrieval 模块 (`src/retrieval/`)

| 文件 | 大小 | 功能 |
|------|------|------|
| [`procedure_extractor.py`](src/retrieval/procedure_extractor.py) | 8.2 KB | 程序元素提取器（基于 Fig. 10 Prompt） |
| [`embeddings.py`](src/retrieval/embeddings.py) | 7.6 KB | Embedding 管理器（支持 OpenAI/本地模型） |
| [`proc_sim_retriever.py`](src/retrieval/proc_sim_retriever.py) | 12.3 KB | **SMST-DBSCAN 核心实现** |

**关键实现**:
```python
class SMSTDBSCANConfig:
    epsilon: float = 0.4  # 邻域半径
    min_pts: int = 5      # 最小点数
    top_k: int = 75       # GPT-4o 最优值

def fit(self, embeddings: np.ndarray) -> Dict[int, List[int]]:
    # 执行 SMST-DBSCAN 聚类
    # 1. 计算ε-邻域
    # 2. 识别核心点/边界点/噪声点
    # 3. 扩展簇
    # 4. 返回簇字典
```

#### 2.2 Extraction 模块 (`src/extraction/`)

| 文件 | 大小 | 功能 |
|------|------|------|
| [`guide_agent.py`](src/extraction/guide_agent.py) | 7.8 KB | Guide Agent - 提出针对性问题 |
| [`implementer_agent.py`](src/extraction/implementer_agent.py) | 6.6 KB | Implementer Agent - 基于对话回答问题 |
| [`qa_cot_generator.py`](src/extraction/qa_cot_generator.py) | 12.0 KB | QA-CoT 生成器（Single-Pass/Multi-Turn） |
| [`workflow_generator.py`](src/extraction/workflow_generator.py) | 13.3 KB | 工作流生成器（从 QA 对生成结构化工作流） |

#### 2.3 Evaluation 模块 (`src/evaluation/`)

| 文件 | 大小 | 功能 |
|------|------|------|
| [`scenario_decomposer.py`](src/evaluation/scenario_decomposer.py) | 7.6 KB | 场景分解器 - 识别所有 branching conditions |
| [`bot_info_generator.py`](src/evaluation/bot_info_generator.py) | 7.3 KB | Bot 信息生成器（Fig. 13） |
| [`customer_bot.py`](src/evaluation/customer_bot.py) | 4.4 KB | 客户模拟器（Fig. 15） |
| [`agent_bot.py`](src/evaluation/agent_bot.py) | 6.9 KB | 客服模拟器（Fig. 16） |
| [`success_evaluator.py`](src/evaluation/success_evaluator.py) | 7.4 KB | 成功评估器（Fig. 14） |

#### 2.4 Prompts 模块 (`src/prompts/`)

| 文件 | 大小 | 功能 |
|------|------|------|
| [`prompt_manager.py`](src/prompts/prompt_manager.py) | 18.4 KB | Prompt 管理器 - 包含 Fig. 10-26 所有 Prompt 的中译版 |

**包含的 Prompt 模板**:
- Fig. 10: 程序元素提取 Prompt
- Fig. 11-12: 代表性样本选择策略
- Fig. 13: Bot 信息生成 Prompt
- Fig. 14: 成功评估 Prompt
- Fig. 15: Customer Bot Prompt
- Fig. 16: Agent Bot Prompt
- Fig. 17-26: QA-CoT 相关工作流 Prompt

#### 2.5 Utils 模块 (`src/utils/`)

| 文件 | 大小 | 功能 |
|------|------|------|
| [`data_loader.py`](src/utils/data_loader.py) | 9.1 KB | 数据加载器（ABCD/SynthABCD 数据集） |
| [`metrics.py`](src/utils/metrics.py) | 8.3 KB | 指标计算器（Macro/Micro Accuracy） |

#### 2.6 主程序入口

| 文件 | 大小 | 功能 |
|------|------|------|
| [`workflow_mining_main.py`](workflow_mining_main.py) | 21.2 KB | **统一的主程序入口和配置管理** |
| [`examples/workflow_mining_example.py`](examples/workflow_mining_example.py) | 7.7 KB | 完整使用示例脚本 |

**主程序核心类**:
```python
class WorkflowMiningConfig:
    """配置管理器，集中管理所有配置参数"""
    def _get_default_config(self) -> Dict[str, Any]:
        return {
            "system": {...},
            "llm": {...},
            "embedding": {...},
            "retrieval": {
                "top_k": 75,
                "clustering_algorithm": "smst-dbscan",
                "smst_dbscan": {
                    "epsilon": 0.4,
                    "min_pts": 5
                }
            },
            "qa_cot": {...},
            "evaluation": {...}
        }

class WorkflowMiningSystem:
    """主系统类，整合所有模块"""
    async def run_full_pipeline(self, dataset_path, intent):
        # Step 1: 加载数据集
        # Step 2: 程序元素提取和检索
        # Step 3: QA-CoT 生成
        # Step 4: 工作流生成
        # Step 5: E2E 评估
        # Step 6: 汇总结果
```

---

### 3. 配置文件 (Configuration)

| 文件 | 大小 | 用途 |
|------|------|------|
| [`config/system_config.yaml`](config/system_config.yaml) | 2.6 KB | 系统级配置（LLM、Embedding、SMST-DBSCAN 参数） |
| [`config/agents/base_agent.yaml`](config/agents/base_agent.yaml) | 332 B | Agent 基础配置模板 |

**SMST-DBSCAN 关键配置**:
```yaml
retrieval:
  clustering_algorithm: "smst-dbscan"
  smst_dbscan:
    epsilon: 0.4      # 邻域半径（推荐范围：0.3-0.5）
    min_pts: 5        # 最小点数（推荐范围：5-10）
    distance_metric: "cosine"
  top_k: 75           # GPT-4o 最优值
```

---

## 📊 代码统计

### Python 文件统计
- **总文件数**: 44 个 `.py` 文件
- **核心模块**: 
  - Retrieval: 3 个文件 (28.1 KB)
  - Extraction: 4 个文件 (39.7 KB)
  - Evaluation: 5 个文件 (33.6 KB)
  - Prompts: 1 个文件 (18.4 KB)
  - Utils: 2 个文件 (17.4 KB)
  - 主程序：2 个文件 (28.9 KB)

### 文档统计
- **设计文档**: 12 个 `.md` 文件
- **核心文档**:
  - `01_project_overview.md`: 52.9 KB
  - `02_system_architecture.md`: 50.7 KB

### 代码行数估算
根据文件大小估算，总代码量约为 **3,500+ 行**（不含注释和空行）

---

## 🔬 核心技术亮点

### 1. SMST-DBSCAN 密度聚类（替代原论文的 K-Means）

**优势**:
- ✅ 自动发现任意形状的簇，无需预设簇数量
- ✅ 有效识别并过滤噪声点（异常对话）
- ✅ 基于密度可达性，更适合高维向量空间
- ✅ 对初始参数不敏感，鲁棒性强

**数学形式化** (详见 [`02_system_architecture.md`](design_docs/mining_agents/02_system_architecture.md)):

- **ε-邻域**: $N_\epsilon(x) = \{p \in D | \text{dist}(x, p) \leq \epsilon\}$
- **核心样本**: $|N_\epsilon(x)| \geq \text{min\_pts}$
- **密度可达**: $\exists p_1, ..., p_n$ 使得 $p_1=x, p_n=y$ 且 $p_{i+1} \in N_\epsilon(p_i)$
- **簇的定义**: 满足最大性和连通性的非空子集

### 2. QA-CoT（Question-Answer Chain-of-Thought）工作流提取

**两种策略**:
- **Single-Pass**: 一次性生成所有 QA 对（适合简单场景）
- **Multi-Turn**: 多轮交互式提问（适合复杂 branching conditions）

**Guide-Implementer 协作模式**:
```
Guide Agent     → 提出针对性问题（基于已收集的程序元素）
Implementer Agent → 基于对话历史回答问题
QACoT Generator → 迭代生成完整的 QA 链
```

### 3. E2E（End-to-End）评估框架

**评估流程**:
1. Scenario Decomposer: 识别所有 branching conditions
2. Customer Bot: 模拟真实客户行为（Fig. 15）
3. Agent Bot: 模拟客服执行工作流（Fig. 16）
4. Success Evaluator: 判定任务是否成功完成（Fig. 14）

**评估指标**:
- Macro Accuracy: 每个场景的准确率平均
- Micro Accuracy: 所有对话的整体准确率

### 4. Proc-Sim（Procedural Element-based Retrieval）

**检索流程**:
1. 从对话中提取程序元素（条件、动作、API 调用等）
2. 使用 OpenAI text-embedding-3-small 向量化
3. SMST-DBSCAN 聚类相似对话
4. 选择代表性样本（IntraSim 算法）
5. 基于代表性样本生成 QA-CoT

---

## 🚀 使用方法

### 快速开始

```bash
# 方式 1: 使用默认配置
python workflow_mining_main.py --dataset ./data/abcd --intent "complex_intent_1"

# 方式 2: 使用自定义配置文件
python workflow_mining_main.py --config config/workflow_mining_config.yaml

# 方式 3: 仅运行特定阶段
python workflow_mining_main.py --stage retrieval  # 仅检索
python workflow_mining_main.py --stage extraction # 仅提取
python workflow_mining_main.py --stage evaluation # 仅评估
```

### 命令行参数

```
--config CONFIG         配置文件路径（YAML 格式）
--dataset DATASET       数据集路径
--intent INTENT         目标意图（留空表示所有复杂意图）
--stage STAGE           执行阶段：all|retrieval|extraction|generation|evaluation
--output OUTPUT         输出目录
--log-level LOG_LEVEL   日志级别：DEBUG|INFO|WARNING|ERROR
```

### 示例脚本

参见 [`examples/workflow_mining_example.py`](examples/workflow_mining_example.py):

```python
from workflow_mining_main import WorkflowMiningSystem, WorkflowMiningConfig

# 创建配置
config = WorkflowMiningConfig("config/system_config.yaml")

# 创建系统实例
system = WorkflowMiningSystem(config)

# 运行完整流程
results = await system.run_full_pipeline(
    dataset_path="./data/abcd",
    intent="complex_intent_1"
)

# 查看结果
print(f"Macro Accuracy: {results['macro_accuracy']:.3f}")
print(f"Micro Accuracy: {results['micro_accuracy']:.3f}")
```

---

## 📋 待办事项（可选扩展）

根据会话摘要，以下任务可作为后续扩展方向：

### 1. 集成测试 ⏳
- [ ] 在 SynthABCD 数据集上验证完整流程
- [ ] 测试所有 branching conditions 覆盖
- [ ] 验证 SMST-DBSCAN 聚类效果

### 2. 对比实验 ⏳
- [ ] 复现论文 Table 1 的结果（QA-CoT vs Baselines）
- [ ] 对比 SMST-DBSCAN vs K-Means 的聚类质量
- [ ] 分析 Single-Pass vs Multi-Turn 的效果差异

### 3. 性能优化 ⏳
- [ ] Embedding 缓存机制
- [ ] 批量处理对话
- [ ] 并行化 E2E 评估

### 4. 可视化 ⏳
- [ ] 聚类结果可视化（t-SNE/UMAP）
- [ ] 工作流图生成（Graphviz/Mermaid）
- [ ] 评估报告自动生成

---

## 📝 版本管理

### v1.0.0 (2026-03-20) - 初始版本

**核心功能**:
- ✅ SMST-DBSCAN 密度聚类实现
- ✅ QA-CoT 工作流提取（Single-Pass + Multi-Turn）
- ✅ E2E 评估框架（Customer Bot + Agent Bot）
- ✅ 统一的配置管理和主程序入口
- ✅ 完整的 Prompt 中译（Fig. 10-26）

**已知限制**:
- 需要 OpenAI API Key（或兼容的本地模型）
- 未包含可视化组件
- 未在真实数据集上进行大规模验证

---

## 🎯 与设计要求的对照

| 要求 | 状态 | 实现位置 |
|------|------|----------|
| 分析论文 workflow 挖掘方案 | ✅ | [`01_project_overview.md`](design_docs/mining_agents/01_project_overview.md) |
| 使用 AgentScope 框架 | ✅ | 所有 Agent 均基于 AgentScope 实现 |
| 详细的系统架构设计文档 | ✅ | [`02_system_architecture.md`](design_docs/mining_agents/02_system_architecture.md) |
| 无代码片段的设计文档 | ✅ | 设计文档仅包含架构和算法描述 |
| Prompt 中译并整合到文档 | ✅ | 架构文档第 4 节 + [`prompt_manager.py`](src/prompts/prompt_manager.py) |
| **聚类使用 SMST-DBSCAN** | ✅ | [`proc_sim_retriever.py`](src/retrieval/proc_sim_retriever.py) |
| src 目录下的完整实现 | ✅ | `src/` 目录包含 6 个子模块 |
| **prj 目录下的配置和主函数入口** | ✅ | [`workflow_mining_main.py`](workflow_mining_main.py) + [`config/system_config.yaml`](config/system_config.yaml) |

---

## 📚 参考资源

### 核心文档
1. [项目概述](design_docs/mining_agents/01_project_overview.md) - 整体流程和架构设计
2. [系统架构](design_docs/mining_agents/02_system_architecture.md) - 详细算法和 Prompt 设计
3. [源代码 README](src/README.md) - 模块使用指南

### 论文参考
- Original Paper: "Turning Conversations into Workflows"
- Key Figures: Fig. 10-26 (Prompt templates)
- Evaluation Framework: Fig. 13-16 (Bot simulation)

### 依赖项
- Python >= 3.9
- AgentScope >= 0.1.0
- OpenAI API (或兼容的本地模型)
- NumPy, Scikit-learn (用于 SMST-DBSCAN)

---

## 💡 联系与反馈

如有问题或建议，请通过项目 Issue 系统反馈。

**最后更新**: 2026-03-20  
**维护者**: Workflow Mining Team
