# 任务概述

你需要基于如下给定的信息，设计一个多agent系统，用于挖掘用于客服agent的sop/规约/工具/专有名词/观测等信息。

# 任务背景

当前的任务背景是我需要构建一个客服agent，我选择了parlant框架，框架中需要注入用于指引agent的sop/规约/工具/专有名词/观测等等信息，
但我由于人工梳理这些业务信息工作量过大，且将信息一个一个录入工作量也过大。因此，我需要完如下三个任务：

1. 任务1：基于parlant的概念和使用要求，设计一个agent配置包，用于可快速加载和使用。
2. 任务2：基于parlant的概念和使用要求，设计一个自动构建parlant agent的脚本，可将配置文件自动加载，并生成parlant agent。
3. 任务3：基于parlant的概念和使用要求，以及设计好的agent配置包，构建一个agent团队自动化挖掘出配置包的详细信息。

当前任务1和2已经完成，我需要你帮我完成任务3。

任务1和2相关文档可参考如下参考文件中的内容。

# 参考文件

- parlant agent配置文件设计：E:\cursorworkspace\c002_parlant_config_manager1\design_docs\config_manager\parlant_agent_config_generate_design.md
- parlant中主要概念和使用：E:\cursorworkspace\c002_parlant_config_manager1\parlant_docs\核心概念和要点使用说明_优化版.md
- parlant详细使用文档：E:\cursorworkspace\c002_parlant_config_manager1\parlant_docs
- 用于自动化构建parlant agent 的文件包；E:\cursorworkspace\c002_parlant_config_manager1\parlant_agent_config
- 自动加载parlant配置文件构建agent的脚本：E:\cursorworkspace\c002_parlant_config_manager1\design_docs\config_manager\automation
- agent设计经验：E:\cursorworkspace\c002_parlant_config_manager1\agent_design_experience

# 任务描述

基于前面的信息，你需要完成任务3。任务3的执行过程中，人工给定的输入是业务信息，agent团队利用自身知识、团队合作、互联网知识、
私域知识完成agent配置包自动化挖掘。你当前的任务是需要按照下面的要求先完成详细设计，并输出设计文档。

下面是详细的要求：

1. 如下每一步，你需要输出文档，文档请存放在：E:\cursorworkspace\c002_parlant_config_manager1\design_docs\mining_agents
2. 请仔细分析构建Parlant配置包所需要的信息，并理解其中的概念和用法，并输出文档。
3. 基于对步骤2的理解，你需要模仿人类团队如何构建这些信息，构建一套多agent系统，并输出总体方案文档（主要是算法原理）。构建的更多的要求如下：
   - agent可模拟人类团队所需要的角色，进行构建
   - 构建过程中，agent可通过讨论、自我思考、LLM council等形式构建
   - agent可使用的工具是：文件系统（注意只能操作工作目录）、git、deep research工具搜索互联网
   - agent可获取的私有数据是客户-用户对话数据
   - 为了提升准确率，你可以考虑细化任务、利用deep agent、增加思考校验等步骤提升准确率，但你同时需要考虑效率和增加步骤的必要性
   - 公开数据挖掘和私域挖掘，可能会有冲突，请考虑如何处理
   - 如果挖掘步骤细化了，不同步骤挖掘出来的信息是否有重复、冲突，请考虑如何处理
   - 方案全局的合理性，请考虑如何处理
   - agent设计经验可参考给定的参考文件
4. 基于步骤3的理解，细化设计文档，细化对每个agent的设计，并输出对应agent的流程文档。注意，这一步更多的还是在原理和算法层的设计。
5. 基于对上述步骤的理解，设计评估系统，由于当前无人工标注的测试集，也没有上线，无法得知业务反馈的ROI，你需要考虑如何利用合成数据、LLM-as-judge、
   Rubric Evaluation等技术，你需要决定选择合适的技术
6. 基于对上面步骤的理解，设计代码架构，并输出代码架构设计文档。设计的一些原则如下：
   - 技术选型不要使用Langchain
   - openai接口需要考虑RMP限制，url/key即可从环境变量加载也可通过配置文件加载
   - 配置文件和代码需要分离
   - 考虑必要地并发设计
   - 为了便于调试，主函数如果debug参数为True，则使用代码中固定的配置启动
   - 考虑必要的单元测试和集成测试
   - 考虑异常处理
   - 日志系统使用logrus
   - 注意agent的上下文管理，可参考给定的参考文件
   - python配置文件开头需要著名文件格式
   - 为方便调试，将流程拆解为独立步骤，需要保存中间文件，可从任意一个步骤开始运行
   - 对于每个步骤有json输出的，你需要通过hook进行校验，如果存在错误，利用LLM修正
