# 项目目录结构说明

**更新日期**: 2026-03-20  
**整理目标**: 将根目录下的文档和脚本分类管理，保持项目清晰整洁

---

## 📁 目录结构总览

```
project_root/
│
├── 📘 核心文件（根目录保留）
│   ├── README.md                  # 项目说明文档
│   ├── workflow_mining_main.py    # 主程序入口
│   ├── requirements.txt           # 生产依赖
│   ├── requirements-dev.txt       # 开发依赖
│   ├── pytest.ini                # pytest 配置
│   ├── .env.example              # 环境变量示例
│   └── .gitignore                # Git 忽略配置
│
├── 📚 docs_guides/                 # 【新增】使用指南和文档
│   ├── PROJECT_OVERVIEW.md        # 项目概览
│   ├── PROJECT_COMPLETION_SUMMARY.md  # 项目完成总结
│   ├── MVP_USAGE_GUIDE.md         # MVP 使用指南
│   ├── TESTING_GUIDE.md           # 测试指南
│   ├── TEST_SUITE_GUIDE.md        # 测试套件指南
│   ├── AGENTSCOPE_TOOLS_GUIDE.md  # AgentScope 工具指南
│   └── CLEANUP_SUMMARY.md         # 清理总结
│
├── 🛠️ scripts_utils/               # 【新增】工具脚本
│   ├── RUN_VERIFICATION.bat       # 验证脚本（Windows）
│   └── test_utils.py              # 测试工具函数
│
├── 💻 src/                         # 源代码
│   ├── conversation_mining/       # 对话挖掘模块
│   ├── mining_agents/             # 挖掘 Agent 模块
│   ├── retrieval/                 # 检索模块
│   ├── extraction/                # 提取模块
│   ├── evaluation/                # 评估模块
│   └── prompts/                   # Prompt 模板
│
├── 🧪 tests/                       # 测试套件
│   ├── test_mvp.py
│   ├── test_step2_step3_agents.py
│   └── ...
│
├── ⚙️ config/                      # 配置文件
│   ├── system_config.yaml         # 系统配置
│   └── agents/                    # Agent 配置
│
├── 📋 prj/                         # 版本化配置和示例
│   ├── v0.1.0_mvp/                # MVP 版本配置
│   │   ├── config/
│   │   ├── run_step1.bat/sh
│   │   └── README.md
│   └── v0.4.0_complete/           # 完整版本配置
│       ├── config/
│       ├── scripts/
│       └── main.py
│
├── 📐 design_docs/                 # 设计文档
│   ├── mining_agents/             # 挖掘 Agent 设计文档
│   │   ├── 01_project_overview.md
│   │   └── 02_system_architecture.md
│   └── config_manager/            # 配置管理器设计文档
│
├── 📖 docs/                        # 其他文档
│   └── plans/                     # 实现计划
│
├── 🔧 scripts/                     # 辅助脚本
│   ├── validate_config.py
│   ├── verify_mvp.py
│   └── verify_step6.py
│
├── 📝 examples/                    # 示例代码
│   └── workflow_mining_example.py
│
├── 🤖 parlant_agent_config/        # Parlant Agent 配置
│   ├── agents/
│   │   ├── airline_customer_service_agent/
│   │   ├── insurance_sales_agent/
│   │   └── medical_customer_service_agent/
│   └── automation/
│
├── 📚 parlant_docs/                # Parlant 文档
│   ├── deep-analysis/
│   ├── docs/
│   ├── examples/
│   └── README.md
│
├── 📊 input/                       # 输入数据目录
├── 📤 output/                      # 输出产物目录
├── 📜 logs/                        # 日志文件目录
│
├── 🎨 agent_design_experience/     # Agent 设计经验
│   ├── AGENT_DESIGN_SPEC.md
│   ├── MULTI_AGENT_ARCHITECTURE.md
│   └── ...
│
├── 📖 agentscope_docs/             # AgentScope 文档（参考）
│   ├── docs/
│   └── examples/
│
├── 📝 design_process_log/          # 设计过程日志
│   ├── auto_mining_prompts.md
│   ├── auto_mining_software_architecture.md
│   └── ...
│
└── 📝 develop_docs/                # 开发文档
    └── mining_agents/
        └── DEVELOPMENT_PLAN.md
```

---

## 📂 目录归类说明

### 1️⃣ **docs_guides/** - 使用指南和文档

**包含内容**:
- 项目概览 (PROJECT_OVERVIEW.md)
- 完成总结 (PROJECT_COMPLETION_SUMMARY.md)
- 使用指南 (MVP_USAGE_GUIDE.md, TESTING_GUIDE.md)
- 工具指南 (AGENTSCOPE_TOOLS_GUIDE.md)
- 测试指南 (TEST_SUITE_GUIDE.md)
- 清理总结 (CLEANUP_SUMMARY.md)

**归类原因**: 
- 这些是面向用户的使用文档和指南
- 统一放在 `docs_guides/` 目录下便于查找
- 避免根目录下散落大量 `.md` 文件

