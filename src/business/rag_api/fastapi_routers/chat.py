"""
RAG API - FastAPI对话路由

极简设计：只提供两个核心接口
- 流式对话（自动创建/使用会话）
- 获取会话历史
"""

import asyncio
import json
import time
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from src.business.rag_api.fastapi_dependencies import get_rag_service
from src.business.rag_api.rag_service import RAGService
from src.business.rag_api.models import (
    ChatRequest,
    SessionHistoryResponse,
)
from src.infrastructure.logger import get_logger
from src.infrastructure.llms import create_deepseek_llm_for_query
from src.infrastructure.llms.reasoning import extract_reasoning_from_stream_chunk, extract_reasoning_content
from src.business.rag_engine.formatting.templates import CHAT_MARKDOWN_TEMPLATE
from src.business.rag_engine.retrieval.factory import create_retriever
from llama_index.core.llms import ChatMessage, MessageRole
from src.infrastructure.config import config

# 全局变量：日志记录器，用于记录对话路由相关的日志信息
logger = get_logger('rag_api_chat_router')

# 全局变量：FastAPI 路由器，定义对话相关的 API 路由
router = APIRouter(prefix="/chat", tags=["对话"])


def _retrieve_nodes_and_sources(
    query: str,  # 用户查询文本
    index_manager,  # 索引管理器，用于获取向量索引
    query_engine,  # 查询引擎，可能包含后处理器
) -> tuple[list, list]:
    """检索节点并转换为来源格式
    
    Args:
        query: 用户查询文本
        index_manager: 索引管理器实例，用于获取向量索引
        query_engine: 查询引擎实例，可能包含后处理器用于优化检索结果
    
    Returns:
        tuple: (nodes_with_scores, sources)
            - nodes_with_scores: 检索到的节点列表（带相似度分数）
            - sources: 转换后的来源信息列表，用于前端展示
    """
    nodes_with_scores = []  # 检索到的节点列表（带相似度分数）
    sources = []  # 转换后的来源信息列表，格式为字典列表
    
    if not index_manager:
        return nodes_with_scores, sources  # 无索引管理器，使用纯 LLM 模式
    
    try:
        index = index_manager.get_index()  # 从索引管理器获取向量索引
        retriever = create_retriever(  # 创建检索器实例
            index=index,
            retrieval_strategy=config.RETRIEVAL_STRATEGY,
            similarity_top_k=config.SIMILARITY_TOP_K
        )
        
        nodes_with_scores = retriever.retrieve(query)  # 执行检索
        
        # 应用后处理（优化、去重等）
        if hasattr(query_engine, 'postprocessors') and query_engine.postprocessors:
            for postprocessor in query_engine.postprocessors:
                nodes_with_scores = postprocessor.postprocess_nodes(
                    nodes_with_scores,
                    query_str=query
                )
        
        # 转换为引用来源格式
        for i, node_with_score in enumerate(nodes_with_scores, 1):
            node = node_with_score.node if hasattr(node_with_score, 'node') else node_with_score
            score = node_with_score.score if hasattr(node_with_score, 'score') else None
            
            source = {
                'index': i,  # 来源序号
                'text': node.text if hasattr(node, 'text') else str(node),  # 节点文本
                'score': score,  # 相似度分数
                'metadata': node.metadata if hasattr(node, 'metadata') else {},  # 元数据
            }
            sources.append(source)
        
        logger.info(f"检索到 {len(nodes_with_scores)} 个文档片段")
    except Exception as e:
        logger.warning(f"检索失败，使用纯 LLM 模式: {e}")
    
    return nodes_with_scores, sources


def _build_prompt(query: str, nodes_with_scores: list) -> str:
    """构建 prompt
    
    Args:
        query: 用户查询文本
        nodes_with_scores: 检索到的节点列表（带相似度分数）
    
    Returns:
        str: 构建完成的 prompt 文本，包含上下文和用户问题
    """
    if nodes_with_scores:
        context_parts = []  # 格式化后的上下文片段列表
        for i, node_with_score in enumerate(nodes_with_scores, 1):
            node = node_with_score.node if hasattr(node_with_score, 'node') else node_with_score
            text = node.text if hasattr(node, 'text') else str(node)
            context_parts.append(f"[{i}] {text}")
        context_str = "\n\n".join(context_parts)  # 用双换行符连接
    else:
        context_str = "（知识库中未找到相关信息）"
    
    prompt = CHAT_MARKDOWN_TEMPLATE.format(context_str=context_str)
    prompt += f"\n\n用户问题：{query}\n\n请用中文回答问题。"
    return prompt


