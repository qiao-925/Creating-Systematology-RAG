"""
GitHub 导入进度组件：展示导入进度条和日志

主要功能：
- render_import_progress(): 渲染完整的进度组件
- 分阶段进度显示
- 固定高度可滚动日志区域
- 取消导入按钮
"""

import streamlit as st
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from backend.infrastructure.data_loader.progress import ImportProgressManager


def render_import_progress(
    progress_manager: "ImportProgressManager",
    on_cancel: Optional[callable] = None
) -> bool:
    """渲染导入进度组件
    
    Args:
        progress_manager: 进度管理器实例
        on_cancel: 取消回调函数（可选）
        
    Returns:
        是否已取消
    """
    from backend.infrastructure.data_loader.progress import ImportStage
    
    # 获取进度数据
    data = progress_manager.to_dict()
    
    # 标题
    st.markdown(f"### 📦 正在导入 {data['repository']}")
    
    # 阶段指示器
    _render_stage_indicator(data, ImportStage)
    
    # 进度条（可量化阶段）
    _render_progress_bar(data)
    
    # 日志区域
    _render_log_area(data)
    
    # 取消按钮
    cancelled = False
    if not data['is_complete']:
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if st.button("❌ 取消", key="cancel_import", use_container_width=True):
                progress_manager.request_cancel()
                if on_cancel:
                    on_cancel()
                cancelled = True
    
    return cancelled


def _render_stage_indicator(data: dict, ImportStage):
    """渲染阶段指示器"""
    current_stage = data['current_stage']
    current_index = data['current_stage_index']
    total_stages = data['total_stages']
    
    # 阶段列表
    stages = [
        ("preflight", "预检"),
        ("git_clone", "克隆"),
        ("file_walk", "扫描"),
        ("doc_parse", "解析"),
        ("vectorize", "向量"),
    ]
    
    # 构建阶段显示
    stage_parts = []
    for i, (stage_id, stage_name) in enumerate(stages, 1):
        if stage_id == current_stage:
            stage_parts.append(f"**[{stage_name}]**")
        elif i < current_index:
            stage_parts.append(f"~~{stage_name}~~")
        else:
            stage_parts.append(stage_name)
    
    stage_text = " → ".join(stage_parts)
    st.markdown(f"**阶段** [{current_index}/{total_stages}]: {stage_text}")


def _render_progress_bar(data: dict):
    """渲染进度条"""
    if data['is_quantifiable'] and data['progress_total'] > 0:
        # 可量化阶段：显示真实进度条
        progress_value = data['progress_current'] / data['progress_total']
        progress_text = f"{data['progress_percent']}% ({data['progress_current']}/{data['progress_total']})"
        st.progress(progress_value, text=progress_text)
    else:
        # 不可量化阶段：显示等待中状态
        elapsed = data['elapsed_seconds']
        stage_name = data['current_stage_name']
        
        if data['is_complete']:
            if data['current_stage'] == 'complete':
                st.success(f"✅ {stage_name}")
            elif data['current_stage'] == 'cancelled':
                st.warning(f"⚠️ {stage_name}")
            elif data['current_stage'] == 'failed':
                st.error(f"❌ {stage_name}")
                if data['error_message']:
                    st.error(data['error_message'])
        else:
            st.info(f"⏳ {stage_name}... (已等待 {elapsed:.0f}秒)")


def _render_log_area(data: dict):
    """渲染日志区域"""
    st.markdown("**📋 操作日志**")
    
    logs = data['logs']
    if logs:
        # 使用固定高度容器
        with st.container(height=150):
            for log in logs:
                st.text(log)
    else:
        st.caption("暂无日志")


def render_import_result(
    success: bool,
    doc_count: int = 0,
    error_message: Optional[str] = None
):
    """渲染导入结果
    
    Args:
        success: 是否成功
        doc_count: 文档数量
        error_message: 错误消息（可选）
    """
    if success:
        st.success(f"✅ 成功导入 {doc_count} 个文档！")
    else:
        if error_message:
            st.error(f"❌ 导入失败: {error_message}")
        else:
            st.error("❌ 导入失败")


def render_preflight_warning(
    size_mb: float,
    threshold_mb: float = 100
) -> bool:
    """渲染大仓库警告
    
    Args:
        size_mb: 仓库大小（MB）
        threshold_mb: 警告阈值（MB）
        
    Returns:
        用户是否确认继续
    """
    if size_mb <= threshold_mb:
        return True
    
    st.warning(
        f"⚠️ 仓库较大 ({size_mb:.1f}MB)，克隆可能需要较长时间。"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("继续导入", type="primary"):
            return True
    with col2:
        if st.button("取消"):
            return False
    
    return None  # 等待用户选择
