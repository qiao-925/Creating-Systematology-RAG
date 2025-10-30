"""
系统科学知识库RAG应用
基于LlamaIndex构建的系统科学领域知识问答系统
"""

# 最优先：设置 UTF-8 编码（必须在所有其他导入之前）
# 这样可以确保所有模块的输出都能正确显示 emoji
import os
import sys

# 先设置环境变量（最基础）
os.environ["PYTHONIOENCODING"] = "utf-8"

# 尝试设置标准输出编码（在导入其他模块之前）
try:
    import io
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    elif not isinstance(sys.stdout, io.TextIOWrapper) or sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    elif not isinstance(sys.stderr, io.TextIOWrapper) or sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
except (AttributeError, ValueError, OSError):
    pass  # 某些环境下可能不支持，忽略

# Windows 平台：设置控制台代码页
if sys.platform == "win32":
    try:
        import subprocess
        subprocess.run(['chcp', '65001'], capture_output=True, timeout=1, check=False)
    except Exception:
        pass  # chcp 可能不可用，忽略

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

# 项目启动时检测GPU设备（延迟到首次导入config时检测）
# 注意：实际检测会在首次导入 src.config 模块时执行
# 这样可以确保所有依赖都已加载完成

