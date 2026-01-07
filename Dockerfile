# 基础镜像
FROM python:3.12-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv（快速依赖安装）
RUN pip install uv

# 工作目录
WORKDIR /app

# 复制依赖文件
COPY pyproject.toml .

# 安装 Python 依赖（使用 uv 加速）
RUN uv pip install --system -r pyproject.toml

# 复制应用代码
COPY . .

# 暴露端口（FastAPI 默认 8000，Streamlit 8501）
EXPOSE 8000 8501

# 启动命令（支持环境变量选择）
# 默认启动 Streamlit（8501），FastAPI 通过 Zeabur 自定义启动命令处理
CMD ["sh", "-c", "if [ \"$APP_MODE\" = \"api\" ]; then uvicorn backend.business.rag_api.fastapi_app:app --host 0.0.0.0 --port ${PORT:-8000}; else streamlit run app.py --server.port=${PORT:-8501} --server.address=0.0.0.0; fi"]
