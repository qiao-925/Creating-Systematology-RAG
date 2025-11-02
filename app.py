"""
Streamlit Web应用 - 主页
系统科学知识库RAG应用的Web界面
"""

import streamlit as st
from pathlib import Path
from typing import Optional
import sys
import time
import atexit
import signal
import logging

# 抑制OpenTelemetry导出器的错误日志（避免连接失败时的噪音）
# 这些错误通常是 transient 的，不影响应用功能
logging.getLogger('opentelemetry.sdk.trace.export').setLevel(logging.WARNING)
logging.getLogger('opentelemetry.exporter.otlp').setLevel(logging.WARNING)
logging.getLogger('opentelemetry.exporter.otlp.proto.grpc').setLevel(logging.WARNING)

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent))

# 优先设置 UTF-8 编码（确保 emoji 正确显示）
try:
    from src.encoding import setup_utf8_encoding
    setup_utf8_encoding()
except ImportError:
    # 如果 encoding 模块尚未加载，手动设置基础编码
    import os
    os.environ["PYTHONIOENCODING"] = "utf-8"

from src.config import config
from src.ui_components import (
    init_session_state,
    preload_embedding_model,
    load_rag_service,
    load_index,
    load_chat_manager,
    display_hybrid_sources,
    display_model_status,
    format_answer_with_citation_links,
    display_sources_with_anchors,
    display_sources_right_panel
)
from src.phoenix_utils import (
    is_phoenix_running,
    start_phoenix_ui,
    stop_phoenix_ui,
    get_phoenix_url,
)
from src.query_engine import format_sources
from llama_index.core import Document as LlamaDocument
from src.logger import setup_logger

logger = setup_logger('app')


def cleanup_resources():
    """清理应用资源，关闭 Chroma 客户端和后台线程
    
    这个函数会在应用退出时被调用，确保 Chroma 的后台线程被正确终止
    """
    try:
        import logging
        log = logging.getLogger('app')
        log.info("🔧 开始清理应用资源...")
        
        # 清理 IndexManager（关闭 Chroma 客户端）
        # 注意：在 Streamlit 中，session_state 可能不可用，所以需要 try-except
        try:
            if hasattr(st, 'session_state') and 'index_manager' in st.session_state:
                index_manager = st.session_state.get('index_manager')
                if index_manager:
                    try:
                        index_manager.close()
                        log.info("✅ 索引管理器已清理")
                    except Exception as e:
                        log.warning(f"⚠️  清理索引管理器时出错: {e}")
        except Exception as e:
            # Streamlit session_state 可能在某些情况下不可用
            log.debug(f"无法访问 session_state: {e}")
        
        # 尝试清理全局资源
        try:
            # 清理全局的 Embedding 模型（如果需要）
            from src.indexer import clear_embedding_model_cache
            clear_embedding_model_cache()
            log.debug("✅ 全局模型缓存已清理")
        except Exception as e:
            log.debug(f"清理全局模型缓存时出错: {e}")
        
        log.info("✅ 应用资源清理完成")
    except Exception as e:
        # 使用 print 作为最后的备选方案
        print(f"❌ 清理资源时发生错误: {e}")


def signal_handler(signum, frame):
    """信号处理器，用于处理 Ctrl+C 等中断信号"""
    try:
        logger.info(f"📡 收到信号 {signum}，开始清理资源...")
    except:
        print(f"📡 收到信号 {signum}，开始清理资源...")
    cleanup_resources()
    sys.exit(0)


# 注册退出钩子（在所有情况下都会执行）
atexit.register(cleanup_resources)

# 注册信号处理器（Windows 和 Unix 都支持）
try:
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # 终止信号
except (ValueError, OSError) as e:
    # Windows 上可能不支持某些信号，忽略错误
    logger.debug(f"无法注册信号处理器: {e}")


