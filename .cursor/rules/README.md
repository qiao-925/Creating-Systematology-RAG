# Cursor Rules 规则索引

> 项目专用的 Cursor AI 规则集合，补充和完善 `AGENTS.md` 中的协作指南

## 📋 规则文件清单

| 规则文件 | 类型 | 作用范围 | 说明 |
|---------|------|---------|------|
| **python-code-style.mdc** | Always | 全局 | Python代码风格规范（类型提示、日志、异常处理等） |
| **rag-architecture.mdc** | Auto Attached | `src/business/**`, `src/query/**` | RAG系统架构规范与LlamaIndex使用指南 |
| **modular-design.mdc** | Auto Attached | 模块相关目录 | 模块化设计原则与实现规范 |
| **testing-standards.mdc** | Auto Attached | `tests/**` | 测试规范与最佳实践 |
| **file-organization.mdc** | Always | 全局 | 文件组织与目录结构规范 |
| **development-workflow.mdc** | Always | 全局 | 开发工作流与协作规范 |
| **workflow-definitions.mdc** | Manual | 按需引用 | 工作流定义指南与最佳实践 |
| **task-log-workflow.mdc** | Always | 全局 | 任务日志管理工作流（基于AGENTS.md） |
| **proposal-discussion-workflow.mdc** | Always | 全局 | 方案讨论工作流（基于AGENTS.md） |
| **decision-making-principles.mdc** | Always | 全局 | 决策原则与争议处理（基于AGENTS.md） |
| **collaboration-guidelines.mdc** | Always | 全局 | 人机协作要点（基于AGENTS.md） |
| **post-task-optimization.mdc** | Always | 全局 | 任务完成后优化分析（强制要求） |
| **requirement-analysis.mdc** | Always | 全局 | 需求理解与边界分析（基于AGENTS.md） |
| **agents-sync-workflow.mdc** | Always | 全局 | 规则文件全量同步工作流（基于AGENTS.md） |

---

## 🎯 规则说明

### 1. Python代码风格 (`python-code-style.mdc`)
**始终生效**，适用于所有 Python 代码文件

涵盖内容：
- 类型提示规范
- 文件行数限制（300行）
- 日志使用规范
- 异常处理模式
- 文档字符串标准
- 导入规范
- 命名约定

### 2. RAG架构规范 (`rag-architecture.mdc`)
**自动附加**，当编辑 `src/business/`, `src/query/`, `src/indexer/` 等目录时生效

涵盖内容：
- 三层架构原则（前端层→业务层→基础设施层）
- LlamaIndex 核心概念和用法
- 模块化设计原则
- 检索策略实现
- Embedding 模型管理
- 可观测性集成

### 3. 模块化设计 (`modular-design.mdc`)
**自动附加**，当编辑模块相关目录（`src/embeddings/`, `src/data_source/` 等）时生效

涵盖内容：
- 单一职责原则
- 抽象基类模式
- 工厂模式实现
- 注册表模式
- 配置驱动设计
- 模块扩展指南

### 4. 测试规范 (`testing-standards.mdc`)
**自动附加**，当编辑 `tests/` 目录时生效

涵盖内容：
- 单元测试 vs 集成测试
- 测试标记（Markers）
- Mock 使用规范
- 测试覆盖率目标
- 测试最佳实践

### 5. 文件组织 (`file-organization.mdc`)
**始终生效**，适用于所有文件

涵盖内容：
- 目录结构规范
- 文件命名约定
- 代码文件组织模板
- 模块拆分原则
- 导入规范
- 任务日志规范

### 6. 开发工作流 (`development-workflow.mdc`)
**始终生效**，适用于所有开发任务

涵盖内容：
- 最小改动原则
- 严格按步骤执行
- 方案讨论流程
- Bug 修复策略
- 决策原则
- Agent 自纠错机制

### 7. 工作流定义指南 (`workflow-definitions.mdc`)
**手动引用**，使用 `@workflow-definitions` 引用

涵盖内容：
- 工作流定义方式（结构化、条件触发、模板化）
- 规则类型选择（Always/Auto Attached/Manual）
- 工作流定义最佳实践
- 复杂工作流示例
- 实际应用案例

### 8. 任务日志管理工作流 (`task-log-workflow.mdc`)
**始终生效**，基于 AGENTS.md 转换

