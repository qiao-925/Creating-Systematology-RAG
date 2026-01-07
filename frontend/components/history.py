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

from backend.infrastructure.indexer import get_embedding_model_status
from backend.business.chat import get_user_sessions_metadata_lazy
from backend.infrastructure.config import config
from backend.infrastructure.logger import get_logger

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


def _get_session_icon_emoji(title: str, session_id: Optional[str] = None) -> str:
    """获取会话图标（统一使用灯泡图标）
    
    Args:
        title: 会话标题（保留参数以保持接口一致）
        session_id: 会话ID（保留参数以保持接口一致）
        
    Returns:
        Emoji图标字符串（统一返回 💡）
    """
    return '💡'


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
    
    使用懒加载优化：只读取最小必要信息，切换时根据session_id动态构建文件路径。
    移除rerun，由render_chat_interface统一处理。
    
    Args:
        user_email: 用户邮箱（单用户模式下可忽略）
        current_session_id: 当前会话ID（用于高亮显示）
    """
    # 使用懒加载版本获取会话元数据（只读取最小必要信息）
    sessions_metadata = get_user_sessions_metadata_lazy(user_email)
    
    if not sessions_metadata:
        st.info("💡 还没有历史会话")
        return
    
    # 按时间分组
    grouped = group_sessions_by_time(sessions_metadata)
    
    # 显示分组后的会话
    for group_name, sessions in grouped.items():
        if sessions:
            # 分组标题（使用原生组件）
            st.caption(group_name.upper())
            for idx, session in enumerate(sessions):
                session_id = session['session_id']
                title = session.get('title', '未命名会话')
                is_current = session_id == current_session_id
                icon_emoji = _get_session_icon_emoji(title, session_id)
                
                # 统一使用按钮实现，按钮文本包含emoji图标和标题
                button_label = f"{icon_emoji} {title}"
                button_key = f"session_{session_id}"
                
                # 选中状态使用disabled按钮（不可点击但显示选中样式）
                if is_current:
                    st.button(
                        button_label,
                        key=button_key,
                        use_container_width=True,
                        type="secondary",
                        disabled=True
                    )
                else:
                    # 未选中状态：可点击按钮
                    if st.button(
                        button_label,
                        key=button_key,
                        use_container_width=True,
                        type="secondary"
                    ):
                        # 设置加载标记（不设置file_path，切换时根据session_id动态构建）
                        st.session_state.load_session_id = session_id
                        # 标记需要加载会话（不立即rerun，由render_chat_interface统一处理）
                        st.session_state.session_loading_pending = True


