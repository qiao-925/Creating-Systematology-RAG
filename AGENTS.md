# AGENTS.md

This repository is wired to `agent-nightshift`.

## Repository Context

- This is a `Python 3.12 + uv + Streamlit` repository. The `frontend/` directory is still Python code, not a Node frontend.
- Read `docs/architecture.md` before making structural changes.
- When architecture decisions are involved, consult `skills/cs-rag-architecture-guideline/SKILL.md`.

## Default Expectations

- Keep changes narrow and directly tied to the current Issue phase.
- Prefer the smallest patch that makes the current phase and repository checks pass.
- Use `.agent/runtime/issue-plan.md` as the canonical execution context for the current run.
- Preserve the current layer boundaries. Do not introduce cross-layer shortcuts that couple frontend, business, and infrastructure code in new ways.
- When the current phase is complete and verify passes, use `agent-nightshift checkpoint`.
- Do not change dependencies, authentication, public APIs, model/provider defaults, or vector-store persistence semantics unless the task explicitly allows it; otherwise escalate to a human.

## Verification Expectations

- Follow `.agent/project.yaml` for the default `setup` and `verify` commands.
- For narrow fixes, add or update the smallest relevant test first, then run the configured verify step.
- Do not treat performance tests or GitHub E2E tests as the default nightly verification path.

## Writing Boundaries

- Do not modify `data/`, `logs/`, `sessions/`, `.env`, `.venv/`, or `agent-task-log/` unless the current Issue explicitly requires it.
- `agent-nightshift` will also enforce `workspace.writable_paths` from `.agent/project.yaml`. Treat that file as the source of truth for what may be modified.
