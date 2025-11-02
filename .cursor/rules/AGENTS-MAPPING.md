# AGENTS.md 到结构化规则的映射

> 说明 `AGENTS.md` 中的每个章节如何映射到 `.cursor/rules/` 中的结构化规则

---

## 📋 映射表

| AGENTS.md 章节 | 行号 | 对应规则文件 | 规则类型 | 状态 |
|---------------|------|-------------|---------|------|
| **任务日志管理** | 3-28 | `task-log-workflow.mdc` | Always | ✅ 已转换 |
| **方案讨论** | 33-42 | `proposal-discussion-workflow.mdc` | Always | ✅ 已转换 |
| **代码修改流程** | 44-58 | `development-workflow.mdc` | Always | ✅ 已存在 |
| **决策原则** | 62-70 | `decision-making-principles.mdc` | Always | ✅ 已转换 |
| **协作要点** | 73-96 | `collaboration-guidelines.mdc` | Always | ✅ 已转换 |
| **项目结构** | 99-113 | `file-organization.mdc` | Always | ✅ 已存在 |
| **测试规范** | 116-121 | `testing-standards.mdc` | Auto Attached | ✅ 已存在 |
| **语言规范** | 124-127 | - | 全局配置 | 📝 无需转换 |
| **Agent自纠错规则** | 130-221 | `development-workflow.mdc` (部分) | Always | ⚠️ 需补充 |

---

## 🔍 详细映射

### 1. 任务日志管理 (3-28行)

**原始位置**: `AGENTS.md` 第 3-28 行

**结构化规则**: `.cursor/rules/task-log-workflow.mdc`

**转换内容**:
- ✅ 文件命名规范
- ✅ 文档类型定义
- ✅ 禁止行为
- ✅ 执行步骤

**使用方式**: Always 生效，所有任务日志记录遵循此规则

---

### 2. 方案讨论流程 (33-42行)

**原始位置**: `AGENTS.md` 第 33-42 行

**结构化规则**: `.cursor/rules/proposal-discussion-workflow.mdc`

**转换内容**:
- ✅ 方案讨论阶段（不要着急修改代码）
- ✅ 方案要求（4个必需内容）
- ✅ 方案确认流程
- ✅ 验证检查清单

**使用方式**: Always 生效，当用户要求"讨论方案"时触发

---

### 3. 代码修改流程 (44-58行)

**原始位置**: `AGENTS.md` 第 44-58 行

**结构化规则**: `.cursor/rules/development-workflow.mdc`

**转换内容**:
- ✅ 严格按步骤执行
- ✅ 最小改动原则
- ✅ 参考现有业务
- ✅ Bug修复策略
- ✅ 代码文件行数限制

**使用方式**: Always 生效，所有代码修改遵循此规则

---

### 4. 决策原则 (62-70行)

**原始位置**: `AGENTS.md` 第 62-70 行

**结构化规则**: `.cursor/rules/decision-making-principles.mdc`

**转换内容**:
- ✅ 需要用户决策的场景
- ✅ 决策流程
- ✅ 决策原则清单
- ✅ 决策报告模板

**使用方式**: Always 生效，遇到争议或不确定时遵循

---

### 5. 协作要点 (73-96行)

**原始位置**: `AGENTS.md` 第 73-96 行

**结构化规则**: `.cursor/rules/collaboration-guidelines.mdc`

**转换内容**:
- ✅ Human 应该介入的时刻
- ✅ Agent 应该自主完成
- ✅ Agent 工作原则
- ✅ 协作流程
- ✅ 协作检查清单

**使用方式**: Always 生效，指导所有协作行为

---

### 6. 项目结构 (99-113行)

**原始位置**: `AGENTS.md` 第 99-113 行

**结构化规则**: `.cursor/rules/file-organization.mdc`

**转换内容**:
- ✅ 目录用途说明
- ✅ 文档更新规则

**使用方式**: Always 生效，文件组织遵循此规则

---

