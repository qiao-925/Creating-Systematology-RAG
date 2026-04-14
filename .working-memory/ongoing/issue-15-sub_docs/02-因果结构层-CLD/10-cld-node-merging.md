# 因果层 - 节点归并向量模型选型调研

## 核心问题

多视角 Agent 提取的变量可能存在表述差异（如"政府补贴"vs"财政补贴"），如何用向量相似度自动归并同一概念，并设计合理的置信度阈值策略。

---

## 备选方案对比

### 方案 A：OpenAI API（云端）

| 维度 | 详情 |
|------|------|
| 模型 | `text-embedding-3-small` / `text-embedding-3-large` |
| 优点 | 省心，性能稳定，多语言支持好 |
| 缺点 | 收费（$0.02/1M tokens），有延迟，依赖网络 |
| 维度 | 1536 / 3072 |
| 适用 | 快速验证，对成本不敏感 |

### 方案 B：HuggingFace 本地轻量模型（推荐）

| 维度 | 详情 |
|------|------|
| 模型 | `all-MiniLM-L6-v2` / `BAAI/bge-small-zh` |
| 优点 | 免费，本地运行，隐私好，延迟低 |
| 缺点 | 需下载模型（80-150MB），中文领域需验证 |
| 维度 | 384 / 512 |
| 适用 | **Phase 1 推荐** |

### 方案 C：领域微调 Embedding

| 维度 | 详情 |
|------|------|
| 方法 | 在政策/经济领域语料上微调预训练模型 |
| 优点 | 领域术语理解准确（如"货币政策"vs"财政政策"） |
| 缺点 | 需要领域标注数据，训练成本高 |
| 适用 | Phase 2 优化，非 MVP |

### 方案 D：混合方案

| 维度 | 详情 |
|------|------|
| 方法 | 本地轻量模型做主流程，OpenAI 做疑难 case 复核 |
| 优点 | 平衡成本与精度 |
| 缺点 | 系统复杂度增加 |
| 适用 | 大规模生产环境 |

---

## 学术/工业界实践

### 1. Sentence-BERT (Reimers & Gurevych, 2019)

**核心原理**：
- 使用 Siamese/Dual-Encoder 架构
- 对两个句子分别编码，计算余弦相似度
- 专门针对语义相似度任务微调

**常用模型**：
| 模型 | 大小 | 性能 | 适用 |
|------|------|------|------|
| `all-MiniLM-L6-v2` | 80MB | 快，质量中等 | **推荐** |
| `all-mpnet-base-v2` | 438MB | 质量高 | 精度优先 |
| `BAAI/bge-large-zh` | 1.3GB | 中文最佳 | 中文场景 |

### 2. BGE (BAAI General Embedding, 2023)

**中文优化**：
- 专门针对中文语料训练
- 在 C-MTEB 基准上表现最佳
- 支持指令微调（通过前缀指定任务）

**指令模板**（重要）：
```python
# 用于语义相似度
instruction = "为这个句子生成表示以用于计算相似度："

# 编码时添加指令前缀
emb = model.encode(instruction + text)
```

### 3. 语义归并算法

**层次聚类（推荐）**：
```python
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity

# 1. 计算所有节点对的相似度矩阵
similarity_matrix = cosine_similarity(embeddings)

# 2. 层次聚类（距离=1-相似度）
clustering = AgglomerativeClustering(
    n_clusters=None,
    distance_threshold=0.15,  # 对应相似度 0.85
    linkage='average'
)
clusters = clustering.fit_predict(1 - similarity_matrix)
```

**优点**：
- 无需预设聚类数量
- 可生成层次结构（父子关系）
- 支持软阈值（0.65-0.85 区间）

### 4. 阈值策略

**三段式阈值（推荐）**：
| 相似度区间 | 动作 | 说明 |
|------------|------|------|
| > 0.85 | **自动归并** | 高置信度，无需人工 |
| 0.65 - 0.85 | **标记待确认** | 灰色地带，人工介入 |
| < 0.65 | **保持分离** | 明显不同概念 |

**阈值选择依据**：
- 0.85：经验值，约 90% 准确率（需实验验证）
- 0.65：下限，避免过度归并

---

## 推荐方案

### Phase 1 MVP 配置

**Embedding 模型**：`all-MiniLM-L6-v2`
- 理由：80MB 轻量，速度极快（CPU 1000+ sentences/sec），质量够用
- 备选：`BAAI/bge-small-zh`（如果中文术语问题严重）

**归并算法**：层次聚类 + 三段式阈值
```python
# 伪代码
from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering

model = SentenceTransformer('all-MiniLM-L6-v2')

# 1. 编码所有节点
embeddings = model.encode(node_names)

# 2. 层次聚类
clustering = AgglomerativeClustering(
    n_clusters=None,
    distance_threshold=0.15,  # 相似度 > 0.85
    linkage='average'
)
clusters = clustering.fit_predict(1 - cosine_similarity(embeddings))

# 3. 处理待确认区间（0.65-0.85）
for pair in node_pairs:
    sim = cosine_similarity(pair)
    if 0.65 <= sim <= 0.85:
        mark_for_human_review(pair, sim)
```

**输出格式**：
```json
{
  "merged_nodes": [
    {
      "canonical_name": "政府住房补贴",
      "aliases": ["财政补贴", "购房补贴", "政府补助"],
      "source_agents": ["policy", "economic"],
      "merge_confidence": 0.92,
      "needs_review": false
    }
  ],
  "pending_review": [
    {
      "node_a": "房产税",
      "node_b": "物业税",
      "similarity": 0.72,
      "suggested_action": "合并",
      "reason": "相似度在灰色区间"
    }
  ]
}
```

---

## 待决策事项

1. **模型选择**
   - 选项 A：`all-MiniLM-L6-v2`（轻量通用）
   - 选项 B：`BAAI/bge-small-zh`（中文优化）
   - **建议**：先用 A，中文问题严重时切 B

2. **阈值数值**
   - 自动归并阈值：0.85（经验值）vs 0.80（宽松）vs 0.90（严格）
   - 人工介入上限：0.65 vs 0.70
   - **建议**：0.85 / 0.65，实验验证后调优

3. **聚类算法**
   - 选项 A：层次聚类（推荐，可解释性强）
   - 选项 B：DBSCAN（无需阈值，自动发现密度）
   - **建议**：层次聚类，DBSCAN 作为备选实验

4. **中文术语处理**
   - 选项 A：依赖模型泛化能力
   - 选项 B：构建领域同义词词典（如"房产税"="物业税"）
   - **建议**：Phase 1 选 A，Phase 2 补充 B

---

## 实验验证建议

**测试数据集**：
- 准备 50-100 对政策术语（含同义、近义、不同义）
- 人工标注相似度标签

**评估指标**：
- Precision@0.85（阈值以上真正是同义词的比例）
- Recall（发现的同义词对占全部的比例）
- 人工介入率（落在 0.65-0.85 的比例）

---

## 下一步

等待用户决策以上 4 个事项，确认后产出实现代码模板。
