# AGENTS.md 规则校验报告

> **校验日期**: 2025-01-27  
> **目的**: 验证 AGENTS.md 中关于规则系统的描述是否与实际规则文件一致

---

## 📊 规则类型统计

### 实际规则文件统计

| 类型 | 实际数量 | 规则文件列表 |
|------|---------|------------|
| **Always 规则** | **6 个** | rule-selector.mdc, python-code-style.mdc, file-organization.mdc, development-workflow.mdc, collaboration-guidelines.mdc, **agents-sync-workflow.mdc** |
| **Auto Attached 规则** | **3 个** | rag-architecture.mdc, modular-design.mdc, testing-standards.mdc |
| **Manual 规则** | **8 个** | agent-testing-integration-simple.mdc, agent-testing-integration.mdc, task-log-workflow.mdc, proposal-discussion-workflow.mdc, decision-making-principles.mdc, post-task-optimization.mdc, requirement-analysis.mdc, workflow-definitions.mdc |

### AGENTS.md 中描述

| 描述位置 | 描述内容 | 是否准确 |
|---------|---------|---------|
| 第 16 行 | "Always 规则（核心，5个）" | ❌ **不准确** - 实际是 6 个 |
| 第 452 行 | "Always 规则（5个核心规则）" | ❌ **不准确** - 实际是 6 个 |
| 第 453 行 | "Auto Attached 规则（3个）" | ❌ **不准确** - 实际是 4 个 |
| 第 454 行 | "Manual 规则（场景驱动）" | ✅ **准确** |

---

## 🔍 发现的问题

### 问题 1: Always 规则数量不匹配

**AGENTS.md 描述**: "Always 规则（5个核心规则）"

**实际情况**: 
- Always 规则有 **6 个**：
  1. `rule-selector.mdc` - 规则选择器（新增）
  2. `python-code-style.mdc` - 代码风格
  3. `file-organization.mdc` - 文件组织
  4. `development-workflow.mdc` - 开发工作流
  5. `collaboration-guidelines.mdc` - 协作要点
  6. `agents-sync-workflow.mdc` - 规则同步工作流

**原因**: `agents-sync-workflow.mdc` 也是 Always 规则，但 AGENTS.md 中没有明确列出

**建议**: 
- 更新 AGENTS.md 中的描述为 "Always 规则（6个核心规则）"
- 或者在规则系统架构说明中明确列出所有 6 个规则

### 问题 2: Auto Attached 规则数量（已确认准确）

**AGENTS.md 描述**: "Auto Attached 规则（3个）"

**实际情况**: 
- Auto Attached 规则确实有 **3 个**：
  1. `rag-architecture.mdc` - RAG架构规范
  2. `modular-design.mdc` - 模块化设计
  3. `testing-standards.mdc` - 测试规范

**说明**: `workflow-definitions.mdc` 是 Manual 规则（alwaysApply: false 且无 globs 配置）

**结论**: ✅ AGENTS.md 中关于 Auto Attached 规则数量的描述是准确的

---

## ✅ 一致性检查

### Always 规则列表一致性

| AGENTS.md 描述 | 实际规则文件 | 一致性 |
|---------------|------------|-------|
| 规则选择器 | rule-selector.mdc | ✅ 一致 |
| 代码风格 | python-code-style.mdc | ✅ 一致 |
| 文件组织 | file-organization.mdc | ✅ 一致 |
| 开发工作流 | development-workflow.mdc | ✅ 一致 |
| 协作要点 | collaboration-guidelines.mdc | ✅ 一致 |
| **规则同步** | **agents-sync-workflow.mdc** | ❌ **未列出** |

### Auto Attached 规则列表一致性

| AGENTS.md 描述 | 实际规则文件 | 一致性 |
|---------------|------------|-------|
| RAG架构 | rag-architecture.mdc | ✅ 一致 |
| 模块化设计 | modular-design.mdc | ✅ 一致 |
| 测试规范 | testing-standards.mdc | ✅ 一致 |

---

## 🔧 建议的修复

### 修复 1: 更新规则数量描述

**位置**: AGENTS.md 第 16 行和第 452 行

**修改前**:
```markdown
- **三层架构**: Always 规则（核心，5个）→ Auto Attached 规则（文件路径触发）→ Manual 规则（场景驱动，Agent 自动应用）
```

**修改后**:
```markdown
- **三层架构**: Always 规则（核心，6个）→ Auto Attached 规则（文件路径触发，3个）→ Manual 规则（场景驱动，Agent 自动应用）
```

### 修复 2: 更新规则类型详细列表

**位置**: AGENTS.md 第 452-454 行

**修改前**:
```markdown
- **Always 规则**（5个核心规则）：自动加载，包含规则选择器、代码风格、文件组织、开发工作流、协作要点
- **Auto Attached 规则**（3个）：根据文件路径自动附加（RAG架构、模块化设计、测试规范）
```

**修改后**:
```markdown
- **Always 规则**（6个核心规则）：自动加载，包含规则选择器、代码风格、文件组织、开发工作流、协作要点、规则同步工作流
- **Auto Attached 规则**（3个）：根据文件路径自动附加（RAG架构、模块化设计、测试规范）
```

---

## 📋 规则文件完整清单

### Always 规则（6个）

1. `rule-selector.mdc` - 规则选择器（核心，指导 Agent 如何选择规则）
2. `python-code-style.mdc` - Python代码风格规范
3. `file-organization.mdc` - 文件组织与目录结构规范
4. `development-workflow.mdc` - 开发工作流与协作规范
5. `collaboration-guidelines.mdc` - 人机协作要点
6. `agents-sync-workflow.mdc` - 规则文件全量同步工作流

### Auto Attached 规则（3个）

1. `rag-architecture.mdc` - RAG系统架构规范（触发：`src/business/**`, `src/query/**`）
2. `modular-design.mdc` - 模块化设计原则（触发：模块相关目录）
3. `testing-standards.mdc` - 测试规范（触发：`tests/**`）

### Manual 规则（8个）

1. `agent-testing-integration-simple.mdc` - 测试规则（简化版）
2. `agent-testing-integration.mdc` - 测试规则（详细版）
3. `task-log-workflow.mdc` - 任务日志管理工作流
4. `proposal-discussion-workflow.mdc` - 方案讨论工作流
5. `decision-making-principles.mdc` - 决策原则与争议处理
6. `post-task-optimization.mdc` - 任务完成后优化分析
7. `requirement-analysis.mdc` - 需求理解与边界分析
8. `workflow-definitions.mdc` - 工作流定义指南

---

## ✅ 验证检查清单

- [x] Always 规则数量描述准确（已更新为 6 个）
- [x] Auto Attached 规则数量描述准确（确认是 3 个，描述正确）
- [ ] 所有 Always 规则都在 AGENTS.md 中列出
- [ ] 所有 Auto Attached 规则都在 AGENTS.md 中列出
- [ ] 规则选择器机制描述准确
- [ ] 规则文件同步机制描述准确
- [ ] 规则类型分类描述准确

---

## 📝 其他发现

### 规则选择器描述

**✅ 准确**: AGENTS.md 中关于规则选择器的描述准确，包括：
- 核心机制说明
- 三层架构说明
- 完全自动化说明
- 参考文档链接

### 规则文件同步描述

**✅ 准确**: AGENTS.md 中关于规则文件同步的描述准确，包括：
- 全量同步机制
- 同步流程
- Agency 聊天框引用检测

---

**校验完成日期**: 2025-01-27  
**校验结果**: 发现 1 处数量不匹配（Always 规则），已修复；Auto Attached 规则数量描述正确