# 页面配置
st.set_page_config(
    page_title="主页",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


def display_trace_info(trace_info: dict):
    """显示查询追踪信息
    
    Args:
        trace_info: 追踪信息字典
    """
    if not trace_info:
        return
    
    with st.expander("📊 查询追踪信息", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("总耗时", f"{trace_info.get('total_time', 0)}s")
        
        with col2:
            retrieval_info = trace_info.get('retrieval', {})
            st.metric("检索耗时", f"{retrieval_info.get('time_cost', 0)}s")
        
        with col3:
            st.metric("召回数量", retrieval_info.get('chunks_retrieved', 0))
        
        st.divider()
        
        # 检索详情
        st.markdown("**🔍 检索详情**")
        col1, col2 = st.columns(2)
        with col1:
            st.text(f"Top K: {retrieval_info.get('top_k', 0)}")
            st.text(f"平均相似度: {retrieval_info.get('avg_score', 0)}")
        
        with col2:
            llm_info = trace_info.get('llm_generation', {})
            st.text(f"LLM模型: {llm_info.get('model', 'N/A')}")
            st.text(f"回答长度: {llm_info.get('response_length', 0)} 字符")


def get_chat_title(messages: list) -> Optional[str]:
    """从第一个用户消息中提取标题
    
    Args:
        messages: 消息列表
        
    Returns:
        标题字符串，如果没有用户消息则返回None
    """
    if not messages:
        return None
    
    # 找到第一个用户消息
    for message in messages:
        if message.get("role") == "user":
            content = message.get("content", "")
            if content:
                # 截取前50个字符作为标题
                title = content[:50].strip()
                # 如果超过50个字符，添加省略号
                if len(content) > 50:
                    title += "..."
                return title
    
    return None


def sidebar():
    """侧边栏 - 精简版，只保留核心功能"""
    with st.sidebar:
        # ========== 应用标题区域 ==========
        st.title("📚 " + config.APP_TITLE)
        st.caption("基于LlamaIndex和DeepSeek的系统科学知识问答系统")
        
        # ========== 新对话（顶部） ==========
        if st.button("💬 开启新对话", type="primary", use_container_width=True, key="new_chat_top"):
            if st.session_state.chat_manager:
                st.session_state.chat_manager.start_session()
                st.session_state.messages = []
                # 清空引用来源映射，避免右侧显示上一个对话的引用来源
                if 'current_sources_map' in st.session_state:
                    st.session_state.current_sources_map = {}
                st.success("✅ 新会话已开始")
                st.rerun()

        # ========== 历史会话（紧随新对话按钮） ==========
        current_session_id = None
        if st.session_state.chat_manager and st.session_state.chat_manager.current_session:
            current_session_id = st.session_state.chat_manager.current_session.session_id
        from src.ui_components import display_session_history
        display_session_history(st.session_state.user_email, current_session_id)
        
        
        # ========== 用户信息区域 ==========
        col1, col2 = st.columns([3, 1])
        with col1:
            st.caption(f"👤 {st.session_state.user_email}")
        with col2:
            if st.button("🚪", key="logout_btn_sidebar", help="退出登录"):
                st.session_state.logged_in = False
                st.session_state.user_email = None
                st.session_state.collection_name = None
                st.session_state.index_manager = None
                st.session_state.chat_manager = None
                st.session_state.messages = []
                st.session_state.index_built = False
                st.rerun()
        
        
        # ========== 系统状态（包含调试日志） ==========
        st.divider()
        with st.expander("🔧 系统状态", expanded=False):
            # Embedding模型状态
            display_model_status()
            
            st.divider()
            
            # 调试/日志（Phoenix）
            st.markdown("#### 🐛 调试 / 日志")
            if is_phoenix_running():
                st.success("Phoenix 已运行")
                url = get_phoenix_url()
                st.markdown(f"**访问：** [{url}]({url})")
            else:
                if st.button("🚀 启动Phoenix", type="primary", use_container_width=True):
                    start_phoenix_ui()
                    st.rerun()
        
        # 保留其他功能区
        
        # 本地文档导入已移至 设置页 > 数据源管理 > 数据导入
        
        # 会话管理旧入口与更多功能入口已移除


def main():
    """主界面"""
    # ========== Claude风格CSS样式 ==========
    st.markdown("""
    <style>
    /* ============================================================
       Claude风格设计系统 - 极简优雅
       ============================================================ */
    
    /* 全局字体和配色 */
    :root {
        --color-bg-primary: #FFFFFF;
        --color-bg-sidebar: #FFFFFF;
        --color-bg-card: #FFFFFF;
        --color-bg-hover: #F5F5F5;
        --color-text-primary: #2C2C2C;
        --color-text-secondary: #6B6B6B;
        --color-accent: #2563EB;
        --color-accent-hover: #1D4ED8;
        --color-border: #E5E5E0;
        --color-border-light: #F0F0EB;
    }
    
    /* 全局字体 - 衬线字体增强可读性 */
    .stApp {
        font-family: "Noto Serif SC", "Source Han Serif SC", "Georgia", "Times New Roman", serif;
        background-color: var(--color-bg-primary);
        color: var(--color-text-primary);
    }
    
    /* 顶部区域 - 改为温暖米色 */
    .stApp > header {
        background-color: var(--color-bg-primary) !important;
    }
    
    /* 底部区域 - 改为温暖米色 */
    .stApp > footer {
        background-color: var(--color-bg-primary) !important;
    }
    
    /* 主内容区域背景 */
    .main .block-container {
        background-color: var(--color-bg-primary);
    }
    
    /* 主内容区域 */
    .main .block-container {
        padding-top: 2.5rem;
        padding-bottom: 3rem;
        max-width: 100%;
    }
    
    /* 正文字体大小和行高 */
    p, div, span {
        font-size: 16px;
        line-height: 1.7;
    }
    
    /* 标题层级 - 优雅的字重和间距 */
    h1 {
        font-size: 2rem;
        font-weight: 600;
        letter-spacing: -0.02em;
        color: var(--color-text-primary);
        margin-bottom: 0.75rem;
    }
    
    h2 {
        font-size: 1.5rem;
        font-weight: 600;
        letter-spacing: -0.01em;
        color: var(--color-text-primary);
        margin-bottom: 0.5rem;
    }
    
    h3 {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--color-text-primary);
        margin-bottom: 0.5rem;
    }
    
    /* 侧边栏 - 温暖的米色背景 */
    [data-testid="stSidebar"] {
        background-color: var(--color-bg-sidebar);
        border-right: 1px solid var(--color-border);
        width: 280px !important;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        font-size: 0.9rem;
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        color: var(--color-text-primary);
    }
    
    /* 消息容器 - 紧凑间距 */
    .stChatMessage {
        padding: 1.0rem 1.25rem;
        border-radius: 12px;
        margin-bottom: 0.9rem;
        border: none;
        box-shadow: none;
        background-color: var(--color-bg-card);
    }
    
    /* 用户消息 - 浅米色背景 */
    .stChatMessage[data-testid="user-message"] {
        background-color: var(--color-bg-hover);
    }
    
    /* AI消息 - 温暖米色背景 */
    .stChatMessage[data-testid="assistant-message"] {
        background-color: var(--color-bg-primary);
    }
    
    /* 消息内容文字 */
    [data-testid="stChatMessageContent"] {
        font-size: 16px;
        line-height: 1.7;
        color: var(--color-text-primary);
    }
    
    /* 按钮 - 温暖的强调色 */
    .stButton button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease;
        border: none;
        box-shadow: none;
        font-family: inherit;
    }
    
    /* 主要按钮 */
    .stButton button[kind="primary"] {
        background-color: var(--color-accent);
        color: white;
        border: none;
    }
    
    .stButton button[kind="primary"]:hover {
        background-color: var(--color-accent-hover);
        transform: none;
        box-shadow: none;
    }
    
    /* 次要按钮 */
    .stButton button[kind="secondary"] {
        background-color: transparent;
        border: 1px solid var(--color-border);
        color: var(--color-text-primary);
    }
    
    .stButton button[kind="secondary"]:hover {
        background-color: var(--color-bg-hover);
        border-color: var(--color-border);
    }
    
    /* 侧边栏历史记录按钮：单行显示 + 超出省略 */
    [data-testid="stSidebar"] .stButton button {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    /* 侧边栏历史记录按钮：去边框框线，紧凑间距 */
    [data-testid="stSidebar"] .stButton button[kind="secondary"] {
        border: none;
        box-shadow: none;
        background: transparent;
        padding: 0.35rem 0.4rem;
        margin: 0.1rem 0;
    }

    [data-testid="stSidebar"] .stButton button[kind="secondary"]:hover {
        background-color: var(--color-bg-hover);
        border: none;
    }

    /* 保持顶部主要按钮的可点击性和视觉权重 */
    [data-testid="stSidebar"] .stButton button[kind="primary"] {
        padding: 0.55rem 0.75rem;
    }
    
    /* 输入框 - 简洁边框，使用温暖米色背景 */
    .stTextInput input, 
    .stTextArea textarea,
    .stChatInput textarea {
        border-radius: 10px;
        border: 1px solid var(--color-border);
        padding: 0.75rem 1rem;
        background-color: var(--color-bg-primary);
        font-size: 16px;
        font-family: inherit;
        color: var(--color-text-primary);
        min-height: 48px;
        resize: none;
    }
    
    .stTextInput input:focus, 
    .stTextArea textarea:focus,
    .stChatInput textarea:focus {
        border-color: var(--color-accent);
        box-shadow: 0 0 0 1px var(--color-accent);
        outline: none;
    }
    
    /* 聊天输入框居中 + 提升观感 */
    .stChatInput {
        max-width: 900px !important;
        margin: 0 auto !important;
    }
    
    [data-testid="stChatInput"] {
        max-width: 900px !important;
        margin: 0 auto !important;
        background: var(--color-bg-card);
        border: 1px solid var(--color-border);
        border-radius: 12px;
        padding: 0.5rem 0.75rem;
        box-shadow: 0 6px 24px rgba(0,0,0,0.06);
        backdrop-filter: saturate(180%) blur(4px);
    }
    
    /* 发送按钮样式 */
    [data-testid="stChatInput"] button {
        background-color: var(--color-accent) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.5rem 0.9rem !important;
    }
    
    [data-testid="stChatInput"] button:hover {
        background-color: var(--color-accent-hover) !important;
    }
    
    /* 展开器 - 极简设计，使用温暖米色 */
    .streamlit-expanderHeader {
        background-color: var(--color-bg-primary);
        border-radius: 8px;
        padding: 0.75rem 1rem;
        border: 1px solid var(--color-border-light);
        transition: all 0.2s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background-color: var(--color-bg-hover);
        border-color: var(--color-border);
    }
    
    .streamlit-expanderContent {
        background-color: var(--color-bg-primary);
        border: none;
        padding: 1rem;
    }
    
    /* 分隔线 */
    hr {
        margin: 1.5rem 0;
        border: none;
        border-top: 1px solid var(--color-border);
    }
    
    /* 提示文字 */
    .stCaption {
        color: var(--color-text-secondary);
        font-size: 0.875rem;
        line-height: 1.5;
    }
    
    /* 指标卡片 */
    [data-testid="stMetric"] {
        background-color: var(--color-bg-card);
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid var(--color-border-light);
        box-shadow: none;
    }
    
    [data-testid="stMetric"] label {
        color: var(--color-text-secondary);
        font-size: 0.875rem;
    }
    
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: var(--color-text-primary);
        font-weight: 600;
    }
    
    /* 提示消息 - 使用温暖米色背景 */
    .stSuccess, .stError, .stInfo, .stWarning {
        border-radius: 8px;
        padding: 1rem;
        border: 1px solid var(--color-border);
    }
    
    .stInfo {
        background-color: var(--color-bg-primary);
        border-color: var(--color-border);
    }
    
    /* 代码块 */
    code {
        font-family: "JetBrains Mono", "Fira Code", "Courier New", monospace;
        background-color: var(--color-bg-hover);
        padding: 0.2em 0.4em;
        border-radius: 4px;
        font-size: 0.9em;
    }
    
    pre code {
        padding: 1rem;
        border-radius: 8px;
    }
    
    /* 滚动条 - 柔和样式 */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--color-bg-primary);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--color-border);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--color-text-secondary);
    }
    
    /* 选项卡 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        border-bottom: 1px solid var(--color-border);
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 0.75rem 1.5rem;
        color: var(--color-text-secondary);
        border: none;
        background-color: transparent;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: var(--color-bg-hover);
        color: var(--color-text-primary);
    }
    
    .stTabs [aria-selected="true"] {
        background-color: var(--color-bg-card);
        color: var(--color-accent);
        border-bottom: 2px solid var(--color-accent);
    }
    
    /* 文件上传器 */
    [data-testid="stFileUploader"] {
        border: 1px dashed var(--color-border);
        border-radius: 8px;
        padding: 1.5rem;
        background-color: var(--color-bg-card);
    }
    
    /* 下拉选择框 */
    .stSelectbox [data-baseweb="select"] {
        border-radius: 8px;
        border: 1px solid var(--color-border);
    }
    
    /* Spinner加载动画 */
    .stSpinner > div {
        border-top-color: var(--color-accent) !important;
    }
    
    /* 引用链接样式 */
    a[href^="#citation_"] {
        color: var(--color-accent) !important;
        text-decoration: none !important;
        font-weight: 500 !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
        padding: 0.1em 0.2em !important;
        border-radius: 3px !important;
        background-color: rgba(37, 99, 235, 0.1) !important;
    }
    
    a[href^="#citation_"]:hover {
        background-color: rgba(37, 99, 235, 0.2) !important;
        color: var(--color-accent-hover) !important;
        text-decoration: underline !important;
    }
    
    /* 引用锚点高亮效果 */
    [id^="citation_"] {
        transition: background-color 0.3s ease !important;
        border-radius: 4px !important;
        padding: 0.25rem 0.5rem !important;
        margin: -0.25rem -0.5rem !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 初始化会话状态（需早于重型初始化，用于控制遮罩）
    init_session_state()
    
    # ========== 启动初始化 ==========
    if not st.session_state.boot_ready:
        # 启动阶段：执行重型初始化
        try:
            preload_embedding_model()
        except Exception:
            # 错误已在函数内部显示
            pass
        try:
            if not is_phoenix_running():
                session = start_phoenix_ui(port=6006)
                if session is None:
                    st.error("❌ Phoenix 启动失败：请确认已安装 arize-phoenix 与 openinference-instrumentation-llama-index，并检查端口 6006 是否被占用。")
        except Exception as e:
            st.error(f"❌ Phoenix 启动异常：{e}")
        # 启动画面完成 -> 标记并刷新
        st.session_state.boot_ready = True
        st.rerun()
        return
    
    # 启动阶段已处理 Phoenix 与模型加载；此处无需再拉起
    
    # 用户认证界面
    if not st.session_state.logged_in:
        st.title("🔐 用户登录")
        
        tab1, tab2 = st.tabs(["登录", "注册"])
        
        with tab1:
            st.subheader("登录")
            email = st.text_input("邮箱", key="login_email")
            password = st.text_input("密码", type="password", key="login_password")
            
            if st.button("登录", type="primary"):
                if not email or not password:
                    st.error("请填写邮箱和密码")
                else:
                    collection = st.session_state.user_manager.login(email, password)
                    if collection:
                        st.session_state.logged_in = True
                        st.session_state.user_email = email
                        st.session_state.collection_name = collection
                        st.success("登录成功！")
                        st.rerun()
                    else:
                        st.error("邮箱或密码错误")
        
        with tab2:
            st.subheader("注册")
            email = st.text_input("邮箱", key="register_email", placeholder="user@example.com")
            password = st.text_input("密码", type="password", key="register_password")
            password_confirm = st.text_input("确认密码", type="password", key="register_password_confirm")
            
            if st.button("注册", type="primary"):
                if not email or not password:
                    st.error("请填写邮箱和密码")
                elif password != password_confirm:
                    st.error("两次密码不一致")
                elif len(password) < 6:
                    st.error("密码长度至少6位")
                else:
                    if st.session_state.user_manager.register(email, password):
                        st.success("注册成功！请登录")
                    else:
                        st.error("该邮箱已注册")
        
        st.divider()
        
        st.stop()  # 未登录则停止，不显示后续内容
    
    # 已登录，显示侧边栏
    sidebar()
    
    # 初始化RAG服务（新架构推荐）
    rag_service = load_rag_service()
    if not rag_service:
        st.error("❌ RAG服务初始化失败")
        return
    
    # 初始化对话管理器（用于会话管理和历史记录）
    chat_manager = load_chat_manager()
    if not chat_manager:
        st.error("❌ 对话管理器初始化失败")
        return
    
    # 辅助函数：使用RAGService执行查询
    def execute_query_with_rag_service(query: str, user_id: str = None, session_id: str = None):
        """使用RAGService执行查询
        
        Returns:
            tuple: (answer, sources, wikipedia_sources)
                - answer: 回答文本
                - sources: 本地来源列表
                - wikipedia_sources: Wikipedia来源列表（当前为空，待后续集成）
        """
        try:
            # 使用RAGService查询
            response = rag_service.query(
                question=query,
                user_id=user_id or st.session_state.user_email,
                session_id=session_id or (chat_manager.current_session.session_id if chat_manager.current_session else None),
            )
            
            # 返回兼容格式
            # TODO: 如果未来需要Wikipedia增强，可以在这里集成
            wikipedia_sources = []  # 暂不支持Wikipedia增强
            
            return response.answer, response.sources, wikipedia_sources
        except Exception as e:
            logger.error(f"RAGService查询失败: {e}", exc_info=True)
            raise
    
    # ========== 处理历史会话加载 ==========
    if 'load_session_id' in st.session_state and st.session_state.load_session_id:
        from src.chat_manager import load_session_from_file
        
        # 加载历史会话
        session_path = st.session_state.load_session_path
        loaded_session = load_session_from_file(session_path)
        
        if loaded_session:
            # 将历史会话设置为当前会话
            chat_manager.current_session = loaded_session
            
            # 将会话历史转换为messages格式
            st.session_state.messages = []
            # 清空引用来源映射，避免显示上一个对话的引用来源
            st.session_state.current_sources_map = {}
            
            for idx, turn in enumerate(loaded_session.history):
                # 用户消息
                st.session_state.messages.append({
                    "role": "user",
                    "content": turn.question
                })
                # AI回复
                assistant_msg = {
                    "role": "assistant",
                    "content": turn.answer,
                    "sources": turn.sources
                }
                st.session_state.messages.append(assistant_msg)
                
                # 如果有引用来源，存储到current_sources_map
                if turn.sources:
                    message_id = f"msg_{len(st.session_state.messages)-1}_{hash(str(assistant_msg))}"
                    st.session_state.current_sources_map[message_id] = turn.sources
            
            st.success(f"✅ 已加载会话: {loaded_session.title}")
        else:
            st.error("❌ 加载会话失败")
        
        # 清除加载标记
        del st.session_state.load_session_id
        del st.session_state.load_session_path
        st.rerun()
    
    # ========== 显示常驻标题（基于第一个用户问题，居中显示） ==========
    chat_title = get_chat_title(st.session_state.messages)
    if chat_title:
        st.markdown(f"<div style='text-align: center;'><h3>{chat_title}</h3></div>", unsafe_allow_html=True)
        st.markdown("---")
    
    # 存储当前消息的引用来源（用于右侧显示）
    if 'current_sources_map' not in st.session_state:
        st.session_state.current_sources_map = {}
    current_sources_map = st.session_state.current_sources_map
    
    # 检查是否有引用来源（用于决定是否显示右侧面板）
    def has_sources():
        """检查是否有非空的引用来源"""
        if not current_sources_map:
            return False
        for sources in current_sources_map.values():
            if sources:  # 只要有一个非空的引用来源列表，就返回True
                return True
        return False
    
    # ========== 主内容区域：根据是否有引用来源决定布局 ==========
    has_ref_sources = has_sources()
    
    if has_ref_sources:
        # 有引用来源：左右分栏布局（左-对话，右-引用来源）
        main_left, main_right = st.columns([3, 2])
    else:
        # 无引用来源：左侧全宽，不显示右侧面板
        main_left = st.container()
        main_right = None
    
    with main_left:
        # 显示对话历史
        for idx, message in enumerate(st.session_state.messages):
            message_id = f"msg_{idx}_{hash(str(message))}"
            with st.chat_message(message["role"]):
                # 如果是AI回答且包含引用，使用带链接的格式
                if message["role"] == "assistant" and "sources" in message and message["sources"]:
                    formatted_content = format_answer_with_citation_links(
                        message["content"],
                        message["sources"],
                        message_id=message_id
                    )
                    st.markdown(formatted_content, unsafe_allow_html=True)
                    # 存储引用来源用于右侧显示
                    current_sources_map[message_id] = message["sources"]
                else:
                    st.markdown(message["content"])
                    # 如果是AI回答但没有引用，存储空列表
                    if message["role"] == "assistant":
                        current_sources_map[message_id] = []
            
            # 更新session_state中的映射
            st.session_state.current_sources_map = current_sources_map
        
        # 默认问题快捷按钮（仅在无对话历史时显示）
        if not st.session_state.messages:
            st.markdown("### 💡 快速开始")
            st.caption("点击下方问题快速体验")
            
            default_questions = [
                "什么是系统科学？它的核心思想是什么？",
                "钱学森对系统科学有哪些贡献？",
                "从定性到定量的综合集成法如何与马克思主义哲学结合起来理解？",
                "系统工程在现代科学中的应用有哪些？"
            ]
            
            # 使用两列布局展示问题按钮
            col1, col2 = st.columns(2)
            for idx, question in enumerate(default_questions):
                col = col1 if idx % 2 == 0 else col2
                with col:
                    if st.button(f"💬 {question}", key=f"default_q_{idx}", use_container_width=True):
                        # 将问题设置为用户输入
                        st.session_state.selected_question = question
                        st.rerun()
            
            st.divider()
        
        # 处理默认问题的点击（在居中区域内处理）
        if 'selected_question' in st.session_state and st.session_state.selected_question:
            prompt = st.session_state.selected_question
            st.session_state.selected_question = None  # 清除状态
            
            # 显示用户消息
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # 生成回答
            with st.chat_message("assistant"):
                with st.spinner("🤔 思考中..."):
                    try:
                        # 初始化变量，避免作用域问题
                        message_id = None
                        answer = ""
                        sources = []
                        
                        # 使用RAGService执行查询（新架构）
                        answer, local_sources, wikipedia_sources = execute_query_with_rag_service(
                            query=prompt,
                            user_id=st.session_state.user_email,
                            session_id=chat_manager.current_session.session_id if chat_manager.current_session else None,
                        )
                        
                        # 生成消息ID
                        msg_idx = len(st.session_state.messages)
                        message_id = f"msg_{msg_idx}_{hash(str(answer))}"
                        
                        # 合并本地和维基百科来源用于右侧显示
                        all_sources_for_display = local_sources + [
                            {**s, 'index': len(local_sources) + i + 1} 
                            for i, s in enumerate(wikipedia_sources)
                        ]
                        
                        # 如果有引用，使用带链接的格式
                        if all_sources_for_display:
                            formatted_answer = format_answer_with_citation_links(
                                answer,
                                all_sources_for_display,
                                message_id=message_id
                            )
                            st.markdown(formatted_answer, unsafe_allow_html=True)
                            # 存储引用来源用于右侧显示
                            current_sources_map[message_id] = all_sources_for_display
                        else:
                            if answer:  # 只在有答案时显示
                                st.markdown(answer)
                            current_sources_map[message_id] = []
                        
                        # 更新session_state
                        st.session_state.current_sources_map = current_sources_map
                        
                        # 保存到消息历史（UI显示用）
                        if answer:  # 只在有答案时保存
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": answer,
                                "sources": local_sources,
                                "wikipedia_sources": wikipedia_sources
                            })
                        
                        # 同时保存到ChatManager会话（持久化）
                        if chat_manager and answer:
                            # 合并所有来源用于保存
                            all_sources = local_sources + [
                                {**s, 'source_type': 'wikipedia'} 
                                for s in wikipedia_sources
                            ]
                            # 如果没有当前会话，先创建一个
                            if not chat_manager.current_session:
                                chat_manager.start_session()
                            # 保存对话
                            chat_manager.current_session.add_turn(prompt, answer, all_sources)
                            # 自动保存
                            if chat_manager.auto_save:
                                chat_manager.save_current_session()
                        
                        st.rerun()  # 刷新页面显示新消息
                        
                    except Exception as e:
                        import traceback
                        st.error(f"❌ 查询失败: {e}")
                        st.error(traceback.format_exc())
    
    # 右侧：引用来源展示区域（仅在存在引用来源时显示）
    if main_right is not None:
        with main_right:
            st.markdown("#### 📚 引用来源")
            
            # 找到最新的有引用的消息
            latest_message_id = None
            latest_sources = []
            for msg_id, sources in reversed(list(current_sources_map.items())):
                if sources:
                    latest_message_id = msg_id
                    latest_sources = sources
                    break
            
            if latest_sources:
                # 在右侧显示引用来源
                display_sources_right_panel(
                    latest_sources,
                    message_id=latest_message_id,
                    container=main_right
                )

    # 用户输入（底部全宽，视觉居中）
    prompt = st.chat_input("请输入您的问题...")
    if prompt:
        # 显示用户消息
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # 生成回答
        with st.chat_message("assistant"):
            with st.spinner("🤔 思考中..."):
                try:
                    # 使用RAGService执行查询（新架构）
                    answer, local_sources, wikipedia_sources = execute_query_with_rag_service(
                        query=prompt,
                        user_id=st.session_state.user_email,
                        session_id=chat_manager.current_session.session_id if chat_manager.current_session else None,
                    )
                    
                    # 生成消息ID
                    msg_idx = len(st.session_state.messages)
                    message_id = f"msg_{msg_idx}_{hash(str(answer))}"
                    
                    # 合并本地和维基百科来源用于右侧显示
                    all_sources_for_display = local_sources + [
                        {**s, 'index': len(local_sources) + i + 1} 
                        for i, s in enumerate(wikipedia_sources)
                    ]
                    
                    # 如果有引用，使用带链接的格式
                    if all_sources_for_display:
                        formatted_answer = format_answer_with_citation_links(
                            answer,
                            all_sources_for_display,
                            message_id=message_id
                        )
                        st.markdown(formatted_answer, unsafe_allow_html=True)
                        # 存储引用来源用于右侧显示
                        current_sources_map[message_id] = all_sources_for_display
                    else:
                        if answer:  # 只在有答案时显示
                            st.markdown(answer)
                        current_sources_map[message_id] = []
                    
                    # 更新session_state
                    st.session_state.current_sources_map = current_sources_map
                    
                    # 保存到消息历史（UI显示用）
                    if answer:  # 只在有答案时保存
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": answer,
                            "sources": local_sources,
                            "wikipedia_sources": wikipedia_sources
                        })
                    
                    # 同时保存到ChatManager会话（持久化）
                    if chat_manager and answer:
                        all_sources = local_sources + [
                            {**s, 'source_type': 'wikipedia'} 
                            for s in wikipedia_sources
                        ]
                        if not chat_manager.current_session:
                            chat_manager.start_session()
                        chat_manager.current_session.add_turn(prompt, answer, all_sources)
                        if chat_manager.auto_save:
                            chat_manager.save_current_session()
                    
                    st.rerun()  # 刷新页面显示新消息
                except Exception as e:
                    import traceback
                    st.error(f"❌ 查询失败: {e}")
                    st.error(traceback.format_exc())


if __name__ == "__main__":
    main()

