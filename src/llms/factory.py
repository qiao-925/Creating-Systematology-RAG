"""
DeepSeek LLM 工厂函数
统一管理 DeepSeek 实例创建，支持推理模型、JSON Output 等功能
"""

from typing import Optional, Dict, Any
from llama_index.llms.deepseek import DeepSeek

from src.config import config
from src.logger import setup_logger
from src.llms import wrap_deepseek

logger = setup_logger('llm_factory')


def create_deepseek_llm(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    use_json_output: bool = False,
    **kwargs
) -> DeepSeek:
    """创建 DeepSeek LLM 实例（统一工厂函数）
    
    统一管理 DeepSeek 实例创建，自动处理：
    - 推理模型配置（deepseek-reasoner）
    - JSON Output（按场景选择）
    - 参数验证和错误处理
    
    Args:
        api_key: API 密钥，默认使用 config.DEEPSEEK_API_KEY
        model: 模型名称，默认使用 config.LLM_MODEL（deepseek-reasoner）
        temperature: 温度参数，推理模型不支持此参数（会被忽略）
        max_tokens: 最大 token 数，默认 32K（推理模型最大 64K）
        use_json_output: 是否启用 JSON Output（仅用于结构化场景）
        **kwargs: 其他参数
        
    Returns:
        包装后的 DeepSeek 实例（已添加日志记录）
        
    Raises:
        ValueError: 如果 API 密钥未设置
    """
    # 获取配置
    final_api_key = api_key or config.DEEPSEEK_API_KEY
    final_model = model or config.LLM_MODEL
    
    if not final_api_key:
        raise ValueError("未设置 DEEPSEEK_API_KEY，请在 .env 文件中配置")
    
    # 确保使用推理模型
    if final_model != "deepseek-reasoner":
        logger.warning(f"模型 {final_model} 不是推理模型，建议使用 deepseek-reasoner")
    
    # 构建 LLM 配置
    llm_kwargs: Dict[str, Any] = {
        'api_key': final_api_key,
        'model': final_model,
        'max_tokens': max_tokens or 32768,  # 推理模型默认 32K
    }
    
    # JSON Output（仅用于结构化场景）
    if use_json_output:
        llm_kwargs['response_format'] = {"type": "json_object"}
        logger.debug("启用 JSON Output 模式")
    
    # 推理模型不支持某些参数，但为了兼容性不报错
    # 注意：temperature、top_p 等参数会被忽略
    if temperature is not None:
        logger.debug(f"推理模型不支持 temperature 参数，已忽略: {temperature}")
    
    # 合并其他参数
    llm_kwargs.update(kwargs)
    
    # 创建实例
    logger.info(f"创建 DeepSeek LLM 实例: model={final_model}, json_output={use_json_output}")
    deepseek_instance = DeepSeek(**llm_kwargs)
    
    # 包装日志记录
    wrapped_llm = wrap_deepseek(deepseek_instance)
    
    return wrapped_llm


def create_deepseek_llm_for_query(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
    **kwargs
) -> DeepSeek:
    """创建用于查询的 DeepSeek LLM 实例（自然语言输出）
    
    用于问答、对话等自然语言场景，不使用 JSON Output。
    
    Args:
        api_key: API 密钥
        model: 模型名称
        max_tokens: 最大 token 数
        **kwargs: 其他参数
        
    Returns:
        包装后的 DeepSeek 实例
    """
    return create_deepseek_llm(
        api_key=api_key,
        model=model,
        max_tokens=max_tokens,
        use_json_output=False,
        **kwargs
    )


def create_deepseek_llm_for_structure(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
    **kwargs
) -> DeepSeek:
    """创建用于结构化输出的 DeepSeek LLM 实例（JSON Output）
    
    用于查询理解、路由决策等结构化场景，启用 JSON Output。
    
    Args:
        api_key: API 密钥
        model: 模型名称
        max_tokens: 最大 token 数
        **kwargs: 其他参数
        
    Returns:
        包装后的 DeepSeek 实例（启用 JSON Output）
    """
    return create_deepseek_llm(
        api_key=api_key,
        model=model,
        max_tokens=max_tokens,
        use_json_output=True,
        **kwargs
    )

