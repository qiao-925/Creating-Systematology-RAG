"""CLDFlow CLD Specialist: extracts causal links from a single perspective.

Each Specialist is an independent LLM call that produces CausalLink objects.
Uses Pydantic schema validation for structured output, with instructor
integration when available for guaranteed schema compliance.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Literal

from llama_index.core.llms import LLM
from pydantic import BaseModel, Field

from backend.core.models import CausalLink, CLDNode
from backend.core.modules.cld.perspectives import CLDPerspective
from backend.infrastructure.logger import get_logger

logger = get_logger("cldflow.specialist")


class SpecialistNode(BaseModel):
    """Schema for a single node extracted by a specialist."""
    id: str
    label: str = Field(..., max_length=64)
    description: str = Field(default="", max_length=200)


class SpecialistLink(BaseModel):
    """Schema for a single causal link extracted by a specialist."""
    source: str
    target: str
    relation: Literal["influences", "causes", "enables", "inhibits", "supports", "requires"] = "influences"


class SpecialistOutput(BaseModel):
    """Schema for specialist LLM output. Used for validation and instructor."""
    nodes: list[SpecialistNode] = Field(..., min_length=1, max_length=20)
    links: list[SpecialistLink] = Field(..., min_length=1, max_length=30)

SPECIALIST_PROMPT = """You are a domain expert analyzing a research question from a specific perspective.

Your task: Extract causal relationships (cause-and-effect links) from the research question and documents.

Perspective: {perspective_name}
Role: {role_definition}
Research Question: {question}

{documents_section}

## Output Format
Return a JSON object with this exact structure:
{{
  "nodes": [
    {{"id": "n1", "label": "concept name", "description": "brief description"}}
  ],
  "links": [
    {{"source": "n1", "target": "n2", "relation": "influences|causes|enables|inhibits|supports|requires"}}
  ]
}}

Rules:
- Extract 3-8 nodes (concepts/variables)
- Extract 3-12 causal links between nodes
- Use clear, concise labels (max 64 chars)
- Each link must have a valid relation type
- All node IDs must be referenced in at least one link
- Focus on the most important causal relationships
"""


async def extract_causal_links(
    perspective: CLDPerspective,
    question: str,
    documents: list[Any],
    llm: LLM,
) -> dict[str, Any]:
    """Extract causal links from a single perspective.

    Uses instructor for structured output when available, falls back to
    manual JSON parsing with Pydantic validation.

    Args:
        perspective: The analysis perspective.
        question: Research question.
        documents: Input documents (Document objects or dicts with 'text' key).
        llm: LlamaIndex LLM instance.

    Returns:
        Dict with 'nodes', 'links', 'perspective_id', 'perspective_name'.
    """
    docs_text = ""
    if documents:
        doc_parts = []
        for i, doc in enumerate(documents[:3]):
            text = doc.text if hasattr(doc, "text") else str(doc.get("text", doc))
            doc_parts.append(f"Document {i+1}:\n{text[:1000]}")
        docs_text = "## Reference Documents\n" + "\n\n".join(doc_parts)

    role_str = json.dumps(perspective.role_definition, indent=2) if perspective.role_definition else "General analyst"

    prompt = SPECIALIST_PROMPT.format(
        perspective_name=perspective.name,
        role_definition=role_str,
        question=question,
        documents_section=docs_text,
    )

    try:
        output = await _extract_with_instructor(llm, prompt)
        result = {
            "nodes": [n.model_dump() for n in output.nodes],
            "links": [l.model_dump() for l in output.links],
        }
    except Exception:
        # Fallback: manual parse + Pydantic validation
        response = await llm.acomplete(prompt)
        result = _parse_and_validate(response.text)

    result["perspective_id"] = perspective.id
    result["perspective_name"] = perspective.name
    logger.info(
        "Specialist extraction complete",
        perspective=perspective.name,
        nodes=len(result.get("nodes", [])),
        links=len(result.get("links", [])),
    )
    return result


async def _extract_with_instructor(llm: LLM, prompt: str) -> SpecialistOutput:
    """Try instructor-based structured extraction.

    Creates an AsyncOpenAI client patched with instructor for guaranteed
    schema compliance. Raises if the LLM doesn't support OpenAI-compatible
    API or if instructor is unavailable.
    """
    import instructor
    from openai import AsyncOpenAI

    # Get the underlying API config from the LlamaIndex LLM
    api_key = getattr(llm, "api_key", None) or getattr(llm, "_api_key", None)
    api_base = getattr(llm, "api_base", None) or getattr(llm, "_api_base", None)
    model = getattr(llm, "model", None) or getattr(llm, "_model", None)

    if not api_key or not model:
        raise ValueError("LLM missing api_key or model for instructor")

    client = instructor.from_openai(AsyncOpenAI(api_key=api_key, base_url=api_base))
    output = await client.chat.completions.create(
        model=model,
        response_model=SpecialistOutput,
        messages=[{"role": "user", "content": prompt}],
        max_retries=2,
    )
    return output


def _parse_and_validate(text: str) -> dict[str, Any]:
    """Parse LLM response and validate through Pydantic schema.

    Extracts JSON from the response text, validates through SpecialistOutput,
    and returns a clean dict. Invalid entries are filtered out.
    """
    text = text.strip()

    # Extract JSON from markdown code block
    if "```json" in text:
        start = text.index("```json") + 7
        end = text.index("```", start)
        text = text[start:end].strip()
    elif "```" in text:
        start = text.index("```") + 3
        end = text.index("```", start)
        text = text[start:end].strip()

    # Find JSON object boundaries
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        brace_start = text.find("{")
        brace_end = text.rfind("}") + 1
        if brace_start != -1 and brace_end > brace_start:
            data = json.loads(text[brace_start:brace_end])
        else:
            return {"nodes": [], "links": [], "error": "Failed to parse LLM response"}

    # Validate through Pydantic — filters malformed entries automatically
    try:
        output = SpecialistOutput.model_validate(data)
        return {"nodes": [n.model_dump() for n in output.nodes], "links": [l.model_dump() for l in output.links]}
    except Exception as exc:
        logger.warning("Pydantic validation failed, using raw data", error=str(exc))
        # Best-effort: extract what we can
        nodes = []
        for node in data.get("nodes", []):
            if isinstance(node, dict) and "id" in node and "label" in node:
                try:
                    validated = SpecialistNode.model_validate(node)
                    nodes.append(validated.model_dump())
                except Exception:
                    continue
        links = []
        for link in data.get("links", []):
            if isinstance(link, dict) and "source" in link and "target" in link:
                try:
                    validated = SpecialistLink.model_validate(link)
                    links.append(validated.model_dump())
                except Exception:
                    continue
        return {"nodes": nodes, "links": links}


async def run_specialists_parallel(
    perspectives: list[CLDPerspective],
    question: str,
    documents: list[Any],
    llm: LLM,
) -> list[dict[str, Any]]:
    """Run multiple Specialists in parallel, one per perspective.

    Args:
        perspectives: List of analysis perspectives.
        question: Research question.
        documents: Input documents.
        llm: LlamaIndex LLM.

    Returns:
        List of specialist outputs (dicts with nodes, links, perspective_id).
    """
    tasks = [
        extract_causal_links(perspective, question, documents, llm)
        for perspective in perspectives
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    outputs: list[dict[str, Any]] = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error("Specialist failed", perspective=perspectives[i].name, error=str(result))
            outputs.append({
                "perspective_id": perspectives[i].id,
                "perspective_name": perspectives[i].name,
                "nodes": [],
                "links": [],
                "error": str(result),
            })
        else:
            outputs.append(result)

    return outputs
