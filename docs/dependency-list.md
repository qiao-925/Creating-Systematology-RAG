# Project Dependency List

This document summarizes the current project dependencies used for local development, backend execution, frontend build, and testing.

## 1. Python project dependencies

Source of truth: `pyproject.toml`

### Core runtime dependencies

- `llama-index`
- `llama-index-llms-litellm`
- `llama-index-embeddings-huggingface`
- `llama-index-vector-stores-chroma`
- `llama-index-readers-file`
- `llama-index-readers-web`
- `chromadb`
- `openai`
- `python-dotenv`
- `pyyaml`
- `tqdm`
- `huggingface-hub`
- `pydantic-settings`
- `structlog`
- `requests`
- `fastapi`
- `uvicorn[standard]`
- `sse-starlette`
- `networkx`
- `sentence-transformers`
- `instructor`
- `numpy`

### Test dependencies

Installed via the `test` extra:

- `pytest`
- `coverage`
- `pytest-cov`
- `pytest-mock`
- `pytest-benchmark`
- `pytest-asyncio`

### Evaluation dependencies

Installed via the `evaluation` extra:

- `ragas`

## 2. Frontend dependencies

Source of truth: `web/package.json`

### Runtime dependencies

- `@ai-sdk/react`
- `@base-ui/react`
- `ai`
- `class-variance-authority`
- `clsx`
- `lucide-react`
- `next`
- `next-intl`
- `next-themes`
- `react`
- `react-dom`
- `react-markdown`
- `remark-gfm`
- `shadcn`
- `tailwind-merge`
- `tw-animate-css`
- `zustand`

### Frontend development dependencies

- `@tailwindcss/postcss`
- `@types/node`
- `@types/react`
- `@types/react-dom`
- `eslint`
- `eslint-config-next`
- `tailwindcss`
- `typescript`

## 3. Tooling and workflow dependencies

These are not application dependencies, but they are required for the project workflow:

- `uv` for Python dependency resolution and environment sync
- `npm` for frontend dependency installation
- `gh` for encrypted environment sync workflows
- `make` for local orchestration
- Docker for containerized deployment and reproducible builds

## 4. Context7 installation

Context7 is configured as an MCP server for Cursor via `.mcp.json`.

Recommended server configuration:

- Server name: `context7`
- Server URL: `https://mcp.context7.com/mcp`

If you also want the CLI-based setup, use the official bootstrap command:

```bash
npx ctx7 setup
```

That command can install the Cursor-oriented setup and generate the appropriate agent guidance.
