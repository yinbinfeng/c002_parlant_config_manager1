# 需求变更追踪文档

**文档版本**: v1.0  
**创建日期**: 2026-03-30  
**最后更新**: 2026-03-30  
**维护者**: System Team

---

## 2026-03-30 重大变更

### 设计文档 v2 版本发布

#### 修改总结

基于新的设计文档 (06_design_optimization_proposal.md 和 07_ui_redesign_v2.md),将老的设计文档 v1 中的每个文件重新编写并放入 v2 目录。本次变更是系统架构的全面重构，从 v1 的 5 步法升级为 v2 的 8 步法 SOP 挖掘流程。

**时间戳**: 2026-03-30 14:00:00

---

### 一、核心变更内容

#### 1. 总体设计重构 (01_overall_design.md)

**变更点**:
- ✅ **流程升级**: 从 5 步法升级到 8 步法 SOP 挖掘流程
- ✅ **3 层 SOP 架构**: 新增一级主 SOP(主干层)、二级分支 SOP(适配层)、三级子弹 SOP(补全层)
- ✅ **中枢管控机制**: 新增 CoordinatorAgent 负责全局目标对齐、组织多 Agent 辩论
- ✅ **高度并发策略**: Step 5 的 N 个主 SOP 节点完全并行，预计加速比 5-8x
- ✅ **设计原则体系**: 新增 8 大核心设计原则和 10 条避坑红线

**验收标准**:
- [ ] 8 步法流程清晰可执行
- [ ] 3 层 SOP 架构符合 Parlant 最佳实践
- [ ] 并发策略可落地，加速比可验证

---

#### 2. Agent 运作机制重构 (02_agent_operation_mechanism.md)

**变更点**:
- ✅ **新增 8 个 Agent**: CoordinatorAgent、MainSOPMiningAgent、GlobalRulesAgent、UserProfileAgent、BranchSOPAgent、EdgeCaseSOPAgent、AssemblyAgent、ValidationAgent
- ✅ **优化 5 个 Agent**: RequirementAnalystAgent(REACT 自我检查)、RuleEngineerAgent(聚焦局部规则)、GlossaryAgent(引用全局术语库)、QualityAgent(逻辑冲突检测)、ComplianceCheckAgent(一票否决权)
- ✅ **8 步法协作流程**: 明确每个步骤的输入输出、依赖关系、可并行对象
- ✅ **Parlant 配置样例**: 完善 3 层 Journey 架构的配置样例和字段说明
- ✅ **日志与对话归档**: 新增 LoggerService 和 MessageArchive,所有 Agent 对话 message 完整保存到 JSONL 文件

**验收标准**:
- [ ] 12 个 Agent 职责清晰无重叠
- [ ] 8 步法依赖关系正确
- [ ] Parlant 配置样例符合官方 schema
- [ ] 所有 Agent 对话 message 完整归档，支持全流程追溯

---

#### 3. 工程化设计重构 (03_engineering_design.md)

**变更点**:
- ✅ **日志库选型**: 使用 logrus(非 pylogrus，非 Python logging)
- ✅ **Step 5 并发控制**: 新增并发控制伪代码、资源隔离机制、信号量控制
- ✅ **Deep Research 强制调用**: 每个 Journey 至少调用 3 次，搜索话题拆分，报告完整保存
- ✅ **配置文件重组**: 按功能模块组织 (agents/ + prompts/),配置与提示词分离
- ✅ **错误处理机制**: 完善的异常分类、重试策略、降级方案
- ✅ **日志归档设计**: 
  - LoggerService: 结构化日志记录到 `./logs/{step}/{agent_id}.log`
  - MessageArchive: 完整对话 message 保存到 `./message_archive/{step}/{agent_id}_messages.jsonl`
  - REACT 历史记录：保存到 `step{N}_react_history.json`
  - 辩论记录：保存到 `step{N}_debate_history.json`

**验收标准**:
- [ ] 日志结构化输出，支持分级
- [ ] Step 5 并发执行效率达到 5-8x 加速比
- [ ] Deep Research 调用次数可统计可验证
- [ ] 所有 Agent 对话 message 完整保存，JSONL 格式便于分析和审计

---

#### 4. UI 交互设计重构 (04_ui_design.md / 07_ui_redesign_v2.md)

**变更点**:
- ✅ **界面扩展**: 从 5 个界面扩展到 10 个界面
- ✅ **并发可视化**: 新增界面 7(Step 5 高度并发监控),显示并发数、进度条、加速比
- ✅ **3 层架构展示**: 新增界面 10(3 层 SOP 架构可视化),主/分支/子弹层级清晰
- ✅ **过程产物展示**: 每个步骤的中间产物可查看、可下载
- ✅ **日志查看器**: 新增界面 8(Agent 日志查看器),支持实时查看各 Agent 日志和对话 archive

**验收标准**:
- [ ] 10 个界面交互流畅
- [ ] 并发状态实时更新
- [ ] 3 层 SOP 架构可视化清晰
- [ ] 日志查看器支持实时刷新和过滤

---

#### 5. UI 与后端交互重构 (05_ui_backend_interaction.md)

**变更点**:
- ✅ **并发状态轮询**: 支持 Step 5 并发状态实时查询
- ✅ **新增 API 接口**: 
  - `GET /api/concurrency/stats`: 获取并发统计信息
  - `GET /api/step5/node_progress`: 获取各节点进度详情
  - `GET /api/logs/{agent_id}`: 获取指定 Agent 的日志
  - `GET /api/messages/{agent_id}`: 获取指定 Agent 的对话 archive
