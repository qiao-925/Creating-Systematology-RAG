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
from src.data_loader import load_documents_from_urls, load_documents_from_github, load_documents_from_wikipedia
from src.query_engine import format_sources, HybridQueryEngine
from src.user_manager import UserManager


# 页面配置
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


def preload_embedding_model():
    """预加载 Embedding 模型（仅加载一次）"""
    if 'embed_model_loaded' not in st.session_state:
        st.session_state.embed_model_loaded = False
    
    if not st.session_state.embed_model_loaded:
        # 检查是否已经有全局模型
        from src.indexer import get_global_embed_model, load_embedding_model
        
        global_model = get_global_embed_model()
        
        if global_model is None:
            # 模型未加载，开始加载
            with st.spinner(f"🚀 正在预加载 Embedding 模型 ({config.EMBEDDING_MODEL})..."):
                try:
                    load_embedding_model()
                    st.session_state.embed_model_loaded = True
                    st.success("✅ Embedding 模型预加载完成")
                except Exception as e:
                    st.error(f"❌ 模型加载失败: {e}")
                    st.stop()
        else:
            # 模型已加载（可能是之前加载的）
            st.session_state.embed_model_loaded = True


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
    
    # 用户的 GitHub Token（每个用户独立）
    if 'user_github_token' not in st.session_state:
        st.session_state.user_github_token = ""
    
    # GitHub 增量更新相关
    if 'metadata_manager' not in st.session_state:
        from src.metadata_manager import MetadataManager
        st.session_state.metadata_manager = MetadataManager(config.GITHUB_METADATA_PATH)
    
    if 'github_repos' not in st.session_state:
        # 从元数据中加载已存在的仓库列表
        st.session_state.github_repos = st.session_state.metadata_manager.list_repositories()


