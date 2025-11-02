"""
配置管理模块 - 向后兼容层
保持向后兼容的接口导出
"""

from src.config.device import (
    detect_gpu_device,
    get_gpu_device,
    is_gpu_available,
    get_device_status,
)
from src.config.settings import Config

# 全局配置实例
config = Config()

# 项目启动时自动检测GPU
try:
    print("=" * 60)
    print("🚀 项目启动 - GPU设备检测")
    print("=" * 60)
    detect_gpu_device()
    print("=" * 60)
except Exception as e:
    import traceback
    print(f"⚠️  项目启动时GPU检测失败: {e}")
    traceback.print_exc()

__all__ = [
    'config',
    'Config',
    'detect_gpu_device',
    'get_gpu_device',
    'is_gpu_available',
    'get_device_status',
]

