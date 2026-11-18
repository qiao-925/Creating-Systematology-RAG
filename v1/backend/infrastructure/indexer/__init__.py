"""
索引构建模块 (Indexer Package)：提供向量索引的构建、管理和维护功能

核心功能：从文档构建向量索引，提供搜索、更新、统计等管理功能。

快速开始：
    >>> from backend.infrastructure.indexer import IndexService
    >>> service = IndexService(collection_name="my_collection")
    >>> index, vector_ids = service.build_index(documents)
    >>> results = service.search("查询文本")

主要接口：
- IndexService: 统一索引服务（推荐）
  - build_index(): 构建或更新索引
  - search(): 搜索相似文档
  - get_stats(): 获取统计信息
  - incremental_update(): 增量更新
- IndexManager: 底层索引管理器（高级用法）
- 便捷函数: create_index_from_directory()

模块结构：
- service.py: 服务层，统一索引接口和流程编排
- core/: 核心层（IndexManager、初始化）
- build/: 构建层（构建入口、正常模式、文档过滤）
- utils/: 工具层（统计、清理、更新、ID管理、文档操作等）

设计说明：
本包采用服务层统一接口，类似 data_loader 的设计模式。
将索引管理的不同职责按层级拆分，提高代码可维护性。
"""

# 统一服务类（推荐使用）
from backend.infrastructure.indexer.service import IndexService

# 底层组件（高级用法）
from backend.infrastructure.indexer.core.manager import IndexManager

# 便捷函数
from backend.infrastructure.indexer.utils.convenience import create_index_from_directory

# Embedding状态查询（向后兼容）
def get_embedding_model_status() -> dict:
    """获取Embedding模型状态（向后兼容函数）
    
    Returns:
        包含模型状态的字典：
        {
            "model_name": str,           # 模型名称
            "loaded": bool,               # 是否已加载到内存
            "cache_exists": bool,         # 本地缓存是否存在
            "offline_mode": bool,         # 是否离线模式
            "mirror": str,                # 镜像地址
        }
    """
    from backend.infrastructure.embeddings.cache import get_embedding_status
    
    status = get_embedding_status()
    
    # 转换格式以兼容旧代码
    return {
        "model_name": status["model_name"],
        "loaded": status["base_embedding_loaded"],
        "cache_exists": status["cache_exists"],
        "offline_mode": status["offline_mode"],
        "mirror": status["mirror"],
    }

# 公共API导出列表
__all__ = [
    # 统一服务接口（推荐使用）
    'IndexService',
    # 底层组件（高级用法）
    'IndexManager',
    # 便捷函数
    'create_index_from_directory',
    # Embedding状态查询
    'get_embedding_model_status',
]
