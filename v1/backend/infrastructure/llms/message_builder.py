"""
消息组装工具 - 根据模型类型适配消息格式

主要功能：
- build_chat_messages()：根据模型类型组装消息列表
- 通用模型：使用 system + user 分开
- 推理模型：全部放入 user（官方推荐）

设计依据：
- DeepSeek R1 官方建议：避免使用 system prompt，指令放 user prompt
- OpenAI o1 官方建议：简单直接的指令，不需要复杂 CoT 引导
- 通用模型（GPT-4o, Claude）：支持 system prompt，效果更好
"""

from typing import List, Optional

from llama_index.core.llms import ChatMessage, MessageRole

from backend.infrastructure.config import config
from backend.infrastructure.logger import get_logger

logger = get_logger('llm_message_builder')


def build_chat_messages(
    system_prompt: str,
    user_query: str,
    model_id: Optional[str] = None,
) -> List[ChatMessage]:
    """根据模型类型组装消息列表
    
    Args:
        system_prompt: 系统提示词（包含角色、指令、格式要求等）
        user_query: 用户查询内容
        model_id: 模型 ID（可选，默认使用当前配置的模型）
        
    Returns:
        ChatMessage 列表，格式取决于模型类型：
        - 通用模型：[system, user]
        - 推理模型：[user]（system 内容合并到 user）
    """
    # 获取模型配置
    final_model_id = model_id or config.get_default_llm_id()
    model_config = config.get_llm_model_config(final_model_id)
    
    # 判断是否为推理模型
    is_reasoning_model = model_config.supports_reasoning if model_config else False
    
    if is_reasoning_model:
        # 推理模型：全部放入 user
        # 官方建议：指令简洁，不需要复杂引导
        combined_content = f"{system_prompt}\n\n{user_query}"
        messages = [
            ChatMessage(role=MessageRole.USER, content=combined_content)
        ]
        logger.debug(
            f"推理模型消息组装: model={final_model_id}, "
            f"format=user_only, content_length={len(combined_content)}"
        )
    else:
        # 通用模型：system + user 分开
        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=system_prompt),
            ChatMessage(role=MessageRole.USER, content=user_query)
        ]
        logger.debug(
            f"通用模型消息组装: model={final_model_id}, "
            f"format=system+user, "
            f"system_length={len(system_prompt)}, user_length={len(user_query)}"
        )
    
    return messages


def is_reasoning_model(model_id: Optional[str] = None) -> bool:
    """判断指定模型是否为推理模型
    
    Args:
        model_id: 模型 ID（可选，默认使用当前配置的模型）
        
    Returns:
        True 如果是推理模型，否则 False
    """
    final_model_id = model_id or config.get_default_llm_id()
    model_config = config.get_llm_model_config(final_model_id)
    return model_config.supports_reasoning if model_config else False