def _extract_token_from_chunk(chunk, full_answer: str) -> str:
    """从 chunk 提取增量 token
    
    Args:
        chunk: LLM 返回的流式响应 chunk 对象
        full_answer: 当前已累积的完整答案文本，用于计算增量
    
    Returns:
        str: 提取到的增量 token 文本，如果没有则返回 None
    """
    # 优先使用 delta.content（增量，直接可用）
    if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'content') and chunk.delta.content:
        return str(chunk.delta.content)
    
    # 从 message.content 计算增量（message.content 是累加的）
    if hasattr(chunk, 'message') and hasattr(chunk.message, 'content') and chunk.message.content:
        current_content = str(chunk.message.content)  # 当前累积的完整内容
        if full_answer and current_content.startswith(full_answer):
            chunk_text = current_content[len(full_answer):]  # 计算增量部分
            return chunk_text if chunk_text else None
        else:
            return current_content  # 第一次或异常情况
    
    return None


def _format_answer(full_answer: str, sources: list, query_engine) -> str:
    """格式化最终答案
    
    Args:
        full_answer: 完整的答案文本（未格式化）
        sources: 引用来源列表
        query_engine: 查询引擎实例，可能包含格式化器
    
    Returns:
        str: 格式化后的答案文本
    """
    formatted_answer = full_answer  # 格式化后的答案，默认为原始答案
    if query_engine and hasattr(query_engine, 'formatter'):
        try:
            formatted_answer = query_engine.formatter.format(full_answer, sources)
            logger.debug("答案格式化完成")
        except Exception as e:
            logger.warning(f"格式化失败，使用原始答案: {e}")
            formatted_answer = full_answer
    return formatted_answer


async def _generate_stream(
    request: ChatRequest,  # 用户请求对象，包含消息和会话ID
    rag_service: RAGService,  # RAG 服务实例，提供索引管理和查询引擎
):
    """生成 SSE 流的主方法
    
    这是流式对话的核心方法，负责：
    1. 检索相关文档节点
    2. 构建 prompt
    3. 调用 LLM 进行流式生成
    4. 提取并 yield token
    5. 格式化答案并返回最终结果
    
    Args:
        request: 用户请求对象，包含消息内容和会话ID
        rag_service: RAG 服务实例，提供索引管理和查询引擎
    
    Yields:
        str: SSE 格式的数据流，包含 token、sources、reasoning、done 等事件
    """
    try:
        # Step 1: 获取必要的组件
        index_manager = rag_service.index_manager  # 索引管理器
        query_engine = rag_service.modular_query_engine  # 查询引擎
        
        # Step 2: 检索节点和来源
        nodes_with_scores, sources = _retrieve_nodes_and_sources(
            request.message,
            index_manager,
            query_engine
        )
        
        # Step 3: 构建 prompt
        prompt = _build_prompt(request.message, nodes_with_scores)
        
        # Step 4: 流式处理 LLM 响应
        llm = create_deepseek_llm_for_query()  # 创建 DeepSeek LLM 实例
        chat_message = ChatMessage(role=MessageRole.USER, content=prompt)
        messages = [chat_message]  # 消息列表
        
        full_answer = ""  # 累积的完整答案文本
        reasoning_content = ""  # 累积的推理链内容
        token_count = 0  # 已处理的 token 数量
        last_chunk = None  # 最后一个 chunk，用于提取最终推理链
        
        logger.debug("🚀 开始直接流式调用 DeepSeek API（绕过中间层）")
        
        for chunk in llm.stream_chat(messages):
            # 提取推理链内容（流式）
            chunk_reasoning = extract_reasoning_from_stream_chunk(chunk)
            if chunk_reasoning:
                reasoning_content += chunk_reasoning
            
            # 提取增量 token
            chunk_text = _extract_token_from_chunk(chunk, full_answer)
            
            if chunk_text:
                token_count += 1
                full_answer += chunk_text
                yield f"data: {json.dumps({'type': 'token', 'data': chunk_text}, ensure_ascii=False)}\n\n"
            
            last_chunk = chunk
        
        # 提取最终推理链（从最后一个 chunk）
        if last_chunk:
            final_reasoning = extract_reasoning_content(last_chunk)
            if final_reasoning:
                reasoning_content = final_reasoning
        
        logger.debug(f"✅ 直接流式生成完成，共 {token_count} 个 token")
        
        # Step 5: 格式化答案
        formatted_answer = _format_answer(full_answer, sources, query_engine)
        
        # Step 6-8: 返回引用来源、推理链和完成事件
        if sources:
            yield f"data: {json.dumps({'type': 'sources', 'data': sources}, ensure_ascii=False)}\n\n"
        if reasoning_content:
            yield f"data: {json.dumps({'type': 'reasoning', 'data': reasoning_content}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'data': {'answer': formatted_answer, 'sources': sources, 'reasoning_content': reasoning_content if reasoning_content else None}}, ensure_ascii=False)}\n\n"
    
    except Exception as e:
        logger.error("直接流式对话失败", error=str(e), exc_info=True)
        error_chunk = {"type": "error", "data": {"message": str(e)}}
        data = json.dumps(error_chunk, ensure_ascii=False)
        yield f"data: {data}\n\n"