**使用方法**:
```bash
# 查看 MVP 使用指南
cat docs_guides/MVP_USAGE_GUIDE.md

# 查看测试指南
cat docs_guides/TESTING_GUIDE.md
```

---

### 2️⃣ **scripts_utils/** - 工具脚本

**包含内容**:
- `RUN_VERIFICATION.bat` - Windows 验证脚本
- `test_utils.py` - 测试工具函数

**归类原因**:
- 这些是辅助性的工具和脚本
- 不是核心业务代码，但经常需要使用
- 与 `scripts/` 目录区分，这里放更通用的工具

**使用方法**:
```bash
# Windows 运行验证
.\scripts_utils\RUN_VERIFICATION.bat

# Python 使用测试工具
python scripts_utils/test_utils.py
```

---

### 3️⃣ **scripts/** - 辅助脚本（原有目录）

**包含内容**:
- `validate_config.py` - 配置验证
- `verify_mvp.py` - MVP 验证
- `verify_step6.py` - Step 6 验证

**与 scripts_utils 的区别**:
- `scripts/` 更多是特定功能的验证脚本
- `scripts_utils/` 是通用工具脚本

---

### 4️⃣ **根目录保留的核心文件**

**为什么保留在根目录**:
- `README.md` - 项目的门面，必须放在根目录
- `workflow_mining_main.py` - 主程序入口，方便直接运行
- `requirements*.txt` - pip 安装依赖的标准位置
- `pytest.ini` - pytest 自动识别的配置文件
- `.env.example` - 环境变量模板
- `.gitignore` - Git 必需文件

---

## 🔄 目录调整对比

### 调整前（散乱）
```
project_root/
├── README.md
├── MVP_USAGE_GUIDE.md
├── PROJECT_OVERVIEW.md
├── PROJECT_COMPLETION_SUMMARY.md
├── TESTING_GUIDE.md
├── TEST_SUITE_GUIDE.md
├── AGENTSCOPE_TOOLS_GUIDE.md
├── CLEANUP_SUMMARY.md
├── RUN_VERIFICATION.bat
├── test_utils.py
├── workflow_mining_main.py
└── ...
```

### 调整后（有序）
```
project_root/
├── README.md
├── workflow_mining_main.py
├── requirements.txt
├── pytest.ini
├── .env.example
├── .gitignore
│
├── docs_guides/
│   ├── MVP_USAGE_GUIDE.md
│   ├── PROJECT_OVERVIEW.md
│   ├── PROJECT_COMPLETION_SUMMARY.md
│   ├── TESTING_GUIDE.md
│   ├── TEST_SUITE_GUIDE.md
│   ├── AGENTSCOPE_TOOLS_GUIDE.md
│   └── CLEANUP_SUMMARY.md
│
└── scripts_utils/
    ├── RUN_VERIFICATION.bat
    └── test_utils.py
```

---

## 📝 使用说明

### 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 查看使用指南
cat docs_guides/MVP_USAGE_GUIDE.md

# 3. 运行主程序
python workflow_mining_main.py --dataset ./data/abcd --intent "complex_intent_1"

# 4. 运行测试
pytest tests/ -v

# 5. 运行验证脚本（Windows）
.\scripts_utils\RUN_VERIFICATION.bat
```

### 查找文档

- **项目介绍**: `docs_guides/PROJECT_OVERVIEW.md`
- **快速开始**: `docs_guides/MVP_USAGE_GUIDE.md`
- **测试指南**: `docs_guides/TESTING_GUIDE.md`
- **工具使用**: `docs_guides/AGENTSCOPE_TOOLS_GUIDE.md`

### 使用工具

- **验证脚本**: `scripts_utils/RUN_VERIFICATION.bat`
- **测试工具**: `scripts_utils/test_utils.py`
- **配置验证**: `scripts/validate_config.py`

---

## ✨ 整理效果

### 优点
1. ✅ **根目录清爽**: 只保留最核心的文件
2. ✅ **分类清晰**: 文档和脚本各归其位
3. ✅ **易于查找**: 按类别组织，快速定位
4. ✅ **专业规范**: 符合标准项目结构

### 对比
- **整理前**: 根目录约 30+ 个文件和文件夹
- **整理后**: 根目录约 20+ 个文件夹，分类清晰

---

## 🎯 最佳实践建议

### 1. 新增文档时
- **使用指南类** → 放入 `docs_guides/`
- **设计文档类** → 放入 `design_docs/`
- **技术文档类** → 放入 `docs/`

### 2. 新增脚本时
- **通用工具类** → 放入 `scripts_utils/`
- **功能验证类** → 放入 `scripts/`
- **示例代码类** → 放入 `examples/`

### 3. 维护建议
- 定期清理临时文件
- 保持根目录简洁
- 及时更新文档索引

---

**整理完成时间**: 2026-03-20  
**整理目的**: 提高项目可维护性和可读性
