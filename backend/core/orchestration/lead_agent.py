"""Systematology Lead Agent: orchestrates CLD → FCM → D2D pipeline.

Uses LlamaIndex AgentWorkflow + ReActAgent, following the pattern
established in backend/business/research_kernel/agent.py.
"""

from __future__ import annotations

from typing import Any

from llama_index.core.agent.workflow import AgentWorkflow, ReActAgent
from llama_index.core.llms import LLM

from backend.core.models import RunContext, StructuredFailureReport, StructuredReport
from backend.core.orchestration.prompts import LEAD_AGENT_SYSTEM_PROMPT
from backend.core.orchestration.tools import create_lead_agent_tools
from backend.infrastructure.logger import get_logger

logger = get_logger("systematology.lead_agent")

DEFAULT_MAX_ITERATIONS = 30
DEFAULT_TIMEOUT_SECONDS = 180.0


class LeadAgent:
    """Systematology Lead Agent: orchestrates the full analysis pipeline."""

    def __init__(
        self,
        llm: LLM,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        judge_model: str = "deepseek-chat",
    ):
        self._llm = llm
        self._max_iterations = max_iterations
        self._timeout_seconds = timeout_seconds
        self._judge_model = judge_model

    async def run(
        self,
        question: str,
        documents: list[Any] | None = None,
        run_context: RunContext | None = None,
    ) -> StructuredReport | StructuredFailureReport:
        """Execute the full Systematology pipeline.

        Args:
            question: Research question.
            documents: Input documents (LlamaIndex Document objects or dicts).
            run_context: Optional RunContext (created if not provided).

        Returns:
            StructuredReport on success, StructuredFailureReport on failure.
        """
        if run_context is None:
            run_context = RunContext()

        question = question.strip()
        if not question:
            return StructuredFailureReport(
                run_id=run_context.run_id,
                stage="input",
                reason="Research question is empty",
            )

        tools = create_lead_agent_tools(run_context, llm=self._llm, judge_model=self._judge_model)

        agent = ReActAgent(
            name="SystematologyLeadAgent",
            description="Research pipeline orchestrator: CLD → FCM → D2D → Report",
            system_prompt=LEAD_AGENT_SYSTEM_PROMPT,
            tools=tools,
            llm=self._llm,
        )

        workflow = AgentWorkflow(
            agents=[agent],
            root_agent="SystematologyLeadAgent",
            timeout=self._timeout_seconds,
        )

        # Build user message with context
        doc_summary = ""
        if documents:
            doc_texts = []
            for i, doc in enumerate(documents[:5]):
                if hasattr(doc, "text"):
                    doc_texts.append(f"[Doc {i+1}] {doc.text[:300]}")
                elif isinstance(doc, dict):
                    doc_texts.append(f"[Doc {i+1}] {str(doc)[:300]}")
            doc_summary = "\n".join(doc_texts)

        user_msg = f"Research question: {question}"
        if doc_summary:
            user_msg += f"\n\nAvailable documents:\n{doc_summary}"
        else:
            user_msg += "\n\nNo documents provided. Generate a CLD from general knowledge."

        logger.info("Lead Agent starting", question=question[:80], doc_count=len(documents or []))

        try:
            response = await workflow.run(
                user_msg=user_msg,
                max_iterations=self._max_iterations,
            )
            logger.info(
                "Lead Agent completed",
                tool_calls=run_context.tool_calls,
                failures=len(run_context.failures),
            )

            # Try to extract structured report from response
            response_text = str(response)
            if run_context.failures:
                last_failure = run_context.failures[-1]
                return StructuredFailureReport(
                    run_id=run_context.run_id,
                    stage=last_failure.stage,
                    reason=last_failure.reason,
                    details=last_failure.details,
                )

            return StructuredReport(
                cld_visualization={"raw_response": response_text[:2000]},
                synthesized_insights=response_text[:5000],
                evidence_tracing={
                    "run_id": run_context.run_id,
                    "tool_calls": run_context.tool_calls,
                },
            )

        except TimeoutError:
            logger.warning("Lead Agent timeout", timeout=self._timeout_seconds)
            return StructuredFailureReport(
                run_id=run_context.run_id,
                stage="orchestration",
                reason=f"Pipeline timed out after {self._timeout_seconds}s",
            )
        except Exception as exc:
            logger.error("Lead Agent error", error=str(exc))
            return StructuredFailureReport(
                run_id=run_context.run_id,
                stage="orchestration",
                reason=f"Pipeline error: {exc}",
            )
