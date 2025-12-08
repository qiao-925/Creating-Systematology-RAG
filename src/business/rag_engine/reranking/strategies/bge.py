"""
RAG引擎重排序模块 - BGE重排序器：基于BGE模型的重排序实现

主要功能：
- BGEReranker类：BGE重排序器适配器

执行流程：
1. 初始化BGE模型
2. 对检索结果进行重排序
3. 返回Top-N结果

特性：
- 基于BAAI General Embedding模型
- 支持FP16加速
- LlamaIndex兼容接口
"""

from typing import List, Optional
from llama_index.core.schema import NodeWithScore, QueryBundle

from src.business.rag_engine.reranking.base import BaseReranker
from src.infrastructure.config import config
from src.infrastructure.logger import get_logger

logger = get_logger('rag_engine.reranking.bge')


class BGEReranker(BaseReranker):
    """BGE重排序器适配器
    
    BGE（BAAI General Embedding）重排序器
    推荐模型：
    - BAAI/bge-reranker-base
    - BAAI/bge-reranker-large
    - BAAI/bge-reranker-v2-m3
    """
    
    def __init__(
        self,
        model: Optional[str] = None,
        top_n: Optional[int] = None,
        use_fp16: bool = True,
    ):
        """初始化BGE重排序器
        
        Args:
            model: 模型名称（默认BAAI/bge-reranker-base）
            top_n: 返回Top-N数量
            use_fp16: 是否使用FP16精度（加速推理）
        """
        self.model_name = model or "BAAI/bge-reranker-base"
        top_n_value = top_n or config.RERANK_TOP_N
        
        super().__init__(name=self.model_name, top_n=top_n_value)
        self.use_fp16 = use_fp16
        
        logger.info(f"📦 初始化BGE重排序器")
        logger.info(f"   模型: {self.model_name}")
        logger.info(f"   Top-N: {self.top_n}")
        logger.info(f"   FP16: {self.use_fp16}")
        
        # 尝试导入FlagEmbeddingReranker
        try:
            from llama_index.postprocessor.flag_embedding_reranker import FlagEmbeddingReranker
            
            # 创建FlagEmbeddingReranker实例
            self._reranker = FlagEmbeddingReranker(
                model=self.model_name,
                top_n=self.top_n,
                use_fp16=self.use_fp16,
            )
            
            logger.info(f"✅ BGE重排序器加载完成")
        except ImportError:
            logger.error("FlagEmbeddingReranker未安装，请运行: pip install llama-index-postprocessor-flag-embedding")
            raise ImportError(
                "FlagEmbeddingReranker未安装。请运行: pip install llama-index-postprocessor-flag-embedding"
            )
    
    def rerank(
        self,
        nodes: List[NodeWithScore],
        query: QueryBundle,
    ) -> List[NodeWithScore]:
        """重排序节点"""
        if not nodes:
            return []
        
        logger.debug(f"BGE重排序: {len(nodes)} 个节点")
        return self._reranker.postprocess_nodes(nodes, query)
    
    def get_llama_index_postprocessor(self):
        """返回LlamaIndex兼容的Postprocessor"""
        return self._reranker
