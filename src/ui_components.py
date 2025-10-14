"""
UI共用组件模块
提供Streamlit应用中可复用的UI组件和函数
"""

import streamlit as st
from pathlib import Path
from typing import Optional

from src.config import config
from src.indexer import IndexManager, get_embedding_model_status, get_global_embed_model, load_embedding_model
from src.chat_manager import ChatManager
from src.query_engine import HybridQueryEngine


def preload_embedding_model():
    """预加载 Embedding 模型（仅加载一次）"""
    if 'embed_model' not in st.session_state:
        st.session_state.embed_model = None
    
    if 'embed_model_loaded' not in st.session_state:
        st.session_state.embed_model_loaded = False
    
    # 如果已经加载过，直接返回（检查session_state中的模型）
    if st.session_state.embed_model_loaded and st.session_state.embed_model is not None:
        # 确保全局变量也有模型引用
        from src.indexer import set_global_embed_model
        set_global_embed_model(st.session_state.embed_model)
        # 显示缓存命中信息
        st.caption(f"✅ Embedding 模型已缓存（对象ID: {id(st.session_state.embed_model)}）")
        return
    
    # 检查是否已经有全局模型
    global_model = get_global_embed_model()
    
    if global_model is None:
        # 模型未加载，开始加载
        with st.spinner(f"🚀 正在预加载 Embedding 模型 ({config.EMBEDDING_MODEL})..."):
            try:
                model = load_embedding_model()
                # 同时存储到session_state和全局变量
                st.session_state.embed_model = model
                st.session_state.embed_model_loaded = True
                st.success("✅ Embedding 模型预加载完成")
            except Exception as e:
                st.error(f"❌ 模型加载失败: {e}")
                st.stop()
    else:
        # 模型已加载（存储到session_state）
        st.session_state.embed_model = global_model
        st.session_state.embed_model_loaded = True


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
    
    # 调试模式配置
    if 'debug_mode_enabled' not in st.session_state:
        st.session_state.debug_mode_enabled = False
    
    if 'phoenix_enabled' not in st.session_state:
        st.session_state.phoenix_enabled = False
    
    if 'collect_trace' not in st.session_state:
        st.session_state.collect_trace = False


def load_index():
    """加载或创建索引"""
    try:
        if st.session_state.index_manager is None:
            # 使用用户专属的 collection
            collection_name = st.session_state.collection_name or config.CHROMA_COLLECTION_NAME
            
            # 获取预加载的模型实例
            embed_model = get_global_embed_model()
            
            with st.spinner("🔧 初始化索引管理器..."):
                # 传递预加载的模型实例，避免重复加载
                st.session_state.index_manager = IndexManager(
                    collection_name=collection_name,
                    embed_model_instance=embed_model
                )
                st.success("✅ 索引管理器已初始化")
        
        return st.session_state.index_manager
    except Exception as e:
        st.error(f"❌ 索引初始化失败: {e}")
        return None


def load_chat_manager():
    """加载或创建对话管理器"""
    try:
        # 尝试加载索引管理器（可能为空）
        index_manager = load_index() if st.session_state.index_built else None
        
        if st.session_state.chat_manager is None:
            mode_desc = "RAG增强模式" if index_manager else "纯对话模式（无知识库）"
            with st.spinner(f"🤖 初始化对话管理器 ({mode_desc})..."):
                st.session_state.chat_manager = ChatManager(
                    index_manager,
                    enable_debug=st.session_state.debug_mode_enabled,
                    user_email=st.session_state.user_email
                )
                # 不在这里创建会话，等第一次提问时再创建
                st.success(f"✅ 对话管理器已初始化 ({mode_desc})")
        
        return st.session_state.chat_manager
    except ValueError as e:
        st.error(f"❌ 请先设置DEEPSEEK_API_KEY环境变量")
        st.info("💡 提示：在项目根目录创建.env文件，添加：DEEPSEEK_API_KEY=your_api_key")
        return None
    except Exception as e:
        st.error(f"❌ 对话管理器初始化失败: {e}")
        return None


def load_hybrid_query_engine():
    """加载或创建混合查询引擎"""
    try:
        index_manager = load_index()
        if not index_manager:
            return None
        
        if st.session_state.hybrid_query_engine is None:
            with st.spinner("🔧 初始化混合查询引擎..."):
                st.session_state.hybrid_query_engine = HybridQueryEngine(
                    index_manager,
                    enable_wikipedia=st.session_state.enable_wikipedia,
                    wikipedia_threshold=st.session_state.wikipedia_threshold,
                    wikipedia_max_results=config.WIKIPEDIA_MAX_RESULTS,
                )
                st.success("✅ 混合查询引擎已初始化")
        
        return st.session_state.hybrid_query_engine
    except Exception as e:
        st.error(f"❌ 混合查询引擎初始化失败: {e}")
        return None


