"""
重排序器基类
"""

from abc import ABC, abstractmethod
from typing import List, Any

from src.business.protocols import RerankingModule, PipelineContext
from src.logger import setup_logger

logger = setup_logger('reranker')


class Reranker(RerankingModule):
    """重排序器基类"""
    
    def __init__(self, name: str = "reranker", top_k: int = 5):
        super().__init__(name)
        self.top_k = top_k
    
    def execute(self, context: PipelineContext) -> PipelineContext:
        """执行重排序"""
        logger.info(f"执行重排序: docs={len(context.retrieved_docs)}")
        
        try:
            if not context.retrieved_docs:
                logger.warning("没有文档需要重排序")
                return context
            
            # 重排序
            reranked = self.rerank(context.query, context.retrieved_docs)
            context.reranked_docs = reranked[:self.top_k]
            context.set_metadata('reranking_done', True)
            
            logger.info(f"重排序完成: {len(context.reranked_docs)}个文档")
            
        except Exception as e:
            logger.error(f"重排序失败: {e}")
            context.set_error(f"重排序失败: {str(e)}")
        
        return context
