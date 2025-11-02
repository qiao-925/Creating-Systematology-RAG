"""
Pipeline模块适配器

将ModularQueryEngine和其他组件适配为PipelineModule
"""

from typing import List, Any, Optional

from src.business.protocols import (
    PipelineModule,
    PipelineContext,
    ModuleType,
    RetrievalModule,
    RerankingModule,
    GenerationModule,
    FormattingModule,
)
from src.query.modular.engine import ModularQueryEngine
from src.indexer import IndexManager
from src.rerankers.factory import create_reranker
from src.logger import setup_logger

logger = setup_logger('pipeline_adapter')


class ModularQueryEngineRetrievalModule(RetrievalModule):
    """ModularQueryEngine检索模块适配器
    
    将ModularQueryEngine包装为RetrievalModule
    """
    
    def __init__(
        self,
        index_manager: IndexManager,
        modular_query_engine: Optional[ModularQueryEngine] = None,
        name: str = "modular_retrieval",
        config: Optional[dict] = None,
    ):
        """初始化检索模块适配器
        
        Args:
            index_manager: 索引管理器
            modular_query_engine: ModularQueryEngine实例（可选，会自动创建）
            name: 模块名称
            config: 模块配置
        """
        super().__init__(name, config)
        self.index_manager = index_manager
        
        if modular_query_engine:
            self.query_engine = modular_query_engine
        else:
            # 从配置创建ModularQueryEngine
            self.query_engine = ModularQueryEngine(
                index_manager=index_manager,
                **config or {}
            )
    
    def execute(self, context: PipelineContext) -> PipelineContext:
        """执行检索
        
        Args:
            context: 流水线上下文
            
        Returns:
            更新后的上下文
        """
        query = context.query
        
        try:
            # 调用ModularQueryEngine检索
            # 注意：这里只执行检索，不生成答案
            retriever = self.query_engine.retriever
            
            from llama_index.core.schema import QueryBundle
            query_bundle = QueryBundle(query_str=query)
            
            # 检索节点
            nodes = retriever.retrieve(query_bundle)
            
            # 应用后处理器
            for postprocessor in self.query_engine.postprocessors:
                nodes = postprocessor.postprocess_nodes(nodes, query_bundle)
            
            # 转换为文档格式
            retrieved_docs = []
            for node_with_score in nodes:
                doc = {
                    "text": node_with_score.node.text,
                    "score": node_with_score.score,
                    "metadata": node_with_score.node.metadata,
                }
                retrieved_docs.append(doc)
            
            # 更新上下文
            context.retrieved_docs = retrieved_docs
            context.set_metadata("retrieval_count", len(retrieved_docs))
            
            logger.info(f"检索完成: {len(retrieved_docs)} 个文档")
            
        except Exception as e:
            logger.error(f"检索失败: {e}", exc_info=True)
            context.set_error(f"检索失败: {str(e)}")
        
        return context
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Any]:
        """检索文档（接口方法）"""
        context = PipelineContext(query=query)
        context = self.execute(context)
        return context.retrieved_docs


class ModularRerankingModule(RerankingModule):
    """ModularQueryEngine重排序模块适配器"""
    
    def __init__(
        self,
        name: str = "modular_reranking",
        config: Optional[dict] = None,
    ):
        """初始化重排序模块适配器
        
        Args:
            name: 模块名称
            config: 模块配置（包含reranker_type等）
        """
        super().__init__(name, config)
        self.reranker = create_reranker(
            reranker_type=config.get("reranker_type") if config else None,
            top_n=config.get("rerank_top_n") if config else None,
        )
    
    def execute(self, context: PipelineContext) -> PipelineContext:
        """执行重排序"""
        if not self.reranker:
            logger.warning("重排序器未配置，跳过重排序")
            context.reranked_docs = context.retrieved_docs
            return context
        
        try:
            # 转换文档为NodeWithScore格式
            from llama_index.core.schema import NodeWithScore, TextNode, QueryBundle
            
            nodes = []
            for doc in context.retrieved_docs:
                node = TextNode(
                    text=doc.get("text", ""),
                    metadata=doc.get("metadata", {}),
                )
                nodes.append(NodeWithScore(
                    node=node,
                    score=doc.get("score", 0.0),
                ))
            
            # 执行重排序
            query_bundle = QueryBundle(query_str=context.query)
            reranked_nodes = self.reranker.rerank(nodes, query_bundle)
            
            # 转换回文档格式
            reranked_docs = []
            for node_with_score in reranked_nodes:
                doc = {
                    "text": node_with_score.node.text,
                    "score": node_with_score.score,
                    "metadata": node_with_score.node.metadata,
                }
                reranked_docs.append(doc)
            
            # 更新上下文
            context.reranked_docs = reranked_docs
            context.set_metadata("reranked_count", len(reranked_docs))
            
            logger.info(f"重排序完成: {len(reranked_docs)} 个文档")
            
        except Exception as e:
            logger.error(f"重排序失败: {e}", exc_info=True)
            context.set_error(f"重排序失败: {str(e)}")
            # 降级：使用原始检索结果
            context.reranked_docs = context.retrieved_docs
        
        return context
    
    def rerank(self, query: str, documents: List[Any]) -> List[Any]:
        """重排序文档（接口方法）"""
        context = PipelineContext(query=query, retrieved_docs=documents)
        context = self.execute(context)
        return context.reranked_docs


