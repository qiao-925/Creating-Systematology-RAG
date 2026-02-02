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

# 暴露端口（Streamlit 默认 8501）
EXPOSE 8501

# 启动命令（Streamlit）
CMD ["sh", "-c", "streamlit run app.py --server.port=${PORT:-8501} --server.address=0.0.0.0"]
