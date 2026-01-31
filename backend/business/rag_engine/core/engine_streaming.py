"""
RAG引擎流式查询模块：处理流式查询逻辑

主要功能：
- 流式查询执行
- 实时 token 输出
- 推理链提取
"""

import time
from typing import Dict, Any, Optional

from backend.infrastructure.logger import get_logger
from backend.business.rag_engine.formatting import ResponseFormatter
from backend.infrastructure.llms.reasoning import extract_reasoning_from_stream_chunk
from backend.infrastructure.llms import extract_reasoning_content
from backend.infrastructure.llms.message_builder import build_chat_messages

logger = get_logger('rag_engine')


async def execute_stream_query(
    llm,
    formatter: ResponseFormatter,
    query_processor,
    retriever,
    postprocessors,
    query_router,
    enable_auto_routing: bool,
    retrieval_strategy: str,
    similarity_top_k: int,
    final_query: str,
    understanding: Optional[Dict[str, Any]] = None
):
    """执行流式查询
    
    Args:
        llm: LLM实例
        formatter: 响应格式化器
        query_processor: 查询处理器
        retriever: 检索器
        postprocessors: 后处理器列表
        query_router: 查询路由器
        enable_auto_routing: 是否启用自动路由
        retrieval_strategy: 检索策略
        similarity_top_k: 相似度top_k
        final_query: 处理后的查询
        understanding: 查询理解结果（可选）
        
    Yields:
        dict: 流式响应字典
    """
    # Step 2: 获取检索器和检索节点
    actual_retriever = None
    strategy_info = ""
    
    if enable_auto_routing and query_router:
        # 自动路由模式
        if understanding:
            actual_retriever, routing_decision = query_router.route_with_understanding(
                final_query,
                understanding=understanding,
                top_k=similarity_top_k
            )
        else:
            actual_retriever, routing_decision = query_router.route(
                final_query,
                top_k=similarity_top_k
            )
        strategy_info = f"策略={routing_decision}, 原因=自动路由模式"
    else:
        # 固定模式：使用初始化时创建的检索器
        actual_retriever = retriever
        strategy_info = f"策略={retrieval_strategy}, 原因=固定检索模式"
    
    logger.info("使用检索策略（直接流式）", strategy_info=strategy_info)
    
    # Step 3: 检索节点
    nodes_with_scores = []
    sources = []
    full_answer = ""
    reasoning_content = ""
    
    try:
        if actual_retriever:
            # 执行检索
            nodes_with_scores = actual_retriever.retrieve(final_query)
            
            # 应用后处理
            if postprocessors:
                for postprocessor in postprocessors:
                    nodes_with_scores = postprocessor.postprocess_nodes(
                        nodes_with_scores,
                        query_str=final_query
                    )
            
            # 转换为引用来源格式
            for i, node_with_score in enumerate(nodes_with_scores, 1):
                node = node_with_score.node if hasattr(node_with_score, 'node') else node_with_score
                score = node_with_score.score if hasattr(node_with_score, 'score') else None
                
                source = {
                    'index': i,
                    'text': node.text if hasattr(node, 'text') else str(node),
                    'score': score,
                    'metadata': node.metadata if hasattr(node, 'metadata') else {},
                }
                sources.append(source)
            
            logger.info(f"检索到 {len(nodes_with_scores)} 个文档片段")
        
        # Step 4: 构建 prompt
        from backend.business.rag_engine.formatting.templates import get_template
        
        # 构建上下文字符串
        context_str = ""
        if nodes_with_scores:
            context_parts = []
            for i, node_with_score in enumerate(nodes_with_scores, 1):
                node = node_with_score.node if hasattr(node_with_score, 'node') else node_with_score
                text = node.text if hasattr(node, 'text') else str(node)
                context_parts.append(f"[{i}] {text}")
            context_str = "\n\n".join(context_parts)
        else:
            context_str = "（知识库中未找到相关信息）"
        
        # 构建系统 prompt 和用户查询
        system_prompt = get_template('chat').format(context_str=context_str)
        user_query = f"用户问题：{final_query}\n\n请用中文回答问题。"
        
        # Step 5: 根据模型类型组装消息（通用模型：system+user，推理模型：合并到user）
        messages = build_chat_messages(system_prompt, user_query)
        
        last_token_time = time.time()
        token_count = 0
        last_chunk = None
        miss_log_count = 0
        
        logger.debug("🚀 开始直接流式调用 DeepSeek API")
        
        # 直接调用 DeepSeek 的 stream_chat（绕过 LlamaIndex 缓冲）
        for chunk in llm.stream_chat(messages):
            # 提取推理链内容（流式）
            chunk_reasoning = extract_reasoning_from_stream_chunk(chunk)
            if chunk_reasoning:
                reasoning_content += chunk_reasoning
            
            # 提取 token 内容（增量）
            chunk_text = ""
            
            # 调试：记录 chunk 的结构
            if token_count == 0:
                logger.debug(f"🔍 Chunk 结构检查: hasattr(chunk, 'delta')={hasattr(chunk, 'delta')}, hasattr(chunk, 'message')={hasattr(chunk, 'message')}")
                if hasattr(chunk, 'delta'):
                    delta = chunk.delta
                    logger.debug(f"🔍 Delta 结构: {dir(delta)}")
                    if hasattr(delta, 'content'):
                        logger.debug(f"🔍 Delta.content 类型: {type(delta.content)}, 值: {repr(delta.content)}")
                if hasattr(chunk, 'message'):
                    message = chunk.message
                    logger.debug(f"🔍 Message 结构: {dir(message)}")
                    if hasattr(message, 'content'):
                        logger.debug(f"🔍 Message.content 类型: {type(message.content)}, 值长度: {len(str(message.content)) if message.content else 0}")
            
            # 方法1：优先使用 delta.content（增量）
            if hasattr(chunk, 'delta'):
                delta = chunk.delta
                if isinstance(delta, str):
                    if delta:
                        chunk_text = delta
                elif isinstance(delta, dict):
                    delta_content = delta.get('content')
                    if delta_content:
                        chunk_text = str(delta_content)
                elif hasattr(delta, 'content') and delta.content:
                    chunk_text = str(delta.content)
                    if len(chunk_text) > 50:
                        logger.warning(f"⚠️ Delta.content 长度异常: {len(chunk_text)} 字符，可能是累加的！内容: {chunk_text[:50]}...")
                elif hasattr(delta, 'text') and delta.text:
                    chunk_text = str(delta.text)
            
            # 方法2：如果 delta 没有命中，尝试从 message.content 计算增量
            if not chunk_text and hasattr(chunk, 'message'):
                message = chunk.message
                current_content = None
                if isinstance(message, str):
                    current_content = message
                elif hasattr(message, 'content') and message.content:
                    current_content = message.content
                
                if current_content:
                    current_content = str(current_content)
                    if full_answer and current_content.startswith(full_answer):
                        chunk_text = current_content[len(full_answer):]
                        if not chunk_text:
                            continue
                    elif not full_answer:
                        chunk_text = current_content
                    else:
                        logger.warning(f"⚠️ Message.content 格式异常: 当前长度={len(current_content)}, 之前长度={len(full_answer)}")
                        if len(current_content) > len(full_answer):
                            chunk_text = current_content[len(full_answer):]
                        else:
                            chunk_text = current_content
                            full_answer = ""
            
            # 方法3：检查 raw 响应（OpenAI 格式）
            if not chunk_text and hasattr(chunk, 'raw'):
                raw = chunk.raw
                if isinstance(raw, dict):
                    choices = raw.get('choices', [])
                    if choices and len(choices) > 0:
                        choice = choices[0]
                        delta = choice.get('delta', {})
                        if isinstance(delta, dict):
                            chunk_text = delta.get('content', '')
                            if chunk_text:
                                chunk_text = str(chunk_text)
            
            if not chunk_text and miss_log_count < 3:
                delta_obj = getattr(chunk, 'delta', None)
                message_obj = getattr(chunk, 'message', None)
                raw_obj = getattr(chunk, 'raw', None)
                msg_content = None
                if isinstance(message_obj, str):
                    msg_content = message_obj
                elif hasattr(message_obj, 'content'):
                    msg_content = message_obj.content
                logger.debug(
                    "stream_chunk_no_token",
                    delta_type=type(delta_obj).__name__,
                    delta_len=len(str(delta_obj)) if delta_obj else 0,
                    message_type=type(message_obj).__name__,
                    message_len=len(str(msg_content)) if msg_content else 0,
                    raw_type=type(raw_obj).__name__,
                    raw_keys=list(raw_obj.keys()) if isinstance(raw_obj, dict) else None,
                )
                miss_log_count += 1
            
            if chunk_text:
                token_count += 1
                current_time = time.time()
                time_since_last = current_time - last_token_time
                last_token_time = current_time
                
                if token_count <= 5 or time_since_last > 0.1:
                    logger.debug(f"🔤 Token #{token_count} '{chunk_text[:20]}...' 到达，间隔: {time_since_last*1000:.1f}ms")
                
                full_answer += chunk_text
                yield {'type': 'token', 'data': chunk_text}
            
            last_chunk = chunk
        
        logger.debug(f"✅ 流式生成完成，共 {token_count} 个 token")
        
        # Step 6: 格式化答案
        full_answer = formatter.format(full_answer, None)
        
        # Step 7: 提取最终推理链（从最后一个 chunk）
        if last_chunk:
            final_reasoning = extract_reasoning_content(last_chunk)
            if final_reasoning:
                reasoning_content = final_reasoning
        
        # 返回引用来源
        if sources:
            yield {'type': 'sources', 'data': sources}
        
        # 返回推理链（答案完成后，非流式）
        if reasoning_content:
            yield {'type': 'reasoning', 'data': reasoning_content}
        
        # 返回完成事件
        yield {
            'type': 'done',
            'data': {
                'answer': full_answer,
                'sources': sources,
                'reasoning_content': reasoning_content if reasoning_content else None,
            }
        }
        
    except Exception as e:
        logger.error(f"流式查询失败: {e}", exc_info=True)
        yield {
            'type': 'error',
            'data': {'message': str(e)}
        }
        raise
