"""
RAG引擎处理模块 - 查询执行：查询执行和后处理器创建逻辑

主要功能：
- execute_query()：执行查询，提取答案、来源和推理链
- create_postprocessors()：创建后处理器链（相似度过滤+重排序）

执行流程：
1. 通知观察器查询开始
2. 执行查询并获取响应
3. 提取推理链、答案和引用来源
4. 格式化答案
5. 通知观察器查询结束
6. 返回查询结果

特性：
- 完整的观察器集成
- 追踪信息收集
- 后处理器链式组合
"""

import time
from typing import List, Optional, Tuple, Dict, Any

from llama_index.core.postprocessor import SimilarityPostprocessor

from src.infrastructure.config import config
from src.infrastructure.logger import get_logger
from src.business.rag_engine.formatting import ResponseFormatter
from src.business.rag_engine.reranking.factory import create_reranker
from src.business.rag_engine.utils.utils import extract_sources_from_response
from src.infrastructure.llms import extract_reasoning_content

logger = get_logger('rag_engine')


def execute_query(
    query_engine,
    formatter: ResponseFormatter,
    observer_manager,
    question: str,
    collect_trace: bool = False
) -> Tuple[str, List[dict], Optional[str], Optional[Dict[str, Any]]]:
    """执行查询
    
    Args:
        query_engine: 查询引擎实例
        formatter: 响应格式化器
        observer_manager: 观察器管理器
        question: 用户问题
        collect_trace: 是否收集追踪信息
        
    Returns:
        (答案文本, 引用来源列表, 推理链内容, 追踪信息)
    """
    trace_info = None
    
    # 通知观察器：查询开始
    trace_ids = observer_manager.on_query_start(question)
    
    try:
        logger.info(f"💬 查询: {question}")
        
        if collect_trace:
            trace_info = {
                "query": question,
                "start_time": time.time(),
                "observer_trace_ids": trace_ids,
            }
        
        # 执行查询
        retrieval_start = time.time()
        response = query_engine.query(question)
        retrieval_time = time.time() - retrieval_start
        
        # 提取推理链内容（如果存在）
        reasoning_content = extract_reasoning_content(response)
        
        # 提取答案
        answer = str(response)
        answer = formatter.format(answer, None)
        
        # 提取引用来源
        sources = extract_sources_from_response(response)
        
        # 追踪信息
        if collect_trace and trace_info:
            trace_info["retrieval_time"] = round(retrieval_time, 2)
            trace_info["chunks_retrieved"] = len(sources)
            trace_info["total_time"] = round(time.time() - trace_info["start_time"], 2)
            if reasoning_content:
                trace_info["has_reasoning"] = True
                trace_info["reasoning_length"] = len(reasoning_content)
        
        logger.info(f"✅ 查询完成，找到 {len(sources)} 个引用来源")
        if reasoning_content:
            logger.debug(f"🧠 推理链内容已提取（长度: {len(reasoning_content)} 字符）")
        
        # 通知观察器：查询结束
        observer_manager.on_query_end(
            query=question,
            answer=answer,
            sources=sources,
            trace_ids=trace_ids,
            retrieval_time=retrieval_time,
        )
        
        return answer, sources, reasoning_content, trace_info
        
    except Exception as e:
        logger.error(f"❌ 查询失败: {e}", exc_info=True)
        raise


def create_postprocessors(
    index_manager,
    similarity_cutoff: float,
    enable_rerank: bool,
    rerank_top_n: int,
    reranker_type: Optional[str] = None,
) -> List:
    """创建后处理器（链式组合）
    
    Args:
        index_manager: 索引管理器
        similarity_cutoff: 相似度阈值
        enable_rerank: 是否启用重排序
        rerank_top_n: 重排序Top-N
        reranker_type: 重排序器类型（可选，默认使用配置）
        
    Returns:
        后处理器列表
    """
    postprocessors = []
    
    # 1. 相似度过滤（总是启用）
    postprocessors.append(
        SimilarityPostprocessor(similarity_cutoff=similarity_cutoff)
    )
    logger.info(f"添加相似度过滤器: cutoff={similarity_cutoff}")
    
    # 2. 重排序（可选）
    if enable_rerank:
        try:
            # 使用工厂函数创建重排序器
            reranker = create_reranker(
                reranker_type=reranker_type,
                top_n=rerank_top_n,
            )
            
            if reranker:
                # 获取LlamaIndex兼容的Postprocessor
                llama_postprocessor = reranker.get_llama_index_postprocessor()
                if llama_postprocessor:
                    postprocessors.append(llama_postprocessor)
                    logger.info(
                        f"添加重排序模块: "
                        f"type={reranker.get_reranker_name()}, "
                        f"top_n={reranker.get_top_n()}"
                    )
                else:
                    logger.warning("重排序器未提供LlamaIndex Postprocessor，跳过")
            else:
                logger.info("重排序器类型为'none'，跳过重排序")
                
        except Exception as e:
            logger.warning(f"⚠️  重排序模块初始化失败: {e}")
    
    return postprocessors
