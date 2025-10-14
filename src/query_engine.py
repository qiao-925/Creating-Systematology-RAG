"""
查询引擎模块
集成DeepSeek API，实现带引用溯源的查询功能
支持Phoenix可观测性和LlamaDebugHandler调试
"""

import time
from typing import List, Optional, Tuple, Dict, Any
from llama_index.core import VectorStoreIndex, Settings
from llama_index.core.query_engine import CitationQueryEngine
from llama_index.core.base.response.schema import Response
from llama_index.core.schema import Document as LlamaDocument
from llama_index.core.callbacks import CallbackManager, LlamaDebugHandler
from llama_index.llms.deepseek import DeepSeek

from src.config import config
from src.indexer import IndexManager
from src.logger import setup_logger

logger = setup_logger('query_engine')


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
        enable_debug: bool = False,
        similarity_threshold: Optional[float] = None,
    ):
        """初始化查询引擎
        
        Args:
            index_manager: 索引管理器
            api_key: DeepSeek API密钥
            api_base: API端点
            model: 模型名称
            similarity_top_k: 检索相似文档数量
            citation_chunk_size: 引用块大小
            enable_debug: 是否启用调试模式（LlamaDebugHandler）
            similarity_threshold: 相似度阈值，低于此值启用推理模式
        """
        self.index_manager = index_manager
        self.similarity_top_k = similarity_top_k or config.SIMILARITY_TOP_K
        self.citation_chunk_size = citation_chunk_size
        self.enable_debug = enable_debug
        self.similarity_threshold = similarity_threshold or config.SIMILARITY_THRESHOLD
        
        # 配置DeepSeek LLM
        self.api_key = api_key or config.DEEPSEEK_API_KEY
        self.model = model or config.LLM_MODEL
        
        if not self.api_key:
            raise ValueError("未设置DEEPSEEK_API_KEY，请检查环境变量或配置文件")
        
        # 配置调试模式
        if self.enable_debug:
            print("🔍 启用调试模式（LlamaDebugHandler）")
            self.llama_debug = LlamaDebugHandler(print_trace_on_end=True)
            Settings.callback_manager = CallbackManager([self.llama_debug])
            logger.info("调试模式已启用")
        
        print(f"🤖 初始化DeepSeek LLM: {self.model}")
        # 使用官方 DeepSeek 集成
        self.llm = DeepSeek(
            api_key=self.api_key,
            model=self.model,
            temperature=0.5,  # 提高温度以增强推理能力
            max_tokens=4096,
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
    
    def query(self, question: str, collect_trace: bool = False) -> Tuple[str, List[dict], Optional[Dict[str, Any]]]:
        """执行查询并返回带引用的答案
        
        Args:
            question: 用户问题
            collect_trace: 是否收集详细的追踪信息（用于调试模式）
            
        Returns:
            (答案文本, 引用来源列表, 追踪信息字典)
            
        Note:
            追踪信息包含：检索时间、检索到的chunk、相似度分数、LLM调用时间等
        """
        trace_info = None
        
        try:
            print(f"\n💬 查询: {question}")
            
            if collect_trace:
                trace_info = {
                    "query": question,
                    "start_time": time.time(),
                    "retrieval": {},
                    "llm_generation": {}
                }
            
            # ===== 1. 执行检索 =====
            retrieval_start = time.time()
            
            # 执行查询
            response: Response = self.query_engine.query(question)
            
            retrieval_time = time.time() - retrieval_start
            
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
            
            # ===== 过滤低质量结果并评估检索质量 =====
            high_quality_sources = [s for s in sources if s.get('score', 0) >= self.similarity_threshold]
            max_score = max([s.get('score', 0) for s in sources]) if sources else 0
            
            if len(high_quality_sources) < len(sources):
                logger.info(f"过滤了 {len(sources) - len(high_quality_sources)} 个低质量结果（阈值: {self.similarity_threshold}）")
            
            if max_score < self.similarity_threshold:
                print(f"⚠️  检索质量较低（最高相似度: {max_score:.2f}），答案可能更多依赖模型推理")
                logger.warning(f"检索质量较低，最高相似度: {max_score:.2f}，阈值: {self.similarity_threshold}")
            elif len(high_quality_sources) >= 2:
                print(f"✅ 检索质量良好（高质量结果: {len(high_quality_sources)}个，最高相似度: {max_score:.2f}）")
            
            # ===== 2. 收集追踪信息 =====
            if collect_trace and trace_info:
                trace_info["retrieval"] = {
                    "time_cost": round(retrieval_time, 2),
                    "top_k": self.similarity_top_k,
                    "chunks_retrieved": len(sources),
                    "chunks": sources,
                    "avg_score": round(sum(s['score'] for s in sources if s['score']) / len(sources), 3) if sources else 0,
                }
                
                trace_info["llm_generation"] = {
                    "model": self.model,
                    "response_length": len(answer),
                }
                
                trace_info["total_time"] = round(time.time() - trace_info["start_time"], 2)
                
                # 记录详细日志
                logger.debug(f"查询追踪: {trace_info}")
            
            print(f"✅ 查询完成，找到 {len(sources)} 个引用来源")
            
            return answer, sources, trace_info
            
        except Exception as e:
            print(f"❌ 查询失败: {e}")
            logger.error(f"查询失败: {e}")
            raise
    
    async def stream_query(self, question: str):
        """异步流式查询（用于Web应用）
        
        Args:
            question: 用户问题
            
        Yields:
            dict: 包含type和data的字典
                - type='token': data为文本token
                - type='sources': data为引用来源列表
                - type='done': data为完整答案
        """
        import asyncio
        
        try:
            print(f"\n💬 流式查询: {question}")
            
            # 执行流式查询
            response_stream = self.query_engine.query(question)
            
            # 对于CitationQueryEngine，我们需要先获取完整响应，然后模拟流式输出
            # 因为引用需要在完整答案生成后才能提取
            answer = str(response_stream)
            
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
            
            # 模拟流式输出（逐字符）
            for char in answer:
                yield {'type': 'token', 'data': char}
                await asyncio.sleep(0.01)  # 打字机效果
            
            print(f"✅ 流式查询完成，找到 {len(sources)} 个引用来源")
            
            # 返回引用来源和完整答案
            yield {'type': 'sources', 'data': sources}
            yield {'type': 'done', 'data': answer}
            
        except Exception as e:
            print(f"❌ 流式查询失败: {e}")
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
        self.model = model or config.LLM_MODEL
        
        if not self.api_key:
            raise ValueError("未设置DEEPSEEK_API_KEY")
        
        # 使用官方 DeepSeek 集成
        self.llm = DeepSeek(
            api_key=self.api_key,
            model=self.model,
            temperature=0.5,  # 提高温度以增强推理能力
            max_tokens=4096,
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


class HybridQueryEngine:
    """混合查询引擎：本地知识库 + 维基百科实时查询"""
    
    def __init__(
        self,
        index_manager: IndexManager,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model: Optional[str] = None,
        similarity_top_k: Optional[int] = None,
        enable_wikipedia: bool = True,
        wikipedia_threshold: float = 0.6,
        wikipedia_max_results: int = 2,
    ):
        """初始化混合查询引擎
        
        Args:
            index_manager: 索引管理器
            api_key: DeepSeek API密钥
            api_base: API端点
            model: 模型名称
            similarity_top_k: 检索相似文档数量
            enable_wikipedia: 是否启用维基百科查询
            wikipedia_threshold: 触发维基百科的相关度阈值（0-1）
            wikipedia_max_results: 维基百科最多返回结果数
        """
        self.index_manager = index_manager
        self.enable_wikipedia = enable_wikipedia
        self.wikipedia_threshold = wikipedia_threshold
        self.wikipedia_max_results = wikipedia_max_results
        
        # 配置DeepSeek LLM
        self.api_key = api_key or config.DEEPSEEK_API_KEY
        self.model = model or config.LLM_MODEL
        self.similarity_top_k = similarity_top_k or config.SIMILARITY_TOP_K
        
        if not self.api_key:
            raise ValueError("未设置DEEPSEEK_API_KEY")
        
        print(f"🤖 初始化混合查询引擎（维基百科: {'启用' if enable_wikipedia else '禁用'}）")
        
        # 使用官方 DeepSeek 集成
        self.llm = DeepSeek(
            api_key=self.api_key,
            model=self.model,
            temperature=0.5,  # 提高温度以增强推理能力
            max_tokens=4096,
        )
        
        # 本地查询引擎
        self.local_engine = QueryEngine(
            index_manager,
            api_key=api_key,
            api_base=api_base,
            model=model,
            similarity_top_k=similarity_top_k,
        )
        
        # 维基百科reader（延迟导入）
        self.wikipedia_reader = None
        if self.enable_wikipedia:
            try:
                from llama_index.readers.wikipedia import WikipediaReader
                self.wikipedia_reader = WikipediaReader()
                print("📖 维基百科 Reader 已加载")
            except ImportError:
                print("⚠️  维基百科 Reader 未安装，将仅使用本地知识库")
                self.enable_wikipedia = False
        
        print("✅ 混合查询引擎初始化完成")
    
    def query(self, question: str) -> Tuple[str, List[dict], List[dict]]:
        """执行混合查询
        
        Args:
            question: 用户问题
            
        Returns:
            (答案文本, 本地来源列表, 维基百科来源列表)
        """
        try:
            print(f"\n💬 混合查询: {question}")
            
            # Step 1: 本地知识库检索
            print("🔍 正在查询本地知识库...")
            local_answer, local_sources, _ = self.local_engine.query(question)
            
            # Step 2: 判断是否需要维基百科补充
            wikipedia_sources = []
            if self._should_query_wikipedia(local_sources, question):
                print("🌐 触发维基百科补充查询...")
                
                # 提取关键词
                keywords = self._extract_keywords(question)
                print(f"   关键词: {keywords}")
                
                # 检测查询语言
                lang = self._detect_language(question)
                print(f"   语言: {'中文' if lang == 'zh' else '英文'}")
                
                # 查询维基百科
                wiki_docs = self._query_wikipedia(keywords, lang)
                
                if wiki_docs:
                    # 从维基百科文档中检索相关内容
                    wikipedia_sources = self._retrieve_from_wiki_docs(wiki_docs, question)
                    print(f"✅ 找到 {len(wikipedia_sources)} 个维基百科来源")
            else:
                print("ℹ️  本地结果充分，跳过维基百科查询")
            
            # Step 3: 合并结果生成最终答案
            if wikipedia_sources:
                final_answer = self._merge_answers(
                    question,
                    local_answer,
                    local_sources,
                    wikipedia_sources
                )
            else:
                final_answer = local_answer
            
            print(f"✅ 混合查询完成")
            print(f"   本地来源: {len(local_sources)} 个")
            print(f"   维基百科来源: {len(wikipedia_sources)} 个")
            
            return final_answer, local_sources, wikipedia_sources
            
        except Exception as e:
            print(f"❌ 混合查询失败: {e}")
            raise
    
    async def stream_query(self, question: str):
        """异步流式混合查询（用于Web应用）
        
        Args:
            question: 用户问题
            
        Yields:
            dict: 包含type和data的字典
                - type='status': data为状态日志消息
                - type='token': data为文本token
                - type='sources': data为{'local': [...], 'wikipedia': [...]}
                - type='done': data为完整答案
        """
        import asyncio
        
        try:
            print(f"\n💬 流式混合查询: {question}")
            
            # Step 1: 本地知识库检索
            yield {'type': 'status', 'data': '🔍 正在查询本地知识库...'}
            print("🔍 正在查询本地知识库...")
            local_answer, local_sources = self.local_engine.query(question)
            yield {'type': 'status', 'data': f'✅ 本地检索完成，找到 {len(local_sources)} 个来源'}
            
            # Step 2: 判断是否需要维基百科补充
            wikipedia_sources = []
            if self._should_query_wikipedia(local_sources, question):
                yield {'type': 'status', 'data': '🌐 正在查询维基百科补充...'}
                print("🌐 触发维基百科补充查询...")
                
                # 提取关键词
                keywords = self._extract_keywords(question)
                print(f"   关键词: {keywords}")
                yield {'type': 'status', 'data': f'🔑 关键词: {", ".join(keywords)}'}
                
                # 检测查询语言
                lang = self._detect_language(question)
                lang_text = '中文' if lang == 'zh' else '英文'
                print(f"   语言: {lang_text}")
                
                # 查询维基百科
                wiki_docs = self._query_wikipedia(keywords, lang)
                
                if wiki_docs:
                    # 从维基百科文档中检索相关内容
                    wikipedia_sources = self._retrieve_from_wiki_docs(wiki_docs, question)
                    print(f"✅ 找到 {len(wikipedia_sources)} 个维基百科来源")
                    yield {'type': 'status', 'data': f'✅ 维基百科检索完成，找到 {len(wikipedia_sources)} 个来源'}
                else:
                    yield {'type': 'status', 'data': '⚠️ 未找到维基百科补充内容'}
            else:
                print("ℹ️  本地结果充分，跳过维基百科查询")
                yield {'type': 'status', 'data': 'ℹ️  本地结果充分，跳过维基百科查询'}
            
            # Step 3: 合并结果生成最终答案
            yield {'type': 'status', 'data': '🤖 正在生成答案...'}
            
            if wikipedia_sources:
                final_answer = self._merge_answers(
                    question,
                    local_answer,
                    local_sources,
                    wikipedia_sources
                )
            else:
                final_answer = local_answer
            
            # Step 4: 流式输出最终答案（带打字机效果）
            for char in final_answer:
                yield {'type': 'token', 'data': char}
                await asyncio.sleep(0.01)  # 打字机效果
            
            print(f"✅ 流式混合查询完成")
            print(f"   本地来源: {len(local_sources)} 个")
            print(f"   维基百科来源: {len(wikipedia_sources)} 个")
            
            # 返回引用来源和完整答案
            yield {
                'type': 'sources', 
                'data': {
                    'local': local_sources,
                    'wikipedia': wikipedia_sources
                }
            }
            yield {'type': 'done', 'data': final_answer}
            
        except Exception as e:
            print(f"❌ 流式混合查询失败: {e}")
            yield {'type': 'status', 'data': f'❌ 查询失败: {str(e)}'}
            raise
    
    def _should_query_wikipedia(self, local_sources: List[dict], question: str) -> bool:
        """判断是否触发维基百科查询
        
        Args:
            local_sources: 本地检索结果
            question: 用户问题
            
        Returns:
            是否需要查询维基百科
        """
        if not self.enable_wikipedia or not self.wikipedia_reader:
            return False
        
        # 策略1: 本地结果为空
        if not local_sources:
            print("   触发原因: 本地结果为空")
            return True
        
        # 策略2: 本地结果相关度低
        if local_sources:
            max_score = max(s.get('score', 0) for s in local_sources)
            if max_score < self.wikipedia_threshold:
                print(f"   触发原因: 本地相关度低 ({max_score:.2f} < {self.wikipedia_threshold})")
                return True
        
        # 策略3: 用户显式请求维基百科
        keywords = ["维基百科", "wikipedia", "百科", "wiki"]
        if any(keyword in question.lower() for keyword in keywords):
            print("   触发原因: 用户显式请求")
            return True
        
        return False
    
    def _detect_language(self, text: str) -> str:
        """检测查询语言（简单规则）
        
        Args:
            text: 查询文本
            
        Returns:
            语言代码（zh/en）
        """
        import re
        # 检测中文字符
        if re.search(r'[\u4e00-\u9fff]', text):
            return "zh"
        return "en"
    
    def _extract_keywords(self, question: str) -> List[str]:
        """提取查询关键词（使用LLM）
        
        Args:
            question: 用户问题
            
        Returns:
            关键词列表
        """
        try:
            prompt = f"""从以下问题中提取1-3个最关键的主题词或实体名称，用于维基百科搜索。
要求：
1. 只提取名词或专有名词
2. 多个关键词用逗号分隔
3. 不要有多余说明，直接输出关键词

问题：{question}
关键词："""
            
            response = self.llm.complete(prompt)
            keywords_str = response.text.strip()
            
            # 清理并分割关键词
            keywords = [k.strip() for k in keywords_str.split(',')]
            keywords = [k for k in keywords if k]  # 移除空字符串
            
            # 最多返回3个关键词
            return keywords[:3]
            
        except Exception as e:
            print(f"⚠️  关键词提取失败: {e}")
            # 回退方案：简单分词（取最后几个词）
            words = question.split()
            return words[-2:] if len(words) >= 2 else words
    
    def _query_wikipedia(self, keywords: List[str], lang: str) -> List[LlamaDocument]:
        """查询维基百科
        
        Args:
            keywords: 关键词列表
            lang: 语言代码
            
        Returns:
            维基百科文档列表
        """
        if not keywords:
            return []
        
        try:
            from src.data_loader import load_documents_from_wikipedia
            
            # 加载维基百科页面（限制数量）
            docs = load_documents_from_wikipedia(
                pages=keywords[:self.wikipedia_max_results],
                lang=lang,
                auto_suggest=True,
                clean=True,
                show_progress=False
            )
            
            return docs
            
        except Exception as e:
            print(f"⚠️  维基百科查询失败: {e}")
            return []
    
    def _retrieve_from_wiki_docs(
        self,
        wiki_docs: List[LlamaDocument],
        question: str
    ) -> List[dict]:
        """从维基百科文档中检索相关内容
        
        Args:
            wiki_docs: 维基百科文档列表
            question: 用户问题
            
        Returns:
            相关内容列表（与 QueryEngine 返回格式一致）
        """
        if not wiki_docs:
            return []
        
        try:
            # 创建临时索引（不持久化）
            from llama_index.core import VectorStoreIndex
            
            # 使用已加载的embedding模型
            temp_index = VectorStoreIndex.from_documents(
                wiki_docs,
                show_progress=False
            )
            
            # 检索相关内容
            retriever = temp_index.as_retriever(
                similarity_top_k=min(self.wikipedia_max_results, len(wiki_docs))
            )
            nodes = retriever.retrieve(question)
            
            # 转换为统一格式
            sources = []
            for node in nodes:
                source = {
                    'text': node.node.text,
                    'score': node.score if hasattr(node, 'score') else None,
                    'metadata': node.node.metadata,
                }
                sources.append(source)
            
            return sources
            
        except Exception as e:
            print(f"⚠️  维基百科内容检索失败: {e}")
            # 如果索引失败，直接返回文档内容
            sources = []
            for doc in wiki_docs[:self.wikipedia_max_results]:
                source = {
                    'text': doc.text[:1000],  # 截取前1000字符
                    'score': 0.5,  # 默认分数
                    'metadata': doc.metadata,
                }
                sources.append(source)
            return sources
    
    def _merge_answers(
        self,
        question: str,
        local_answer: str,
        local_sources: List[dict],
        wikipedia_sources: List[dict]
    ) -> str:
        """合并本地和维基百科的答案
        
        Args:
            question: 用户问题
            local_answer: 本地答案
            local_sources: 本地来源
            wikipedia_sources: 维基百科来源
            
        Returns:
            合并后的答案
        """
        try:
            # 如果没有维基百科补充，直接返回本地答案
            if not wikipedia_sources:
                return local_answer
            
            # 构建包含维基百科信息的上下文
            wiki_context = "\n\n".join([
                f"【维基百科-{s['metadata'].get('title', '未知')}】\n{s['text'][:500]}"
                for s in wikipedia_sources[:2]  # 最多使用2个维基百科来源
            ])
            
            # 使用LLM重新生成综合答案
            prompt = f"""基于本地知识库和维基百科的信息，综合回答用户的问题。

用户问题：{question}

本地知识库的回答：
{local_answer}

维基百科补充信息：
{wiki_context}

请综合以上信息，给出完整、准确的回答。要求：
1. 优先使用本地知识库的专业内容
2. 用维基百科补充背景知识或扩展信息
3. 保持回答的连贯性和完整性
4. 不要提及"本地知识库"或"维基百科"这些术语

综合回答："""
            
            response = self.llm.complete(prompt)
            merged_answer = response.text.strip()
            
            return merged_answer
            
        except Exception as e:
            print(f"⚠️  答案合并失败，返回本地答案: {e}")
            return local_answer


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

