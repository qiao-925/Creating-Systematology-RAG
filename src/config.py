"""
配置管理模块 - 向后兼容层
已模块化拆分，此文件保持向后兼容
"""

from src.config import (
    config,
    Config,
    detect_gpu_device,
    get_gpu_device,
    is_gpu_available,
    get_device_status,
)

__all__ = [
    'config',
    'Config',
    'detect_gpu_device',
    'get_gpu_device',
    'is_gpu_available',
    'get_device_status',
]
