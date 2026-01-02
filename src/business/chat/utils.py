"""
对话管理 - 工具函数模块
会话元数据查询等辅助函数
"""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any

from src.infrastructure.config import config
from src.infrastructure.logger import get_logger
from src.business.chat.session import ChatSession

logger = get_logger('chat_manager')

# 条件导入streamlit（仅在Streamlit环境中可用）
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    # 创建一个假的st对象，避免装饰器报错
    class FakeStreamlit:
        def cache_data(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
    st = FakeStreamlit()


def _read_session_metadata_partial(session_file: Path) -> Optional[Dict[str, Any]]:
    """局部读取会话文件的元数据（不解析完整history）
    
    只读取必要的顶层字段，避免解析完整的history数组，大幅提升性能。
    
    Args:
        session_file: 会话文件路径
        
    Returns:
        元数据字典，如果读取失败返回None
    """
    try:
        with open(session_file, 'r', encoding='utf-8') as f:
            # 读取文件内容
            content = f.read()
            
        # 解析JSON（但只提取需要的字段）
        data = json.loads(content)
        
        # 提取顶层元数据（不解析history内容）
        metadata = {
            'session_id': data.get('session_id', ''),
            'title': data.get('title', ''),
            'created_at': data.get('created_at', ''),
            'updated_at': data.get('updated_at', ''),
            'file_path': str(session_file)
        }
        
        # 获取message_count：只获取数组长度，不解析内容
        history = data.get('history', [])
        metadata['message_count'] = len(history) if isinstance(history, list) else 0
        
        # 如果没有标题，且history不为空，才读取第一条消息
        if not metadata['title'] and history and len(history) > 0:
            try:
                first_turn = history[0]
                if isinstance(first_turn, dict):
                    first_question = first_turn.get('question', '')
                    if first_question:
                        metadata['title'] = first_question[:20] + ('...' if len(first_question) > 20 else '')
            except (KeyError, IndexError, TypeError):
                # 如果读取第一条消息失败，使用默认标题
                pass
        
        # 如果仍然没有标题，使用默认值
        if not metadata['title']:
            metadata['title'] = '新对话'
        
        return metadata
        
    except json.JSONDecodeError as e:
        logger.warning(f"JSON解析失败: {session_file}, 错误: {e}")
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


# 如果Streamlit可用，添加缓存装饰器
if STREAMLIT_AVAILABLE:
    _get_sessions_metadata_cached = st.cache_data(ttl=3600, show_spinner=False)(_get_sessions_metadata_cached)


def get_user_sessions_metadata(user_email: Optional[str] = None) -> List[Dict[str, Any]]:
    """获取用户所有会话的元数据（用于UI展示）
    
    使用缓存和局部读取优化性能：
    - 使用Streamlit缓存避免重复读取
    - 只读取必要的元数据字段，不解析完整history
    
    Args:
        user_email: 用户邮箱（单用户模式下可忽略，使用默认路径）
        
    Returns:
        会话元数据列表
    """
    # 单用户模式：直接使用默认会话目录
    sessions_dir = config.SESSIONS_PATH / "default" if user_email is None else config.SESSIONS_PATH / user_email
    
    if not sessions_dir.exists():
        return []
    
    # 获取所有会话文件的修改时间（用于缓存失效）
    session_files = list(sessions_dir.glob("*.json"))
    file_mtimes = tuple(
        (f.name, f.stat().st_mtime) 
        for f in session_files 
        if f.exists()
    )
    
    # 使用缓存版本获取元数据
    return _get_sessions_metadata_cached(
        user_email=user_email,
        sessions_dir_str=str(sessions_dir),
        file_mtimes=file_mtimes
    )


def get_user_sessions_metadata_lazy(user_email: Optional[str] = None) -> List[Dict[str, Any]]:
    """懒加载版本的会话元数据获取（只读取最小必要信息）
    
    用于列表展示，只读取：
    - session_id
    - title
    - created_at
    - updated_at
    
    不读取：
    - message_count（列表展示不需要）
    - file_path（切换时根据session_id动态构建）
    
    Args:
        user_email: 用户邮箱（单用户模式下可忽略，使用默认路径）
        
    Returns:
        会话元数据列表（最小信息）
    """
    # 单用户模式：直接使用默认会话目录
    sessions_dir = config.SESSIONS_PATH / "default" if user_email is None else config.SESSIONS_PATH / user_email
    
    if not sessions_dir.exists():
        return []
    
    sessions_metadata = []
    
    for session_file in sessions_dir.glob("*.json"):
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 只提取最小必要信息
            metadata = {
                'session_id': data.get('session_id', ''),
                'title': data.get('title', '新对话'),
                'created_at': data.get('created_at', ''),
                'updated_at': data.get('updated_at', '')
            }
            
            # 如果没有标题，尝试从第一条消息生成（但只读取第一条）
            if not metadata['title']:
                history = data.get('history', [])
                if history and len(history) > 0:
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
            
            sessions_metadata.append(metadata)
            
        except Exception as e:
            logger.warning(f"加载会话文件失败: {session_file}, 错误: {e}")
            continue
    
    # 按更新时间倒序排序（最新的在前）
    sessions_metadata.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
    
    return sessions_metadata


def load_session_from_file(file_path: str) -> Optional[ChatSession]:
    """从文件加载会话
    
    Args:
        file_path: 会话文件路径
        
    Returns:
        ChatSession对象，如果加载失败返回None
    """
    try:
        return ChatSession.load(Path(file_path))
    except Exception as e:
        logger.error(f"加载会话失败: {file_path}, 错误: {e}", exc_info=True)
        return None

