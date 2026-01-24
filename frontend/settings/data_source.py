"""
设置页面数据源管理模块
GitHub仓库、本地文件管理
支持进度可视化和取消导入
"""

import streamlit as st

from backend.infrastructure.data_loader import (
    DataImportService,
    parse_github_url,
    sync_github_repository,
    check_repository,
    ImportProgressManager,
)


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


def _handle_add_github_repo(github_url: str):
    """处理添加GitHub仓库（支持进度可视化和取消）"""
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
    
    if st.session_state.github_sync_manager.has_repository(github_owner, github_repo, github_branch):
        st.warning(f"⚠️ 仓库已存在")
        return
    
    # 从统一初始化系统获取 IndexManager
    init_result = st.session_state.get('init_result')
    if not init_result:
        st.error("❌ 应用未初始化，请刷新页面")
        return
    index_manager = init_result.instances.get('index_manager')
    if not index_manager:
        st.error("❌ 索引管理器未初始化")
        return
    
    # 创建进度管理器
    progress_manager = ImportProgressManager(github_owner, github_repo, github_branch)
    
    # 创建进度显示容器
    progress_container = st.container()
    
    with progress_container:
        st.markdown(f"### 📦 正在导入 {github_owner}/{github_repo}")
        
        # 步骤 1: 仓库预检
        stage_text = st.empty()
        progress_bar = st.empty()
        log_container = st.container(height=150)
        cancel_col1, cancel_col2, cancel_col3 = st.columns([2, 1, 2])
        
        # 检查是否已请求取消
        cancel_key = f"cancel_{github_owner}_{github_repo}"
        if st.session_state.get(cancel_key):
            st.warning("⚠️ 导入已取消")
            st.session_state[cancel_key] = False
            return
        
        with cancel_col2:
            if st.button("❌ 取消", key="cancel_add_repo"):
                st.session_state[cancel_key] = True
                st.warning("⚠️ 正在取消...")
                return
        
        try:
            # 预检阶段
            stage_text.markdown("**阶段 [1/5]**: 🔍 仓库预检...")
            progress_bar.progress(0.1)
            
            preflight_result = check_repository(github_owner, github_repo)
            
            if not preflight_result.success:
                st.error(f"❌ 预检失败: {preflight_result.error_message}")
                return
            
            # 大仓库警告
            if preflight_result.is_large:
                st.warning(f"⚠️ 仓库较大 ({preflight_result.size_mb:.1f}MB)，克隆可能需要较长时间")
            
            with log_container:
                st.text(f"✅ 预检通过 (大小: {preflight_result.size_mb:.1f}MB)")
            
            # 检查取消
            if st.session_state.get(cancel_key):
                st.warning("⚠️ 导入已取消")
                st.session_state[cancel_key] = False
                return
            
            # 克隆/同步阶段
            stage_text.markdown("**阶段 [2/5]**: 🔄 克隆仓库...")
            progress_bar.progress(0.2)
            
            documents, changes, commit_sha = sync_github_repository(
                owner=github_owner,
                repo=github_repo,
                branch=github_branch,
                github_sync_manager=st.session_state.github_sync_manager,
                show_progress=False
            )
            
            with log_container:
                st.text(f"✅ 预检通过 (大小: {preflight_result.size_mb:.1f}MB)")
                if commit_sha:
                    st.text(f"✅ 仓库同步完成 (Commit: {commit_sha[:8]})")
            
            # 检查取消
            if st.session_state.get(cancel_key):
                st.warning("⚠️ 导入已取消")
                st.session_state[cancel_key] = False
                return
            
            if not documents:
                st.warning("⚠️ 未能加载任何文件")
                return
            
            # 索引构建阶段
            stage_text.markdown(f"**阶段 [4/5]**: 🔢 构建索引 ({len(documents)} 个文档)...")
            progress_bar.progress(0.6)
            
            with log_container:
                st.text(f"✅ 预检通过 (大小: {preflight_result.size_mb:.1f}MB)")
                st.text(f"✅ 仓库同步完成 (Commit: {commit_sha[:8]})")
                st.text(f"🔄 正在构建索引 ({len(documents)} 个文档)...")
            
            index, vector_ids_map = index_manager.build_index(
                documents, 
                show_progress=False,
                github_sync_manager=st.session_state.github_sync_manager
            )
            
            # 保存状态
            stage_text.markdown("**阶段 [5/5]**: 💾 保存状态...")
            progress_bar.progress(0.9)
            
            st.session_state.github_sync_manager.update_repository_sync_state(
                owner=github_owner,
                repo=github_repo,
                branch=github_branch,
                documents=documents,
                vector_ids_map=vector_ids_map,
                commit_sha=commit_sha
            )
            st.session_state.github_repos = st.session_state.github_sync_manager.list_repositories()
            st.session_state.index_built = True
            
            # 完成
            stage_text.markdown("**完成** ✅")
            progress_bar.progress(1.0)
            
            with log_container:
                st.text(f"✅ 预检通过 (大小: {preflight_result.size_mb:.1f}MB)")
                st.text(f"✅ 仓库同步完成 (Commit: {commit_sha[:8]})")
                st.text(f"✅ 索引构建完成 ({len(documents)} 个文档)")
                st.text(f"✅ 导入完成！")
            
            st.success(f"✅ 成功添加 {len(documents)} 个文件！")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ 添加失败: {str(e)[:100]}")
            with log_container:
                st.text(f"❌ 错误: {str(e)[:80]}")


