"""
UI组件 - 加载函数模块：加载模型、索引、服务等

主要功能：
- preload_embedding_model()：预加载Embedding模型
- load_rag_service()：加载RAG服务
- load_index()：加载索引管理器
- load_chat_manager()：加载对话管理器
- load_hybrid_query_engine()：加载混合查询引擎

执行流程：
1. 检查是否已加载
2. 创建或获取服务实例
3. 缓存到session_state
4. 返回服务实例

特性：
- 延迟加载机制
- 单例模式缓存
- 完整的错误处理
- 进度显示
"""

import streamlit as st
from typing import Optional, Any

from src.infrastructure.config import config
from src.infrastructure.indexer import IndexManager
from src.infrastructure.embeddings.factory import create_embedding, get_embedding_instance
from src.business.chat import ChatManager
from src.business.rag_api import RAGService
from src.infrastructure.logger import get_logger

logger = get_logger('ui_components')


def preload_embedding_model() -> None:
    """预加载 Embedding 模型（仅加载一次）
    
    根据配置的 EMBEDDING_TYPE 创建合适的 Embedding 实例：
    - local: 本地 HuggingFace 模型
    - hf-inference: Hugging Face Inference API
    """
    if 'embed_model' not in st.session_state:
        st.session_state.embed_model = None
    
    if 'embed_model_loaded' not in st.session_state:
        st.session_state.embed_model_loaded = False
    
    # 如果已经加载过，直接返回
    if st.session_state.embed_model_loaded and st.session_state.embed_model is not None:
        return
    
    # 检查工厂函数是否已有缓存的实例
    cached_instance = get_embedding_instance()
    
    if cached_instance is not None:
        # 使用工厂函数缓存的实例
        logger.info(f"✅ 使用工厂函数缓存的 Embedding 实例: {type(cached_instance).__name__}")
        st.session_state.embed_model = cached_instance
        st.session_state.embed_model_loaded = True
        return
    
    # 创建新的 Embedding 实例（根据配置自动选择类型）
    embedding_type = config.EMBEDDING_TYPE
    model_name = config.EMBEDDING_MODEL
    
    # 根据类型显示不同的加载提示
    if embedding_type == "hf-inference":
        spinner_text = f"📡 正在连接 Hugging Face Inference API ({model_name})..."
        success_text = "✅ Hugging Face Inference API 连接成功"
    else:
        spinner_text = f"🚀 正在预加载 Embedding 模型 ({model_name})..."
        success_text = "✅ Embedding 模型预加载完成"
    
    with st.spinner(spinner_text):
        try:
            # 使用工厂函数创建 Embedding 实例（会根据 EMBEDDING_TYPE 自动选择类型）
            embedding_instance = create_embedding()
            st.session_state.embed_model = embedding_instance
            st.session_state.embed_model_loaded = True
            logger.info(f"✅ Embedding 实例创建成功: {type(embedding_instance).__name__}")
        except Exception as e:
            error_msg = f"❌ Embedding 加载失败: {e}"
            st.error(error_msg)
            logger.error(error_msg, exc_info=True)
            st.stop()


