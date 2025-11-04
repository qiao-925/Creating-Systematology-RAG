"""
查询路由器 - 自动路由模式

基于LlamaIndex的auto_routed模式，智能选择检索策略
轻量级Agent路由层，根据查询意图自动选择检索模式
"""

from typing import Optional, List, Dict, Any
from llama_index.core.schema import QueryBundle, NodeWithScore

from src.indexer import IndexManager
from src.logger import setup_logger
from src.config import config
from src.retrievers.file_level_retrievers import (
    FilesViaContentRetriever,
    FilesViaMetadataRetriever,
)

logger = setup_logger('query_router')


class QueryRouter:
    """查询路由器 - 自动路由模式
    
    基于LlamaIndex的auto_routed模式，智能选择检索策略
    轻量级Agent路由层，根据查询意图自动选择检索模式
    
    支持的检索模式：
    - chunk: 精确信息查询（默认）
    - files_via_metadata: 文件名查询
    - files_via_content: 宽泛主题查询
    """
    
    def __init__(
        self,
        index_manager: IndexManager,
        llm=None,
        enable_auto_routing: bool = True,
    ):
        """初始化查询路由器
        
        Args:
            index_manager: 索引管理器
            llm: 用于查询分类的LLM（可选，默认使用DeepSeek）
            enable_auto_routing: 是否启用自动路由
        """
        self.index_manager = index_manager
        self.enable_auto_routing = enable_auto_routing
        
        # 延迟初始化LLM
        self._llm = llm
        self._llm_initialized = False
        
        # 检索器缓存
        self._chunk_retriever = None
        self._files_via_metadata_retriever = None
        self._files_via_content_retriever = None
        
        logger.info(f"查询路由器初始化: auto_routing={enable_auto_routing}")
    
    def route(self, query: str, top_k: int = 5) -> tuple:
        """路由查询到合适的检索器
        
        Args:
            query: 用户查询
            top_k: 返回Top-K结果
            
        Returns:
            (retriever, routing_decision): 检索器实例和路由决策
        """
        return self.route_with_understanding(query, understanding=None, top_k=top_k)
    
    def route_with_understanding(
        self, 
        query: str, 
        understanding: Optional[Dict[str, Any]] = None,
        top_k: int = 5
    ) -> tuple:
        """路由查询到合适的检索器（基于意图理解结果）
        
        Args:
            query: 用户查询（可能是改写后的查询）
            understanding: 意图理解结果（可选，如果提供则基于此选择策略）
            top_k: 返回Top-K结果
            
        Returns:
            (retriever, routing_decision): 检索器实例和路由决策
        """
        if not self.enable_auto_routing:
            # 禁用自动路由，返回默认chunk检索器
            logger.info(
                f"🔀 查询路由决策: "
                f"查询={query[:50]}..., "
                f"决策=chunk, "
                f"原因=自动路由已禁用，使用默认chunk检索器"
            )
            return self._get_chunk_retriever(top_k), "chunk"
        
        # 如果有意图理解结果，优先使用
        if understanding:
            routing_decision, decision_reason = self._analyze_with_understanding(
                query, understanding
            )
        else:
            # 否则使用规则匹配
            routing_decision, decision_reason = self._analyze_query(query)
        
        logger.info(
            f"🔀 查询路由决策: "
            f"查询={query[:50]}..., "
            f"决策={routing_decision}, "
            f"原因={decision_reason}"
        )
        
        # 根据决策返回对应检索器
        if routing_decision == "files_via_metadata":
            return self._get_files_via_metadata_retriever(top_k), "files_via_metadata"
        elif routing_decision == "files_via_content":
            return self._get_files_via_content_retriever(top_k), "files_via_content"
        else:
            return self._get_chunk_retriever(top_k), "chunk"
    
    def _analyze_with_understanding(
        self, 
        query: str, 
        understanding: Dict[str, Any]
    ) -> tuple:
        """基于意图理解结果分析查询
        
        Args:
            query: 用户查询
            understanding: 意图理解结果
            
        Returns:
            (决策, 原因)
        """
        query_type = understanding.get("query_type", "factual")
        complexity = understanding.get("complexity", "medium")
        
        # 基于查询类型选择策略
        if query_type == "specific":
            # 特定查询（精确匹配、文件名）
            reason = (
                f"基于意图理解（类型={query_type}）, "
                f"判断为文件级别元数据查询"
            )
            return "files_via_metadata", reason
        
        elif query_type == "exploratory":
            # 探索性查询（概述、介绍）
            reason = (
                f"基于意图理解（类型={query_type}）, "
                f"判断为文件级别内容查询"
            )
            return "files_via_content", reason
        
        else:
            # 其他类型（factual/comparative/explanatory）使用chunk
            reason = (
                f"基于意图理解（类型={query_type}, 复杂度={complexity}）, "
                f"使用chunk检索模式进行精确信息查询"
            )
            return "chunk", reason
    
    def _analyze_query(self, query: str) -> tuple:
        """分析查询，返回检索模式决策和决策原因
        
        Returns:
            (决策, 原因): ("chunk" | "files_via_metadata" | "files_via_content", 决策原因说明)
        """
        # 简单的规则匹配（第一阶段实现）
        # 后续可以升级为LLM分类
        
        query_lower = query.lower()
        matched_keywords = []
        
        # 检查是否包含文件名关键词
        file_keywords = ["文件", "文档", "pdf", "md", "txt", ".py", ".md", ".pdf"]
        matched_file_keywords = [kw for kw in file_keywords if kw in query_lower]
        
        if matched_file_keywords:
            matched_keywords.extend(matched_file_keywords)
            # 检查是否明确提到文件名
            content_keywords = ["的", "说", "内容", "讲"]
            matched_content_keywords = [kw for kw in content_keywords if kw in query]
            
            if matched_content_keywords:
                reason = (
                    f"检测到文件名关键词: {matched_file_keywords}, "
                    f"以及内容查询关键词: {matched_content_keywords}, "
                    f"判断为文件级别元数据查询"
                )
                return "files_via_metadata", reason
        
        # 检查是否是宽泛主题查询
        broad_indicators = [
            "什么是", "如何", "介绍", "概述", "总结", "说明",
            "概述", "背景", "历史", "发展", "前景", "未来"
        ]
        matched_broad_indicators = [ind for ind in broad_indicators if ind in query_lower]
        
        if matched_broad_indicators:
            reason = (
                f"检测到宽泛主题查询关键词: {matched_broad_indicators}, "
                f"判断为文件级别内容查询"
            )
            return "files_via_content", reason
        
        # 默认使用chunk模式
        if matched_keywords:
            reason = (
                f"检测到文件名关键词: {matched_keywords}, "
                f"但未匹配到文件级别查询模式, "
                f"使用默认chunk检索模式进行精确信息查询"
            )
        else:
            reason = (
                f"未匹配到特殊查询模式, "
                f"使用默认chunk检索模式进行精确信息查询"
            )
        return "chunk", reason
    
    def _get_chunk_retriever(self, top_k: int):
        """获取chunk检索器"""
        if self._chunk_retriever is None:
            index = self.index_manager.get_index()
            self._chunk_retriever = index.as_retriever(similarity_top_k=top_k)
        return self._chunk_retriever
    
    def _get_files_via_metadata_retriever(self, top_k: int):
        """获取files_via_metadata检索器
        
        使用文件级别元数据检索器，根据文件名/路径匹配检索文件内容
        """
        if self._files_via_metadata_retriever is None:
            self._files_via_metadata_retriever = FilesViaMetadataRetriever(
                index_manager=self.index_manager,
                top_k_per_file=max(3, top_k // 2),  # 每个文件保留的chunks数量
                similarity_top_k=top_k * 2,  # 初始检索数量
            )
            logger.info(
                f"文件级别元数据检索器已创建: "
                f"top_k_per_file={self._files_via_metadata_retriever.top_k_per_file}, "
                f"similarity_top_k={self._files_via_metadata_retriever.similarity_top_k}"
            )
        return self._files_via_metadata_retriever
    
    def _get_files_via_content_retriever(self, top_k: int):
        """获取files_via_content检索器
        
        使用文件级别内容检索器，通过语义检索找到相关文件，再检索文件内容
        """
        if self._files_via_content_retriever is None:
            # 计算参数：假设最多返回 top_k 个结果，平均分配给文件
            top_k_files = max(3, top_k // 3)  # 文件数量
            top_k_per_file = max(2, top_k // top_k_files)  # 每个文件的chunks数量
            
            self._files_via_content_retriever = FilesViaContentRetriever(
                index_manager=self.index_manager,
                top_k_files=top_k_files,
                top_k_per_file=top_k_per_file,
                similarity_top_k=top_k * 5,  # 初始检索更多chunks用于文件筛选
            )
            logger.info(
                f"文件级别内容检索器已创建: "
                f"top_k_files={top_k_files}, "
                f"top_k_per_file={top_k_per_file}, "
                f"similarity_top_k={self._files_via_content_retriever.similarity_top_k}"
            )
        return self._files_via_content_retriever
    
    def _initialize_llm(self):
        """初始化LLM（延迟加载）"""
        if self._llm_initialized:
            return
        
        if self._llm is None:
            try:
                from llama_index.llms.deepseek import DeepSeek
                from src.config import config
                
                self._llm = DeepSeek(
                    api_key=config.DEEPSEEK_API_KEY,
                    model=config.LLM_MODEL,
                    temperature=0.3,  # 低温度用于分类任务
                )
                logger.info("查询路由器LLM已初始化")
            except Exception as e:
                logger.warning(f"查询路由器LLM初始化失败: {e}，将使用规则匹配")
        
        self._llm_initialized = True

