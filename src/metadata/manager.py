"""
元数据管理 - 管理器核心模块
MetadataManager类实现
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from llama_index.core.schema import Document as LlamaDocument

from src.logger import setup_logger
from src.metadata.file_change import FileChange
from src.metadata.utils import compute_hash

logger = setup_logger('metadata_manager')


class MetadataManager:
    """元数据管理器
    
    负责管理 GitHub 仓库的元数据，追踪文件变化，支持增量更新
    """
    
    def __init__(self, metadata_path: Path):
        """初始化元数据管理器
        
        Args:
            metadata_path: 元数据文件路径
        """
        self.metadata_path = metadata_path
        self.metadata: Dict = self._load_metadata()
        
    def _load_metadata(self) -> Dict:
        """加载元数据文件
        
        Returns:
            元数据字典
        """
        if not self.metadata_path.exists():
            logger.info("元数据文件不存在，创建新的元数据")
            return {
                "version": "1.0",
                "repositories": {}
            }
        
        try:
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            logger.info(f"加载元数据成功，共 {len(metadata.get('repositories', {}))} 个仓库")
            return metadata
        except Exception as e:
            logger.error(f"加载元数据失败: {e}")
            logger.warning("将创建新的元数据文件")
            return {
                "version": "1.0",
                "repositories": {}
            }
    
    def save_metadata(self):
        """保存元数据到文件"""
        try:
            self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
            
            logger.info(f"元数据保存成功: {self.metadata_path}")
        except Exception as e:
            logger.error(f"保存元数据失败: {e}")
            raise
    
    def get_repository_key(self, owner: str, repo: str, branch: str = "main") -> str:
        """生成仓库的唯一标识
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            branch: 分支名称
            
        Returns:
            仓库标识字符串
        """
        return f"{owner}/{repo}@{branch}"
    
    def has_repository(self, owner: str, repo: str, branch: str = "main") -> bool:
        """检查仓库是否已存在
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            branch: 分支名称
            
        Returns:
            是否已存在
        """
        repo_key = self.get_repository_key(owner, repo, branch)
        return repo_key in self.metadata["repositories"]
    
    def get_repository_metadata(self, owner: str, repo: str, branch: str = "main") -> Optional[Dict]:
        """获取仓库的元数据
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            branch: 分支名称
            
        Returns:
            仓库元数据，如果不存在返回 None
        """
        repo_key = self.get_repository_key(owner, repo, branch)
        return self.metadata["repositories"].get(repo_key)

