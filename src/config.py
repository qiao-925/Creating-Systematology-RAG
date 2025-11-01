"""
配置管理模块
管理API密钥、模型配置、路径配置等
"""

import os
from pathlib import Path
from typing import Optional, Tuple
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 全局GPU设备信息（项目启动时检测）
_GPU_DEVICE: Optional[str] = None
_GPU_AVAILABLE: bool = False
_GPU_DEVICE_NAME: Optional[str] = None


def detect_gpu_device() -> Tuple[bool, str, Optional[str]]:
    """检测GPU设备配置（简化版）
    
    Returns:
        (has_gpu, device, device_name)
    """
    global _GPU_AVAILABLE, _GPU_DEVICE, _GPU_DEVICE_NAME
    
    # 如果已经检测过，直接返回缓存结果
    if _GPU_DEVICE is not None:
        return _GPU_AVAILABLE, _GPU_DEVICE, _GPU_DEVICE_NAME
    
    print("🔍 检测GPU设备...")
    
    try:
        import torch
        if torch.cuda.is_available():
            _GPU_AVAILABLE = True
            _GPU_DEVICE = "cuda:0"
            _GPU_DEVICE_NAME = torch.cuda.get_device_name(0)
            print(f"✅ 使用GPU: {_GPU_DEVICE_NAME}")
        else:
            _GPU_AVAILABLE = False
            _GPU_DEVICE = "cpu"
            _GPU_DEVICE_NAME = None
            print("⚠️  使用CPU模式")
    except:
        _GPU_AVAILABLE = False
        _GPU_DEVICE = "cpu"
        _GPU_DEVICE_NAME = None
        print("⚠️  使用CPU模式")
    
    return _GPU_AVAILABLE, _GPU_DEVICE, _GPU_DEVICE_NAME


def get_device_status() -> dict:
    """获取当前设备状态摘要
    
    Returns:
        包含设备状态的字典：
        {
            "device": str,           # 设备字符串
            "has_gpu": bool,         # 是否有GPU
            "device_name": str,      # GPU设备名称（如果有）
            "is_gpu": bool,          # 当前是否使用GPU
        }
    """
    device = get_gpu_device()
    has_gpu, _, device_name = detect_gpu_device()
    
    return {
        "device": device,
        "has_gpu": has_gpu,
        "device_name": device_name,
        "is_gpu": device.startswith("cuda"),
    }


def get_gpu_device() -> str:
    """获取GPU设备字符串（GPU优先，CPU兜底）
    
    Returns:
        设备字符串 ("cuda:0" 或 "cpu")
    """
    if _GPU_DEVICE is None:
        # 如果还没检测，先检测一次
        detect_gpu_device()
    return _GPU_DEVICE or "cpu"


def is_gpu_available() -> bool:
    """检查GPU是否可用（必须在detect_gpu_device()之后调用）
    
    Returns:
        是否有GPU可用
    """
    if _GPU_DEVICE is None:
        # 如果还没检测，先检测一次
        detect_gpu_device()
    return _GPU_AVAILABLE


