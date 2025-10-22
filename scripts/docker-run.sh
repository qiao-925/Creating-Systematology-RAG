#!/bin/bash
# 本地 Docker 测试脚本

echo "🐳 构建 Docker 镜像..."
docker build -t systematology-rag:latest .

echo "🚀 启动容器..."
docker run -it --rm \
  -p 8501:8501 \
  -e DEEPSEEK_API_KEY=$DEEPSEEK_API_KEY \
  systematology-rag:latest