def load_rag_service(force_validate: bool = False) -> Optional[RAGService]:
    """加载或创建RAG服务（新架构推荐）
    
    Args:
        force_validate: 是否强制验证服务有效性（默认使用缓存结果）
    
    Returns:
        Optional[RAGService]: RAG服务实例，失败返回None
    """
    try:
        # 使用默认collection（从config读取）
        collection_name = st.session_state.get('collection_name') or config.CHROMA_COLLECTION_NAME
        
        # 检查是否需要验证（首次加载或强制验证）
        need_validate = (
            force_validate or 
            st.session_state.get('force_validate_services', False) or
            not st.session_state.get('rag_service_validated', False)
        )
        
        # 检查缓存的 RAGService 是否有效（仅在需要时验证）
        if st.session_state.rag_service is not None and need_validate:
            try:
                # 尝试获取统计信息，如果集合不存在会抛出异常
                stats = st.session_state.rag_service.index_manager.get_stats()
                # 如果返回的错误信息表明集合不存在，清理缓存
                if stats.get('error') and ('不存在' in stats.get('error') or '已删除' in stats.get('error')):
                    logger.warning(f"⚠️  检测到集合不存在，清理 RAGService 缓存")
                    st.session_state.rag_service = None
                    st.session_state.rag_service_validated = False
                    # 同时清理相关的 index_manager 缓存
                    if 'index_manager' in st.session_state:
                        st.session_state.index_manager = None
                        st.session_state.index_manager_validated = False
                else:
                    # 验证成功，标记为已验证
                    st.session_state.rag_service_validated = True
                    logger.debug("✅ RAGService 验证通过，使用缓存")
            except Exception as e:
                # 如果访问失败，可能是集合已被删除，清理缓存
                error_str = str(e).lower()
                if 'not found' in error_str or 'soft deleted' in error_str or 'collection' in error_str:
                    logger.warning(f"⚠️  检测到集合访问失败，清理 RAGService 缓存: {e}")
                    st.session_state.rag_service = None
                    st.session_state.rag_service_validated = False
                    if 'index_manager' in st.session_state:
                        st.session_state.index_manager = None
                        st.session_state.index_manager_validated = False
                else:
                    # 其他异常，可能是临时网络问题，保留缓存但标记为未验证
                    logger.warning(f"⚠️  RAGService 验证时出现异常（保留缓存）: {e}")
                    st.session_state.rag_service_validated = False
        elif st.session_state.rag_service is not None:
            # 已有缓存且已验证，直接使用
            logger.debug("✅ 使用已验证的 RAGService 缓存")
        
        # 如果缓存为空或已被清理，重新创建
        if st.session_state.rag_service is None:
            with st.spinner("🔧 初始化RAG服务..."):
                st.session_state.rag_service = RAGService(
                    collection_name=collection_name,
                    enable_debug=st.session_state.get('debug_mode_enabled', False),
                    enable_markdown_formatting=True,
                )
                # 新创建的服务标记为已验证（刚创建肯定是有效的）
                st.session_state.rag_service_validated = True
                logger.info("✅ RAG服务已初始化")
        
        # 清除强制验证标志
        if st.session_state.get('force_validate_services', False):
            st.session_state.force_validate_services = False
        
        return st.session_state.rag_service
    except Exception as e:
        st.error(f"❌ RAG服务初始化失败: {e}")
        logger.error(f"RAG服务初始化失败: {e}", exc_info=True)
        return None


def load_index(force_validate: bool = False) -> Optional[IndexManager]:
    """加载或创建索引
    
    Args:
        force_validate: 是否强制验证索引管理器有效性（默认使用缓存结果）
    """
    try:
        # 使用默认collection（从config读取）
        collection_name = st.session_state.get('collection_name') or config.CHROMA_COLLECTION_NAME
        
        # 检查是否需要验证（首次加载或强制验证）
        need_validate = (
            force_validate or 
            st.session_state.get('force_validate_services', False) or
            not st.session_state.get('index_manager_validated', False)
        )
        
        # 检查缓存的 IndexManager 是否有效（仅在需要时验证）
        if st.session_state.index_manager is not None and need_validate:
            try:
                # 尝试获取统计信息，如果集合不存在会抛出异常
                stats = st.session_state.index_manager.get_stats()
                # 如果返回的错误信息表明集合不存在，清理缓存
                if stats.get('error') and ('不存在' in stats.get('error') or '已删除' in stats.get('error')):
                    logger.warning(f"⚠️  检测到集合不存在，清理 IndexManager 缓存")
                    st.session_state.index_manager = None
                    st.session_state.index_manager_validated = False
                else:
                    # 验证成功，标记为已验证
                    st.session_state.index_manager_validated = True
                    logger.debug("✅ IndexManager 验证通过，使用缓存")
            except Exception as e:
                # 如果访问失败，可能是集合已被删除，清理缓存
                error_str = str(e).lower()
                if 'not found' in error_str or 'soft deleted' in error_str or 'collection' in error_str:
                    logger.warning(f"⚠️  检测到集合访问失败，清理 IndexManager 缓存: {e}")
                    st.session_state.index_manager = None
                    st.session_state.index_manager_validated = False
                else:
                    # 其他异常，可能是临时网络问题，保留缓存但标记为未验证
                    logger.warning(f"⚠️  IndexManager 验证时出现异常（保留缓存）: {e}")
                    st.session_state.index_manager_validated = False
        elif st.session_state.index_manager is not None:
            # 已有缓存且已验证，直接使用
            logger.debug("✅ 使用已验证的 IndexManager 缓存")
        
        # 如果缓存为空或已被清理，重新创建
        if st.session_state.index_manager is None:
            # 确保 embedding 实例已加载
            embedding_instance = st.session_state.get('embed_model')
            if embedding_instance is None:
                # 如果未加载，尝试从工厂函数获取或创建
                cached_instance = get_embedding_instance()
                if cached_instance is not None:
                    embedding_instance = cached_instance
                    st.session_state.embed_model = cached_instance
                    logger.info(f"✅ 从工厂函数获取 Embedding 实例: {type(cached_instance).__name__}")
                else:
                    # 如果工厂函数也没有，创建新实例
                    logger.info(f"📦 创建新的 Embedding 实例（类型: {config.EMBEDDING_TYPE}）")
                    embedding_instance = create_embedding()
                    st.session_state.embed_model = embedding_instance
            
            with st.spinner("🔧 初始化索引管理器..."):
                st.session_state.index_manager = IndexManager(
                    collection_name=collection_name,
                    embedding_instance=embedding_instance
                )
                # 新创建的索引管理器标记为已验证
                st.session_state.index_manager_validated = True
                logger.info("✅ 索引管理器已初始化")
        
        return st.session_state.index_manager
    except Exception as e:
        st.error(f"❌ 索引管理器初始化失败: {e}")
        logger.error(f"索引管理器初始化失败: {e}", exc_info=True)
        return None


