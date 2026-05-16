# 2026-01-24 【plan】Skills 渐进式披露实现-实施计划

## Checkpoint 状态表

| CP | 任务 | Skills | 状态 | 完成日期 |
|----|------|--------|------|----------|
| CP1 | 拆分 architecture-cognition | 1个（231行→62行） | ✅ | 2026-01-24 |
| CP2 | 拆分任务管理类 | task-planning, task-closure | ✅ | 2026-01-24 |
| CP3 | 拆分代码质量类 | python-coding-standards, file-size-limit, single-responsibility, file-header-comments | ✅ | 2026-01-24 |
| CP4 | 拆分文档规范类 | documentation-standards, doc-driven-development | ✅ | 2026-01-24 |
| CP5 | 拆分架构+测试+前端类 | architecture-design, testing-and-diagnostics, frontend-development | ✅ | 2026-01-24 |
| CP6 | 拆分管理+沟通+原则类 | skill-management, concise-communication, project-principles | ✅ | 2026-01-24 |
| CP7 | 验证与收尾 | 全部 15 个 | ✅ | 2026-01-24 |

---

## 1. 背景与目标

### 1.1 背景

当前 Skills 实现状态：
- ✅ 所有 15 个 Skills 都有 `references/` 目录
- ✅ 所有 SKILL.md 都在"参考资料"章节引用了 references 文件
- ✅ 所有 36 个 `references/` 文件已创建并填充内容
- ✅ 所有 SKILL.md 已精简（最大 66 行，符合 ≤80 行要求）

### 1.2 目标

严格按照渐进式披露原则，全量拆分所有 15 个 Skills：
- SKILL.md 保留核心内容（约 50-80 行）
- 详细内容移到 `references/` 目录
- 确保所有引用的文件都存在

---

## 2. 技术方案

### 2.1 渐进式披露原则

```
SKILL.md（主文件，50-80 行）
├── Frontmatter（name, description）
├── 一句话概述
├── ⚠️ 核心强制要求（关键信息）
├── AI Agent 行为要求（快速参考）
├── 工具脚本说明（简要，如有）
└── 参考资料章节（链接到 references/）

references/（详细内容）
├── 详细规范说明
├── 最佳实践指南
├── 工作流详细说明
└── 示例代码或模板
```

### 2.2 拆分策略

**保留在 SKILL.md**：
- Frontmatter
- 核心强制要求（⚠️ 标记）
- AI Agent 行为要求
- 触发条件（简要）
- 工具脚本说明（简要）
- 参考资料链接

