"""
系统科学知识库RAG应用
基于LlamaIndex构建的系统科学领域知识问答系统
"""

import os
from pathlib import Path
from dotenv import load_dotenv

__version__ = "0.1.0"

# 优先加载环境变量（在导入任何 HuggingFace 库之前）
# 这样才能确保镜像配置生效
_env_file = Path(__file__).parent.parent / ".env"
if _env_file.exists():
    load_dotenv(_env_file)

# 立即设置 HuggingFace 环境变量
_hf_endpoint = os.getenv("HF_ENDPOINT", "https://hf-mirror.com")
_hf_offline = os.getenv("HF_OFFLINE_MODE", "false").lower() == "true"

if _hf_endpoint:
    # 设置所有可能的环境变量以确保兼容性
    os.environ['HF_ENDPOINT'] = _hf_endpoint
    os.environ['HUGGINGFACE_HUB_ENDPOINT'] = _hf_endpoint
    os.environ['HF_HUB_ENDPOINT'] = _hf_endpoint  # 新版本使用这个
    # sentence-transformers 可能使用这个
    os.environ['SENTENCE_TRANSFORMERS_HOME'] = str(Path.home() / ".cache" / "huggingface")

if _hf_offline:
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'