class ModularGenerationModule(GenerationModule):
    """ModularQueryEngine生成模块适配器
    
    使用ModularQueryEngine的LLM生成答案
    """
    
    def __init__(
        self,
        modular_query_engine: ModularQueryEngine,
        name: str = "modular_generation",
        config: Optional[dict] = None,
    ):
        """初始化生成模块适配器
        
        Args:
            modular_query_engine: ModularQueryEngine实例
            name: 模块名称
            config: 模块配置
        """
        super().__init__(name, config)
        self.query_engine = modular_query_engine
        self.llm = modular_query_engine.llm
    
    def execute(self, context: PipelineContext) -> PipelineContext:
        """执行生成"""
        try:
            # 构建提示词（使用检索到的文档）
            documents = context.reranked_docs or context.retrieved_docs
            
            # 构建上下文字符串
            context_str = "\n\n".join([
                f"[文档{i+1}] {doc.get('text', '')}"
                for i, doc in enumerate(documents)
            ])
            
            # 构建提示词
            prompt = f"""你是一位系统科学领域的资深专家，拥有深厚的理论基础和丰富的实践经验。

【知识库参考】
{context_str}

【用户问题】
{context.query}

【回答要求】
1. 充分理解用户问题的深层含义和背景
2. 优先使用知识库中的权威信息作为基础
3. 结合你的专业知识进行深入分析和推理
4. 当知识库信息不足时，可基于专业原理进行合理推断，但需说明这是推理结论
5. 提供完整、深入、有洞察力的回答

请用中文回答问题。"""
            
            # 使用LLM生成答案
            response = self.llm.complete(prompt)
            answer = str(response).strip()
            
            # 更新上下文
            context.raw_answer = answer
            context.prompt = prompt
            context.set_metadata("documents_used", len(documents))
            
            logger.info(f"生成完成: answer_len={len(answer)}")
            
        except Exception as e:
            logger.error(f"生成失败: {e}", exc_info=True)
            context.set_error(f"生成失败: {str(e)}")
        
        return context
    
    def generate(self, prompt: str) -> str:
        """生成答案（接口方法）"""
        context = PipelineContext(query=prompt)
        context = self.execute(context)
        return context.raw_answer


class ModularFormattingModule(FormattingModule):
    """响应格式化模块适配器"""
    
    def __init__(
        self,
        modular_query_engine: ModularQueryEngine,
        name: str = "modular_formatting",
        config: Optional[dict] = None,
    ):
        """初始化格式化模块适配器"""
        super().__init__(name, config)
        self.formatter = modular_query_engine.formatter
    
    def execute(self, context: PipelineContext) -> PipelineContext:
        """执行格式化"""
        try:
            # 获取源文档（用于格式化）
            sources = []
            documents = context.reranked_docs or context.retrieved_docs
            
            # 转换为sources格式
            for doc in documents:
                source = {
                    "text": doc.get("text", ""),
                    "score": doc.get("score", 0.0),
                    "metadata": doc.get("metadata", {}),
                }
                sources.append(source)
            
            # 使用ModularQueryEngine的格式化器
            formatted_answer = self.formatter.format(
                answer=context.raw_answer,
                sources=sources,
            )
            
            # 更新上下文
            context.formatted_answer = formatted_answer
            context.set_metadata("sources", sources)
            
            logger.info(f"格式化完成")
            
        except Exception as e:
            logger.error(f"格式化失败: {e}", exc_info=True)
            # 降级：使用原始答案
            context.formatted_answer = context.raw_answer
        
        return context
    
    def format(self, answer: str, sources: List[Any]) -> str:
        """格式化输出（接口方法）"""
        context = PipelineContext(
            raw_answer=answer,
            metadata={"sources": sources}
        )
        context = self.execute(context)
        return context.formatted_answer

