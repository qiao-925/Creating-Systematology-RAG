"""
降级策略模块：实现三级降级策略

主要功能：
- 一级降级：回退到 vector_search（使用 ModularQueryEngine）
- 二级降级：纯 LLM 生成（无检索）
- 三级降级：返回错误信息
"""

from typing import Tuple, List, Optional, Dict, Any

from backend.infrastructure.indexer import IndexManager
from backend.infrastructure.logger import get_logger
from backend.business.rag_engine.core.engine import ModularQueryEngine
from backend.infrastructure.observers.manager import ObserverManager

logger = get_logger('rag_engine.agentic.fallback')


class FallbackHandler:
    """降级策略处理器"""
    
    def __init__(
        self,
        index_manager: IndexManager,
        llm,
        similarity_top_k: int,
        enable_rerank: bool,
        rerank_top_n: int,
        reranker_type: Optional[str],
        similarity_cutoff: float,
        observer_manager: ObserverManager,
        formatter,
    ):
        """初始化降级处理器
        
        Args:
            index_manager: 索引管理器
            llm: LLM 实例
            similarity_top_k: Top-K值
            enable_rerank: 是否启用重排序
            rerank_top_n: 重排序Top-N
            reranker_type: 重排序器类型
            similarity_cutoff: 相似度阈值
            observer_manager: 观察器管理器
            formatter: 响应格式化器
        """
        self.index_manager = index_manager
        self.llm = llm
        self.similarity_top_k = similarity_top_k
        self.enable_rerank = enable_rerank
        self.rerank_top_n = rerank_top_n
        self.reranker_type = reranker_type
        self.similarity_cutoff = similarity_cutoff
        self.observer_manager = observer_manager
        self.formatter = formatter
        
        # 创建降级引擎（延迟初始化）
        self._fallback_engine: Optional[ModularQueryEngine] = None
    
    def _get_fallback_engine(self) -> ModularQueryEngine:
        """获取降级引擎（用于一级降级）"""
        if self._fallback_engine is None:
            self._fallback_engine = ModularQueryEngine(
                index_manager=self.index_manager,
                retrieval_strategy="vector",
                similarity_top_k=self.similarity_top_k,
                enable_rerank=self.enable_rerank,
                rerank_top_n=self.rerank_top_n,
                reranker_type=self.reranker_type,
                similarity_cutoff=self.similarity_cutoff,
                enable_markdown_formatting=True,
                observer_manager=self.observer_manager,
            )
            logger.info("降级引擎已创建（vector_search）")
        
        return self._fallback_engine
    
    def fallback_to_traditional_rag(
        self,
        question: str,
        collect_trace: bool,
        trace_info: Optional[Dict[str, Any]],
        trace_ids: List[str]
    ) -> Tuple[str, List[dict], Optional[str], Optional[Dict[str, Any]]]:
        """降级到传统 RAG（一级降级）"""
        logger.info("执行一级降级：使用 vector_search")
        
        try:
            fallback_engine = self._get_fallback_engine()
            answer, sources, reasoning_content, fallback_trace_info = fallback_engine.query(
                question,
                collect_trace=collect_trace
            )
            
            # 更新追踪信息
            if collect_trace and trace_info:
                trace_info["fallback_used"] = True
                trace_info["fallback_reason"] = "Agent 调用失败或超时"
                trace_info["fallback_engine"] = "vector_search"
                if fallback_trace_info:
                    trace_info["fallback_trace_info"] = fallback_trace_info
                    # 使用降级引擎的 retrieval_time
                    if "retrieval_time" in fallback_trace_info:
                        trace_info["retrieval_time"] = fallback_trace_info["retrieval_time"]
                # 确保 retrieval_time 存在
                if "retrieval_time" not in trace_info:
                    trace_info["retrieval_time"] = 0
            
            return answer, sources, reasoning_content, trace_info
        except Exception as e:
            logger.error("一级降级失败，执行二级降级", error=str(e))
            return self.fallback_to_pure_llm(question, collect_trace, trace_info, trace_ids)
    
    def fallback_to_pure_llm(
        self,
        question: str,
        collect_trace: bool,
        trace_info: Optional[Dict[str, Any]],
        trace_ids: List[str]
    ) -> Tuple[str, List[dict], Optional[str], Optional[Dict[str, Any]]]:
        """降级到纯 LLM 生成（二级降级）"""
        logger.warning("执行二级降级：纯 LLM 生成（无检索）")
        
        try:
            # 使用 LLM 直接生成答案
            from llama_index.core.llms import ChatMessage, MessageRole
            
            messages = [
                ChatMessage(
                    role=MessageRole.USER,
                    content=f"请回答以下问题：{question}"
                )
            ]
            
            response = self.llm.chat(messages)
            answer = str(response)
            answer = self.formatter.format(answer, None)
            
            # 更新追踪信息
            if collect_trace and trace_info:
                trace_info["fallback_used"] = True
                trace_info["fallback_reason"] = "一级降级失败"
                trace_info["fallback_engine"] = "pure_llm"
                if "retrieval_time" not in trace_info:
                    trace_info["retrieval_time"] = 0
            
            # 通知观察器：查询结束
            self.observer_manager.on_query_end(
                query=question,
                answer=answer,
                sources=[],
                trace_ids=trace_ids,
                retrieval_time=trace_info.get("retrieval_time", 0) if trace_info else 0,
            )
            
            return answer, [], None, trace_info
        except Exception as e:
            logger.error("二级降级失败，返回错误信息", error=str(e))
            return self.fallback_to_error(question, collect_trace, trace_info, trace_ids, str(e))
    
    def fallback_to_error(
        self,
        question: str,
        collect_trace: bool,
        trace_info: Optional[Dict[str, Any]],
        trace_ids: List[str],
        error_message: str
    ) -> Tuple[str, List[dict], Optional[str], Optional[Dict[str, Any]]]:
        """降级到错误信息（三级降级）"""
        logger.error("执行三级降级：返回错误信息")
        
        answer = f"抱歉，查询失败：{error_message}"
        
        # 更新追踪信息
        if collect_trace and trace_info:
            trace_info["fallback_used"] = True
            trace_info["fallback_reason"] = "所有降级策略都失败"
            trace_info["fallback_engine"] = "error"
            trace_info["error"] = error_message
            if "retrieval_time" not in trace_info:
                trace_info["retrieval_time"] = 0
        
        # 通知观察器：查询结束
        self.observer_manager.on_query_end(
            query=question,
            answer=answer,
            sources=[],
            trace_ids=trace_ids,
            retrieval_time=trace_info.get("retrieval_time", 0) if trace_info else 0,
        )
        
        return answer, [], None, trace_info

