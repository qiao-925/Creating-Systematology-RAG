---
name: skill-management
description: Skills 管理规范，包含 Skills 格式规范和设计最佳实践。适用于创建、优化或评估 Skills 体系的任务。
---

# Skills 管理规范

> 适用于创建、优化或评估 Skills 体系的任务。

---

## ⚠️ 核心强制要求

### 文件结构

```
skill-name/
├── SKILL.md          # 主文件（≤ 80 行）
├── references/       # 参考文档
└── scripts/          # 执行脚本（可选）
```

### Frontmatter 格式

```yaml
---
name: skill-name
description: Skill 描述
---
```

### 渐进式披露

- **SKILL.md**：核心要求，放在前 50 行
- **references/**：详细内容，按需加载

---

## AI Agent 行为要求

### 创建 Skill 时

- 必须在 `.cursor/skills/` 目录下创建
- 必须使用正确的 frontmatter 格式
- 必须将详细内容放在 `references/`

### 修改 Skill 时

- 保持 frontmatter 格式正确
- 同步更新相关文档

---

## 参考资料

- `references/skill-format.md` - Skills 格式详细规范
- `references/skill-authoring.md` - Skills 设计详细指南
- `references/skill-migration.md` - Skills 迁移详细说明
- `references/official-docs.md` - 官方文档引用
