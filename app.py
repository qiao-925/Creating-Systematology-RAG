"""
Streamlit Web应用
系统科学知识库RAG应用的Web界面
"""

import streamlit as st
from pathlib import Path
from typing import Optional
import sys

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.config import config
from src.indexer import IndexManager, create_index_from_directory
from src.chat_manager import ChatManager
from src.data_loader import load_documents_from_urls, load_documents_from_github
from src.query_engine import format_sources
from src.user_manager import UserManager


# 页面配置
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


def init_session_state():
    """初始化会话状态"""
    # 用户管理
    if 'user_manager' not in st.session_state:
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


def load_index():
    """加载或创建索引"""
    try:
        if st.session_state.index_manager is None:
            # 使用用户专属的 collection
            collection_name = st.session_state.collection_name or config.CHROMA_COLLECTION_NAME
            with st.spinner("🔧 初始化索引管理器..."):
                st.session_state.index_manager = IndexManager(collection_name=collection_name)
                st.success("✅ 索引管理器已初始化")
        
        return st.session_state.index_manager
    except Exception as e:
        st.error(f"❌ 索引初始化失败: {e}")
        return None


def load_chat_manager():
    """加载或创建对话管理器"""
    try:
        index_manager = load_index()
        if index_manager is None:
            return None
        
        if st.session_state.chat_manager is None:
            with st.spinner("🤖 初始化对话管理器..."):
                st.session_state.chat_manager = ChatManager(index_manager)
                st.session_state.chat_manager.start_session()
                st.success("✅ 对话管理器已初始化")
        
        return st.session_state.chat_manager
    except ValueError as e:
        st.error(f"❌ 请先设置DEEPSEEK_API_KEY环境变量")
        st.info("💡 提示：在项目根目录创建.env文件，添加：DEEPSEEK_API_KEY=your_api_key")
        return None
    except Exception as e:
        st.error(f"❌ 对话管理器初始化失败: {e}")
        return None


def sidebar():
    """侧边栏"""
    with st.sidebar:
        st.title("📚 文档管理")
        
        # 显示索引状态
        st.subheader("📊 索引状态")
        if st.session_state.index_manager:
            stats = st.session_state.index_manager.get_stats()
            if stats:
                st.metric("文档数量", stats.get('document_count', 0))
                st.caption(f"模型: {stats.get('embedding_model', 'N/A')}")
                st.caption(f"分块大小: {stats.get('chunk_size', 'N/A')}")
        else:
            st.info("索引尚未初始化")
        
        st.divider()
        
        # 文档上传
        st.subheader("📁 上传Markdown文档")
        uploaded_files = st.file_uploader(
            "选择文件",
            type=['md', 'markdown'],
            accept_multiple_files=True,
            help="支持批量上传Markdown文件"
        )
        
        if uploaded_files and st.button("📥 导入文档", type="primary"):
            index_manager = load_index()
            if index_manager:
                with st.spinner(f"正在处理 {len(uploaded_files)} 个文件..."):
                    try:
                        from llama_index.core import Document as LlamaDocument
                        
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
                        
                        index_manager.build_index(documents)
                        st.session_state.index_built = True
                        st.success(f"✅ 成功导入 {len(documents)} 个文档")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ 导入失败: {e}")
        
        st.divider()
        
        # 从目录加载
        st.subheader("📂 从目录加载")
        if st.button("📖 加载data/raw目录"):
            index_manager = load_index()
            if index_manager:
                with st.spinner("正在加载目录中的文档..."):
                    try:
                        from src.data_loader import load_documents_from_directory
                        documents = load_documents_from_directory(config.RAW_DATA_PATH)
                        if documents:
                            index_manager.build_index(documents)
                            st.session_state.index_built = True
                            st.success(f"✅ 成功加载 {len(documents)} 个文档")
                            st.rerun()
                        else:
                            st.warning("⚠️ 目录中没有找到文档")
                    except Exception as e:
                        st.error(f"❌ 加载失败: {e}")
        
        st.divider()
        
        # URL加载
        st.subheader("🌐 从网页加载")
        url_input = st.text_area(
            "输入URL（每行一个）",
            height=100,
            placeholder="https://example.com/article1\nhttps://example.com/article2"
        )
        
        if st.button("🌍 加载网页") and url_input:
            urls = [url.strip() for url in url_input.split('\n') if url.strip()]
            if urls:
                index_manager = load_index()
                if index_manager:
                    with st.spinner(f"正在加载 {len(urls)} 个网页..."):
                        try:
                            documents = load_documents_from_urls(urls)
                            if documents:
                                index_manager.build_index(documents)
                                st.session_state.index_built = True
                                st.success(f"✅ 成功加载 {len(documents)} 个网页")
                                st.rerun()
                            else:
                                st.warning("⚠️ 没有成功加载任何网页")
                        except Exception as e:
                            st.error(f"❌ 加载失败: {e}")
        
        st.divider()
        
        # GitHub 导入
        with st.expander("📦 从 GitHub 导入", expanded=False):
            github_owner = st.text_input("仓库所有者", placeholder="microsoft", key="github_owner")
            github_repo = st.text_input("仓库名称", placeholder="TypeScript", key="github_repo")
            github_branch = st.text_input("分支", value="main", key="github_branch")
            github_token = st.text_input(
                "Token（可选）", 
                type="password", 
                help="私有仓库需要提供",
                key="github_token"
            )
            
            if st.button("📥 导入 GitHub 仓库", key="import_github_btn"):
                if not github_owner or not github_repo:
                    st.error("请填写仓库所有者和名称")
                else:
                    index_manager = load_index()
                    if index_manager:
                        with st.spinner(f"正在从 GitHub 加载 {github_owner}/{github_repo}..."):
                            try:
                                documents = load_documents_from_github(
                                    owner=github_owner,
                                    repo=github_repo,
                                    branch=github_branch,
                                    github_token=github_token if github_token else None,
                                    show_progress=False  # Streamlit 不需要控制台进度条
                                )
                                
                                if documents:
                                    index_manager.build_index(documents, show_progress=False)
                                    st.session_state.index_built = True
                                    st.success(f"✅ 成功导入 {len(documents)} 个文件！")
                                    st.rerun()
                                else:
                                    st.warning("⚠️ 未能加载任何文件")
                            except Exception as e:
                                st.error(f"❌ 导入失败: {e}")
        
        st.divider()
        
        # 会话管理
        st.subheader("💬 会话管理")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🆕 新会话"):
                if st.session_state.chat_manager:
                    st.session_state.chat_manager.start_session()
                    st.session_state.messages = []
                    st.success("✅ 新会话已开始")
                    st.rerun()
        
        with col2:
            if st.button("💾 保存"):
                if st.session_state.chat_manager:
                    st.session_state.chat_manager.save_current_session()
                    st.success("✅ 会话已保存")
        
        st.divider()
        
        # 清空索引
        st.subheader("⚙️ 高级操作")
        if st.button("🗑️ 清空索引", help="删除所有已索引的文档"):
            if st.session_state.index_manager:
                if st.checkbox("确认清空索引"):
                    st.session_state.index_manager.clear_index()
                    st.session_state.index_built = False
                    st.success("✅ 索引已清空")
                    st.rerun()


