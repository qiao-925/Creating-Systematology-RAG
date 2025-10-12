#!/usr/bin/env python3
"""
测试 HuggingFace 镜像配置是否生效
"""

import os
import sys
from pathlib import Path

print("\n" + "="*60)
print("🔍 测试 HuggingFace 镜像配置")
print("="*60)

# 1. 设置环境变量（在导入之前）
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
print(f"\n✅ 设置环境变量:")
print(f"   HF_ENDPOINT = {os.environ['HF_ENDPOINT']}")

# 2. 导入 huggingface_hub
try:
    from huggingface_hub import HfApi
    from huggingface_hub.constants import HUGGINGFACE_HUB_CACHE
    print(f"\n✅ 已导入 huggingface_hub")
    
    # 3. 检查 HfApi 的endpoint
    api = HfApi()
    print(f"\n📡 HfApi 配置:")
    print(f"   endpoint: {api.endpoint}")
    
    # 4. 检查缓存目录
    print(f"\n📁 缓存配置:")
    print(f"   HUGGINGFACE_HUB_CACHE: {HUGGINGFACE_HUB_CACHE}")
    
    # 5. 检查所有相关环境变量
    print(f"\n🌐 环境变量:")
    env_vars = [
        'HF_ENDPOINT',
        'HUGGINGFACE_HUB_ENDPOINT',
        'HF_HUB_ENDPOINT',
        'TRANSFORMERS_OFFLINE',
        'HF_HUB_OFFLINE',
    ]
    for var in env_vars:
        value = os.getenv(var, 'Not set')
        print(f"   {var} = {value}")
    
    print(f"\n{'='*60}")
    if 'hf-mirror.com' in api.endpoint:
        print("✅ 镜像配置已生效！")
    else:
        print("⚠️  镜像配置未生效，仍使用官方地址")
        print("\n💡 可能原因:")
        print("   1. 环境变量设置时机不对（需要在导入之前）")
        print("   2. 库版本不支持 HF_ENDPOINT 变量")
        print("   3. 需要使用其他环境变量名")
    print("="*60)
    
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("请确认已安装: pip install huggingface_hub")
    sys.exit(1)

print()

