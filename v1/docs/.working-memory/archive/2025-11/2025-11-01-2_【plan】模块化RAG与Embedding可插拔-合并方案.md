# 2025-11-01 【plan】模块化 RAG 与 Embedding 可插拔 - 合并方案

**【Task Type】**: plan
> **创建时间**: 2025-11-01  
> **背景**: 发现两个任务有重叠，需要合并规划  
> **文档类型**: 合并方案

---

## 📋 任务对比分析

### 任务1：模块化 RAG（已完成核心）

**范围**：检索层的模块化
- ✅ 检索策略可插拔（vector/bm25/hybrid）
- ✅ 后处理模块可插拔（相似度过滤、重排序）
- ✅ 配置驱动

**架构层级**：
```
查询 → [ModularQueryEngine] → Retriever → Postprocessor → LLM
```

### 任务2：Embedding 模型可插拔 + API 化（待实施）

**范围**：向量化层的模块化
- ❌ Embedding 模型可插拔（本地/API）
- ❌ 支持多种 Embedding 后端
- ❌ 独立 Embedding 服务

**架构层级**：
```
文档/查询 → [Embedding] → 向量 → Chroma
```

---

## 🔗 重叠部分识别

### 重叠点1：可插拔设计理念

**共同特征**：
- 工厂模式
- 配置驱动
- 接口抽象
- 向后兼容

**实现一致性**：
两个任务都需要统一的可插拔架构风格！

### 重叠点2：后处理模块

**模块化 RAG 中的重排序**：
```python
SentenceTransformerRerank(
    model=config.RERANK_MODEL or config.EMBEDDING_MODEL,
    top_n=self.rerank_top_n,
)
```

**问题**：重排序模块使用了 Embedding 模型！
- 当前使用相同的 embedding 模型做重排序
- 如果 Embedding 模型可插拔，重排序也需要适配

### 重叠点3：配置管理

**当前配置（config.py）**：
```python
# 模块化RAG配置
RETRIEVAL_STRATEGY = "vector"
ENABLE_RERANK = False
RERANK_MODEL = None  # ← 使用 EMBEDDING_MODEL

# Embedding配置
EMBEDDING_MODEL = "Qwen/Qwen3-Embedding-0.6B"
```

**未来配置（需要统一）**：
```python
# Embedding配置
EMBEDDING_TYPE = "local" | "api"  # 新增
EMBEDDING_MODEL = "Qwen/Qwen3-Embedding-0.6B"
EMBEDDING_API_URL = "http://localhost:8000/embed"  # 新增

# 重排序配置（依赖Embedding）
RERANK_MODEL = None  # ← 需要适配新的Embedding架构
```

### 重叠点4：轻量机 + GPU 推理机构想

**TRACKER.md 中的构想**：
> 轻量机（Web/UI）+ GPU 推理机（模型/向量/重排/OCR）

**关联性**：
- **向量化**：Embedding 模型可以部署在 GPU 推理机
- **重排序**：重排序模型也可以部署在 GPU 推理机
- **检索策略**：检索逻辑在轻量机，向量化在 GPU 机

---

## 🎯 合并方案设计

### 方案概览

**统一的可插拔架构**：

```
┌─────────────────────────────────────────────────┐
│           RAG 可插拔架构（统一设计）             │
├─────────────────────────────────────────────────┤
│                                                  │
│  1. Embedding 层（向量化）                       │
│     ├─ BaseEmbedding（抽象）                    │
│     ├─ LocalEmbedding（本地模型）               │
│     └─ APIEmbedding（远程API）                  │
│                                                  │
│  2. Retriever 层（检索策略）                     │
│     ├─ VectorRetriever                          │
│     ├─ BM25Retriever                            │
│     └─ HybridRetriever                          │
│                                                  │
│  3. Postprocessor 层（后处理）                   │
│     ├─ SimilarityPostprocessor                  │
│     └─ RerankPostprocessor（依赖Embedding）     │
│                                                  │
│  4. LLM 层（生成）                               │
│     ├─ APIBasedLLM（DeepSeek）                  │
│     └─ LocalLLM（未来扩展）                      │
│                                                  │
└─────────────────────────────────────────────────┘
```

