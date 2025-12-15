"""
RAG引擎核心模块：ModularQueryEngine类实现

主要功能：
- ModularQueryEngine类：模块化查询引擎，支持vector、bm25、hybrid、grep、multi等策略
- query()：执行查询，返回格式化的回答和引用来源
- stream_query()：流式查询，实时返回答案token（用于Web应用）

执行流程：
1. 初始化查询引擎（创建检索器、后处理器等）
2. 执行查询（非流式或流式）
3. 处理检索结果
4. 应用后处理（重排序等）
5. 生成回答并格式化
6. 返回查询结果

特性：
- 模块化设计
- 支持多种检索策略
- 可插拔的后处理器
- 完整的错误处理和兜底机制
- 真正的流式输出支持（使用DeepSeek原生流式API）
"""

from typing import List, Optional, Tuple, Dict, Any
from llama_index.core import Settings
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core import get_response_synthesizer
from src.infrastructure.config import config
from src.infrastructure.indexer import IndexManager
from src.infrastructure.logger import get_logger
from src.business.rag_engine.formatting import ResponseFormatter
from src.infrastructure.observers.manager import ObserverManager
from src.infrastructure.observers.factory import create_observer_from_config
from src.business.rag_engine.retrieval.factory import create_retriever
from src.business.rag_engine.processing.execution import create_postprocessors, execute_query
from src.business.rag_engine.processing.query_processor import QueryProcessor
from src.business.rag_engine.utils.utils import handle_fallback
from src.infrastructure.llms import create_deepseek_llm_for_query
from src.business.rag_engine.models import QueryContext, QueryResult, SourceModel

logger = get_logger('rag_engine')


