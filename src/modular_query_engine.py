"""
模块化查询引擎
支持多种检索策略和后处理模块的灵活组合
"""

import time
from typing import List, Optional, Tuple, Dict, Any
from llama_index.core import VectorStoreIndex, Settings
from llama_index.core.retrievers import (
    VectorIndexRetriever,
    QueryFusionRetriever,
)
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import (
    SimilarityPostprocessor,
    SentenceTransformerRerank,
)
from llama_index.llms.deepseek import DeepSeek

from src.config import config
from src.indexer import IndexManager
from src.logger import setup_logger
from src.response_formatter import ResponseFormatter
from src.observers.manager import ObserverManager
from src.observers.factory import create_observer_from_config

logger = setup_logger('modular_query_engine')


class ModularQueryEngine:
    """模块化查询引擎（工厂模式）"""
    
    # 支持的检索策略
    SUPPORTED_STRATEGIES = ["vector", "bm25", "hybrid"]
    
    def __init__(
        self,
        index_manager: IndexManager,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        retrieval_strategy: Optional[str] = None,
        similarity_top_k: Optional[int] = None,
        enable_rerank: Optional[bool] = None,
        rerank_top_n: Optional[int] = None,
        similarity_cutoff: Optional[float] = None,
        enable_markdown_formatting: bool = True,
        observer_manager: Optional[ObserverManager] = None,  # 新增：观察器管理器
        **kwargs
    ):
        """初始化模块化查询引擎
        
        Args:
            index_manager: 索引管理器
            api_key: DeepSeek API密钥
            model: 模型名称
            retrieval_strategy: 检索策略 ("vector"|"bm25"|"hybrid")
            similarity_top_k: 检索文档数量
            enable_rerank: 是否启用重排序
            rerank_top_n: 重排序保留文档数
            similarity_cutoff: 相似度过滤阈值
            enable_markdown_formatting: 是否启用Markdown格式化
        """
        self.index_manager = index_manager
        self.index = index_manager.get_index()
        
        # 配置参数（优先使用传入参数，否则使用配置文件）
        self.retrieval_strategy = retrieval_strategy or config.RETRIEVAL_STRATEGY
        self.similarity_top_k = similarity_top_k or config.SIMILARITY_TOP_K
        self.enable_rerank = enable_rerank if enable_rerank is not None else config.ENABLE_RERANK
        self.rerank_top_n = rerank_top_n or config.RERANK_TOP_N
        self.similarity_cutoff = similarity_cutoff or config.SIMILARITY_CUTOFF
        
        # 验证策略
        if self.retrieval_strategy not in self.SUPPORTED_STRATEGIES:
            raise ValueError(
                f"不支持的检索策略: {self.retrieval_strategy}. "
                f"支持的策略: {self.SUPPORTED_STRATEGIES}"
            )
        
        # 初始化响应格式化器
        self.formatter = ResponseFormatter(enable_formatting=enable_markdown_formatting)
        
        # 初始化观察器管理器
        if observer_manager is not None:
            self.observer_manager = observer_manager
            logger.info(f"✅ 使用提供的观察器管理器: {len(observer_manager.observers)} 个观察器")
        else:
            # 从配置创建观察器
            self.observer_manager = create_observer_from_config()
            logger.info(f"✅ 从配置创建观察器管理器: {len(self.observer_manager.observers)} 个观察器")
        
        # 获取所有回调处理器
        callback_handlers = self.observer_manager.get_callback_handlers()
        if callback_handlers:
            from llama_index.core.callbacks import CallbackManager
            Settings.callback_manager = CallbackManager(callback_handlers)
            logger.info(f"✅ 设置 {len(callback_handlers)} 个回调处理器到 LlamaIndex")
        
        # 配置 LLM
        self.api_key = api_key or config.DEEPSEEK_API_KEY
        self.model = model or config.LLM_MODEL
        if not self.api_key:
            raise ValueError("未设置DEEPSEEK_API_KEY")
        
        self.llm = DeepSeek(
            api_key=self.api_key,
            model=self.model,
            temperature=0.5,
            max_tokens=4096,
        )
        
        # 创建检索器
        self.retriever = self._create_retriever()
        
        # 创建后处理器
        self.postprocessors = self._create_postprocessors()
        
        # 创建查询引擎
        self.query_engine = RetrieverQueryEngine.from_args(
            retriever=self.retriever,
            llm=self.llm,
            node_postprocessors=self.postprocessors,
        )
        
        logger.info(
            f"模块化查询引擎初始化完成: "
            f"策略={self.retrieval_strategy}, "
            f"top_k={self.similarity_top_k}, "
            f"重排序={self.enable_rerank}, "
            f"相似度阈值={self.similarity_cutoff}"
        )
        print(f"✅ 模块化查询引擎初始化完成")
        print(f"   检索策略: {self.retrieval_strategy}")
        print(f"   Top-K: {self.similarity_top_k}")
        print(f"   重排序: {'启用' if self.enable_rerank else '禁用'}")
        print(f"   相似度阈值: {self.similarity_cutoff}")
    
    def _create_retriever(self):
        """创建检索器（根据策略）"""
        if self.retrieval_strategy == "vector":
            logger.info("创建向量检索器")
            return VectorIndexRetriever(
                index=self.index,
                similarity_top_k=self.similarity_top_k,
            )
        
        elif self.retrieval_strategy == "bm25":
            logger.info("创建BM25检索器")
            try:
                from llama_index.retrievers.bm25 import BM25Retriever
            except ImportError:
                logger.error("BM25Retriever未安装，请运行: pip install llama-index-retrievers-bm25")
                raise ImportError(
                    "BM25Retriever未安装。请运行: pip install llama-index-retrievers-bm25"
                )
            
            # 从索引中获取所有节点
            nodes = list(self.index.docstore.docs.values())
            
            return BM25Retriever.from_defaults(
                nodes=nodes,
                similarity_top_k=self.similarity_top_k,
            )
        
        elif self.retrieval_strategy == "hybrid":
            logger.info("创建混合检索器（向量+BM25）")
            try:
                from llama_index.retrievers.bm25 import BM25Retriever
            except ImportError:
                logger.warning("BM25Retriever未安装，降级为纯向量检索")
                print("⚠️  BM25未安装，降级为向量检索")
                return VectorIndexRetriever(
                    index=self.index,
                    similarity_top_k=self.similarity_top_k,
                )
            
            # 向量检索器
            vector_retriever = VectorIndexRetriever(
                index=self.index,
                similarity_top_k=self.similarity_top_k,
            )
            
            # BM25检索器
            nodes = list(self.index.docstore.docs.values())
            bm25_retriever = BM25Retriever.from_defaults(
                nodes=nodes,
                similarity_top_k=self.similarity_top_k,
            )
            
            # 融合检索器
            return QueryFusionRetriever(
                retrievers=[vector_retriever, bm25_retriever],
                similarity_top_k=self.similarity_top_k,
                num_queries=1,  # 不生成额外查询
                mode="reciprocal_rerank",  # 倒数排名融合
                use_async=False,
            )
    
    def _create_postprocessors(self) -> List:
        """创建后处理器（链式组合）"""
        postprocessors = []
        
        # 1. 相似度过滤（总是启用）
        postprocessors.append(
            SimilarityPostprocessor(similarity_cutoff=self.similarity_cutoff)
        )
        logger.info(f"添加相似度过滤器: cutoff={self.similarity_cutoff}")
        
        # 2. 重排序（可选）
        if self.enable_rerank:
            try:
                # 尝试使用统一的Embedding实例
                embedding_instance = self.index_manager.get_embedding_instance()
                
                if embedding_instance is not None:
                    # 优先使用统一的Embedding实例
                    logger.info(f"重排序使用统一Embedding实例: {embedding_instance.get_model_name()}")
                    
                    # 获取LlamaIndex兼容的模型
                    if hasattr(embedding_instance, 'get_llama_index_embedding'):
                        rerank_embedding = embedding_instance.get_llama_index_embedding()
                        # 使用底层模型名称
                        rerank_model = rerank_embedding.model_name
                    else:
                        # 直接使用（假设已兼容）
                        rerank_model = config.RERANK_MODEL or config.EMBEDDING_MODEL
                else:
                    # 降级：使用配置中的模型名称
                    rerank_model = config.RERANK_MODEL or config.EMBEDDING_MODEL
                    logger.info(f"重排序使用配置模型: {rerank_model}")
                
                postprocessors.append(
                    SentenceTransformerRerank(
                        model=rerank_model,
                        top_n=self.rerank_top_n,
                    )
                )
                logger.info(f"添加重排序模块: model={rerank_model}, top_n={self.rerank_top_n}")
            except Exception as e:
                logger.warning(f"重排序模块初始化失败，跳过: {e}")
                print(f"⚠️  重排序模块初始化失败: {e}")
        
        return postprocessors
    
    def query(
        self, 
        question: str, 
        collect_trace: bool = False
    ) -> Tuple[str, List[dict], Optional[Dict[str, Any]]]:
        """执行查询（兼容现有API）
        
        Args:
            question: 用户问题
            collect_trace: 是否收集追踪信息
            
        Returns:
            (答案文本, 引用来源列表, 追踪信息)
        """
        trace_info = None
        
        # 通知观察器：查询开始
        trace_ids = self.observer_manager.on_query_start(question)
        
        try:
            logger.info(f"执行查询: {question}")
            print(f"\n💬 查询: {question}")
            
            if collect_trace:
                trace_info = {
                    "query": question,
                    "strategy": self.retrieval_strategy,
                    "start_time": time.time(),
                    "observer_trace_ids": trace_ids,  # 记录观察器追踪ID
                }
            
            # 执行查询
            retrieval_start = time.time()
            response = self.query_engine.query(question)
            retrieval_time = time.time() - retrieval_start
            
            # 提取答案
            answer = str(response)
            answer = self.formatter.format(answer, None)
            
            # 提取引用来源
            sources = []
            if hasattr(response, 'source_nodes') and response.source_nodes:
                logger.info(f"检索到 {len(response.source_nodes)} 个文档片段")
                print(f"🔍 检索到 {len(response.source_nodes)} 个文档片段")
                
                for i, node in enumerate(response.source_nodes, 1):
                    try:
                        metadata = node.node.metadata if hasattr(node, 'node') and hasattr(node.node, 'metadata') else {}
                        if not isinstance(metadata, dict):
                            metadata = {}
                    except Exception:
                        metadata = {}
                    
                    score = node.score if hasattr(node, 'score') else None
                    
                    source = {
                        'index': i,
                        'text': node.node.text if hasattr(node, 'node') else '',
                        'score': score,
                        'metadata': metadata,
                    }
                    sources.append(source)
                    
                    # 打印简要信息
                    score_str = f"{score:.4f}" if score is not None else "N/A"
                    file_name = metadata.get('file_name', metadata.get('file_path', '未知').split('/')[-1])
                    print(f"  [{i}] {file_name} (分数: {score_str})")
            
            # 追踪信息
            if collect_trace and trace_info:
                trace_info["retrieval_time"] = round(retrieval_time, 2)
                trace_info["chunks_retrieved"] = len(sources)
                trace_info["total_time"] = round(time.time() - trace_info["start_time"], 2)
            
            print(f"✅ 查询完成，找到 {len(sources)} 个引用来源")
            
            # 通知观察器：查询结束
            self.observer_manager.on_query_end(
                query=question,
                answer=answer,
                sources=sources,
                trace_ids=trace_ids,
                retrieval_time=retrieval_time if 'retrieval_time' in locals() else None,
            )
            
            return answer, sources, trace_info
            
        except Exception as e:
            logger.error(f"查询失败: {e}", exc_info=True)
            print(f"❌ 查询失败: {e}")
            raise
    
    async def stream_query(self, question: str):
        """异步流式查询（用于Web应用）"""
        # TODO: 实现流式查询
        raise NotImplementedError("流式查询暂未实现")


def create_modular_query_engine(
    index_manager: IndexManager,
    strategy: Optional[str] = None,
    **kwargs
) -> ModularQueryEngine:
    """创建模块化查询引擎（便捷函数）
    
    Args:
        index_manager: 索引管理器
        strategy: 检索策略 ("vector"|"bm25"|"hybrid")
        **kwargs: 其他参数
        
    Returns:
        ModularQueryEngine实例
    """
    return ModularQueryEngine(
        index_manager=index_manager,
        retrieval_strategy=strategy,
        **kwargs
    )

