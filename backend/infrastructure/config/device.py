"""
配置管理 - 设备检测模块

项目使用纯 CPU 模式（PyTorch CPU 版本）。
所有 LLM 调用走远程 API，数值计算使用 NumPy。
"""

from typing import Optional, Tuple

_device: Optional[str] = "cpu"
_device_name: Optional[str] = None


def detect_gpu_device() -> Tuple[bool, str, Optional[str]]:
    """设备检测 — 项目固定使用 CPU 模式。

    Returns:
        (False, "cpu", None)
    """
    return False, "cpu", None


def get_gpu_device() -> str:
    """返回设备字符串（固定为 cpu）。"""
    return "cpu"


def is_gpu_available() -> bool:
    """GPU 不可用 — 项目使用纯 CPU 模式。"""
    return False


def get_device_status() -> dict:
    """获取当前设备状态摘要。"""
    return {
        "device": "cpu",
        "has_gpu": False,
        "device_name": None,
        "is_gpu": False,
    }
