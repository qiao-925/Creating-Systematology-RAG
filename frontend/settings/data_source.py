"""
设置页面数据源管理模块
GitHub仓库、本地文件管理
支持进度可视化和取消导入（后台线程 + 轮询机制）
"""

import time
import streamlit as st

from backend.infrastructure.data_loader import (
    DataImportService,
    parse_github_url,
    sync_github_repository,
    check_repository,
    ImportTask,
    SyncTask,
)


def render_data_source_tab():
    """渲染数据源管理标签页"""
    st.header("📦 数据源管理")
    st.caption("配置和管理各种数据源")
    
    # 检查是否有正在进行的导入任务
    if _render_import_progress():
        # 有任务进行中，不显示其他内容
        return
    
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
    """处理添加GitHub仓库 - 启动后台任务"""
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
    
    # 按需初始化 index_manager（延迟加载）
    if not index_manager:
        with st.spinner("正在初始化索引管理器..."):
            try:
                from backend.infrastructure.initialization.registry_init import init_index_manager
                index_manager = init_index_manager(init_result.manager)
                init_result.instances['index_manager'] = index_manager
            except Exception as e:
                st.error(f"❌ 索引管理器初始化失败: {str(e)[:100]}")
                return
    
    if not index_manager:
        st.error("❌ 索引管理器初始化失败")
        return
    
    # 启动后台导入任务
    task = ImportTask.start(
        owner=github_owner,
        repo=github_repo,
        branch=github_branch,
        index_manager=index_manager,
        github_sync_manager=st.session_state.github_sync_manager
    )
    
    # 保存任务到 session_state
    st.session_state['import_task'] = task
    st.session_state['import_task_type'] = 'import'
    st.rerun()


def _render_import_progress():
    """渲染导入/同步进度（轮询模式）
    
    支持 ImportTask 和 SyncTask，统一进度显示逻辑。
    
    Returns:
        bool: 是否有正在进行的任务
    """
    task = st.session_state.get('import_task')
    if not task:
        return False
    
    progress = task.get_progress()
    task_type = st.session_state.get('import_task_type', 'import')
    
    # 渲染进度 UI（根据任务类型显示不同标题）
    if task_type == 'sync':
        st.markdown(f"### 🔄 正在同步 {progress['repository']}")
    else:
        st.markdown(f"### 📦 正在导入 {progress['repository']}")
    
    # 阶段指示器
    stages = ["预检", "克隆", "扫描", "解析", "向量"]
    current_idx = progress['current_stage_index']
    stage_parts = []
    for i, name in enumerate(stages, 1):
        if i == current_idx:
            stage_parts.append(f"**[{name}]**")
        elif i < current_idx:
            stage_parts.append(f"~~{name}~~")
        else:
            stage_parts.append(name)
    st.markdown(f"**阶段** [{current_idx}/{progress['total_stages']}]: " + " → ".join(stage_parts))
    
    # 进度条
    if progress['is_quantifiable'] and progress['progress_total'] > 0:
        progress_value = progress['progress_current'] / progress['progress_total']
        progress_text = f"{progress['progress_percent']}% ({progress['progress_current']}/{progress['progress_total']})"
        st.progress(progress_value, text=progress_text)
    else:
        elapsed = progress['elapsed_seconds']
        stage_name = progress['current_stage_name']
        if progress['is_complete']:
            if progress['current_stage'] == 'complete':
                st.success(f"✅ {stage_name}")
            elif progress['current_stage'] == 'cancelled':
                st.warning(f"⚠️ {stage_name}")
            elif progress['current_stage'] == 'failed':
                st.error(f"❌ {stage_name}")
                if progress['error_message']:
                    st.error(progress['error_message'])
        else:
            st.info(f"⏳ {stage_name}... (已等待 {elapsed:.0f}秒)")
    
    # 日志区域
    st.markdown("**📋 操作日志**")
    logs = progress['logs']
    if logs:
        with st.container(height=150):
            for log in logs[-10:]:  # 只显示最近 10 条
                st.text(log)
    else:
        st.caption("暂无日志")
    
    # 取消按钮
    if not progress['is_complete']:
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if st.button("❌ 取消", key="cancel_import_task", use_container_width=True):
                task.cancel()
                st.rerun()
        
        # 轮询：等待后刷新
        time.sleep(1)  # 1 秒轮询间隔
        st.rerun()
    else:
        # 任务完成，显示结果并清理
        task_type = st.session_state.get('import_task_type', 'import')
        
        if task.is_success:
            # 更新仓库列表
            st.session_state.github_repos = st.session_state.github_sync_manager.list_repositories()
            st.session_state.index_built = True
            
            if task_type == 'sync':
                # SyncTask 特有属性
                if hasattr(task, 'has_changes') and not task.has_changes:
                    st.success("✅ 已是最新版本")
                else:
                    changes_summary = getattr(task, 'changes_summary', '')
                    st.success(f"✅ 同步完成！{changes_summary}")
            else:
                st.success(f"✅ 成功导入 {task.documents_count} 个文档！")
        elif progress['current_stage'] == 'cancelled':
            if task_type == 'sync':
                st.warning("⚠️ 同步已取消")
            else:
                st.warning("⚠️ 导入已取消")
        else:
            if task_type == 'sync':
                st.error(f"❌ 同步失败: {task.error_message or '未知错误'}")
            else:
                st.error(f"❌ 导入失败: {task.error_message or '未知错误'}")
        
        # 清理任务
        if st.button("确定", key="clear_import_task", use_container_width=True):
            st.session_state['import_task'] = None
            st.session_state['import_task_type'] = None
            st.rerun()
    
    return True


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
    """处理仓库同步 - 启动后台任务"""
    # 从统一初始化系统获取 IndexManager
    init_result = st.session_state.get('init_result')
    if not init_result:
        st.error("❌ 应用未初始化，请刷新页面")
        return
    index_manager = init_result.instances.get('index_manager')
    
    # 按需初始化 index_manager（延迟加载，与导入逻辑一致）
    if not index_manager:
        with st.spinner("正在初始化索引管理器..."):
            try:
                from backend.infrastructure.initialization.registry_init import init_index_manager
                index_manager = init_index_manager(init_result.manager)
                init_result.instances['index_manager'] = index_manager
            except Exception as e:
                st.error(f"❌ 索引管理器初始化失败: {str(e)[:100]}")
                return
    
    if not index_manager:
        st.error("❌ 索引管理器初始化失败")
        return
    
    # 解析仓库信息
    parts = repo['key'].split('@')
    repo_part = parts[0]
    branch = parts[1] if len(parts) > 1 else 'main'
    owner, repo_name = repo_part.split('/')
    
    # 启动后台同步任务
    task = SyncTask.start(
        owner=owner,
        repo=repo_name,
        branch=branch,
        index_manager=index_manager,
        github_sync_manager=st.session_state.github_sync_manager
    )
    
    # 保存任务到 session_state（复用导入的 key，一次只能有一个任务）
    st.session_state['import_task'] = task
    st.session_state['import_task_type'] = 'sync'
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



