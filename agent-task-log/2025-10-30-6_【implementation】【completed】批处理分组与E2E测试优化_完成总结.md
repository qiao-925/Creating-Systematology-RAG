### 任务概述
- 目标：默认启用“按目录/子模块分批”的索引流水，在每批内串行完成 分块 → 向量化（微批）→ 批量写入；增强可视化与可观测性；为测试添加前 N 批限制，加速 E2E。
- 范围：`src/indexer.py`、`src/config.py`、`Makefile`；仅最小改动，保留原有非批模式兼容路径（现不再走到）。

### 核心改动
- 批处理默认启用（移除开关依赖），索引总是先“按目录/子模块分组 → 生成批次”。
- 每批执行三段式流水：
  - 阶段1 分块：`SentenceSplitter` 按文档流式分块（加进度）
  - 阶段2 向量化+写入：优先 `insert_nodes` 批量插入；不可用则批内逐个 `insert`（含简易重试）
  - 阶段3 摘要：输出批耗时、nodes/s(it/s)、docs/s、tok/s
- 批级断点续传与重试：
  - 以“组名 + 文件列表哈希”作为 `batch_id` 写入 `persist_dir/batch_checkpoints/{collection}.json`
  - 已完成批跳过；批失败回退逐个插入，最多重试 2 次
- 测试加速：新增 `INDEX_MAX_BATCHES`，在 Makefile 的 `test-github-e2e` 中设置为 5，仅处理前 5 批。

### 配置项（新增/关键）
- `GROUP_DEPTH`：目录分组深度（默认 1）
- `DOCS_PER_BATCH`：目标每批文档数（默认 20）
- `INDEX_MAX_BATCHES`：限制最大批次数（默认 0=不限制；测试设置为 5）
- 仍生效：`EMBED_BATCH_SIZE`（建议 GPU 32–48 视显存调优）、`EMBED_MAX_LENGTH`（默认 512）

### 使用与验证
- 真实运行：不设置 `INDEX_MAX_BATCHES`（或置 0）即可全量处理；日志会出现：
  - "🧭 批处理模式已启用"（分组方式/深度/每批文档/总文档/批次数）
  - 每批：组名、docs、估算 tokens、阶段提示（分块/向量化+写入）、批总结（nodes/s=it/s、docs/s、tok/s、耗时）
  - 总结：总批次、总文档、总节点、总 tokens(估算)、平均速率
- 测试加速：
  - 直接执行 `make test-github-e2e`（已在目标中注入 `INDEX_MAX_BATCHES=5`）

### 风险与回滚
- 目录分组负载可能不均衡（大文件组更慢）：可通过 `DOCS_PER_BATCH`、后续 `NODES_PER_BATCH` 细化。
- 回滚策略：保留非批模式路径及逐个插入兼容逻辑；如需彻底移除旧分支可后续精简。

### 后续建议（可选）
- 自动调参：对 `EMBED_BATCH_SIZE` 做一次性暖机搜索，记录最优吞吐。
- 指标补充：累计层面的 ETA、分位延迟、向量库写入耗时拆分。

### 改动清单
- `src/indexer.py`：
  - 新增：目录分组与二次切分、批执行管线、批级 checkpoint、详细日志与综合速率
  - 优先 `insert_nodes`；`insert_ref_docs` 缺失时不再依赖异常路径
- `src/config.py`：
  - 新增：`GROUP_DEPTH`、`DOCS_PER_BATCH`、`INDEX_MAX_BATCHES`、`INDEX_STRATEGY` 等
- `Makefile`：
  - `test-github-e2e` 注入 `INDEX_MAX_BATCHES=5`

### 结论
- 以向量化为瓶颈的“木桶短板”优化方向清晰：保持“分块轻量化、向量化微批、写入批量”的节奏。批处理与分组用于观测、断点续传与增量边界，配合详细日志与速率指标，便于在真实 GitHub 仓库上稳定扩展与调优。