### 7. 测试规范 (116-121行)

**原始位置**: `AGENTS.md` 第 116-121 行

**结构化规则**: `.cursor/rules/testing-standards.mdc`

**转换内容**:
- ✅ 基本测试要求
- ✅ Bug修复测试流程

**使用方式**: Auto Attached，编辑 `tests/` 目录时生效

---

### 8. Agent自纠错规则 (130-221行)

**原始位置**: `AGENTS.md` 第 130-221 行

**结构化规则**: `.cursor/rules/development-workflow.mdc` (已包含部分)

**转换内容**:
- ✅ 错误检测（语法、逻辑、运行时、结果验证）
- ✅ 错误分类（严重性级别）
- ✅ 纠正策略（重试、参数调整、算法替换、回滚）
- ✅ 重试机制（条件、超时控制）
- ✅ 日志和报告
- ✅ 与现有规范的整合

**状态**: ⚠️ 部分已包含在 `development-workflow.mdc`，可能需要单独补充

---

## 🔄 更新同步机制

### 当 AGENTS.md 更新时

1. **检查映射表**: 确认更新的章节是否有对应的规则文件

2. **更新对应规则文件**: 
   - 如果已有对应规则文件，更新该文件
   - 如果新建章节，创建新的规则文件
   - 更新本映射文档

3. **验证一致性**:
   - 确保规则文件与 AGENTS.md 内容一致
   - 确保规则文件符合 MDC 格式
   - 确保规则类型（Always/Auto Attached/Manual）选择正确

4. **更新规则索引**: 在 `.cursor/rules/README.md` 中更新规则清单

### 转换原则

1. **保持语义一致**: 结构化规则必须准确反映 AGENTS.md 的意图
2. **增强可执行性**: 将自然语言描述转换为可执行的步骤和检查清单
3. **保留原则说明**: 在规则文件中引用原始 AGENTS.md 位置，保留上下文
4. **互补而非替代**: 结构化规则是对 AGENTS.md 的补充，不是替代

---

## 📚 规则文件清单

### Always 类型（始终生效）
- `task-log-workflow.mdc` - 任务日志管理
- `proposal-discussion-workflow.mdc` - 方案讨论
- `development-workflow.mdc` - 开发工作流
- `decision-making-principles.mdc` - 决策原则
- `collaboration-guidelines.mdc` - 协作要点
- `file-organization.mdc` - 文件组织
- `python-code-style.mdc` - Python代码风格

### Auto Attached 类型（按路径自动附加）
- `rag-architecture.mdc` - RAG架构规范
- `modular-design.mdc` - 模块化设计
- `testing-standards.mdc` - 测试规范

### Manual 类型（按需引用）
- `workflow-definitions.mdc` - 工作流定义指南

---

## 🎯 使用建议

### 对于 AI Agent
1. **优先使用结构化规则**：明确的步骤和检查清单
2. **参考 AGENTS.md 获取上下文**：理解规则背后的原则
3. **保持两者一致**：确保执行行为符合 AGENTS.md 的精神

### 对于人类开发者
1. **阅读 AGENTS.md**：理解协作原则和流程
2. **查看规则文件**：了解具体的执行步骤
3. **更新时同步**：修改 AGENTS.md 后，记得更新对应的规则文件

---

## 📝 维护指南

### 添加新规则

1. 在 `AGENTS.md` 中添加新章节
2. 创建对应的 `.mdc` 规则文件
3. 在本映射文档中添加映射关系
4. 更新 `.cursor/rules/README.md` 规则清单

### 更新现有规则

1. 同步更新 `AGENTS.md` 和对应的规则文件
2. 更新映射文档中的行号（如变化）
3. 验证规则文件格式正确

### 删除规则

1. 从 `AGENTS.md` 删除内容
2. 删除或标记废弃对应的规则文件
3. 更新映射文档和规则索引

---

**最后更新**: 2025-11-02  
**维护者**: 当 AGENTS.md 更新时，同步更新本映射文档