涵盖内容：
- 任务日志保存位置和命名规范
- 文档类型选择
- 禁止行为清单
- 验证检查步骤

### 9. 方案讨论工作流 (`proposal-discussion-workflow.mdc`)
**始终生效**，基于 AGENTS.md 转换

涵盖内容：
- 方案讨论阶段流程
- 方案文档必需内容（4项）
- 方案确认检查清单
- 与代码修改的衔接

### 10. 决策原则 (`decision-making-principles.mdc`)
**始终生效**，基于 AGENTS.md 转换

涵盖内容：
- 需要用户决策的场景（5种）
- 决策流程和检查清单
- 决策报告模板
- 与其他规则的整合

### 11. 协作要点 (`collaboration-guidelines.mdc`)
**始终生效**，基于 AGENTS.md 转换

涵盖内容：
- Human 应该介入的时刻（5种）
- Agent 应该自主完成的任务（4类）
- Agent 工作原则（应该做/不应该做）
- 协作流程和检查清单

### 12. 任务完成后优化分析 (`post-task-optimization.mdc`)
**始终生效**，强制要求

涵盖内容：
- 6个分析维度（代码质量、架构、性能、测试、可维护性、技术债务）
- 优化策略输出模板
- 与任务日志的整合方式
- 分析深度要求和验证检查

**核心要求**: 每个 Agent 任务完成后必须进行优化分析

### 13. 需求理解与边界分析 (`requirement-analysis.mdc`)
**始终生效**，基于 AGENTS.md 转换

涵盖内容：
- 需求分析要求
- 边界条件明确
- 风险识别
- 现有业务参考

**使用方式**: Always 生效，任务开始前必须完成（前置任务）

### 14. 规则文件全量同步工作流 (`agents-sync-workflow.mdc`)
**始终生效**，基于 AGENTS.md 转换

涵盖内容：
- 全量同步原则
- 同步流程（4步骤）
- 全量同步检查清单
- 同步时机

**使用方式**: Always 生效，当 AGENTS.md 更新时执行

**核心要求**: 确保 AGENTS.md 与规则文件完全同步

---

## 📖 AGENTS.md 映射

所有基于 `AGENTS.md` 转换的规则文件映射关系，请查看：
- **映射文档**: `.cursor/rules/AGENTS-MAPPING.md`
- **原始文档**: `AGENTS.md`

当 `AGENTS.md` 更新时，请同步更新对应的规则文件。

---

## 🔄 与 AGENTS.md 的关系

- **AGENTS.md**：AI Agent 协作指南，定义人机协作的核心原则和流程
- **.cursor/rules/**：技术实现规范，定义代码风格、架构原则、开发规范

两者互补：
- `AGENTS.md` 关注 **协作流程** 和 **工作原则**
- `.cursor/rules/` 关注 **技术细节** 和 **实现规范**

---

## 📖 使用方式

### 自动应用
- **Always** 类型规则：自动包含在所有上下文中
- **Auto Attached** 类型规则：当编辑匹配的文件时自动附加
- **Manual** 类型规则：需要使用 `@ruleName` 明确引用

### 手动引用
如果需要明确引用某个规则，在聊天中使用：

```
@python-code-style
@rag-architecture
```

---

## 🆕 添加新规则

1. 在 `.cursor/rules/` 目录创建 `.mdc` 文件
2. 添加元数据头部（description, globs, alwaysApply）
3. 编写规则内容（Markdown格式）
4. 在本文件中更新规则清单

---

## 📚 参考文档

- [Cursor Rules 文档](https://docs.cursor.com/rules)
- 项目架构：`docs/ARCHITECTURE.md`
- Agent协作指南：`AGENTS.md`
- 项目结构：`docs/PROJECT_STRUCTURE.md`

---

**最后更新**: 2025-11-03

---

## 📝 更新说明

### 2025-11-03 更新

本次更新反映了 AGENTS.md 2.0 版本的分层重构：

1. **新增规则文件**:
   - `requirement-analysis.mdc` - 需求理解与边界分析（前置任务）
   - `agents-sync-workflow.mdc` - 规则文件全量同步工作流

2. **更新的规则文件**:
   - `python-code-style.mdc` - 补充了完整的日志规范和代码注释规范

3. **映射关系**:
   - 详细映射关系请参考 `.cursor/rules/AGENTS-MAPPING.md`
