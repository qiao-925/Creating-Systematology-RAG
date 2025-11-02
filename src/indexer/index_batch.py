"""
索引批处理相关功能模块
"""

from collections import defaultdict
from pathlib import Path
from typing import List

from llama_index.core.schema import Document as LlamaDocument

from src.logger import setup_logger

logger = setup_logger('indexer')


def group_documents_by_directory(
    documents: List[LlamaDocument],
    depth: int,
    docs_per_batch: int,
    persist_dir: Path
) -> List[List[LlamaDocument]]:
    """按相对路径目录层级分组并切分为批次
    
    分组规则：
    - 以文档 metadata['file_path'] 为依据，按 depth 层目录分组
    - 无法解析路径或在根目录的文件归为 '_root'
    - 每个组内按 docs_per_batch 进行二次切分
    
    Args:
        documents: 文档列表
        depth: 目录深度
        docs_per_batch: 每批文档数
        persist_dir: 持久化目录
        
    Returns:
        批次列表（每批为文档列表）
    """
    if not documents:
        return []

    # 归一化分隔符，避免 Windows 路径影响
    def normalize_rel_path(p: str) -> str:
        if not p:
            return ""
        return p.replace('\\', '/').lstrip('/')

    # 计算分组键
    def group_key_for_path(rel_path: str) -> str:
        if not rel_path:
            return "_root"
        parts = [seg for seg in normalize_rel_path(rel_path).split('/') if seg]
        if not parts:
            return "_root"
        use_depth = max(1, depth)
        return '/'.join(parts[:use_depth])

    groups: defaultdict[str, List[LlamaDocument]] = defaultdict(list)
    for doc in documents:
        rel_path = doc.metadata.get('file_path', '') or ''
        key = group_key_for_path(rel_path)
        groups[key].append(doc)

    # 二次切分：将每个组按 docs_per_batch 切分为多个批次
    batches: List[List[LlamaDocument]] = []
    per_batch = max(1, int(docs_per_batch) if docs_per_batch else 20)
    for key, docs in groups.items():
        # 保持稳定性：按文件名排序
        docs_sorted = sorted(
            docs,
            key=lambda d: (d.metadata.get('file_path', ''), d.metadata.get('file_name', ''))
        )
        for i in range(0, len(docs_sorted), per_batch):
            batch_docs = docs_sorted[i:i+per_batch]
            batches.append(batch_docs)

    # 稳定排序：按组名、再按首文档路径
    def batch_sort_key(batch: List[LlamaDocument]) -> tuple:
        if not batch:
            return ("", "")
        first_path = batch[0].metadata.get('file_path', '') or ''
        key = group_key_for_path(first_path)
        return (key, first_path)

    batches.sort(key=batch_sort_key)
    return batches


def get_batch_ckpt_path(persist_dir: Path, collection_name: str) -> Path:
    """返回批级checkpoint文件路径（每个集合一个文件）"""
    ckpt_dir = persist_dir / "batch_checkpoints"
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    return ckpt_dir / f"{collection_name}.json"


def load_batch_ckpt(persist_dir: Path, collection_name: str) -> dict:
    """加载批级checkpoint"""
    import json
    ckpt_file = get_batch_ckpt_path(persist_dir, collection_name)
    if not ckpt_file.exists():
        return {"completed": {}}
    try:
        with open(ckpt_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, dict) or 'completed' not in data:
                return {"completed": {}}
            return data
    except Exception:
        return {"completed": {}}


def save_batch_ckpt(data: dict, persist_dir: Path, collection_name: str) -> None:
    """保存批级checkpoint"""
    import json
    ckpt_file = get_batch_ckpt_path(persist_dir, collection_name)
    try:
        with open(ckpt_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"写入批次checkpoint失败: {e}")


def compute_batch_id(group_key: str, file_paths: List[str]) -> str:
    """计算批次ID"""
    import hashlib
    import json
    payload = json.dumps({
        "group": group_key,
        "files": sorted(file_paths),
    }, ensure_ascii=False)
    return hashlib.md5(payload.encode('utf-8')).hexdigest()

