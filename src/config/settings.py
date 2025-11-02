"""
配置管理 - 配置类模块
Config类实现
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """应用配置类"""
    
    def __init__(self):
        # 项目根目录
        self.PROJECT_ROOT = Path(__file__).parent.parent.parent
        
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
        self.SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.5"))
        
        # Embedding配置
        self.EMBEDDING_TYPE = os.getenv("EMBEDDING_TYPE", "local")
        self.EMBEDDING_API_URL = os.getenv("EMBEDDING_API_URL", "http://localhost:8000")
        self.EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", None) or None
        
        # 可观测性配置
        self.ENABLE_PHOENIX = os.getenv("ENABLE_PHOENIX", "true").lower() == "true"
        self.PHOENIX_LAUNCH_APP = os.getenv("PHOENIX_LAUNCH_APP", "false").lower() == "true"
        self.PHOENIX_HOST = os.getenv("PHOENIX_HOST", "0.0.0.0")
        self.PHOENIX_PORT = int(os.getenv("PHOENIX_PORT", "6006"))
        
        # LlamaDebug 配置
        self.ENABLE_DEBUG_HANDLER = os.getenv("ENABLE_DEBUG_HANDLER", "false").lower() == "true"
        self.DEBUG_PRINT_TRACE = os.getenv("DEBUG_PRINT_TRACE", "true").lower() == "true"
        
        # RAGAS 评估器配置
        self.ENABLE_RAGAS = os.getenv("ENABLE_RAGAS", "false").lower() == "true"
        ragas_metrics_str = os.getenv("RAGAS_METRICS", "faithfulness,context_precision,context_recall,answer_relevancy,context_relevancy")
        self.RAGAS_METRICS = [m.strip() for m in ragas_metrics_str.split(",") if m.strip()]
        self.RAGAS_BATCH_SIZE = int(os.getenv("RAGAS_BATCH_SIZE", "10"))
        
        # 模块化RAG配置
        self.RETRIEVAL_STRATEGY = os.getenv("RETRIEVAL_STRATEGY", "vector")
        self.ENABLE_RERANK = os.getenv("ENABLE_RERANK", "false").lower() == "true"
        self.RERANKER_TYPE = os.getenv("RERANKER_TYPE", "sentence-transformer")
        self.RERANK_MODEL = os.getenv("RERANK_MODEL", None) or None
        self.RERANK_TOP_N = int(os.getenv("RERANK_TOP_N", "3"))
        self.SIMILARITY_CUTOFF = float(os.getenv("SIMILARITY_CUTOFF", "0.6"))
        self.HYBRID_ALPHA = float(os.getenv("HYBRID_ALPHA", "0.5"))
        
        # 多策略检索配置
        enabled_strategies_str = os.getenv("ENABLED_RETRIEVAL_STRATEGIES", "vector")
        self.ENABLED_RETRIEVAL_STRATEGIES = [
            s.strip() for s in enabled_strategies_str.split(",") if s.strip()
        ]
        self.MERGE_STRATEGY = os.getenv("MERGE_STRATEGY", "reciprocal_rank_fusion")
        # 权重配置（JSON格式）
        import json
        from src.logger import setup_logger as setup_config_logger
        config_logger = setup_config_logger('config')
        retriever_weights_str = os.getenv(
            "RETRIEVER_WEIGHTS",
            '{"vector": 1.0, "bm25": 0.8, "grep": 0.6}'
        )
        try:
            self.RETRIEVER_WEIGHTS = json.loads(retriever_weights_str)
        except json.JSONDecodeError:
            config_logger.warning(f"无法解析RETRIEVER_WEIGHTS，使用默认值")
            self.RETRIEVER_WEIGHTS = {"vector": 1.0, "bm25": 0.8, "grep": 0.6}
        self.ENABLE_DEDUPLICATION = os.getenv("ENABLE_DEDUPLICATION", "true").lower() == "true"
        
        # 模块注册中心配置
        self.MODULE_CONFIG_PATH = os.getenv("MODULE_CONFIG_PATH", None) or None
        self.AUTO_REGISTER_MODULES = os.getenv("AUTO_REGISTER_MODULES", "true").lower() == "true"
        
        # Embedding性能优化配置
        self.EMBED_BATCH_SIZE = int(os.getenv("EMBED_BATCH_SIZE", "10"))
        self.EMBED_MAX_LENGTH = int(os.getenv("EMBED_MAX_LENGTH", "512"))
        
        # 批处理与分组配置
        self.INDEX_BATCH_MODE = os.getenv("INDEX_BATCH_MODE", "false").lower() == "true"
        self.INDEX_GROUP_BY = os.getenv("INDEX_GROUP_BY", "directory")
        self.GROUP_DEPTH = int(os.getenv("GROUP_DEPTH", "1"))
        self.DOCS_PER_BATCH = int(os.getenv("DOCS_PER_BATCH", "20"))
        self.NODES_PER_BATCH = int(os.getenv("NODES_PER_BATCH", "0"))
        self.TOKENS_PER_BATCH = int(os.getenv("TOKENS_PER_BATCH", "0"))
        self.INDEX_STRATEGY = os.getenv("INDEX_STRATEGY", "nodes").lower()
        self.INDEX_MAX_BATCHES = int(os.getenv("INDEX_MAX_BATCHES", "0"))
        
        # 应用配置
        self.APP_TITLE = os.getenv("APP_TITLE", "主页")
        self.APP_PORT = int(os.getenv("APP_PORT", "8501"))
        
        # GitHub数据源配置
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
            self.CACHE_STATE_PATH.parent,
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


# 向后兼容：添加COLLECTION_NAME属性
def _get_collection_name(self):
    """向后兼容属性"""
    return self.CHROMA_COLLECTION_NAME

# 动态添加属性
Config.COLLECTION_NAME = property(_get_collection_name)

