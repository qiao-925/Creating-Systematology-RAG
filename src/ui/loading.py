"""
UI组件 - 加载函数模块
加载模型、索引、服务等
"""

import streamlit as st
from typing import Optional

from src.config import config
from src.indexer import (
    IndexManager,
    get_global_embed_model,
    load_embedding_model,
    set_global_embed_model
)
from src.chat_manager import ChatManager
from src.business.services import RAGService
from src.logger import setup_logger

logger = setup_logger('ui_components')


def preload_embedding_model():
    """预加载 Embedding 模型（仅加载一次）"""
    if 'embed_model' not in st.session_state:
        st.session_state.embed_model = None
    
    if 'embed_model_loaded' not in st.session_state:
        st.session_state.embed_model_loaded = False
    
    # 如果已经加载过，直接返回
    if st.session_state.embed_model_loaded and st.session_state.embed_model is not None:
        set_global_embed_model(st.session_state.embed_model)
        return
    
    # 检查是否已经有全局模型
    global_model = get_global_embed_model()
    
    if global_model is None:
        # 模型未加载，开始加载
        with st.spinner(f"🚀 正在预加载 Embedding 模型 ({config.EMBEDDING_MODEL})..."):
            try:
                model = load_embedding_model()
                st.session_state.embed_model = model
                st.session_state.embed_model_loaded = True
                st.success("✅ Embedding 模型预加载完成")
            except Exception as e:
                st.error(f"❌ 模型加载失败: {e}")
                st.stop()
    else:
        # 模型已加载
        st.session_state.embed_model = global_model
        st.session_state.embed_model_loaded = True


def load_rag_service() -> Optional[RAGService]:
    """加载或创建RAG服务（新架构推荐）
    
    Returns:
        Optional[RAGService]: RAG服务实例，失败返回None
    """
    try:
        if st.session_state.rag_service is None:
            # 使用用户专属的 collection
            if not st.session_state.collection_name:
                raise ValueError("未登录或 collection_name 未设置，请先登录")
            collection_name = st.session_state.collection_name
            
            with st.spinner("🔧 初始化RAG服务..."):
                st.session_state.rag_service = RAGService(
                    collection_name=collection_name,
                    enable_debug=st.session_state.get('debug_mode_enabled', False),
                    enable_markdown_formatting=True,
                )
                st.success("✅ RAG服务已初始化")
        
        return st.session_state.rag_service
    except Exception as e:
        st.error(f"❌ RAG服务初始化失败: {e}")
        logger.error(f"RAG服务初始化失败: {e}", exc_info=True)
        return None


def load_index():
    """加载或创建索引（向后兼容）"""
    try:
        if st.session_state.index_manager is None:
            # 使用用户专属的 collection（登录后必须有 collection_name）
            if not st.session_state.collection_name:
                raise ValueError("未登录或 collection_name 未设置，请先登录")
            collection_name = st.session_state.collection_name
            
            with st.spinner("🔧 初始化索引管理器..."):
                st.session_state.index_manager = IndexManager(
                    collection_name=collection_name,
                    embedding_instance=st.session_state.get('embed_model')
                )
                st.success("✅ 索引管理器已初始化")
        
        return st.session_state.index_manager
    except Exception as e:
        st.error(f"❌ 索引管理器初始化失败: {e}")
        logger.error(f"索引管理器初始化失败: {e}", exc_info=True)
        return None


def load_chat_manager():
    """加载或创建对话管理器"""
    try:
        if st.session_state.chat_manager is None:
            if not st.session_state.collection_name:
                raise ValueError("未登录或 collection_name 未设置，请先登录")
            
            index_manager = load_index()
            if not index_manager:
                raise ValueError("索引管理器未初始化")
            
            with st.spinner("🔧 初始化对话管理器..."):
                st.session_state.chat_manager = ChatManager(
                    index_manager=index_manager,
                    user_email=st.session_state.user_email,
                    enable_debug=st.session_state.get('debug_mode_enabled', False),
                    enable_markdown_formatting=True,
                )
                st.success("✅ 对话管理器已初始化")
        
        return st.session_state.chat_manager
    except ValueError as e:
        st.error(f"❌ 请先设置DEEPSEEK_API_KEY环境变量")
        st.info("💡 提示：在项目根目录创建.env文件，添加：DEEPSEEK_API_KEY=your_api_key")
        return None
    except Exception as e:
        st.error(f"❌ 对话管理器初始化失败: {e}")
        return None


class HybridQueryEngineWrapper:
    """混合查询引擎包装器（兼容层）
    
    用于向后兼容load_hybrid_query_engine接口
    内部使用RAGService
    """
    
    def __init__(self, rag_service: RAGService, enable_wikipedia: bool = False):
        """初始化包装器
        
        Args:
            rag_service: RAGService实例
            enable_wikipedia: 是否启用Wikipedia增强（暂不支持）
        """
        self.rag_service = rag_service
        self.enable_wikipedia = enable_wikipedia
    
    def query(self, question: str):
        """执行查询
        
        Args:
            question: 查询问题
            
        Returns:
            tuple: (answer, local_sources, wikipedia_sources)
                - answer: 回答文本
                - local_sources: 本地来源列表
                - wikipedia_sources: Wikipedia来源列表（暂不支持，返回空列表）
        """
        # 使用RAGService查询
        response = self.rag_service.query(question)
        
        # 返回兼容格式
        # TODO: 如果未来需要Wikipedia增强，可以在这里集成
        wikipedia_sources = []  # 暂不支持Wikipedia增强
        
        return response.answer, response.sources, wikipedia_sources


def load_hybrid_query_engine():
    """加载混合查询引擎（向后兼容）
    
    返回一个兼容旧接口的查询引擎包装器
    内部使用RAGService
    
    Returns:
        Optional[HybridQueryEngineWrapper]: 查询引擎包装器，失败返回None
    """
    try:
        # 加载RAGService
        rag_service = load_rag_service()
        if not rag_service:
            return None
        
        # 检查是否启用Wikipedia增强
        enable_wikipedia = st.session_state.get('enable_wikipedia', False)
        
        # 创建包装器
        wrapper = HybridQueryEngineWrapper(
            rag_service=rag_service,
            enable_wikipedia=enable_wikipedia,
        )
        
        return wrapper
    except Exception as e:
        logger.error(f"加载混合查询引擎失败: {e}", exc_info=True)
        return None
