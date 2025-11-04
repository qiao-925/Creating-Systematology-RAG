#!/usr/bin/env python3
"""
Chroma 向量库可视化/导出脚本（只读）

功能：
  - 列出所有集合及计数
  - 抽样查看指定集合：ids / metadatas / 样本向量维度
  - 导出集合的 ids + metadatas（NDJSON），可用于外部审阅

使用示例：
  # 列集合
  python scripts/chroma_inspect.py list

  # 抽样查看集合（默认3条）
  python scripts/chroma_inspect.py inspect --collection default --limit 5

  # 导出集合元数据到文件
  python scripts/chroma_inspect.py export --collection default --out data/export.ndjson
"""

import argparse
import json
import sys
from pathlib import Path


# 确保项目根目录在 sys.path 中（从 scripts/ 回到仓库根）
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _safe_print(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def _get_client():
    # 延迟导入，避免环境未装时报错影响其它命令
    import chromadb
    from src.config import config
    
    if not config.CHROMA_CLOUD_API_KEY or not config.CHROMA_CLOUD_TENANT or not config.CHROMA_CLOUD_DATABASE:
        raise ValueError(
            "Chroma Cloud配置不完整，请设置以下环境变量：\n"
            "- CHROMA_CLOUD_API_KEY\n"
            "- CHROMA_CLOUD_TENANT\n"
            "- CHROMA_CLOUD_DATABASE"
        )
    
    client = chromadb.CloudClient(
        api_key=config.CHROMA_CLOUD_API_KEY,
        tenant=config.CHROMA_CLOUD_TENANT,
        database=config.CHROMA_CLOUD_DATABASE
    )
    return client


def cmd_list_collections(args):
    client = _get_client()
    cols = client.list_collections() if hasattr(client, 'list_collections') else client.get_collections()

    out = []
    for col in cols:
        info = {
            "name": getattr(col, 'name', None),
            "id": getattr(col, 'id', None),
        }
        try:
            info["count"] = col.count()
        except Exception as e:
            info["count_error"] = str(e)
        md = getattr(col, 'metadata', None) or {}
        if isinstance(md, dict):
            info["embedding_dim_meta"] = md.get("embedding_dimension")
        out.append(info)

    _safe_print(out)
    return 0


def _compute_sample_dim(embs):
    try:
        # embs 可能是 list/tuple 或 numpy 数组
        if embs is None:
            return None
        # list 情况
        if isinstance(embs, (list, tuple)):
            if len(embs) == 0:
                return None
            return len(embs[0]) if isinstance(embs[0], (list, tuple)) else (embs[0].shape[0] if hasattr(embs[0], 'shape') else None)
        # numpy 情况
        if hasattr(embs, 'size') and hasattr(embs, 'shape'):
            if getattr(embs, 'size', 0) == 0:
                return None
            # 形如 (n, dim)
            if len(embs.shape) == 2:
                return int(embs.shape[1])
            # 单向量 (dim,)
            if len(embs.shape) == 1:
                return int(embs.shape[0])
        return None
    except Exception:
        return None


def cmd_inspect(args):
    client = _get_client()
    col = client.get_collection(name=args.collection)

    # 计数 + 抽样
    count = col.count()
    try:
        sample = col.peek(limit=args.limit)
    except TypeError:
        # 兼容旧版（无 limit 参数时退化为默认采样）
        sample = col.peek()

    ids = (sample.get('ids', []) if isinstance(sample, dict) else []) or []
    metadatas = (sample.get('metadatas', []) if isinstance(sample, dict) else []) or []
    embs = (sample.get('embeddings', []) if isinstance(sample, dict) else []) or []
    sample_dim = _compute_sample_dim(embs)

    out = {
        "collection": getattr(col, 'name', args.collection),
        "count": count,
        "sample_size": len(ids),
        "sample_embedding_dim": sample_dim,
        "sample_ids": ids,
        "sample_metadatas": metadatas,
    }
    _safe_print(out)
    return 0


def cmd_export(args):
    client = _get_client()
    col = client.get_collection(name=args.collection)
    total = col.count()
    step = max(1, int(args.batch))
    written = 0
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # 逐批导出到 NDJSON：每行 {id, metadata, document?}
    with out_path.open('w', encoding='utf-8') as f:
        offset = 0
        while offset < total:
            # include 文段在不同版本行为有差异，做兼容
            result = None
            try:
                result = col.get(limit=step, offset=offset, include=["ids", "metadatas", "documents"])
            except TypeError:
                # 旧版本不支持 offset/include，退化为 peek（仅抽样，不保证完整导出）
                result = col.peek(limit=step)
                # 为避免死循环，直接置 offset = total
                offset = total

            ids = result.get('ids', []) or []
            metas = result.get('metadatas', []) or []
            docs = result.get('documents', []) or []

            # 对齐长度
            max_len = max(len(ids), len(metas), len(docs))
            for i in range(max_len):
                rec = {
                    "id": ids[i] if i < len(ids) else None,
                    "metadata": metas[i] if i < len(metas) else None,
                }
                if args.include_documents:
                    rec["document"] = docs[i] if i < len(docs) else None
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                written += 1

            if offset < total:
                offset += step

    _safe_print({
        "collection": getattr(col, 'name', args.collection),
        "count": total,
        "written": written,
        "out": str(out_path),
        "include_documents": bool(args.include_documents),
    })
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Chroma 向量库可视化/导出工具（只读）")
    sub = parser.add_subparsers(dest="command")

    p_list = sub.add_parser("list", help="列出所有集合及计数")
    p_list.set_defaults(func=cmd_list_collections)

    p_insp = sub.add_parser("inspect", help="抽样查看集合（ids/metadatas/样本向量维度）")
    p_insp.add_argument("--collection", required=True, help="集合名")
    p_insp.add_argument("--limit", type=int, default=3, help="抽样条数（默认3）")
    p_insp.set_defaults(func=cmd_inspect)

    p_exp = sub.add_parser("export", help="导出集合到 NDJSON（ids+metadatas，兼容可选 documents）")
    p_exp.add_argument("--collection", required=True, help="集合名")
    p_exp.add_argument("--out", required=True, help="输出文件路径（.ndjson）")
    p_exp.add_argument("--batch", type=int, default=500, help="批大小，默认500")
    p_exp.add_argument("--include-documents", action='store_true', help="若版本支持，导出 documents 字段")
    p_exp.set_defaults(func=cmd_export)

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())


