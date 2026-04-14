# 输入增强层详细设计

> 架构概览见：`docs/CLDFlow-architecture.md` 输入层
> 默认参数见：`docs/CLDFlow-defaults.md` 输入层

---

## 查询增强策略

**HyDE（Hypothetical Document Embeddings）**：先用 LLM 生成假设答案，用假设答案做向量检索

**多查询生成**：从3-5个角度重写用户查询，扩大检索覆盖

| 策略 | 作用 | Phase |
|------|------|-------|
| HyDE | 提升语义匹配质量 | Phase 1 |
| 多查询(3-5角度) | 扩大检索覆盖 | Phase 1 |
| 查询分解 | 复杂问题拆子问题 | Phase 2 |

---

## 检索停止条件

### 硬限制（必须）

| 维度 | 默认值 | 可调 |
|------|--------|------|
| 总轮次 | 10轮 | ✅ |
| 每轮查询 | 5次 | ✅ |
| 总成本 | $5/查询 | ✅ |
| 总时间 | 5分钟 | ✅ |

### 软停止（饱和度检测）

| 条件 | 默认值 | 说明 |
|------|--------|------|
| 重复率 | >70% | 连续两轮检索结果重叠超过70% |
| 无新变量 | 连续2轮 | 未发现新的因果变量 |

---

## 数据源分级

| 层级 | 来源类型 | 示例 |
|------|---------|------|
| Tier 1 | 政府官方、顶级期刊、国际组织 | FRED, World Bank, OECD, NBER |
| Tier 2 | 知名智库、学术预印本 | NBER Working Papers, SSRN |
| Tier 3 | 主流媒体、行业报告 | WSJ, 行业白皮书 |
| Tier 4 | 博客、社论、非专家观点 | 仅作参考，需标注 |

### Phase 1 数据源

| 数据源 | 类型 | 接入方式 |
|--------|------|----------|
| arXiv | Tier 2 | API |
| Semantic Scholar | Tier 2 | API |
| FRED | Tier 1 | API |
| World Bank | Tier 1 | API |
| OECD | Tier 1 | API |

---

## 检索质量评估

| 维度 | 说明 |
|------|------|
| Coverage | 是否覆盖问题的主要方面 |
| Novelty | 新信息比例 |
| Authority | 来源层级分布 |
| Depth | 是否有足够的因果分析深度 |

---

*整合自 issue-15-sub_docs: 01-input-enhancement.md, 02-stopping-criteria.md, 19-retrieval-stopping.md, 04-academic-sources.md*
