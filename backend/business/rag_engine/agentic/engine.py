"""
AgenticQueryEngine 主入口：基于 Agent 的自主检索策略选择

主要功能：
- AgenticQueryEngine类：Agentic RAG 查询引擎
- query()：调用规划 Agent，提取结果，格式化返回
- 接口与 ModularQueryEngine.query() 完全一致
"""

import time
import asyncio
import inspect
from typing import Optional, Tuple, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

# 尝试导入 Context（新版本 ReActAgent 需要）
try:
    from llama_index.core.workflow import Context
except ImportError:
    Context = None

from backend.infrastructure.indexer import IndexManager
from backend.infrastructure.logger import get_logger
from backend.infrastructure.config import config
from backend.business.rag_engine.formatting import ResponseFormatter
from backend.business.rag_engine.agentic.agent.planning import create_planning_agent
from backend.business.rag_engine.agentic.fallback import FallbackHandler
from backend.business.rag_engine.agentic.extraction import (
    extract_sources_from_agent,
    extract_reasoning_from_agent,
)
from backend.business.rag_engine.utils.utils import handle_fallback
from backend.infrastructure.llms import create_deepseek_llm_for_query
from backend.infrastructure.observers.manager import ObserverManager
from backend.infrastructure.observers.factory import create_observer_from_config

logger = get_logger('rag_engine.agentic')


