"""
LLM 工厂函数：统一管理 LLM 实例创建，支持多模型动态切换

主要功能：
- create_llm()：按模型 ID 创建 LLM 实例（推荐使用）
- get_available_models()：获取所有可用模型列表
- create_deepseek_llm_for_query()：创建用于查询的 LLM（向后兼容）
- create_deepseek_llm_for_structure()：创建用于结构化输出的 LLM（向后兼容）

特性：
- 多模型支持（通过 LiteLLM 统一接口）
- 动态模型切换
- 向后兼容旧接口
- 日志包装
- 超时和重试机制
"""

import os
import time
from typing import Optional, Dict, Any, List, TYPE_CHECKING

# 延迟导入：LiteLLM 导入耗时 6+ 秒，只在实际创建时导入
if TYPE_CHECKING:
    from llama_index.llms.litellm import LiteLLM

from llama_index.core.llms import LLM

from backend.infrastructure.config import config
from backend.infrastructure.config.models import LLMModelConfig
from backend.infrastructure.logger import get_logger

logger = get_logger('llm_factory')


def create_llm(
    model_id: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    enable_retry: bool = True,
    **kwargs
) -> LLM:
    """按模型 ID 创建 LLM 实例（推荐使用）

    通过 LiteLLM 统一接口创建 LLM 实例，支持多种模型提供商。

    Args:
        model_id: 模型标识（如 "deepseek-chat"、"qwen-plus"）
                  默认使用 config.get_default_llm_id()
        temperature: 温度参数（覆盖配置中的默认值）
        max_tokens: 最大 token 数（覆盖配置中的默认值）
        enable_retry: 是否启用重试机制（默认 True）
        **kwargs: 其他 LiteLLM 参数

    Returns:
        LLM 实例

    Raises:
        ValueError: 如果模型 ID 无效或 API Key 未设置
        RuntimeError: 如果初始化失败且重试次数耗尽
    """
    # 获取模型 ID
    final_model_id = model_id or config.get_default_llm_id()

    # 获取模型配置
    model_config = config.get_llm_model_config(final_model_id)
    if not model_config:
        available = [m.id for m in config.get_available_llm_models()]
        raise ValueError(
            f"未找到模型配置: {final_model_id}，"
            f"可用模型: {available}"
        )

    # 获取 API Key
    api_key = os.getenv(model_config.api_key_env, "")
    if not api_key:
        raise ValueError(
            f"未设置 {model_config.api_key_env}，请在 .env 文件中配置"
        )

    # 获取重试配置
    llm_config = config.get_llm_config()
    max_retries = llm_config.get('max_retries', 3) if enable_retry else 1
    retry_delay = llm_config.get('retry_delay', 2.0)
    init_timeout = llm_config.get('initialization_timeout', 30.0)

    # 构建 LLM 配置
    llm_kwargs: Dict[str, Any] = {
        'model': model_config.litellm_model,
        'api_key': api_key,
    }

    # 设置 request_timeout（LiteLLM 支持）
    request_timeout = model_config.request_timeout or init_timeout
    if request_timeout:
        llm_kwargs['request_timeout'] = request_timeout

    # 设置 max_tokens
    final_max_tokens = max_tokens or model_config.max_tokens
    if final_max_tokens:
        llm_kwargs['max_tokens'] = final_max_tokens

    # 设置 temperature（推理模型不支持）
    final_temperature = temperature if temperature is not None else model_config.temperature
    if final_temperature is not None:
        if model_config.supports_reasoning:
            logger.debug(f"推理模型不支持 temperature 参数，已忽略: {final_temperature}")
        else:
            llm_kwargs['temperature'] = final_temperature

    # 合并其他参数
    llm_kwargs.update(kwargs)

    # 带重试的创建 LiteLLM 实例
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            start_time = time.perf_counter()
            logger.info(
                f"创建 LLM 实例 (尝试 {attempt}/{max_retries}): "
                f"model_id={final_model_id}, litellm_model={model_config.litellm_model}, "
                f"timeout={request_timeout}s"
            )

            # 延迟导入：只在实际创建时导入 LiteLLM（导入耗时 6+ 秒）
            from llama_index.llms.litellm import LiteLLM

            llm = LiteLLM(**llm_kwargs)

            elapsed = time.perf_counter() - start_time
            logger.info(f"✅ LLM 实例创建成功 (耗时: {elapsed:.2f}s)")
            return llm

        except Exception as e:
            elapsed = time.perf_counter() - start_time
            last_error = e
            logger.warning(
                f"⚠️  LLM 初始化失败 (尝试 {attempt}/{max_retries}, 耗时: {elapsed:.2f}s): {e}"
            )

            # 如果还有重试机会，等待后重试
            if attempt < max_retries:
                wait_time = retry_delay * (2 ** (attempt - 1))  # 指数退避
                logger.info(f"等待 {wait_time:.1f}s 后重试...")
                time.sleep(wait_time)
            else:
                # 重试次数耗尽
                logger.error(f"❌ LLM 初始化失败，已重试 {max_retries} 次")
                raise RuntimeError(
                    f"LLM 初始化失败（模型: {final_model_id}）: {last_error}"
                ) from last_error

    # 理论上不会到达这里
    raise RuntimeError(f"LLM 初始化失败: {last_error}")


