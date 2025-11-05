"""
对话管理 - 管理器核心模块
ChatManager类实现
"""

from typing import Optional, List
from pathlib import Path

from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.chat_engine import CondensePlusContextChatEngine
from llama_index.core.llms import ChatMessage, MessageRole

from src.config import config
from src.indexer import IndexManager
from src.logger import setup_logger
from src.response_formatter import ResponseFormatter
from src.response_formatter.templates import CHAT_MARKDOWN_TEMPLATE
from src.chat.session import ChatSession
from src.llms import create_deepseek_llm_for_query, extract_reasoning_content, extract_reasoning_from_stream_chunk

logger = setup_logger('chat_manager')


class ChatManager:
    """对话管理器"""
    
    def __init__(
        self,
        index_manager: Optional[IndexManager] = None,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model: Optional[str] = None,
        memory_token_limit: int = 3000,
        similarity_top_k: Optional[int] = None,
        auto_save: bool = True,
        user_email: Optional[str] = None,
        enable_debug: bool = False,
        similarity_threshold: Optional[float] = None,
        enable_markdown_formatting: bool = True,
    ):
        """初始化对话管理器
        
        Args:
            index_manager: 索引管理器（可选，None时为纯LLM对话模式）
            api_key: DeepSeek API密钥
            api_base: API端点
            model: 模型名称
            memory_token_limit: 记忆token限制
            similarity_top_k: 检索相似文档数量
            auto_save: 是否自动保存会话
            user_email: 用户邮箱（用于会话目录隔离）
            enable_debug: 是否启用调试模式
            similarity_threshold: 相似度阈值
            enable_markdown_formatting: 是否启用Markdown格式化
        """
        self.index_manager = index_manager
        self.similarity_top_k = similarity_top_k or config.SIMILARITY_TOP_K
        self.auto_save = auto_save
        self.user_email = user_email
        self.enable_debug = enable_debug
        self.similarity_threshold = similarity_threshold or config.SIMILARITY_THRESHOLD
        
        # 初始化响应格式化器
        self.formatter = ResponseFormatter(enable_formatting=enable_markdown_formatting)
        logger.info(f"响应格式化器已{'启用' if enable_markdown_formatting else '禁用'}")
        
        # 配置DeepSeek LLM
        self.api_key = api_key or config.DEEPSEEK_API_KEY
        self.model = model or config.LLM_MODEL
        
        if not self.api_key:
            raise ValueError("未设置DEEPSEEK_API_KEY")
        
        # 配置调试模式
        if self.enable_debug:
            from llama_index.core import Settings
            from llama_index.core.callbacks import CallbackManager, LlamaDebugHandler
            logger.info("对话管理器：启用调试模式")
            llama_debug = LlamaDebugHandler(print_trace_on_end=True)
            Settings.callback_manager = CallbackManager([llama_debug])
        
        logger.info(f"初始化DeepSeek LLM (对话模式): {self.model}")
        self.llm = create_deepseek_llm_for_query(
            api_key=self.api_key,
            model=self.model,
        )
        
        # 创建记忆缓冲区
        self.memory = ChatMemoryBuffer.from_defaults(
            token_limit=memory_token_limit,
        )
        
        # 创建聊天引擎
        self._init_chat_engine(enable_markdown_formatting)
        
        # 当前会话
        self.current_session: Optional[ChatSession] = None
        
        logger.info("对话管理器初始化完成")
    
    def _init_chat_engine(self, enable_markdown_formatting: bool):
        """初始化聊天引擎"""
        if self.index_manager:
            # 有索引：使用RAG增强的对话引擎
            self.index = self.index_manager.get_index()
            logger.info("创建RAG增强对话引擎")
            
            # 选择 Prompt
            if enable_markdown_formatting:
                context_prompt = CHAT_MARKDOWN_TEMPLATE
                logger.info("已启用 Markdown 格式的对话 Prompt")
            else:
                context_prompt = (
                    "你是一位系统科学领域的资深专家，拥有深厚的理论基础和丰富的实践经验。\n\n"
                    "【知识库参考】\n{context_str}\n\n"
                    "【回答要求】\n"
                    "1. 充分理解用户问题的深层含义和背景\n"
                    "2. 优先使用知识库中的权威信息作为基础\n"
                    "3. 结合你的专业知识进行深入分析和推理\n"
                    "4. 当知识库信息不足时，可基于专业原理进行合理推断，但需说明这是推理结论\n"
                    "5. 提供完整、深入、有洞察力的回答\n\n"
                    "请用中文回答问题。"
                )
            
            self.chat_engine = CondensePlusContextChatEngine.from_defaults(
                retriever=self.index.as_retriever(similarity_top_k=self.similarity_top_k),
                llm=self.llm,
                memory=self.memory,
                context_prompt=context_prompt,
            )
        else:
            # 无索引：使用纯LLM对话引擎
            from llama_index.core.chat_engine import SimpleChatEngine
            logger.info("创建纯LLM对话引擎（无知识库）")
            self.chat_engine = SimpleChatEngine.from_defaults(
                llm=self.llm,
                memory=self.memory,
                system_prompt=(
                    "你是一位系统科学领域的资深专家，拥有深厚的理论基础和丰富的实践经验。\n"
                    "请用中文回答用户的问题，提供专业、深入的见解。"
                )
            )
    
    def start_session(self, session_id: Optional[str] = None) -> ChatSession:
        """开始新会话"""
        self.current_session = ChatSession(session_id=session_id)
        self.memory.reset()
        logger.info(f"新会话开始: {self.current_session.session_id}")
        return self.current_session
    
    def load_session(self, file_path: Path):
        """加载已有会话"""
        self.current_session = ChatSession.load(file_path)
        
        # 恢复对话历史到记忆
        self.memory.reset()
        for turn in self.current_session.history:
            self.memory.put(ChatMessage(role=MessageRole.USER, content=turn.question))
            self.memory.put(ChatMessage(role=MessageRole.ASSISTANT, content=turn.answer))
        
        logger.info(f"会话已加载: {self.current_session.session_id}, 包含 {len(self.current_session.history)} 轮对话")
    
    def chat(self, message: str) -> tuple[str, List[dict], Optional[str]]:
        """进行对话
        
        Returns:
            (答案, 引用来源, 推理链内容)
        """
        if self.current_session is None:
            self.start_session()
        
        try:
            logger.info(f"用户消息: {message}")
            
            # 执行对话
            response = self.chat_engine.chat(message)
            
            # 提取推理链内容（如果存在）
            reasoning_content = extract_reasoning_content(response)
            
            # 提取答案
            answer = str(response)
            answer = self.formatter.format(answer, None)
            
            # 提取引用来源（仅RAG模式有）
            sources = []
            if hasattr(response, 'source_nodes') and response.source_nodes:
                for i, node in enumerate(response.source_nodes, 1):
                    source = {
                        'index': i,
                        'text': node.node.text,
                        'score': node.score if hasattr(node, 'score') else None,
                        'metadata': node.node.metadata,
                    }
                    sources.append(source)
            
            # 评估检索质量（仅RAG模式）
            if self.index_manager and sources:
                max_score = max([s.get('score', 0) for s in sources]) if sources else 0
                high_quality_sources = [s for s in sources if s.get('score', 0) >= self.similarity_threshold]
                
                if max_score < self.similarity_threshold:
                    logger.warning(f"检索质量较低（最高相似度: {max_score:.2f}），答案可能更多依赖模型推理")
                elif len(high_quality_sources) >= 2:
                    logger.info(f"检索质量良好（高质量结果: {len(high_quality_sources)}个，最高相似度: {max_score:.2f}）")
            elif not self.index_manager:
                logger.debug("纯LLM模式（无知识库检索）")
            
            # 添加到会话历史（根据配置决定是否存储推理链）
            store_reasoning = config.DEEPSEEK_STORE_REASONING if reasoning_content else False
            if store_reasoning:
                # 注意：ChatTurn 需要扩展支持 reasoning_content
                self.current_session.add_turn(message, answer, sources, reasoning_content)
            else:
                self.current_session.add_turn(message, answer, sources)
            
            logger.info(f"AI回答（前100字符）: {answer[:100]}...")
            if sources:
                logger.info(f"引用来源: {len(sources)} 个")
            if reasoning_content:
                logger.debug(f"推理链内容已提取（长度: {len(reasoning_content)} 字符）")
            
            # 自动保存会话
            if self.auto_save:
                self.save_current_session()
            
            return answer, sources, reasoning_content
            
        except Exception as e:
            logger.error(f"对话失败: {e}", exc_info=True)
            raise
    
    async def stream_chat(self, message: str):
        """异步流式对话"""
        import asyncio
        
        if self.current_session is None:
            self.start_session()
        
        try:
            logger.info(f"用户消息（流式）: {message}")
            
            # 执行流式对话
            response_stream = self.chat_engine.stream_chat(message)
            
            # 收集完整答案和推理链
            full_answer = ""
            full_reasoning = ""
            
            # 流式输出token和推理链
            for chunk in response_stream.response_gen:
                # 提取推理链内容（流式）
                reasoning_chunk = extract_reasoning_from_stream_chunk(chunk) if hasattr(chunk, 'delta') or hasattr(chunk, 'message') else None
                if reasoning_chunk:
                    full_reasoning += reasoning_chunk
                    # 推理链内容不直接输出给用户，但可以记录
                    logger.debug(f"收到推理链片段: {len(reasoning_chunk)} 字符")
                
                # 提取普通内容
                if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'content'):
                    token = chunk.delta.content
                    if token:
                        full_answer += token
                        yield {'type': 'token', 'data': token}
                elif isinstance(chunk, str):
                    full_answer += chunk
                    yield {'type': 'token', 'data': chunk}
                
                await asyncio.sleep(0.02)
            
            # 提取引用来源
            sources = []
            if hasattr(response_stream, 'source_nodes') and response_stream.source_nodes:
                for i, node in enumerate(response_stream.source_nodes, 1):
                    source = {
                        'index': i,
                        'text': node.node.text,
                        'score': node.score if hasattr(node, 'score') else None,
                        'metadata': node.node.metadata,
                    }
                    sources.append(source)
            
            # 添加到会话历史（根据配置决定是否存储推理链）
            reasoning_content = full_reasoning if full_reasoning else None
            store_reasoning = config.DEEPSEEK_STORE_REASONING if reasoning_content else False
            if store_reasoning:
                self.current_session.add_turn(message, full_answer, sources, reasoning_content)
            else:
                self.current_session.add_turn(message, full_answer, sources)
            
            logger.info(f"AI回答（流式，前100字符）: {full_answer[:100]}...")
            if sources:
                logger.info(f"引用来源: {len(sources)} 个")
            if reasoning_content:
                logger.debug(f"推理链内容已提取（流式，长度: {len(reasoning_content)} 字符）")
            
            # 自动保存会话
            if self.auto_save:
                self.save_current_session()
            
            # 返回引用来源、推理链和完整答案
            yield {'type': 'sources', 'data': sources}
            if reasoning_content:
                yield {'type': 'reasoning', 'data': reasoning_content}
            yield {'type': 'done', 'data': full_answer}
            
        except Exception as e:
            logger.error(f"流式对话失败: {e}", exc_info=True)
            raise
    
    def get_current_session(self) -> Optional[ChatSession]:
        """获取当前会话"""
        return self.current_session
    
    def save_current_session(self, save_dir: Optional[Path] = None):
        """保存当前会话"""
        if self.current_session is None:
            logger.warning("没有活动会话需要保存")
            return
        
        if save_dir is None:
            # 如果有用户邮箱，保存到用户专属目录
            if self.user_email:
                save_dir = config.SESSIONS_PATH / self.user_email
                logger.debug(f"保存到用户目录: {save_dir}")
            else:
                save_dir = config.SESSIONS_PATH
                logger.debug(f"保存到默认目录: {save_dir}")
        
        self.current_session.save(save_dir)
    
    def reset_session(self):
        """重置当前会话"""
        if self.current_session:
            self.current_session.clear_history()
        self.memory.reset()
        logger.info("会话已重置")

