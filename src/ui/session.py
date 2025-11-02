"""
UI组件 - 会话状态管理模块
初始化和管理Streamlit会话状态
"""

import streamlit as st

from src.config import config


def init_session_state():
    """初始化会话状态"""
    # 用户管理
    if 'user_manager' not in st.session_state:
        from src.user_manager import UserManager
        st.session_state.user_manager = UserManager()
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    
    if 'collection_name' not in st.session_state:
        st.session_state.collection_name = None
    
    # 索引和对话管理
    if 'index_manager' not in st.session_state:
        st.session_state.index_manager = None
    
    if 'chat_manager' not in st.session_state:
        st.session_state.chat_manager = None
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'index_built' not in st.session_state:
        st.session_state.index_built = False
    
    # 维基百科配置
    if 'enable_wikipedia' not in st.session_state:
        st.session_state.enable_wikipedia = config.ENABLE_WIKIPEDIA
    
    if 'wikipedia_threshold' not in st.session_state:
        st.session_state.wikipedia_threshold = config.WIKIPEDIA_THRESHOLD
    
    if 'hybrid_query_engine' not in st.session_state:
        st.session_state.hybrid_query_engine = None
    
    # 默认登录账号（方便测试）
    if 'login_email' not in st.session_state:
        st.session_state.login_email = "test@example.com"
    
    if 'login_password' not in st.session_state:
        st.session_state.login_password = "123456"
    
    # GitHub 增量更新相关
    if 'metadata_manager' not in st.session_state:
        from src.metadata_manager import MetadataManager
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

