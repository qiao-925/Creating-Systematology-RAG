# Makefile for Creating-Systematology-RAG

# 默认目标：直接运行 make 将执行完整工作流
.DEFAULT_GOAL := all

.PHONY: help install test test-unit test-integration test-cov clean run dev ready start all

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
	@echo "  make test-github-e2e  - Run GitHub E2E tests (requires network)"
	@echo "  make test-performance - Run performance tests"
	@echo "  make test-cov         - Tests + coverage report"
	@echo "  make test-fast        - Fast tests (skip slow tests)"
	@echo ""
	@echo "🚀 Run Commands:"
	@echo "  make run              - Start Streamlit application"
	@echo "  make dev              - Development mode (install + fast test)"
	@echo ""
	@echo "🔄 Full Workflow:"
	@echo "  make ready            - Ready (install + full test)"
	@echo "  make start            - One-click start (ready + run)"
	@echo "  make all              - Same as make ready"
	@echo ""
	@echo "🧹 Clean Commands:"
	@echo "  make clean            - Clean generated files"

install:
	@echo "📦 Installing dependencies..."
	uv sync
	@echo ""
	@echo "💡 Tip: For GPU acceleration, please refer to README.md for manual installation of CUDA version PyTorch"

install-test:
	@echo "📦 Installing test dependencies..."
	uv sync --extra test

install-gpu:
	@echo "⚠️  Deprecated: Please refer to README.md for manual installation of GPU version PyTorch"
	@echo "   Install command: uv pip install --force-reinstall --index-url https://download.pytorch.org/whl/cu121 torch torchvision torchaudio"

test: install-test
	@echo "🧪 Running all tests..."
	uv run --no-sync pytest tests/ -v

test-unit: install-test
	@echo "🧪 Running unit tests..."
	uv run --no-sync pytest tests/unit -v

test-integration: install-test
	@echo "🧪 Running integration tests..."
	uv run --no-sync pytest tests/integration -v

test-github-e2e: install-test
	@echo "🔗 Running GitHub E2E tests..."
	@echo "⚠️  Note: Requires network connection and Git tool"
	@echo ""
	uv run --no-sync pytest tests/integration/test_github_e2e.py -v

test-performance: install-test
	@echo "⚡ Running performance tests..."
	uv run --no-sync pytest tests/performance -v

test-cov: install-test
	@echo "📊 Running tests and generating coverage report..."
	uv run --no-sync pytest tests/ --cov=src --cov-report=term-missing
	@echo "✓ Coverage report displayed in terminal"

test-fast: install-test
	@echo "⚡ Running fast tests..."
	uv run --no-sync pytest tests/ -v -m "not slow"

clean:
	@echo "🧹 Cleaning generated files..."
	rm -rf __pycache__
	rm -rf src/__pycache__
	rm -rf tests/__pycache__
	rm -rf tests/*/__pycache__
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf vector_store/*
	rm -rf sessions/*
	@echo "✓ Cleanup completed"

run:
	@echo "🚀 Starting Streamlit application..."
	@echo "⚠️  Note: If running for the first time, please execute make install to install dependencies"
	uv run --no-sync streamlit run app.py

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

