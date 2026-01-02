"""
初始化注册表：注册所有需要初始化的模块

主要功能：
- register_all_modules()：注册所有模块到初始化管理器
- 定义各模块的检查函数和依赖关系
"""

import streamlit as st
from typing import Optional

from src.infrastructure.initialization.manager import InitializationManager
from src.infrastructure.config import config
from src.infrastructure.logger import get_logger

logger = get_logger('initialization_registry')


def register_all_modules(manager: InitializationManager) -> None:
    """注册所有需要初始化的模块到初始化管理器
    
    Args:
        manager: 初始化管理器实例
    """
    logger.info("开始注册所有模块...")
    
    # ========== 基础设施层 ==========
    
    # 1. 编码设置
    manager.register_module(
        name="encoding",
        category="infrastructure",
        check_func=lambda: _check_encoding(),
        is_required=True,
        description="UTF-8编码设置"
    )
    
    # 2. 配置系统
    manager.register_module(
        name="config",
        category="infrastructure",
        check_func=lambda: _check_config(),
        dependencies=["encoding"],
        is_required=True,
        description="配置系统加载"
    )
    
    # 3. 日志系统
    manager.register_module(
        name="logger",
        category="infrastructure",
        check_func=lambda: _check_logger(),
        dependencies=["config"],
        is_required=True,
        description="日志系统初始化"
    )
    
    # 4. Embedding 模型
    manager.register_module(
        name="embedding",
        category="infrastructure",
        check_func=lambda: _check_embedding(),
        dependencies=["config", "logger"],
        is_required=True,
        description=f"Embedding模型 ({config.EMBEDDING_TYPE})"
    )
    
    # 5. Chroma 向量数据库
    manager.register_module(
        name="chroma",
        category="infrastructure",
        check_func=lambda: _check_chroma(),
        dependencies=["config", "logger"],
        is_required=True,
        description="Chroma向量数据库连接"
    )
    
    # 6. 索引管理器
    manager.register_module(
        name="index_manager",
        category="infrastructure",
        check_func=lambda: _check_index_manager(),
        dependencies=["embedding", "chroma"],
        is_required=True,
        description="索引管理器"
    )
    
    # ========== 业务层 ==========
    
    # 7. LLM 工厂
    manager.register_module(
        name="llm_factory",
        category="business",
        check_func=lambda: _check_llm_factory(),
        dependencies=["config", "logger"],
        is_required=True,
        description="LLM工厂（DeepSeek）"
    )
    
    # 8. 查询引擎
    manager.register_module(
        name="query_engine",
        category="business",
        check_func=lambda: _check_query_engine(),
        dependencies=["index_manager", "llm_factory"],
        is_required=False,  # 可选，因为可能没有索引
        description="模块化查询引擎"
    )
    
    # 9. RAG 服务
    manager.register_module(
        name="rag_service",
        category="business",
        check_func=lambda: _check_rag_service(),
        dependencies=["index_manager", "llm_factory"],
        is_required=False,  # 可选，因为可能没有索引
        description="RAG服务"
    )
    
    # 10. 对话管理器
    manager.register_module(
        name="chat_manager",
        category="business",
        check_func=lambda: _check_chat_manager(),
        dependencies=["index_manager", "llm_factory"],
        is_required=False,  # 可选，因为可能没有索引
        description="对话管理器"
    )
    
    # ========== UI层 ==========
    
    # 11. 会话状态
    manager.register_module(
        name="session_state",
        category="ui",
        check_func=lambda: _check_session_state(),
        dependencies=["config"],
        is_required=True,
        description="Streamlit会话状态初始化"
    )
    
    # ========== 可观测性 ==========
    
    # 12. Phoenix 观察器
    manager.register_module(
        name="phoenix",
        category="observability",
        check_func=lambda: _check_phoenix(),
        dependencies=["config", "logger"],
        is_required=False,
        description="Phoenix可观测性工具"
    )
    
    # 13. LlamaDebug 观察器
    manager.register_module(
        name="llama_debug",
        category="observability",
        check_func=lambda: _check_llama_debug(),
        dependencies=["config", "logger"],
        is_required=False,
        description="LlamaDebug调试工具"
    )
    
    # 14. RAGAS 评估器
    manager.register_module(
        name="ragas",
        category="observability",
        check_func=lambda: _check_ragas(),
        dependencies=["config", "logger"],
        is_required=False,
        description="RAGAS评估工具"
    )
    
    logger.info(f"✅ 已注册 {len(manager.modules)} 个模块")


# ========== 检查函数实现 ==========

def _check_encoding() -> bool:
    """检查编码设置"""
    try:
        import os
        return os.environ.get("PYTHONIOENCODING", "").lower() == "utf-8"
    except Exception:
        return False


