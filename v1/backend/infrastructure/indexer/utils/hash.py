"""
哈希计算模块：计算文档列表的哈希值
"""

import hashlib
import json
from typing import List

from llama_index.core.schema import Document as LlamaDocument


def compute_documents_hash(documents: List[LlamaDocument]) -> str:
    """计算文档列表的哈希值
    
    Args:
        documents: 文档列表
        
    Returns:
        MD5哈希值
    """
    docs_data = []
    for doc in documents:
        docs_data.append({
            "text": doc.text[:1000],  # 只使用前1000字符以提高性能
            "file_path": doc.metadata.get("file_path", ""),
            "file_name": doc.metadata.get("file_name", "")
        })
    
    docs_str = json.dumps(docs_data, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(docs_str.encode('utf-8')).hexdigest()
