# 无损合并路由与原文映射

## 1. 合并策略

本次为**无损合并（lossless merge）**：

- 新增聚合入口 `cs-rag-architecture-guideline`
- 已将原 skill 与 references 的文本内容全量复制到新 skill 的 `references/`
- 删除原 skill 后，聚合 skill 仍可独立使用

---

## 2. 路由映射

| 聚合阶段 | 目标 skill | 作用 |
|----------|------------|------|
| 阶段 A：认知 | `architecture-cognition` | 分层位置识别、影响面分析、数据流审查 |
| 阶段 B：设计 | `architecture-design` | 契约设计、依赖注入、可插拔/工厂注册 |
| 阶段 C：复核 | `architecture-cognition` + `architecture-design` | 复核跨层/反向/循环依赖与兼容性 |

---

## 3. 原文路径

> 以下为迁移前源路径（已下线，仅用于历史追溯）。

### 3.1 架构认知原文

- `architecture-cognition/SKILL.md`
- `architecture-cognition/references/system-overview.md`
- `architecture-cognition/references/three-layer-architecture.md`
- `architecture-cognition/references/component-map.md`
- `architecture-cognition/references/data-flow.md`

### 3.2 架构设计原文

- `architecture-design/SKILL.md`
- `architecture-design/references/layer-guidelines.md`
- `architecture-design/references/module-planning.md`
- `architecture-design/references/interface-design.md`

---

## 3.3 迁移后承载路径（删除源 skill 后仍保留）

- `cs-rag-architecture-guideline/references/architecture-cognition-skill.md`
- `cs-rag-architecture-guideline/references/architecture-cognition-system-overview.md`
- `cs-rag-architecture-guideline/references/architecture-cognition-three-layer-architecture.md`
- `cs-rag-architecture-guideline/references/architecture-cognition-component-map.md`
- `cs-rag-architecture-guideline/references/architecture-cognition-data-flow.md`
- `cs-rag-architecture-guideline/references/architecture-design-skill.md`
- `cs-rag-architecture-guideline/references/architecture-design-layer-guidelines.md`
- `cs-rag-architecture-guideline/references/architecture-design-module-planning.md`
- `cs-rag-architecture-guideline/references/architecture-design-interface-design.md`

---

## 4. 迁移后维护规则

- 新增通用策略时，优先更新聚合入口中的路由与判定逻辑。
- 删除源 skill 后，所有细节规则在聚合 skill 的 `references/` 中维护。
- 若历史规则有增补，需同步更新聚合 skill 的镜像文本并重做完整性校验。
