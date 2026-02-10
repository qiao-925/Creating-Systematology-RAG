---
name: architecture-cognition
description: 项目专用的全局架构认知规范，帮助 AI Agent 在 RAG 分层系统中建立全局认知并分析影响范围。适用于该项目内的 Python 和 Markdown 文件。
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

# 全局架构认知规范

> 帮助 AI Agent 建立对系统的全局认知，避免局部优化导致全局问题。

---

## ⚠️ 核心强制要求

**在修改任何代码前，必须理解该修改在整个系统中的位置、影响范围和依赖关系。**

### 三层架构约束

- 前端层 → 业务层 → 基础设施层（**单向依赖**）
- **禁止反向依赖**：基础设施层不能依赖业务层或前端层
- **禁止跨层访问**：前端层不能直接访问基础设施层

---

## AI Agent 行为要求

### 修改代码前必须回答

1. **位置识别**：属于哪一层？影响哪些组件？有跨层依赖风险？
2. **影响范围**：影响哪些数据流？有组件依赖此接口？需更新测试？
3. **架构约束**：是否违反三层架构？是否引入循环依赖？

### 创建新组件时必须明确

1. **职责定位**：属于哪一层？单一职责是什么？与现有组件关系？
2. **接口设计**：需要抽象基类/Protocol？需要工厂模式？
3. **依赖管理**：依赖哪些组件？是否可依赖注入？是否违反依赖方向？

### 遇到以下情况必须升级给用户

- 涉及跨层依赖的修改
- 涉及核心组件接口变更
- 涉及数据流向改变的修改
- 涉及性能或资源消耗的重大变更

---

## 快速参考

| 层 | 核心组件 | 职责 |
|----|----------|------|
| 前端层 | `frontend/main.py` | 用户交互、UI 展示 |
| 业务层 | `RAGService`, `QueryEngine` | 业务逻辑、流程编排 |
| 基础设施层 | `IndexManager`, `Embedding`, `LLM` | 技术实现、无业务逻辑 |

---

## 参考资料

- `references/system-overview.md` - 系统定位与核心价值
- `references/three-layer-architecture.md` - 三层架构详细说明与违规示例
- `references/component-map.md` - 核心组件地图与依赖关系
- `references/data-flow.md` - 查询流程与索引构建数据流

---

## 分类标注

- 本 skill 属于**项目专用架构规则**，仅适用于当前 RAG 项目结构。
- 若需跨项目复用，请优先使用 `architecture-governance`。

---

## 路由声明（无损合并）

- 本 skill 已被 `cs-rag-architecture-guideline` 聚合为项目主入口。
- 本文件保留原始规则文本，作为“架构认知与影响面分析”子规范。
- 使用建议：优先触发 `cs-rag-architecture-guideline`，由其路由到本 skill。
