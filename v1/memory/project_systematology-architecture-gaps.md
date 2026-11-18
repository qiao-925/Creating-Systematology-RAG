---
name: systematology-architecture-gaps
description: Architecture audit findings: guardrails not called, sentence-transformers missing, rater/uncertainty/input-pipeline detached, two-stage method absent
metadata:
  type: project
---

2026-05-31 architecture assessment found three categories of drift from ARCHITECTURE.md commitments:

**Fatal (2):** 5 guardrail functions in guardrails.py have zero call sites; node merging uses string trigrams only (sentence-transformers path missing, threshold lowered from 0.8→0.6, docstring claims it's intentional).

**Medium (3):** FCM rater.py (LLM 7-level edge rating) not wired into run_fcm_analysis; D2D uncertainty.py (confidence propagation) not called; input pipeline (HyDE + multi-query enhancement) entirely bypassed by Lead Agent.

**Minor (3):** DDC classifier is keyword-only (LLM path is stub); D2D sensitivity rebuilds weights from SharedCLD edges instead of consuming FCM WeightedFCM; Lead Agent system prompt too thin for meaningful orchestration decisions.

Root cause pattern: modules are implemented (code quality OK) but the integration layer (tools.py / lead_agent.py) doesn't wire them together.

**Why:** all RAG/retrieval/infrastructure code was built first; the Systematology core (CLD→FCM→D2D pipeline) was layered on top as MVP. The integration is shallow — tools.py acts as thin wrappers without invoking guardrails, rater, uncertainty, or input enhancement.

**How to apply:** when working on pipeline improvements, prioritize wiring existing modules over writing new code. See [[论文改进清单]] for tracked action items.
