"""
查询路由器 - 自动路由模式

基于LlamaIndex的auto_routed模式，智能选择检索策略
轻量级Agent路由层，根据查询意图自动选择检索模式
"""

from typing import Optional, List
from llama_index.core.schema import QueryBundle, NodeWithScore

from src.indexer import IndexManager
from src.logger import setup_logger
from src.config import config

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
        if not self.enable_auto_routing:
            # 禁用自动路由，返回默认chunk检索器
            return self._get_chunk_retriever(top_k), "chunk"
        
        # 分析查询意图
        routing_decision = self._analyze_query(query)
        
        logger.info(f"查询路由决策: query={query[:50]}..., decision={routing_decision}")
        
        # 根据决策返回对应检索器
        if routing_decision == "files_via_metadata":
            return self._get_files_via_metadata_retriever(top_k), "files_via_metadata"
        elif routing_decision == "files_via_content":
            return self._get_files_via_content_retriever(top_k), "files_via_content"
        else:
            return self._get_chunk_retriever(top_k), "chunk"
    
    def _analyze_query(self, query: str) -> str:
        """分析查询，返回检索模式决策
        
        Returns:
            "chunk" | "files_via_metadata" | "files_via_content"
        """
        # 简单的规则匹配（第一阶段实现）
        # 后续可以升级为LLM分类
        
        query_lower = query.lower()
        
        # 检查是否包含文件名关键词
        file_keywords = ["文件", "文档", "pdf", "md", "txt", ".py", ".md", ".pdf"]
        if any(keyword in query_lower for keyword in file_keywords):
            # 检查是否明确提到文件名
            if any(keyword in query for keyword in ["的", "说", "内容", "讲"]):
                return "files_via_metadata"
        
        # 检查是否是宽泛主题查询
        broad_indicators = [
            "什么是", "如何", "介绍", "概述", "总结", "说明",
            "概述", "背景", "历史", "发展", "前景", "未来"
        ]
        if any(indicator in query_lower for indicator in broad_indicators):
            return "files_via_content"
        
        # 默认使用chunk模式
        return "chunk"
    
    def _get_chunk_retriever(self, top_k: int):
        """获取chunk检索器"""
        if self._chunk_retriever is None:
            index = self.index_manager.get_index()
            self._chunk_retriever = index.as_retriever(similarity_top_k=top_k)
        return self._chunk_retriever
    
    def _get_files_via_metadata_retriever(self, top_k: int):
        """获取files_via_metadata检索器
        
        注意：LlamaIndex的文件级别检索需要特殊实现
        目前返回chunk检索器（占位实现）
        """
        logger.warning("files_via_metadata检索器尚未完全实现，使用chunk检索器")
        return self._get_chunk_retriever(top_k)
    
    def _get_files_via_content_retriever(self, top_k: int):
        """获取files_via_content检索器
        
        注意：LlamaIndex的文件级别检索需要特殊实现
        目前返回chunk检索器（占位实现）
        """
        logger.warning("files_via_content检索器尚未完全实现，使用chunk检索器")
        return self._get_chunk_retriever(top_k)
    
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