def load_index():
    """加载或创建索引"""
    try:
        if st.session_state.index_manager is None:
            # 使用用户专属的 collection
            collection_name = st.session_state.collection_name or config.CHROMA_COLLECTION_NAME
            
            # 获取预加载的模型实例
            from src.indexer import get_global_embed_model
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
        
        # ========== 1. GitHub Token 配置 ==========
        with st.expander("🔑 GitHub Token 配置", expanded=False):
            st.markdown("**个人访问令牌**（每个用户独立配置）")
            st.caption("用于访问 GitHub 仓库，公开仓库必须配置")
            
            current_token = st.session_state.user_github_token
            token_display = "***" + current_token[-4:] if len(current_token) > 4 else "未配置"
            st.text(f"当前状态: {token_display}")
            
            new_token = st.text_input(
                "GitHub Token",
                value="",
                type="password",
                key="new_github_token_input",
                placeholder="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                help="访问 https://github.com/settings/tokens 获取"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 保存 Token", use_container_width=True):
                    if new_token.strip():
                        if st.session_state.user_manager.set_github_token(
                            st.session_state.user_email,
                            new_token.strip()
                        ):
                            st.session_state.user_github_token = new_token.strip()
                            st.success("✅ Token 已保存")
                            st.rerun()
                    else:
                        st.warning("请输入 Token")
            
            with col2:
                if st.button("🗑️ 清除 Token", use_container_width=True):
                    if st.session_state.user_manager.set_github_token(
                        st.session_state.user_email,
                        ""
                    ):
                        st.session_state.user_github_token = ""
                        st.success("✅ Token 已清除")
                        st.rerun()
            
            st.divider()
            
            st.markdown("**获取 Token 步骤**：")
            st.markdown("""
            1. 访问 [GitHub Settings/Tokens](https://github.com/settings/tokens)
            2. 点击 "Generate new token (classic)"
            3. 设置名称（如 "RAG App"）
            4. 权限：公开仓库无需勾选，私有仓库勾选 `repo`
            5. 生成并复制 Token，粘贴到上方输入框
            6. 点击"保存 Token"
            """)
        
        st.divider()
        
        # ========== 2. GitHub 仓库管理（增量更新）==========
        st.subheader("🐙 GitHub 仓库管理")
        
        # 显示已添加的仓库列表
        if st.session_state.github_repos:
            st.caption(f"已管理 {len(st.session_state.github_repos)} 个仓库")
            for repo in st.session_state.github_repos:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.text(f"📦 {repo['key']}")
                    st.caption(f"  {repo['file_count']} 个文件 · 最后更新: {repo['last_indexed_at'][:10]}")
                with col2:
                    if st.button("🗑️", key=f"del_{repo['key']}", help="删除仓库"):
                        parts = repo['key'].split('@')
                        repo_part = parts[0]
                        branch = parts[1] if len(parts) > 1 else 'main'
                        owner, repo_name = repo_part.split('/')
                        st.session_state.metadata_manager.remove_repository(owner, repo_name, branch)
                        st.session_state.github_repos = st.session_state.metadata_manager.list_repositories()
                        st.rerun()
        else:
            st.info("尚未添加 GitHub 仓库")
        
        st.divider()
        
        # 添加新仓库
        with st.expander("➕ 添加新仓库", expanded=False):
            st.caption("💡 直接粘贴 GitHub 仓库链接，自动解析所有信息")
            
            github_url = st.text_input(
                "GitHub 仓库 URL",
                placeholder="https://github.com/microsoft/TypeScript",
                key="github_url",
                help="粘贴完整的 GitHub 仓库链接，例如：https://github.com/owner/repo"
            )
            
            # 可选：分支名（如果 URL 中没有指定）
            github_branch_override = st.text_input(
                "分支（可选）",
                value="",
                key="github_branch_override",
                placeholder="留空则使用 main 分支，或从 URL 中解析",
                help="如果 URL 中包含分支信息（如 /tree/dev），会优先使用 URL 中的分支"
            )
            
            # 显示 Token 状态
            if st.session_state.user_github_token:
                token_preview = "***" + st.session_state.user_github_token[-4:]
                st.caption(f"✅ 使用您的 GitHub Token ({token_preview})")
            else:
                st.warning("⚠️ 未配置 Token，请先在上方 🔑 GitHub Token 配置 中保存您的 Token")
            
            if st.button("➕ 添加并同步", type="primary", use_container_width=True):
                if not github_url or not github_url.strip():
                    st.error("❌ 请输入 GitHub 仓库 URL")
                else:
                    # 解析 GitHub URL
                    from src.data_loader import parse_github_url
                    
                    repo_info = parse_github_url(github_url.strip())
                    if not repo_info:
                        st.error("❌ 无效的 GitHub URL，请检查格式")
                        st.caption("支持格式：https://github.com/owner/repo 或 https://github.com/owner/repo/tree/branch")
                    else:
                        github_owner = repo_info['owner']
                        github_repo = repo_info['repo']
                        # 使用用户指定的分支，或 URL 中的分支，或默认 main
                        github_branch = github_branch_override.strip() or repo_info.get('branch', 'main')
                        
                        st.info(f"📦 解析结果: {github_owner}/{github_repo}@{github_branch}")
                        
                        # 检查是否已存在
                        if st.session_state.metadata_manager.has_repository(github_owner, github_repo, github_branch):
                            st.warning(f"⚠️ 仓库 {github_owner}/{github_repo}@{github_branch} 已存在")
                        else:
                            # 首次添加，执行完整索引
                            index_manager = load_index()
                            if index_manager:
                                with st.spinner(f"正在首次索引 {github_owner}/{github_repo}..."):
                                    try:
                                        from src.data_loader import sync_github_repository
                                        # 使用用户保存的 token
                                        github_token = st.session_state.user_github_token or None
                                        
                                        # 加载并检测（首次会标记所有文件为新增）
                                        documents, changes = sync_github_repository(
                                            owner=github_owner,
                                            repo=github_repo,
                                            branch=github_branch,
                                            metadata_manager=st.session_state.metadata_manager,
                                            github_token=github_token,
                                            show_progress=False
                                        )
                                        
                                        if documents:
                                            # 添加到索引
                                            index_manager.build_index(documents, show_progress=False)
                                            
                                            # 更新元数据
                                            st.session_state.metadata_manager.update_repository_metadata(
                                                owner=github_owner,
                                                repo=github_repo,
                                                branch=github_branch,
                                                documents=documents
                                            )
                                            
                                            # 刷新仓库列表
                                            st.session_state.github_repos = st.session_state.metadata_manager.list_repositories()
                                            st.session_state.index_built = True
                                            
                                            st.success(f"✅ 成功添加并索引 {len(documents)} 个文件！")
                                            st.rerun()
                                        else:
                                            st.warning("⚠️ 未能加载任何文件")
                                    except Exception as e:
                                        st.error(f"❌ 添加失败: {str(e)[:150]}")
        
        st.divider()
        
        # 同步控制
        st.caption("🔄 同步控制")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 检测变更", use_container_width=True, help="检测所有仓库的变更，不更新索引"):
                if not st.session_state.github_repos:
                    st.warning("⚠️ 没有仓库可检测")
                else:
                    with st.spinner("正在检测变更..."):
                        github_token = st.session_state.user_github_token or None
                        total_changes = 0
                        
                        for repo_info in st.session_state.github_repos:
                            parts = repo_info['key'].split('@')
                            repo_part = parts[0]
                            branch = parts[1] if len(parts) > 1 else 'main'
                            owner, repo_name = repo_part.split('/')
                            
                            try:
                                from src.data_loader import sync_github_repository
                                _, changes = sync_github_repository(
                                    owner=owner,
                                    repo=repo_name,
                                    branch=branch,
                                    metadata_manager=st.session_state.metadata_manager,
                                    github_token=github_token,
                                    show_progress=False
                                )
                                
                                if changes.has_changes():
                                    st.info(f"📊 {owner}/{repo_name}: {changes.summary()}")
                                    total_changes += changes.total_count()
                            except Exception as e:
                                st.error(f"❌ {owner}/{repo_name}: {str(e)[:100]}")
                        
                        if total_changes == 0:
                            st.success("✅ 所有仓库都是最新的")
        
        with col2:
            if st.button("🔄 同步更新", type="primary", use_container_width=True, help="增量同步所有仓库并更新索引"):
                if not st.session_state.github_repos:
                    st.warning("⚠️ 没有仓库可同步")
                else:
                    index_manager = load_index()
                    if index_manager:
                        with st.spinner("正在同步仓库..."):
                            github_token = st.session_state.user_github_token or None
                            total_added = 0
                            total_modified = 0
                            total_deleted = 0
                            
                            for repo_info in st.session_state.github_repos:
                                parts = repo_info['key'].split('@')
                                repo_part = parts[0]
                                branch = parts[1] if len(parts) > 1 else 'main'
                                owner, repo_name = repo_part.split('/')
                                
                                try:
                                    from src.data_loader import sync_github_repository
                                    
                                    # 1. 检测变更
                                    documents, changes = sync_github_repository(
                                        owner=owner,
                                        repo=repo_name,
                                        branch=branch,
                                        metadata_manager=st.session_state.metadata_manager,
                                        github_token=github_token,
                                        show_progress=False
                                    )
                                    
                                    if not changes.has_changes():
                                        st.info(f"✅ {owner}/{repo_name}: 无变更")
                                        continue
                                    
                                    # 2. 执行增量更新
                                    added_docs, modified_docs, deleted_paths = st.session_state.metadata_manager.get_documents_by_change(
                                        documents, changes
                                    )
                                    
                                    update_stats = index_manager.incremental_update(
                                        added_docs=added_docs,
                                        modified_docs=modified_docs,
                                        deleted_file_paths=deleted_paths,
                                        metadata_manager=st.session_state.metadata_manager
                                    )
                                    
                                    total_added += update_stats['added']
                                    total_modified += update_stats['modified']
                                    total_deleted += update_stats['deleted']
                                    
                                    # 3. 更新元数据
                                    st.session_state.metadata_manager.update_repository_metadata(
                                        owner=owner,
                                        repo=repo_name,
                                        branch=branch,
                                        documents=documents
                                    )
                                    
                                    if changes.has_changes():
                                        st.success(f"✅ {owner}/{repo_name}: {changes.summary()}")
                                    
                                except Exception as e:
                                    st.error(f"❌ {owner}/{repo_name}: {str(e)[:100]}")
                            
                            # 刷新仓库列表
                            st.session_state.github_repos = st.session_state.metadata_manager.list_repositories()
                            st.session_state.index_built = True
                            
                            # 显示总结
                            if total_added + total_modified + total_deleted > 0:
                                st.success(f"🎉 同步完成！新增 {total_added}，修改 {total_modified}，删除 {total_deleted}")
                                st.rerun()
                            else:
                                st.success("✅ 所有仓库都是最新的")
        
        st.caption("💡 支持多仓库管理，自动检测文件变更，只更新变化的部分")
        
        st.divider()
        
        # ========== 2. 上传文档 ==========
        st.subheader("📁 上传文档")
        uploaded_files = st.file_uploader(
            "选择文件（支持多选）",
            type=['md', 'markdown', 'txt', 'rst', 'pdf', 'docx', 'json', 'csv', 'py', 'js', 'ts', 'java', 'cpp', 'c', 'h'],
            accept_multiple_files=True,
            help="支持多种格式：Markdown、文本、PDF、Word、代码等"
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
        
        # ========== 3. 从网页加载 ==========
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
        
        # ========== 4. 从目录加载（开发/测试用）==========
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
        
        # 维基百科配置
        with st.expander("🌐 维基百科增强", expanded=False):
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
                
                st.divider()
                
                # 预索引维基百科概念
                st.markdown("**预索引核心概念**")
                st.caption("将维基百科页面添加到索引中，提升查询速度")
                
                wiki_concepts_input = st.text_area(
                    "概念列表（每行一个）",
                    value="\n".join(config.WIKIPEDIA_PRELOAD_CONCEPTS),
                    height=100,
                    help="输入维基百科页面标题"
                )
                
                wiki_lang = st.selectbox(
                    "语言",
                    options=["zh", "en"],
                    format_func=lambda x: "中文" if x == "zh" else "English",
                    help="维基百科语言版本"
                )
                
                if st.button("📖 预索引维基百科", key="preload_wiki_btn"):
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
                        # 加载用户的 GitHub Token
                        st.session_state.user_github_token = st.session_state.user_manager.get_github_token(email)
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
                    # 判断使用哪种查询模式
                    if st.session_state.enable_wikipedia:
                        # 混合查询模式（维基百科增强）
                        hybrid_engine = load_hybrid_query_engine()
                        if hybrid_engine:
                            answer, local_sources, wikipedia_sources = hybrid_engine.query(prompt)
                            st.markdown(answer)
                            
                            # 分区显示来源
                            display_hybrid_sources(local_sources, wikipedia_sources)
                            
                            # 保存到消息历史
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": answer,
                                "sources": local_sources,
                                "wikipedia_sources": wikipedia_sources
                            })
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