### 核心设计原则

1. **统一的抽象层**
   - 所有可插拔模块继承统一的基类
   - 统一的接口规范

2. **配置驱动**
   - 所有模块通过配置文件选择
   - 支持环境变量和参数传递

3. **依赖注入**
   - 高层模块不依赖低层模块
   - 通过接口依赖抽象

4. **向后兼容**
   - 保持现有API不变
   - 逐步迁移，平滑升级

---

## 📐 详细设计方案

### 阶段1：Embedding 抽象层（基础）

**目标**：建立 Embedding 的可插拔基础

#### 1.1 创建抽象基类

**新文件**：`src/embeddings/base.py`

```python
from abc import ABC, abstractmethod
from typing import List

class BaseEmbedding(ABC):
    """Embedding 模型基类"""
    
    @abstractmethod
    def get_query_embedding(self, query: str) -> List[float]:
        """生成查询向量"""
        pass
    
    @abstractmethod
    def get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """批量生成文本向量"""
        pass
    
    @abstractmethod
    def get_embedding_dimension(self) -> int:
        """获取向量维度"""
        pass
```

#### 1.2 本地模型适配器

**新文件**：`src/embeddings/local_embedding.py`

```python
class LocalEmbedding(BaseEmbedding):
    """本地 HuggingFace 模型适配器（封装现有逻辑）"""
    
    def __init__(self, model_name: str, device: str = "cuda"):
        # 复用现有 HuggingFaceEmbedding 逻辑
        pass
```

#### 1.3 API 模型适配器

**新文件**：`src/embeddings/api_embedding.py`

```python
class APIEmbedding(BaseEmbedding):
    """远程 API 模型适配器"""
    
    def __init__(self, api_url: str, api_key: Optional[str] = None):
        self.api_url = api_url
        self.api_key = api_key
    
    def get_query_embedding(self, query: str) -> List[float]:
        # 调用远程 API
        response = requests.post(
            f"{self.api_url}/embed",
            json={"text": query},
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return response.json()["embedding"]
```

#### 1.4 工厂函数

**新文件**：`src/embeddings/factory.py`

```python
def create_embedding(
    embedding_type: str = None,
    model_name: str = None,
    api_url: str = None,
    **kwargs
) -> BaseEmbedding:
    """创建 Embedding 实例（工厂函数）"""
    
    embedding_type = embedding_type or config.EMBEDDING_TYPE
    
    if embedding_type == "local":
        return LocalEmbedding(
            model_name=model_name or config.EMBEDDING_MODEL,
            **kwargs
        )
    elif embedding_type == "api":
        return APIEmbedding(
            api_url=api_url or config.EMBEDDING_API_URL,
            **kwargs
        )
    else:
        raise ValueError(f"不支持的 Embedding 类型: {embedding_type}")
```

### 阶段2：集成到 ModularQueryEngine

**目标**：让模块化 RAG 使用可插拔的 Embedding

#### 2.1 修改 IndexManager

**文件**：`src/indexer.py`

```python
class IndexManager:
    def __init__(
        self,
        embedding: Optional[BaseEmbedding] = None,  # 新增参数
        **kwargs
    ):
        # 如果没有传入 embedding，使用工厂创建
        if embedding is None:
            from src.embeddings.factory import create_embedding
            embedding = create_embedding()
        
        self.embed_model = embedding
```

#### 2.2 修改 ModularQueryEngine

**文件**：`src/modular_query_engine.py`