- ✅ **Streamlit 状态管理**: 优化轮询机制，支持增量更新
- ✅ **日志 Stream API**: 支持日志流式传输，实时更新前端

**验收标准**:
- [ ] API 接口响应时间<100ms
- [ ] 状态更新延迟<3 秒
- [ ] 并发统计准确无误
- [ ] 日志 Stream API 支持实时推送

---

#### 6. Agent 对话日志归档设计 (新增)

**变更点**:
- ✅ **LoggerService**: 结构化日志记录到 `./logs/{step}/{agent_id}.log`
- ✅ **MessageArchive**: 完整对话 message 保存到 `./message_archive/{step}/{agent_id}_messages.jsonl`
- ✅ **REACT 历史记录**: 自我反思过程保存到 `step{N}_react_history.json`
- ✅ **辩论记录**: 多 Agent 辩论保存到 `step{N}_debate_history.json`
- ✅ **12 个 Agent 全部接入日志归档**,支持全流程追溯和审计
- ✅ **JSONL 格式**: 便于日志分析和审计，每行一个 JSON 对象
- ✅ **日志分级**: 支持 DEBUG/INFO/WARNING/ERROR 等级别

**验收标准**:
- [ ] 所有 Agent 对话 message 完整保存
- [ ] JSONL 格式便于分析和审计
- [ ] REACT 历史、辩论记录可追溯
- [ ] 日志支持按级别过滤和检索

---

### 二、改造实施计划

#### 阶段 1: 核心流程重构 (3-5 天)
- [ ] 实现 8 步法流程框架
- [ ] 新增 CoordinatorAgent、MainSOPMiningAgent
- [ ] 实现 Step 2 的目标对齐与主 SOP 挖掘
- [ ] 实现 Step 5 的并行挖掘机制

#### 阶段 2: Agent 职责优化 (2-3 天)
- [ ] 新增 GlobalRulesAgent、UserProfileAgent
- [ ] 新增 BranchSOPAgent、EdgeCaseSOPAgent
- [ ] 优化现有 Agent 职责边界
- [ ] 实现中枢管控机制

#### 阶段 3: 配置与提示词完善 (2-3 天)
- [ ] 完善 Parlant 配置模板
- [ ] 优化所有 Agent 的提示词
- [ ] 实现 Deep Research 强制调用机制
- [ ] 配置系统参数优化

#### 阶段 4: 工程化改进 (2-3 天)
- [ ] 使用 logrus 替换 Print
- [ ] 实现完善的错误处理机制
- [ ] 编写单元测试和集成测试
- [ ] 性能优化和并发测试

#### 阶段 5: 端到端验证 (2-3 天)
- [ ] 使用真实业务场景测试
- [ ] 对比新旧流程输出质量
- [ ] 收集用户反馈并迭代优化

**总工期**: 11-17 天

---

### 三、风险评估与应对措施

| 风险 | 影响程度 | 发生概率 | 应对措施 |
|------|---------|---------|---------|
| **并发冲突** | 高 | 中 | 实现严格的资源隔离和信号量控制 |
| **目标偏离** | 高 | 中 | CoordinatorAgent 定期检查目标对齐 |
| **合规风险** | 极高 | 低 | ComplianceCheckAgent 一票否决权 |
| **性能不达标** | 中 | 中 | 并发测试和优化，必要时调整并发策略 |
| **UI 复杂度高** | 中 | 高 | 分阶段实现，优先保证核心功能 |

---

### 四、验收标准

#### 功能性验收
- [ ] 8 步法流程完整可执行
- [ ] 3 层 SOP 架构输出符合 Parlant schema
- [ ] Step 5 并发加速比≥4x(实测)
- [ ] Deep Research 调用次数≥3 次/Journey(可统计)
- [ ] **所有 Agent 对话 message 完整归档**

#### 非功能性验收
- [ ] 日志结构化，支持分级和检索
- [ ] 错误处理完善，异常情况可追溯
- [ ] UI 响应流畅，状态更新延迟<3 秒
- [ ] 代码可维护性高，注释完整

#### 文档验收
- [ ] v2 设计文档完整、清晰、无歧义
- [ ] 配置样例符合官方 schema
- [ ] API 接口文档完整
- [ ] 测试用例覆盖核心场景

---

### 五、下一步行动计划

1. **立即行动** (本周内):
   - [ ] 组织团队学习 v2 设计文档
   - [ ] 分配开发任务和责任
   - [ ] 搭建开发环境和分支策略

2. **短期计划** (2 周内):
   - [ ] 完成阶段 1-2(核心流程重构 + Agent 职责优化)
   - [ ] 实现 Step 5 并发框架
   - [ ] 完成日志系统迁移

3. **中期计划** (1 个月内):
   - [ ] 完成阶段 3-4(配置与提示词完善 + 工程化改进)
   - [ ] 端到端测试和优化
   - [ ] UI 界面改版上线

4. **长期计划** (持续优化):
   - [ ] 收集用户反馈，迭代优化
   - [ ] 性能监控和持续改进
   - [ ] 总结经验，形成最佳实践

---

**最后更新**: 2026-03-30 14:00:00  
**下次审查日期**: 2026-04-06  
**审查人**: System Team