def _create_delete_callback(repo: dict):
    """创建删除仓库的回调函数（闭包捕获 repo）"""
    def callback():
        parts = repo['key'].split('@')
        repo_part = parts[0]
        branch = parts[1] if len(parts) > 1 else 'main'
        owner, repo_name = repo_part.split('/')
        st.session_state.github_sync_manager.remove_repository(owner, repo_name, branch)
        st.session_state.github_repos = st.session_state.github_sync_manager.list_repositories()
        st.session_state._delete_success_msg = f"已删除 {repo['key']}"
    return callback


def _render_github_repos_list():
    """渲染GitHub仓库列表"""
    # 显示删除成功消息（如果有）
    if st.session_state.get('_delete_success_msg'):
        st.success(st.session_state._delete_success_msg)
        st.session_state._delete_success_msg = None
    
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
                
                # 同步此仓库（耗时操作，保持 if st.button）
                with col2:
                    if st.button("🔄 同步", key=f"sync_{repo['key']}"):
                        _handle_sync_repo(repo)
                
                # 删除此仓库（快速操作，使用 on_click）
                with col3:
                    st.button(
                        "🗑️ 删除", 
                        key=f"del_{repo['key']}",
                        on_click=_create_delete_callback(repo)
                    )
    else:
        st.info("尚未添加任何仓库")


