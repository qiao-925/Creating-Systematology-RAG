# 2026-01-23 【plan】Cursor-Agent工作流体系重构-实施计划

> 基于组件职责边界分析和功能领域讨论，全量迁移 Rules 和 Commands 到 Skills，按功能领域重新组织，实现"上下文是认知，工作流是行为"的统一体系

---

## Checkpoint 状态

| CP | 阶段 | 状态 | 完成时间 |
|----|------|------|----------|
| CP0 | 组件职责边界分析 | ✅ 已完成 | 2026-01-23 |
| CP1 | 功能领域决策讨论 | ✅ 已完成 | 2026-01-23 |
| CP2 | 创建 Skills 目录结构 | ✅ 已完成 | 2026-01-23 |
| CP3 | 迁移功能领域1-3（代码质量、文档、架构） | ✅ 已完成 | 2026-01-23 |
| CP4 | 迁移功能领域4-5（任务管理、测试诊断） | ✅ 已完成 | 2026-01-23 |
| CP5 | 迁移功能领域6-9（前端、规则、沟通、原则） | ✅ 已完成 | 2026-01-23 |
| CP6 | 创建 Scripts 并整合 Commands | ✅ 已完成 | 2026-01-23 |
| CP7 | 清理 Rules 和 Commands 目录 | ✅ 已完成 | 2026-01-23 |
| CP8 | 更新文档与索引 | ✅ 已完成 | 2026-01-23 |

**当前进度**: CP8 - 更新文档与索引已完成，所有 Checkpoint 已完成

---

## 1. 背景与目标

### 1.1 现状问题

**组件职责边界不清**：
- Rules 和 Commands 功能重叠，边界模糊
- Skills 是更通用的开放标准，但项目未使用
- 功能分散在 Rules 和 Commands 中，缺少统一组织

**功能重叠问题**：
- Rules vs Commands：边界不清（"何时" vs "如何"）
- Commands vs Hooks：Hooks 本质是 Commands 的聚合
- Rules vs Skills：Skills 可以替代部分 Rules 和 Commands

**组织问题**：
- 按 Rules/Commands 分类，而非按功能领域
- 缺少统一的能力管理体系

### 1.2 核心原则

基于分析文档和功能领域讨论：

1. **上下文是认知，工作流是行为**
   - Skills 是上下文+执行的一体化（知识 + 脚本）
   - Skills 可以替代 Rules 和 Commands

2. **全量迁移到 Skills**
   - 所有 Rules 和 Commands 迁移为 Skills
   - 按功能领域重新组织，而非简单映射

3. **Skills 是开放标准**
   - 可移植、可执行、渐进式加载
   - 基于官方文档和开放标准

### 1.3 目标

1. **全量迁移**：所有 Rules 和 Commands 迁移到 Skills
2. **按功能领域组织**：14个 Skills，覆盖9个功能领域
3. **统一能力管理**：Skills 作为统一的能力扩展方式
4. **清理旧体系**：Rules 和 Commands 目录清空或删除
5. **更新文档**：同步所有文档，建立 Skills 索引

---

## 2. 技术方案

### 2.1 迁移后架构

```
.cursor/
├── rules/                    # 清空或只保留最小配置
│   └── (空或删除)
│
└── skills/                   # 所有能力统一在这里（14个 Skills）
    ├── 功能领域1：代码质量（3个）
    │   ├── python-coding-standards/
    │   ├── file-size-limit/
    │   └── single-responsibility/
    ├── 功能领域2：文档规范（2个）
    │   ├── documentation-standards/
    │   └── doc-driven-development/
    ├── 功能领域3：架构设计（2个）
    │   ├── architecture-cognition/
    │   └── architecture-design/
    ├── 功能领域4：任务管理（2个）
    │   ├── task-planning/
    │   └── task-closure/
    ├── 功能领域5：测试与诊断（1个）
    │   └── testing-and-diagnostics/
    ├── 功能领域6：前端开发（1个）
    │   └── frontend-development/
    ├── 功能领域7：规则管理（1个）
    │   └── skill-management/
    ├── 功能领域8：沟通与协作（1个）
    │   └── concise-communication/
    └── 功能领域9：项目原则（1个）
        └── project-principles/
```

### 2.2 核心设计

