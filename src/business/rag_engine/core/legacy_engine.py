"""
RAG引擎遗留模块：CitationQueryEngine实现，带引用溯源

主要功能：
- QueryEngine类：查询引擎，基于CitationQueryEngine实现
- query()：执行查询，返回带引用的回答
- 支持推理链提取和格式化

执行流程：
1. 初始化查询引擎（连接索引、LLM、回调管理器）
2. 执行查询并获取响应
3. 提取推理链（如果支持）
4. 格式化响应和引用来源
5. 返回查询结果

特性：
- 带引用溯源的查询
- 支持推理链显示
- 完整的响应格式化
- 支持调试和追踪
"""

import time
from typing import List, Optional, Tuple, Dict, Any

from llama_index.core import VectorStoreIndex, Settings, PromptTemplate
from llama_index.core.query_engine import CitationQueryEngine
from llama_index.core.base.response.schema import Response
from llama_index.core.callbacks import CallbackManager, LlamaDebugHandler

from src.infrastructure.config import config, get_gpu_device
from src.infrastructure.indexer import IndexManager
from src.infrastructure.logger import get_logger
from src.business.rag_engine.formatting import ResponseFormatter
from src.business.rag_engine.formatting.templates import SIMPLE_MARKDOWN_TEMPLATE
from src.business.rag_engine.utils.utils import extract_sources_from_response
from src.infrastructure.llms import create_deepseek_llm_for_query, extract_reasoning_content

logger = get_logger('rag_engine')


