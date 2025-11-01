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
    """检测GPU设备配置（全局函数，项目启动时调用）
    
    策略：GPU优先，CPU兜底
    
    Returns:
        (has_gpu, device, device_name)
        - has_gpu: 是否有可用的GPU
        - device: 设备字符串 ("cuda:0" 或 "cpu")
        - device_name: GPU设备名称（如果有）
    """
    global _GPU_AVAILABLE, _GPU_DEVICE, _GPU_DEVICE_NAME
    
    # 如果已经检测过，直接返回缓存结果
    if _GPU_DEVICE is not None:
        return _GPU_AVAILABLE, _GPU_DEVICE, _GPU_DEVICE_NAME
    
    print("🔍 开始检测GPU设备（GPU优先，CPU兜底）...")
    
    try:
        import torch
        print(f"📦 PyTorch版本: {torch.__version__}")
        
        # 检查CUDA是否可用
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
            
            # 提供更多诊断信息和性能提示
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
        
        # 缓存配置
        self.ENABLE_CACHE = os.getenv("ENABLE_CACHE", "true").lower() == "true"
        self.CACHE_STATE_PATH = self._get_path("CACHE_STATE_PATH", "data/cache_state.json")
        
        # 索引配置
        self.CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
        self.CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
        self.SIMILARITY_TOP_K = int(os.getenv("SIMILARITY_TOP_K", "3"))
        self.SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.2"))  # 相似度阈值，低于此值会启用推理模式
        
        # Embedding性能优化配置
        self.EMBED_BATCH_SIZE = int(os.getenv("EMBED_BATCH_SIZE", "10"))  # 批处理大小，默认10（可根据GPU内存调整）
        self.EMBED_MAX_LENGTH = int(os.getenv("EMBED_MAX_LENGTH", "512"))  # 最大文本长度，超过会被截断
        
        # 批处理与分组（索引构建）配置
        # 是否启用批模式（按目录/子模块分批执行）
        self.INDEX_BATCH_MODE = os.getenv("INDEX_BATCH_MODE", "false").lower() == "true"
        # 分组方式：目前仅支持 directory（按相对路径的层级目录分组）
        self.INDEX_GROUP_BY = os.getenv("INDEX_GROUP_BY", "directory")
        # 参与分组的目录深度：1 表示第一层目录；2 表示两层
        self.GROUP_DEPTH = int(os.getenv("GROUP_DEPTH", "1"))
        # 目标每批文档数（用于二次切分/合并的参考上限）
        self.DOCS_PER_BATCH = int(os.getenv("DOCS_PER_BATCH", "20"))
        # 可选：每批目标节点数上限（0 表示不限制）
        self.NODES_PER_BATCH = int(os.getenv("NODES_PER_BATCH", "0"))
        # 可选：每批目标token数上限（0 表示不限制，为粗估）
        self.TOKENS_PER_BATCH = int(os.getenv("TOKENS_PER_BATCH", "0"))
        # 插入策略优先级：nodes | docs | legacy
        self.INDEX_STRATEGY = os.getenv("INDEX_STRATEGY", "nodes").lower()
        # 测试/管控：限制最大批次数（0 表示不限制）
        self.INDEX_MAX_BATCHES = int(os.getenv("INDEX_MAX_BATCHES", "0"))
        
        # 应用配置
        self.APP_TITLE = os.getenv("APP_TITLE", "主页")
        self.APP_PORT = int(os.getenv("APP_PORT", "8501"))
        
        # GitHub数据源配置（仅支持公开仓库）
        self.GITHUB_DEFAULT_BRANCH = os.getenv("GITHUB_DEFAULT_BRANCH", "main")
        
        # 维基百科配置
        self.ENABLE_WIKIPEDIA = os.getenv("ENABLE_WIKIPEDIA", "true").lower() == "true"
        self.WIKIPEDIA_AUTO_LANG = os.getenv("WIKIPEDIA_AUTO_LANG", "true").lower() == "true"
        self.WIKIPEDIA_THRESHOLD = float(os.getenv("WIKIPEDIA_THRESHOLD", "0.6"))
        self.WIKIPEDIA_MAX_RESULTS = int(os.getenv("WIKIPEDIA_MAX_RESULTS", "2"))
        self.WIKIPEDIA_PRELOAD_CONCEPTS = [
            concept.strip() 
            for concept in os.getenv(
                "WIKIPEDIA_PRELOAD_CONCEPTS",
                "系统科学,钱学森,系统工程,控制论,信息论"
            ).split(',')
            if concept.strip()
        ]
        
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
            self.CACHE_STATE_PATH.parent,  # 确保缓存状态文件目录存在
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
    INDEX_BATCH_MODE={self.INDEX_BATCH_MODE},
    INDEX_GROUP_BY={self.INDEX_GROUP_BY},
    GROUP_DEPTH={self.GROUP_DEPTH},
    DOCS_PER_BATCH={self.DOCS_PER_BATCH},
    NODES_PER_BATCH={self.NODES_PER_BATCH},
    TOKENS_PER_BATCH={self.TOKENS_PER_BATCH},
    INDEX_STRATEGY={self.INDEX_STRATEGY},
    INDEX_MAX_BATCHES={self.INDEX_MAX_BATCHES},
    GITHUB_DEFAULT_BRANCH={self.GITHUB_DEFAULT_BRANCH},
    ENABLE_WIKIPEDIA={self.ENABLE_WIKIPEDIA},
    WIKIPEDIA_THRESHOLD={self.WIKIPEDIA_THRESHOLD},
    WIKIPEDIA_MAX_RESULTS={self.WIKIPEDIA_MAX_RESULTS},
    ENABLE_CACHE={self.ENABLE_CACHE},
    CACHE_STATE_PATH={self.CACHE_STATE_PATH}
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

