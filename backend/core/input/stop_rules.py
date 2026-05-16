"""CLDFlow input stop rules: saturation detection for retrieval."""

from __future__ import annotations

from llama_index.core import Document


def _jaccard_similarity(text_a: str, text_b: str, ngram_size: int = 3) -> float:
    """Compute Jaccard similarity between two texts using character n-grams."""
    def ngrams(text: str) -> set[str]:
        text = text.lower()
        return {text[i : i + ngram_size] for i in range(max(len(text) - ngram_size + 1, 0))}

    set_a = ngrams(text_a)
    set_b = ngrams(text_b)
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


def check_saturation(
    documents: list[Document],
    threshold: float = 0.9,
    window_size: int = 5,
) -> bool:
    """Detect diminishing returns in retrieved documents.

    Compares each new document against the running set. If the average
    similarity of the last `window_size` documents exceeds `threshold`,
    we've hit saturation.

    Args:
        documents: Retrieved documents in order.
        threshold: Jaccard similarity threshold for saturation (0-1).
        window_size: Number of recent docs to check.

    Returns:
        True if saturated (stop retrieving), False otherwise.
    """
    if len(documents) < window_size + 1:
        return False

    recent = documents[-window_size:]
    prior = documents[:-window_size]

    if not prior:
        return False

    # Build a combined fingerprint of all prior documents
    prior_text = " ".join(doc.text[:500] for doc in prior if doc.text)

    similarities: list[float] = []
    for doc in recent:
        if doc.text:
            sim = _jaccard_similarity(prior_text, doc.text[:500])
            similarities.append(sim)

    if not similarities:
        return False

    avg_similarity = sum(similarities) / len(similarities)
    return avg_similarity >= threshold


def get_saturation_stats(documents: list[Document], window_size: int = 5) -> dict[str, float]:
    """Return saturation metrics for diagnostics."""
    if len(documents) < 2:
        return {"avg_similarity": 0.0, "unique_ratio": 1.0, "count": float(len(documents))}

    recent = documents[-window_size:]
    prior = documents[:-window_size]
    prior_text = " ".join(doc.text[:500] for doc in prior if doc.text) if prior else ""

    similarities: list[float] = []
    for doc in recent:
        if doc.text and prior_text:
            similarities.append(_jaccard_similarity(prior_text, doc.text[:500]))

    return {
        "avg_similarity": sum(similarities) / len(similarities) if similarities else 0.0,
        "unique_ratio": 1.0 - (sum(similarities) / len(similarities) if similarities else 0.0),
        "count": float(len(documents)),
    }
