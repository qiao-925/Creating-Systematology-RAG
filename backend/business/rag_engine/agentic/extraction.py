"""
结果提取模块：从 Agent 返回结果提取信息

主要功能：
- 从 Agent 响应中提取 sources
- 从 Agent 响应中提取 reasoning
"""

from typing import List, Optional, Dict, Any

from backend.infrastructure.logger import get_logger

logger = get_logger('rag_engine.agentic.extraction')


def extract_sources_from_agent(response: Any, agent: Optional[Any] = None) -> List[dict]:
    """从 Agent 响应中提取 sources
    
    尝试从多个可能的属性中提取 sources，包括：
    - response.source_nodes
    - response.sources
    - response.metadata 中的 sources
    - Agent 的工具调用历史（如果提供 agent 实例）
    
    Args:
        response: Agent 返回的响应对象
        agent: Agent 实例（可选，用于访问工具调用历史）
        
    Returns:
        引用来源列表
    """
    sources = []
    
    # 记录响应对象类型和属性，便于调试
    response_type = type(response).__name__
    response_attrs = [attr for attr in dir(response) if not attr.startswith('_')]
    logger.debug(
        "开始提取 sources",
        response_type=response_type,
        response_attrs_count=len(response_attrs),
        has_agent=agent is not None
    )
    
    # 方式1：尝试从 response.source_nodes 提取
    if hasattr(response, 'source_nodes') and response.source_nodes:
        logger.debug("从 response.source_nodes 提取 sources")
        try:
            for i, node in enumerate(response.source_nodes, 1):
                source = {
                    'index': i,
                    'text': node.text if hasattr(node, 'text') else str(node),
                    'score': node.score if hasattr(node, 'score') else None,
                    'metadata': node.metadata if hasattr(node, 'metadata') else {},
                }
                sources.append(source)
            logger.debug("成功从 source_nodes 提取 sources", count=len(sources))
            return sources
        except Exception as e:
            logger.warning("从 source_nodes 提取 sources 时出错", error=str(e))
    
    # 方式2：尝试从 response.sources 提取
    if hasattr(response, 'sources') and response.sources:
        logger.debug("从 response.sources 提取 sources")
        try:
            if isinstance(response.sources, list):
                sources = response.sources
            else:
                sources = [response.sources]
            logger.debug("成功从 sources 属性提取", count=len(sources))
            return sources
        except Exception as e:
            logger.warning("从 sources 属性提取时出错", error=str(e))
    
    # 方式3：尝试从 response.metadata 中提取
    if hasattr(response, 'metadata') and isinstance(response.metadata, dict):
        logger.debug("尝试从 response.metadata 提取 sources")
        try:
            if 'sources' in response.metadata:
                metadata_sources = response.metadata['sources']
                if isinstance(metadata_sources, list):
                    sources = metadata_sources
                    logger.debug("成功从 metadata 提取 sources", count=len(sources))
                    return sources
        except Exception as e:
            logger.warning("从 metadata 提取 sources 时出错", error=str(e))
    
    # 方式4：尝试从 Agent 的工具调用历史中提取（如果提供了 agent 实例）
    if agent is not None:
        logger.debug("尝试从 Agent 工具调用历史中提取 sources")
        try:
            # 检查 Agent 是否有 chat_history 或 memory 属性
            if hasattr(agent, 'chat_history') and agent.chat_history:
                # 从聊天历史中提取工具调用结果
                for msg in agent.chat_history:
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            if hasattr(tool_call, 'result') and hasattr(tool_call.result, 'source_nodes'):
                                for node in tool_call.result.source_nodes:
                                    source = {
                                        'text': node.text if hasattr(node, 'text') else str(node),
                                        'score': node.score if hasattr(node, 'score') else None,
                                        'metadata': node.metadata if hasattr(node, 'metadata') else {},
                                    }
                                    sources.append(source)
            
            # 检查 Agent 是否有 memory 或 memory_buffer 属性
            if hasattr(agent, 'memory') and agent.memory:
                if hasattr(agent.memory, 'get_all') and callable(agent.memory.get_all):
                    memory_messages = agent.memory.get_all()
                    for msg in memory_messages:
                        if hasattr(msg, 'tool_calls') and msg.tool_calls:
                            for tool_call in msg.tool_calls:
                                if hasattr(tool_call, 'result') and hasattr(tool_call.result, 'source_nodes'):
                                    for node in tool_call.result.source_nodes:
                                        source = {
                                            'text': node.text if hasattr(node, 'text') else str(node),
                                            'score': node.score if hasattr(node, 'score') else None,
                                            'metadata': node.metadata if hasattr(node, 'metadata') else {},
                                        }
                                        sources.append(source)
            
            if sources:
                logger.debug("成功从 Agent 工具调用历史提取 sources", count=len(sources))
                return sources
        except Exception as e:
            logger.warning("从 Agent 工具调用历史提取 sources 时出错", error=str(e), exc_info=True)
    
    # 如果所有方式都失败，记录警告并返回空列表
    logger.debug(
        "无法从 Agent 响应中提取 sources，返回空列表",
        response_type=response_type,
        response_str_preview=str(response)[:200] if response else None
    )
    
    return sources


