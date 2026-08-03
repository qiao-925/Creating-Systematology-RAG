"""
RAG引擎重排序模块 - SentenceTransformer重排序器：基于句子嵌入的重排序实现

主要功能：
- SentenceTransformerReranker类：基于句子嵌入的重排序器适配器

执行流程：
1. 初始化SentenceTransformer模型
2. 对检索结果进行重排序
3. 返回Top-N结果

特性：
- 基于交叉编码器（Cross-Encoder）
- 支持多种模型
- LlamaIndex兼容接口
"""

from typing import List, Optional
from llama_index.core.schema import NodeWithScore, QueryBundle
from llama_index.core.postprocessor import SentenceTransformerRerank

from backend.infrastructure.reranking.base import BaseReranker
from backend.infrastructure.config import config
from backend.infrastructure.logger import get_logger

logger = get_logger('rag_engine.reranking.sentence_transformer')


class SentenceTransformerReranker(BaseReranker):
    """SentenceTransformer重排序器适配器
    
    基于句子嵌入的重排序，使用交叉编码器（Cross-Encoder）
    推荐模型：
    - BAAI/bge-reranker-base
    - BAAI/bge-reranker-large
    - cross-encoder/ms-marco-MiniLM-L-12-v2
    """
    
    def __init__(
        self,
        model: Optional[str] = None,
        top_n: Optional[int] = None,
        device: Optional[str] = None,
    ):
        """初始化SentenceTransformer重排序器
        
        Args:
            model: 模型名称（默认使用配置）
            top_n: 返回Top-N数量（默认使用配置）
            device: 设备（cuda/cpu，默认自动检测）
        """
        self.model_name = model or config.RERANK_MODEL or config.EMBEDDING_MODEL
        top_n_value = top_n or config.RERANK_TOP_N
        
        super().__init__(name=self.model_name, top_n=top_n_value)
        self.device = device
        
        logger.info(f"📦 初始化SentenceTransformer重排序器")
        logger.info(f"   模型: {self.model_name}")
        logger.info(f"   Top-N: {self.top_n}")
        
        # 创建LlamaIndex的SentenceTransformerRerank实例
        reranker_kwargs = {
            "model": self.model_name,
            "top_n": self.top_n,
        }
        if device:
            reranker_kwargs["device"] = device
            
        self._reranker = SentenceTransformerRerank(**reranker_kwargs)
        
        logger.info(f"✅ 重排序器加载完成")
    
    def rerank(
        self,
        nodes: List[NodeWithScore],
        query: QueryBundle,
    ) -> List[NodeWithScore]:
        """重排序节点"""
        if not nodes:
            return []
        
        logger.debug(f"重排序: {len(nodes)} 个节点")
        return self._reranker.postprocess_nodes(nodes, query)
    
    def get_llama_index_postprocessor(self):
        """返回LlamaIndex兼容的Postprocessor"""
        return self._reranker