**Skills 组织原则**：
- 按功能领域组织，而非按 Rules/Commands 分类
- 每个 Skill 包含：SKILL.md（知识）+ scripts/（执行能力）
- 详细内容放在 references/，实现渐进式加载

**调用方式设计**：
- 大部分 Skills 自动调用（Agent 智能判断）
- 部分 Scripts 手动调用（用户主动触发）

**迁移策略**：
- 全量迁移：所有 Rules 和 Commands 迁移到 Skills
- 合并优化：相关功能合并，删除冗余
- 基于官方文档：参考 Cursor 和 Agent Skills 官方文档

---

## 3. 实施步骤

### CP2: 创建 Skills 目录结构

**目标**：创建 `.cursor/skills/` 目录结构，准备迁移

**文件**：
- `.cursor/skills/`（新建目录）

**内容**：
1. **创建 Skills 目录**：
   - 创建 `.cursor/skills/` 目录
   - 参考官方文档格式

2. **创建 README**：
   - 创建 `.cursor/skills/README.md`（Skills 索引和使用指南）

**验收标准**：
- [ ] Skills 目录创建完成
- [ ] README 创建完成

---

### CP3: 迁移功能领域1-3（代码质量、文档、架构）

**目标**：迁移代码质量、文档规范、架构设计三个领域的 Rules 到 Skills

#### 功能领域1：代码质量（3个 Skills）

**Skills**：
1. **`python-coding-standards/`**
   - 来源：`coding_practices.mdc`（类型提示、日志、命名、注释部分）
   - 结构：SKILL.md + references/（type-hints.md, logging.md, naming-conventions.md, code-structure.md）
   - 调用：自动调用（`disable-model-invocation: false`）
   - Description：适用于所有 Python 代码文件，包括类型提示、日志规范、命名约定等

2. **`file-size-limit/`**
   - 来源：`coding_practices.mdc`（文件≤300行硬性要求部分）
   - 结构：SKILL.md + references/（splitting-guide.md）
   - 调用：自动调用（`disable-model-invocation: false`）
   - Description：文件行数限制规范，单个代码文件必须≤300行

3. **`single-responsibility/`**
   - 来源：`single-responsibility-principle.mdc`
   - 结构：SKILL.md + references/（file-level.md, function-level.md, module-level.md）
   - 调用：自动调用（`disable-model-invocation: false`）
   - Description：单一职责原则，确保代码文件、函数、模块职责清晰单一

#### 功能领域2：文档规范（2个 Skills）

**Skills**：
4. **`documentation-standards/`**
   - 来源：`documentation_guidelines.mdc`
   - 结构：SKILL.md + references/（structure-standards.md, date-format.md, submission-checklist.md）
   - 调用：自动调用（`disable-model-invocation: false`）
   - Description：文档编写规范，适用于所有 Markdown 文件，包括标题编号、日期格式、引用规范

5. **`doc-driven-development/`**
   - 来源：`documentation_driven_development.mdc`
   - 结构：SKILL.md + references/（when-to-consult.md, api-verification.md）
   - 调用：自动调用（`disable-model-invocation: false`）
   - Description：文档驱动开发流程，在生成代码或修复 bug 时优先查阅官方文档

#### 功能领域3：架构设计（2个 Skills）

**Skills**：
6. **`architecture-cognition/`**
   - 来源：`global_architecture_cognition.mdc`
   - 结构：SKILL.md + references/（system-overview.md, three-layer-architecture.md, component-map.md, data-flow.md）
   - 调用：自动调用（`disable-model-invocation: false`）
   - Description：全局架构认知，适用于所有 Python 和 Markdown 文件，帮助 AI Agent 建立系统全局认知

7. **`architecture-design/`**
   - 来源：`architecture_design_guidelines.mdc`
   - 结构：SKILL.md + references/（layer-guidelines.md, module-planning.md, interface-design.md）
   - 调用：自动调用（`disable-model-invocation: false`）
   - Description：架构设计规范，适用于 src/business/、src/query/ 等目录内的架构设计

**验收标准**：
- [ ] 7 个 Skills 创建完成，结构正确
- [ ] 所有 references/ 目录创建完成
- [ ] SKILL.md 内容迁移完整
- [ ] Frontmatter 格式正确（name, description, disable-model-invocation）
- [ ] 调用方式设置正确（全部自动调用）
- [ ] 格式符合官方规范

---

### CP4: 迁移功能领域4-5（任务管理、测试诊断）

