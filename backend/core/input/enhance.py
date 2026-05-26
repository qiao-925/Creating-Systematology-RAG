"""Systematology input enhancement: HyDE and multi-query generation."""

from __future__ import annotations

import asyncio

from llama_index.core.llms import LLM


HYDE_PROMPT = """You are a research assistant. Given the following research question,
write a short hypothetical answer (2-3 paragraphs) that could appear in an academic paper.
This answer will be used to improve document retrieval — it does not need to be correct,
just plausible and specific enough to match relevant documents.

Research question: {question}

Hypothetical answer:"""


MULTI_QUERY_PROMPT = """You are a research assistant. Given the following research question,
generate {n} alternative phrasings that approach the same topic from different angles.
Each phrasing should be a standalone search query. Return them as a numbered list.

Research question: {question}

Alternative queries:"""


async def hyde_expand(question: str, llm: LLM) -> str:
    """Generate a hypothetical answer for HyDE-based retrieval enhancement."""
    prompt = HYDE_PROMPT.format(question=question)
    response = await llm.acomplete(prompt)
    return response.text.strip()


async def multi_query_generate(question: str, llm: LLM, n: int = 3) -> list[str]:
    """Generate N alternative query phrasings for broader retrieval."""
    prompt = MULTI_QUERY_PROMPT.format(question=question, n=n)
    response = await llm.acomplete(prompt)
    lines = response.text.strip().splitlines()
    queries: list[str] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Strip numbering: "1. query" → "query"
        if line[0].isdigit():
            dot_idx = line.find(".")
            if dot_idx != -1 and dot_idx < 4:
                line = line[dot_idx + 1:].strip()
        if line:
            queries.append(line)
    return queries[:n]


async def enhance_query(question: str, llm: LLM, n_queries: int = 3) -> tuple[str, list[str]]:
    """Run HyDE and multi-query in parallel. Returns (hyde_answer, alt_queries)."""
    hyde_task = hyde_expand(question, llm)
    multi_task = multi_query_generate(question, llm, n=n_queries)
    hyde_answer, alt_queries = await asyncio.gather(hyde_task, multi_task)
    return hyde_answer, alt_queries
