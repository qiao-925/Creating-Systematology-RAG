"""
模块化查询引擎

基于PipelineExecutor实现的模块化RAG查询引擎
演示如何将现有功能适配到新的流水线架构
"""

from typing import List, Tuple, Optional, Dict, Any

from src.business.protocols import (
    PipelineModule,
    PipelineContext,
    RetrievalModule,
    GenerationModule,
    FormattingModule,
)
from src.business.pipeline import PipelineExecutor, Pipeline, ExecutionResult
from src.indexer import IndexManager
from src.query_engine import QueryEngine
from src.logger import setup_logger

logger = setup_logger('modular_query_engine')


class QueryEngineRetrievalModule(RetrievalModule):
    """QueryEngine检索模块适配器
    
    将现有的QueryEngine检索功能适配到模块化架构
    """
    
    def __init__(self, query_engine: QueryEngine, name: str = "query_engine_retrieval"):
        super().__init__(name)
        self.query_engine = query_engine
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Any]:
        """检索文档（委托给QueryEngine）"""
        # 注意：这里简化实现，实际应该直接访问索引
        # QueryEngine的query方法会同时执行检索和生成
        # 在完整实现中，应该分离检索和生成逻辑
        return []
    
    def execute(self, context: PipelineContext) -> PipelineContext:
        """执行检索"""
        logger.info(f"执行检索: query={context.query[:50]}...")
        
        try:
            # 使用QueryEngine的索引进行检索
            index = self.query_engine.index
            retriever = index.as_retriever(
                similarity_top_k=self.query_engine.similarity_top_k
            )
            
            # 检索文档
            nodes = retriever.retrieve(context.query)
            context.retrieved_docs = nodes
            
            logger.info(f"检索完成: 找到 {len(nodes)} 个文档")
            context.set_metadata('retrieval_count', len(nodes))
            
        except Exception as e:
            logger.error(f"检索失败: {e}")
            context.set_error(f"检索失败: {str(e)}")
        
        return context


class QueryEngineGenerationModule(GenerationModule):
    """QueryEngine生成模块适配器"""
    
    def __init__(self, query_engine: QueryEngine, name: str = "query_engine_generation"):
        super().__init__(name)
        self.query_engine = query_engine
    
    def generate(self, prompt: str) -> str:
        """生成答案"""
        # 实际生成逻辑委托给LLM
        return ""
    
    def execute(self, context: PipelineContext) -> PipelineContext:
        """执行生成"""
        logger.info("执行生成...")
        
        try:
            # 使用CitationQueryEngine生成答案
            # 注意：这里直接使用query_engine.query()，在完整实现中应该分离
            answer, sources = self.query_engine.query(context.query)
            
            context.raw_answer = answer
            context.formatted_answer = answer
            context.set_metadata('sources', sources)
            
            logger.info(f"生成完成: answer_len={len(answer)}, sources={len(sources)}")
            
        except Exception as e:
            logger.error(f"生成失败: {e}")
            context.set_error(f"生成失败: {str(e)}")
        
        return context


class ModularQueryEngine:
    """模块化查询引擎
    
    基于PipelineExecutor的查询引擎，演示模块化架构
    
    Examples:
        >>> index_manager = IndexManager()
        >>> engine = ModularQueryEngine(index_manager)
        >>> answer, sources = engine.query("什么是系统思维？")
    """
    
    def __init__(
        self,
        index_manager: IndexManager,
        enable_pipeline: bool = True,
        **query_engine_kwargs
    ):
        """初始化模块化查询引擎
        
        Args:
            index_manager: 索引管理器
            enable_pipeline: 是否启用流水线模式（False则使用原QueryEngine）
            **query_engine_kwargs: 传递给QueryEngine的参数
        """
        self.index_manager = index_manager
        self.enable_pipeline = enable_pipeline
        
        # 创建QueryEngine（向后兼容）
        self.query_engine = QueryEngine(
            index_manager=index_manager,
            **query_engine_kwargs
        )
        
        if enable_pipeline:
            # 创建流水线
            self._setup_pipeline()
        
        logger.info(f"ModularQueryEngine初始化: pipeline={enable_pipeline}")
    
    def _setup_pipeline(self):
        """设置流水线"""
        # 创建模块
        retrieval_module = QueryEngineRetrievalModule(self.query_engine)
        generation_module = QueryEngineGenerationModule(self.query_engine)
        
        # 创建流水线
        self.pipeline = Pipeline(
            name="modular_rag",
            modules=[retrieval_module, generation_module],
            description="模块化RAG流水线",
        )
        
        # 创建执行器
        self.executor = PipelineExecutor(
            enable_hooks=True,
            stop_on_error=False,
        )
        
        logger.info("流水线设置完成")
    
    def query(
        self,
        question: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """查询接口
        
        Args:
            question: 用户问题
            user_id: 用户ID
            session_id: 会话ID
            
        Returns:
            Tuple[str, List[Dict]]: (答案, 来源列表)
        """
        if not self.enable_pipeline:
            # 降级到原QueryEngine
            logger.info("使用原QueryEngine")
            return self.query_engine.query(question)
        
        # 使用流水线
        logger.info(f"使用流水线查询: question={question[:50]}...")
        
        # 创建上下文
        context = PipelineContext(
            query=question,
            user_id=user_id,
            session_id=session_id,
        )
        
        # 执行流水线
        result = self.executor.execute(self.pipeline, context)
        
        if not result.success:
            logger.warning(f"流水线执行有错误: {result.errors}")
        
        # 提取结果
        answer = result.context.formatted_answer or result.context.raw_answer
        sources = result.context.get_metadata('sources', [])
        
        return answer, sources
    
    def add_module(self, module: PipelineModule):
        """添加模块到流水线"""
        if not self.enable_pipeline:
            logger.warning("Pipeline未启用，无法添加模块")
            return
        
        self.pipeline.add_module(module)
        logger.info(f"添加模块: {module.name}")
    
    def remove_module(self, module_name: str):
        """从流水线移除模块"""
        if not self.enable_pipeline:
            logger.warning("Pipeline未启用，无法移除模块")
            return
        
        self.pipeline.remove_module(module_name)
        logger.info(f"移除模块: {module_name}")
    
    def get_pipeline(self) -> Optional[Pipeline]:
        """获取流水线"""
        return self.pipeline if self.enable_pipeline else None
    
    def get_executor(self) -> Optional[PipelineExecutor]:
        """获取执行器"""
        return self.executor if self.enable_pipeline else None


# 便捷函数

def create_modular_query_engine(
    index_manager: IndexManager,
    enable_pipeline: bool = True,
    **kwargs
) -> ModularQueryEngine:
    """创建模块化查询引擎
    
    Args:
        index_manager: 索引管理器
        enable_pipeline: 是否启用流水线
        **kwargs: 其他参数
        
    Returns:
        ModularQueryEngine: 查询引擎实例
    """
    return ModularQueryEngine(
        index_manager=index_manager,
        enable_pipeline=enable_pipeline,
        **kwargs
    )
