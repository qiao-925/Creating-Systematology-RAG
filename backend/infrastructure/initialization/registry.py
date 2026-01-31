"""
初始化注册表：注册所有需要初始化的模块

主要功能：
- register_all_modules()：注册所有模块到初始化管理器
- 定义各模块的检查函数和依赖关系
"""

import streamlit as st
from typing import Optional, Any

from backend.infrastructure.initialization.manager import InitializationManager, InitStatus
from backend.infrastructure.initialization.categories import InitCategory
from backend.infrastructure.config import config
from backend.infrastructure.logger import get_logger
from backend.infrastructure.initialization.registry_checks import (
    check_encoding, check_config, check_logger, check_embedding, check_chroma,
    check_index_manager, check_llm_factory, check_query_engine, check_rag_service,
    check_chat_manager, check_session_state, check_llama_debug, check_ragas
)
from backend.infrastructure.initialization.registry_init import (
    init_encoding, init_config, init_logger, init_embedding, init_index_manager,
    init_llm_factory, init_session_state, init_rag_service, init_chat_manager
)

logger = get_logger('initialization_registry')


def register_all_modules(manager: InitializationManager) -> None:
    """注册所有需要初始化的模块到初始化管理器
    
    Args:
        manager: 初始化管理器实例
    """
    logger.info("开始注册所有模块...")
    
    # ========== 基础层 ==========
    
    # 1. 编码设置
    manager.register_module(
        name="encoding",
        category=InitCategory.FOUNDATION.value,
        check_func=lambda: check_encoding(),
        init_func=lambda: init_encoding(manager),
        is_required=True,
        description="UTF-8编码设置"
    )
    
    # 2. 配置系统
    manager.register_module(
        name="config",
        category=InitCategory.FOUNDATION.value,
        check_func=lambda: check_config(),
        init_func=lambda: init_config(manager),
        dependencies=["encoding"],
        is_required=True,
        description="配置系统加载"
    )
    
    # 3. 日志系统
    manager.register_module(
        name="logger",
        category=InitCategory.FOUNDATION.value,
        check_func=lambda: check_logger(),
        init_func=lambda: init_logger(manager),
        dependencies=["config"],
        is_required=True,
        description="日志系统初始化"
    )
    
    # ========== 核心层 ==========
    
    # 4. Embedding 模型（延迟加载：启动时不初始化，首次使用时再初始化）
    manager.register_module(
        name="embedding",
        category=InitCategory.CORE.value,
        check_func=lambda: check_embedding(),
        init_func=lambda: init_embedding(manager),
        dependencies=["config", "logger"],
        is_required=False,  # 改为可选，延迟加载
        description=f"Embedding模型 ({config.EMBEDDING_TYPE}) - 延迟加载"
    )
    
    # 5. Chroma 向量数据库（延迟加载：启动时不连接，首次使用时再连接）
    manager.register_module(
        name="chroma",
        category=InitCategory.CORE.value,
        check_func=lambda: check_chroma(),
        dependencies=["config", "logger"],
        is_required=False,  # 改为可选，延迟加载
        description="Chroma向量数据库连接 - 延迟加载"
    )
    
    # 6. 索引管理器（延迟加载：启动时不初始化，首次使用时再初始化）
    manager.register_module(
        name="index_manager",
        category=InitCategory.CORE.value,
        check_func=lambda: check_index_manager(),
        init_func=lambda: init_index_manager(manager),
        dependencies=[],  # 移除强制依赖，改为延迟初始化
        is_required=False,  # 改为可选，延迟加载
        description="索引管理器 - 延迟加载"
    )
    
    # 7. LLM 工厂（延迟加载：启动时仅验证配置，首次使用时再创建实例）
    manager.register_module(
        name="llm_factory",
        category=InitCategory.CORE.value,
        check_func=lambda: check_llm_factory(),
        init_func=lambda: init_llm_factory(manager),
        dependencies=["config", "logger"],
        is_required=False,  # 改为可选，延迟加载
        description="LLM工厂（DeepSeek）- 延迟加载"
    )
    
    # 8. 会话状态
    manager.register_module(
        name="session_state",
        category=InitCategory.CORE.value,
        check_func=lambda: check_session_state(),
        init_func=lambda: init_session_state(manager),
        dependencies=["config"],
        is_required=True,
        description="Streamlit会话状态初始化"
    )
    
    # 9. RAG 服务（延迟加载：启动时不初始化，首次使用时再初始化）
    manager.register_module(
        name="rag_service",
        category=InitCategory.CORE.value,
        check_func=lambda: check_rag_service(),
        init_func=lambda: init_rag_service(manager),
        dependencies=["llm_factory"],  # 移除对 index_manager 的强制依赖
        is_required=False,  # 改为可选，延迟加载
        description="RAG服务 - 延迟加载"
    )
    
    # 10. 对话管理器（延迟加载：启动时不初始化，首次使用时再初始化）
    manager.register_module(
        name="chat_manager",
        category=InitCategory.CORE.value,
        check_func=lambda: check_chat_manager(),
        init_func=lambda: init_chat_manager(manager),
        dependencies=["llm_factory"],  # 移除对 index_manager 的强制依赖
        is_required=False,  # 改为可选，延迟加载
        description="对话管理器 - 延迟加载"
    )
    
    # ========== 可选层 ==========
    
    # 11. 查询引擎（可选）
    manager.register_module(
        name="query_engine",
        category=InitCategory.OPTIONAL.value,
        check_func=lambda: check_query_engine(),
        dependencies=["index_manager", "llm_factory"],
        is_required=False,
        description="模块化查询引擎"
    )
    
    # 12. LlamaDebug 观察器
    manager.register_module(
        name="llama_debug",
        category=InitCategory.OPTIONAL.value,
        check_func=lambda: check_llama_debug(),
        dependencies=["config", "logger"],
        is_required=False,
        description="LlamaDebug调试工具"
    )
    
    # 13. RAGAS 评估器
    manager.register_module(
        name="ragas",
        category=InitCategory.OPTIONAL.value,
        check_func=lambda: check_ragas(),
        dependencies=["config", "logger"],
        is_required=False,
        description="RAGAS评估工具"
    )
    
    logger.info(f"所有模块注册完成，共注册 {len(manager.modules)} 个模块")
