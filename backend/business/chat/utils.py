"""
对话管理 - 工具函数模块
会话文件持久化与元数据查询

主要功能：
- get_user_sessions_metadata(): 获取用户会话元数据列表
- load_session_from_file(): 从文件加载会话
- _read_session_metadata_partial(): 局部读取元数据（性能优化）
"""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any

from backend.infrastructure.config import config
from backend.infrastructure.logger import get_logger
from backend.business.chat.session import ChatSession

logger = get_logger('chat_utils')

# 条件导入 streamlit（仅在 Streamlit 环境中可用）
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    
    class FakeStreamlit:
        """假的 st 对象，避免装饰器报错"""
        def cache_data(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
    st = FakeStreamlit()


def _read_session_metadata_partial(session_file: Path) -> Optional[Dict[str, Any]]:
    """局部读取会话文件的元数据（不解析完整 history）
    
    只读取必要的顶层字段，避免解析完整的 history 数组，大幅提升性能。
    
    Args:
        session_file: 会话文件路径
        
    Returns:
        元数据字典，如果读取失败返回 None
    """
    try:
        with open(session_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        data = json.loads(content)
        
        # 提取顶层元数据（不解析 history 内容）
        metadata = {
            'session_id': data.get('session_id', ''),
            'title': data.get('title', ''),
            'created_at': data.get('created_at', ''),
            'updated_at': data.get('updated_at', ''),
            'file_path': str(session_file)
        }
        
        # 获取 message_count：只获取数组长度，不解析内容
        history = data.get('history', [])
        metadata['message_count'] = len(history) if isinstance(history, list) else 0
        
        # 如果没有标题，且 history 不为空，才读取第一条消息
        if not metadata['title'] and history and len(history) > 0:
            try:
                first_turn = history[0]
                if isinstance(first_turn, dict):
                    first_question = first_turn.get('question', '')
                    if first_question:
                        metadata['title'] = first_question[:20] + ('...' if len(first_question) > 20 else '')
            except (KeyError, IndexError, TypeError):
                pass
        
        if not metadata['title']:
            metadata['title'] = '新对话'
        
        return metadata
        
    except json.JSONDecodeError as e:
        logger.warning(f"JSON 解析失败: {session_file}, 错误: {e}")
        return None
    except Exception as e:
        logger.warning(f"加载会话文件失败: {session_file}, 错误: {e}")
        return None


def _get_sessions_metadata_cached(
    user_email: Optional[str],
    sessions_dir_str: str,
    file_mtimes: tuple
) -> List[Dict[str, Any]]:
    """缓存版本的会话元数据获取函数
    
    Args:
        user_email: 用户邮箱
        sessions_dir_str: 会话目录路径（字符串格式，用于缓存键）
        file_mtimes: 文件修改时间元组（用于缓存失效）
        
    Returns:
        会话元数据列表
    """
    sessions_dir = Path(sessions_dir_str)
    
    if not sessions_dir.exists():
        return []
    
    sessions_metadata = []
    
    for session_file in sessions_dir.glob("*.json"):
        metadata = _read_session_metadata_partial(session_file)
        if metadata:
            sessions_metadata.append(metadata)
    
    # 按更新时间倒序排序（最新的在前）
    sessions_metadata.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
    
    return sessions_metadata


# 如果 Streamlit 可用，添加缓存装饰器
if STREAMLIT_AVAILABLE:
    _get_sessions_metadata_cached = st.cache_data(
        ttl=3600, show_spinner=False
    )(_get_sessions_metadata_cached)


def get_user_sessions_metadata(user_email: Optional[str] = None) -> List[Dict[str, Any]]:
    """获取用户所有会话的元数据（用于 UI 展示）
    
    使用缓存和局部读取优化性能：
    - 使用 Streamlit 缓存避免重复读取
    - 只读取必要的元数据字段，不解析完整 history
    
    Args:
        user_email: 用户邮箱（单用户模式下可忽略，使用默认路径）
        
    Returns:
        会话元数据列表
    """
    sessions_dir = (
        config.SESSIONS_PATH / "default" 
        if user_email is None 
        else config.SESSIONS_PATH / user_email
    )
    
    # #region agent log
    import json as _json; open('/home/q/Desktop/START/repos/AI-Practice (皮卡丘)/Creating-Systematology-RAG/.cursor/debug.log','a').write(_json.dumps({"hypothesisId":"H3","location":"utils.py:get_metadata","message":"checking sessions_dir","data":{"sessions_dir":str(sessions_dir),"exists":sessions_dir.exists(),"SESSIONS_PATH":str(config.SESSIONS_PATH)},"timestamp":__import__('time').time(),"sessionId":"debug-session"})+'\n')
    # #endregion
    
    if not sessions_dir.exists():
        return []
    
    # 获取所有会话文件的修改时间（用于缓存失效）
    session_files = list(sessions_dir.glob("*.json"))
    
    # #region agent log
    open('/home/q/Desktop/START/repos/AI-Practice (皮卡丘)/Creating-Systematology-RAG/.cursor/debug.log','a').write(_json.dumps({"hypothesisId":"H3","location":"utils.py:scan_files","message":"found session files","data":{"file_count":len(session_files),"files":[str(f.name) for f in session_files[:5]]},"timestamp":__import__('time').time(),"sessionId":"debug-session"})+'\n')
    # #endregion
    
    file_mtimes = tuple(
        (f.name, f.stat().st_mtime) 
        for f in session_files 
        if f.exists()
    )
    
    return _get_sessions_metadata_cached(
        user_email=user_email,
        sessions_dir_str=str(sessions_dir),
        file_mtimes=file_mtimes
    )


def load_session_from_file(file_path: str) -> Optional[ChatSession]:
    """从文件加载会话
    
    Args:
        file_path: 会话文件路径
        
    Returns:
        ChatSession 对象，如果加载失败返回 None
    """
    try:
        return ChatSession.load(Path(file_path))
    except Exception as e:
        logger.error(f"加载会话失败: {file_path}, 错误: {e}", exc_info=True)
        return None
