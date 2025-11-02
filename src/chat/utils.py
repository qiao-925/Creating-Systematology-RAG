"""
对话管理 - 工具函数模块
会话元数据查询等辅助函数
"""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any

from src.config import config
from src.logger import setup_logger
from src.chat.session import ChatSession

logger = setup_logger('chat_manager')


def get_user_sessions_metadata(user_email: str) -> List[Dict[str, Any]]:
    """获取用户所有会话的元数据（用于UI展示）
    
    Args:
        user_email: 用户邮箱
        
    Returns:
        会话元数据列表
    """
    sessions_dir = config.SESSIONS_PATH / user_email
    
    logger.debug(f"查找会话目录: {sessions_dir}")
    
    if not sessions_dir.exists():
        logger.debug(f"会话目录不存在: {sessions_dir}")
        return []
    
    sessions_metadata = []
    
    logger.debug("开始扫描会话文件...")
    for session_file in sessions_dir.glob("*.json"):
        logger.debug(f"找到会话文件: {session_file}")
        try:
            # 读取会话文件
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 提取元数据
            metadata = {
                'session_id': data.get('session_id', ''),
                'title': data.get('title', '新对话'),
                'created_at': data.get('created_at', ''),
                'updated_at': data.get('updated_at', ''),
                'message_count': len(data.get('history', [])),
                'file_path': str(session_file)
            }
            
            # 如果没有标题，尝试从第一条消息生成
            if not metadata['title'] and data.get('history'):
                first_question = data['history'][0].get('question', '')
                metadata['title'] = first_question[:20] + ('...' if len(first_question) > 20 else '')
            
            sessions_metadata.append(metadata)
            
        except Exception as e:
            logger.warning(f"加载会话文件失败: {session_file}, 错误: {e}")
            continue
    
    # 按更新时间倒序排序（最新的在前）
    sessions_metadata.sort(key=lambda x: x['updated_at'], reverse=True)
    
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

