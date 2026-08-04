# Wayfinding — Makefile
# Three blocks: install & run / test / clean

.DEFAULT_GOAL := run

.PHONY: run test clean

# ════════════════════ Block 1 · Install & Run ════════════════════

# Default target: install deps, then start backend (:8000) & frontend (:3000)
run:
	uv sync
	cd web && npm install
	@trap 'kill 0' INT TERM; \
	(cd web && npm run dev) & \
	uv run uvicorn backend.fastapi.main:app --reload

# ════════════════════ Block 2 · Test ════════════════════

# Run all tests with coverage report
test:
	uv run pytest tests/ --cov=backend --cov-report=term-missing

# ════════════════════ Block 3 · Clean ════════════════════

# Wipe project-local caches and dependencies (.venv, node_modules)
clean:
	rm -rf .venv web/node_modules
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage web/.next
