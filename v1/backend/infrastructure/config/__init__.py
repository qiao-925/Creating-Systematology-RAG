"""
配置管理模块 - 导出配置类和全局实例
"""

from backend.infrastructure.config.settings import Config
from backend.infrastructure.config.device import (
    detect_gpu_device,
    get_gpu_device,
    is_gpu_available,
    get_device_status,
)

# 全局配置实例
config = Config()

__all__ = [
    'config',
    'Config',
    'detect_gpu_device',
    'get_gpu_device',
    'is_gpu_available',
    'get_device_status',
]
