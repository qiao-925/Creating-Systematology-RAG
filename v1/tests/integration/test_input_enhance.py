"""Integration tests: input/enhance.py — query enhancement with mock LLM."""

from __future__ import annotations

import pytest

from backend.core.input.enhance import hyde_expand, multi_query_generate, enhance_query
from tests.fixtures.systematology_fixtures import MockLLM


class TestHydeExpand:
    @pytest.mark.asyncio
    async def test_generates_answer(self):
        llm = MockLLM(responses={"hypothetical answer": "Subsidies stimulate demand by lowering costs."})
        result = await hyde_expand("How do subsidies affect housing?", llm)
        assert len(result) > 0
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_question_appears_in_result(self):
        llm = MockLLM()
        result = await hyde_expand("test question?", llm)
        assert isinstance(result, str)


class TestMultiQueryGenerate:
    @pytest.mark.asyncio
    async def test_generates_queries(self):
        response = "1. How do government subsidies affect the housing market?\n2. What is the relationship between fiscal policy and real estate?\n3. Impact of public spending on housing affordability"
        llm = MockLLM(responses={"alternative phrasings": response})

        result = await multi_query_generate("How do subsidies affect housing?", llm, n=3)
        assert len(result) <= 3
        assert all(isinstance(q, str) for q in result)

    @pytest.mark.asyncio
    async def test_respects_n_limit(self):
        response = "\n".join([f"{i}. Query {i}" for i in range(1, 11)])
        llm = MockLLM(responses={"alternative phrasings": response})

        result = await multi_query_generate("test", llm, n=2)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_empty_lines_filtered(self):
        response = "1. Query one\n\n\n2. Query two\n"
        llm = MockLLM(responses={"alternative phrasings": response})

        result = await multi_query_generate("test", llm, n=5)
        assert len(result) == 2


class TestEnhanceQuery:
    @pytest.mark.asyncio
    async def test_parallel_execution(self):
        multi_response = "1. Alternative query one\n2. Alternative query two"
        llm = MockLLM(responses={
            "alternative phrasings": multi_response,
        })

        hyde_answer, alt_queries = await enhance_query("test question?", llm, n_queries=2)
        assert isinstance(hyde_answer, str)
        assert isinstance(alt_queries, list)
        assert len(alt_queries) <= 2
