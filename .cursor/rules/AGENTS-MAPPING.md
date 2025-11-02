# AGENTS.md 到结构化规则的映射

> 说明 `AGENTS.md` 中的每个章节如何映射到 `.cursor/rules/` 中的结构化规则

---

## 📋 映射表

| AGENTS.md 章节 | 行号 | 对应规则文件 | 规则类型 | 状态 |
|---------------|------|-------------|---------|------|
| **前置任务** | | | | |
| 方案讨论 | 33-66 | `proposal-discussion-workflow.mdc` | Always | ✅ 已转换 |
| 需求理解与边界分析 | 69-77 | `requirement-analysis.mdc` | Always | ✅ 已转换 |
| **任务中的工程实践** | | | | |
| 执行原则 | 84-105 | `development-workflow.mdc` | Always | ✅ 已转换 |
| 代码规范 | 108-167 | `python-code-style.mdc` | Always | ✅ 已更新 |
| 错误处理与自纠错 | 170-218 | `development-workflow.mdc` | Always | ✅ 已转换 |
| 协作与决策 | 221-262 | `decision-making-principles.mdc`<br/>`collaboration-guidelines.mdc` | Always | ✅ 已转换 |
| **后置任务** | | | | |
| 任务日志管理 | 269-305 | `task-log-workflow.mdc` | Always | ✅ 已转换 |
| 测试与验证 | 308-321 | `testing-standards.mdc` | Auto Attached | ✅ 已存在 |
| 文档更新 | 324-332 | `file-organization.mdc` | Always | ✅ 已存在 |
| **规则文件同步** | 335-394 | `agents-sync-workflow.mdc` | Always | ✅ 已转换 |
| **附录** | | | | |
| 项目结构 | 399-415 | `file-organization.mdc` | Always | ✅ 已存在 |
| 语言规范 | 418-421 | - | 全局配置 | 📝 无需转换 |

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

### 2. 前置任务

#### 2.1 方案讨论 (33-66行)

**原始位置**: `AGENTS.md` 第 33-66 行

**结构化规则**: `.cursor/rules/proposal-discussion-workflow.mdc`

**转换内容**:
- ✅ 方案讨论阶段（不要着急修改代码）
- ✅ 方案要求（4个必需内容）
- ✅ 方案确认流程
- ✅ 验证检查清单

**使用方式**: Always 生效，当用户要求"讨论方案"时触发

#### 2.2 需求理解与边界分析 (69-77行)

**原始位置**: `AGENTS.md` 第 69-77 行

**结构化规则**: `.cursor/rules/requirement-analysis.mdc`

**转换内容**:
- ✅ 需求分析要求
- ✅ 边界条件明确
- ✅ 风险识别
- ✅ 现有业务参考

**使用方式**: Always 生效，任务开始前必须完成

---

### 3. 任务中的工程实践

#### 3.1 执行原则 (84-105行)

**原始位置**: `AGENTS.md` 第 84-105 行

**结构化规则**: `.cursor/rules/development-workflow.mdc`

**转换内容**:
- ✅ 严格按步骤执行
- ✅ 最小改动原则
- ✅ 参考现有业务

**使用方式**: Always 生效，所有代码修改遵循此规则

#### 3.2 代码规范 (108-167行)

**原始位置**: `AGENTS.md` 第 108-167 行

**结构化规则**: `.cursor/rules/python-code-style.mdc`

**转换内容**:
- ✅ 使用日志代替print（含例外情况）
- ✅ 使用枚举（Enum）
- ✅ 代码文件行数限制
- ✅ 代码注释规范（为什么 vs 做什么）

**使用方式**: Always 生效，所有代码编写遵循此规则

#### 3.3 错误处理与自纠错 (170-218行)

**原始位置**: `AGENTS.md` 第 170-218 行

**结构化规则**: `.cursor/rules/development-workflow.mdc`

**转换内容**:
- ✅ Bug修复策略
- ✅ Agent自纠错机制
- ✅ 错误检测与分类
- ✅ 纠正策略与重试机制

**使用方式**: Always 生效，错误处理遵循此规则

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

### 4. 后置任务

#### 4.1 任务日志管理 (269-305行)

**原始位置**: `AGENTS.md` 第 269-305 行

**结构化规则**: `.cursor/rules/task-log-workflow.mdc`

**转换内容**:
- ✅ 文件命名规范
- ✅ 文档类型定义
- ✅ 禁止行为
- ✅ 日志内容要求（含优化分析要求）

**使用方式**: Always 生效，所有任务日志记录遵循此规则

#### 4.2 测试与验证 (308-321行)

**原始位置**: `AGENTS.md` 第 308-321 行

**结构化规则**: `.cursor/rules/testing-standards.mdc`

**转换内容**:
- ✅ 代码实现后的测试要求
- ✅ Bug修复后的验证要求

**使用方式**: Auto Attached，编辑 `tests/` 目录时生效

#### 4.3 文档更新 (324-332行)

**原始位置**: `AGENTS.md` 第 324-332 行

**结构化规则**: `.cursor/rules/file-organization.mdc`

**转换内容**:
- ✅ 文档更新规则
- ✅ 不同文档的更新场景

**使用方式**: Always 生效

#### 4.4 规则文件同步 (335-394行)

**原始位置**: `AGENTS.md` 第 335-394 行

**结构化规则**: `.cursor/rules/agents-sync-workflow.mdc`

**转换内容**:
- ✅ 全量同步原则
- ✅ 同步流程（4步骤）
- ✅ 全量同步检查清单
- ✅ 同步时机

**使用方式**: Always 生效，当 AGENTS.md 更新时执行

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
- `requirement-analysis.mdc` - 需求理解与边界分析
- `development-workflow.mdc` - 开发工作流
- `decision-making-principles.mdc` - 决策原则
- `collaboration-guidelines.mdc` - 协作要点
- `file-organization.mdc` - 文件组织
- `python-code-style.mdc` - Python代码风格
- `agents-sync-workflow.mdc` - 规则文件全量同步工作流

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

**最后更新**: 2025-11-03  
**维护者**: 当 AGENTS.md 更新时，执行全量同步（参考 `agents-sync-workflow.mdc`）

---

## 🔄 更新说明

### 2025-11-03 更新

本次更新反映了 AGENTS.md 2.0 版本的分层重构：

1. **新增规则文件**:
   - `requirement-analysis.mdc` - 需求理解与边界分析（前置任务）
   - `agents-sync-workflow.mdc` - 规则文件全量同步工作流

2. **更新的规则文件**:
   - `python-code-style.mdc` - 补充了完整的日志规范和代码注释规范

3. **映射关系调整**:
   - 按分层结构重新组织映射表（前置任务 → 任务中 → 后置任务）
   - 更新了所有章节的行号（反映重构后的结构）
   - 明确了规则文件的分类和用途