class AgenticQueryEngine:
    """Agentic RAG 查询引擎（基于 Agent 的自主检索策略选择）"""
    
    def __init__(
        self,
        index_manager: IndexManager,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        similarity_top_k: Optional[int] = None,
        enable_rerank: Optional[bool] = None,
        rerank_top_n: Optional[int] = None,
        reranker_type: Optional[str] = None,
        similarity_cutoff: Optional[float] = None,
        enable_markdown_formatting: bool = True,
        observer_manager: Optional[ObserverManager] = None,
        max_iterations: int = 5,
        timeout_seconds: int = 30,
        max_llm_calls: int = 35,
        **kwargs
    ):
        """初始化 AgenticQueryEngine
        
        Args:
            index_manager: 索引管理器
            api_key: API密钥（可选，默认使用配置）
            model: 模型名称（可选，默认使用配置）
            similarity_top_k: Top-K值（可选，默认使用配置）
            enable_rerank: 是否启用重排序（可选，默认使用配置）
            rerank_top_n: 重排序Top-N（可选，默认使用配置）
            reranker_type: 重排序器类型（可选，默认使用配置）
            similarity_cutoff: 相似度阈值（可选，默认使用配置）
            enable_markdown_formatting: 是否启用Markdown格式化
            observer_manager: 观察器管理器（可选）
            max_iterations: Agent最大迭代次数（默认5）
            timeout_seconds: 超时时间（秒，默认30）
            max_llm_calls: 最大LLM调用次数（默认35）
            **kwargs: 其他参数（忽略，保持接口兼容性）
        """
        self.index_manager = index_manager
        self.index = index_manager.get_index()
        
        # 配置参数
        self.similarity_top_k = similarity_top_k or config.SIMILARITY_TOP_K
        self.enable_rerank = enable_rerank if enable_rerank is not None else config.ENABLE_RERANK
        self.rerank_top_n = rerank_top_n or config.RERANK_TOP_N
        self.reranker_type = reranker_type or config.RERANKER_TYPE
        self.similarity_cutoff = similarity_cutoff or config.SIMILARITY_CUTOFF
        self.max_iterations = max_iterations
        self.timeout_seconds = timeout_seconds
        self.max_llm_calls = max_llm_calls
        
        # 初始化组件
        self.formatter = ResponseFormatter(enable_formatting=enable_markdown_formatting)
        self.observer_manager = self._setup_observer_manager(observer_manager)
        self.llm = self._setup_llm(api_key, model)
        
        # 创建规划 Agent（延迟初始化，在首次查询时创建）
        self._planning_agent: Optional[Any] = None
        
        # 创建降级处理器
        self.fallback_handler = FallbackHandler(
            index_manager=self.index_manager,
            llm=self.llm,
            similarity_top_k=self.similarity_top_k,
            enable_rerank=self.enable_rerank,
            rerank_top_n=self.rerank_top_n,
            reranker_type=self.reranker_type,
            similarity_cutoff=self.similarity_cutoff,
            observer_manager=self.observer_manager,
            formatter=self.formatter,
        )
        
        logger.info(
            "AgenticQueryEngine 初始化完成",
            top_k=self.similarity_top_k,
            max_iterations=self.max_iterations,
            timeout_seconds=self.timeout_seconds,
            max_llm_calls=self.max_llm_calls,
            note="注意：max_llm_calls 当前未实现跟踪逻辑，通过 max_iterations 间接控制"
        )
    
    def _setup_observer_manager(self, observer_manager: Optional[ObserverManager]) -> ObserverManager:
        """设置观察器管理器"""
        if observer_manager is not None:
            manager = observer_manager
            logger.info("使用提供的观察器管理器", observer_count=len(manager.observers))
        else:
            manager = create_observer_from_config()
            logger.info("从配置创建观察器管理器", observer_count=len(manager.observers))
        
        return manager
    
    def _setup_llm(self, api_key: Optional[str], model: Optional[str]):
        """设置LLM"""
        api_key = api_key or config.DEEPSEEK_API_KEY
        model = model or config.LLM_MODEL
        if not api_key:
            raise ValueError("未设置DEEPSEEK_API_KEY")
        
        return create_deepseek_llm_for_query(
            api_key=api_key,
            model=model,
            max_tokens=4096,
        )
    
    def _get_planning_agent(self):
        """获取规划 Agent（延迟初始化）"""
        if self._planning_agent is None:
            self._planning_agent = create_planning_agent(
                index_manager=self.index_manager,
                llm=self.llm,
                similarity_top_k=self.similarity_top_k,
                similarity_cutoff=self.similarity_cutoff,
                enable_rerank=self.enable_rerank,
                rerank_top_n=self.rerank_top_n,
                reranker_type=self.reranker_type,
                max_iterations=self.max_iterations,
                verbose=True,
            )
            logger.info("规划 Agent 已创建")
        
        return self._planning_agent
    
    
    def query(
        self,
        question: str,
        collect_trace: bool = False
    ) -> Tuple[str, List[dict], Optional[str], Optional[Dict[str, Any]]]:
        """执行查询（与 ModularQueryEngine.query() 接口一致）
        
        Args:
            question: 用户问题
            collect_trace: 是否收集追踪信息
            
        Returns:
            (答案, 引用来源, 推理链内容, 追踪信息)
        """
        trace_info = None
        
        # 通知观察器：查询开始
        trace_ids = self.observer_manager.on_query_start(question)
        
        if collect_trace:
            trace_info = {
                "query": question,
                "start_time": time.time(),
                "observer_trace_ids": trace_ids,
                "engine_type": "agentic",
            }
        
        try:
            query_start_time = time.time()
            logger.info(
                "Agentic RAG 查询开始",
                query=question[:50] if len(question) > 50 else question,
                max_iterations=self.max_iterations,
                timeout=self.timeout_seconds
            )
            
            # 调用规划 Agent（带超时控制）
            agent_start_time = time.time()
            agent = self._get_planning_agent()
            agent_init_time = round(time.time() - agent_start_time, 3)
            logger.debug("规划 Agent 初始化完成", init_time=agent_init_time)
            
            response = self._call_agent_with_timeout(agent, question)
            agent_call_time = round(time.time() - agent_start_time, 3)
            logger.debug("Agent 调用完成", call_time=agent_call_time)
            
            # 提取结果
            extraction_start_time = time.time()
            answer = str(response)
            # 传递 Agent 实例以便访问工具调用历史
            sources = extract_sources_from_agent(response, agent=agent)
            reasoning_content = extract_reasoning_from_agent(response, agent=agent)
            extraction_time = round(time.time() - extraction_start_time, 3)
            logger.debug(
                "结果提取完成",
                extraction_time=extraction_time,
                sources_count=len(sources),
                has_reasoning=reasoning_content is not None
            )
            
            # 格式化答案
            format_start_time = time.time()
            answer = self.formatter.format(answer, sources)
            format_time = round(time.time() - format_start_time, 3)
            logger.debug("答案格式化完成", format_time=format_time)
            
            # 追踪信息
            total_time = round(time.time() - query_start_time, 3)
            if collect_trace and trace_info:
                trace_info["retrieval_time"] = round(time.time() - trace_info["start_time"], 2)
                trace_info["chunks_retrieved"] = len(sources)
                trace_info["total_time"] = round(time.time() - trace_info["start_time"], 2)
                trace_info["agent_init_time"] = agent_init_time
                trace_info["agent_call_time"] = agent_call_time
                trace_info["extraction_time"] = extraction_time
                trace_info["format_time"] = format_time
                if reasoning_content:
                    trace_info["has_reasoning"] = True
                    trace_info["reasoning_length"] = len(reasoning_content)
            
            logger.info(
                "Agentic RAG 查询完成",
                sources_count=len(sources),
                answer_len=len(answer),
                total_time=total_time,
                agent_call_time=agent_call_time,
                has_reasoning=reasoning_content is not None
            )
            
            # 处理兜底逻辑（无来源、低相似度或空答案时触发）
            # 注意：使用原始查询进行兜底处理，确保用户看到的是原始问题的答案
            answer, fallback_reason = handle_fallback(
                answer, sources, question, self.llm, self.similarity_cutoff
            )
            
            # 如果收集追踪信息，记录兜底状态
            if collect_trace and trace_info:
                trace_info['fallback_used'] = bool(fallback_reason)
                trace_info['fallback_reason'] = fallback_reason
            
            # 通知观察器：查询结束
            retrieval_time = 0
            if trace_info and isinstance(trace_info, dict):
                retrieval_time = trace_info.get("retrieval_time", 0)
            
            self.observer_manager.on_query_end(
                query=question,
                answer=answer,
                sources=sources,
                trace_ids=trace_ids,
                retrieval_time=retrieval_time,
            )
            
            return answer, sources, reasoning_content, trace_info
            
        except FutureTimeoutError:
            # 安全计算 elapsed_time
            if trace_info and isinstance(trace_info, dict):
                start_time = trace_info.get("start_time", time.time())
                elapsed_time = round(time.time() - start_time, 2)
            else:
                elapsed_time = 0
            
            logger.warning(
                "Agent 调用超时，降级到传统 RAG",
                timeout=self.timeout_seconds,
                elapsed_time=elapsed_time,
                query=question[:50] if len(question) > 50 else question
            )
            return self.fallback_handler.fallback_to_traditional_rag(
                question, collect_trace, trace_info, trace_ids
            )
        except Exception as e:
            # 安全计算 elapsed_time
            if trace_info and isinstance(trace_info, dict):
                start_time = trace_info.get("start_time", time.time())
                elapsed_time = round(time.time() - start_time, 2)
            else:
                elapsed_time = 0
            
            logger.error(
                "Agent 调用失败，降级到传统 RAG",
                error=str(e),
                error_type=type(e).__name__,
                elapsed_time=elapsed_time,
                query=question[:50] if len(question) > 50 else question,
                exc_info=True
            )
            return self.fallback_handler.fallback_to_traditional_rag(
                question, collect_trace, trace_info, trace_ids
            )
    
    def _call_agent_with_timeout(self, agent, question: str):
        """调用 Agent（带超时控制）"""
        # 检测 Agent 的可用方法
        method = None
        method_name = None
        is_async = False
        
        # 优先尝试 query() 方法（LlamaIndex ReActAgent 的标准方法）
        if hasattr(agent, 'query') and callable(getattr(agent, 'query')):
            method = agent.query
            method_name = 'query'
            # 检查是否是异步方法
            is_async = inspect.iscoroutinefunction(method)
        # 备选：尝试 chat() 方法
        elif hasattr(agent, 'chat') and callable(getattr(agent, 'chat')):
            method = agent.chat
            method_name = 'chat'
            is_async = inspect.iscoroutinefunction(method)
        # 备选：尝试 run() 方法（可能是异步的）
        elif hasattr(agent, 'run') and callable(getattr(agent, 'run')):
            method = agent.run
            method_name = 'run'
            # run() 方法即使不是协程函数，也可能内部使用异步代码（如 asyncio.create_task）
            # 因此总是将其作为异步方法处理
            is_async = True
            logger.debug("使用 run() 方法，将使用 asyncio.run() 执行（即使不是协程函数）")
        else:
            # 如果所有方法都不存在，记录可用方法并抛出错误
            available_methods = [
                m for m in dir(agent) 
                if not m.startswith('_') and callable(getattr(agent, m))
            ]
            logger.error(
                "ReActAgent 没有找到可用的调用方法",
                available_methods=available_methods[:10],  # 只显示前10个
                total_methods=len(available_methods)
            )
            raise AttributeError(
                f"ReActAgent 没有 query/chat/run 方法。"
                f"可用方法（前10个）: {available_methods[:10]}"
            )
        
        logger.debug(
            "使用 Agent 方法调用",
            method=method_name,
            is_async=is_async,
            question_preview=question[:50] if len(question) > 50 else question
        )
        
        # 使用线程池执行器实现超时
        with ThreadPoolExecutor(max_workers=1) as executor:
            if is_async:
                # 异步方法：使用 asyncio.run() 在新的事件循环中运行
                def run_async():
                    if inspect.iscoroutinefunction(method):
                        # 如果是协程函数，直接使用 asyncio.run()
                        return asyncio.run(method(question))
                    else:
                        # 如果不是协程函数但内部使用异步代码（如 asyncio.create_task）
                        # run() 方法内部会调用 asyncio.create_task()，需要运行中的事件循环
                        # 新版本的 run() 方法需要 Context 参数
                        async def wrapper():
                            # 检查是否需要 Context 参数
                            sig = inspect.signature(method)
                            needs_context = 'context' in sig.parameters
                            
                            if needs_context and Context is not None:
                                # 创建 Context 并传递
                                ctx = Context(agent)
                                return await method(question, context=ctx)
                            else:
                                # 旧版本或不需要 Context
                                return method(question)
                        return asyncio.run(wrapper())
                
                future = executor.submit(run_async)
            else:
                # 同步方法：直接调用
                future = executor.submit(method, question)
            
            try:
                response = future.result(timeout=self.timeout_seconds)
                return response
            except FutureTimeoutError:
                logger.warning("Agent 调用超时", timeout=self.timeout_seconds, method=method_name, is_async=is_async)
                raise
    
    async def stream_query(self, question: str):
        """异步流式查询（用于Web应用）
        
        注意：Agentic RAG 的流式查询实现较复杂，当前版本暂不支持流式输出。
        如需流式输出，请使用传统 ModularQueryEngine。
        
        Args:
            question: 用户问题
            
        Yields:
            dict: 流式响应字典（当前版本降级为非流式）
        """
        # 当前版本：降级为非流式查询
        logger.warning("AgenticQueryEngine 暂不支持流式查询，降级为非流式")
        answer, sources, reasoning_content, _ = self.query(question, collect_trace=False)
        
        # 模拟流式输出
        for char in answer:
            yield {'type': 'token', 'data': char}
        
        if sources:
            yield {'type': 'sources', 'data': sources}
        
        if reasoning_content:
            yield {'type': 'reasoning', 'data': reasoning_content}
        
        yield {
            'type': 'done',
            'data': {
                'answer': answer,
                'sources': sources,
                'reasoning_content': reasoning_content,
            }
        }