```python
class ModularQueryEngine:
    def _create_postprocessors(self) -> List:
        """创建后处理器"""
        postprocessors = []
        
        # 相似度过滤
        postprocessors.append(
            SimilarityPostprocessor(similarity_cutoff=self.similarity_cutoff)
        )
        
        # 重排序（使用 Embedding）
        if self.enable_rerank:
            # 从 index_manager 获取 embedding 实例
            rerank_embedding = self.index_manager.embed_model
            
            postprocessors.append(
                SentenceTransformerRerank(
                    model=rerank_embedding,  # 使用统一的 Embedding
                    top_n=self.rerank_top_n,
                )
            )
        
        return postprocessors
```

### 阶段3：独立 Embedding 服务（可选）

**目标**：支持 GPU 推理机部署

#### 3.1 服务端（GPU 机）

**新文件**：`embedding_service/server.py`

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI(title="Embedding Service")

class EmbedRequest(BaseModel):
    texts: List[str]

class EmbedResponse(BaseModel):
    embeddings: List[List[float]]
    dimension: int

@app.post("/embed", response_model=EmbedResponse)
async def embed_texts(request: EmbedRequest):
    """生成文本向量"""
    # 调用本地模型
    embeddings = embedding_model.get_text_embeddings(request.texts)
    return EmbedResponse(
        embeddings=embeddings,
        dimension=len(embeddings[0])
    )

@app.get("/models")
async def list_models():
    """列出可用模型"""
    return {
        "models": [
            {"name": "qwen-embedding", "dimension": 768},
            {"name": "bge-base-zh", "dimension": 768},
        ]
    }
```

#### 3.2 客户端（轻量机）

**使用方式**：

```python
# 配置
EMBEDDING_TYPE = "api"
EMBEDDING_API_URL = "http://gpu-server:8000"

# 自动使用 APIEmbedding
engine = ModularQueryEngine(index_manager)
```

### 阶段4：配置统一管理

**文件**：`src/config.py`

```python
class Config:
    # ===== Embedding配置 =====
    
    # Embedding类型: "local" | "api"
    EMBEDDING_TYPE = os.getenv("EMBEDDING_TYPE", "local")
    
    # 本地模型配置
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-0.6B")
    
    # API配置
    EMBEDDING_API_URL = os.getenv("EMBEDDING_API_URL", "http://localhost:8000")
    EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", None)
    
    # ===== 模块化RAG配置 =====
    
    RETRIEVAL_STRATEGY = os.getenv("RETRIEVAL_STRATEGY", "vector")
    ENABLE_RERANK = os.getenv("ENABLE_RERANK", "false").lower() == "true"
    RERANK_MODEL = None  # 使用 Embedding 实例，不再需要单独配置
```

---

## 📅 实施计划（合并后）

### 阶段划分

| 阶段 | 任务 | 工作量 | 依赖 |
|------|------|--------|------|
| **✅ 已完成** | 模块化RAG核心 | 2h | - |
| **阶段1** | Embedding抽象层 | 3h | - |
| **阶段2** | 集成到ModularQueryEngine | 2h | 阶段1 |
| **阶段3** | 独立Embedding服务 | 4h | 阶段2 |
| **阶段4** | 配置统一 + 测试 | 3h | 阶段2 |

**总计**：约 14 小时（2 个工作日）

### 详细任务

#### 阶段1：Embedding 抽象层（3h）

- [ ] 创建 `BaseEmbedding` 抽象类
- [ ] 实现 `LocalEmbedding` 适配器（封装现有逻辑）
- [ ] 实现 `APIEmbedding` 适配器
- [ ] 实现工厂函数 `create_embedding`
- [ ] 编写单元测试

#### 阶段2：集成到 ModularQueryEngine（2h）

- [ ] 修改 `IndexManager` 支持传入 Embedding
- [ ] 修改 `ModularQueryEngine` 的重排序逻辑
- [ ] 更新工厂函数
- [ ] 测试集成

#### 阶段3：独立 Embedding 服务（4h）

- [ ] 创建 FastAPI 服务端
- [ ] 实现 `/embed` 接口
- [ ] 实现模型管理
- [ ] 部署文档
- [ ] 性能测试

#### 阶段4：配置统一 + 测试（3h）

- [ ] 统一配置管理
- [ ] 更新环境变量示例
- [ ] 完整集成测试
- [ ] 性能对比测试
- [ ] 文档更新

---

## 🎯 合并后的优势

### 1. 统一的可插拔架构

**一致性**：
- Embedding 层、Retriever 层、Postprocessor 层都使用相同的设计模式
- 降低理解成本和维护成本

### 2. 解耦部署

**灵活性**：
```
[轻量机]                    [GPU 推理机]
  Web UI                     Embedding 服务
  检索逻辑          ←─────→  向量化
  后处理链                   重排序
  LLM API调用                （可选）OCR服务
