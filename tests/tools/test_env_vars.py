#!/usr/bin/env python3
"""测试环境变量设置"""

import os
import sys
from pathlib import Path

print("\n=== 导入 src 之前的环境变量 ===")
print(f"HF_ENDPOINT: {os.getenv('HF_ENDPOINT', 'Not set')}")
print(f"HUGGINGFACE_HUB_ENDPOINT: {os.getenv('HUGGINGFACE_HUB_ENDPOINT', 'Not set')}")

# 导入 src 包（会触发 __init__.py）
sys.path.insert(0, str(Path(__file__).parent))
import src

print("\n=== 导入 src 之后的环境变量 ===")
print(f"HF_ENDPOINT: {os.getenv('HF_ENDPOINT', 'Not set')}")
print(f"HUGGINGFACE_HUB_ENDPOINT: {os.getenv('HUGGINGFACE_HUB_ENDPOINT', 'Not set')}")
print(f"SENTENCE_TRANSFORMERS_HOME: {os.getenv('SENTENCE_TRANSFORMERS_HOME', 'Not set')}")
print(f"HF_HUB_OFFLINE: {os.getenv('HF_HUB_OFFLINE', 'Not set')}")
print(f"TRANSFORMERS_OFFLINE: {os.getenv('TRANSFORMERS_OFFLINE', 'Not set')}")

print("\n=== 配置信息 ===")
from src.config import config
print(f"config.HF_ENDPOINT: {config.HF_ENDPOINT}")
print(f"config.HF_OFFLINE_MODE: {config.HF_OFFLINE_MODE}")

print("\n✅ 测试完成")

