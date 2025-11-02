"""
元数据管理 - 工具函数模块
哈希计算等工具函数
"""

import hashlib


def compute_hash(content: str) -> str:
    """计算文本内容的 MD5 哈希值
    
    Args:
        content: 文本内容
        
    Returns:
        MD5 哈希值（十六进制字符串）
    """
    return hashlib.md5(content.encode('utf-8')).hexdigest()