```

### 3. 降低成本

**成本优化**：
- 轻量机：低配置（1核1G），仅运行 Web 和检索逻辑
- GPU 机：自托管或按需使用，承载重计算任务
- 估算节省：30-50% 部署成本

### 4. 渐进式演进

**平滑升级**：
1. ✅ 第一步：模块化 RAG（已完成）
2. 🎯 第二步：Embedding 可插拔（本方案）
3. 🔮 第三步：LLM 可插拔（未来）
4. 🚀 第四步：完整的插件化系统

---

## ❓ 需要决策的问题

### 问题1：实施优先级

**选项 A**：立即实施全部阶段（2个工作日）
- ✅ 一次性完成，架构完整
- ❌ 工作量大，风险稍高

**选项 B**：分步实施
- 先实施阶段1-2（Embedding抽象 + 集成）
- 验证效果后再实施阶段3（独立服务）
- ✅ 风险低，可控
- ❌ 需要分两次迭代

### 问题2：Embedding 服务部署

**选项 A**：立即部署独立服务
- 适合有 GPU 资源的情况
- 可以立即享受解耦部署的好处

**选项 B**：暂时保持本地模式
- 先完成抽象层设计
- 为未来部署留好接口
- 降低初期复杂度

### 问题3：API 后端支持

需要支持哪些 API 后端？
- [ ] 自建 Embedding 服务（FastAPI）
- [ ] OpenAI Embeddings
- [ ] Cohere Embeddings
- [ ] 其他（请指定）

### 问题4：兼容性策略

切换 Embedding 模型后，向量维度可能不同：

**选项 A**：重建索引
- 切换模型后强制重建
- 简单直接

**选项 B**：多版本共存
- 支持不同模型的索引并存
- 复杂但灵活

---

## 🚀 推荐方案

基于你的需求和风险控制，我推荐：

### 推荐配置

1. **实施优先级**: **选项 B（分步实施）**
   - 先完成阶段1-2（约1天）
   - 验证后再决定是否实施阶段3

2. **部署方式**: **选项 B（暂时本地）**
   - 完成抽象层设计，留好接口
   - 等有 GPU 资源时再部署服务

3. **API 后端**: 
   - 优先支持自建服务
   - 预留 OpenAI/Cohere 接口（未来扩展）

4. **兼容性**: **选项 A（重建索引）**
   - 切换模型时提示用户重建
   - 简单可靠

### 实施路径

```
Week 1:
  ✅ Day 1-2: 模块化RAG（已完成）
  🎯 Day 3: Embedding抽象层（阶段1）
  🎯 Day 4: 集成到ModularQueryEngine（阶段2）
  
Week 2+:
  🔮 根据需要实施独立服务（阶段3）
```

---

## 📄 相关文档

- 📄 [模块化RAG实施方案](2025-10-31-9_模块化RAG实施方案_实施方案.md)
- 📄 [模块化RAG核心实现总结](2025-11-01-1_模块化RAG核心实现_完成总结.md)
- 📄 [TRACKER.md](../docs/TRACKER.md) - 任务追踪

---

**文档创建时间**: 2025-11-01  
**下一步**: 等待决策，确定实施优先级