def main():
    """主界面"""
    init_session_state()
    
    # 用户认证界面
    if not st.session_state.logged_in:
        st.title("🔐 用户登录")
        st.caption("简单的用户管理（仅用于反馈收集）")
        
        tab1, tab2 = st.tabs(["登录", "注册"])
        
        with tab1:
            st.subheader("登录")
            email = st.text_input("邮箱", key="login_email", placeholder="user@example.com")
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
    
    # 检查索引状态
    if not st.session_state.index_built:
        st.info("👈 请先在左侧侧边栏上传文档或从目录加载文档")
        
        # 显示快速开始指南
        with st.expander("📖 快速开始指南"):
            st.markdown("""
            ### 使用步骤
            
            1. **准备API密钥**
               - 在项目根目录创建 `.env` 文件
               - 添加：`DEEPSEEK_API_KEY=your_api_key_here`
            
            2. **加载文档**
               - 上传Markdown文件，或
               - 将文档放在 `data/raw/` 目录，点击"加载data/raw目录"，或
               - 输入网页URL，或
               - 从 GitHub 仓库导入
            
            3. **开始对话**
               - 在下方输入框提问
               - 支持多轮对话和追问
               - 每个回答都会显示引用来源
            
            ### 功能特性
            
            - ✅ **引用溯源**：每个答案都标注来源文档
            - ✅ **多轮对话**：支持上下文追问
            - ✅ **会话保存**：可以保存和恢复对话历史
            - ✅ **多种数据源**：Markdown文件、网页内容、GitHub仓库
            - ✅ **用户隔离**：每个用户独立的知识库
            """)
        return
    
    # 初始化对话管理器
    chat_manager = load_chat_manager()
    if not chat_manager:
        return
    
    # 显示对话历史
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # 显示引用来源
            if message["role"] == "assistant" and "sources" in message:
                with st.expander("📚 查看引用来源"):
                    for source in message["sources"]:
                        st.markdown(f"**[{source['index']}] {source['metadata'].get('title', source['metadata'].get('file_name', 'Unknown'))}**")
                        if source['score']:
                            st.caption(f"相似度: {source['score']:.2f}")
                        st.text(source['text'][:300] + "..." if len(source['text']) > 300 else source['text'])
                        st.divider()
    
    # 用户输入
    if prompt := st.chat_input("请输入您的问题..."):
        # 显示用户消息
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # 生成回答
        with st.chat_message("assistant"):
            with st.spinner("🤔 思考中..."):
                try:
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
                    st.error(f"❌ 查询失败: {e}")


if __name__ == "__main__":
    main()

