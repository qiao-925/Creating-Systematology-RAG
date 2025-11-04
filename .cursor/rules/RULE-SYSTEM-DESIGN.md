# Cursor 规则系统设计文档

> **文档类型**: 规则系统设计说明  
> **版本**: 2.0（Agent驱动规则选择）  
> **更新日期**: 2025-01-27  
> **目的**: 全面说明规则系统的设计思想、架构和实现细节

---

## 📐 设计思想

### 核心设计原则

#### 1. **最小化默认规则（Minimal Always Rules）**

**问题**: 如果所有规则都设为 Always，会导致：
- 上下文窗口负担过重（2000+ 行规则内容）
- Agent 注意力分散，无法聚焦关键规则
- 规则可能被截断或忽略

**解决方案**: 
- 只保留 **5 个核心规则** 为 Always
- 总 Always 规则内容控制在 **800-1000 行**以内
- 其他规则改为 Manual，由 Agent 按需选择

#### 2. **Agent 驱动的规则选择（Agent-Driven Rule Selection）**

**核心思想**: 
- Agent 根据任务场景自动判断需要哪些规则
- 用户不需要手动 @引用任何规则
- 规则选择器（rule-selector.mdc）作为"元规则"，指导 Agent 如何选择

**优势**:
- 完全自动化，用户无需关心规则调度
- Agent 只加载当前任务需要的规则
- 减少无关规则干扰，提高执行效率

#### 3. **三层规则架构（Three-Layer Rule Architecture）**

```
Layer 1: Always 规则（核心，自动加载）
  ↓
Layer 2: Auto Attached 规则（文件路径触发，自动附加）
  ↓
Layer 3: Manual 规则（场景驱动，Agent 自动选择）
```

---

## 🏗️ 架构设计

### 规则分类

#### Always 规则（5 个核心规则）

| 规则文件 | 行数 | 作用 | 为什么是 Always |
|---------|------|------|----------------|
| `rule-selector.mdc` | ~356 | **规则选择器** - Agent 如何选择规则 | 必须，指导 Agent 规则选择 |
| `python-code-style.mdc` | ~200 | Python 代码风格规范 | 核心，所有代码都需遵循 |
| `file-organization.mdc` | ~300 | 文件组织规范 | 核心，所有文件都需遵循 |
| `development-workflow.mdc` | ~215 | 开发工作流 | 核心，所有开发任务都需遵循 |
| `collaboration-guidelines.mdc` | ~200 | 人机协作要点 | 核心，所有协作都需遵循 |

**总 Always 规则**: 约 1271 行

#### Auto Attached 规则（3 个）

| 规则文件 | 触发条件 | 作用 |
|---------|---------|------|
| `rag-architecture.mdc` | `src/business/**`, `src/query/**` | RAG 架构规范 |
| `modular-design.mdc` | 模块相关目录 | 模块化设计原则 |
| `testing-standards.mdc` | `tests/**` | 测试规范 |

**机制**: Cursor 自动根据文件路径匹配，自动附加规则

#### Manual 规则（9+ 个）

| 规则文件 | 使用场景 | 由谁触发 |
|---------|---------|---------|
| `agent-testing-integration-simple.mdc` | 代码修改任务 | rule-selector 自动选择 |
| `agent-testing-integration.mdc` | 测试相关任务 | rule-selector 自动选择 |
| `task-log-workflow.mdc` | 任务完成后 | rule-selector 自动选择 |
| `proposal-discussion-workflow.mdc` | 方案讨论任务 | rule-selector 自动选择 |
| `decision-making-principles.mdc` | 方案讨论/架构决策 | rule-selector 自动选择 |
| `post-task-optimization.mdc` | 任务完成后 | rule-selector 自动选择 |
| `requirement-analysis.mdc` | 方案讨论前 | rule-selector 自动选择 |
| `agents-sync-workflow.mdc` | AGENTS.md 更新时 | rule-selector 自动选择 |
| `workflow-definitions.mdc` | 定义新工作流时 | 按需手动引用 |

