# Makefile for Creating-Systematology-RAG

# 默认目标：直接运行 make 将执行完整工作流
.DEFAULT_GOAL := all

.PHONY: help install test test-unit test-integration test-cov clean run dev ready start all env-init env-push env-pull e2e-smoke e2e-regression verify-observability

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
	@echo "  make run              - Start Streamlit application"
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
# 在 Windows 上，需要在输出 emoji 前设置编码
# 注意：Python 代码输出的 emoji 已经正确（通过 backend/encoding.py 设置）
# 这里主要解决 Makefile echo 命令的输出问题
#
# 问题分析：
# - Makefile 通过 cmd.exe 执行命令，cmd.exe 的 echo 输出显示在 PowerShell 控制台
# - PowerShell 控制台的编码（GBK）与 cmd.exe 设置的代码页（UTF-8）不一致
# - 解决方案：使用 PowerShell 的 Write-Host 代替 cmd.exe 的 echo
# - 或者：在 PowerShell 启动时设置编码（见 README.md）
ifeq ($(OS),Windows_NT)
    # Windows: Makefile 可能使用 Git Bash 的 sh.exe 或 cmd.exe
    # 检测 shell 类型，使用对应的命令设置 UTF-8
    # 注意：PowerShell 控制台的编码设置是独立的，无法通过 Makefile 直接改变
    # Python 代码的 emoji 输出已通过 backend/encoding.py 正确设置
    # Makefile 的 echo 乱码不影响功能
    ifdef COMSPEC
        # cmd.exe 环境
        SET_UTF8 = @chcp 65001 >nul 2>&1 || true
    else
        # Git Bash/其他 shell 环境，跳过编码设置（不影响 Python 输出）
        SET_UTF8 = @:
    endif
else
    # Linux/Mac: 直接使用 echo
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

test-performance: install-test
	@echo "⚡ Running performance tests..."
	uv run --no-sync pytest tests/performance -v

test-cov: install-test
	@echo "📊 Running tests and generating coverage report..."
	uv run --no-sync pytest tests/ --cov=backend --cov=frontend --cov-report=term-missing
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
	uv run --no-sync python scripts/env_sync.py init

env-push:
	@echo "🔐 Pushing encrypted .env to Gist..."
	uv run --no-sync python scripts/env_sync.py push

env-pull:
	@echo "🔐 Pulling .env from Gist..."
	uv run --no-sync python scripts/env_sync.py pull

# ==================== Clean ====================

clean:
	@echo "🧹 Cleaning generated files..."
	rm -rf __pycache__
	rm -rf backend/__pycache__
	rm -rf tests/__pycache__
	rm -rf tests/*/__pycache__
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf vector_store/*
	@echo "✓ Cleanup completed"

run:
	@echo "🚀 Starting Streamlit application..."
	@echo "⚠️  Note: If running for the first time, please execute make install to install dependencies"
	uv run --no-sync python -m streamlit run app.py

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

