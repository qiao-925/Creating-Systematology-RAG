"""
元数据管理 - FileChange数据模型模块
文件变更记录类
"""

from typing import List


class FileChange:
    """文件变更记录"""
    
    def __init__(self):
        self.added: List[str] = []      # 新增的文件
        self.modified: List[str] = []   # 修改的文件
        self.deleted: List[str] = []    # 删除的文件
    
    def has_changes(self) -> bool:
        """是否有变更"""
        return bool(self.added or self.modified or self.deleted)
    
    def summary(self) -> str:
        """变更摘要"""
        parts = []
        if self.added:
            parts.append(f"新增 {len(self.added)} 个")
        if self.modified:
            parts.append(f"修改 {len(self.modified)} 个")
        if self.deleted:
            parts.append(f"删除 {len(self.deleted)} 个")
        return "、".join(parts) if parts else "无变更"
    
    def total_count(self) -> int:
        """总变更数"""
        return len(self.added) + len(self.modified) + len(self.deleted)