---

## 🔄 自动规则选择机制

### 工作流程

```
用户请求
  ↓
Agent 接收任务
  ↓
规则选择器（Always 规则，已在上下文中）
  ↓
Agent 识别任务类型
  ↓
根据规则选择器的场景映射，判断需要哪些规则
  ↓
Agent 自动应用规则要求（无需加载规则文件到上下文）
  ↓
执行任务，遵循规则要求
  ↓
任务完成
  ↓
自动应用 post-task-optimization 和 task-log-workflow
```

### 关键机制说明

#### 1. 规则选择器的作用

`rule-selector.mdc` 作为"元规则"：
- 包含所有场景的规则映射
- 定义每个场景需要应用哪些规则的要求
- Agent 根据映射直接执行，无需加载具体规则文件

**示例**:
```markdown
场景 1: 代码修改任务
→ Agent 必须自动应用:
   1. agent-testing-integration-simple.mdc 的要求
   2. development-workflow.mdc 的要求（已 Always 加载）
   3. python-code-style.mdc 的要求（已 Always 加载）
→ Agent 执行流程:
   1. 修改代码
   2. 运行单元测试（根据测试规则要求）
   3. 记录结果
```

#### 2. Agent 如何"应用"规则

**重要理解**: Agent 不需要实际加载规则文件到上下文中，而是：
1. 根据规则选择器的指导，知道需要执行哪些步骤
2. 直接执行这些步骤（如运行测试、记录日志等）
3. 规则选择器已经包含了所有规则的核心要求

**为什么这样设计**:
- 减少上下文负担（不需要加载所有规则文件）
- 提高执行效率（只执行需要的步骤）
- 简化规则管理（规则选择器统一管理）

---

## 📋 任务场景映射

### 场景 1: 代码修改任务

**触发条件**: 用户要求修改代码、添加功能、重构代码

**自动应用的规则**:
- `agent-testing-integration-simple.mdc` - 测试规则（必须）
- `development-workflow.mdc` - 开发工作流（已 Always）
- `python-code-style.mdc` - 代码风格（已 Always）

**自动判断附加**:
- 修改 `src/business/` 或 `src/query/` → `rag-architecture.mdc` (Auto Attached)
- 修改模块相关代码 → `modular-design.mdc` (Auto Attached)
- 修改测试代码 → `testing-standards.mdc` (Auto Attached)

**执行步骤**:
1. 识别任务类型
2. 应用测试规则要求（运行单元测试）
3. 应用开发工作流要求（最小改动、按步骤执行）
4. 应用代码风格要求（类型提示、日志等）
5. 任务完成后应用优化分析和日志记录

### 场景 2: 方案讨论任务

**触发条件**: 用户要求"先讨论方案"、"制定方案"、"方案设计"

**自动应用的规则**:
- `proposal-discussion-workflow.mdc` - 方案讨论工作流
- `requirement-analysis.mdc` - 需求理解
- `decision-making-principles.mdc` - 决策原则

**执行步骤**:
1. **不要着急修改代码**
2. 充分讨论方案
3. 输出方案文档（必须包含4项内容）
4. 等待用户确认

### 场景 3: 任务完成后的优化分析

**触发条件**: 任何任务完成后（无论成功/失败）

**自动应用的规则**:
- `post-task-optimization.mdc` - 优化分析
- `task-log-workflow.mdc` - 任务日志

**执行步骤**:
1. 分析代码质量、架构、性能等6个维度
2. 识别优化点和技术债务
3. 记录到任务日志
4. 输出优化建议

### 其他场景

- **测试相关任务** → `agent-testing-integration.mdc` + `testing-standards.mdc`
- **Bug 修复任务** → `development-workflow.mdc` + `agent-testing-integration-simple.mdc`
- **架构设计任务** → `rag-architecture.mdc` + `modular-design.mdc` + `decision-making-principles.mdc`
- **文档更新任务** → `file-organization.mdc`

---

## 🔍 关键设计细节

