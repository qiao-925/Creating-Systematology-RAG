"""
历史记录组件 - 显示会话历史列表

主要功能：
- group_sessions_by_time(): 按时间分组会话
- display_session_history(): 显示会话历史列表

特性：
- 会话历史管理
- 时间分组功能（今天/昨天/7天内/30天内）
- 懒加载优化
"""

import streamlit as st
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from backend.business.chat import get_user_sessions_metadata
from backend.infrastructure.logger import get_logger

logger = get_logger('frontend.history')


def _get_session_icon_emoji(title: str, session_id: Optional[str] = None) -> str:
    """获取会话图标（统一使用灯泡图标）"""
    return '💡'


def group_sessions_by_time(sessions_metadata: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """按时间分组会话
    
    Args:
        sessions_metadata: 会话元数据列表
        
    Returns:
        分组后的字典: {'今天': [...], '昨天': [...], '7天内': [...], '30天内': [...]}
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


def display_session_history(
    user_email: Optional[str] = None, 
    current_session_id: Optional[str] = None
) -> None:
    """显示历史会话列表（按时间分组）
    
    使用懒加载优化：只读取最小必要信息，切换时根据 session_id 动态构建文件路径。
    移除 rerun，由 render_chat_interface 统一处理。
    
    Args:
        user_email: 用户邮箱（单用户模式下可忽略）
        current_session_id: 当前会话ID（用于高亮显示）
    """
    # #region agent log
    import json as _json; open('/home/q/Desktop/START/repos/AI-Practice (皮卡丘)/Creating-Systematology-RAG/.cursor/debug.log','a').write(_json.dumps({"hypothesisId":"H2","location":"history.py:entry","message":"display_session_history called","data":{"user_email":user_email,"current_session_id":current_session_id},"timestamp":__import__('time').time(),"sessionId":"debug-session"})+'\n')
    # #endregion
    
    # 获取会话元数据
    sessions_metadata = get_user_sessions_metadata(user_email)
    
    # #region agent log
    open('/home/q/Desktop/START/repos/AI-Practice (皮卡丘)/Creating-Systematology-RAG/.cursor/debug.log','a').write(_json.dumps({"hypothesisId":"H2","location":"history.py:after_get_metadata","message":"got sessions_metadata","data":{"count":len(sessions_metadata) if sessions_metadata else 0,"sessions":sessions_metadata[:3] if sessions_metadata else []},"timestamp":__import__('time').time(),"sessionId":"debug-session"})+'\n')
    # #endregion
    
    if not sessions_metadata:
        st.caption("💡 还没有历史会话")
        return
    
    # 按时间分组
    grouped = group_sessions_by_time(sessions_metadata)
    
    # #region agent log
    open('/home/q/Desktop/START/repos/AI-Practice (皮卡丘)/Creating-Systematology-RAG/.cursor/debug.log','a').write(_json.dumps({"hypothesisId":"H4","location":"history.py:after_group","message":"grouped sessions","data":{"today":len(grouped.get('今天',[])),"yesterday":len(grouped.get('昨天',[])),"week":len(grouped.get('7天内',[])),"month":len(grouped.get('30天内',[]))},"timestamp":__import__('time').time(),"sessionId":"debug-session"})+'\n')
    # #endregion
    
    # 显示分组后的会话
    for group_name, sessions in grouped.items():
        if sessions:
            # 分组标题
            st.caption(f"**{group_name}**")
            
            for session in sessions:
                session_id = session['session_id']
                title = session.get('title', '未命名会话')
                is_current = session_id == current_session_id
                icon_emoji = _get_session_icon_emoji(title, session_id)
                
                button_label = f"{icon_emoji} {title}"
                button_key = f"session_{session_id}"
                
                # 选中状态使用 disabled 按钮
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
                        # 设置加载标记
                        st.session_state.load_session_id = session_id
                        st.session_state.session_loading_pending = True
