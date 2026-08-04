"""
LLM模块：统一的多模型 LLM 接口

主要功能：
- create_llm()：按模型 ID 创建 LLM 实例（推荐使用）
- get_available_models()：获取所有可用模型列表
- wrap_llm()：包装 LLM 实例，添加日志功能
- create_deepseek_llm_for_query()：创建用于查询的 LLM（向后兼容）
- create_deepseek_llm_for_structure()：创建用于结构化输出的 LLM（向后兼容）
- extract_reasoning_content()：提取推理链内容
- extract_reasoning_from_stream_chunk()：从流式响应中提取推理链

执行流程：
1. 创建LLM实例（通过 LiteLLM 统一接口）
2. 配置模型参数
3. 执行查询
4. 提取推理链（如果支持）

特性：
- 多模型支持（DeepSeek、Qwen、GPT 等）
- 推理链支持
- JSON输出支持
- 日志记录功能
"""

from backend.infrastructure.llms.deepseek_logger import (
    LLMLogger,
    DeepSeekLogger,  # 向后兼容
    wrap_llm,
    wrap_deepseek,  # 向后兼容
)
from backend.infrastructure.llms.factory import (
    create_llm,
    get_available_models,
    get_model_info,
    create_deepseek_llm,  # 向后兼容
    create_deepseek_llm_for_query,
    create_deepseek_llm_for_structure,
)
from backend.infrastructure.llms.reasoning import (
    extract_reasoning_content,
    extract_reasoning_from_stream_chunk,
    clean_messages_for_api,
    has_reasoning_content,
)
from backend.infrastructure.llms.message_builder import (
    build_chat_messages,
    is_reasoning_model,
)

__all__ = [
    # 新接口（推荐使用）
    'create_llm',
    'get_available_models',
    'get_model_info',
    'LLMLogger',
    'wrap_llm',
    # 消息组装（模型类型适配）
    'build_chat_messages',
    'is_reasoning_model',
    # 向后兼容接口
    'DeepSeekLogger',
    'wrap_deepseek',
    'create_deepseek_llm',
    'create_deepseek_llm_for_query',
    'create_deepseek_llm_for_structure',
    # 推理链工具
    'extract_reasoning_content',
    'extract_reasoning_from_stream_chunk',
    'clean_messages_for_api',
    'has_reasoning_content',
]