def _handle_sync_repo(repo: dict):
    """处理仓库同步（支持进度显示）"""
    # 从统一初始化系统获取 IndexManager
    init_result = st.session_state.get('init_result')
    if not init_result:
        st.error("❌ 应用未初始化，请刷新页面")
        return
    index_manager = init_result.instances.get('index_manager')
    if not index_manager:
        st.error("❌ 索引管理器未初始化")
        return
    
    # 解析仓库信息
    parts = repo['key'].split('@')
    repo_part = parts[0]
    branch = parts[1] if len(parts) > 1 else 'main'
    owner, repo_name = repo_part.split('/')
    
    # 创建进度显示
    progress_container = st.container()
    
    with progress_container:
        stage_text = st.empty()
        progress_bar = st.empty()
        log_container = st.container(height=120)
        
        try:
            # 同步阶段
            stage_text.markdown(f"**同步** 🔄 {repo['key']}...")
            progress_bar.progress(0.2)
            
            with log_container:
                st.text(f"🔄 正在同步 {owner}/{repo_name}@{branch}...")
            
            documents, changes, commit_sha = sync_github_repository(
                owner=owner,
                repo=repo_name,
                branch=branch,
                github_sync_manager=st.session_state.github_sync_manager,
                show_progress=False
            )
            
            progress_bar.progress(0.5)
            
            if changes.has_changes():
                with log_container:
                    st.text(f"🔄 正在同步 {owner}/{repo_name}@{branch}...")
                    st.text(f"📝 检测到变更: {changes.summary()}")
                
                added_docs, modified_docs, deleted_paths = st.session_state.github_sync_manager.get_documents_by_change(
                    documents, changes
                )
                
                if added_docs or modified_docs:
                    stage_text.markdown(f"**构建索引** 🔢 处理变更...")
                    progress_bar.progress(0.7)
                    
                    index_manager.build_index(
                        added_docs + modified_docs,
                        show_progress=False,
                        github_sync_manager=st.session_state.github_sync_manager
                    )
                
                index_manager.incremental_update(
                    added_docs=added_docs,
                    modified_docs=modified_docs,
                    deleted_file_paths=deleted_paths,
                    github_sync_manager=st.session_state.github_sync_manager
                )
                
                vector_ids_map = {}
                for doc in documents:
                    file_path = doc.metadata.get("file_path", "")
                    if file_path:
                        vector_ids = st.session_state.github_sync_manager.get_file_vector_ids(
                            owner, repo_name, branch, file_path
                        )
                        vector_ids_map[file_path] = vector_ids
                
                st.session_state.github_sync_manager.update_repository_sync_state(
                    owner=owner,
                    repo=repo_name,
                    branch=branch,
                    documents=documents,
                    vector_ids_map=vector_ids_map,
                    commit_sha=commit_sha
                )
                st.session_state.github_repos = st.session_state.github_sync_manager.list_repositories()
                
                progress_bar.progress(1.0)
                stage_text.markdown("**完成** ✅")
                
                with log_container:
                    st.text(f"🔄 正在同步 {owner}/{repo_name}@{branch}...")
                    st.text(f"📝 检测到变更: {changes.summary()}")
                    st.text(f"✅ 同步完成！")
                
                st.success("✅ 仓库已同步")
            else:
                progress_bar.progress(1.0)
                stage_text.markdown("**完成** ✅")
                
                with log_container:
                    st.text(f"🔄 正在同步 {owner}/{repo_name}@{branch}...")
                    st.text(f"✅ 已是最新版本")
                
                st.success("✅ 已是最新")
            
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ 同步失败: {str(e)[:80]}")


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
        # 从统一初始化系统获取 IndexManager
        init_result = st.session_state.get('init_result')
        if not init_result:
            st.error("❌ 应用未初始化，请刷新页面")
            return
        index_manager = init_result.instances.get('index_manager')
        if index_manager:
            with st.spinner(f"正在处理 {len(uploaded_files)} 个文件..."):
                try:
                    from backend.infrastructure.data_loader.source import LocalFileSource
                    from backend.infrastructure.data_loader import DataImportService
                    
                    service = DataImportService(show_progress=False)
                    source = LocalFileSource(source=list(uploaded_files))
                    result = service.import_from_source(source, clean=True)
                    source.cleanup()
                    
                    if result.success and result.documents:
                        _, _ = index_manager.build_index(result.documents)
                        st.session_state.index_built = True
                        st.success(f"✅ 成功导入 {len(result.documents)} 个文档")
                        st.rerun()
                    else:
                        error_msg = "❌ 未能解析任何文档，请检查文件格式"
                        if result.errors:
                            error_msg += f"\n错误: {', '.join(result.errors)}"
                        st.error(error_msg)
                except Exception as e:
                    st.error(f"❌ 导入失败: {e}")



