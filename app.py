"""
Streamlit Web应用 - 主页
系统科学知识库RAG应用的Web界面
"""

import streamlit as st
from pathlib import Path
from typing import Optional
import sys

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.config import config
from src.ui_components import (
    init_session_state,
    preload_embedding_model,
    load_index,
    load_chat_manager,
    load_hybrid_query_engine,
    display_hybrid_sources,
    display_model_status
)
from src.query_engine import format_sources
from llama_index.core import Document as LlamaDocument


# 页面配置
st.set_page_config(
    page_title=config.APP_TITLE,
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


def sidebar():
    """侧边栏 - 精简版，只保留核心功能"""
    with st.sidebar:
        st.title("📚 快速操作")
        
        # 显示索引状态
        st.subheader("📊 索引状态")
        if st.session_state.index_manager:
            stats = st.session_state.index_manager.get_stats()
            if stats:
                st.metric("文档数量", stats.get('document_count', 0))
                st.caption(f"模型: {stats.get('embedding_model', 'N/A')}")
        else:
            st.info("索引尚未初始化")
        
        st.divider()
        
        # ========== 本地文档上传 ==========
        st.subheader("📁 本地文档")
        uploaded_files = st.file_uploader(
            "选择文件",
            type=['md', 'markdown', 'txt', 'rst', 'pdf', 'docx', 'json', 'csv', 'py', 'js', 'ts', 'java', 'cpp', 'c', 'h'],
            accept_multiple_files=True,
            help="支持多种格式：Markdown、文本、PDF、Word、代码等"
        )
        
        if uploaded_files and st.button("📥 导入", type="primary", use_container_width=True):
            index_manager = load_index()
            if index_manager:
                with st.spinner(f"正在处理 {len(uploaded_files)} 个文件..."):
                    try:
                        documents = []
                        for file in uploaded_files:
                            content = file.read().decode('utf-8')
                            doc = LlamaDocument(
                                text=content,
                                metadata={
                                    'file_name': file.name,
                                    'source_type': 'upload',
                                }
                            )
                            documents.append(doc)
                        
                        _, _ = index_manager.build_index(documents)
                        st.session_state.index_built = True
                        st.success(f"✅ 成功导入 {len(documents)} 个文档")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ 导入失败: {e}")
        
        st.divider()
        
        # ========== 会话管理 ==========
        st.subheader("💬 会话管理")
        if st.button("🆕 新会话", use_container_width=True):
            if st.session_state.chat_manager:
                st.session_state.chat_manager.start_session()
                st.session_state.messages = []
                st.success("✅ 新会话已开始")
                st.rerun()
        
        st.caption("💡 会话自动保存，无需手动操作")
        
        st.divider()
        
        # ========== 历史会话 ==========
        st.subheader("📜 历史会话")
        
        # 获取当前会话ID
        current_session_id = None
        if st.session_state.chat_manager and st.session_state.chat_manager.current_session:
            current_session_id = st.session_state.chat_manager.current_session.session_id
        
        # 显示历史会话列表（按时间分组）
        from src.ui_components import display_session_history
        display_session_history(st.session_state.user_email, current_session_id)
        
        st.divider()
        
        # ========== 进入设置页 ==========
        st.subheader("⚙️ 更多功能")
        st.caption("更多数据源、配置和调试工具")
        if st.button("🔧 打开设置页面", type="secondary", use_container_width=True):
            st.switch_page("pages/1_⚙️_设置.py")


def main():
    """主界面"""
    # ========== 自定义CSS样式 ==========
    st.markdown("""
    <style>
    /* 全局样式优化 */
    .stApp {
        max-width: 100%;
        background-color: #ffffff;
    }
    
    /* 主内容区域 */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* 消息容器样式优化 */
    .stChatMessage {
        padding: 1.2rem 1.5rem;
        border-radius: 0.75rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    
    /* 用户消息样式 */
    [data-testid="stChatMessageContent"] {
        font-size: 0.95rem;
        line-height: 1.6;
    }
    
    /* 侧边栏优化 */
    [data-testid="stSidebar"] {
        background-color: #fafafa;
        border-right: 1px solid #e5e7eb;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        font-size: 0.9rem;
    }
    
    /* 按钮样式优化 */
    .stButton button {
        border-radius: 0.5rem;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    /* 主要按钮（会话项）样式 */
    .stButton button[kind="primary"] {
        background-color: #dbeafe;
        border-left: 3px solid #3b82f6;
        color: #1e40af;
    }
    
    .stButton button[kind="secondary"] {
        background-color: #f9fafb;
        border: 1px solid #e5e7eb;
    }
    
    .stButton button[kind="secondary"]:hover {
        background-color: #f3f4f6;
        border-color: #d1d5db;
    }
    
    /* 输入框样式 */
    .stTextInput input, .stChatInput textarea {
        border-radius: 0.5rem;
        border: 1px solid #e5e7eb;
        padding: 0.75rem 1rem;
    }
    
    .stTextInput input:focus, .stChatInput textarea:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
    
    /* 聊天输入框居中 - 强制居中布局 */
    .stChatInput {
        max-width: 80% !important;
        margin: 0 auto !important;
        display: block !important;
    }
    
    /* 输入框容器居中 */
    [data-testid="stChatInput"] {
        max-width: 80% !important;
        margin: 0 auto !important;
    }
    
    /* 展开器样式 */
    .streamlit-expanderHeader {
        background-color: #f9fafb;
        border-radius: 0.5rem;
        padding: 0.75rem 1rem;
        border: 1px solid #e5e7eb;
    }
    
    .streamlit-expanderHeader:hover {
        background-color: #f3f4f6;
    }
    
    /* 分隔线样式 */
    hr {
        margin: 1.5rem 0;
        border-color: #e5e7eb;
    }
    
    /* 标题样式 */
    h1, h2, h3 {
        font-weight: 600;
        letter-spacing: -0.02em;
    }
    
    /* 提示文字样式 */
    .stCaption {
        color: #6b7280;
        font-size: 0.875rem;
    }
    
    /* 指标卡片样式 */
    [data-testid="stMetric"] {
        background-color: #f9fafb;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e5e7eb;
    }
    
    /* 成功/错误/信息提示样式 */
    .stSuccess, .stError, .stInfo, .stWarning {
        border-radius: 0.5rem;
        padding: 1rem;
    }
    
    /* 滚动条样式 */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #c1c1c1;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #a8a8a8;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 预加载 Embedding 模型（全局，应用启动时就加载）
    preload_embedding_model()
    
    # 初始化会话状态
    init_session_state()
    
    # 用户认证界面
    if not st.session_state.logged_in:
        st.title("🔐 用户登录")
        st.caption("简单的用户管理（仅用于反馈收集）")
        
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
        
        st.info("💡 提示：这是简单的演示用户系统，仅用于数据隔离和反馈收集")
        
        st.stop()  # 未登录则停止，不显示后续内容
    
    # 已登录，显示侧边栏
    sidebar()
    
    # 主标题
    st.title(config.APP_TITLE)
    st.caption("基于LlamaIndex和DeepSeek的系统科学知识问答系统")
    
    # 显示用户信息
    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption(f"👤 当前用户: {st.session_state.user_email}")
    with col2:
        if st.button("退出登录", key="logout_btn"):
            st.session_state.logged_in = False
            st.session_state.user_email = None
            st.session_state.collection_name = None
            st.session_state.index_manager = None
            st.session_state.chat_manager = None
            st.session_state.messages = []
            st.session_state.index_built = False
            st.rerun()
    
    # 显示知识库状态提示
    if not st.session_state.index_built:
        st.info("💡 当前为纯对话模式，导入文档后可获得知识增强")
    
    # 初始化对话管理器（无论是否有索引都可以初始化）
    chat_manager = load_chat_manager()
    if not chat_manager:
        st.error("❌ 对话管理器初始化失败")
        return
    
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
            for turn in loaded_session.history:
                # 用户消息
                st.session_state.messages.append({
                    "role": "user",
                    "content": turn.question
                })
                # AI回复
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": turn.answer,
                    "sources": turn.sources
                })
            
            st.success(f"✅ 已加载会话: {loaded_session.title}")
        else:
            st.error("❌ 加载会话失败")
        
        # 清除加载标记
        del st.session_state.load_session_id
        del st.session_state.load_session_path
        st.rerun()
    
    # ========== 主内容区域居中布局 ==========
    # 创建三列布局，中间列为主要内容区域
    left_spacer, main_content, right_spacer = st.columns([1, 8, 1])
    
    with main_content:
        # 显示对话历史
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # 显示引用来源（支持混合查询）
                if message["role"] == "assistant":
                    if "wikipedia_sources" in message and message["wikipedia_sources"]:
                        # 混合查询结果 - 分区展示
                        display_hybrid_sources(
                            message.get("sources", []),
                            message.get("wikipedia_sources", [])
                        )
                    elif "sources" in message:
                        # 普通查询结果
                        if message["sources"]:
                            with st.expander("📚 查看引用来源"):
                                for source in message["sources"]:
                                    st.markdown(f"**[{source['index']}] {source['metadata'].get('title', source['metadata'].get('file_name', 'Unknown'))}**")
                                    if source['score']:
                                        st.caption(f"相似度: {source['score']:.2f}")
                                    st.text(source['text'][:300] + "..." if len(source['text']) > 300 else source['text'])
                                    st.divider()
        
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
                        # 判断使用哪种查询模式
                        if st.session_state.enable_wikipedia:
                            # 混合查询模式（维基百科增强）
                            hybrid_engine = load_hybrid_query_engine()
                            if hybrid_engine:
                                answer, local_sources, wikipedia_sources = hybrid_engine.query(prompt)
                                st.markdown(answer)
                                
                                # 分区显示来源
                                display_hybrid_sources(local_sources, wikipedia_sources)
                                
                                # 保存到消息历史（UI显示用）
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": answer,
                                    "sources": local_sources,
                                    "wikipedia_sources": wikipedia_sources
                                })
                                
                                # 同时保存到ChatManager会话（持久化）
                                if chat_manager:
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
                            else:
                                st.error("混合查询引擎初始化失败")
                        else:
                            # 普通对话模式
                            answer, sources = chat_manager.chat(prompt)
                            st.markdown(answer)
                            
                            # 显示引用来源
                            if sources:
                                with st.expander("📚 查看引用来源", expanded=True):
                                    for source in sources:
                                        st.markdown(f"**[{source['index']}] {source['metadata'].get('title', source['metadata'].get('file_name', 'Unknown'))}**")
                                        if source['score']:
                                            st.caption(f"相似度: {source['score']:.2f}")
                                        st.text(source['text'][:300] + "..." if len(source['text']) > 300 else source['text'])
                                        st.divider()
                            
                            # 保存到消息历史
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": answer,
                                "sources": sources
                            })
                        
                        st.rerun()  # 刷新页面显示新消息
                        
                    except Exception as e:
                        import traceback
                        st.error(f"❌ 查询失败: {e}")
                        st.error(traceback.format_exc())
    
    # 用户输入（chat_input 无法放入 columns，但通过 CSS 居中）
    if prompt := st.chat_input("请输入您的问题..."):
        # 创建居中布局来显示新消息
        _, center_col, _ = st.columns([1, 8, 1])
        
        with center_col:
            # 显示用户消息
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # 生成回答
            with st.chat_message("assistant"):
                with st.spinner("🤔 思考中..."):
                    try:
                        # 判断使用哪种查询模式
                        if st.session_state.enable_wikipedia:
                            # 混合查询模式（维基百科增强）
                            hybrid_engine = load_hybrid_query_engine()
                            if hybrid_engine:
                                answer, local_sources, wikipedia_sources = hybrid_engine.query(prompt)
                                st.markdown(answer)
                                
                                # 分区显示来源
                                display_hybrid_sources(local_sources, wikipedia_sources)
                                
                                # 保存到消息历史（UI显示用）
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": answer,
                                    "sources": local_sources,
                                    "wikipedia_sources": wikipedia_sources
                                })
                                
                                # 同时保存到ChatManager会话（持久化）
                                if chat_manager:
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
                            else:
                                st.error("混合查询引擎初始化失败")
                        else:
                            # 普通对话模式
                            answer, sources = chat_manager.chat(prompt)
                            st.markdown(answer)
                            
                            # 显示引用来源
                            if sources:
                                with st.expander("📚 查看引用来源", expanded=True):
                                    for source in sources:
                                        st.markdown(f"**[{source['index']}] {source['metadata'].get('title', source['metadata'].get('file_name', 'Unknown'))}**")
                                        if source['score']:
                                            st.caption(f"相似度: {source['score']:.2f}")
                                        st.text(source['text'][:300] + "..." if len(source['text']) > 300 else source['text'])
                                        st.divider()
                            
                            # 保存到消息历史
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": answer,
                                "sources": sources
                            })
                        
                    except Exception as e:
                        import traceback
                        st.error(f"❌ 查询失败: {e}")
                        st.error(traceback.format_exc())


if __name__ == "__main__":
    main()