class ModularQueryEngine:
    """模块化查询引擎（工厂模式）"""
    
    SUPPORTED_STRATEGIES = ["vector", "bm25", "hybrid", "grep", "multi"]
    
    def __init__(
        self,
        index_manager: IndexManager,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        retrieval_strategy: Optional[str] = None,
        similarity_top_k: Optional[int] = None,
        enable_rerank: Optional[bool] = None,
        rerank_top_n: Optional[int] = None,
        reranker_type: Optional[str] = None,
        similarity_cutoff: Optional[float] = None,
        enable_markdown_formatting: bool = True,
        observer_manager: Optional[ObserverManager] = None,
        enable_auto_routing: Optional[bool] = None,
        **kwargs
    ):
        """初始化模块化查询引擎"""
        self.index_manager = index_manager
        self.index = index_manager.get_index()
        
        # 配置参数
        self._load_config(
            retrieval_strategy, similarity_top_k, enable_rerank,
            rerank_top_n, reranker_type, similarity_cutoff, enable_auto_routing
        )
        
        # 初始化组件
        self.formatter = ResponseFormatter(enable_formatting=enable_markdown_formatting)
        self.observer_manager = self._setup_observer_manager(observer_manager)
        self.llm = self._setup_llm(api_key, model)
        self.query_processor = QueryProcessor(llm=self.llm)
        logger.info("查询处理器已初始化", note="标准化流程：意图理解+改写")
        
        # 初始化路由和检索组件
        self.query_router = self._setup_query_router(index_manager) if self.enable_auto_routing else None
        self.retriever, self.query_engine = self._setup_retrieval_components()
        self.postprocessors = create_postprocessors(
            self.index_manager,
            self.similarity_cutoff,
            self.enable_rerank,
            self.rerank_top_n,
            reranker_type=self.reranker_type,
        )
        
        self._log_initialization_summary()
    
    def _load_config(
        self,
        retrieval_strategy: Optional[str],
        similarity_top_k: Optional[int],
        enable_rerank: Optional[bool],
        rerank_top_n: Optional[int],
        reranker_type: Optional[str],
        similarity_cutoff: Optional[float],
        enable_auto_routing: Optional[bool]
    ) -> None:
        """加载并验证配置参数"""
        self.retrieval_strategy = retrieval_strategy or config.RETRIEVAL_STRATEGY
        self.similarity_top_k = similarity_top_k or config.SIMILARITY_TOP_K
        self.enable_rerank = enable_rerank if enable_rerank is not None else config.ENABLE_RERANK
        self.rerank_top_n = rerank_top_n or config.RERANK_TOP_N
        self.reranker_type = reranker_type or config.RERANKER_TYPE
        self.similarity_cutoff = similarity_cutoff or config.SIMILARITY_CUTOFF
        self.enable_auto_routing = enable_auto_routing if enable_auto_routing is not None else config.ENABLE_AUTO_ROUTING
        
        if self.retrieval_strategy not in self.SUPPORTED_STRATEGIES:
            raise ValueError(
                f"不支持的检索策略: {self.retrieval_strategy}. "
                f"支持的策略: {self.SUPPORTED_STRATEGIES}"
            )
    
    def _setup_observer_manager(self, observer_manager: Optional[ObserverManager]) -> ObserverManager:
        """设置观察器管理器"""
        if observer_manager is not None:
            manager = observer_manager
            logger.info("使用提供的观察器管理器", observer_count=len(manager.observers))
        else:
            manager = create_observer_from_config()
            logger.info("从配置创建观察器管理器", observer_count=len(manager.observers))
        
        callback_handlers = manager.get_callback_handlers()
        if callback_handlers:
            from llama_index.core.callbacks import CallbackManager
            Settings.callback_manager = CallbackManager(callback_handlers)
            logger.info("设置回调处理器到LlamaIndex", handler_count=len(callback_handlers))
        
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
    
    def _setup_query_router(self, index_manager: IndexManager):
        """设置查询路由器"""
        from src.business.rag_engine.routing.query_router import QueryRouter
        router = QueryRouter(
            index_manager=index_manager,
            llm=self.llm,
            enable_auto_routing=True,
        )
        logger.info("查询路由器已启用", mode="自动路由模式")
        return router
    
    def _setup_retrieval_components(self) -> Tuple[Optional[Any], Optional[RetrieverQueryEngine]]:
        """设置检索组件"""
        if not self.enable_auto_routing:
            retriever = create_retriever(
                self.index,
                self.retrieval_strategy,
                self.similarity_top_k
            )
            query_engine = self._create_query_engine_from_retriever(retriever)
            return retriever, query_engine
        else:
            return None, None
    
    def _log_initialization_summary(self) -> None:
        """记录初始化摘要"""
        logger.info(
            "模块化查询引擎初始化完成",
            strategy=self.retrieval_strategy,
            top_k=self.similarity_top_k,
            rerank_enabled=self.enable_rerank,
            similarity_cutoff=self.similarity_cutoff,
            auto_routing=self.enable_auto_routing
        )
    
    def _create_query_engine_from_retriever(self, retriever, streaming: bool = False) -> RetrieverQueryEngine:
        """从检索器创建查询引擎
        
        Args:
            retriever: 检索器实例
            streaming: 是否启用流式输出
            
        Returns:
            RetrieverQueryEngine实例
        """
        if streaming:
            # 创建流式响应合成器
            response_synthesizer = get_response_synthesizer(
                streaming=True,
                llm=self.llm
            )
            return RetrieverQueryEngine(
                retriever=retriever,
                response_synthesizer=response_synthesizer,
                node_postprocessors=self.postprocessors,
            )
        else:
            return RetrieverQueryEngine.from_args(
                retriever=retriever,
                llm=self.llm,
                node_postprocessors=self.postprocessors,
            )
    
    def _get_or_create_query_engine(
        self,
        final_query: str,
        understanding: Optional[Dict[str, Any]] = None,
        streaming: bool = False
    ) -> Tuple[RetrieverQueryEngine, str]:
        """获取或创建查询引擎（支持自动路由）
        
        Args:
            final_query: 处理后的查询
            understanding: 查询理解结果（可选）
            streaming: 是否启用流式输出
            
        Returns:
            (查询引擎实例, 路由决策/策略名称)
        """
        if self.enable_auto_routing and self.query_router:
            # 自动路由模式：根据查询意图动态选择检索器
            if understanding:
                retriever, routing_decision = self.query_router.route_with_understanding(
                    final_query,
                    understanding=understanding,
                    top_k=self.similarity_top_k
                )
            else:
                retriever, routing_decision = self.query_router.route(
                    final_query,
                    top_k=self.similarity_top_k
                )
            
            query_engine = self._create_query_engine_from_retriever(retriever, streaming=streaming)
            strategy_info = f"策略={routing_decision}, 原因=自动路由模式，根据查询意图动态选择"
            return query_engine, strategy_info
        else:
            # 固定模式：使用初始化时创建的查询引擎
            # 如果是流式模式，需要重新创建流式查询引擎
            if streaming:
                # 获取当前查询引擎的检索器
                current_retriever = self.retriever
                if current_retriever:
                    query_engine = self._create_query_engine_from_retriever(current_retriever, streaming=True)
                    strategy_info = f"策略={self.retrieval_strategy}, 原因=固定检索模式（流式）"
                    return query_engine, strategy_info
            strategy_info = f"策略={self.retrieval_strategy}, 原因=固定检索模式（初始化时配置）"
            return self.query_engine, strategy_info
    
    def _execute_with_query_engine(
        self,
        query_engine: RetrieverQueryEngine,
        final_query: str,
        collect_trace: bool
    ) -> Tuple[str, List[dict], Optional[str], Optional[Dict[str, Any]]]:
        """使用查询引擎执行查询
        
        Args:
            query_engine: 查询引擎实例
            final_query: 处理后的查询
            collect_trace: 是否收集追踪信息
            
        Returns:
            (答案, 引用来源, 推理链内容, 追踪信息)
        """
        return execute_query(
            query_engine,
            self.formatter,
            self.observer_manager,
            final_query,
            collect_trace
        )
    
    def query(
        self, 
        question: str, 
        collect_trace: bool = False
    ) -> Tuple[str, List[dict], Optional[str], Optional[Dict[str, Any]]]:
        """执行查询（兼容现有API）
        
        Returns:
            (答案, 引用来源, 推理链内容, 追踪信息)
        """
        
        # Step 1: 查询处理（标准化流程：意图理解+改写）
        processed = self.query_processor.process(question)
        final_query = processed["final_query"]
        understanding = processed.get("understanding")
        
        logger.info(
            "查询处理完成",
            original_query=question[:50] if len(question) > 50 else question,
            processed_query=final_query[:50] if len(final_query) > 50 else final_query,
            processing_method=processed['processing_method']
        )
        
        # Step 2: 获取或创建查询引擎（支持自动路由）
        query_engine, strategy_info = self._get_or_create_query_engine(
            final_query,
            understanding
        )
        
        logger.info("使用检索策略", strategy_info=strategy_info)
        
        # Step 3: 执行查询
        answer, sources, reasoning_content, trace_info = self._execute_with_query_engine(
            query_engine,
            final_query,
            collect_trace
        )
        
        # 记录追踪信息
        if collect_trace and trace_info:
            trace_info["original_query"] = question
            trace_info["processed_query"] = final_query
            trace_info["query_processing"] = processed
        
        # 处理兜底逻辑（无来源、低相似度或空答案时触发）
        # 注意：使用原始查询进行兜底处理，确保用户看到的是原始问题的答案
        answer, fallback_reason = handle_fallback(
            answer, sources, question, self.llm, self.similarity_cutoff
        )
        
        # 如果收集追踪信息，记录兜底状态
        if collect_trace and trace_info:
            trace_info['fallback_used'] = bool(fallback_reason)
            trace_info['fallback_reason'] = fallback_reason
        
        return answer, sources, reasoning_content, trace_info
    
    def query_with_context(
        self,
        context: QueryContext
    ) -> QueryResult:
        """执行查询（使用 QueryContext 和 QueryResult 模型）
        
        Args:
            context: 查询上下文模型
            
        Returns:
            QueryResult 模型
        """
        logger.info(
            "执行查询（使用上下文模型）",
            query=context.query[:50] if len(context.query) > 50 else context.query,
            user_id=context.user_id,
            session_id=context.session_id,
            strategy=context.strategy,
            top_k=context.top_k
        )
        
        # 使用处理后的查询或原始查询
        query_text = context.processed_query or context.query
        
        # 执行查询
        answer, sources, reasoning_content, trace_info = self.query(
            query_text,
            collect_trace=bool(context.metadata.get('collect_trace', False))
        )
        
        # 转换为 SourceModel 列表
        source_models = []
        for source in sources:
            if isinstance(source, dict):
                source_models.append(SourceModel(**source))
            else:
                source_models.append(SourceModel(
                    text=source.get('text', ''),
                    score=source.get('score', 0.0),
                    metadata=source.get('metadata', {}),
                    file_name=source.get('file_name'),
                    page_number=source.get('page_number'),
                    node_id=source.get('node_id')
                ))
        
        # 创建 QueryResult
        result = QueryResult(
            answer=answer,
            sources=source_models,
            reasoning_content=reasoning_content,
            trace_info=trace_info,
            metadata={
                **context.metadata,
                'query': context.query,
                'processed_query': context.processed_query,
                'strategy': context.strategy,
                'top_k': context.top_k
            }
        )
        
        logger.info(
            "查询完成",
            user_id=context.user_id,
            sources_count=len(result.sources),
            answer_len=len(answer)
        )
        
        return result
    
    async def stream_query(self, question: str):
        """异步流式查询（用于Web应用）- 优化版本：直接使用 DeepSeek 流式输出
        
        绕过 LlamaIndex 的 StreamingResponse 缓冲，直接使用 DeepSeek 的 stream_chat，
        实现真正的实时流式输出。
        
        Args:
            question: 用户问题
            
        Yields:
            dict: 流式响应字典，包含以下类型：
                - 'type': 'token', 'data': token文本
                - 'type': 'sources', 'data': 引用来源列表
                - 'type': 'reasoning', 'data': 推理链内容
                - 'type': 'done', 'data': 完整答案和元数据
        """
        # Step 1: 查询处理（标准化流程：意图理解+改写）
        processed = self.query_processor.process(question)
        final_query = processed["final_query"]
        understanding = processed.get("understanding")
        
        logger.info(
            "流式查询处理完成（直接流式模式）",
            original_query=question[:50] if len(question) > 50 else question,
            processed_query=final_query[:50] if len(final_query) > 50 else final_query,
            processing_method=processed['processing_method']
        )
        
        # Step 2: 获取检索器和检索节点
        retriever = None
        strategy_info = ""
        
        if self.enable_auto_routing and self.query_router:
            # 自动路由模式
            if understanding:
                retriever, routing_decision = self.query_router.route_with_understanding(
                    final_query,
                    understanding=understanding,
                    top_k=self.similarity_top_k
                )
            else:
                retriever, routing_decision = self.query_router.route(
                    final_query,
                    top_k=self.similarity_top_k
                )
            strategy_info = f"策略={routing_decision}, 原因=自动路由模式"
        else:
            # 固定模式：使用初始化时创建的检索器
            retriever = self.retriever
            strategy_info = f"策略={self.retrieval_strategy}, 原因=固定检索模式"
        
        logger.info("使用检索策略（直接流式）", strategy_info=strategy_info)
        
        # Step 3: 检索节点
        nodes_with_scores = []
        sources = []
        full_answer = ""
        reasoning_content = ""
        
        try:
            if retriever:
                # 执行检索
                nodes_with_scores = retriever.retrieve(final_query)
                
                # 应用后处理
                if self.postprocessors:
                    for postprocessor in self.postprocessors:
                        nodes_with_scores = postprocessor.postprocess_nodes(
                            nodes_with_scores,
                            query_str=final_query
                        )
                
                # 转换为引用来源格式
                for i, node_with_score in enumerate(nodes_with_scores, 1):
                    node = node_with_score.node if hasattr(node_with_score, 'node') else node_with_score
                    score = node_with_score.score if hasattr(node_with_score, 'score') else None
                    
                    source = {
                        'index': i,
                        'text': node.text if hasattr(node, 'text') else str(node),
                        'score': score,
                        'metadata': node.metadata if hasattr(node, 'metadata') else {},
                    }
                    sources.append(source)
                
                logger.info(f"检索到 {len(nodes_with_scores)} 个文档片段")
            
            # Step 4: 构建 prompt
            from src.business.rag_engine.formatting.templates import CHAT_MARKDOWN_TEMPLATE
            
            # 构建上下文字符串
            context_str = ""
            if nodes_with_scores:
                context_parts = []
                for i, node_with_score in enumerate(nodes_with_scores, 1):
                    node = node_with_score.node if hasattr(node_with_score, 'node') else node_with_score
                    text = node.text if hasattr(node, 'text') else str(node)
                    context_parts.append(f"[{i}] {text}")
                context_str = "\n\n".join(context_parts)
            else:
                context_str = "（知识库中未找到相关信息）"
            
            # 构建完整 prompt
            # CHAT_MARKDOWN_TEMPLATE 只包含 context_str，需要手动添加查询
            prompt = CHAT_MARKDOWN_TEMPLATE.format(context_str=context_str)
            prompt += f"\n\n用户问题：{final_query}\n\n请用中文回答问题。"
            
            # Step 5: 直接使用 DeepSeek 流式输出
            import time
            from src.infrastructure.llms.reasoning import extract_reasoning_from_stream_chunk
            from llama_index.core.llms import ChatMessage, MessageRole
            
            # 创建 ChatMessage 对象（LlamaIndex 要求）
            chat_message = ChatMessage(
                role=MessageRole.USER,
                content=prompt
            )
            messages = [chat_message]
            
            last_token_time = time.time()
            token_count = 0
            last_chunk = None
            
            logger.debug("🚀 开始直接流式调用 DeepSeek API")
            
            # 直接调用 DeepSeek 的 stream_chat（绕过 LlamaIndex 缓冲）
            for chunk in self.llm.stream_chat(messages):
                # 提取推理链内容（流式）
                chunk_reasoning = extract_reasoning_from_stream_chunk(chunk)
                if chunk_reasoning:
                    reasoning_content += chunk_reasoning
                
                # 提取 token 内容（增量）
                # DeepSeek 流式返回应该是增量的，检查实际返回格式
                chunk_text = ""
                
                # 调试：记录 chunk 的结构
                if token_count == 0:
                    logger.debug(f"🔍 Chunk 结构检查: hasattr(chunk, 'delta')={hasattr(chunk, 'delta')}, hasattr(chunk, 'message')={hasattr(chunk, 'message')}")
                    if hasattr(chunk, 'delta'):
                        delta = chunk.delta
                        logger.debug(f"🔍 Delta 结构: {dir(delta)}")
                        if hasattr(delta, 'content'):
                            logger.debug(f"🔍 Delta.content 类型: {type(delta.content)}, 值: {repr(delta.content)}")
                    if hasattr(chunk, 'message'):
                        message = chunk.message
                        logger.debug(f"🔍 Message 结构: {dir(message)}")
                        if hasattr(message, 'content'):
                            logger.debug(f"🔍 Message.content 类型: {type(message.content)}, 值长度: {len(str(message.content)) if message.content else 0}")
                
                # 提取增量 token（DeepSeek 流式返回应该是增量的）
                # 关键：message.content 是累加的，delta.content 是增量的
                
                # 方法1：优先使用 delta.content（增量）
                if hasattr(chunk, 'delta'):
                    delta = chunk.delta
                    if hasattr(delta, 'content') and delta.content:
                        chunk_text = str(delta.content)
                        # 验证：delta.content 应该是增量（很短）
                        if len(chunk_text) > 50:
                            logger.warning(f"⚠️ Delta.content 长度异常: {len(chunk_text)} 字符，可能是累加的！内容: {chunk_text[:50]}...")
                
                # 方法2：如果没有 delta，从 message.content 计算增量
                elif hasattr(chunk, 'message'):
                    message = chunk.message
                    if hasattr(message, 'content') and message.content:
                        current_content = str(message.content)
                        # message.content 是累加的，计算增量：当前 - 之前
                        if full_answer and current_content.startswith(full_answer):
                            # 正常情况：当前内容包含之前的内容，提取增量
                            chunk_text = current_content[len(full_answer):]
                            if not chunk_text:
                                # 增量为空，可能是重复的 chunk，跳过
                                continue
                        elif not full_answer:
                            # 第一次：使用整个内容
                            chunk_text = current_content
                        else:
                            # 异常情况：当前内容不包含之前的内容
                            logger.warning(f"⚠️ Message.content 格式异常: 当前长度={len(current_content)}, 之前长度={len(full_answer)}")
                            # 尝试计算增量（取差值部分）
                            if len(current_content) > len(full_answer):
                                chunk_text = current_content[len(full_answer):]
                            else:
                                # 如果当前内容更短，可能是新的开始，使用整个内容
                                chunk_text = current_content
                                full_answer = ""  # 重置
                
                # 方法3：检查 raw 响应（OpenAI 格式）
                if not chunk_text and hasattr(chunk, 'raw'):
                    raw = chunk.raw
                    if isinstance(raw, dict):
                        choices = raw.get('choices', [])
                        if choices and len(choices) > 0:
                            choice = choices[0]
                            delta = choice.get('delta', {})
                            if isinstance(delta, dict):
                                chunk_text = delta.get('content', '')
                                if chunk_text:
                                    chunk_text = str(chunk_text)
                
                if chunk_text:
                    token_count += 1
                    current_time = time.time()
                    time_since_last = current_time - last_token_time
                    last_token_time = current_time
                    
                    # 记录每个 token 的到达时间（仅在前几个和间隔较长时记录）
                    if token_count <= 5 or time_since_last > 0.1:
                        logger.debug(f"🔤 Token #{token_count} '{chunk_text[:20]}...' 到达，间隔: {time_since_last*1000:.1f}ms")
                    
                    full_answer += chunk_text
                    # 立即 yield token（无缓冲）- 每个 token 单独返回，不累计
                    # 注意：这里 yield 的是单个 token，不是累计的 full_answer
                    yield {'type': 'token', 'data': chunk_text}
                
                last_chunk = chunk
            
            logger.debug(f"✅ 流式生成完成，共 {token_count} 个 token")
            
            # Step 6: 格式化答案
            full_answer = self.formatter.format(full_answer, None)
            
            # Step 7: 提取最终推理链（从最后一个 chunk）
            if last_chunk:
                from src.infrastructure.llms import extract_reasoning_content
                final_reasoning = extract_reasoning_content(last_chunk)
                if final_reasoning:
                    reasoning_content = final_reasoning
            
            # 返回引用来源
            if sources:
                yield {'type': 'sources', 'data': sources}
            
            # 返回推理链（答案完成后，非流式）
            if reasoning_content:
                yield {'type': 'reasoning', 'data': reasoning_content}
            
            # 返回完成事件
            yield {
                'type': 'done',
                'data': {
                    'answer': full_answer,
                    'sources': sources,
                    'reasoning_content': reasoning_content if reasoning_content else None,
                }
            }
            
        except Exception as e:
            logger.error(f"流式查询失败: {e}", exc_info=True)
            # 发送错误事件
            yield {
                'type': 'error',
                'data': {'message': str(e)}
            }
            raise


