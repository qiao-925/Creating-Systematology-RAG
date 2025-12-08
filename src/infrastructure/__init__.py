"""
基础设施层模块 - 纯技术支撑，无业务逻辑

提供通用的技术能力，包括：
- LLM 封装
- 向量化模型
- 配置管理
- 日志工具
- 索引管理
- 数据加载
- 可观测性
- Git 工具
等基础设施能力
"""

# 导出主要接口（延迟导入，避免循环依赖）
__all__ = [
    # LLM
    'llms',
    # Embeddings
    'embeddings',
    # Config
    'config',
    # Logger
    'logger',
    # Indexer
    'indexer',
    # Data Loader
    'data_loader',
    # Observers
    'observers',
    # Git
    'git',
]

