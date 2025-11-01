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

from src.config import config, get_gpu_device, is_gpu_available
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
            # 获取当前设备信息
            device = get_gpu_device()
            device_mode = "GPU加速" if device.startswith("cuda") else "CPU模式"
            
            print(f"\n💬 查询: {question}")
            logger.debug(f"查询设备: {device} ({device_mode})")
            
            if collect_trace:
                trace_info = {
                    "query": question,
                    "start_time": time.time(),
                    "retrieval": {},
                    "llm_generation": {}
                }
            
            # ===== 1. 执行检索 =====
            retrieval_start = time.time()
            
            # 获取 Collection 统计信息
            stats = self.index_manager.get_stats()
            collection_total_docs = stats.get('document_count', 0)
            collection_name = stats.get('collection_name', 'unknown')
            
            # 检查是否有错误信息
            if 'error' in stats:
                error_info = stats.get('error', '未知错误')
                logger.warning(f"⚠️  获取Collection统计信息时出现问题: {error_info}")
                print(f"⚠️  获取Collection统计信息时出现问题: {error_info}")
                print(f"   这可能是因为collection未正确初始化或访问失败")
            
            logger.info(f"📊 Collection 信息: {collection_name}, 总文档数: {collection_total_docs}")
            print(f"📊 Collection: {collection_name}, 总文档数: {collection_total_docs}")
            
            # 如果文档数为0，输出警告
            if collection_total_docs == 0:
                logger.warning(f"⚠️  Collection '{collection_name}' 的文档数为0，可能是空collection或初始化问题")
                print(f"⚠️  注意: Collection '{collection_name}' 的文档数为0")
                print(f"   如果这不符合预期，请检查:")
                print(f"   1. 索引是否已正确构建")
                print(f"   2. Collection名称是否正确")
                print(f"   3. 向量存储路径是否正确")
            
            # 执行查询
            response: Response = self.query_engine.query(question)
            
            retrieval_time = time.time() - retrieval_start
            
            # 提取答案
            answer = str(response)
            
            # 提取引用来源
            sources = []
            if hasattr(response, 'source_nodes') and response.source_nodes:
                logger.info(f"🔍 检索到 {len(response.source_nodes)} 个文档片段")
                print(f"🔍 检索到 {len(response.source_nodes)} 个文档片段:")
                
                for i, node in enumerate(response.source_nodes, 1):
                    # 提取元数据中的文档信息
                    try:
                        metadata = node.node.metadata if hasattr(node, 'node') and hasattr(node.node, 'metadata') else {}
                        if not isinstance(metadata, dict):
                            metadata = {}
                    except Exception:
                        metadata = {}
                    
                    # 尝试多种方式获取文件路径
                    file_path = (
                        metadata.get('file_path') or 
                        metadata.get('file_name') or 
                        metadata.get('source') or 
                        metadata.get('url') or 
                        '未知来源'
                    )
                    file_name = file_path.split('/')[-1] if '/' in file_path else file_path.split('\\')[-1]
                    page_label = metadata.get('page_label', metadata.get('page', ''))
                    doc_id = metadata.get('doc_id', metadata.get('document_id', metadata.get('id', '')))
                    
                    score = node.score if hasattr(node, 'score') else None
                    node_text = node.node.text if hasattr(node, 'node') and hasattr(node.node, 'text') else ''
                    text_preview = node_text[:200] + '...' if len(node_text) > 200 else node_text
                    
                    source = {
                        'index': i,
                        'text': node_text,
                        'score': score,
                        'metadata': metadata,
                    }
                    sources.append(source)
                    
                    # 详细日志输出
                    score_str = f"{score:.4f}" if score is not None else "N/A"
                    logger.info(
                        f"  [{i}] 文档片段 #{i}:\n"
                        f"    - 文件名: {file_name}\n"
                        f"    - 文件路径: {file_path}\n"
                        f"    - 相似度分数: {score_str}\n"
                        f"    - 文档ID: {doc_id}\n"
                        f"    - 页码: {page_label}\n"
                        f"    - 内容预览: {text_preview}\n"
                        f"    - 完整元数据: {metadata}"
                    )
                    print(f"  [{i}] {file_name} (分数: {score_str})")
                    if score is not None:
                        print(f"      路径: {file_path}")
                        print(f"      内容: {text_preview}")
                
                # 汇总信息
                logger.info(
                    f"📋 检索结果汇总:\n"
                    f"  - Collection: {collection_name}\n"
                    f"  - Collection 总文档数: {collection_total_docs}\n"
                    f"  - 检索到的片段数: {len(sources)}\n"
                    f"  - 有分数的片段数: {len([s for s in sources if s.get('score') is not None])}\n"
                    f"  - 无分数的片段数: {len([s for s in sources if s.get('score') is None])}"
                )
            
            # ===== 过滤低质量结果并评估检索质量 =====
            numeric_scores = [s.get('score') for s in sources if s.get('score') is not None]
            max_score = max(numeric_scores) if numeric_scores else None
            high_quality_sources = [
                s for s in sources
                if (s.get('score') is not None) and (s.get('score') >= self.similarity_threshold)
            ]
            
            # 仅当存在数值分数时，才基于阈值进行质量判断
            if max_score is not None:
                if len(high_quality_sources) < len(sources):
                    logger.info(
                        f"过滤了 {len(sources) - len(high_quality_sources)} 个低质量结果（阈值: {self.similarity_threshold}）"
                    )
                if max_score < self.similarity_threshold:
                    print(
                        f"⚠️  检索质量较低（最高相似度: {max_score:.2f}），答案可能更多依赖模型推理"
                    )
                    logger.warning(
                        f"检索质量较低，最高相似度: {max_score:.2f}，阈值: {self.similarity_threshold}"
                    )
                elif len(high_quality_sources) >= 2:
                    print(
                        f"✅ 检索质量良好（高质量结果: {len(high_quality_sources)}个，最高相似度: {max_score:.2f}）"
                    )
            else:
                # 分数缺失（例如 CitationQueryEngine 未返回 score），打印提示但不判定为低相关
                logger.info(
                    "检索评分缺失：所有来源的score为None（chunks=%s），跳过低相关判定，仅依据其他条件兜底",
                    len(sources),
                )
            
            # ===== 兜底策略（方案A）：输出守护 + 纯LLM定义类回答 =====
            # 计算更多统计信息，便于日志观测
            scores_list = [s['score'] for s in sources if s.get('score') is not None]
            avg_score = sum(scores_list) / len(scores_list) if scores_list else 0.0
            min_score = min(scores_list) if scores_list else 0.0
            max_score_logged = (max(scores_list) if scores_list else None)
            scores_none_count = len(sources) - len(scores_list)
            
            logger.debug(
                "检索统计: top_k=%s, chunks=%s, numeric=%s, none=%s, min=%s, avg=%s, max=%s, threshold=%.3f",
                self.similarity_top_k,
                len(sources),
                len(scores_list),
                scores_none_count,
                (f"{min_score:.3f}" if scores_list else "-"),
                (f"{avg_score:.3f}" if scores_list else "-"),
                (f"{max_score_logged:.3f}" if scores_list else "-"),
                self.similarity_threshold,
            )
            
            # 判定是否需要兜底
            fallback_reason = None
            if not sources:
                fallback_reason = "no_sources"
            elif (max_score_logged is not None) and (max_score_logged < self.similarity_threshold):
                fallback_reason = f"low_similarity({max_score_logged:.2f}<{self.similarity_threshold})"
            elif not answer or not answer.strip():
                fallback_reason = "empty_answer"
            
            if fallback_reason:
                print(f"🛟  触发兜底生成（原因: {fallback_reason}）")
                logger.info(
                    "触发兜底生成: reason=%s, chunks=%s, min=%.3f, avg=%.3f, max=%.3f, threshold=%.3f",
                    fallback_reason,
                    len(sources),
                    min_score,
                    avg_score,
                    max_score_logged if max_score_logged is not None else 0.0,
                    self.similarity_threshold,
                )
                
                # 纯LLM定义类回答提示词（中文输出，适配学习用途，明确说明为通用推理）
                fallback_prompt = (
                    "你是一位系统科学领域的资深专家。当前未检索到足够高相关的知识库内容，"
                    "请基于通用学术知识与常见教材，回答用户问题，给出清晰、结构化、可自洽的解释。\n\n"
                    "要求：\n"
                    "1) 先给出简明定义/核心思想，再给出关键要点条目；\n"
                    "2) 保持严谨、中立，不捏造具体引用；\n"
                    "3) 必须用中文回答；\n"
                    "4) 末尾增加一行提示：‘注：未检索到足够高相关资料，本回答基于通用知识推理，可能不含引用。’\n\n"
                    f"用户问题：{question}\n"
                    "回答："
                )
                try:
                    llm_start = time.time()
                    llm_resp = self.llm.complete(fallback_prompt)
                    llm_time = time.time() - llm_start
                    new_answer = (llm_resp.text or "").strip()
                    if new_answer:
                        answer = new_answer
                    else:
                        # 双重兜底：给出最小可用占位文本
                        answer = (
                            "抱歉，未检索到与该问题高度相关的资料。基于一般知识：\n"
                            "- 该问题属于通识类主题，建议进一步细化范围；\n"
                            "- 如需权威来源，可提供更具体的关键词以便检索。\n\n"
                            "注：未检索到足够高相关资料，本回答基于通用知识推理，可能不含引用。"
                        )
                    logger.info("兜底生成完成: length=%s, llm_time=%.2fs", len(answer), llm_time)
                except Exception as fe:
                    logger.error("兜底生成失败: %s", fe)
                    # 仍保证非空输出
                    answer = (
                        "抱歉，当前无法生成高质量答案。\n"
                        "- 建议调整提问方式或补充上下文；\n"
                        "- 稍后可重试以获取更稳定结果。\n\n"
                        "注：未检索到足够高相关资料，本回答基于通用知识推理，可能不含引用。"
                    )
            
            # ===== 2. 收集追踪信息 =====
            if collect_trace and trace_info:
                # 使用前面已计算的统计数据（若还未计算，做安全回退）
                _scores = [s['score'] for s in sources if s.get('score') is not None]
                _avg = sum(_scores) / len(_scores) if _scores else 0.0
                _min = min(_scores) if _scores else 0.0
                _max = max(_scores) if _scores else 0.0
                _hq = len([s for s in sources if (s.get('score') is not None) and (s.get('score') >= self.similarity_threshold)])
                _none_count = len(sources) - len(_scores)
                
                trace_info["retrieval"] = {
                    "time_cost": round(retrieval_time, 2),
                    "top_k": self.similarity_top_k,
                    "chunks_retrieved": len(sources),
                    "chunks": sources,
                    "avg_score": round(_avg, 3),
                    "min_score": round(_min, 3),
                    "max_score": round(_max, 3),
                    "threshold": self.similarity_threshold,
                    "high_quality_count": _hq,
                    "numeric_scores_count": len(_scores),
                    "scores_none_count": _none_count,
                }
                
                # 标注是否触发兜底
                trace_info["llm_generation"] = {
                    "model": self.model,
                    "response_length": len(answer),
                    "fallback_used": bool('fallback_reason' in locals() and fallback_reason),
                    "fallback_reason": fallback_reason if 'fallback_reason' in locals() else None,
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
        
        # 完整显示文本内容，不截断
        formatted += f"\n   {source['text']}"
    
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

