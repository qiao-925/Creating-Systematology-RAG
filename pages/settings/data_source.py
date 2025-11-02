"""
设置页面数据源管理模块
GitHub仓库、本地文件、网页URL、维基百科管理
"""

import streamlit as st

from src.data_loader import (
    load_documents_from_urls,
    load_documents_from_github,
    parse_github_url,
    sync_github_repository
)
from src.ui_components import load_index


def render_data_source_tab():
    """渲染数据源管理标签页"""
    st.header("📦 数据源管理")
    st.caption("配置和管理各种数据源")
    
    # GitHub 仓库管理
    st.subheader("🐙 GitHub 仓库管理")
    st.info("ℹ️ 仅支持公开仓库")
    
    # 添加新仓库
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
            _handle_add_github_repo(github_url)
    
    with col2:
        pass
    
    st.divider()
    
    # 已添加的仓库列表
    st.markdown("**已添加的仓库**")
    _render_github_repos_list()
    
    st.divider()
    
    # 数据导入（本地文档）
    _render_local_file_upload()
    
    st.divider()
    
    # 网页URL导入
    _render_web_url_import()
    
    st.divider()
    
    # 维基百科预索引
    _render_wikipedia_preload()


def _handle_add_github_repo(github_url: str):
    """处理添加GitHub仓库"""
    if not github_url or not github_url.strip():
        st.error("❌ 请输入 GitHub 仓库 URL")
        return
    
    repo_info = parse_github_url(github_url.strip())
    if not repo_info:
        st.error("❌ 无效的 GitHub URL")
        return
    
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
                    documents, changes, commit_sha, cache_manager, task_id = sync_github_repository(
                        owner=github_owner,
                        repo=github_repo,
                        branch=github_branch,
                        metadata_manager=st.session_state.metadata_manager,
                        show_progress=True
                    )
                    
                    if documents:
                        index, vector_ids_map = index_manager.build_index(
                            documents, 
                            show_progress=True,
                            cache_manager=cache_manager,
                            task_id=task_id
                        )
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


def _render_github_repos_list():
    """渲染GitHub仓库列表"""
    if st.session_state.github_repos:
        st.caption(f"共 {len(st.session_state.github_repos)} 个仓库")
        
        for repo in st.session_state.github_repos:
            with st.expander(f"📦 {repo['key']}", expanded=False):
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.text(f"文件数量: {repo['file_count']}")
                    st.text(f"最后更新: {repo['last_indexed_at']}")
                    if 'commit_sha' in repo:
                        st.text(f"Commit: {repo['commit_sha'][:8]}")
                
                # 同步此仓库
                with col2:
                    if st.button("🔄 同步", key=f"sync_{repo['key']}"):
                        _handle_sync_repo(repo)
                
                # 删除此仓库
                with col3:
                    if st.button("🗑️ 删除", key=f"del_{repo['key']}"):
                        _handle_delete_repo(repo)
    else:
        st.info("尚未添加任何仓库")


def _handle_sync_repo(repo: dict):
    """处理仓库同步"""
    index_manager = load_index()
    if index_manager:
        with st.spinner(f"正在同步 {repo['key']}..."):
            try:
                parts = repo['key'].split('@')
                repo_part = parts[0]
                branch = parts[1] if len(parts) > 1 else 'main'
                owner, repo_name = repo_part.split('/')
                
                documents, changes, commit_sha, cache_manager, task_id = sync_github_repository(
                    owner=owner,
                    repo=repo_name,
                    branch=branch,
                    metadata_manager=st.session_state.metadata_manager,
                    show_progress=True
                )
                
                if changes.has_changes():
                    added_docs, modified_docs, deleted_paths = st.session_state.metadata_manager.get_documents_by_change(
                        documents, changes
                    )
                    if added_docs or modified_docs:
                        index_manager.build_index(
                            added_docs + modified_docs,
                            show_progress=True,
                            cache_manager=cache_manager,
                            task_id=task_id
                        )
                    index_manager.incremental_update(
                        added_docs=added_docs,
                        modified_docs=modified_docs,
                        deleted_file_paths=deleted_paths,
                        metadata_manager=st.session_state.metadata_manager
                    )
                    
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
                    st.session_state.github_repos = st.session_state.metadata_manager.list_repositories()
                    st.success("✅ 仓库已同步")
                else:
                    st.success("✅ 已是最新")
                st.rerun()
            except Exception as e:
                st.error(f"❌ 同步失败: {str(e)[:80]}")


def _handle_delete_repo(repo: dict):
    """处理仓库删除"""
    parts = repo['key'].split('@')
    repo_part = parts[0]
    branch = parts[1] if len(parts) > 1 else 'main'
    owner, repo_name = repo_part.split('/')
    st.session_state.metadata_manager.remove_repository(owner, repo_name, branch)
    st.session_state.github_repos = st.session_state.metadata_manager.list_repositories()
    st.success(f"已删除 {repo['key']}")
    st.rerun()


def _render_local_file_upload():
    """渲染本地文件上传"""
    st.subheader("📥 数据导入（本地文档）")
    st.caption("将本地文件直接导入索引，支持多种格式")
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
                    from src.data_source import LocalFileSource
                    from src.data_loader import load_documents_from_source
                    
                    source = LocalFileSource(source=list(uploaded_files))
                    documents = load_documents_from_source(source, clean=True, show_progress=False)
                    source.cleanup()
                    
                    if documents:
                        _, _ = index_manager.build_index(documents)
                        st.session_state.index_built = True
                        st.success(f"✅ 成功导入 {len(documents)} 个文档")
                        st.rerun()
                    else:
                        st.error("❌ 未能解析任何文档，请检查文件格式")
                except Exception as e:
                    st.error(f"❌ 导入失败: {e}")


def _render_web_url_import():
    """渲染网页URL导入"""
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


def _render_wikipedia_preload():
    """渲染维基百科预索引"""
    st.subheader("🌐 维基百科预索引")
    st.caption("将维基百科页面添加到索引中，提升查询速度")
    
    from src.config import config
    
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

