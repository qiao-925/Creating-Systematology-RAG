"""Systematology input retrieval: source-tiered document retrieval."""

from __future__ import annotations

from llama_index.core import Document

# Source tier ranking (lower = higher priority)
SOURCE_TIERS: dict[str, int] = {
    "academic": 1,
    "journal": 1,
    "arxiv": 1,
    "government": 2,
    "gov": 2,
    "worldbank": 2,
    "oecd": 2,
    "fred": 2,
    "report": 3,
    "news": 4,
    "blog": 5,
    "unknown": 5,
}


def _get_source_tier(doc: Document) -> int:
    """Determine tier from document metadata."""
    source = doc.metadata.get("source", "").lower()
    source_type = doc.metadata.get("source_type", "").lower()
    for key in (source, source_type):
        for tier_key, tier_val in SOURCE_TIERS.items():
            if tier_key in key:
                return tier_val
    return SOURCE_TIERS["unknown"]


def _content_hash(doc: Document) -> str:
    """Simple content fingerprint for deduplication."""
    text = doc.text or ""
    # Use first 200 chars as rough fingerprint
    return text[:200].strip()


def source_tiered_retrieve(
    queries: list[str],
    retriever,
    top_k: int = 10,
) -> list[Document]:
    """Retrieve documents across multiple queries, rank by source tier, deduplicate.

    Args:
        queries: List of query strings (original + enhanced).
        retriever: LlamaIndex retriever with .retrieve(query) -> list[NodeWithScore].
        top_k: Maximum documents to return.

    Returns:
        Deduplicated, tier-ranked list of Documents.
    """
    seen_hashes: set[str] = set()
    all_docs: list[Document] = []

    for query in queries:
        try:
            nodes = retriever.retrieve(query)
        except Exception:
            continue
        for node in nodes:
            doc = Document(
                text=node.node.get_content(),
                metadata=dict(node.node.metadata) if node.node.metadata else {},
            )
            fingerprint = _content_hash(doc)
            if fingerprint in seen_hashes:
                continue
            seen_hashes.add(fingerprint)
            doc.metadata["_relevance_score"] = node.score if node.score else 0.0
            all_docs.append(doc)

    # Sort: lower tier first (better source), then higher relevance score
    all_docs.sort(key=lambda d: (_get_source_tier(d), -d.metadata.get("_relevance_score", 0)))
    return all_docs[:top_k]
