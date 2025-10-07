# Makefile for Creating-Systematology-RAG

.PHONY: help install test test-unit test-integration test-cov clean run dev

help:
	@echo "系统科学知识库RAG - Makefile"
	@echo ""
	@echo "可用命令："
	@echo "  make install          - 安装依赖"
	@echo "  make install-test     - 安装测试依赖"
	@echo "  make test             - 运行所有测试"
	@echo "  make test-unit        - 运行单元测试"
	@echo "  make test-integration - 运行集成测试"
	@echo "  make test-cov         - 运行测试并生成覆盖率报告"
	@echo "  make test-fast        - 运行快速测试（跳过慢速测试）"
	@echo "  make clean            - 清理生成的文件"
	@echo "  make run              - 启动Streamlit应用"
	@echo "  make dev              - 开发模式（安装+测试+运行）"

install:
	@echo "📦 安装依赖..."
	uv sync

install-test:
	@echo "📦 安装测试依赖..."
	uv sync --extra test

test: install-test
	@echo "🧪 运行所有测试..."
	pytest tests/ -v

test-unit: install-test
	@echo "🧪 运行单元测试..."
	pytest tests/unit -v

test-integration: install-test
	@echo "🧪 运行集成测试..."
	pytest tests/integration -v

test-performance: install-test
	@echo "⚡ 运行性能测试..."
	pytest tests/performance -v

test-cov: install-test
	@echo "📊 运行测试并生成覆盖率报告..."
	pytest tests/ --cov=src --cov-report=html --cov-report=term-missing
	@echo "✓ 覆盖率报告: htmlcov/index.html"

test-fast: install-test
	@echo "⚡ 运行快速测试..."
	pytest tests/ -v -m "not slow"

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
	streamlit run app.py

dev: install install-test test-fast
	@echo "🎉 开发环境准备完成！"
	@echo "使用 'make run' 启动应用"