class Config:
    """应用配置类"""
    
    def __init__(self):
        # 项目根目录
        self.PROJECT_ROOT = Path(__file__).parent.parent
        
        # DeepSeek API配置
        self.DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
        self.DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
        
        # 模型配置
        self.LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
        self.EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-0.6B")
        
        # HuggingFace镜像配置
        self.HF_ENDPOINT = os.getenv("HF_ENDPOINT", "https://hf-mirror.com")
        self.HF_OFFLINE_MODE = os.getenv("HF_OFFLINE_MODE", "false").lower() == "true"
        
        # 向量数据库配置
        self.VECTOR_STORE_PATH = self._get_path("VECTOR_STORE_PATH", "vector_store")
        self.CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "default")
        
        # 文档路径配置
        self.RAW_DATA_PATH = self._get_path("RAW_DATA_PATH", "data/raw")
        self.PROCESSED_DATA_PATH = self._get_path("PROCESSED_DATA_PATH", "data/processed")
        
        # 会话和日志路径配置
        self.SESSIONS_PATH = self._get_path("SESSIONS_PATH", "sessions")
        self.ACTIVITY_LOG_PATH = self._get_path("ACTIVITY_LOG_PATH", "logs/activity")
        
        # GitHub 配置
        self.GITHUB_REPOS_PATH = self._get_path("GITHUB_REPOS_PATH", "data/github_repos")
        self.GITHUB_METADATA_PATH = self._get_path("GITHUB_METADATA_PATH", "data/github_metadata.json")
        
        # 索引配置
        self.CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
        self.CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
        self.SIMILARITY_TOP_K = int(os.getenv("SIMILARITY_TOP_K", "3"))
        self.SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.5"))
        
        # Embedding性能优化配置
        self.EMBED_BATCH_SIZE = int(os.getenv("EMBED_BATCH_SIZE", "10"))
        self.EMBED_MAX_LENGTH = int(os.getenv("EMBED_MAX_LENGTH", "512"))
        
        # 应用配置
        self.APP_TITLE = os.getenv("APP_TITLE", "主页")
        self.APP_PORT = int(os.getenv("APP_PORT", "8501"))
        
        # GitHub数据源配置（仅支持公开仓库）
        self.GITHUB_DEFAULT_BRANCH = os.getenv("GITHUB_DEFAULT_BRANCH", "main")
        
    def _get_path(self, env_var: str, default: str) -> Path:
        """获取路径配置，支持相对路径和绝对路径"""
        path_str = os.getenv(env_var, default)
        path = Path(path_str)
        
        # 如果是相对路径，则相对于项目根目录
        if not path.is_absolute():
            path = self.PROJECT_ROOT / path
            
        return path
    
    def ensure_directories(self):
        """确保所有必要的目录存在"""
        directories = [
            self.VECTOR_STORE_PATH,
            self.RAW_DATA_PATH,
            self.PROCESSED_DATA_PATH,
            self.SESSIONS_PATH,
            self.ACTIVITY_LOG_PATH,
            self.GITHUB_REPOS_PATH,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
    def validate(self) -> tuple[bool, Optional[str]]:
        """验证配置是否完整
        
        Returns:
            (is_valid, error_message)
        """
        if not self.DEEPSEEK_API_KEY:
            return False, "未设置DEEPSEEK_API_KEY环境变量"
        
        if self.CHUNK_SIZE <= 0:
            return False, "CHUNK_SIZE必须大于0"
            
        if self.CHUNK_OVERLAP < 0:
            return False, "CHUNK_OVERLAP必须大于等于0"
            
        if self.CHUNK_OVERLAP >= self.CHUNK_SIZE:
            return False, "CHUNK_OVERLAP必须小于CHUNK_SIZE"
            
        return True, None
    
    def __repr__(self) -> str:
        """返回配置的字符串表示（隐藏敏感信息）"""
        return f"""Config(
    PROJECT_ROOT={self.PROJECT_ROOT},
    DEEPSEEK_API_BASE={self.DEEPSEEK_API_BASE},
    LLM_MODEL={self.LLM_MODEL},
    EMBEDDING_MODEL={self.EMBEDDING_MODEL},
    HF_ENDPOINT={self.HF_ENDPOINT},
    HF_OFFLINE_MODE={self.HF_OFFLINE_MODE},
    VECTOR_STORE_PATH={self.VECTOR_STORE_PATH},
    SESSIONS_PATH={self.SESSIONS_PATH},
    ACTIVITY_LOG_PATH={self.ACTIVITY_LOG_PATH},
    GITHUB_METADATA_PATH={self.GITHUB_METADATA_PATH},
    CHUNK_SIZE={self.CHUNK_SIZE},
    CHUNK_OVERLAP={self.CHUNK_OVERLAP},
    SIMILARITY_TOP_K={self.SIMILARITY_TOP_K},
    EMBED_BATCH_SIZE={self.EMBED_BATCH_SIZE},
    EMBED_MAX_LENGTH={self.EMBED_MAX_LENGTH},
    GITHUB_DEFAULT_BRANCH={self.GITHUB_DEFAULT_BRANCH}
)"""


# 全局配置实例
config = Config()

# 项目启动时自动检测GPU（在config模块加载后）
# 这样确保所有必要的模块都已导入
try:
    print("=" * 60)
    print("🚀 项目启动 - GPU设备检测")
    print("=" * 60)
    detect_gpu_device()
    print("=" * 60)
except Exception as e:
    # GPU检测失败不影响项目启动，仅记录
    import traceback
    print(f"⚠️  项目启动时GPU检测失败: {e}")
    traceback.print_exc()


if __name__ == "__main__":
    # 测试配置
    print("=== 配置信息 ===")
    print(config)
    print("\n=== 配置验证 ===")
    is_valid, error_msg = config.validate()
    if is_valid:
        print("✅ 配置验证通过")
        config.ensure_directories()
        print("✅ 目录创建成功")
    else:
        print(f"❌ 配置验证失败: {error_msg}")

