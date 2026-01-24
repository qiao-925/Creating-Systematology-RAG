# Skills 迁移详细说明

## 1. 从 Rules 迁移到 Skills

### 1.1 迁移步骤

```
1. 识别 Rule 内容
   ↓
2. 确定目标 Skill 目录
   ↓
3. 转换格式（frontmatter）
   ↓
4. 拆分内容（SKILL.md + references/）
   ↓
5. 删除旧 Rule 文件
```

### 1.2 格式转换

**旧格式（Rule）**：

```markdown
---
description: Rule 描述
globs:
  - "**/*.py"
alwaysApply: false
---

# Rule 内容
```

**新格式（Skill）**：

```markdown
---
name: skill-name
description: Skill 描述
---

# Skill 内容
```

## 2. 内容拆分

### 2.1 识别核心内容

核心内容（保留在 SKILL.md）：
- 强制要求
- AI Agent 行为要求
- 快速参考

### 2.2 识别详细内容

详细内容（移到 references/）：
- 详细规范说明
- 示例代码
- 最佳实践
- 故障排除

### 2.3 拆分示例

```
原 Rule（200 行）
├── 强制要求（20 行）→ SKILL.md
├── AI 行为要求（30 行）→ SKILL.md
├── 详细规范（80 行）→ references/detailed.md
└── 示例代码（70 行）→ references/examples.md

结果：
├── SKILL.md（~60 行）
└── references/
    ├── detailed.md（80 行）
    └── examples.md（70 行）
```

## 3. 迁移检查清单

### 3.1 迁移前

- [ ] 识别所有需要迁移的 Rule
- [ ] 确定目标 Skill 目录结构
- [ ] 确认无功能丢失

### 3.2 迁移中

- [ ] 转换 frontmatter 格式
- [ ] 拆分核心内容和详细内容
- [ ] 创建 references/ 目录和文件
- [ ] 更新引用路径

### 3.3 迁移后

- [ ] 验证 Skill 格式正确
- [ ] 验证 references/ 文件完整
- [ ] 删除旧 Rule 文件
- [ ] 更新相关文档引用

## 4. 常见问题

### 4.1 多个 Rules 合并

如果多个 Rules 职责相关，可以合并为一个 Skill：

```
Rules:
- rule-a.mdc（功能 A）
- rule-b.mdc（功能 B，与 A 相关）

合并为：
skill-ab/
├── SKILL.md（核心要求）
└── references/
    ├── feature-a.md
    └── feature-b.md
```

### 4.2 一个 Rule 拆分

如果一个 Rule 职责过多，可以拆分为多个 Skills：

```
Rule:
- big-rule.mdc（功能 A + 功能 B + 功能 C）

拆分为：
skill-a/
skill-b/
skill-c/
```
