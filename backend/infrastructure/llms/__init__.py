"""
LLM模块：包含DeepSeek相关的包装器和工具

主要功能：
- DeepSeekLogger类：DeepSeek日志记录器
- wrap_deepseek()：包装DeepSeek LLM，添加日志功能
- create_deepseek_llm()：创建DeepSeek LLM实例
- create_deepseek_llm_for_query()：创建用于查询的DeepSeek LLM
- create_deepseek_llm_for_structure()：创建用于结构化输出的DeepSeek LLM
- extract_reasoning_content()：提取推理链内容
- extract_reasoning_from_stream_chunk()：从流式响应中提取推理链

执行流程：
1. 创建LLM实例
2. 配置推理模型和JSON输出
3. 执行查询
4. 提取推理链（如果支持）

特性：
- DeepSeek LLM集成
- 推理链支持
- JSON输出支持
- 日志记录功能
"""

from backend.infrastructure.llms.deepseek_logger import DeepSeekLogger, wrap_deepseek
from backend.infrastructure.llms.factory import (
    create_deepseek_llm,
    create_deepseek_llm_for_query,
    create_deepseek_llm_for_structure,
)
from backend.infrastructure.llms.reasoning import (
    extract_reasoning_content,
    extract_reasoning_from_stream_chunk,
    clean_messages_for_api,
    has_reasoning_content,
)

__all__ = [
    'DeepSeekLogger',
    'wrap_deepseek',
    'create_deepseek_llm',
    'create_deepseek_llm_for_query',
    'create_deepseek_llm_for_structure',
    'extract_reasoning_content',
    'extract_reasoning_from_stream_chunk',
    'clean_messages_for_api',
    'has_reasoning_content',
]

