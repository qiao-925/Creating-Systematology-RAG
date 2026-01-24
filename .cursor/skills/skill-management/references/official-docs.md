# 官方文档引用

## 1. Cursor Rules 官方文档

### 1.1 Rules 格式

参考：[Cursor Rules](https://docs.cursor.com/context/rules-for-ai)

```yaml
---
description: Rule 描述
globs:
  - "**/*.py"
alwaysApply: false
---
```

### 1.2 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `description` | string | Rule 描述 |
| `globs` | string[] | 文件匹配模式 |
| `alwaysApply` | boolean | 是否总是应用 |

## 2. Agent Skills 官方文档

### 2.1 Skills 格式

参考：[Cursor Agent Skills](https://docs.cursor.com/context/agent-skills)

```yaml
---
name: skill-name
description: Skill 描述
---
```

### 2.2 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | Skill 名称（与目录名一致） |
| `description` | string | Skill 描述（何时使用） |

## 3. 项目采用的格式

### 3.1 Skills 格式

本项目采用 Agent Skills 格式：

```yaml
---
name: skill-name
description: Skill 描述
---
```

### 3.2 目录结构

```
.cursor/skills/
├── skill-name/
│   ├── SKILL.md          # 主文件
│   ├── references/       # 参考文档
│   └── scripts/          # 执行脚本（可选）
```

### 3.3 渐进式披露

- **SKILL.md**：核心要求（≤ 80 行）
- **references/**：详细内容（按需加载）

## 4. 更新日志

| 日期 | 变更 |
|------|------|
| 2026-01-23 | 从 Rules 迁移到 Skills 格式 |
| 2026-01-24 | 实现渐进式披露 |
