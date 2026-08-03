"""Systematology input pipeline: orchestrates enhance → retrieve → stop_rules."""

from __future__ import annotations

from typing import Any

from llama_index.core import Document
from llama_index.core.llms import LLM

from backend.core.input.enhance import enhance_query
from backend.core.input.retrieve import source_tiered_retrieve
from backend.core.input.stop_rules import check_saturation
from backend.core.models import ParsedQuery


async def run_input_pipeline(
    question: str,
    llm: LLM,
    retriever,
    max_retrieve_rounds: int = 3,
    top_k_per_round: int = 5,
    saturation_threshold: float = 0.9,
    context: dict[str, Any] | None = None,
) -> ParsedQuery:
    """Run the full input pipeline: enhance → retrieve → stop check.

    Args:
        question: Raw research question.
        llm: LlamaIndex LLM for query enhancement.
        retriever: LlamaIndex retriever for document retrieval.
        max_retrieve_rounds: Maximum retrieval rounds before forced stop.
        top_k_per_round: Documents per retrieval round.
        saturation_threshold: Jaccard similarity threshold for saturation.
        context: Optional additional context to attach.

    Returns:
        ParsedQuery with enhanced documents and context.
    """
    # Step 1: Enhance query
    hyde_answer, alt_queries = await enhance_query(question, llm)

    # Step 2: Build query list (original + HyDE + alternatives)
    all_queries = [question, hyde_answer] + alt_queries

    # Step 3: Iterative retrieval with saturation check
    all_docs: list[Document] = []
    for round_num in range(max_retrieve_rounds):
        batch = source_tiered_retrieve(
            queries=all_queries,
            retriever=retriever,
            top_k=top_k_per_round,
        )
        if not batch:
            break
        all_docs.extend(batch)
        if check_saturation(all_docs, threshold=saturation_threshold):
            break

    # Step 4: Build ParsedQuery
    enhanced_context: dict[str, Any] = {
        "hyde_answer": hyde_answer,
        "alternative_queries": alt_queries,
        "retrieve_rounds": min(round_num + 1, max_retrieve_rounds),
        "total_documents": len(all_docs),
        **(context or {}),
    }

    return ParsedQuery(
        query_text=question,
        documents=all_docs,
        context=enhanced_context,
    )