def extract_reasoning_from_agent(response: Any, agent: Optional[Any] = None) -> Optional[str]:
    """从 Agent 响应中提取 reasoning
    
    尝试从多个可能的属性路径中提取推理链内容
    
    Args:
        response: Agent 返回的响应对象
        agent: Agent 实例（可选，用于访问思考过程）
        
    Returns:
        推理链内容（如果存在）
    """
    reasoning_content = None
    
    # 记录响应对象类型，便于调试
    response_type = type(response).__name__
    logger.debug("开始提取 reasoning", response_type=response_type, has_agent=agent is not None)
    
    # 方式1：直接检查 response.reasoning_content
    if hasattr(response, 'reasoning_content') and response.reasoning_content:
        logger.debug("从 response.reasoning_content 提取 reasoning")
        try:
            reasoning_content = response.reasoning_content
            if reasoning_content:
                logger.debug("成功提取 reasoning", length=len(str(reasoning_content)))
                return str(reasoning_content)
        except Exception as e:
            logger.warning("从 reasoning_content 提取时出错", error=str(e))
    
    # 方式2：检查 response.message.reasoning_content
    if hasattr(response, 'message') and response.message:
        if hasattr(response.message, 'reasoning_content') and response.message.reasoning_content:
            logger.debug("从 response.message.reasoning_content 提取 reasoning")
            try:
                reasoning_content = response.message.reasoning_content
                if reasoning_content:
                    logger.debug("成功从 message 提取 reasoning", length=len(str(reasoning_content)))
                    return str(reasoning_content)
            except Exception as e:
                logger.warning("从 message.reasoning_content 提取时出错", error=str(e))
    
    # 方式3：检查 response.metadata 中的 reasoning
    if hasattr(response, 'metadata') and isinstance(response.metadata, dict):
        logger.debug("尝试从 response.metadata 提取 reasoning")
        try:
            if 'reasoning' in response.metadata:
                reasoning_content = response.metadata['reasoning']
                if reasoning_content:
                    logger.debug("成功从 metadata 提取 reasoning", length=len(str(reasoning_content)))
                    return str(reasoning_content)
        except Exception as e:
            logger.warning("从 metadata 提取 reasoning 时出错", error=str(e))
    
    # 方式4：尝试从 Agent 的思考过程中提取（如果提供了 agent 实例）
    if agent is not None:
        logger.debug("尝试从 Agent 思考过程中提取 reasoning")
        try:
            # 检查 Agent 是否有 chat_history 或 memory
            if hasattr(agent, 'chat_history') and agent.chat_history:
                # 从聊天历史中提取思考过程
                reasoning_parts = []
                for msg in agent.chat_history:
                    if hasattr(msg, 'content') and msg.content:
                        # 检查是否包含思考过程（通常包含 "Thought:" 或类似标记）
                        content = str(msg.content)
                        if 'thought' in content.lower() or 'reasoning' in content.lower():
                            reasoning_parts.append(content)
                
                if reasoning_parts:
                    reasoning_content = "\n".join(reasoning_parts)
                    logger.debug("成功从 Agent 思考过程提取 reasoning", length=len(reasoning_content))
                    return reasoning_content
        except Exception as e:
            logger.warning("从 Agent 思考过程提取 reasoning 时出错", error=str(e), exc_info=True)
    
    # 如果所有方式都失败，返回 None
    logger.debug("无法从 Agent 响应中提取 reasoning")
    
    return reasoning_content

