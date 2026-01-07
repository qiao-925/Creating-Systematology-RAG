"""
配置管理 - 主配置类：基于Pydantic Settings的配置系统

主要功能：
- Config类：组合YAML加载器和Pydantic模型，提供配置访问
- 职责分离：敏感信息从环境变量读取，静态配置从YAML读取
- 向后兼容：提供大写属性访问（如config.DEEPSEEK_API_KEY）

特性：
- 自动类型转换和验证
- 路径自动解析（相对路径转为绝对路径）
- 隐藏敏感信息的字符串表示
"""

import os
from pathlib import Path
from typing import Optional, Any

from dotenv import load_dotenv
from pydantic import ValidationError

from backend.infrastructure.config.yaml_loader import load_yaml_config
from backend.infrastructure.config.models import ConfigModel

# 加载环境变量
load_dotenv()


class Config:
    """应用配置类：基于Pydantic Settings的配置系统
    
    职责分离：
    - 环境变量（.env）：仅用于敏感信息（API keys、tokens、密钥）
    - YAML 配置（application.yml）：仅用于静态非敏感配置
    """
    
    # 属性映射表：将大写属性名映射到Pydantic模型路径
    _PROPERTY_MAPPING = {
        # API配置
        'DEEPSEEK_API_BASE': lambda m: m.api.deepseek.base,
        # 模型配置
        'LLM_MODEL': lambda m: m.model.llm,
        'EMBEDDING_MODEL': lambda m: m.model.embedding,
        # HuggingFace配置
        'HF_ENDPOINT': lambda m: m.huggingface.endpoint,
        'HF_OFFLINE_MODE': lambda m: m.huggingface.offline_mode,
        # 向量数据库配置
        'CHROMA_COLLECTION_NAME': lambda m: m.vector_store.collection_name,
        # 缓存配置（已废弃：缓存管理器功能已移除，此配置不再使用）
        'ENABLE_CACHE': lambda m: m.cache.enable,
        # 索引配置
        'CHUNK_SIZE': lambda m: m.index.chunk_size,
        'CHUNK_OVERLAP': lambda m: m.index.chunk_overlap,
        'SIMILARITY_TOP_K': lambda m: m.index.similarity_top_k,
        'SIMILARITY_THRESHOLD': lambda m: m.index.similarity_threshold,
        # Embedding配置
        'EMBEDDING_TYPE': lambda m: m.embedding.type,
        'EMBEDDING_API_URL': lambda m: m.embedding.api_url,
        'EMBED_BATCH_SIZE': lambda m: m.embedding.batch_size,
        'EMBED_MAX_LENGTH': lambda m: m.embedding.max_length,
        # 可观测性配置
        'ENABLE_PHOENIX': lambda m: m.observability.phoenix.enable,
        'PHOENIX_LAUNCH_APP': lambda m: m.observability.phoenix.launch_app,
        'PHOENIX_HOST': lambda m: m.observability.phoenix.host,
        'PHOENIX_PORT': lambda m: m.observability.phoenix.port,
        'ENABLE_DEBUG_HANDLER': lambda m: m.observability.llama_debug.enable,
        'DEBUG_PRINT_TRACE': lambda m: m.observability.llama_debug.print_trace,
        # RAGAS配置
        'ENABLE_RAGAS': lambda m: m.ragas.enable,
        'RAGAS_BATCH_SIZE': lambda m: m.ragas.batch_size,
        # RAG配置
        'RETRIEVAL_STRATEGY': lambda m: m.rag.retrieval_strategy,
        'ENABLE_RERANK': lambda m: m.rag.enable_rerank,
        'RERANKER_TYPE': lambda m: m.rag.reranker.type,
        'RERANK_TOP_N': lambda m: m.rag.reranker.top_n,
        'SIMILARITY_CUTOFF': lambda m: m.rag.similarity_cutoff,
        'HYBRID_ALPHA': lambda m: m.rag.hybrid_alpha,
        'ENABLE_AUTO_ROUTING': lambda m: m.rag.enable_auto_routing,
        'MERGE_STRATEGY': lambda m: m.rag.multi_strategy.merge_strategy,
        'ENABLE_DEDUPLICATION': lambda m: m.rag.multi_strategy.enable_deduplication,
        # 模块注册中心配置
        'AUTO_REGISTER_MODULES': lambda m: m.module_registry.auto_register_modules,
        # 批处理配置
        'INDEX_BATCH_MODE': lambda m: m.batch_processing.index_batch_mode,
        'INDEX_GROUP_BY': lambda m: m.batch_processing.index_group_by,
        'GROUP_DEPTH': lambda m: m.batch_processing.group_depth,
        'DOCS_PER_BATCH': lambda m: m.batch_processing.docs_per_batch,
        'NODES_PER_BATCH': lambda m: m.batch_processing.nodes_per_batch,
        'TOKENS_PER_BATCH': lambda m: m.batch_processing.tokens_per_batch,
        'INDEX_MAX_BATCHES': lambda m: m.batch_processing.index_max_batches,
        # 应用配置
        'APP_TITLE': lambda m: m.app.title,
        'APP_PORT': lambda m: m.app.port,
        'APP_DEV_MODE': lambda m: m.app.dev_mode,
        # GitHub配置
        'GITHUB_DEFAULT_BRANCH': lambda m: m.github.default_branch,
        # 日志配置
        'LOG_LEVEL': lambda m: m.logging.level.upper(),
        'LOG_FILE_LEVEL': lambda m: m.logging.file_level.upper(),
        # DeepSeek配置
        'DEEPSEEK_ENABLE_REASONING_DISPLAY': lambda m: m.deepseek.enable_reasoning_display,
        'DEEPSEEK_STORE_REASONING': lambda m: m.deepseek.store_reasoning,
        'DEEPSEEK_JSON_OUTPUT_ENABLED': lambda m: m.deepseek.json_output_enabled,
    }
    
    def __init__(self):
        # 项目根目录
        self.PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
        
        # 初始化日志器（延迟导入避免循环依赖）
        try:
            from backend.infrastructure.logger import get_logger
            self._config_logger = get_logger('config')
        except Exception:
            self._config_logger = None
        
        # 加载YAML配置
        yaml_data = load_yaml_config(self.PROJECT_ROOT)
        
        # 创建Pydantic模型实例
        try:
            self._model = ConfigModel(**yaml_data)
        except ValidationError as e:
            if self._config_logger:
                self._config_logger.error("配置验证失败", error=str(e))
            raise ValueError(f"配置验证失败，请检查 application.yml: {e}") from e
    
    def __getattr__(self, name: str) -> Any:
        """动态属性访问：支持大写属性名访问配置"""
        # 路径配置（需要特殊处理：解析为Path对象）
        path_mapping = {
            'RAW_DATA_PATH': 'raw_data',
            'PROCESSED_DATA_PATH': 'processed_data',
            'VECTOR_STORE_PATH': 'vector_store',
            'SESSIONS_PATH': 'sessions',
            'ACTIVITY_LOG_PATH': 'activity_log',
            'GITHUB_REPOS_PATH': 'github_repos',
            'GITHUB_SYNC_STATE_PATH': 'github_sync_state',
            'CACHE_STATE_PATH': 'cache_state',  # 已废弃：缓存管理器功能已移除，此配置不再使用
        }
        
        if name in path_mapping:
            path_str = getattr(self._model.paths, path_mapping[name])
            return self._resolve_path(path_str)
        
        # 列表配置（需要特殊处理）
        if name == 'RAGAS_METRICS':
            return [str(m).strip() for m in self._model.ragas.metrics if m]
        
        if name == 'ENABLED_RETRIEVAL_STRATEGIES':
            return [str(s).strip() for s in self._model.rag.multi_strategy.enabled_strategies if s]
        
        if name == 'RETRIEVER_WEIGHTS':
            return self._model.rag.multi_strategy.retriever_weights
        
        if name == 'INDEX_STRATEGY':
            return self._model.batch_processing.index_strategy.lower()
        
        # 环境变量配置（敏感信息）
        env_mapping = {
            'DEEPSEEK_API_KEY': lambda: os.getenv("DEEPSEEK_API_KEY", ""),
            'HF_TOKEN': lambda: os.getenv("HF_TOKEN", None),
            'CHROMA_CLOUD_API_KEY': lambda: os.getenv("CHROMA_CLOUD_API_KEY", ""),
            'CHROMA_CLOUD_TENANT': lambda: os.getenv("CHROMA_CLOUD_TENANT", ""),
            'CHROMA_CLOUD_DATABASE': lambda: os.getenv("CHROMA_CLOUD_DATABASE", ""),
            'RERANK_MODEL': lambda: os.getenv("RERANK_MODEL", None),
        }
        
        if name in env_mapping:
            return env_mapping[name]()
        
        if name == 'MODULE_CONFIG_PATH':
            # 优先从YAML读取，否则从环境变量
            if self._model.module_registry.config_path:
                return self._model.module_registry.config_path
            return os.getenv("MODULE_CONFIG_PATH", None)
        
        # 从属性映射表获取
        if name in self._PROPERTY_MAPPING:
            return self._PROPERTY_MAPPING[name](self._model)
        
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def _resolve_path(self, path_str: str) -> Path:
        """解析路径，支持相对路径和绝对路径
        
        Args:
            path_str: 路径字符串
            
        Returns:
            Path对象
        """
        path = Path(path_str)
        if not path.is_absolute():
            path = self.PROJECT_ROOT / path
        return path
    
    def ensure_directories(self) -> None:
        """确保所有必要的目录存在"""
        from backend.infrastructure.config.paths import ensure_directories, get_required_directories
        directories = get_required_directories(self)
        ensure_directories(directories)
    
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
        
        # 索引配置验证（Pydantic已经验证，但这里做额外检查）
        if self.CHUNK_SIZE <= 0:
            return False, "CHUNK_SIZE必须大于0"
        if self.CHUNK_OVERLAP < 0:
            return False, "CHUNK_OVERLAP必须大于等于0"
        if self.CHUNK_OVERLAP >= self.CHUNK_SIZE:
            return False, "CHUNK_OVERLAP必须小于CHUNK_SIZE"
        
        return True, None
    
    def __repr__(self) -> str:
        """返回配置的字符串表示（隐藏敏感信息）"""
        attrs = []
        for key in dir(self):
            if key.isupper() and not key.startswith('_'):
                try:
                    value = getattr(self, key)
                    # 隐藏敏感信息
                    if 'key' in key.lower() or 'token' in key.lower() or 'secret' in key.lower():
                        attrs.append(f"    {key}=***")
                    elif isinstance(value, Path):
                        attrs.append(f"    {key}={value}")
                    else:
                        attrs.append(f"    {key}={value}")
                except Exception:
                    pass  # 忽略无法访问的属性
        return f"Config(\n" + "\n".join(attrs[:20]) + "\n    ...\n)"


# 添加COLLECTION_NAME属性（别名）
def _get_collection_name(self) -> str:
    """COLLECTION_NAME属性（CHROMA_COLLECTION_NAME的别名）"""
    return self.CHROMA_COLLECTION_NAME

# 动态添加属性
Config.COLLECTION_NAME = property(_get_collection_name)
