"""
配置管理模块 - 导出配置类和全局实例
"""

from src.infrastructure.config.settings import Config
from src.infrastructure.config.device import (
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
