"""
UI组件 - 会话状态管理模块：初始化和管理Streamlit会话状态

主要功能：
- init_session_state()：初始化Streamlit会话状态，包括索引管理、对话管理等

执行流程：
1. 初始化collection_name（使用默认配置）
2. 初始化索引和对话管理状态
3. 初始化UI显示相关状态
4. 设置默认值

特性：
- 完整的会话状态初始化
- 单例模式管理服务
- 默认值设置
"""

import streamlit as st

from src.infrastructure.config import config


def init_session_state() -> None:
    """初始化会话状态"""
    # 设置默认collection_name（使用配置中的默认值）
    if 'collection_name' not in st.session_state:
        st.session_state.collection_name = config.CHROMA_COLLECTION_NAME
    
    # 索引和对话管理
    if 'index_manager' not in st.session_state:
        st.session_state.index_manager = None
    
    if 'chat_manager' not in st.session_state:
        st.session_state.chat_manager = None
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'index_built' not in st.session_state:
        st.session_state.index_built = False
    
    if 'hybrid_query_engine' not in st.session_state:
        st.session_state.hybrid_query_engine = None
    
    # GitHub 增量更新相关
    if 'metadata_manager' not in st.session_state:
        from src.infrastructure.data_loader.metadata import MetadataManager
        st.session_state.metadata_manager = MetadataManager(config.GITHUB_METADATA_PATH)
    
    if 'github_repos' not in st.session_state:
        # 从元数据中加载已存在的仓库列表
        st.session_state.github_repos = st.session_state.metadata_manager.list_repositories()
    
    # 调试模式与可观测性（默认开启）
    if 'debug_mode_enabled' not in st.session_state:
        st.session_state.debug_mode_enabled = True
    
    if 'phoenix_enabled' not in st.session_state:
        st.session_state.phoenix_enabled = True
    
    if 'collect_trace' not in st.session_state:
        st.session_state.collect_trace = True
    
    # RAG服务（新架构）
    if 'rag_service' not in st.session_state:
        st.session_state.rag_service = None
    
    # 启动遮罩：首屏加载完成前为 False，完成后置 True
    if 'boot_ready' not in st.session_state:
        st.session_state.boot_ready = False
    
    # 对话设置（推理链）
    if 'show_reasoning' not in st.session_state:
        st.session_state.show_reasoning = config.DEEPSEEK_ENABLE_REASONING_DISPLAY
    
    if 'store_reasoning' not in st.session_state:
        st.session_state.store_reasoning = config.DEEPSEEK_STORE_REASONING
    
    # 服务验证状态缓存（避免每次rerun都验证）
    if 'rag_service_validated' not in st.session_state:
        st.session_state.rag_service_validated = False
    
    if 'index_manager_validated' not in st.session_state:
        st.session_state.index_manager_validated = False
    
    # 强制验证标志（当配置变更时需要重新验证）
    if 'force_validate_services' not in st.session_state:
        st.session_state.force_validate_services = False

