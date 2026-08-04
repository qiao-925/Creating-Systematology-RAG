---
name: architecture-design
description: 项目专用的架构设计规范，适用于当前 RAG 项目的架构设计、重构与新模块规划，确保分层清晰、接口稳定、组件可插拔。
metadata:
  type: declarative
  category: architecture
  scope: project-specific
  project: cs-rag
  classification: project-architecture
  status: legacy-routed
  primary_entry_skill: cs-rag-architecture-guideline
  related_generic_skill: architecture-governance
---

# 架构设计规范

> 适用于架构设计、重构与新模块规划，确保分层清晰、接口稳定、组件可插拔。

---

## ⚠️ 核心强制要求

### 三层架构基线

- 保持"前端 → 业务 → 基础设施"链路，禁止越层访问
- 业务层通过依赖注入获取基础设施能力
- 基础设施层不得夹带业务逻辑

### 接口设计

- 以抽象基类或 Protocol 定义契约
- 新接口默认向后兼容
- 使用构造函数依赖注入，禁止静态单例

### 可插拔设计

- 使用工厂或注册表模式注册新实现
- 所有可切换组件通过配置项启用

---

## AI Agent 行为要求

### 设计变更时

- [ ] 标注影响到的层级与上下游模块
- [ ] 确认无循环依赖
- [ ] 确认无跨层访问

### 新模块规划时

- [ ] 每个模块/类仅负责单一领域
- [ ] 命名遵循 `src/<layer>/<role>/module.py` 结构

### 涉及全局策略/性能/数据一致性风险时

**必须升级给用户决策**

---

## 参考资料

- `references/layer-guidelines.md` - 三层架构详细指南
- `references/module-planning.md` - 模块规划详细说明
- `references/interface-design.md` - 接口设计详细说明

---

## 分类标注

- 本 skill 属于**项目专用架构规则**，仅适用于当前 RAG 项目目录与约定。
- 若需跨项目复用，请优先使用 `architecture-governance`。

---

## 路由声明（无损合并）

- 本 skill 已被 `cs-rag-architecture-guideline` 聚合为项目主入口。
- 本文件保留原始规则文本，作为“架构设计与重构约束”子规范。
- 使用建议：优先触发 `cs-rag-architecture-guideline`，由其路由到本 skill。
