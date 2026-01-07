"""
配置管理 - GPU设备检测模块
GPU设备检测相关函数
"""

from typing import Optional, Tuple

# 全局GPU设备信息（项目启动时检测）
_GPU_DEVICE: Optional[str] = None
_GPU_AVAILABLE: bool = False
_GPU_DEVICE_NAME: Optional[str] = None


def detect_gpu_device() -> Tuple[bool, str, Optional[str]]:
    """检测GPU设备配置（全局函数，项目启动时调用）
    
    Returns:
        (has_gpu, device, device_name)
    """
    global _GPU_AVAILABLE, _GPU_DEVICE, _GPU_DEVICE_NAME
    
    if _GPU_DEVICE is not None:
        return _GPU_AVAILABLE, _GPU_DEVICE, _GPU_DEVICE_NAME
    
    print("🔍 开始检测GPU设备（GPU优先，CPU兜底）...")
    
    try:
        import torch
        print(f"📦 PyTorch版本: {torch.__version__}")
        
        _GPU_AVAILABLE = torch.cuda.is_available()
        print(f"🔍 torch.cuda.is_available() = {_GPU_AVAILABLE}")
        
        if _GPU_AVAILABLE:
            try:
                device_count = torch.cuda.device_count()
                current_device = torch.cuda.current_device()
                _GPU_DEVICE = f"cuda:{current_device}"
                _GPU_DEVICE_NAME = torch.cuda.get_device_name(current_device)
                
                print(f"✅ 检测到 GPU（优先使用）:")
                print(f"   设备数量: {device_count}")
                print(f"   当前设备: {current_device}")
                print(f"   设备名称: {_GPU_DEVICE_NAME}")
                print(f"   CUDA版本: {torch.version.cuda}")
                print(f"🔧 使用设备: {_GPU_DEVICE} ⚡ GPU加速模式")
            except Exception as e:
                print(f"⚠️  获取GPU详细信息失败: {e}")
                _GPU_AVAILABLE = False
                _GPU_DEVICE = "cpu"
                _GPU_DEVICE_NAME = None
                print("⚠️  降级到 CPU 模式")
        else:
            _GPU_DEVICE = "cpu"
            _GPU_DEVICE_NAME = None
            print("⚠️  未检测到 GPU，使用 CPU 兜底模式")
            
            if hasattr(torch.version, 'cuda') and torch.version.cuda:
                print(f"   PyTorch已编译CUDA支持，但运行时不可用")
                print(f"   可能原因：CUDA驱动版本不匹配或GPU被占用")
            else:
                print(f"   PyTorch未编译CUDA支持（CPU版本）")
            
            print(f"💡 性能提示: CPU模式较慢，索引构建可能需要30分钟+（GPU模式下约5分钟）")
                
    except ImportError as e:
        _GPU_AVAILABLE = False
        _GPU_DEVICE = "cpu"
        _GPU_DEVICE_NAME = None
        print(f"⚠️  PyTorch 未安装或导入失败: {e}")
        print("⚠️  使用 CPU 兜底模式")
        print(f"💡 性能提示: CPU模式较慢，建议安装CUDA版本的PyTorch")
    except Exception as e:
        _GPU_AVAILABLE = False
        _GPU_DEVICE = "cpu"
        _GPU_DEVICE_NAME = None
        print(f"⚠️  GPU检测失败: {e}")
        import traceback
        print(f"   错误详情:")
        traceback.print_exc()
        print("⚠️  使用 CPU 兜底模式")
    
    return _GPU_AVAILABLE, _GPU_DEVICE, _GPU_DEVICE_NAME


def get_gpu_device() -> str:
    """获取GPU设备字符串（GPU优先，CPU兜底）
    
    Returns:
        设备字符串 ("cuda:0" 或 "cpu")
    """
    if _GPU_DEVICE is None:
        detect_gpu_device()
    return _GPU_DEVICE or "cpu"


def is_gpu_available() -> bool:
    """检查GPU是否可用
    
    Returns:
        是否有GPU可用
    """
    if _GPU_DEVICE is None:
        detect_gpu_device()
    return _GPU_AVAILABLE


def get_device_status() -> dict:
    """获取当前设备状态摘要
    
    Returns:
        包含设备状态的字典
    """
    device = get_gpu_device()
    has_gpu, _, device_name = detect_gpu_device()
    
    return {
        "device": device,
        "has_gpu": has_gpu,
        "device_name": device_name,
        "is_gpu": device.startswith("cuda"),
    }
