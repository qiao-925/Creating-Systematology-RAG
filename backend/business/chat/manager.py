"""
对话管理 - 管理器核心模块：ChatManager类实现

主要功能：
- ChatManager类：对话管理器，管理对话会话和历史记录（仅内存）
- start_session()：开始新会话
- chat()：非流式对话（同步）
- stream_chat()：流式对话（异步，使用真正的流式API）

执行流程：
1. 初始化对话管理器（连接索引管理器）
2. 创建会话
3. 执行对话查询（使用ModularQueryEngine + 对话记忆）

特性：
- 会话管理（仅内存，不持久化）
- 推理链支持
- 复用ModularQueryEngine的丰富检索策略
- 真正的流式输出支持（实时token输出，无模拟延迟）
"""

from __future__ import annotations

import asyncio
from typing import Optional, List, Tuple, TYPE_CHECKING, Callable

# 延迟导入：这些模块导入耗时较长，改为按需加载
if TYPE_CHECKING:
    from llama_index.core.memory import ChatMemoryBuffer
    from llama_index.core.llms import ChatMessage, MessageRole
    from backend.infrastructure.indexer import IndexManager
    from backend.business.rag_engine.core.engine import ModularQueryEngine
    from backend.business.rag_engine.agentic import AgenticQueryEngine

from backend.infrastructure.config import config
from backend.infrastructure.logger import get_logger
from backend.business.rag_engine.formatting import ResponseFormatter
from backend.business.chat.session import ChatSession
from backend.infrastructure.llms import (
    create_llm,
    create_deepseek_llm_for_query,  # 向后兼容
    extract_reasoning_content,
)

logger = get_logger('chat_manager')