**移到 references/**：
- 详细规范说明
- 流程图/数据流图
- 示例代码
- 常见问题/错误
- 官方文档引用

---

## 3. 实施步骤

### CP1：拆分 architecture-cognition（验证模式）

**目标**：拆分最复杂的 Skill，验证拆分模式

**文件**：
- `architecture-cognition/SKILL.md`（231行 → ~70行）
- 新建 `architecture-cognition/references/system-overview.md`
- 新建 `architecture-cognition/references/three-layer-architecture.md`
- 新建 `architecture-cognition/references/component-map.md`
- 新建 `architecture-cognition/references/data-flow.md`

**验收标准**：
- [ ] SKILL.md ≤ 80 行
- [ ] 4 个 references 文件都存在且内容完整
- [ ] 核心内容在 SKILL.md 前 50 行

---

### CP2：拆分任务管理类

**目标**：拆分 task-planning（173行）和 task-closure（90行）

**task-planning**：
- `task-planning/SKILL.md`（173行 → ~70行）
- 新建 `task-planning/references/planning-workflow.md`
- 新建 `task-planning/references/requirements-decisions.md`

**task-closure**：
- `task-closure/SKILL.md`（90行 → ~50行）
- 新建 `task-closure/references/closure-workflow.md`

**验收标准**：
- [ ] 两个 SKILL.md 都 ≤ 80 行
- [ ] 3 个 references 文件都存在且内容完整

---

### CP3：拆分代码质量类

**目标**：拆分 4 个代码质量相关 Skills

**python-coding-standards**（117行 → ~60行）：
- 新建 `references/type-hints.md`
- 新建 `references/logging.md`
- 新建 `references/naming-conventions.md`
- 新建 `references/code-structure.md`

**file-size-limit**（77行 → ~50行）：
- 新建 `references/splitting-guide.md`

**single-responsibility**（157行 → ~60行）：
- 新建 `references/file-level.md`
- 新建 `references/function-level.md`
- 新建 `references/module-level.md`

**file-header-comments**（92行 → ~50行）：
- 新建 `references/comment-templates.md`
- 新建 `references/best-practices.md`

**验收标准**：
- [ ] 4 个 SKILL.md 都 ≤ 70 行
- [ ] 10 个 references 文件都存在且内容完整

---

### CP4：拆分文档规范类

**目标**：拆分 2 个文档相关 Skills

**documentation-standards**（68行 → ~45行）：
- 新建 `references/structure-standards.md`
- 新建 `references/date-format.md`
- 新建 `references/submission-checklist.md`

**doc-driven-development**（152行 → ~60行）：
- 新建 `references/when-to-consult.md`
- 新建 `references/api-verification.md`

**验收标准**：
- [ ] 2 个 SKILL.md 都 ≤ 70 行
- [ ] 5 个 references 文件都存在且内容完整

---

### CP5：拆分架构+测试+前端类

**目标**：拆分 3 个混合类 Skills

**architecture-design**（87行 → ~50行）：
- 新建 `references/layer-guidelines.md`
- 新建 `references/module-planning.md`
- 新建 `references/interface-design.md`

**testing-and-diagnostics**（139行 → ~60行）：
- 新建 `references/testing-workflow.md`
- 新建 `references/browser-testing.md`
- 新建 `references/diagnosis-workflow.md`

**frontend-development**（153行 → ~60行）：
- 新建 `references/streamlit-components.md`
- 新建 `references/ui-natural-language-editing.md`

**验收标准**：
- [ ] 3 个 SKILL.md 都 ≤ 70 行
- [ ] 8 个 references 文件都存在且内容完整

---

### CP6：拆分管理+沟通+原则类

**目标**：拆分最后 3 个 Skills

**skill-management**（123行 → ~60行）：
- 新建 `references/skill-format.md`
- 新建 `references/skill-authoring.md`
- 新建 `references/skill-migration.md`
- 新建 `references/official-docs.md`

**concise-communication**（115行 → ~50行）：
- 新建 `references/communication-guidelines.md`

**project-principles**（165行 → ~60行）：
- 新建 `references/focus-principles.md`

**验收标准**：
- [ ] 3 个 SKILL.md 都 ≤ 70 行
- [ ] 6 个 references 文件都存在且内容完整

---

### CP7：验证与收尾

**目标**：全量验证，更新索引

**任务**：
1. 验证所有 15 个 SKILL.md 长度 ≤ 80 行
2. 验证所有 references 文件都存在（共 36 个）
3. 验证所有引用链接有效
4. 更新 `skills/README.md`
5. 删除 `skills/PROGRESSIVE_DISCLOSURE_ANALYSIS.md`（临时分析文件）
6. 生成任务日志

**验收标准**：
- [ ] 所有 SKILL.md ≤ 80 行
- [ ] 所有 references 引用有效
- [ ] README.md 已更新
- [ ] 任务日志已生成

---

## 4. 文件改动清单

### 4.1 修改文件（15个 SKILL.md）

| 文件 | 原行数 | 目标行数 |
|------|--------|----------|
| `architecture-cognition/SKILL.md` | 231 | ~70 |
| `task-planning/SKILL.md` | 173 | ~70 |
| `project-principles/SKILL.md` | 165 | ~60 |
| `single-responsibility/SKILL.md` | 157 | ~60 |
| `frontend-development/SKILL.md` | 153 | ~60 |
| `doc-driven-development/SKILL.md` | 152 | ~60 |
| `testing-and-diagnostics/SKILL.md` | 139 | ~60 |
| `skill-management/SKILL.md` | 123 | ~60 |
| `python-coding-standards/SKILL.md` | 117 | ~60 |
| `concise-communication/SKILL.md` | 115 | ~50 |
| `file-header-comments/SKILL.md` | 92 | ~50 |
| `task-closure/SKILL.md` | 90 | ~50 |
| `architecture-design/SKILL.md` | 87 | ~50 |
| `file-size-limit/SKILL.md` | 77 | ~50 |
| `documentation-standards/SKILL.md` | 68 | ~45 |

### 4.2 新建文件（36个 references）

| Skill | 新建 references 文件数 |
|-------|----------------------|
| architecture-cognition | 4 |
| task-planning | 2 |
| task-closure | 1 |
| python-coding-standards | 4 |
| file-size-limit | 1 |
| single-responsibility | 3 |
| file-header-comments | 2 |
| documentation-standards | 3 |
| doc-driven-development | 2 |
| architecture-design | 3 |
| testing-and-diagnostics | 3 |
| frontend-development | 2 |
| skill-management | 4 |
| concise-communication | 1 |
| project-principles | 1 |
| **总计** | **36** |

---

## 5. 风险与注意事项

### 5.1 风险

1. **内容丢失**：拆分时可能遗漏重要内容
   - 缓解：拆分前完整阅读，拆分后验证

2. **引用断裂**：SKILL.md 中引用的 references 路径错误
   - 缓解：统一使用相对路径 `references/xxx.md`

3. **核心内容识别错误**：把详细内容误判为核心内容
   - 缓解：严格按"⚠️ 强制要求"和"AI Agent 行为要求"判断

### 5.2 注意事项

- 每个 CP 完成后立即验证，发现问题及时修正
- 保持 references 文件的完整性，不要只放标题
- 参考资料章节的链接格式统一为 `- \`references/xxx.md\` - 描述`

---

## 6. 版本信息

- **创建日期**：2026-01-24
- **完成日期**：2026-01-24
- **版本**：v1.0
- **状态**：已完成

### 6.1 实施结果

**验收结果**：
- ✅ 所有 15 个 SKILL.md ≤ 80 行（最大 66 行）
- ✅ 所有 36 个 references 文件已创建并填充内容
- ✅ 所有引用链接有效

**SKILL.md 行数统计**：
| Skill | 行数 |
|-------|------|
| testing-and-diagnostics | 66 |
| task-planning | 65 |
| frontend-development | 63 |
| python-coding-standards | 62 |
| architecture-cognition | 62 |
| task-closure | 60 |
| single-responsibility | 60 |
| skill-management | 59 |
| architecture-design | 56 |
| documentation-standards | 52 |
| project-principles | 50 |
| file-header-comments | 50 |
| doc-driven-development | 49 |
| concise-communication | 49 |
| file-size-limit | 46 |
