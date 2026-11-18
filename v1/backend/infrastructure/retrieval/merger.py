"""
RAG引擎检索模块 - 结果合并器：支持多种合并策略

主要功能：
- ResultMerger类：结果合并器，支持RRF、加权分数融合、简单拼接等策略
- merge()：合并多个检索策略的结果

执行流程：
1. 接收多个检索策略的结果
2. 根据合并策略处理结果
3. 去重和排序
4. 返回Top-K合并结果

特性：
- Reciprocal Rank Fusion (RRF) - 倒数排名融合
- Weighted Score Fusion - 加权分数融合
- Simple Concatenation - 简单拼接
- 去重和排序
"""

import hashlib
from typing import Dict, List, Optional
from llama_index.core.schema import NodeWithScore, TextNode

from backend.infrastructure.logger import get_logger

logger = get_logger('rag_engine.retrieval')


class ResultMerger:
    """结果合并器
    
    支持多种合并策略：
    1. Reciprocal Rank Fusion (RRF) - 倒数排名融合
    2. Weighted Score Fusion - 加权分数融合
    3. Simple Concatenation - 简单拼接
    """
    
    def __init__(
        self,
        strategy: str = "reciprocal_rank_fusion",
        weights: Optional[Dict[str, float]] = None,
        enable_deduplication: bool = True,
        rrf_k: int = 60,
    ):
        """初始化结果合并器
        
        Args:
            strategy: 合并策略（"reciprocal_rank_fusion" | "weighted_score" | "simple"）
            weights: 各检索器的权重（可选）
            enable_deduplication: 是否启用去重
            rrf_k: RRF算法的常数k（默认60）
        """
        self.strategy = strategy
        self.weights = weights or {}
        self.enable_deduplication = enable_deduplication
        self.rrf_k = rrf_k
        
        logger.info(
            f"结果合并器初始化: "
            f"策略={strategy}, "
            f"去重={enable_deduplication}, "
            f"权重={weights}"
        )
    
    def merge(
        self,
        results_dict: Dict[str, List[NodeWithScore]],
        top_k: int = 10,
    ) -> List[NodeWithScore]:
        """合并多个检索结果
        
        Args:
            results_dict: {retriever_name: [NodeWithScore]}
            top_k: 返回Top-K结果
            
        Returns:
            合并后的结果列表
        """
        if not results_dict:
            return []
        
        # 根据策略合并
        match self.strategy:
            case "reciprocal_rank_fusion":
                merged = self._reciprocal_rank_fusion(results_dict, top_k)
            case "weighted_score":
                merged = self._weighted_score_fusion(results_dict, top_k)
            case _:
                merged = self._simple_concatenation(results_dict, top_k)
        
        # 去重
        if self.enable_deduplication:
            merged = self._deduplicate(merged)
        
        return merged[:top_k]
    
    def _reciprocal_rank_fusion(
        self,
        results_dict: Dict[str, List[NodeWithScore]],
        top_k: int,
    ) -> List[NodeWithScore]:
        """倒数排名融合（RRF）
        
        公式：RRF_score = Σ(weight / (k + rank))
        k是常数（通常为60），rank是排名（从1开始）
        """
        node_scores = {}  # {node_id: rrf_score}
        node_map = {}  # {node_id: NodeWithScore}
        
        for retriever_name, results in results_dict.items():
            weight = self.weights.get(retriever_name, 1.0)
            
            for rank, node_with_score in enumerate(results, start=1):
                node_id = self._get_node_id(node_with_score.node)
                
                # 计算RRF分数
                rrf_score = weight / (self.rrf_k + rank)
                
                if node_id in node_scores:
                    node_scores[node_id] += rrf_score
                else:
                    node_scores[node_id] = rrf_score
                    node_map[node_id] = node_with_score
        
        # 转换为NodeWithScore列表并排序
        merged_nodes = []
        for node_id, score in sorted(node_scores.items(), key=lambda x: x[1], reverse=True):
            node_with_score = node_map[node_id]
            # 使用合并后的分数创建新的NodeWithScore
            merged_nodes.append(NodeWithScore(node=node_with_score.node, score=score))
        
        return merged_nodes
    
    def _weighted_score_fusion(
        self,
        results_dict: Dict[str, List[NodeWithScore]],
        top_k: int,
    ) -> List[NodeWithScore]:
        """加权分数融合"""
        node_scores = {}
        node_map = {}
        
        for retriever_name, results in results_dict.items():
            weight = self.weights.get(retriever_name, 1.0)
            
            for node_with_score in results:
                node_id = self._get_node_id(node_with_score.node)
                weighted_score = node_with_score.score * weight
                
                if node_id in node_scores:
                    # 取最大值（或其他策略）
                    node_scores[node_id] = max(node_scores[node_id], weighted_score)
                else:
                    node_scores[node_id] = weighted_score
                    node_map[node_id] = node_with_score
        
        # 排序并返回
        merged_nodes = []
        for node_id, score in sorted(node_scores.items(), key=lambda x: x[1], reverse=True):
            node_with_score = node_map[node_id]
            merged_nodes.append(NodeWithScore(node=node_with_score.node, score=score))
        
        return merged_nodes
    
    def _simple_concatenation(
        self,
        results_dict: Dict[str, List[NodeWithScore]],
        top_k: int,
    ) -> List[NodeWithScore]:
        """简单拼接（按顺序合并）"""
        all_nodes = []
        
        for results in results_dict.values():
            all_nodes.extend(results)
        
        # 去重（基于节点ID）
        seen = set()
        unique_nodes = []
        for node_with_score in all_nodes:
            node_id = self._get_node_id(node_with_score.node)
            if node_id not in seen:
                seen.add(node_id)
                unique_nodes.append(node_with_score)
        
        return unique_nodes
    
    def _deduplicate(self, nodes: List[NodeWithScore]) -> List[NodeWithScore]:
        """去重（基于节点内容）"""
        seen = set()
        unique_nodes = []
        
        for node_with_score in nodes:
            node_id = self._get_node_id(node_with_score.node)
            if node_id not in seen:
                seen.add(node_id)
                unique_nodes.append(node_with_score)
        
        return unique_nodes
    
    def _get_node_id(self, node: TextNode) -> str:
        """获取节点的唯一ID
        
        基于节点内容和元数据生成hash
        """
        # 使用节点内容和关键元数据生成ID
        content = node.text or ""
        metadata_str = str(node.metadata.get("file_path", ""))
        
        # 如果有node_id，优先使用
        if hasattr(node, 'node_id') and node.node_id:
            return node.node_id
        
        # 否则生成hash
        id_string = f"{content}|{metadata_str}"
        return hashlib.md5(id_string.encode('utf-8')).hexdigest()