### 1. 规则选择器的设计

**位置**: `rule-selector.mdc` (Always 规则)

**内容结构**:
1. 自动规则选择机制说明
2. 任务场景与规则映射（7 个场景）
3. 自动规则选择决策树
4. 规则文件清单
5. 检查清单和示例

**关键特性**:
- 明确说明 Agent 不需要加载规则文件到上下文
- 每个场景都有明确的规则要求和执行步骤
- 提供决策树帮助 Agent 快速判断

### 2. Always 规则的选择标准

**标准**:
1. **最核心**: 所有任务都需要的规则
2. **最通用**: 适用于所有场景的规则
3. **最简洁**: 规则内容精简，不超过 300 行

**当前 Always 规则**:
- `rule-selector.mdc` - 规则选择器（必须）
- `python-code-style.mdc` - 代码风格（核心）
- `file-organization.mdc` - 文件组织（核心）
- `development-workflow.mdc` - 开发工作流（核心）
- `collaboration-guidelines.mdc` - 协作要点（核心）

### 3. Manual 规则的设计

**设计原则**:
- 场景特定：只在特定场景需要
- 详细说明：包含完整的要求和步骤
- 可独立使用：规则文件本身包含完整信息

**Agent 如何使用**:
- Agent 根据规则选择器的指导，知道需要执行哪些步骤
- 不需要加载规则文件，直接执行步骤即可
- 规则选择器已经包含了核心要求

### 4. Auto Attached 规则的设计

**设计原则**:
- 文件路径触发：根据编辑的文件路径自动附加
- 精确匹配：使用 globs 模式精确匹配目录
- 自动处理：由 Cursor 自动处理，Agent 无需关心

**当前 Auto Attached 规则**:
- `rag-architecture.mdc` - 编辑 RAG 相关代码时自动附加
- `modular-design.mdc` - 编辑模块相关代码时自动附加
- `testing-standards.mdc` - 编辑测试代码时自动附加

---

## 📊 规则系统状态

### 规则文件统计

| 类型 | 数量 | 总行数（估算） |
|------|------|--------------|
| Always 规则 | 5 | ~1271 行 |
| Auto Attached 规则 | 3 | ~600 行 |
| Manual 规则 | 9+ | ~2000+ 行 |
| **总计** | **17+** | **~3871+ 行** |

### 上下文负担分析

**Always 规则负担**: ~1271 行
- ✅ **在合理范围内**（< 2000 行）
- ✅ **核心规则精简**
- ✅ **不会导致上下文溢出**

**Auto Attached 规则**: 按需加载，不增加默认负担

**Manual 规则**: 不在上下文中，由规则选择器指导 Agent 执行

---

## 🎯 规则选择决策树

```
任务开始
  ↓
Agent 自动识别任务类型
  ↓
┌─────────────────────────────────────────────────┐
│ 代码修改? → 自动应用: agent-testing-integration-simple │
│          → 已加载: development-workflow │
│          → 已加载: python-code-style   │
│          → 自动判断: rag-architecture (如修改相关目录) │
├─────────────────────────────────────────────────┤
│ 方案讨论? → 自动应用: proposal-discussion-workflow │
│          → 自动应用: requirement-analysis │
│          → 自动应用: decision-making-principles │
├─────────────────────────────────────────────────┤
│ 测试相关? → 自动应用: agent-testing-integration │
│          → 自动附加: testing-standards (Auto Attached) │
├─────────────────────────────────────────────────┤
│ Bug修复? → 自动应用: agent-testing-integration-simple │
│         → 已加载: development-workflow │
├─────────────────────────────────────────────────┤
│ 架构设计? → 自动附加: rag-architecture (Auto Attached) │
│          → 自动附加: modular-design (Auto Attached) │
└─────────────────────────────────────────────────┘
  ↓
Agent 自动执行任务（遵循规则要求）
  ↓
任务完成
  ↓
Agent 自动应用:
  - post-task-optimization.mdc
  - task-log-workflow.mdc
```

---

