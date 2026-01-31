"""
初始化注册表：检查函数

主要功能：
- 提供各模块的检查函数，用于验证模块是否已正确初始化
"""

import streamlit as st

from backend.infrastructure.config import config
from backend.infrastructure.logger import get_logger

logger = get_logger('initialization_registry')


def check_encoding() -> bool:
    """检查编码设置"""
    try:
        import os
        return os.environ.get("PYTHONIOENCODING", "").lower() == "utf-8"
    except Exception:
        return False


def check_config() -> bool:
    """检查配置系统"""
    try:
        return (
            hasattr(config, 'DEEPSEEK_API_KEY') and
            hasattr(config, 'EMBEDDING_TYPE') and
            hasattr(config, 'CHROMA_COLLECTION_NAME')
        )
    except Exception:
        return False


def check_logger() -> bool:
    """检查日志系统"""
    try:
        from backend.infrastructure.logger import get_logger
        test_logger = get_logger('test')
        test_logger.info("测试日志")
        return True
    except Exception:
        return False


def check_embedding() -> bool:
    """检查Embedding模型"""
    try:
        if hasattr(st, 'session_state'):
            if 'embed_model' in st.session_state and st.session_state.embed_model is not None:
                return True
        
        from backend.infrastructure.embeddings.factory import get_embedding_instance
        instance = get_embedding_instance()
        return instance is not None
    except Exception:
        return False


def check_chroma() -> bool:
    """检查Chroma向量数据库"""
    try:
        if not config.CHROMA_COLLECTION_NAME:
            return False
        
        from backend.infrastructure.indexer import IndexManager
        return True
    except Exception:
        return False


def check_index_manager() -> bool:
    """检查索引管理器"""
    try:
        init_result = st.session_state.get('init_result')
        if init_result and 'index_manager' in init_result.instances:
            return init_result.instances['index_manager'] is not None
        
        if hasattr(st, 'session_state'):
            if 'index_manager' in st.session_state and st.session_state.index_manager is not None:
                return True
        
        return False
    except Exception as e:
        logger.debug(f"索引管理器检查失败: {e}")
        return False


def check_llm_factory() -> bool:
    """检查LLM工厂（延迟加载：仅验证配置）"""
    try:
        # 仅验证配置，不创建实例
        if not config.DEEPSEEK_API_KEY:
            logger.warning("未设置 DEEPSEEK_API_KEY")
            return False

        # 验证默认模型配置
        default_model_id = config.get_default_llm_id()
        model_config = config.get_llm_model_config(default_model_id)
        if not model_config:
            logger.warning(f"未找到默认模型配置: {default_model_id}")
            return False

        # 验证工厂函数可用
        from backend.infrastructure.llms.factory import create_llm
        if not callable(create_llm):
            logger.warning("LLM工厂函数不可用")
            return False

        return True
    except Exception as e:
        logger.warning(f"LLM工厂检查失败: {e}")
        return False


def check_query_engine() -> bool:
    """检查查询引擎"""
    try:
        if not check_index_manager():
            return False
        
        from backend.business.rag_engine.core.engine import ModularQueryEngine
        return True
    except Exception:
        return False


def check_rag_service() -> bool:
    """检查RAG服务"""
    try:
        init_result = st.session_state.get('init_result')
        if init_result and 'rag_service' in init_result.instances:
            return init_result.instances['rag_service'] is not None
        
        if hasattr(st, 'session_state'):
            if 'rag_service' in st.session_state and st.session_state.rag_service is not None:
                return True
        
        return False
    except Exception as e:
        logger.debug(f"RAG服务检查失败: {e}")
        return False


def check_chat_manager() -> bool:
    """检查对话管理器"""
    try:
        init_result = st.session_state.get('init_result')
        if init_result and 'chat_manager' in init_result.instances:
            return init_result.instances['chat_manager'] is not None
        
        if hasattr(st, 'session_state'):
            if 'chat_manager' in st.session_state and st.session_state.chat_manager is not None:
                return True
        
        return False
    except Exception as e:
        logger.debug(f"对话管理器检查失败: {e}")
        return False


def check_session_state() -> bool:
    """检查会话状态"""
    try:
        if not hasattr(st, 'session_state'):
            return False
        
        required_keys = ['collection_name', 'messages']
        return all(key in st.session_state for key in required_keys)
    except Exception:
        return False


def check_llama_debug() -> bool:
    """检查LlamaDebug观察器"""
    from backend.infrastructure.logger import get_logger
    check_logger = get_logger('initialization.check')
    
    if not hasattr(config, 'ENABLE_DEBUG_HANDLER'):
        error_msg = "配置项 ENABLE_DEBUG_HANDLER 不存在，请检查配置文件"
        check_logger.error(error_msg)
        raise AttributeError(error_msg)
    
    if not config.ENABLE_DEBUG_HANDLER:
        error_msg = "LlamaDebug 未启用（ENABLE_DEBUG_HANDLER=False），请在 application.yml 中设置 observability.llama_debug.enable=true"
        check_logger.warning(error_msg)
        return False
    
    try:
        from backend.infrastructure.observers.llama_debug_observer import LlamaDebugObserver
        check_logger.debug("LlamaDebugObserver 模块导入成功")
    except ImportError as e:
        error_msg = f"无法导入 LlamaDebugObserver 模块: {e}。请检查模块文件是否存在"
        check_logger.error(error_msg)
        raise ImportError(error_msg) from e
    
    try:
        observer = LlamaDebugObserver(enabled=False)
        check_logger.debug("LlamaDebugObserver 实例创建成功")
    except Exception as e:
        error_msg = f"LlamaDebugObserver 实例创建失败: {e}。请检查依赖项是否正确安装"
        check_logger.error(error_msg, exc_info=True)
        raise RuntimeError(error_msg) from e
    
    check_logger.info("LlamaDebug 检查通过")
    return True


def check_ragas() -> bool:
    """检查RAGAS评估器"""
    try:
        if not config.RAGAS_ENABLE:
            return False
        
        from backend.infrastructure.observers.ragas_evaluator import RAGASEvaluator
        return True
    except Exception:
        return False