**目标**：迁移任务管理和测试诊断领域的 Rules 和 Commands 到 Skills

#### 功能领域4：任务管理（2个 Skills）

**Skills**：
1. **`task-planning/`**
   - 来源 Rules：`task_planning_guidelines.mdc` + `workflow_requirements_and_decisions.mdc`
   - 来源 Commands：`generate-task-plan`
   - 结构：SKILL.md + references/（planning-workflow.md, requirements-decisions.md）+ scripts/
   - Scripts：`generate_task_plan.py`（对应 `/generate-task-plan`，手动调用）
   - 调用：Skill 自动调用，Script 手动调用（`disable-model-invocation: true` for script）
   - Description：任务规划规范，适用于复杂任务（≥3步），包含需求决策和计划书创建

2. **`task-closure/`**
   - 来源 Rules：`task_closure_guidelines.mdc`（删除 run-rule-check 相关内容）
   - 来源 Commands：`generate-task-log` + `run-optimization-review`（合并）
   - 结构：SKILL.md + references/（closure-workflow.md）+ scripts/
   - Scripts：`generate_task_log.py`（合并 generate-task-log + run-optimization-review，手动调用）
   - 调用：Skill 自动调用，Script 手动调用（`disable-model-invocation: true` for script）
   - Description：任务收尾规范，包含日志生成和优化分析
   - 删除：`run-rule-check`、`execute-post-hooks`

#### 功能领域5：测试与诊断（1个 Skill）

**Skills**：
3. **`testing-and-diagnostics/`**
   - 来源 Rules：`testing_and_diagnostics_guidelines.mdc`
   - 来源 Commands：
     - `select-tests` + `run-unit-tests` + `summarize-test-results` → `run_test_workflow.py`
     - `browser-test` + `browser-a11y` + `browser-visual-regression` + `browser-restart-and-test` → `run_browser_tests.py`
     - `auto-diagnose` → `auto_diagnose.py`
   - 结构：SKILL.md + references/（testing-workflow.md, browser-testing.md, diagnosis-workflow.md）+ scripts/
   - Scripts：
     - `run_test_workflow.py` - 单元测试工作流（聚合 select + run + summarize）
     - `run_browser_tests.py` - 浏览器测试工作流（整合所有 browser 测试 Commands）
     - `auto_diagnose.py` - 诊断流程
   - 调用：Skill 自动调用（代码变更后自动判断测试类型），Scripts 主要自动触发
   - Description：测试与诊断工作流，包含单元测试和浏览器测试，测试失败时自动诊断
   - 测试逻辑：
     - 后端变更（`src/**`）→ 执行单元测试
     - 前端变更（`frontend/**`）→ 执行浏览器测试
     - 全栈变更 → 先单元测试，再浏览器测试

**验收标准**：
- [ ] 3 个 Skills 创建完成，结构正确
- [ ] 5 个 Scripts 创建完成
- [ ] Scripts 功能完整（与原 Commands 一致）
- [ ] 调用方式设置正确
- [ ] 测试逻辑在 SKILL.md 中明确说明

---

### CP5: 迁移功能领域6-9（前端、规则、沟通、原则）

**目标**：迁移剩余功能领域的 Rules 到 Skills

#### 功能领域6：前端开发（1个 Skill）

**Skills**：
1. **`frontend-development/`**
   - 来源 Rules：`streamlit_native_components.mdc` + `browser_visual_editor_integration.mdc`（开发部分）
   - 来源 Commands：`browser-edit`（包含启动逻辑）
   - 结构：SKILL.md + references/（streamlit-components.md, ui-natural-language-editing.md）+ scripts/
   - Scripts：`browser_edit.py`（UI 自然语言编辑，包含启动逻辑，手动调用）
   - 调用：Skill 自动调用（在 `frontend/**` 工作时），Script 手动调用
   - Description：前端开发规范，包含 Streamlit 原生组件优先使用和 UI 自然语言编辑
   - 删除：`browser-start`（逻辑已整合到 `browser-edit`）

#### 功能领域7：规则管理（1个 Skill）

