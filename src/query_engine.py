"""
查询引擎模块
集成DeepSeek API，实现带引用溯源的查询功能
"""

from typing import List, Optional, Tuple
from llama_index.core import VectorStoreIndex
from llama_index.core.query_engine import CitationQueryEngine
from llama_index.core.schema import Response
from llama_index.llms.openai import OpenAI

from src.config import config
from src.indexer import IndexManager


class QueryEngine:
    """查询引擎"""
    
    def __init__(
        self,
        index_manager: IndexManager,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model: Optional[str] = None,
        similarity_top_k: Optional[int] = None,
        citation_chunk_size: int = 512,
    ):
        """初始化查询引擎
        
        Args:
            index_manager: 索引管理器
            api_key: DeepSeek API密钥
            api_base: API端点
            model: 模型名称
            similarity_top_k: 检索相似文档数量
            citation_chunk_size: 引用块大小
        """
        self.index_manager = index_manager
        self.similarity_top_k = similarity_top_k or config.SIMILARITY_TOP_K
        self.citation_chunk_size = citation_chunk_size
        
        # 配置DeepSeek LLM
        self.api_key = api_key or config.DEEPSEEK_API_KEY
        self.api_base = api_base or config.DEEPSEEK_API_BASE
        self.model = model or config.LLM_MODEL
        
        if not self.api_key:
            raise ValueError("未设置DEEPSEEK_API_KEY，请检查环境变量或配置文件")
        
        print(f"🤖 初始化DeepSeek LLM: {self.model}")
        self.llm = OpenAI(
            api_key=self.api_key,
            api_base=self.api_base,
            model=self.model,
            temperature=0.1,  # 降低温度以获得更稳定的回答
        )
        
        # 获取索引
        self.index = self.index_manager.get_index()
        
        # 创建带引用的查询引擎
        print("📝 创建引用查询引擎")
        self.query_engine = CitationQueryEngine.from_args(
            self.index,
            llm=self.llm,
            similarity_top_k=self.similarity_top_k,
            citation_chunk_size=self.citation_chunk_size,
        )
        
        print("✅ 查询引擎初始化完成")
    
    def query(self, question: str) -> Tuple[str, List[dict]]:
        """执行查询并返回带引用的答案
        
        Args:
            question: 用户问题
            
        Returns:
            (答案文本, 引用来源列表)
        """
        try:
            print(f"\n💬 查询: {question}")
            
            # 执行查询
            response: Response = self.query_engine.query(question)
            
            # 提取答案
            answer = str(response)
            
            # 提取引用来源
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
            
            print(f"✅ 查询完成，找到 {len(sources)} 个引用来源")
            
            return answer, sources
            
        except Exception as e:
            print(f"❌ 查询失败: {e}")
            raise
    
    def get_retriever(self):
        """获取检索器（用于高级用法）"""
        return self.index.as_retriever(similarity_top_k=self.similarity_top_k)


class SimpleQueryEngine:
    """简单查询引擎（不带引用溯源，用于快速查询）"""
    
    def __init__(
        self,
        index_manager: IndexManager,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model: Optional[str] = None,
        similarity_top_k: Optional[int] = None,
    ):
        """初始化简单查询引擎
        
        Args:
            index_manager: 索引管理器
            api_key: DeepSeek API密钥
            api_base: API端点
            model: 模型名称
            similarity_top_k: 检索相似文档数量
        """
        self.index_manager = index_manager
        self.similarity_top_k = similarity_top_k or config.SIMILARITY_TOP_K
        
        # 配置DeepSeek LLM
        self.api_key = api_key or config.DEEPSEEK_API_KEY
        self.api_base = api_base or config.DEEPSEEK_API_BASE
        self.model = model or config.LLM_MODEL
        
        if not self.api_key:
            raise ValueError("未设置DEEPSEEK_API_KEY")
        
        self.llm = OpenAI(
            api_key=self.api_key,
            api_base=self.api_base,
            model=self.model,
            temperature=0.1,
        )
        
        # 获取索引
        self.index = self.index_manager.get_index()
        
        # 创建标准查询引擎
        self.query_engine = self.index.as_query_engine(
            llm=self.llm,
            similarity_top_k=self.similarity_top_k,
        )
    
    def query(self, question: str) -> str:
        """执行简单查询
        
        Args:
            question: 用户问题
            
        Returns:
            答案文本
        """
        try:
            response = self.query_engine.query(question)
            return str(response)
        except Exception as e:
            print(f"❌ 查询失败: {e}")
            raise


def format_sources(sources: List[dict]) -> str:
    """格式化引用来源为可读文本
    
    Args:
        sources: 引用来源列表
        
    Returns:
        格式化的文本
    """
    if not sources:
        return "（无引用来源）"
    
    formatted = "\n\n📚 引用来源：\n"
    for source in sources:
        formatted += f"\n[{source['index']}] "
        
        # 添加文档信息
        metadata = source['metadata']
        if 'title' in metadata:
            formatted += f"{metadata['title']}"
        elif 'file_name' in metadata:
            formatted += f"{metadata['file_name']}"
        elif 'url' in metadata:
            formatted += f"{metadata['url']}"
        
        # 添加相似度分数
        if source['score'] is not None:
            formatted += f" (相似度: {source['score']:.2f})"
        
        formatted += f"\n   {source['text'][:200]}..."
        
        if len(source['text']) > 200:
            formatted += f"\n   （共{len(source['text'])}字）"
    
    return formatted


def create_query_engine(
    index_manager: IndexManager,
    with_citation: bool = True
) -> QueryEngine | SimpleQueryEngine:
    """创建查询引擎（便捷函数）
    
    Args:
        index_manager: 索引管理器
        with_citation: 是否使用引用溯源
        
    Returns:
        QueryEngine或SimpleQueryEngine对象
    """
    if with_citation:
        return QueryEngine(index_manager)
    else:
        return SimpleQueryEngine(index_manager)


if __name__ == "__main__":
    # 测试代码
    from llama_index.core import Document as LlamaDocument
    
    print("=== 测试查询引擎 ===\n")
    
    # 创建测试文档
    test_docs = [
        LlamaDocument(
            text="""系统科学是20世纪中期兴起的一门新兴学科，它研究系统的一般规律和方法。
            系统科学包括系统论、控制论、信息论等多个分支。""",
            metadata={"title": "系统科学概述", "source": "test"}
        ),
        LlamaDocument(
            text="""钱学森（1911-2009）是中国著名科学家，被誉为"中国航天之父"。
            他在系统工程和系统科学领域做出了杰出贡献，提出了开放的复杂巨系统理论。""",
            metadata={"title": "钱学森生平", "source": "test"}
        ),
        LlamaDocument(
            text="""系统工程是一种组织管理技术，用于解决大规模复杂系统的设计和实施问题。
            钱学森将系统工程引入中国，并结合中国实际进行了创新性发展。""",
            metadata={"title": "系统工程简介", "source": "test"}
        ),
    ]
    
    # 创建索引
    index_manager = IndexManager(collection_name="test_query")
    index_manager.build_index(test_docs)
    
    # 创建查询引擎
    query_engine = QueryEngine(index_manager)
    
    # 测试查询
    question = "钱学森在系统科学领域有什么贡献？"
    answer, sources = query_engine.query(question)
    
    print(f"\n问题: {question}")
    print(f"\n答案:\n{answer}")
    print(format_sources(sources))
    
    # 清理
    index_manager.clear_index()
    print("\n✅ 测试完成")

