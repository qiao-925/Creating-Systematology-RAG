"""
历史记录组件
显示模型状态和会话历史

主要功能：
- display_model_status()：显示Embedding模型状态
- group_sessions_by_time()：按时间分组会话
- display_session_history()：显示会话历史

特性：
- 模型状态显示
- 会话历史管理
- 时间分组功能
- 友好的UI展示
"""

import streamlit as st
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from src.infrastructure.indexer import get_embedding_model_status
from src.business.chat import get_user_sessions_metadata
from src.infrastructure.logger import get_logger

logger = get_logger('frontend.history')


def display_model_status() -> None:
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


def group_sessions_by_time(sessions_metadata: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """按时间分组会话
    
    Args:
        sessions_metadata: 会话元数据列表
        
    Returns:
        分组后的字典: {'今天': [...], '7天内': [...], '30天内': [...]}
    """
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)
    
    groups = {
        '今天': [],
        '昨天': [],
        '7天内': [],
        '30天内': []
    }
    
    for session in sessions_metadata:
        try:
            updated_at = datetime.fromisoformat(session['updated_at'])
            
            if updated_at >= today_start:
                groups['今天'].append(session)
            elif updated_at >= yesterday_start:
                groups['昨天'].append(session)
            elif updated_at >= seven_days_ago:
                groups['7天内'].append(session)
            elif updated_at >= thirty_days_ago:
                groups['30天内'].append(session)
        except Exception as e:
            logger.warning(f"解析时间失败: {e}")
            continue
    
    return groups


def display_session_history(user_email: Optional[str] = None, current_session_id: Optional[str] = None) -> None:
    """显示历史会话列表（按时间分组）
    
    Args:
        user_email: 用户邮箱（单用户模式下可忽略）
        current_session_id: 当前会话ID（用于高亮显示）
    """
    # 获取所有会话元数据（单用户模式下user_email为None）
    sessions_metadata = get_user_sessions_metadata(user_email)
    
    if not sessions_metadata:
        st.info("💡 还没有历史会话")
        return
    
    # 按时间分组
    grouped = group_sessions_by_time(sessions_metadata)
    
    # 显示分组后的会话
    for group_name, sessions in grouped.items():
        if sessions:
            # 分组标题样式（类似DeepSeek：小字体，灰色，加粗）
            st.markdown(
                f"<div class='session-group-title' style='margin-top: 0.5rem; margin-bottom: 0.25rem; font-size: 0.8rem; font-weight: 600; color: var(--color-text-secondary);'><strong>{group_name}</strong></div>",
                unsafe_allow_html=True
            )
            for idx, session in enumerate(sessions):
                session_id = session['session_id']
                title = session.get('title', '未命名会话')
                is_current = session_id == current_session_id
                
                if is_current:
                    # 选中状态：使用markdown显示，浅蓝色背景，深蓝色文字（类似DeepSeek）
                    st.markdown(
                        f'<div class="session-item-current" style="margin: 0.0625rem 0; padding: 0.15rem 0.4rem; border-radius: 6px; background-color: rgba(37, 99, 235, 0.1); color: var(--color-accent); font-size: 0.85rem; font-weight: 500; line-height: 1.3;">{title}</div>',
                        unsafe_allow_html=True
                    )
                else:
                    # 未选中状态：使用button，hover时浅灰色背景
                    if st.button(f"{title}", key=f"session_{session_id}", use_container_width=True):
                        # 设置加载标记和文件路径（app.py会检查这些标记来加载会话）
                        st.session_state.load_session_id = session_id
                        st.session_state.load_session_path = session.get('file_path', '')
                        st.rerun()