**Skills**：
2. **`skill-management/`**
   - 来源 Rules：`cursor-rules-format.mdc` + `rule_authoring_guidelines.mdc`
   - 来源 Commands：`design-rule`
   - 结构：SKILL.md + references/（skill-format.md, skill-authoring.md, skill-migration.md, official-docs.md）+ scripts/
   - Scripts：`design_skill.py`（对应 `/design-rule`，更新为设计 Skills，手动调用）
   - 调用：Skill 自动调用（创建/修改 Skills 时），Script 手动调用
   - Description：Skills 管理规范，包含 Skills 格式规范和设计最佳实践
   - 内容更新：
     - 基于官方文档更新为 Skills 管理规范
     - 包含 Skills 格式规范（SKILL.md 格式）
     - 包含 Skills 设计最佳实践
     - 保存官方文档引用（Cursor Skills 官方文档、Agent Skills 开放标准）

#### 功能领域8：沟通与协作（1个 Skill）

**Skills**：
3. **`concise-communication/`**
   - 来源 Rules：`concise_communication.mdc`
   - 结构：SKILL.md + references/（communication-guidelines.md）
   - 调用：自动调用（`disable-model-invocation: false`）
   - Description：简洁沟通规范，适用于所有对话，优先简洁回复，避免冗长报告
   - Scripts：不需要（纯规范，无执行工具）

#### 功能领域9：项目原则（1个 Skill）

**Skills**：
4. **`project-principles/`**
   - 来源 Rules：`personal-project-focus.mdc`
   - 结构：SKILL.md + references/（focus-principles.md）
   - 调用：自动调用（`disable-model-invocation: false`）
   - Description：项目聚焦原则，适用于所有设计决策，聚焦核心功能，避免大而全
   - Scripts：不需要（纯规范，无执行工具）

**验收标准**：
- [ ] 4 个 Skills 创建完成，结构正确
- [ ] 2 个 Scripts 创建完成（browser_edit.py, design_skill.py）
- [ ] skill-management 内容更新完成（基于官方文档）
- [ ] 官方文档引用保存完成（references/official-docs.md）
- [ ] 所有 Skills 格式符合官方规范

---

### CP6: 创建 Scripts 并整合 Commands

**目标**：将所有 Commands 的逻辑提取为 Scripts，整合到对应 Skills

**文件**：
- 各 Skills 的 `scripts/` 目录

**内容**：
1. **任务管理 Scripts**：
   - `task-planning/scripts/generate_task_plan.py`
     - 来源：`generate-task-plan` 命令
     - 功能：生成任务计划书（含 Checkpoint 状态表）
     - 调用：手动调用（`disable-model-invocation: true`）
   
   - `task-closure/scripts/generate_task_log.py`
     - 来源：`generate-task-log` + `run-optimization-review`（合并）
     - 功能：生成任务日志 + 优化分析
     - 调用：手动调用（`disable-model-invocation: true`）

2. **测试与诊断 Scripts**：
   - `testing-and-diagnostics/scripts/run_test_workflow.py`
     - 来源：`select-tests` + `run-unit-tests` + `summarize-test-results`（聚合）
     - 功能：完整的单元测试工作流
     - 调用：主要自动触发，也可手动调用
   
   - `testing-and-diagnostics/scripts/run_browser_tests.py`
     - 来源：`browser-test` + `browser-a11y` + `browser-visual-regression` + `browser-restart-and-test`（整合）
     - 功能：完整的浏览器测试工作流
     - 调用：主要自动触发，也可手动调用
   
   - `testing-and-diagnostics/scripts/auto_diagnose.py`
     - 来源：`auto-diagnose` 命令
     - 功能：自动诊断流程（最多三轮）
     - 调用：测试失败时自动触发

3. **前端开发 Scripts**：
   - `frontend-development/scripts/browser_edit.py`
     - 来源：`browser-edit` 命令（包含 `browser-start` 逻辑）
     - 功能：UI 自然语言编辑
     - 调用：手动调用（`disable-model-invocation: true`）

4. **规则管理 Scripts**：
   - `skill-management/scripts/design_skill.py`
     - 来源：`design-rule` 命令（更新为设计 Skills）
     - 功能：设计/优化 Skills
     - 调用：手动调用（`disable-model-invocation: true`）

5. **更新 SKILL.md**：
   - 在 SKILL.md 中引用 scripts/（使用相对路径）
   - 说明脚本的使用方式和触发条件
   - 示例：`Run the script: scripts/generate_task_plan.py`

