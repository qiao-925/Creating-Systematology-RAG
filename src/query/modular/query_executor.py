"""
模块化查询引擎 - 查询执行模块
查询执行逻辑
"""

import time
from typing import List, Optional, Tuple, Dict, Any

from src.logger import setup_logger
from src.response_formatter import ResponseFormatter
from src.llms import extract_reasoning_content

logger = setup_logger('modular_query_engine')


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
        sources = []
        if hasattr(response, 'source_nodes') and response.source_nodes:
            logger.info(f"🔍 检索到 {len(response.source_nodes)} 个文档片段")
            
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
                
                score_str = f"{score:.4f}" if score is not None else "N/A"
                file_name = metadata.get('file_name', metadata.get('file_path', '未知').split('/')[-1])
                logger.debug(f"  [{i}] {file_name} (分数: {score_str})")
        
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

