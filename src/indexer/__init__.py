"""
索引构建模块 (Indexer Package)

本包提供向量索引的构建、管理和维护功能，采用模块化设计，将索引管理的不同职责
拆分到多个子模块中，提升代码的可维护性和可读性。

架构设计
--------
本包采用模块化设计，将索引管理的不同职责拆分：

核心模块：
- index_manager.py      : IndexManager主类，提供统一的索引管理接口
- index_init.py         : 索引初始化逻辑
- index_core.py         : 核心索引操作（获取索引、打印信息）

构建相关：
- index_builder.py      : 索引构建逻辑
- index_manager_build.py : IndexManager的build_index方法实现
- index_batch.py        : 批量处理逻辑

操作相关：
- index_operations.py   : 索引操作（搜索、统计、清空）
- index_incremental.py  : 增量更新逻辑
- index_vector_ids.py   : 向量ID管理

工具模块：
- index_convenience.py  : 便捷函数（从目录/URL创建索引）
- embedding_utils.py    : Embedding模型管理工具
- index_utils.py        : 通用工具函数

辅助模块：
- index_dimension.py    : 维度匹配检测和修复
- index_compatibility.py: 兼容性处理
- index_lifecycle.py    : 生命周期管理（关闭资源）
- index_methods.py      : 方法绑定辅助
- index_wikipedia.py    : Wikipedia增强功能

公共API
------
本包导出的主要接口：

核心类：
- IndexManager          : 索引管理器，提供统一的索引管理接口
                          用于索引构建、查询、更新等操作

便捷函数：
- create_index_from_directory : 从本地目录创建索引
- create_index_from_urls      : 从URL列表创建索引

Embedding工具：
- get_embedding_model_status  : 获取Embedding模型状态
- get_global_embed_model      : 获取全局Embedding模型
- load_embedding_model        : 加载Embedding模型
- set_global_embed_model      : 设置全局Embedding模型
- clear_embedding_model_cache : 清空Embedding模型缓存

使用示例
--------

基础使用 - 创建索引管理器：
    >>> from src.indexer import IndexManager
    >>> manager = IndexManager(collection_name="my_collection")
    >>> index = manager.build_index(documents)

便捷函数 - 从目录创建索引：
    >>> from src.indexer import create_index_from_directory
    >>> manager = create_index_from_directory("./data/documents")

Embedding管理：
    >>> from src.indexer import load_embedding_model, get_embedding_model_status
    >>> model = load_embedding_model("BAAI/bge-small-zh-v1.5")
    >>> status = get_embedding_model_status()

向后兼容性
----------
本包保持向后兼容，原有的 `from src.indexer import IndexManager` 等导入方式
仍然有效。包结构已模块化拆分，但对外接口保持一致。

注意事项
--------
- IndexManager采用延迟初始化策略，首次访问索引时才真正创建
- Embedding模型会被缓存，避免重复加载
- 增量更新时需要注意向量维度的一致性
"""

# 核心类导入
from src.indexer.index_manager import IndexManager

# 便捷函数导入
from src.indexer.index_convenience import (
    create_index_from_directory,
    create_index_from_urls,
)

# Embedding工具函数导入
from src.indexer.embedding_utils import (
    get_embedding_model_status,
    get_global_embed_model,
    load_embedding_model,
    set_global_embed_model,
    clear_embedding_model_cache,
)

# 公共API导出列表
# 这些接口是包的外部API，供其他模块使用
__all__ = [
    # 核心类
    'IndexManager',
    # 便捷函数
    'create_index_from_directory',
    'create_index_from_urls',
    # Embedding工具函数
    'get_embedding_model_status',
    'get_global_embed_model',
    'load_embedding_model',
    'set_global_embed_model',
    'clear_embedding_model_cache',
]

