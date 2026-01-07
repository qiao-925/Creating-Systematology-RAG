"""
RAG引擎工具模块 - 工具函数集合：提供格式化、兜底处理、追踪信息收集等辅助功能

主要功能：
- format_sources()：格式化引用来源为可读文本
- handle_fallback()：处理兜底逻辑，当相似度低于阈值或无结果时使用LLM直接回答
- collect_trace_info()：收集查询过程的详细追踪信息
- extract_sources_from_response()：从响应对象中提取引用来源

特性：
- 友好的引用来源格式
- 智能兜底机制
- 详细的追踪信息收集
- 性能统计
"""

import time
from typing import List, Tuple, Optional, Dict, Any

from backend.infrastructure.logger import get_logger

logger = get_logger('rag_engine')


def extract_sources_from_response(response) -> List[dict]:
    """从响应对象中提取引用来源
    
    Args:
        response: 查询响应对象（LlamaIndex Response）
        
    Returns:
        引用来源列表
    """
    sources = []
    if hasattr(response, 'source_nodes') and response.source_nodes:
        logger.info(f"🔍 检索到 {len(response.source_nodes)} 个文档片段")
        
        for i, node in enumerate(response.source_nodes, 1):
            try:
                # 提取元数据
                metadata = {}
                if hasattr(node, 'node') and hasattr(node.node, 'metadata'):
                    metadata_raw = node.node.metadata
                    if isinstance(metadata_raw, dict):
                        metadata = metadata_raw
                
                # 提取文本
                text = ""
                if hasattr(node, 'node'):
                    text = node.node.text if hasattr(node.node, 'text') else str(node)
                else:
                    text = str(node)
                
                # 提取分数
                score = node.score if hasattr(node, 'score') else None
                
                source = {
                    'index': i,
                    'text': text,
                    'score': score,
                    'metadata': metadata,
                }
                sources.append(source)
                
                # 打印调试信息
                score_str = f" (相似度: {score:.3f})" if score is not None else ""
                title = metadata.get('title') or metadata.get('file_name') or metadata.get('file_path', '未知').split('/')[-1] if metadata.get('file_path') else 'Unknown'
                logger.debug(f"  [{i}] {title}{score_str}")
                
            except Exception as e:
                logger.warning(f"提取来源 {i} 失败: {e}")
                continue
    
    return sources


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
        
        # 完整显示文本内容
        formatted += f"\n   {source['text']}"
    
    return formatted




def handle_fallback(
    answer: str,
    sources: List[dict],
    question: str,
    llm,
    similarity_threshold: float
) -> Tuple[str, Optional[str]]:
    """处理兜底逻辑
    
    Args:
        answer: 原始答案
        sources: 引用来源列表
        question: 用户问题
        llm: LLM实例
        similarity_threshold: 相似度阈值
        
    Returns:
        (处理后的答案, 兜底原因)
    """
    # 计算统计信息
    scores_list = [s['score'] for s in sources if s.get('score') is not None]
    scores_none_count = len(sources) - len(scores_list)
    
    min_score = min(scores_list) if scores_list else None
    avg_score = sum(scores_list) / len(scores_list) if scores_list else None
    max_score_logged = max(scores_list) if scores_list else None
    
    # 打印统计信息
    logger.info(f"📊 检索统计:")
    logger.info(f"   检索到 {len(sources)} 个chunk")
    logger.info(f"   相似度分数: {len(scores_list)} 个有效, {scores_none_count} 个为空")
    if scores_list:
        logger.info(f"   范围: {min_score:.3f} ~ {max_score_logged:.3f}, 平均: {avg_score:.3f}")
    logger.info(f"   阈值: {similarity_threshold}")
    
    # 判定是否需要兜底
    fallback_reason = None
    if not sources:
        fallback_reason = "no_sources"
    elif (max_score_logged is not None) and (max_score_logged < similarity_threshold):
        fallback_reason = f"low_similarity({max_score_logged:.2f}<{similarity_threshold})"
    elif not answer or not answer.strip():
        fallback_reason = "empty_answer"
    
    if fallback_reason:
        logger.info(f"🛟  触发兜底生成（原因: {fallback_reason}）")
        
        # 纯LLM定义类回答提示词
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
            llm_resp = llm.complete(fallback_prompt)
            llm_time = time.time() - llm_start
            new_answer = (llm_resp.text or "").strip()
            if new_answer:
                answer = new_answer
            else:
                answer = (
                    "抱歉，未检索到与该问题高度相关的资料。基于一般知识：\n"
                    "- 该问题属于通识类主题，建议进一步细化范围；\n"
                    "- 如需权威来源，可提供更具体的关键词以便检索。\n\n"
                    "注：未检索到足够高相关资料，本回答基于通用知识推理，可能不含引用。"
                )
            logger.info(f"兜底生成完成: length={len(answer)}, llm_time={llm_time:.2f}s")
        except Exception as fe:
            logger.error(f"兜底生成失败: {fe}")
            answer = (
                "抱歉，当前无法生成高质量答案。\n"
                "- 建议调整提问方式或补充上下文；\n"
                "- 稍后可重试以获取更稳定结果。\n\n"
                "注：未检索到足够高相关资料，本回答基于通用知识推理，可能不含引用。"
            )
    
    return answer, fallback_reason


def collect_trace_info(
    trace_info: Dict[str, Any],
    retrieval_time: float,
    sources: List[dict],
    similarity_top_k: int,
    similarity_threshold: float,
    model: str,
    answer: str,
    fallback_reason: Optional[str]
) -> Dict[str, Any]:
    """收集追踪信息
    
    Args:
        trace_info: 追踪信息字典
        retrieval_time: 检索耗时
        sources: 引用来源列表
        similarity_top_k: Top K值
        similarity_threshold: 相似度阈值
        model: 模型名称
        answer: 答案文本
        fallback_reason: 兜底原因
        
    Returns:
        完整的追踪信息字典
    """
    # 使用前面已计算的统计数据
    _scores = [s['score'] for s in sources if s.get('score') is not None]
    _avg = sum(_scores) / len(_scores) if _scores else 0.0
    _min = min(_scores) if _scores else 0.0
    _max = max(_scores) if _scores else 0.0
    _hq = len([s for s in sources if (s.get('score') is not None) and (s.get('score') >= similarity_threshold)])
    _none_count = len(sources) - len(_scores)
    
    trace_info["retrieval"] = {
        "time_cost": round(retrieval_time, 2),
        "top_k": similarity_top_k,
        "chunks_retrieved": len(sources),
        "chunks": sources,
        "avg_score": round(_avg, 3),
        "min_score": round(_min, 3),
        "max_score": round(_max, 3),
        "threshold": similarity_threshold,
        "high_quality_count": _hq,
        "numeric_scores_count": len(_scores),
        "scores_none_count": _none_count,
    }
    
    trace_info["llm_generation"] = {
        "model": model,
        "response_length": len(answer),
        "fallback_used": bool(fallback_reason),
        "fallback_reason": fallback_reason,
    }
    
    trace_info["total_time"] = round(time.time() - trace_info["start_time"], 2)
    
    return trace_info
