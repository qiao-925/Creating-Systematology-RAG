"""
数据来源层基类
定义统一的数据源接口
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional


@dataclass
class SourceFile:
    """数据源文件信息"""
    path: Path  # 文件路径
    source_type: str  # 来源类型: 'github', 'local', 'web'
    metadata: Dict[str, Any]  # 额外元数据（如repo信息、URL等）


class DataSource(ABC):
    """数据源抽象基类"""
    
    @abstractmethod
    def get_file_paths(self) -> List[SourceFile]:
        """获取文件路径列表
        
        Returns:
            文件路径列表，每个SourceFile包含路径、来源类型和元数据
        """
        pass
    
    @abstractmethod
    def get_source_metadata(self) -> Dict[str, Any]:
        """获取数据源的元数据
        
        Returns:
            数据源级别的元数据（如仓库信息、URL等）
        """
        pass

