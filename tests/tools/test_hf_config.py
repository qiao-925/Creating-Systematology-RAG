#!/usr/bin/env python3
"""
测试 HuggingFace 镜像和离线模式配置
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.config import config
from src.indexer import get_embedding_model_status, load_embedding_model


def test_config():
    """测试配置读取"""
    print("=" * 60)
    print("📋 配置测试")
    print("=" * 60)
    
    print(f"\n✅ Embedding 模型: {config.EMBEDDING_MODEL}")
    print(f"✅ HF 镜像地址: {config.HF_ENDPOINT}")
    print(f"✅ 离线模式: {config.HF_OFFLINE_MODE}")
    print(f"\n当前环境变量:")
    print(f"   HF_ENDPOINT: {os.getenv('HF_ENDPOINT', 'Not set')}")
    print(f"   HF_HUB_OFFLINE: {os.getenv('HF_HUB_OFFLINE', 'Not set')}")


def test_model_status():
    """测试模型状态检查"""
    print("\n" + "=" * 60)
    print("🔍 模型状态检查")
    print("=" * 60)
    
    status = get_embedding_model_status()
    
    print(f"\n模型名称: {status['model_name']}")
    print(f"已加载: {'✅ 是' if status['loaded'] else '❌ 否'}")
    print(f"本地缓存: {'✅ 存在' if status['cache_exists'] else '⚠️  不存在'}")
    print(f"离线模式: {'📴 是' if status['offline_mode'] else '🌐 否'}")
    print(f"镜像地址: {status['mirror']}")
    print(f"缓存路径: {status['cache_dir']}")


def test_model_loading():
    """测试模型加载（可选，会实际下载模型）"""
    print("\n" + "=" * 60)
    print("📦 模型加载测试")
    print("=" * 60)
    
    response = input("\n⚠️  是否要测试模型加载？（首次会下载约400MB，y/n）: ")
    
    if response.lower() == 'y':
        print("\n开始加载模型...")
        try:
            model = load_embedding_model()
            print("✅ 模型加载成功！")
            
            # 再次检查状态
            print("\n加载后状态:")
            test_model_status()
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
    else:
        print("⏭️  跳过模型加载测试")


if __name__ == "__main__":
    print("\n🚀 HuggingFace 配置测试工具\n")
    
    # 1. 配置测试
    test_config()
    
    # 2. 模型状态检查
    test_model_status()
    
    # 3. 模型加载测试（可选）
    test_model_loading()
    
    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)
    print("\n💡 提示:")
    print("   - 如果本地无缓存，首次加载会从镜像下载（约400MB）")
    print("   - 下载后会缓存到 ~/.cache/huggingface/")
    print("   - 后续使用直接从缓存加载，无需联网")
    print()

