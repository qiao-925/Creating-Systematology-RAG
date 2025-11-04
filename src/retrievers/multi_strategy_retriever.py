"""
多策略检索器

并行执行多种检索策略，然后合并结果
"""

import concurrent.futures
from typing import List, Dict, Optional
from llama_index.core.schema import NodeWithScore

from src.retrievers.result_merger import ResultMerger
from src.logger import setup_logger

logger = setup_logger('multi_strategy_retriever')


class BaseRetriever:
    """检索器基类（接口定义）
    
    所有检索器都应实现retrieve方法
    """
    
    def __init__(self, name: str):
        """初始化检索器
        
        Args:
            name: 检索器名称
        """
        self.name = name
    
    def retrieve(self, query: str, top_k: int = 10) -> List[NodeWithScore]:
        """执行检索
        
        Args:
            query: 查询文本
            top_k: 返回Top-K结果
            
        Returns:
            检索结果列表
        """
        raise NotImplementedError("子类必须实现retrieve方法")


class MultiStrategyRetriever(BaseRetriever):
    """多策略检索器
    
    并行执行多种检索策略，然后合并结果
    
    Examples:
        >>> retrievers = [vector_retriever, bm25_retriever, grep_retriever]
        >>> multi_retriever = MultiStrategyRetriever(
        ...     retrievers=retrievers,
        ...     merge_strategy="reciprocal_rank_fusion",
        ...     weights={"vector": 1.0, "bm25": 0.8, "grep": 0.6}
        ... )
        >>> results = multi_retriever.retrieve("系统科学", top_k=10)
    """
    
    def __init__(
        self,
        retrievers: List[BaseRetriever],
        merge_strategy: str = "reciprocal_rank_fusion",
        weights: Optional[Dict[str, float]] = None,
        enable_deduplication: bool = True,
        max_workers: int = 4,
    ):
        """初始化多策略检索器
        
        Args:
            retrievers: 检索器列表
            merge_strategy: 合并策略（"reciprocal_rank_fusion" | "weighted_score" | "simple"）
            weights: 各检索器的权重（可选）
            enable_deduplication: 是否启用去重
            max_workers: 并行执行的最大线程数
        """
        super().__init__("multi_strategy")
        self.retrievers = retrievers
        self.merge_strategy = merge_strategy
        self.weights = weights or {}
        self.enable_deduplication = enable_deduplication
        self.max_workers = max_workers
        
        # 如果没有提供权重，为每个检索器设置默认权重
        if not self.weights:
            self.weights = {retriever.name: 1.0 for retriever in retrievers}
        
        # 创建结果合并器
        self.merger = ResultMerger(
            strategy=merge_strategy,
            weights=self.weights,
            enable_deduplication=enable_deduplication,
        )
        
        retriever_names = [r.name for r in retrievers]
        logger.info(
            f"🔀 多策略检索器初始化: "
            f"启用的策略={retriever_names}, "
            f"策略数量={len(retrievers)}, "
            f"合并策略={merge_strategy}, "
            f"权重分配={self.weights}, "
            f"去重={'启用' if enable_deduplication else '禁用'}, "
            f"原因=使用多策略并行检索，融合不同检索方法的优势以提升召回率"
        )
    
    def retrieve(self, query: str, top_k: int = 10) -> List[NodeWithScore]:
        """执行多策略检索
        
        Args:
            query: 查询文本
            top_k: 返回Top-K结果
            
        Returns:
            合并后的检索结果
        """
        # 并行执行所有检索策略
        all_results = self._parallel_retrieve(query, top_k)
        
        # 记录各策略的检索结果
        strategy_results_summary = {
            name: len(results) 
            for name, results in all_results.items()
        }
        
        # 合并结果
        merged_results = self.merger.merge(all_results, top_k=top_k)
        
        total_retrieved = sum(len(r) for r in all_results.values())
        logger.info(
            f"🔀 多策略检索完成: "
            f"查询={query[:50]}..., "
            f"各策略结果数={strategy_results_summary}, "
            f"总检索结果数={total_retrieved}, "
            f"合并策略={self.merge_strategy}, "
            f"合并后结果数={len(merged_results)}, "
            f"原因=并行执行多种检索策略并通过{self.merge_strategy}融合结果，"
            f"提升召回率和准确性"
        )
        
        return merged_results
    
    def _parallel_retrieve(
        self,
        query: str,
        top_k: int,
    ) -> Dict[str, List[NodeWithScore]]:
        """并行执行所有检索策略"""
        all_results = {}
        
        def retrieve_with_name(retriever: BaseRetriever):
            """检索包装函数"""
            try:
                results = retriever.retrieve(query, top_k=top_k)
                logger.debug(
                    f"  ✓ {retriever.name}策略检索完成: "
                    f"结果数={len(results)}, "
                    f"权重={self.weights.get(retriever.name, 1.0)}"
                )
                return retriever.name, results
            except Exception as e:
                logger.warning(
                    f"  ✗ 检索器 {retriever.name} 失败: {e}, "
                    f"原因=检索过程中发生异常，将使用其他策略的结果"
                )
                return retriever.name, []
        
        # 使用线程池并行执行
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(retrieve_with_name, retriever): retriever.name
                for retriever in self.retrievers
            }
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    retriever_name, results = future.result()
                    all_results[retriever_name] = results
                except Exception as e:
                    retriever_name = futures[future]
                    logger.error(f"检索器 {retriever_name} 执行异常: {e}")
                    all_results[retriever_name] = []
        
        return all_results