def get_available_models() -> List[LLMModelConfig]:
    """获取所有可用的 LLM 模型列表
    
    Returns:
        LLMModelConfig 列表
    """
    return config.get_available_llm_models()


def get_model_info(model_id: str) -> Optional[Dict[str, Any]]:
    """获取模型信息（供前端使用）
    
    Args:
        model_id: 模型标识
        
    Returns:
        模型信息字典，包含 id, name, supports_reasoning 等
    """
    model_config = config.get_llm_model_config(model_id)
    if not model_config:
        return None
    return {
        'id': model_config.id,
        'name': model_config.name,
        'supports_reasoning': model_config.supports_reasoning,
        'temperature': model_config.temperature,
        'max_tokens': model_config.max_tokens,
    }


# ==================== 向后兼容接口 ====================


def create_deepseek_llm(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    use_json_output: bool = False,
    **kwargs
) -> LLM:
    """创建 DeepSeek LLM 实例（向后兼容）
    
    注意：此函数保留用于向后兼容，推荐使用 create_llm()。
    
    Args:
        api_key: API 密钥（已弃用，使用环境变量配置）
        model: 模型名称（已弃用，使用 model_id）
        temperature: 温度参数
        max_tokens: 最大 token 数
        use_json_output: 是否启用 JSON Output
        **kwargs: 其他参数
        
    Returns:
        LLM 实例
    """
    # 映射旧模型名称到新模型 ID
    model_id_map = {
        'deepseek-chat': 'deepseek-chat',
        'deepseek-reasoner': 'deepseek-reasoner',
    }
    
    model_name = model or config.LLM_MODEL
    model_id = model_id_map.get(model_name, 'deepseek-chat')
    
    # JSON Output 通过 kwargs 传递
    if use_json_output:
        kwargs['response_format'] = {"type": "json_object"}
        logger.debug("启用 JSON Output 模式")
    
    return create_llm(
        model_id=model_id,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs
    )


def create_deepseek_llm_for_query(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
    **kwargs
) -> LLM:
    """创建用于查询的 LLM 实例（向后兼容）"""
    return create_deepseek_llm(
        api_key=api_key, model=model, max_tokens=max_tokens,
        use_json_output=False, **kwargs
    )


def create_deepseek_llm_for_structure(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
    **kwargs
) -> LLM:
    """创建用于结构化输出的 LLM 实例（向后兼容）"""
    return create_deepseek_llm(
        api_key=api_key, model=model, max_tokens=max_tokens,
        use_json_output=True, **kwargs
    )