@router.post("/stream")
async def stream_chat(
    request: ChatRequest,  # 用户请求对象，包含消息内容和会话ID
    rag_service: RAGService = Depends(get_rag_service),  # RAG 服务依赖注入
):
    """流式对话接口 - 直接流式管道版本
    
    绕过中间层，直接在 FastAPI 层建立与 DeepSeek 的流式管道：
    1. 检索节点（如果需要 RAG）
    2. 构建 prompt
    3. 直接调用 DeepSeek stream_chat
    4. 从 raw 响应中提取增量 token
    5. 立即 yield 给前端
    
    - 如果提供了 session_id，使用该会话
    - 如果没有提供 session_id，自动创建新会话
    - 流式返回答案，包含 token、sources 和 done 事件
    
    Args:
        request: 用户请求对象，包含消息内容和可选的会话ID
        rag_service: RAG 服务实例，通过依赖注入获取
    
    Returns:
        StreamingResponse: SSE 格式的流式响应
    """
    logger.info(
        "收到流式对话请求（直接流式管道）",
        message=request.message[:50] if len(request.message) > 50 else request.message,
        session_id=request.session_id
    )
    
    # 返回 SSE 格式的流式响应
    return StreamingResponse(
        _generate_stream(request, rag_service),  # 生成 SSE 流的异步生成器
        media_type="text/event-stream",  # SSE 媒体类型
        headers={
            "Cache-Control": "no-cache",  # 禁用缓存
            "Connection": "keep-alive",  # 保持连接
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
        }
    )


@router.get("/sessions/{session_id}/history", response_model=SessionHistoryResponse)
async def get_session_history(
    session_id: str,  # 会话ID，从 URL 路径参数获取
    rag_service: RAGService = Depends(get_rag_service),  # RAG 服务依赖注入
):
    """获取指定会话的历史记录
    
    Args:
        session_id: 会话ID，从 URL 路径参数获取
        rag_service: RAG 服务实例，通过依赖注入获取
    
    Returns:
        SessionHistoryResponse: 会话历史记录响应对象
    
    Raises:
        HTTPException: 
            - 404: 会话不存在
            - 500: 获取会话历史失败
    """
    logger.info("获取会话历史", session_id=session_id)
    try:
        return await asyncio.to_thread(rag_service.get_session_history, session_id)
    except FileNotFoundError as e:
        logger.warning("会话不存在", session_id=session_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SESSION_NOT_FOUND", "message": str(e)}
        )
    except Exception as e:
        logger.error("获取会话历史失败", session_id=session_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "HISTORY_FETCH_FAILED", "message": f"获取会话历史失败: {str(e)}"}
        )