class ChatManager:
    """对话管理器"""
    
    def __init__(
        self,
        index_manager: Optional[IndexManager] = None,
        index_manager_provider: Optional[Callable[[], IndexManager]] = None,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model: Optional[str] = None,
        model_id: Optional[str] = None,  # 新增：模型 ID（优先使用）
        memory_token_limit: int = 3000,
        similarity_top_k: Optional[int] = None,
        enable_debug: bool = False,
        similarity_threshold: Optional[float] = None,
        enable_markdown_formatting: bool = True,
        retrieval_strategy: Optional[str] = None,
        enable_rerank: Optional[bool] = None,
        max_history_turns: int = 6,
        enable_smart_condense: bool = True,
        use_agentic_rag: bool = False,
        temperature: Optional[float] = None,  # 新增：LLM 温度参数
        max_tokens: Optional[int] = None,  # 新增：LLM 最大 token 数
        **kwargs
    ):
        """初始化对话管理器
        
        Args:
            index_manager: 索引管理器（可选，None时为纯LLM对话模式）
            api_key: DeepSeek API密钥
            api_base: API端点
            model: 模型名称
            memory_token_limit: 记忆token限制
            similarity_top_k: 检索相似文档数量
            enable_debug: 是否启用调试模式
            similarity_threshold: 相似度阈值
            enable_markdown_formatting: 是否启用Markdown格式化
            retrieval_strategy: 检索策略（vector/bm25/hybrid/grep/multi）
            enable_rerank: 是否启用重排序
            max_history_turns: 最大历史轮数（用于查询压缩）
            enable_smart_condense: 是否启用智能压缩（短历史不压缩）
            use_agentic_rag: 是否使用 Agentic RAG（默认False）
            temperature: LLM 温度参数（覆盖配置默认值，推理模型忽略）
            max_tokens: LLM 最大 token 数（覆盖配置默认值）
            **kwargs: 传递给查询引擎的其他参数
        """
        self.index_manager = index_manager
        self._index_manager_provider = index_manager_provider
        self.similarity_top_k = similarity_top_k or config.SIMILARITY_TOP_K
        self.enable_debug = enable_debug
        self.similarity_threshold = similarity_threshold or config.SIMILARITY_THRESHOLD
        self.max_history_turns = max_history_turns
        self.enable_smart_condense = enable_smart_condense
        self.min_high_quality_sources = 2  # 高质量来源的最小数量

        # 保存 API 密钥（无论使用哪种模式都需要）
        self.api_key = api_key or config.DEEPSEEK_API_KEY

        # 初始化响应格式化器
        self.formatter = ResponseFormatter(enable_formatting=enable_markdown_formatting)
        logger.info(f"响应格式化器已{'启用' if enable_markdown_formatting else '禁用'}")

        # 保存 LLM 配置参数（延迟创建）
        self._llm = None  # 延迟加载的 LLM 实例
        self._model_id = model_id
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

        # 确定模型名称（用于日志和查询引擎）
        if model_id:
            model_config = config.get_llm_model_config(model_id)
            if model_config:
                self.model = model_config.litellm_model
            else:
                self.model = model_id
        else:
            self.model = model or config.LLM_MODEL
            if not self.api_key:
                logger.warning("DEEPSEEK_API_KEY not set; LLM will be validated on first use.")

        logger.info(
            f"ChatManager 配置完成 (模型: {self.model}, "
            f"延迟加载: True)"
        )

        # 配置调试模式
        if self.enable_debug:
            from llama_index.core import Settings
            from llama_index.core.callbacks import CallbackManager, LlamaDebugHandler
            logger.info("对话管理器：启用调试模式")
            llama_debug = LlamaDebugHandler(print_trace_on_end=True)
            Settings.callback_manager = CallbackManager([llama_debug])

        # 延迟创建记忆缓冲区（避免导入 ChatMemoryBuffer 耗时 1.17s）
        self._memory = None
        self._memory_token_limit = memory_token_limit

        # 保存其他参数
        self.retrieval_strategy = retrieval_strategy
        self.enable_rerank = enable_rerank
        self.use_agentic_rag = use_agentic_rag
        self.engine_kwargs = kwargs

        # 延迟创建查询引擎
        self._query_engine = None

        # 当前会话
        self.current_session: Optional[ChatSession] = None

        logger.info("对话管理器初始化完成（延迟加载模式）")

    @property
    def memory(self):
        """获取记忆缓冲区（延迟加载）"""
        if self._memory is None:
            from llama_index.core.memory import ChatMemoryBuffer
            logger.debug("首次使用 memory，创建 ChatMemoryBuffer")
            self._memory = ChatMemoryBuffer.from_defaults(
                token_limit=self._memory_token_limit,
            )
        return self._memory

    def _get_index_manager(self):
        if self.index_manager is None and self._index_manager_provider:
            self.index_manager = self._index_manager_provider()
        return self.index_manager

    @property
    def llm(self):
        """获取 LLM 实例（延迟加载）"""
        if self._llm is None:
            logger.info("首次使用 LLM，开始创建实例...")

            # 配置 LLM（优先使用 model_id，向后兼容 model）
            if self._model_id:
                # 使用新的多模型接口
                logger.info(
                    f"创建 LLM (模型 ID: {self._model_id}, "
                    f"temperature: {self._temperature}, max_tokens: {self._max_tokens})"
                )
                self._llm = create_llm(
                    model_id=self._model_id,
                    temperature=self._temperature,
                    max_tokens=self._max_tokens,
                )
            else:
                # 向后兼容：使用旧的接口
                logger.info(f"创建 LLM (向后兼容模式): {self.model}")
                self._llm = create_deepseek_llm_for_query(
                    api_key=self.api_key,
                    model=self.model,
                )

            logger.info("✅ LLM 实例创建完成")

        return self._llm

    @property
    def query_engine(self):
        """获取查询引擎（延迟加载）"""
        index_manager = self._get_index_manager()
        if self._query_engine is None and index_manager:
            if self.use_agentic_rag:
                from backend.business.rag_engine.agentic import AgenticQueryEngine
                logger.info("创建 AgenticQueryEngine（Agent 自主选择检索策略）")
                self._query_engine = AgenticQueryEngine(
                    index_manager=index_manager,
                    api_key=self.api_key,
                    model=self.model,
                    similarity_top_k=self.similarity_top_k,
                    enable_markdown_formatting=True,
                    enable_rerank=self.enable_rerank,
                    **self.engine_kwargs
                )
                logger.info("AgenticQueryEngine 已创建")
            else:
                from backend.business.rag_engine.core.engine import ModularQueryEngine
                logger.info("创建模块化查询引擎（支持多种检索策略）")
                self._query_engine = ModularQueryEngine(
                    index_manager=index_manager,
                    api_key=self.api_key,
                    model=self.model,
                    similarity_top_k=self.similarity_top_k,
                    enable_markdown_formatting=True,
                    retrieval_strategy=self.retrieval_strategy,
                    enable_rerank=self.enable_rerank,
                    enable_debug=self.enable_debug,
                    **self.engine_kwargs
                )
                logger.info(f"模块化查询引擎已创建（检索策略: {self.retrieval_strategy or config.RETRIEVAL_STRATEGY}）")

        return self._query_engine
    
    def _format_history_text(self, max_turns: Optional[int] = None) -> str:
        """格式化对话历史为文本（公共方法）

        Args:
            max_turns: 最大轮数，None表示使用self.max_history_turns

        Returns:
            格式化的历史文本
        """
        from llama_index.core.llms import MessageRole

        chat_history = self.memory.get_all()
        if not chat_history:
            return ""

        max_turns = max_turns or self.max_history_turns
        history_text = ""
        for msg in chat_history[-max_turns:]:
            role = "用户" if msg.role == MessageRole.USER else "助手"
            history_text += f"{role}: {msg.content}\n"
        return history_text
    
    def _condense_query_with_history(self, current_message: str) -> str:
        """将对话历史压缩为完整查询（智能策略：短历史不压缩）

        Args:
            current_message: 当前用户消息

        Returns:
            压缩后的完整查询
        """
        from llama_index.core.llms import MessageRole

        # 获取历史对话
        chat_history = self.memory.get_all()

        if not chat_history or len(chat_history) == 0:
            # 没有历史，直接返回当前消息
            return current_message

        # 计算用户消息数量（每2条消息=1轮对话）
        user_message_count = sum(1 for msg in chat_history if msg.role == MessageRole.USER)
        
        # 智能压缩策略
        if self.enable_smart_condense:
            if user_message_count <= 2:
                # 短历史（≤2轮）：直接拼接，不调用LLM压缩
                history_text = self._format_history_text(max_turns=4)
                if history_text:
                    # 简单拼接：历史 + 当前问题
                    condensed_query = f"{history_text.strip()}\n用户: {current_message}"
                    logger.debug(f"短历史直接拼接（{user_message_count}轮）")
                    return condensed_query
            elif user_message_count <= 4:
                # 中等历史（3-4轮）：简单拼接，不压缩
                history_text = self._format_history_text(max_turns=6)
                if history_text:
                    condensed_query = f"{history_text.strip()}\n用户: {current_message}"
                    logger.debug(f"中等历史简单拼接（{user_message_count}轮）")
                    return condensed_query
        
        # 长历史（≥5轮）：使用LLM压缩
        history_text = self._format_history_text(max_turns=self.max_history_turns)
        
        condense_prompt = f"""基于以下对话历史和当前问题，生成一个完整的、自包含的查询。

对话历史：
{history_text}

当前问题：{current_message}

请生成一个完整的查询，该查询应该：
1. 包含对话历史中的关键上下文信息
2. 明确当前问题的意图
3. 是一个可以直接用于检索的完整问题

只返回生成的查询，不要其他说明。"""
        
        try:
            response = self.llm.complete(condense_prompt)
            condensed_query = response.text.strip()
            logger.debug(f"查询压缩（{user_message_count}轮）: '{current_message[:50]}...' -> '{condensed_query[:50]}...'")
            return condensed_query
        except Exception as e:
            logger.warning(f"查询压缩失败，使用简单拼接: {e}")
            # 降级策略：简单拼接
            history_text = self._format_history_text(max_turns=4)
            if history_text:
                return f"{history_text.strip()}\n用户: {current_message}"
            return current_message
    
    def _evaluate_retrieval_quality(self, sources: List[dict]) -> None:
        """评估检索质量并记录日志
        
        Args:
            sources: 引用来源列表
        """
        if not sources:
            return
        
        max_score = max([s.get('score', 0) for s in sources]) if sources else 0
        high_quality_sources = [s for s in sources if s.get('score', 0) >= self.similarity_threshold]
        
        if max_score < self.similarity_threshold:
            logger.warning(f"检索质量较低（最高相似度: {max_score:.2f}），答案可能更多依赖模型推理")
        elif len(high_quality_sources) >= self.min_high_quality_sources:
            logger.info(f"检索质量良好（高质量结果: {len(high_quality_sources)}个，最高相似度: {max_score:.2f}）")
    
    def _build_llm_prompt(self, message: str) -> str:
        """构建纯LLM模式的prompt
        
        Args:
            message: 用户消息
            
        Returns:
            构建的prompt
        """
        history_text = self._format_history_text()
        
        if history_text:
            return f"""基于以下对话历史回答用户问题。

对话历史：
{history_text}

用户问题：{message}

请用中文提供专业、深入的回答。"""
        else:
            return f"""回答用户问题。

用户问题：{message}

请用中文提供专业、深入的回答。"""
    
    def _execute_rag_query(self, message: str) -> Tuple[str, List[dict], Optional[str]]:
        """执行RAG模式查询
        
        Args:
            message: 用户消息
            
        Returns:
            (答案, 引用来源, 推理链内容)
        """
        # 压缩对话历史+当前问题为完整查询
        condensed_query = self._condense_query_with_history(message)
        
        # 使用ModularQueryEngine执行查询
        answer, sources, reasoning_content, _ = self.query_engine.query(condensed_query, collect_trace=False)
        
        # 评估检索质量
        self._evaluate_retrieval_quality(sources)
        
        return answer, sources, reasoning_content
    
    def _execute_llm_query(self, message: str) -> Tuple[str, List[dict], Optional[str]]:
        """执行纯LLM模式查询
        
        Args:
            message: 用户消息
            
        Returns:
            (答案, 引用来源, 推理链内容)
        """
        prompt = self._build_llm_prompt(message)
        response = self.llm.complete(prompt)
        answer = response.text.strip()
        answer = self.formatter.format(answer, None)
        logger.debug("纯LLM模式（无知识库检索）")
        return answer, [], None
    
    def _update_memory_and_session(
        self,
        message: str,
        answer: str,
        sources: List[dict],
        reasoning_content: Optional[str]
    ) -> None:
        """更新对话记忆和会话上下文

        Args:
            message: 用户消息
            answer: AI回答
            sources: 引用来源
            reasoning_content: 推理链内容
        """
        from llama_index.core.llms import ChatMessage, MessageRole

        # 更新对话记忆
        self.memory.put(ChatMessage(role=MessageRole.USER, content=message))
        self.memory.put(ChatMessage(role=MessageRole.ASSISTANT, content=answer))
        
        # 添加到会话上下文
        store_reasoning = config.DEEPSEEK_STORE_REASONING if reasoning_content else False
        if store_reasoning:
            self.current_session.add_turn(message, answer, sources, reasoning_content)
        else:
            self.current_session.add_turn(message, answer, sources)
        
        # 自动保存会话到文件
        self._save_session()
        
        # 记录日志
        logger.info(f"AI回答（前100字符）: {answer[:100]}...")
        if sources:
            logger.info(f"引用来源: {len(sources)} 个")
        if reasoning_content:
            logger.debug(f"推理链内容已提取（长度: {len(reasoning_content)} 字符）")
    
    def _save_session(self) -> None:
        """保存当前会话到文件"""
        return
    
    def start_session(self, session_id: Optional[str] = None) -> ChatSession:
        """开始新会话"""
        self.current_session = ChatSession(session_id=session_id)
        self.memory.reset()
        logger.info(f"新会话开始: {self.current_session.session_id}")
        return self.current_session

    def _iter_async_stream(self, async_iter):
        """Iterate an async generator from sync code."""
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            while True:
                try:
                    chunk = loop.run_until_complete(async_iter.__anext__())
                except StopAsyncIteration:
                    break
                yield chunk
        finally:
            try:
                loop.run_until_complete(async_iter.aclose())
            except Exception:
                pass
            loop.close()
            asyncio.set_event_loop(None)
    
    def chat(self, message: str) -> tuple[str, List[dict], Optional[str]]:
        """进行对话（使用ModularQueryEngine + 对话记忆）
        
        Returns:
            (答案, 引用来源, 推理链内容)
        """
        if self.current_session is None:
            self.start_session()
        
        try:
            logger.info(f"用户消息: {message}")

            parts: List[str] = []
            sources: List[dict] = []
            reasoning_content: Optional[str] = None
            final_answer: Optional[str] = None

            async_iter = self.stream_chat(message)
            for chunk in self._iter_async_stream(async_iter):
                if not isinstance(chunk, dict):
                    continue
                chunk_type = chunk.get("type")
                if chunk_type == "token":
                    text = chunk.get("data") or ""
                    if text:
                        parts.append(text)
                elif chunk_type == "sources":
                    sources = chunk.get("data") or []
                elif chunk_type == "reasoning":
                    reasoning_content = chunk.get("data")
                elif chunk_type == "done":
                    data = chunk.get("data") or {}
                    if "answer" in data:
                        final_answer = data.get("answer")
                    if "sources" in data:
                        sources = data.get("sources") or sources
                    if "reasoning_content" in data:
                        reasoning_content = data.get("reasoning_content")
                elif chunk_type == "error":
                    message = (chunk.get("data") or {}).get("message", "Unknown error")
                    raise RuntimeError(message)

            answer = final_answer if final_answer is not None else "".join(parts).strip()
            return answer, sources, reasoning_content
            
        except Exception as e:
            logger.error(f"对话失败: {e}", exc_info=True)
            raise
    
    
    async def stream_chat(self, message: str):
        """异步流式对话（使用真正的流式API）
        
        Args:
            message: 用户消息
            
        Yields:
            dict: 流式响应字典，包含以下类型：
                - 'type': 'token', 'data': token文本
                - 'type': 'sources', 'data': 引用来源列表
                - 'type': 'reasoning', 'data': 推理链内容
                - 'type': 'done', 'data': 完整答案和会话信息
        """
        if self.current_session is None:
            self.start_session()
        
        try:
            logger.info(f"用户消息（流式）: {message}")
            
            full_answer = ""
            sources = []
            reasoning_content = None
            
            # 执行流式查询
            if self.query_engine:
                # RAG模式：使用流式查询
                condensed_query = self._condense_query_with_history(message)
                
                async for chunk in self.query_engine.stream_query(condensed_query):
                    if chunk['type'] == 'token':
                        full_answer += chunk['data']
                        yield chunk
                    elif chunk['type'] == 'sources':
                        sources = chunk['data']
                        yield chunk
                    elif chunk['type'] == 'reasoning':
                        reasoning_content = chunk['data']
                        yield chunk
                    elif chunk['type'] == 'done':
                        # 从 done 事件中获取最终答案（如果流式过程中有格式化）
                        if 'answer' in chunk['data']:
                            full_answer = chunk['data']['answer']
                        if 'sources' in chunk['data']:
                            sources = chunk['data']['sources']
                        if 'reasoning_content' in chunk['data']:
                            reasoning_content = chunk['data']['reasoning_content']
                    elif chunk['type'] == 'error':
                        logger.error(f"流式查询错误: {chunk['data'].get('message', 'Unknown error')}")
                        yield chunk
                        return
            else:
                # 纯LLM模式：使用流式完成
                prompt = self._build_llm_prompt(message)
                
                # 使用 stream_complete 进行流式输出
                for chunk in self.llm.stream_complete(prompt):
                    chunk_text = chunk.text if hasattr(chunk, 'text') else str(chunk)
                    if chunk_text:
                        full_answer += chunk_text
                        yield {'type': 'token', 'data': chunk_text}
                
                # 格式化答案
                full_answer = self.formatter.format(full_answer, None)
            
            # 更新对话记忆和会话上下文
            self._update_memory_and_session(message, full_answer, sources, reasoning_content)
            
            # 返回完成事件
            yield {
                'type': 'done',
                'data': {
                    'answer': full_answer,
                    'session_id': self.current_session.session_id if self.current_session else None,
                    'turn_count': len(self.current_session.history) if self.current_session else 0,
                }
            }
            
        except Exception as e:
            logger.error(f"流式对话失败: {e}", exc_info=True)
            yield {
                'type': 'error',
                'data': {'message': str(e)}
            }
            raise
    
    def get_current_session(self) -> Optional[ChatSession]:
        """获取当前会话"""
        return self.current_session
    
    def reset_session(self):
        """重置当前会话"""
        if self.current_session:
            self.current_session.clear_history()
        self.memory.reset()
        logger.info("会话已重置")

