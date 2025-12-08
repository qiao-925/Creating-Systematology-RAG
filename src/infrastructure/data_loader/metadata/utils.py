"""
元数据管理 - 工具函数模块：哈希计算等工具函数

主要功能：
- compute_hash()：计算文本内容的MD5哈希值

执行流程：
1. 将文本编码为UTF-8
2. 计算MD5哈希
3. 返回十六进制字符串

特性：
- MD5哈希算法
- UTF-8编码支持
- 快速计算
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
