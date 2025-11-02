"""
查询引擎兜底处理模块
处理低相似度或无结果的情况
"""

import time
from typing import List, Tuple, Optional

from src.logger import setup_logger

logger = setup_logger('query_engine')


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