class QueryEngine:
    """查询引擎（遗留实现）"""
    
    def __init__(
        self,
        index_manager: IndexManager,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model: Optional[str] = None,
        similarity_top_k: Optional[int] = None,
        citation_chunk_size: int = 512,
        enable_debug: bool = False,
        similarity_threshold: Optional[float] = None,
        enable_markdown_formatting: bool = True,
    ):
        """初始化查询引擎
        
        Args:
            index_manager: 索引管理器
            api_key: DeepSeek API密钥
            api_base: API端点
            model: 模型名称
            similarity_top_k: 检索相似文档数量
            citation_chunk_size: 引用块大小
            enable_debug: 是否启用调试模式
            similarity_threshold: 相似度阈值
            enable_markdown_formatting: 是否启用Markdown格式化
        """
        self.index_manager = index_manager
        self.similarity_top_k = similarity_top_k or config.SIMILARITY_TOP_K
        self.citation_chunk_size = citation_chunk_size
        self.enable_debug = enable_debug
        self.similarity_threshold = similarity_threshold or config.SIMILARITY_THRESHOLD
        
        # 初始化响应格式化器
        self.formatter = ResponseFormatter(enable_formatting=enable_markdown_formatting)
        logger.info(f"响应格式化器已{'启用' if enable_markdown_formatting else '禁用'}")
        
        # 配置DeepSeek LLM
        self.api_key = api_key or config.DEEPSEEK_API_KEY
        self.model = model or config.LLM_MODEL
        
        if not self.api_key:
            raise ValueError("未设置DEEPSEEK_API_KEY，请检查环境变量或配置文件")
        
        # 配置调试模式
        if self.enable_debug:
            logger.info("🔍 启用调试模式（LlamaDebugHandler）")
            self.llama_debug = LlamaDebugHandler(print_trace_on_end=True)
            Settings.callback_manager = CallbackManager([self.llama_debug])
        
        logger.info(f"🤖 初始化DeepSeek LLM: {self.model}")
        self.llm = create_deepseek_llm_for_query(
            api_key=self.api_key,
            model=self.model,
            max_tokens=4096,
        )
        
        # 获取索引
        self.index = self.index_manager.get_index()
        
        # 创建 Markdown Prompt 模板（如果启用格式化）
        markdown_template = None
        if enable_markdown_formatting:
            markdown_template = PromptTemplate(SIMPLE_MARKDOWN_TEMPLATE)
            logger.info("📝 启用 Markdown 格式化 Prompt")
        
        # 创建带引用的查询引擎
        logger.info("📝 创建引用查询引擎")
        query_engine_kwargs = {
            'llm': self.llm,
            'similarity_top_k': self.similarity_top_k,
            'citation_chunk_size': self.citation_chunk_size,
        }
        
        if markdown_template is not None:
            query_engine_kwargs['text_qa_template'] = markdown_template
        
        self.query_engine = CitationQueryEngine.from_args(
            self.index,
            **query_engine_kwargs
        )
        
        logger.info("✅ 查询引擎初始化完成")
    
    def query(self, question: str, collect_trace: bool = False) -> Tuple[str, List[dict], Optional[str], Optional[Dict[str, Any]]]:
        """执行查询并返回带引用的答案
        
        Args:
            question: 用户问题
            collect_trace: 是否收集详细的追踪信息
            
        Returns:
            (答案文本, 引用来源列表, 推理链内容, 追踪信息字典)
        """
        from src.business.rag_engine.utils.utils import collect_trace_info, handle_fallback
        
        trace_info = None
        
        try:
            device = get_gpu_device()
            device_mode = "GPU加速" if device.startswith("cuda") else "CPU模式"
            
            logger.info(f"💬 查询: {question}")
            logger.debug(f"查询设备: {device} ({device_mode})")
            
            if collect_trace:
                trace_info = {
                    "query": question,
                    "start_time": time.time(),
                    "retrieval": {},
                    "llm_generation": {}
                }
            
            # 执行检索
            retrieval_start = time.time()
            
            # 获取 Collection 统计信息
            stats = self.index_manager.get_stats()
            collection_total_docs = stats.get('document_count', 0)
            collection_name = stats.get('collection_name', 'unknown')
            
            if 'error' in stats:
                error_info = stats.get('error', '未知错误')
                logger.warning(f"⚠️  获取Collection统计信息时出现问题: {error_info}")
            
            logger.info(f"📊 Collection: {collection_name}, 总文档数: {collection_total_docs}")
            
            if collection_total_docs == 0:
                logger.warning(f"⚠️  **重要提示**: Collection '{collection_name}' 的文档数为0")
                logger.warning(f"   请前往 '设置页面 > 数据源管理' 重新导入数据")
            
            # 执行查询
            response: Response = self.query_engine.query(question)
            retrieval_time = time.time() - retrieval_start
            
            # 提取推理链内容（如果存在）
            reasoning_content = extract_reasoning_content(response)
            
            # 提取答案
            answer = str(response)
            answer = self.formatter.format(answer, None)
            
            # 提取引用来源
            sources = extract_sources_from_response(response)
            
            # 处理兜底逻辑（使用共享函数，与新引擎逻辑统一）
            # 使用 SIMILARITY_CUTOFF 确保与新引擎使用相同的阈值配置
            similarity_cutoff = config.SIMILARITY_CUTOFF
            answer, fallback_reason = handle_fallback(
                answer, sources, question, self.llm, similarity_cutoff
            )
            
            # 收集追踪信息
            if collect_trace and trace_info:
                trace_info = collect_trace_info(
                    trace_info, retrieval_time, sources, self.similarity_top_k,
                    similarity_cutoff, self.model, answer, fallback_reason
                )
                if reasoning_content:
                    trace_info["has_reasoning"] = True
                    trace_info["reasoning_length"] = len(reasoning_content)
            
            logger.info(f"✅ 查询完成，找到 {len(sources)} 个引用来源")
            if reasoning_content:
                logger.debug(f"🧠 推理链内容已提取（长度: {len(reasoning_content)} 字符）")
            
            return answer, sources, reasoning_content, trace_info
            
        except Exception as e:
            logger.error(f"❌ 查询失败: {e}")
            raise
    
    async def stream_query(self, question: str):
        """异步流式查询（暂未实现）
        
        Args:
            question: 用户问题
            
        Yields:
            dict: 包含type和data的字典
        """
        raise NotImplementedError("流式查询暂未实现")
    
    def get_retriever(self):
        """获取检索器（用于高级用法）"""
        return self.index.as_retriever(similarity_top_k=self.similarity_top_k)
