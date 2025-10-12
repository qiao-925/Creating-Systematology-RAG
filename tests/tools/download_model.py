#!/usr/bin/env python3
"""
手动从镜像下载 Embedding 模型
解决自动下载时访问 huggingface.co 超时的问题
"""

import os
import sys
from pathlib import Path

# 设置镜像环境变量（必须在导入 huggingface_hub 之前）
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
print(f"✅ 设置 HF_ENDPOINT={os.environ['HF_ENDPOINT']}")

try:
    from huggingface_hub import snapshot_download
    print("✅ 已导入 huggingface_hub")
except ImportError:
    print("❌ 未安装 huggingface_hub")
    print("请运行: pip install huggingface_hub")
    sys.exit(1)

def download_model():
    """从镜像下载模型"""
    model_id = "BAAI/bge-base-zh-v1.5"
    cache_dir = Path.home() / ".cache" / "huggingface"
    
    print(f"\n{'='*60}")
    print(f"📦 开始下载模型: {model_id}")
    print(f"🌐 镜像地址: {os.environ.get('HF_ENDPOINT', 'Not set')}")
    print(f"📁 缓存目录: {cache_dir}")
    print(f"{'='*60}\n")
    
    try:
        # 使用 snapshot_download 下载整个模型
        local_path = snapshot_download(
            repo_id=model_id,
            cache_dir=str(cache_dir),
            resume_download=True,  # 支持断点续传
            local_files_only=False,  # 允许下载
        )
        
        print(f"\n{'='*60}")
        print(f"✅ 模型下载成功！")
        print(f"📁 本地路径: {local_path}")
        print(f"{'='*60}\n")
        
        print("💡 现在你可以正常启动应用，模型将从本地缓存加载")
        print("   streamlit run app.py")
        
        return True
        
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"❌ 下载失败: {e}")
        print(f"{'='*60}\n")
        
        print("🔍 排查建议:")
        print("   1. 检查网络连接")
        print("   2. 确认镜像地址可访问: https://hf-mirror.com")
        print("   3. 尝试手动访问: https://hf-mirror.com/BAAI/bge-base-zh-v1.5")
        
        return False

if __name__ == "__main__":
    success = download_model()
    sys.exit(0 if success else 1)