def display_hybrid_sources(local_sources, wikipedia_sources):
    """分区展示混合查询的来源
    
    Args:
        local_sources: 本地知识库来源列表
        wikipedia_sources: 维基百科来源列表
    """
    # 本地知识库来源
    if local_sources:
        with st.expander(f"📚 本地知识库来源 ({len(local_sources)})", expanded=True):
            for i, source in enumerate(local_sources, 1):
                title = source['metadata'].get('title', source['metadata'].get('file_name', 'Unknown'))
                st.markdown(f"**[{i}] {title}**")
                
                # 显示元数据
                metadata_parts = []
                if 'file_name' in source['metadata']:
                    metadata_parts.append(f"📁 {source['metadata']['file_name']}")
                if source.get('score') is not None:
                    metadata_parts.append(f"相似度: {source['score']:.2f}")
                if metadata_parts:
                    st.caption(" | ".join(metadata_parts))
                
                # 显示内容预览
                text_preview = source['text'][:300] if len(source['text']) > 300 else source['text']
                st.text(text_preview + ("..." if len(source['text']) > 300 else ""))
                
                if i < len(local_sources):
                    st.divider()
    
    # 维基百科来源
    if wikipedia_sources:
        with st.expander(f"🌐 维基百科补充 ({len(wikipedia_sources)})", expanded=False):
            for i, source in enumerate(wikipedia_sources, 1):
                title = source['metadata'].get('title', 'Unknown')
                st.markdown(f"**[W{i}] {title}**")
                
                # 显示维基百科链接和相似度
                wiki_url = source['metadata'].get('wikipedia_url', '#')
                metadata_parts = [f"🔗 [{wiki_url}]({wiki_url})"]
                if source.get('score') is not None:
                    metadata_parts.append(f"相似度: {source['score']:.2f}")
                st.caption(" | ".join(metadata_parts))
                
                # 显示内容预览
                text_preview = source['text'][:300] if len(source['text']) > 300 else source['text']
                st.text(text_preview + ("..." if len(source['text']) > 300 else ""))
                
                if i < len(wikipedia_sources):
                    st.divider()


def display_model_status():
    """在页面底部显示 Embedding 模型状态"""
    st.markdown("---")
    
    try:
        status = get_embedding_model_status()
        
        # 使用 expander 默认收起
        with st.expander("🔧 Embedding 模型状态", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**模型信息**")
                st.text(f"名称: {status['model_name']}")
                if status['loaded']:
                    st.success("✅ 已加载到内存")
                else:
                    st.info("💤 未加载（首次使用时加载）")
            
            with col2:
                st.markdown("**缓存状态**")
                if status['cache_exists']:
                    st.success("✅ 本地缓存存在")
                    st.caption("后续使用无需联网")
                else:
                    st.warning("⚠️  本地无缓存")
                    st.caption("首次使用将从镜像下载")
            
            with col3:
                st.markdown("**网络配置**")
                if status['offline_mode']:
                    st.info("📴 离线模式")
                    st.caption("仅使用本地缓存")
                else:
                    st.info(f"🌐 在线模式")
                    st.caption(f"镜像: {status['mirror']}")
            
            # 详细信息（可折叠）
            with st.expander("查看详细信息", expanded=False):
                st.json(status)
    
    except Exception as e:
        st.error(f"获取模型状态失败: {e}")


def group_sessions_by_time(sessions_metadata):
    """按时间分组会话
    
    Args:
        sessions_metadata: 会话元数据列表
        
    Returns:
        分组后的字典: {'今天': [...], '7天内': [...], '30天内': [...]}
    """
    from datetime import datetime, timedelta
    
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)
    
    groups = {
        '📅 今天': [],
        '📅 7天内': [],
        '📅 30天内': []
    }
    
    for session in sessions_metadata:
        try:
            # 解析更新时间
            updated_at = datetime.fromisoformat(session['updated_at'])
            
            if updated_at >= today_start:
                groups['📅 今天'].append(session)
            elif updated_at >= seven_days_ago:
                groups['📅 7天内'].append(session)
            elif updated_at >= thirty_days_ago:
                groups['📅 30天内'].append(session)
        except Exception as e:
            print(f"解析时间失败: {e}")
            continue
    
    return groups


def display_session_history(user_email: str, current_session_id: Optional[str] = None):
    """显示历史会话列表（按时间分组）
    
    Args:
        user_email: 用户邮箱
        current_session_id: 当前会话ID（用于高亮显示）
    """
    from src.chat_manager import get_user_sessions_metadata
    
    # 调试信息
    print(f"📜 [DEBUG] 正在查找用户会话: {user_email}")
    
    # 获取所有会话元数据
    sessions_metadata = get_user_sessions_metadata(user_email)
    
    print(f"📜 [DEBUG] 找到 {len(sessions_metadata)} 个会话")
    
    if not sessions_metadata:
        st.caption("暂无历史会话")
        return
    
    # 按时间分组
    grouped_sessions = group_sessions_by_time(sessions_metadata)
    
    # 显示各分组
    for group_name, sessions in grouped_sessions.items():
        if sessions:
            st.markdown(f"**{group_name}**")
            
            for session in sessions:
                # 判断是否为当前会话
                is_current = session['session_id'] == current_session_id
                
                # 创建会话按钮
                session_title = session['title'] or "新对话"
                button_label = f"{'🔵 ' if is_current else '💬 '}{session_title}"
                
                # 使用容器来实现悬停效果和点击
                if st.button(
                    button_label,
                    key=f"session_{session['session_id']}",
                    use_container_width=True,
                    type="primary" if is_current else "secondary"
                ):
                    # 点击后加载该会话
                    if not is_current:
                        st.session_state.load_session_id = session['session_id']
                        st.session_state.load_session_path = session['file_path']
                        st.rerun()
                
                # 显示会话信息
                if is_current:
                    st.caption(f"✅ 当前会话 · {session['message_count']} 条消息")
                else:
                    st.caption(f"{session['message_count']} 条消息")
            
            st.divider()

