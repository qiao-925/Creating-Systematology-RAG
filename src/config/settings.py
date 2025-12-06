"""
配置管理 - 配置类模块
Config类实现

支持混合配置方式：
1. 环境变量（.env 文件）- 优先级最高，用于敏感信息
2. YAML 配置文件（application.yml）- 位于项目根目录，用于应用配置
3. 默认值 - 作为后备

优先级：环境变量 > YAML 配置 > 默认值
"""

import os
import json
from pathlib import Path
from typing import Optional, Any, Dict

import yaml
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """应用配置类
    
    支持混合配置方式：
    - 环境变量（.env）：优先级最高，用于敏感信息
    - YAML 配置（application.yml）：位于项目根目录，用于应用配置
    - 默认值：作为后备
    
    优先级：环境变量 > YAML 配置 > 默认值
    """
    
    def __init__(self):
        # 项目根目录
        self.PROJECT_ROOT = Path(__file__).parent.parent.parent
        
        # 加载 YAML 配置
        self._yaml_config = self._load_yaml_config()
        
        # 从配置读取日志器（延迟导入避免循环依赖）
        try:
            from src.logger import setup_logger as setup_config_logger
            self._config_logger = setup_config_logger('config')
        except Exception:
            self._config_logger = None
        
        # DeepSeek API配置（敏感信息，必须从环境变量读取）
        self.DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
        self.DEEPSEEK_API_BASE = self._get_config("DEEPSEEK_API_BASE", "api.deepseek.base", "https://api.deepseek.com/v1")
        
        # Hugging Face Token（用于 Inference API）
        self.HF_TOKEN = os.getenv("HF_TOKEN", "")
        
        # 模型配置
        self.LLM_MODEL = self._get_config("LLM_MODEL", "model.llm", "deepseek-reasoner")
        self.EMBEDDING_MODEL = self._get_config("EMBEDDING_MODEL", "model.embedding", "Qwen/Qwen3-Embedding-0.6B")
        
        # HuggingFace镜像配置
        self.HF_ENDPOINT = self._get_config("HF_ENDPOINT", "huggingface.endpoint", "https://hf-mirror.com")
        hf_offline_str = self._get_config("HF_OFFLINE_MODE", "huggingface.offline_mode", "false")
        self.HF_OFFLINE_MODE = str(hf_offline_str).lower() == "true"
        
        # 向量数据库配置（Chroma Cloud）
        self.CHROMA_CLOUD_API_KEY = os.getenv("CHROMA_CLOUD_API_KEY", "")
        self.CHROMA_CLOUD_TENANT = os.getenv("CHROMA_CLOUD_TENANT", "")
        self.CHROMA_CLOUD_DATABASE = os.getenv("CHROMA_CLOUD_DATABASE", "")
        self.CHROMA_COLLECTION_NAME = self._get_config("CHROMA_COLLECTION_NAME", "vector_store.collection_name", "default")
        
        # 文档路径配置
        self.RAW_DATA_PATH = self._resolve_path(self._get_config("RAW_DATA_PATH", "paths.raw_data", "data/raw"))
        self.PROCESSED_DATA_PATH = self._resolve_path(self._get_config("PROCESSED_DATA_PATH", "paths.processed_data", "data/processed"))
        
        # 会话和日志路径配置
        self.SESSIONS_PATH = self._resolve_path(self._get_config("SESSIONS_PATH", "paths.sessions", "sessions"))
        self.ACTIVITY_LOG_PATH = self._resolve_path(self._get_config("ACTIVITY_LOG_PATH", "paths.activity_log", "logs/activity"))
        
        # GitHub 配置
        self.GITHUB_REPOS_PATH = self._resolve_path(self._get_config("GITHUB_REPOS_PATH", "paths.github_repos", "data/github_repos"))
        self.GITHUB_METADATA_PATH = self._resolve_path(self._get_config("GITHUB_METADATA_PATH", "paths.github_metadata", "data/github_metadata.json"))
        
        # 缓存配置
        cache_enable_str = self._get_config("ENABLE_CACHE", "cache.enable", "true")
        self.ENABLE_CACHE = str(cache_enable_str).lower() == "true"
        self.CACHE_STATE_PATH = self._resolve_path(self._get_config("CACHE_STATE_PATH", "paths.cache_state", "data/cache_state.json"))
        
        # 索引配置
        self.CHUNK_SIZE = int(self._get_config("CHUNK_SIZE", "index.chunk_size", "512"))
        self.CHUNK_OVERLAP = int(self._get_config("CHUNK_OVERLAP", "index.chunk_overlap", "50"))
        self.SIMILARITY_TOP_K = int(self._get_config("SIMILARITY_TOP_K", "index.similarity_top_k", "3"))
        self.SIMILARITY_THRESHOLD = float(self._get_config("SIMILARITY_THRESHOLD", "index.similarity_threshold", "0.4"))
        
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
        self.RETRIEVAL_STRATEGY = self._get_config("RETRIEVAL_STRATEGY", "rag.retrieval_strategy", "vector")
        enable_rerank_str = self._get_config("ENABLE_RERANK", "rag.enable_rerank", "false")
        self.ENABLE_RERANK = str(enable_rerank_str).lower() == "true"
        
        # JWT 配置
        self.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-in-production-min-32-chars")
        self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "43200"))  # 30天
        self.RERANKER_TYPE = self._get_config("RERANKER_TYPE", "rag.reranker.type", "sentence-transformer")
        self.RERANK_MODEL = os.getenv("RERANK_MODEL", None) or None
        rerank_top_n_str = self._get_config("RERANK_TOP_N", "rag.reranker.top_n", "3")
        self.RERANK_TOP_N = int(rerank_top_n_str) if isinstance(rerank_top_n_str, (int, str)) else 3
        similarity_cutoff_str = self._get_config("SIMILARITY_CUTOFF", "rag.similarity_cutoff", "0.4")
        self.SIMILARITY_CUTOFF = float(similarity_cutoff_str) if isinstance(similarity_cutoff_str, (int, float, str)) else 0.4
        hybrid_alpha_str = self._get_config("HYBRID_ALPHA", "rag.hybrid_alpha", "0.5")
        self.HYBRID_ALPHA = float(hybrid_alpha_str) if isinstance(hybrid_alpha_str, (int, float, str)) else 0.5
        enable_auto_routing_str = self._get_config("ENABLE_AUTO_ROUTING", "rag.enable_auto_routing", "false")
        self.ENABLE_AUTO_ROUTING = str(enable_auto_routing_str).lower() == "true"
        
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
        
        # 日志配置
        self.LOG_LEVEL = self._get_config("LOG_LEVEL", "logging.level", "INFO").upper()
        self.LOG_FILE_LEVEL = self._get_config("LOG_FILE_LEVEL", "logging.file_level", "DEBUG").upper()
    
        # DeepSeek 推理模型配置
        enable_reasoning_display_str = self._get_config("DEEPSEEK_ENABLE_REASONING_DISPLAY", "deepseek.enable_reasoning_display", "true")
        self.DEEPSEEK_ENABLE_REASONING_DISPLAY = str(enable_reasoning_display_str).lower() == "true"
        store_reasoning_str = self._get_config("DEEPSEEK_STORE_REASONING", "deepseek.store_reasoning", "false")
        self.DEEPSEEK_STORE_REASONING = str(store_reasoning_str).lower() == "true"
        json_output_enabled_str = self._get_config("DEEPSEEK_JSON_OUTPUT_ENABLED", "deepseek.json_output_enabled", "false")
        self.DEEPSEEK_JSON_OUTPUT_ENABLED = str(json_output_enabled_str).lower() == "true"
    
    def _load_yaml_config(self) -> Dict[str, Any]:
        """加载 YAML 配置文件
        
        Returns:
            配置字典，如果文件不存在或加载失败返回空字典
        """
        config_file = self.PROJECT_ROOT / "application.yml"
        
        if not config_file.exists():
            # YAML 文件不存在时，使用纯环境变量方式（向后兼容）
            return {}
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            return config
        except Exception as e:
            # YAML 加载失败时，回退到环境变量方式
            if self._config_logger:
                self._config_logger.warning(f"加载 YAML 配置失败: {e}，回退到环境变量模式")
            return {}
    
    def _get_config(self, env_var: str, yaml_path: str, default: Any) -> Any:
        """获取配置值，遵循优先级：环境变量 > YAML 配置 > 默认值
        
        Args:
            env_var: 环境变量名称
            yaml_path: YAML 配置路径，使用点号分隔（如 "api.deepseek.base"）
            default: 默认值
            
        Returns:
            配置值
        """
        # 优先级 1: 环境变量（最高优先级）
        env_value = os.getenv(env_var)
        if env_value is not None:
            return env_value
        
        # 优先级 2: YAML 配置
        if self._yaml_config:
            yaml_value = self._get_nested_value(self._yaml_config, yaml_path)
            if yaml_value is not None:
                return yaml_value
        
        # 优先级 3: 默认值
        return default
    
    def _get_nested_value(self, config: Dict[str, Any], path: str) -> Any:
        """从嵌套字典中获取值
        
        Args:
            config: 配置字典
            path: 点号分隔的路径（如 "api.deepseek.base"）
            
        Returns:
            配置值，如果不存在返回 None
        """
        keys = path.split('.')
        value = config
        
        try:
            for key in keys:
                if isinstance(value, dict):
                    value = value.get(key)
                else:
                    return None
                if value is None:
                    return None
            return value
        except Exception:
            return None
    
    def _resolve_path(self, path_str: str) -> Path:
        """解析路径，支持相对路径和绝对路径
        
        Args:
            path_str: 路径字符串
            
        Returns:
            Path 对象
        """
        path = Path(path_str)
        
        if not path.is_absolute():
            path = self.PROJECT_ROOT / path
            
        return path
    
    def _get_path(self, env_var: str, default: str) -> Path:
        """获取路径配置，支持相对路径和绝对路径（向后兼容方法）"""
        path_str = os.getenv(env_var, default)
        return self._resolve_path(path_str)
    
    def ensure_directories(self):
        """确保所有必要的目录存在"""
        directories = [
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
        
        # Chroma Cloud 配置验证
        if not self.CHROMA_CLOUD_API_KEY:
            return False, "未设置CHROMA_CLOUD_API_KEY环境变量（Chroma Cloud 模式必需）"
        if not self.CHROMA_CLOUD_TENANT:
            return False, "未设置CHROMA_CLOUD_TENANT环境变量（Chroma Cloud 模式必需）"
        if not self.CHROMA_CLOUD_DATABASE:
            return False, "未设置CHROMA_CLOUD_DATABASE环境变量（Chroma Cloud 模式必需）"
        
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
    CHROMA_CLOUD_TENANT={self.CHROMA_CLOUD_TENANT},
    CHROMA_CLOUD_DATABASE={self.CHROMA_CLOUD_DATABASE},
    CHROMA_COLLECTION_NAME={self.CHROMA_COLLECTION_NAME},
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

