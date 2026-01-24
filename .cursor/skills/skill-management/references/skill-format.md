# Skills 格式详细规范

## 1. 目录结构

每个 Skill 包含：

```
skill-name/
├── SKILL.md          # 主文件（知识 + 规范）
├── references/       # 参考文档（渐进式加载）
│   └── *.md
└── scripts/          # 执行脚本（可选）
    └── *.py
```

## 2. SKILL.md 格式

### 2.1 Frontmatter（必需）

```yaml
---
name: skill-name
description: Skill 描述，说明何时使用此 Skill
---
```

| 字段 | 类型 | 描述 |
|------|------|------|
| `name` | string | Skill 名称（与目录名一致） |
| `description` | string | Skill 描述（何时使用此 Skill） |

### 2.2 内容结构

```markdown
---
name: skill-name
description: Skill 描述
---

# Skill 标题

> 一句话概述

---

## ⚠️ 核心强制要求

[关键信息，放在前 50 行]

---

## AI Agent 行为要求

[Agent 应该如何执行]

---

## 参考资料

- `references/xxx.md` - 描述

---

## 版本信息

- **最后更新**：YYYY-MM-DD
- **版本**：v1.0
```

## 3. references 目录

### 3.1 用途

存放详细内容，实现渐进式加载。

### 3.2 命名规范

```
references/
├── detailed-guide.md      # 详细指南
├── examples.md            # 示例
├── best-practices.md      # 最佳实践
└── troubleshooting.md     # 故障排除
```

### 3.3 引用方式

在 SKILL.md 中引用：

```markdown
## 参考资料

- `references/detailed-guide.md` - 详细指南
- `references/examples.md` - 示例代码
```

## 4. scripts 目录（可选）

### 4.1 用途

存放执行脚本，提供自动化能力。

### 4.2 命名规范

```
scripts/
├── run_xxx.py           # 执行脚本
├── generate_xxx.py      # 生成脚本
└── validate_xxx.py      # 验证脚本
```

### 4.3 脚本说明

在 SKILL.md 中说明脚本用途：

```markdown
## 工具脚本

**脚本**：`scripts/run_xxx.py`

**功能**：描述功能

**调用方式**：手动调用/自动触发
```

## 5. 长度限制

| 文件类型 | 限制 |
|----------|------|
| SKILL.md | ≤ 80 行（核心内容在前 50 行）|
| references/*.md | 单个文件 ≤ 200 行 |
| scripts/*.py | 单个文件 ≤ 300 行 |
