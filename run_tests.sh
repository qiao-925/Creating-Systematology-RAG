#!/bin/bash
# 测试运行脚本

set -e

echo "=================================="
echo "系统科学知识库RAG - 测试运行器"
echo "=================================="

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查测试依赖
echo -e "\n${YELLOW}[1/5] 检查测试依赖...${NC}"
if ! python -c "import pytest" 2>/dev/null; then
    echo -e "${RED}pytest未安装！正在安装测试依赖...${NC}"
    uv sync --extra test
    echo -e "${GREEN}✓ 测试依赖安装完成${NC}"
else
    echo -e "${GREEN}✓ 测试依赖已安装${NC}"
fi

# 运行单元测试
echo -e "\n${YELLOW}[2/5] 运行单元测试...${NC}"
pytest tests/unit -v --tb=short
echo -e "${GREEN}✓ 单元测试完成${NC}"

# 运行集成测试
echo -e "\n${YELLOW}[3/5] 运行集成测试...${NC}"
pytest tests/integration -v --tb=short
echo -e "${GREEN}✓ 集成测试完成${NC}"

# 运行性能测试
echo -e "\n${YELLOW}[4/5] 运行性能测试...${NC}"
pytest tests/performance -v --tb=short
echo -e "${GREEN}✓ 性能测试完成${NC}"

# 生成覆盖率报告
echo -e "\n${YELLOW}[5/5] 生成覆盖率报告...${NC}"
pytest tests/ --cov=src --cov-report=html --cov-report=term-missing
echo -e "${GREEN}✓ 覆盖率报告已生成${NC}"
echo -e "   HTML报告: htmlcov/index.html"

echo -e "\n${GREEN}=================================="
echo -e "✓ 所有测试完成！"
echo -e "==================================${NC}\n"

