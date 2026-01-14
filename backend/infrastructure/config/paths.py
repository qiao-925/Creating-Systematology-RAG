"""
路径管理模块：处理应用目录的创建和管理

主要功能：
- ensure_directories()：确保所有必要的目录存在
"""

from pathlib import Path
from typing import List


def ensure_directories(directories: List[Path]) -> None:
    """确保所有必要的目录存在
    
    Args:
        directories: 需要创建的目录列表
    """
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def get_required_directories(config) -> List[Path]:
    """获取所有需要创建的目录列表
    
    Args:
        config: Config 实例
        
    Returns:
        目录列表
    """
    return [
        config.RAW_DATA_PATH,
        config.PROCESSED_DATA_PATH,
        config.VECTOR_STORE_PATH,  # 向后兼容
        config.ACTIVITY_LOG_PATH,
        config.GITHUB_REPOS_PATH,
        # 确保主日志目录存在（用于 logger.py）
        Path(config.PROJECT_ROOT / "data" / "logs"),
    ]
