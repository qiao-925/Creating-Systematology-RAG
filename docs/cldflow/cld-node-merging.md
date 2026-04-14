# CLD层 - 节点归并设计

> 架构概览见：`docs/CLDFlow-architecture.md` CLD层
> 默认参数见：`docs/CLDFlow-defaults.md` CLD层

---

## 核心问题

不同Agent可能用不同表述指代同一概念（"财政补贴" vs "政府住房补贴" vs "购房补贴"），需要自动归并。

---

## 归并策略

**算法**：Sentence Transformer + 余弦相似度

| 步骤 | 说明 |
|------|------|
| 1. 编码 | 用 Sentence Transformer 将所有节点名编码为向量 |
| 2. 配对 | 计算所有节点对的余弦相似度 |
| 3. 归并 | 相似度 > 0.8 的节点自动归并 |
| 4. 命名 | 保留最早出现的名称作为 canonical_name，其余记为 aliases |

**阈值**：0.8（可调，见 `CLDFlow-defaults.md`）

**模型选择**：MiniLM-L6-v2 或 BGE-small（Phase 1用MiniLM，足够且快）

---

## 归并后节点结构

```json
{
  "id": "uuid",
  "name": "政府住房补贴",
  "aliases": ["财政补贴", "购房补贴"],
  "domain": "政策"
}
```

---

## 边界情况

| 情况 | 处理 |
|------|------|
| 相似但不同概念（如"住房价格"vs"土地价格"） | 相似度<0.8，不归并 |
| 完全相同名称 | 直接合并（相似度=1.0） |
| 部分重叠概念 | 0.8阈值边界，Phase 2引入人工确认 |

---

*整合自 issue-15-sub_docs: 10-cld-node-merging.md*
