import json
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st
from src.config import config


st.set_page_config(page_title="Chroma Viewer", layout="wide")


@st.cache_resource(show_spinner=False)
def get_chroma_client():
    try:
        import chromadb
        from src.config import config
        
        if not config.CHROMA_CLOUD_API_KEY or not config.CHROMA_CLOUD_TENANT or not config.CHROMA_CLOUD_DATABASE:
            return None, "Chroma Cloud配置不完整，请设置以下环境变量：CHROMA_CLOUD_API_KEY, CHROMA_CLOUD_TENANT, CHROMA_CLOUD_DATABASE"
        
        client = chromadb.CloudClient(
            api_key=config.CHROMA_CLOUD_API_KEY,
            tenant=config.CHROMA_CLOUD_TENANT,
            database=config.CHROMA_CLOUD_DATABASE
        )
        return client, None
    except Exception as e:
        return None, str(e)


def list_collections(client) -> List[Dict[str, Any]]:
    cols = client.list_collections() if hasattr(client, 'list_collections') else client.get_collections()
    out: List[Dict[str, Any]] = []
    for col in cols:
        info: Dict[str, Any] = {
            "name": getattr(col, 'name', None),
            "id": getattr(col, 'id', None),
            "embedding_dim_meta": (getattr(col, 'metadata', {}) or {}).get('embedding_dimension') if getattr(col, 'metadata', None) else None,
        }
        try:
            info["count"] = col.count()
        except Exception as e:
            info["count_error"] = str(e)
        out.append(info)
    return out


def safe_compute_sample_dim(embs) -> int | None:
    try:
        if embs is None:
            return None
        if isinstance(embs, (list, tuple)):
            if len(embs) == 0:
                return None
            v0 = embs[0]
            if isinstance(v0, (list, tuple)):
                return len(v0)
            if hasattr(v0, 'shape') and len(getattr(v0, 'shape')) >= 1:
                return int(v0.shape[-1])
            return None
        if hasattr(embs, 'size') and hasattr(embs, 'shape'):
            if int(getattr(embs, 'size', 0)) == 0:
                return None
            sh = getattr(embs, 'shape')
            if len(sh) == 2:
                return int(sh[1])
            if len(sh) == 1:
                return int(sh[0])
        return None
    except Exception:
        return None


def peek_collection(col, limit: int = 5) -> Dict[str, Any]:
    try:
        s = col.peek(limit=limit)
    except TypeError:
        s = col.peek()
    if isinstance(s, dict):
        ids = s.get('ids') if s.get('ids') is not None else []
        metas = s.get('metadatas') if s.get('metadatas') is not None else []
        # 注意：embeddings 可能是 numpy 数组，禁止使用 "or []" 触发布尔判断
        embs = s.get('embeddings') if 'embeddings' in s else None
        docs = s.get('documents') if s.get('documents') is not None else []
    else:
        ids, metas, docs, embs = [], [], [], None
    return {
        "ids": ids,
        "metadatas": metas,
        "documents": docs,
        "embedding_dim": safe_compute_sample_dim(embs),
    }


def run_query(col, query: str, top_k: int = 5) -> Dict[str, Any]:
    # 仅计算 query 的 embedding，避免使用 IndexManager 触发重建逻辑
    from src.indexer import load_embedding_model
    embed = load_embedding_model(force_reload=False)
    qv = embed.get_query_embedding(query)
    try:
        res = col.query(query_embeddings=[qv], n_results=top_k, include=["ids", "metadatas", "documents", "distances"])
    except TypeError:
        # 旧版不支持 include，降级只拿 ids/metadatas
        res = col.query(query_embeddings=[qv], n_results=top_k)
    return {
        "ids": res.get('ids', [[]])[0] if isinstance(res.get('ids', None), list) else [],
        "metadatas": res.get('metadatas', [[]])[0] if isinstance(res.get('metadatas', None), list) else [],
        "documents": res.get('documents', [[]])[0] if isinstance(res.get('documents', None), list) else [],
        "distances": res.get('distances', [[]])[0] if isinstance(res.get('distances', None), list) else [],
    }


def main():
    st.title("🔎 Chroma Viewer")
    st.caption("只读浏览集合 / 抽样 / 相似检索，不会修改或删除数据")

    client, err = get_chroma_client()
    if err:
        st.error(f"无法连接 Chroma: {err}")
        st.stop()

    with st.sidebar:
        st.subheader("集合列表")
        cols = list_collections(client)
        if not cols:
            st.info("未发现集合。")
        else:
            for c in cols:
                st.write(f"- {c.get('name')} (count={c.get('count','?')}, dim={c.get('embedding_dim_meta')})")

        names = [c.get('name') for c in cols]
        default_name = None
        # 优先选择配置中的默认集合名称
        if config.CHROMA_COLLECTION_NAME in names:
            default_name = config.CHROMA_COLLECTION_NAME
        sel = st.selectbox("选择集合", names, index=(names.index(default_name) if default_name in names else 0) if names else None)
        refresh = st.button("刷新列表")
        if refresh:
            st.experimental_rerun()

    if not names:
        st.stop()

    col = client.get_collection(name=sel)
    cnt = col.count()
    md = getattr(col, 'metadata', None) or {}

    st.markdown(f"**集合**: `{sel}`  ·  **条数**: {cnt}  ·  **metadata.dim**: {md.get('embedding_dimension')}")

    with st.expander("抽样预览", expanded=True):
        limit = st.slider("抽样条数", 1, 50, 5)
        sample = peek_collection(col, limit=limit)
        st.write(f"样本向量维度: {sample.get('embedding_dim')}")
        if sample.get('metadatas'):
            st.write("metadatas（前几条）")
            st.json(sample['metadatas'])
        if sample.get('documents'):
            st.write("documents（前几条）")
            st.json(sample['documents'])

    with st.expander("相似检索（向量）", expanded=True):
        q = st.text_input("查询文本")
        k = st.slider("TopK", 1, 20, 5)
        go = st.button("检索")
        if go and q.strip():
            with st.spinner("检索中..."):
                try:
                    res = run_query(col, q.strip(), top_k=k)
                    rows = []
                    for i in range(len(res.get('ids', []))):
                        rows.append({
                            "id": res['ids'][i] if i < len(res['ids']) else None,
                            "distance": res['distances'][i] if i < len(res.get('distances', [])) else None,
                            "metadata": res['metadatas'][i] if i < len(res['metadatas']) else None,
                            "document": res['documents'][i] if i < len(res.get('documents', [])) else None,
                        })
                    st.dataframe(rows, use_container_width=True)
                except Exception as e:
                    st.error(f"检索失败: {e}")


if __name__ == "__main__":
    main()