def load_chat_manager() -> Optional[ChatManager]:
    """加载或创建对话管理器"""
    try:
        if st.session_state.chat_manager is None:
            index_manager = load_index()
            if not index_manager:
                error_msg = "索引管理器未初始化，请先构建索引"
                logger.error(error_msg)
                st.error(f"❌ {error_msg}")
                st.info("💡 提示：请先在'设置'页面构建索引，或检查索引管理器初始化是否成功")
                return None
            
            with st.spinner("🔧 初始化对话管理器..."):
                try:
                    st.session_state.chat_manager = ChatManager(
                        index_manager=index_manager,
                        user_email=None,  # 单用户模式，不需要用户标识
                        enable_debug=st.session_state.get('debug_mode_enabled', False),
                        enable_markdown_formatting=True,
                    )
                    logger.info("✅ 对话管理器已初始化")
                except ValueError as e:
                    error_str = str(e)
                    if "DEEPSEEK_API_KEY" in error_str or "未设置" in error_str:
                        logger.error(f"对话管理器初始化失败: {e}", exc_info=True)
                        st.error(f"❌ 请先设置DEEPSEEK_API_KEY环境变量")
                        st.info("💡 提示：在项目根目录创建.env文件，添加：DEEPSEEK_API_KEY=your_api_key")
                    else:
                        logger.error(f"对话管理器初始化失败: {e}", exc_info=True)
                        st.error(f"❌ 对话管理器初始化失败: {e}")
                    return None
        
        return st.session_state.chat_manager
    except Exception as e:
        logger.error(f"对话管理器初始化失败: {e}", exc_info=True)
        st.error(f"❌ 对话管理器初始化失败: {e}")
        return None


class HybridQueryEngineWrapper:
    """混合查询引擎包装器（兼容层）
    
    兼容 load_hybrid_query_engine 接口
    内部使用RAGService
    """
    
    def __init__(self, rag_service: RAGService):
        """初始化包装器
        
        Args:
            rag_service: RAGService实例
        """
        self.rag_service = rag_service
    
    def query(self, question: str):
        """执行查询
        
        Args:
            question: 查询问题
            
        Returns:
            tuple: (answer, sources)
                - answer: 回答文本
                - sources: 来源列表
        """
        # 使用RAGService查询
        response = self.rag_service.query(question)
        
        return response.answer, response.sources


def load_hybrid_query_engine() -> Optional[Any]:
    """加载混合查询引擎
    
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
        
        # 创建包装器
        wrapper = HybridQueryEngineWrapper(rag_service=rag_service)
        
        return wrapper
    except Exception as e:
        logger.error(f"加载混合查询引擎失败: {e}", exc_info=True)
        return None


def invalidate_service_cache() -> None:
    """使服务缓存失效，下次加载时会重新验证
    
    在以下场景调用：
    - 集合名称变更
    - 配置变更
    - 手动触发验证
    """
    st.session_state.rag_service_validated = False
    st.session_state.index_manager_validated = False
    st.session_state.force_validate_services = True
    logger.info("🔄 服务缓存已失效，下次加载时将重新验证")
