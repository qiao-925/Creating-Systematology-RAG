"""
设置页面
提供详细的配置选项：数据源管理、查询配置、开发者工具、系统设置
"""

import streamlit as st
from pathlib import Path
import sys

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import config
from src.ui_components import (
    init_session_state, 
    preload_embedding_model, 
    load_index,
    display_model_status
)
from src.data_loader import (
    load_documents_from_urls,
    load_documents_from_github,
    parse_github_url,
    sync_github_repository
)
from src.phoenix_utils import (
    start_phoenix_ui, 
    stop_phoenix_ui, 
    is_phoenix_running, 
    get_phoenix_url
)


# 页面配置
st.set_page_config(
    page_title="设置 - " + config.APP_TITLE,
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ========== Claude风格CSS样式（与主页保持一致） ==========
st.markdown("""
<style>
/* ============================================================
   Claude风格设计系统 - 极简优雅
   ============================================================ */

/* 全局字体和配色 */
:root {
    --color-bg-primary: #F5F5F0;
    --color-bg-sidebar: #EEEEE9;
    --color-bg-card: #FFFFFF;
    --color-bg-hover: #F9F9F6;
    --color-text-primary: #2C2C2C;
    --color-text-secondary: #6B6B6B;
    --color-accent: #D97706;
    --color-accent-hover: #B45309;
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

/* 输入框 - 简洁边框，使用温暖米色背景 */
.stTextInput input, 
.stTextArea textarea {
    border-radius: 10px;
    border: 1px solid var(--color-border);
    padding: 0.75rem 1rem;
    background-color: var(--color-bg-primary);
    font-size: 16px;
    font-family: inherit;
    color: var(--color-text-primary);
}

.stTextInput input:focus, 
.stTextArea textarea:focus {
    border-color: var(--color-accent);
    box-shadow: 0 0 0 1px var(--color-accent);
    outline: none;
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

/* Checkbox */
.stCheckbox {
    color: var(--color-text-primary);
}

/* Spinner加载动画 */
.stSpinner > div {
    border-top-color: var(--color-accent) !important;
}
</style>
""", unsafe_allow_html=True)

# 预加载模型和初始化状态
preload_embedding_model()
init_session_state()

# 检查登录状态
if not st.session_state.logged_in:
    st.warning("⚠️ 请先在主页登录")
    st.stop()

# 页面标题
st.title("⚙️ 系统设置")
st.caption(f"当前用户: {st.session_state.user_email}")

# 开启新对话按钮 - 居中显示
col1, col2, col3 = st.columns([2, 3, 2])
with col2:
    if st.button("💬 开启新对话", type="primary", use_container_width=True):
        if st.session_state.chat_manager:
            st.session_state.chat_manager.start_session()
            st.session_state.messages = []
            st.success("✅ 新会话已开始")
            # 跳转回主页
            st.switch_page("app.py")

st.divider()

# 面包屑导航
st.markdown("📍 主页 > 设置")
st.divider()

# 创建标签页
tab1, tab2, tab3, tab4 = st.tabs([
    "📦 数据源管理",
    "🔧 查询配置",
    "🐛 开发者工具",
    "⚙️ 系统设置"
])

# ==================== Tab1: 数据源管理 ====================
with tab1:
    st.header("📦 数据源管理")
    st.caption("配置和管理各种数据源")
    
    # ========== 1. GitHub 仓库管理 ==========
    st.subheader("🐙 GitHub 仓库管理")
    st.info("ℹ️ 仅支持公开仓库")
    
    # --- 添加新仓库 ---
    st.markdown("**添加新仓库**")
    github_url = st.text_input(
        "GitHub 仓库 URL",
        placeholder="https://github.com/owner/repo",
        key="github_url_settings",
        help="粘贴完整的 GitHub 仓库链接"
    )
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("➕ 添加仓库", type="primary", use_container_width=True):
            if not github_url or not github_url.strip():
                st.error("❌ 请输入 GitHub 仓库 URL")
            else:
                repo_info = parse_github_url(github_url.strip())
                if not repo_info:
                    st.error("❌ 无效的 GitHub URL")
                else:
                    github_owner = repo_info['owner']
                    github_repo = repo_info['repo']
                    github_branch = repo_info.get('branch', 'main')
                    
                    if st.session_state.metadata_manager.has_repository(github_owner, github_repo, github_branch):
                        st.warning(f"⚠️ 仓库已存在")
                    else:
                        index_manager = load_index()
                        if index_manager:
                            with st.spinner(f"正在索引 {github_owner}/{github_repo}..."):
                                try:
                                    documents, changes, commit_sha = sync_github_repository(
                                        owner=github_owner,
                                        repo=github_repo,
                                        branch=github_branch,
                                        metadata_manager=st.session_state.metadata_manager,
                                        show_progress=True
                                    )
                                    
                                    if documents:
                                        index, vector_ids_map = index_manager.build_index(documents, show_progress=True)
                                        st.session_state.metadata_manager.update_repository_metadata(
                                            owner=github_owner,
                                            repo=github_repo,
                                            branch=github_branch,
                                            documents=documents,
                                            vector_ids_map=vector_ids_map,
                                            commit_sha=commit_sha
                                        )
                                        st.session_state.github_repos = st.session_state.metadata_manager.list_repositories()
                                        st.session_state.index_built = True
                                        st.success(f"✅ 成功添加 {len(documents)} 个文件！")
                                        st.rerun()
                                    else:
                                        st.warning("⚠️ 未能加载任何文件")
                                except Exception as e:
                                    st.error(f"❌ 添加失败: {str(e)[:100]}")
    
    with col2:
        # 同步所有仓库按钮
        if st.session_state.github_repos:
            if st.button("🔄 同步", use_container_width=True, help="同步所有仓库"):
                index_manager = load_index()
                if index_manager:
                    with st.spinner("同步中..."):
                        synced = 0
                        for repo_info in st.session_state.github_repos:
                            parts = repo_info['key'].split('@')
                            repo_part = parts[0]
                            branch = parts[1] if len(parts) > 1 else 'main'
                            owner, repo_name = repo_part.split('/')
                            
                            try:
                                documents, changes, commit_sha = sync_github_repository(
                                    owner=owner,
                                    repo=repo_name,
                                    branch=branch,
                                    metadata_manager=st.session_state.metadata_manager,
                                    show_progress=False
                                )
                                
                                if changes.has_changes():
                                    added_docs, modified_docs, deleted_paths = st.session_state.metadata_manager.get_documents_by_change(
                                        documents, changes
                                    )
                                    index_manager.incremental_update(
                                        added_docs=added_docs,
                                        modified_docs=modified_docs,
                                        deleted_file_paths=deleted_paths,
                                        metadata_manager=st.session_state.metadata_manager
                                    )
                                    
                                    # 获取所有文档的向量ID（增量更新后）
                                    vector_ids_map = {}
                                    for doc in documents:
                                        file_path = doc.metadata.get("file_path", "")
                                        if file_path:
                                            vector_ids = st.session_state.metadata_manager.get_file_vector_ids(
                                                owner, repo_name, branch, file_path
                                            )
                                            vector_ids_map[file_path] = vector_ids
                                    
                                    st.session_state.metadata_manager.update_repository_metadata(
                                        owner=owner,
                                        repo=repo_name,
                                        branch=branch,
                                        documents=documents,
                                        vector_ids_map=vector_ids_map,
                                        commit_sha=commit_sha
                                    )
                                    synced += 1
                            except Exception as e:
                                st.error(f"❌ {owner}/{repo_name}: {str(e)[:80]}")
                        
                        st.session_state.github_repos = st.session_state.metadata_manager.list_repositories()
                        if synced > 0:
                            st.success(f"✅ 同步了 {synced} 个仓库")
                        else:
                            st.success("✅ 所有仓库都是最新的")
                        st.rerun()
    
    st.divider()
    
    # --- 已添加的仓库列表 ---
    st.markdown("**已添加的仓库**")
    if st.session_state.github_repos:
        st.caption(f"共 {len(st.session_state.github_repos)} 个仓库")
        
        for repo in st.session_state.github_repos:
            with st.expander(f"📦 {repo['key']}", expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.text(f"文件数量: {repo['file_count']}")
                    st.text(f"最后更新: {repo['last_indexed_at']}")
                    if 'commit_sha' in repo:
                        st.text(f"Commit: {repo['commit_sha'][:8]}")
                
                with col2:
                    if st.button("🗑️ 删除", key=f"del_{repo['key']}"):
                        parts = repo['key'].split('@')
                        repo_part = parts[0]
                        branch = parts[1] if len(parts) > 1 else 'main'
                        owner, repo_name = repo_part.split('/')
                        st.session_state.metadata_manager.remove_repository(owner, repo_name, branch)
                        st.session_state.github_repos = st.session_state.metadata_manager.list_repositories()
                        st.success(f"已删除 {repo['key']}")
                        st.rerun()
    else:
        st.info("尚未添加任何仓库")
    
    st.divider()
    
    # ========== 2. 网页URL导入 ==========
    st.subheader("🌐 从网页加载")
    url_input = st.text_area(
        "输入URL（每行一个）",
        height=100,
        placeholder="https://example.com/article1\nhttps://example.com/article2"
    )
    
    if st.button("🌍 加载网页", type="primary") and url_input:
        urls = [url.strip() for url in url_input.split('\n') if url.strip()]
        if urls:
            index_manager = load_index()
            if index_manager:
                with st.spinner(f"正在加载 {len(urls)} 个网页..."):
                    try:
                        documents = load_documents_from_urls(urls)
                        if documents:
                            _, _ = index_manager.build_index(documents)
                            st.session_state.index_built = True
                            st.success(f"✅ 成功加载 {len(documents)} 个网页")
                            st.rerun()
                        else:
                            st.warning("⚠️ 没有成功加载任何网页")
                    except Exception as e:
                        st.error(f"❌ 加载失败: {e}")
    
    st.divider()
    
    # ========== 3. 本地目录加载 ==========
    st.subheader("📂 从目录加载")
    st.caption("加载data/raw目录中的所有文档（开发/测试用）")
    
    if st.button("📖 加载data/raw目录", type="primary"):
        index_manager = load_index()
        if index_manager:
            with st.spinner("正在加载目录中的文档..."):
                try:
                    from src.data_loader import load_documents_from_directory
                    documents = load_documents_from_directory(config.RAW_DATA_PATH)
                    if documents:
                        _, _ = index_manager.build_index(documents)
                        st.session_state.index_built = True
                        st.success(f"✅ 成功加载 {len(documents)} 个文档")
                        st.rerun()
                    else:
                        st.warning("⚠️ 目录中没有找到文档")
                except Exception as e:
                    st.error(f"❌ 加载失败: {e}")
    
    st.divider()
    
    # ========== 4. 维基百科预索引 ==========
    st.subheader("🌐 维基百科预索引")
    st.caption("将维基百科页面添加到索引中，提升查询速度")
    
    wiki_concepts_input = st.text_area(
        "概念列表（每行一个）",
        value="\n".join(config.WIKIPEDIA_PRELOAD_CONCEPTS),
        height=100,
        help="输入维基百科页面标题"
    )
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        wiki_lang = st.selectbox(
            "语言",
            options=["zh", "en"],
            format_func=lambda x: "中文" if x == "zh" else "English",
            help="维基百科语言版本"
        )
    
    with col2:
        if st.button("📖 预索引", type="primary", use_container_width=True):
            concepts = [c.strip() for c in wiki_concepts_input.split('\n') if c.strip()]
            if concepts:
                index_manager = load_index()
                if index_manager:
                    with st.spinner(f"正在加载 {len(concepts)} 个维基百科页面..."):
                        try:
                            count = index_manager.preload_wikipedia_concepts(
                                concepts,
                                lang=wiki_lang,
                                show_progress=False
                            )
                            if count > 0:
                                st.session_state.index_built = True
                                st.success(f"✅ 成功索引 {count} 个维基百科页面！")
                                st.rerun()
                            else:
                                st.warning("⚠️ 未能加载任何维基百科页面")
                        except Exception as e:
                            st.error(f"❌ 加载失败: {e}")
            else:
                st.warning("请输入至少一个概念")


# ==================== Tab2: 查询配置 ====================
with tab2:
    st.header("🔧 查询配置")
    st.caption("调整查询引擎的行为参数")
    
    # ========== 维基百科增强 ==========
    st.subheader("🌐 维基百科增强")
    st.markdown("启用维基百科可以在本地结果不足时自动补充背景知识")
    
    enable_wiki = st.checkbox(
        "启用维基百科查询", 
        value=st.session_state.enable_wikipedia,
        help="查询时如果本地结果相关度不足，会自动查询维基百科补充"
    )
    st.session_state.enable_wikipedia = enable_wiki
    
    if enable_wiki:
        threshold = st.slider(
            "触发阈值",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.wikipedia_threshold,
            step=0.1,
            help="本地结果相关度低于此值时触发维基百科查询"
        )
        st.session_state.wikipedia_threshold = threshold
        
        # 重置混合查询引擎（配置改变后需要重新初始化）
        if st.button("应用配置", type="primary"):
            st.session_state.hybrid_query_engine = None
            st.success("✅ 配置已应用，下次查询时生效")
    
    st.divider()
    
    # ========== 未来扩展：检索参数调整 ==========
    st.subheader("🔍 检索参数（未来扩展）")
    st.info("ℹ️ 此部分功能将在未来版本中提供")
    
    # 预留位置
    st.text_input("相似度阈值", value=str(config.SIMILARITY_THRESHOLD), disabled=True)
    st.text_input("检索数量 (Top K)", value=str(config.SIMILARITY_TOP_K), disabled=True)


# ==================== Tab3: 开发者工具 ====================
with tab3:
    st.header("🐛 开发者工具")
    st.caption("RAG流程可观测性和调试工具")
    
    # ========== Phoenix可视化平台 ==========
    st.subheader("📊 Phoenix可视化平台")
    st.markdown("""
    **Phoenix** 是开源的LLM可观测性平台，提供：
    - 📊 实时追踪RAG查询流程
    - 🔍 向量检索可视化
    - 📈 性能分析和统计
    - 🐛 调试和问题诊断
    """)
    
    if is_phoenix_running():
        st.success(f"✅ Phoenix已启动")
        st.markdown(f"**访问地址：** [{get_phoenix_url()}]({get_phoenix_url()})")
        
        if st.button("🛑 停止Phoenix", use_container_width=True):
            stop_phoenix_ui()
            st.session_state.phoenix_enabled = False
            st.success("Phoenix已停止")
            st.rerun()
    else:
        if st.button("🚀 启动Phoenix UI", type="primary", use_container_width=True):
            with st.spinner("正在启动Phoenix..."):
                session = start_phoenix_ui(port=6006)
                if session:
                    st.session_state.phoenix_enabled = True
                    st.success("✅ Phoenix已启动！")
                    st.rerun()
                else:
                    st.error("❌ Phoenix启动失败，请检查依赖是否安装")
    
    st.divider()
    
    # ========== LlamaDebugHandler调试 ==========
    st.subheader("🐛 LlamaDebugHandler调试")
    st.markdown("""
    **LlamaDebugHandler** 是LlamaIndex内置的调试工具：
    - 📝 输出详细的执行日志
    - 🔎 显示LLM调用和检索过程
    - ⚡ 轻量级，无需额外服务
    """)
    
    debug_enabled = st.checkbox(
        "启用调试日志",
        value=st.session_state.debug_mode_enabled,
        help="在控制台输出详细的调试信息"
    )
    st.session_state.debug_mode_enabled = debug_enabled
    
    if debug_enabled:
        st.info("ℹ️ 调试日志将输出到控制台和日志文件")
        st.warning("⚠️ 配置更改后需要重新初始化对话管理器才能生效")
        
        if st.button("重新初始化对话管理器"):
            st.session_state.chat_manager = None
            st.success("✅ 对话管理器已重置，下次对话时将应用新配置")
    
    st.divider()
    
    # ========== 追踪信息收集 ==========
    st.subheader("📈 查询追踪信息")
    st.markdown("""
    收集每次查询的详细指标：
    - ⏱️ 检索时间和LLM生成时间
    - 📊 相似度分数统计
    - 📝 完整的chunk内容
    """)
    
    trace_enabled = st.checkbox(
        "启用追踪信息收集",
        value=st.session_state.collect_trace,
        help="在界面上显示详细的查询追踪信息"
    )
    st.session_state.collect_trace = trace_enabled
    
    if trace_enabled:
        st.info("ℹ️ 追踪信息将在每次查询后显示")


# ==================== Tab4: 系统设置 ====================
with tab4:
    st.header("⚙️ 系统设置")
    st.caption("系统级配置和管理操作")
    
    # ========== 索引管理 ==========
    st.subheader("🗂️ 索引管理")
    
    if st.session_state.index_manager:
        stats = st.session_state.index_manager.get_stats()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("文档数量", stats.get('document_count', 0))
        with col2:
            st.metric("分块大小", stats.get('chunk_size', 'N/A'))
        with col3:
            st.metric("分块重叠", stats.get('chunk_overlap', 'N/A'))
        
        st.divider()
        
        # 清空索引
        st.markdown("**危险操作**")
        st.warning("⚠️ 以下操作不可撤销")
        
        if st.button("🗑️ 清空索引", help="删除所有已索引的文档"):
            confirm = st.checkbox("确认清空索引")
            if confirm:
                st.session_state.index_manager.clear_index()
                st.session_state.index_built = False
                st.success("✅ 索引已清空")
                st.rerun()
    else:
        st.info("索引尚未初始化")
    
    st.divider()
    
    # ========== Embedding模型状态 ==========
    st.subheader("🔧 Embedding 模型状态")
    display_model_status()
    
    st.divider()
    
    # ========== 系统信息 ==========
    st.subheader("ℹ️ 系统信息")
    
    sys_info = {
        "应用标题": config.APP_TITLE,
        "LLM模型": config.LLM_MODEL,
        "Embedding模型": config.EMBEDDING_MODEL,
        "向量数据库": "ChromaDB",
        "HuggingFace镜像": config.HF_ENDPOINT,
        "离线模式": "是" if config.HF_OFFLINE_MODE else "否",
    }
    
    for key, value in sys_info.items():
        col1, col2 = st.columns([1, 2])
        with col1:
            st.text(key)
        with col2:
            st.code(value)

