"""
模块注册中心初始化

注册所有内置模块
"""

from src.business.registry import ModuleRegistry, get_registry
from src.business.protocols import ModuleType, ModuleMetadata
from src.business.pipeline.adapter_factory import (
    create_retrieval_module,
    create_reranking_module,
    create_generation_module,
    create_formatting_module,
)

logger = setup_logger('module_registry_init')


def register_builtin_modules(registry: Optional[ModuleRegistry] = None):
    """注册内置模块
    
    Args:
        registry: 模块注册中心（可选，默认使用全局实例）
    """
    if registry is None:
        registry = get_registry()
    
    # 注册检索模块
    registry.register(
        metadata=ModuleMetadata(
            name="modular_retrieval",
            module_type=ModuleType.RETRIEVAL,
            version="1.0.0",
            description="ModularQueryEngine检索模块",
            dependencies=["ModularQueryEngine"],
        ),
        factory=create_retrieval_module,
        config_schema={
            "defaults": {},
            "properties": {
                "retrieval_strategy": {"type": "string", "default": "vector"},
                "similarity_top_k": {"type": "integer", "default": 5},
            }
        }
    )
    
    # 注册重排序模块
    registry.register(
        metadata=ModuleMetadata(
            name="modular_reranking",
            module_type=ModuleType.RERANKING,
            version="1.0.0",
            description="ModularQueryEngine重排序模块",
            dependencies=["create_reranker"],
        ),
        factory=create_reranking_module,
        config_schema={
            "defaults": {},
            "properties": {
                "reranker_type": {"type": "string", "default": "sentence-transformer"},
                "rerank_top_n": {"type": "integer", "default": 3},
            }
        }
    )
    
    # 注册生成模块
    registry.register(
        metadata=ModuleMetadata(
            name="modular_generation",
            module_type=ModuleType.GENERATION,
            version="1.0.0",
            description="ModularQueryEngine生成模块",
            dependencies=["ModularQueryEngine"],
        ),
        factory=create_generation_module,
        config_schema={
            "defaults": {},
            "properties": {}
        }
    )
    
    # 注册格式化模块
    registry.register(
        metadata=ModuleMetadata(
            name="modular_formatting",
            module_type=ModuleType.FORMATTING,
            version="1.0.0",
            description="ModularQueryEngine格式化模块",
            dependencies=["ModularQueryEngine"],
        ),
        factory=create_formatting_module,
        config_schema={
            "defaults": {},
            "properties": {}
        }
    )
    
    logger.info(f"注册内置模块完成: {len(registry.list_modules())} 个模块")


def load_modules_from_config(config_path: Optional[str] = None):
    """从配置文件加载模块
    
    Args:
        config_path: 配置文件路径（可选，默认使用config.MODULE_CONFIG_PATH）
    """
    from src.config import config
    
    if config_path is None:
        config_path = getattr(config, 'MODULE_CONFIG_PATH', None)
        if not config_path:
            logger.info("未配置MODULE_CONFIG_PATH，跳过YAML加载")
            return
    
    registry = get_registry()
    registry.load_from_yaml(config_path)
    
    logger.info(f"从配置加载模块完成: {len(registry.list_modules())} 个模块")


# 自动注册内置模块
def init_registry():
    """初始化模块注册中心"""
    registry = get_registry()
    register_builtin_modules(registry)
    load_modules_from_config()
    return registry

