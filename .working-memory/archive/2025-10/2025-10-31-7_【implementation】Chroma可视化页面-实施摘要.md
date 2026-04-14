# 2025-10-31 【implementation】## Chroma 可视化页面（方案A）- 实施摘要

**【Task Type】**: implementation
- 时间: 2025-10-31
- 目标: 在现有 Streamlit 多页面应用中，新增只读“Chroma Viewer”页面，支持集合列表、抽样预览、相似检索，不触发删除/重建。

#### 关键实现
- 新增: `pages/3_🔎_Chroma_Viewer.py`
  - 连接方式: `chromadb.PersistentClient(path=config.VECTOR_STORE_PATH)`
  - 列表: 显示集合名、计数、metadata 中的 embedding 维度
  - 抽样: `collection.peek(limit=N)`，展示 ids/metadatas/documents，安全推断样本向量维度
  - 检索: 仅计算查询向量（`src.indexer.load_embedding_model()`）→ `collection.query(query_embeddings=[...], n_results=K)`，避免 `IndexManager` 的维度校验副作用
  - 兼容: 处理旧版 Chroma 对 include/offset 的兼容降级

#### 使用方式
- 启动应用后，侧栏进入“Chroma Viewer”：
  - 选择集合 → 抽样预览 → 输入查询文本进行相似检索

#### 注意
- 页面全程只读，未对向量库执行写入或删除操作。
- 若本地 `chromadb` 未安装，页面会提示错误信息。
