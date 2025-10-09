# Makefile for Creating-Systematology-RAG

# 默认目标：直接运行 make 将执行完整工作流
.DEFAULT_GOAL := all

.PHONY: help install test test-unit test-integration test-cov clean run dev ready start all

# ==================== 完整工作流（默认） ====================

all: ready
	@echo ""
	@echo "✅ 项目准备完成！"
	@echo "💡 提示: 运行 'make start' 可以自动启动应用"
	@echo ""

# ==================== 帮助信息 ====================

help:
	@echo "=================================="
	@echo "系统科学知识库RAG - Makefile"
	@echo "=================================="
	@echo ""
	@echo "💡 快速开始："
	@echo "  make                  - 默认：完整工作流（安装+测试）"
	@echo "  make start            - 完整流程并启动应用"
	@echo ""
	@echo "📦 安装命令："
	@echo "  make install          - 安装项目依赖"
	@echo "  make install-test     - 安装测试依赖"
	@echo ""
	@echo "🧪 测试命令："
	@echo "  make test             - 运行所有测试"
	@echo "  make test-unit        - 运行单元测试"
	@echo "  make test-integration - 运行集成测试"
	@echo "  make test-performance - 运行性能测试"
	@echo "  make test-cov         - 测试 + 覆盖率报告"
	@echo "  make test-fast        - 快速测试（跳过慢速测试）"
	@echo ""
	@echo "🚀 运行命令："
	@echo "  make run              - 启动Streamlit应用"
	@echo "  make dev              - 开发模式（安装+快速测试）"
	@echo ""
	@echo "🔄 完整工作流："
	@echo "  make ready            - 准备就绪（安装+完整测试）"
	@echo "  make start            - 一键启动（ready + run）"
	@echo "  make all              - 同 make ready"
	@echo ""
	@echo "🧹 清理命令："
	@echo "  make clean            - 清理生成的文件"

install:
	@echo "📦 安装依赖..."
	uv sync

install-test:
	@echo "📦 安装测试依赖..."
	uv sync --extra test

test: install-test
	@echo "🧪 运行所有测试..."
	uv run pytest tests/ -v

test-unit: install-test
	@echo "🧪 运行单元测试..."
	uv run pytest tests/unit -v

test-integration: install-test
	@echo "🧪 运行集成测试..."
	uv run pytest tests/integration -v

test-performance: install-test
	@echo "⚡ 运行性能测试..."
	uv run pytest tests/performance -v

test-cov: install-test
	@echo "📊 运行测试并生成覆盖率报告..."
	uv run pytest tests/ --cov=src --cov-report=term-missing
	@echo "✓ 覆盖率报告已显示在终端"

test-fast: install-test
	@echo "⚡ 运行快速测试..."
	uv run pytest tests/ -v -m "not slow"

clean:
	@echo "🧹 清理生成的文件..."
	rm -rf __pycache__
	rm -rf src/__pycache__
	rm -rf tests/__pycache__
	rm -rf tests/*/__pycache__
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf vector_store/*
	rm -rf sessions/*
	@echo "✓ 清理完成"

run: install
	@echo "🚀 启动Streamlit应用..."
	uv run streamlit run app.py

dev: install install-test test-fast
	@echo "🎉 开发环境准备完成！"
	@echo "使用 'make run' 启动应用"

# ==================== 完整工作流 ====================

ready: install install-test test-cov
	@echo ""
	@echo "✅ =================================="
	@echo "✅ 项目准备就绪！"
	@echo "✅ =================================="
	@echo ""
	@echo "📊 已完成："
	@echo "  ✓ 安装所有依赖"
	@echo "  ✓ 运行完整测试套件"
	@echo "  ✓ 生成覆盖率报告"
	@echo ""
	@echo "🚀 下一步："
	@echo "  运行 'make run' 或 'make start' 启动应用"
	@echo ""

start: ready
	@echo ""
	@echo "🚀 正在启动应用..."
	@echo ""
	@$(MAKE) run