## 🔧 规则管理机制

### 规则同步

**来源**: AGENTS.md（主文档）

**同步机制**:
- `agents-sync-workflow.mdc` 定义同步流程
- 当 AGENTS.md 更新时，需要同步更新规则文件
- 映射关系见 `AGENTS-MAPPING.md`

### 规则添加

**步骤**:
1. 确定规则类型（Always/Auto Attached/Manual）
2. 创建规则文件（`.mdc` 格式）
3. 在 `rule-selector.mdc` 中注册场景映射（如果是 Manual）
4. 在 `README.md` 中更新规则清单

### 规则优化

**优化原则**:
- Always 规则数量 < 7 个
- 每个 Always 规则 < 300 行
- Manual 规则按场景细分
- 规则内容精简，避免重复

---

## 📝 关键设计决策

### 决策 1: 为什么规则选择器是 Always 规则？

**原因**:
- 规则选择器是"元规则"，必须始终可用
- Agent 需要根据它来判断如何选择规则
- 它是规则系统的核心，必须加载

### 决策 2: 为什么 Agent 不需要加载规则文件？

**原因**:
- 规则选择器已经包含了所有规则的核心要求
- Agent 只需要执行步骤，不需要查看完整规则文件
- 减少上下文负担，提高执行效率

### 决策 3: 为什么测试规则分为简化版和详细版？

**原因**:
- 简化版：代码修改时快速应用（核心要求）
- 详细版：测试相关任务时详细说明（完整流程）
- 根据场景选择，避免过度加载

### 决策 4: 为什么任务完成后必须应用优化分析？

**原因**:
- 确保每个任务都有优化分析
- 识别技术债务和优化点
- 持续改进代码质量

---

## 🔍 潜在问题和改进方向

### 当前潜在问题

1. **规则选择器可能过长**（356 行）
   - 可能影响 Agent 的注意力
   - 建议：进一步精简核心映射

2. **场景映射可能不够全面**
   - 某些特殊场景可能未覆盖
   - 建议：根据实际使用情况补充

3. **规则执行可能不够严格**
   - Agent 可能忽略某些规则要求
   - 建议：强化规则要求的表述

### 改进方向

1. **规则选择器优化**
   - 精简核心映射，保留关键信息
   - 将详细说明移到 Manual 规则

2. **场景覆盖扩展**
   - 根据实际使用情况补充场景
   - 完善场景映射关系

3. **规则执行验证**
   - 添加规则执行检查机制
   - 记录规则执行情况

---

## 📚 相关文档

- **规则索引**: `.cursor/rules/README.md` - 规则文件清单和使用说明
- **规则选择器**: `.cursor/rules/rule-selector.mdc` - 自动规则选择机制
- **规则诊断**: `.cursor/rules/RULE-DIAGNOSIS.md` - 规则系统诊断指南
- **规则优化**: `.cursor/rules/RULE-OPTIMIZATION.md` - 规则优化建议
- **AGENTS 映射**: `.cursor/rules/AGENTS-MAPPING.md` - AGENTS.md 与规则文件的映射关系

---

## 🎯 总结

### 设计优势

1. **上下文负担最小化**: Always 规则只有 5 个，总内容约 1271 行
2. **完全自动化**: Agent 自动选择规则，用户无需手动 @引用
3. **场景驱动**: 根据任务场景精确选择规则
4. **易于维护**: 规则选择器统一管理规则映射

### 核心机制

1. **规则选择器作为元规则**: 指导 Agent 如何选择规则
2. **Agent 自动执行**: 根据规则选择器的指导直接执行步骤
3. **三层规则架构**: Always → Auto Attached → Manual

### 使用方式

**用户**: 只需提出任务，Agent 自动处理规则选择和执行

**Agent**: 
1. 识别任务类型
2. 查看规则选择器的场景映射
3. 自动应用相关规则要求
4. 执行任务

---

**最后更新**: 2025-01-27  
**版本**: 2.0（Agent驱动规则选择）  
**维护者**: 开发团队

