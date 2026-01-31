"""
Pydantic配置模型 - 定义所有配置项的模型结构

主要功能：
- 定义嵌套的配置模型（AppConfig, APIConfig, ModelConfig等）
- 提供字段验证和类型转换
- 支持环境变量和YAML配置的映射
"""

from pathlib import Path
from typing import Optional, Dict, List

from pydantic import BaseModel, Field, field_validator


# ==================== 嵌套配置模型 ====================

class AppConfig(BaseModel):
    """应用基础配置"""
    title: str
    port: int
    dev_mode: bool = True


class LoggingConfig(BaseModel):
    """日志配置"""
    level: str = "INFO"
    file_level: str = "DEBUG"


class CacheConfig(BaseModel):
    """缓存配置"""
    enable: bool = True


class DeepSeekAPIConfig(BaseModel):
    """DeepSeek API配置"""
    base: str


class APIConfig(BaseModel):
    """API配置"""
    deepseek: DeepSeekAPIConfig


class HuggingFaceConfig(BaseModel):
    """HuggingFace配置"""
    endpoint: str
    offline_mode: bool = False


class GitHubConfig(BaseModel):
    """GitHub配置"""
    default_branch: str = "main"


class LLMModelConfig(BaseModel):
    """单个 LLM 模型配置"""
    id: str  # 模型标识（如 "deepseek-chat"）
    name: str  # 显示名称（如 "DeepSeek Chat"）
    litellm_model: str  # LiteLLM 模型标识（如 "deepseek/deepseek-chat"）
    api_key_env: str  # API Key 环境变量名
    temperature: Optional[float] = 0.7  # 温度参数
    max_tokens: Optional[int] = 4096  # 最大 token 数
    supports_reasoning: bool = False  # 是否支持推理链
    request_timeout: Optional[float] = 30.0  # API 请求超时时间（秒）


class LLMModelsConfig(BaseModel):
    """LLM 多模型配置"""
    default: str = "deepseek-chat"  # 默认模型 ID
    available: List[LLMModelConfig] = []  # 可用模型列表
    initialization_timeout: float = 30.0  # 初始化超时时间（秒）
    max_retries: int = 3  # 最大重试次数
    retry_delay: float = 2.0  # 重试延迟（秒，指数退避）


class ModelConfig(BaseModel):
    """模型配置"""
    llm: str  # 向后兼容：单模型配置
    embedding: str
    llms: Optional[LLMModelsConfig] = None  # 多模型配置（可选）


class EmbeddingConfig(BaseModel):
    """Embedding配置"""
    type: str
    api_url: Optional[str] = None
    batch_size: int = 10
    max_length: int = 512


class DeepSeekConfig(BaseModel):
    """DeepSeek推理模型配置"""
    enable_reasoning_display: bool = True
    store_reasoning: bool = False
    json_output_enabled: bool = False


class VectorStoreConfig(BaseModel):
    """向量存储配置"""
    collection_name: str = "default"


class PathsConfig(BaseModel):
    """路径配置（字符串形式，后续会解析为Path）"""
    raw_data: str
    processed_data: str
    vector_store: str
    activity_log: str
    github_repos: str
    github_sync_state: str
    cache_state: str
    sessions: str = "./data/sessions"  # 会话持久化目录


class IndexConfig(BaseModel):
    """索引配置"""
    chunk_size: int
    chunk_overlap: int
    similarity_top_k: int
    similarity_threshold: float
    
    @field_validator('chunk_overlap')
    def validate_overlap(cls, v: int, info) -> int:
        """验证chunk_overlap必须小于chunk_size"""
        chunk_size = info.data.get('chunk_size', 0)
        if v >= chunk_size:
            raise ValueError('chunk_overlap 必须小于 chunk_size')
        if v < 0:
            raise ValueError('chunk_overlap 必须大于等于0')
        return v
    
    @field_validator('chunk_size')
    def validate_chunk_size(cls, v: int) -> int:
        """验证chunk_size必须大于0"""
        if v <= 0:
            raise ValueError('chunk_size 必须大于0')
        return v


class RerankerConfig(BaseModel):
    """重排序器配置"""
    type: str = "sentence-transformer"
    model: Optional[str] = None
    top_n: int = 3


class MultiStrategyConfig(BaseModel):
    """多策略检索配置"""
    enabled_strategies: List[str]
    merge_strategy: str = "reciprocal_rank_fusion"
    retriever_weights: Dict[str, float]
    enable_deduplication: bool = True


class RAGConfig(BaseModel):
    """RAG核心配置"""
    retrieval_strategy: str = "vector"
    enable_rerank: bool = False
    reranker: RerankerConfig
    similarity_cutoff: float = 0.4
    hybrid_alpha: float = 0.5
    enable_auto_routing: bool = True
    multi_strategy: MultiStrategyConfig


class ModuleRegistryConfig(BaseModel):
    """模块注册中心配置"""
    config_path: Optional[str] = None
    auto_register_modules: bool = True


class BatchProcessingConfig(BaseModel):
    """批处理配置"""
    index_batch_mode: bool = False
    index_group_by: str = "directory"
    group_depth: int = 1
    docs_per_batch: int = 20
    nodes_per_batch: int = 0
    tokens_per_batch: int = 0
    index_strategy: str = "nodes"
    index_max_batches: int = 0


class LlamaDebugConfig(BaseModel):
    """LlamaDebug配置"""
    enable: bool = True  # 默认启用
    print_trace: bool = True


class ObservabilityConfig(BaseModel):
    """可观测性配置"""
    llama_debug: LlamaDebugConfig


class RagasConfig(BaseModel):
    """RAGAS评估器配置"""
    enable: bool = True  # 默认启用
    metrics: List[str] = [
        "faithfulness",
        "context_precision",
        "context_recall",
        "answer_relevancy",
        "context_relevancy",
    ]
    batch_size: int = 10


class TestGitHubConfig(BaseModel):
    """测试GitHub配置"""
    owner: str
    repo: str
    branch: str = "main"


class TestConfig(BaseModel):
    """测试配置"""
    github: TestGitHubConfig


# ==================== 主配置模型 ====================

class ConfigModel(BaseModel):
    """主配置模型 - 包含所有配置项"""
    
    # 应用配置
    app: AppConfig
    logging: LoggingConfig
    cache: CacheConfig
    
    # API与外部服务
    api: APIConfig
    huggingface: HuggingFaceConfig
    github: GitHubConfig
    
    # 模型配置
    model: ModelConfig
    embedding: EmbeddingConfig
    deepseek: DeepSeekConfig
    
    # 向量存储与索引
    vector_store: VectorStoreConfig
    paths: PathsConfig
    index: IndexConfig
    
    # RAG配置
    rag: RAGConfig
    module_registry: ModuleRegistryConfig
    batch_processing: BatchProcessingConfig
    
    # 可观测性
    observability: ObservabilityConfig
    ragas: RagasConfig
    
    # 测试配置（可选）
    test: Optional[TestConfig] = None