def _check_config() -> bool:
    """检查配置系统"""
    try:
        # 检查关键配置是否存在
        return (
            hasattr(config, 'DEEPSEEK_API_KEY') and
            hasattr(config, 'EMBEDDING_TYPE') and
            hasattr(config, 'CHROMA_COLLECTION_NAME')
        )
    except Exception:
        return False


def _check_logger() -> bool:
    """检查日志系统"""
    try:
        from src.infrastructure.logger import get_logger
        test_logger = get_logger('test')
        test_logger.info("测试日志")
        return True
    except Exception:
        return False


def _check_embedding() -> bool:
    """检查Embedding模型"""
    try:
        # 检查session_state中是否有embedding实例
        if hasattr(st, 'session_state'):
            if 'embed_model' in st.session_state and st.session_state.embed_model is not None:
                return True
        
        # 尝试从工厂函数获取
        from src.infrastructure.embeddings.factory import get_embedding_instance
        instance = get_embedding_instance()
        return instance is not None
    except Exception:
        return False


def _check_chroma() -> bool:
    """检查Chroma向量数据库"""
    try:
        # 检查配置
        if not config.CHROMA_COLLECTION_NAME:
            return False
        
        # 尝试创建IndexManager来测试Chroma连接
        from src.infrastructure.indexer import IndexManager
        # 不实际创建，只检查配置
        return True
    except Exception:
        return False


def _check_index_manager() -> bool:
    """检查索引管理器"""
    try:
        if hasattr(st, 'session_state'):
            if 'index_manager' in st.session_state and st.session_state.index_manager is not None:
                return True
        
        # 尝试加载
        from frontend.utils.services import load_index
        index_manager = load_index()
        return index_manager is not None
    except Exception as e:
        logger.debug(f"索引管理器检查失败: {e}")
        return False


def _check_llm_factory() -> bool:
    """检查LLM工厂"""
    try:
        # 检查API Key是否配置
        if not config.DEEPSEEK_API_KEY:
            return False
        
        # 尝试创建LLM实例（不实际调用API）
        from src.infrastructure.llms.factory import create_deepseek_llm_for_query
        # 只检查函数是否存在，不实际创建
        return callable(create_deepseek_llm_for_query)
    except Exception:
        return False


def _check_query_engine() -> bool:
    """检查查询引擎"""
    try:
        # 查询引擎是可选的，需要索引管理器
        if not _check_index_manager():
            return False
        
        # 检查模块是否存在
        from src.business.rag_engine.core.engine import ModularQueryEngine
        return True
    except Exception:
        return False


def _check_rag_service() -> bool:
    """检查RAG服务"""
    try:
        if hasattr(st, 'session_state'):
            if 'rag_service' in st.session_state and st.session_state.rag_service is not None:
                return True
        
        # 尝试加载
        from frontend.utils.services import load_rag_service
        rag_service = load_rag_service()
        return rag_service is not None
    except Exception as e:
        logger.debug(f"RAG服务检查失败: {e}")
        return False


def _check_chat_manager() -> bool:
    """检查对话管理器"""
    try:
        if hasattr(st, 'session_state'):
            if 'chat_manager' in st.session_state and st.session_state.chat_manager is not None:
                return True
        
        # 尝试加载
        from frontend.utils.services import load_chat_manager
        chat_manager = load_chat_manager()
        return chat_manager is not None
    except Exception as e:
        logger.debug(f"对话管理器检查失败: {e}")
        return False


def _check_session_state() -> bool:
    """检查会话状态"""
    try:
        if not hasattr(st, 'session_state'):
            return False
        
        # 检查关键状态是否存在
        required_keys = ['collection_name', 'messages']
        return all(key in st.session_state for key in required_keys)
    except Exception:
        return False


def _check_phoenix() -> bool:
    """检查Phoenix观察器"""
    try:
        if not config.OBSERVABILITY_PHOENIX_ENABLE:
            return False
        
        # 检查模块是否存在
        from src.infrastructure.observers.phoenix_observer import PhoenixObserver
        return True
    except Exception:
        return False


def _check_llama_debug() -> bool:
    """检查LlamaDebug观察器"""
    try:
        if not config.OBSERVABILITY_LLAMA_DEBUG_ENABLE:
            return False
        
        # 检查模块是否存在
        from src.infrastructure.observers.llama_debug_observer import LlamaDebugObserver
        return True
    except Exception:
        return False


def _check_ragas() -> bool:
    """检查RAGAS评估器"""
    try:
        if not config.RAGAS_ENABLE:
            return False
        
        # 检查模块是否存在
        from src.infrastructure.observers.ragas_evaluator import RAGASEvaluator
        return True
    except Exception:
        return False
