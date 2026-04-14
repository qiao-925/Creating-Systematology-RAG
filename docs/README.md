# CLDFlow 文档中心

> 按任务组织的文档体系

---

## 文档结构

```
docs/
├── README.md                    # 本文档（导航入口）
├── issues/                      # 按任务聚合（推荐优先查看）
│   └── 15-metathesis-architecture/   # Issue #15: 综合集成法架构
│       ├── README.md            # 任务摘要
│       ├── 01-input-enhancement.md
│       ├── 02-stopping-criteria.md
│       ├── 03-evaluation-strategy.md
│       ├── 04-academic-sources.md
│       ├── 05-human-in-loop.md
│       ├── 06-dynamic-agent.md
│       ├── 07-template-evaluation.md
│       └── 08-implementation-report.md
│
├── research/                    # 通用研究成果（跨任务）
│   ├── ecosystem-map-system-dynamics.md
│   └── cld-engineering-landscape.md
│
├── design/                      # 设计文档（待创建）
├── api/                         # API 文档（待创建）
│
└── archive/                     # 已关闭任务归档
    └── 2026-04-closed/
```

---

## 快速导航

### 进行中任务

| Issue | 任务 | 状态 | 最后更新 |
|-------|------|------|---------|
| [#15](issues/15-metathesis-architecture/) | 综合集成法架构洞察 | 🟡 进行中 | 04-12 |
| #14 | 项目方向对齐 | ⬜ 待启动 | - |
| #13 | Research Kernel MVP | ⬜ 待启动 | - |

### 通用研究

- [系统动力学学科生态图谱](ecosystem-map-system-dynamics-2026-04-10.md)
- [CLD 工具生态调研](research-cld-engineering-landscape-2026-04-10.md)
- [产品方向头脑风暴](brainstorm-product-direction-2026-04-10.md)

---

## 使用指南

### 查找任务文档

1. 先看 `issues/{issue-number}/README.md` 了解任务概况
2. 按编号顺序阅读相关文档
3. 最新决策通常在 README 的「核心决策」部分

### 创建新任务文档

```bash
mkdir -p docs/issues/{issue-number}-{short-name}/
# 创建 README.md 作为入口
touch docs/issues/{issue-number}-{short-name}/README.md
```

### 命名规范

- Issue 目录：`{number}-{short-name}/`（如 `15-metathesis-architecture/`）
- 文档文件：`{NN}-{short-title}.md`（如 `01-input-enhancement.md`）
- 日期标记：如需日期，放在元数据中而非文件名

---

*最后更新：2026-04-12*