**验收标准**：
- [ ] 所有 Scripts 创建完成（7个）
- [ ] Scripts 功能完整（与原 Commands 一致）
- [ ] Scripts 路径引用正确（相对路径）
- [ ] SKILL.md 中正确引用 scripts/
- [ ] 调用方式设置正确（自动/手动）

---

### CP7: 清理 Rules 和 Commands 目录

**目标**：清理已迁移的 Rules 和 Commands，保留必要文档

**文件**：
- `.cursor/rules/*.mdc`（删除或归档）
- `.cursor/commands/**/*.md`（删除或归档）

**内容**：
1. **备份现有内容**：
   - 创建备份目录（可选）
   - 记录迁移映射关系

2. **删除已迁移内容**：
   - 删除已迁移的 Rules
   - 删除已迁移的 Commands

3. **保留必要文档**：
   - 保留 README.md（更新为迁移说明）
   - 保留决策总结文档

**验收标准**：
- [ ] 已迁移内容清理完成
- [ ] 必要文档保留
- [ ] 迁移映射关系记录完整

---

### CP8: 更新文档与索引

**目标**：更新所有相关文档，建立 Skills 索引

**文件**：
- `.cursor/skills/README.md`（新建）
- `.cursor/rules/README.md`（更新为迁移说明）
- `.cursor/commands/README.md`（更新为迁移说明）

**内容**：
1. **创建 Skills README**：
   - 按功能领域组织 Skills 索引
   - 添加使用指南
   - 添加快速参考

2. **更新 Rules/Commands README**：
   - 说明已迁移到 Skills
   - 提供迁移映射表
   - 指向 Skills README

3. **更新项目文档**：
   - 更新主 README.md（如有相关章节）
   - 更新工作流文档

**验收标准**：
- [ ] Skills README 创建完成
- [ ] Rules/Commands README 更新完成
- [ ] 所有文档同步，无遗漏

---

## 4. 风险与注意事项

### 4.1 风险点

- **迁移不完整**：遗漏某些 Rules 或 Commands
  - **应对**：基于决策总结文档逐一检查，确保全覆盖

- **Skills 格式错误**：不符合官方规范
  - **应对**：严格参考官方文档，使用 `/migrate-to-skills` 工具验证

- **Scripts 功能缺失**：迁移后 Scripts 功能不完整
  - **应对**：每个 Script 创建后验证功能，确保与原 Commands 一致

- **调用方式错误**：自动/手动调用设置不当
  - **应对**：根据决策总结文档设置，测试验证

### 4.2 注意事项

- **分阶段迁移**：按功能领域逐步迁移，便于验证
- **保持功能一致**：迁移后功能应与原 Rules/Commands 一致
- **文档同步**：每次迁移同步更新文档
- **测试验证**：每个 CP 完成后测试 Skills 是否正常工作

---

## 5. 文件改动清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `.cursor/skills/` | 新建 | Skills 目录（14个 Skills） |
| `.cursor/skills/*/SKILL.md` | 新建 | 14个 Skills 主文件 |
| `.cursor/skills/*/references/` | 新建 | 各 Skills 的参考文档 |
| `.cursor/skills/*/scripts/` | 新建 | 7个 Scripts（5个 Skills 包含） |
| `.cursor/skills/README.md` | 新建 | Skills 索引和使用指南 |
| `.cursor/rules/*.mdc` | 删除 | 已迁移的 Rules（备份后删除） |
| `.cursor/rules/README.md` | 更新 | 更新为迁移说明 |
| `.cursor/commands/**/*.md` | 删除 | 已迁移的 Commands（备份后删除） |
| `.cursor/commands/README.md` | 更新 | 更新为迁移说明 |
| `.cursor/SKILLS_MIGRATION_DECISIONS.md` | 已有 | 决策总结文档（引用） |
| `.cursor/WORKFLOW_COMPONENTS_ANALYSIS.md` | 已有 | 组件职责边界分析（引用） |

---

## 6. 版本信息

- **创建日期**：2026-01-23
- **最后更新**：2026-01-23
- **版本**：v2.0（更新为全量迁移到 Skills 方案）
- **基于**：
  - `WORKFLOW_COMPONENTS_ANALYSIS.md` - 组件职责边界分析
  - `SKILLS_MIGRATION_DECISIONS.md` - 功能领域决策总结
  - [Cursor Skills 官方文档](https://cursor.com/cn/docs/context/skills)
  - [Agent Skills 开放标准](https://agentskills.io/home)
