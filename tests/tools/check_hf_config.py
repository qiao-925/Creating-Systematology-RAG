#!/usr/bin/env python3
"""
简化版配置检查工具（不依赖其他模块）
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

print("\n" + "=" * 60)
print("🔍 HuggingFace 配置检查")
print("=" * 60)

# 读取配置
hf_endpoint = os.getenv("HF_ENDPOINT", "https://hf-mirror.com")
hf_offline = os.getenv("HF_OFFLINE_MODE", "false").lower() == "true"
embedding_model = os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-zh-v1.5")

print("\n📋 环境配置:")
print(f"   EMBEDDING_MODEL: {embedding_model}")
print(f"   HF_ENDPOINT: {hf_endpoint}")
print(f"   HF_OFFLINE_MODE: {hf_offline}")

# 检查缓存
cache_root = Path.home() / ".cache" / "huggingface" / "hub"
model_cache_name = embedding_model.replace("/", "--")
cache_dir = cache_root / f"models--{model_cache_name}"

print(f"\n💾 缓存状态:")
print(f"   缓存目录: {cache_dir}")
if cache_dir.exists():
    print(f"   状态: ✅ 已存在")
    print(f"   提示: 后续使用无需联网")
else:
    print(f"   状态: ⚠️  不存在")
    print(f"   提示: 首次使用将从镜像下载（约400MB）")

print(f"\n🌐 网络配置:")
if hf_offline:
    print(f"   模式: 📴 离线模式")
    print(f"   行为: 仅使用本地缓存")
else:
    print(f"   模式: 🌐 在线模式")
    print(f"   镜像: {hf_endpoint}")

print("\n" + "=" * 60)
print("✅ 配置检查完成")
print("=" * 60)

print("\n💡 下一步:")
if not cache_dir.exists():
    print("   1. 确保网络畅通")
    print("   2. 启动应用: streamlit run app.py")
    print("   3. 首次启动会自动从镜像下载模型")
    print("   4. 下载完成后将缓存到本地")
else:
    print("   1. 模型已缓存，可以直接使用")
    print("   2. 启动应用: streamlit run app.py")
    print("   3. 加载速度：秒级启动 ⚡")

print()

