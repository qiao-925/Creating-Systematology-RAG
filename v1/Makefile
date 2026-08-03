# Makefile for Systematology

# 默认目标：直接运行 make 将执行完整工作流
.DEFAULT_GOAL := all

.PHONY: help install test test-unit test-integration test-cov clean run dev ready start all env-init env-push env-pull env-example e2e-smoke e2e-regression verify-observability preload-models

# ==================== 完整工作流（默认） ====================

all: ready
	@echo ""
	@echo "✅ Project setup completed!"
	@echo "💡 Tip: Run make start to automatically start the application"
	@echo ""

# ==================== 帮助信息 ====================

help:
	@echo "=================================="
	@echo "Systematology RAG - Makefile"
	@echo "=================================="
	@echo ""
	@echo "💡 Quick Start:"
	@echo "  make                  - Default: Full workflow (install + test)"
	@echo "  make start            - Full process and start application"
	@echo ""
	@echo "📦 Install Commands:"
	@echo "  make install          - Install project dependencies"
	@echo "  make install-test     - Install test dependencies"
	@echo "  ⚠️  GPU version PyTorch requires manual installation (see README.md)"
	@echo ""
	@echo "🧪 Test Commands:"
	@echo "  make test             - Run all tests"
	@echo "  make test-unit        - Run unit tests"
	@echo "  make test-integration - Run integration tests"
	@echo "  make test-github-e2e  - Run GitHub E2E tests (skip sync, preserves CUDA PyTorch)"
	@echo "  make test-performance - Run performance tests"
	@echo "  make test-cov         - Tests + coverage report"
	@echo "  make test-fast        - Fast tests (skip slow tests)"
	@echo ""
	@echo "🚀 Run Commands:"
	@echo "  make run              - Start Next.js frontend"
	@echo "  make dev              - Development mode (install + fast test)"
	@echo ""
	@echo ""
	@echo "🔄 Full Workflow:"
	@echo "  make ready            - Ready (install + full test)"
	@echo "  make start            - One-click start (ready + run)"
	@echo "  make all              - Same as make ready"
	@echo ""
	@echo "🧹 Clean Commands:"
	@echo "  make clean            - Clean generated files"

# Windows PowerShell UTF-8 编码设置
ifeq ($(OS),Windows_NT)
    ifdef COMSPEC
        SET_UTF8 = @chcp 65001 >nul 2>&1 || true
    else
        SET_UTF8 = @:
    endif
else
    SET_UTF8 = @:
endif

install:
	@$(SET_UTF8)
	@echo "📦 Installing dependencies..."
	uv sync
	@echo ""
	@echo "💡 Tip: For GPU acceleration, please refer to README.md for manual installation of CUDA version PyTorch"

install-test:
	@$(SET_UTF8)
	@echo "📦 Installing test dependencies..."
	uv sync --extra test

test: install-test
	@echo "🧪 Running all tests..."
	uv run --no-sync pytest tests/ -v

test-unit: install-test
	@echo "🧪 Running unit tests..."
	uv run --no-sync pytest tests/unit -v

test-integration: install-test
	@echo "🧪 Running integration tests..."
	uv run --no-sync pytest tests/integration -v

test-github-e2e:
	@$(SET_UTF8)
	@echo "🔗 Running GitHub E2E tests..."
	@echo "⚠️  Note: Requires network connection and Git tool"
	@echo "💡 This command skips 'uv sync' to preserve manually installed CUDA PyTorch"
	@echo ""
	@echo "📦 Checking test dependencies..."
ifeq ($(OS),Windows_NT)
	@uv run --no-sync python -c "import pytest" 2>nul || (echo "❌ pytest not found. Installing test dependencies (excluding PyTorch)..." && uv pip install pytest pytest-cov pytest-mock pytest-benchmark pytest-asyncio && echo "✅ Test dependencies installed")
else
	@uv run --no-sync python -c "import pytest" 2>/dev/null || (echo "❌ pytest not found. Installing test dependencies (excluding PyTorch)..." && uv pip install pytest pytest-cov pytest-mock pytest-benchmark pytest-asyncio && echo "✅ Test dependencies installed")
endif
	@echo ""
	INDEX_MAX_BATCHES=5 uv run --no-sync pytest tests/integration/test_github_e2e.py -v -s --log-cli-level=INFO

test-cov: install-test
	@echo "📊 Running tests and generating coverage report..."
	uv run --no-sync pytest tests/ --cov=backend --cov-report=term-missing
	@echo "✓ Coverage report displayed in terminal"

test-fast: install-test
	@echo "⚡ Running fast tests..."
	uv run --no-sync pytest tests/ -v -m "not slow"

# ==================== E2E Verification ====================

e2e-smoke:
	@echo "🔬 Running E2E smoke test (1 question)..."
	uv run --no-sync pytest tests/e2e/test_research_e2e.py::TestResearchSmoke -v -s -m e2e

e2e-regression:
	@echo "🔬 Running E2E regression tests (all questions)..."
	uv run --no-sync pytest tests/e2e/test_research_e2e.py::TestResearchRegression -v -s -m e2e

verify-observability:
	@echo "🔍 Verifying observability & evaluation..."
	uv run --no-sync python scripts/verify_observability.py

# ==================== Env Sync ====================

env-init:
	@echo "🔐 Initializing encrypted env sync..."
	@gh auth status >/dev/null 2>&1 || (echo "❌ gh not authenticated. Run: gh auth login" && exit 1)
	uv run --no-sync python scripts/env_sync.py init

env-push:
	@echo "🔐 Pushing encrypted .env to Gist..."
	@gh auth status >/dev/null 2>&1 || (echo "❌ gh not authenticated. Run: gh auth login" && exit 1)
	uv run --no-sync python scripts/env_sync.py push

env-pull:
	@echo "🔐 Pulling .env from Gist..."
	@gh auth status >/dev/null 2>&1 || (echo "❌ gh not authenticated. Run: gh auth login" && exit 1)
	uv run --no-sync python scripts/env_sync.py pull

env-example:
	@echo "📋 Copying .env.example to .env..."
	@if exist .env (echo "⚠️  .env already exists. Delete it first.") else (cp .env.example .env && echo "✅ Created .env from template. Edit it with your API keys.")

# ==================== Preload Models ====================

preload-models:
	@echo "📥 Pre-downloading sentence-transformers models..."
	uv run --no-sync python scripts/preload_models.py

# ==================== Clean ====================

clean:
	@echo "🧹 Cleaning generated files..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage
	@echo "✓ Cleanup completed"

run:
	@echo "🚀 Starting Next.js frontend..."
	@echo "⚠️  Note: If running for the first time, please execute 'cd web && npm install' first"
	cd web && npm run dev

dev: install install-test test-fast
	@echo "🎉 Development environment ready!"
	@echo "Use make run to start the application"

# ==================== Full Workflow ====================

ready: install install-test test-cov
	@echo ""
	@echo "✅ =================================="
	@echo "✅ Project ready!"
	@echo "✅ =================================="
	@echo ""
	@echo "📊 Completed:"
	@echo "  ✓ Installed all dependencies"
	@echo "  ✓ Ran full test suite"
	@echo "  ✓ Generated coverage report"
	@echo ""
	@echo "🚀 Next step:"
	@echo "  Run make run or make start to start the application"
	@echo ""

start: ready
	@echo ""
	@echo "🚀 Starting application..."
	@echo ""
	@echo "⚠️  Note: Ensure CUDA version PyTorch is installed (if using GPU)"
	@$(MAKE) run
