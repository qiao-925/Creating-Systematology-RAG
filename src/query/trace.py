"""
查询引擎追踪信息收集模块
收集查询过程的详细追踪信息
"""

from typing import Dict, Any, List, Optional


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
    import time
    
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

