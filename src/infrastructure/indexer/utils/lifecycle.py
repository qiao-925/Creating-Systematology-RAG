"""
生命周期管理模块：关闭和资源释放功能
"""

from typing import TYPE_CHECKING

from src.infrastructure.logger import get_logger

if TYPE_CHECKING:
    from src.infrastructure.indexer.core.manager import IndexManager

logger = get_logger('indexer')


def close(index_manager: "IndexManager") -> None:
    """关闭索引管理器，释放资源
    
    显式关闭 Chroma 客户端连接，停止后台线程
    应该在应用关闭时调用此方法
    """
    try:
        logger.info("🔧 开始关闭索引管理器...")
        
        # 1. 清理 Chroma 客户端
        if hasattr(index_manager, 'chroma_client') and index_manager.chroma_client is not None:
            try:
                client = index_manager.chroma_client
                
                # 方法1: 尝试调用 close() 方法
                if hasattr(client, 'close'):
                    client.close()
                    logger.info("✅ Chroma客户端已通过 close() 方法关闭")
                # 方法2: 尝试调用 reset() 方法
                elif hasattr(client, 'reset'):
                    client.reset()
                    logger.info("✅ Chroma客户端已通过 reset() 方法重置")
                # 方法3: 尝试访问内部属性并关闭
                elif hasattr(client, '_client'):
                    inner_client = getattr(client, '_client', None)
                    if inner_client and hasattr(inner_client, 'close'):
                        inner_client.close()
                        logger.info("✅ Chroma内部客户端已关闭")
                
                # 清理引用
                index_manager.chroma_client = None
                logger.info("✅ Chroma客户端引用已清理")
                
            except Exception as e:
                logger.warning(f"⚠️  关闭 Chroma 客户端时出错: {e}")
                index_manager.chroma_client = None
        
        # 2. 清理其他引用
        if hasattr(index_manager, 'chroma_collection'):
            index_manager.chroma_collection = None
        if hasattr(index_manager, 'vector_store'):
            index_manager.vector_store = None
        if hasattr(index_manager, 'storage_context'):
            index_manager.storage_context = None
        if hasattr(index_manager, '_index'):
            index_manager._index = None
        
        # 3. 强制垃圾回收
        try:
            import gc
            gc.collect()
            logger.debug("✅ 已执行垃圾回收")
        except Exception as e:
            logger.debug(f"垃圾回收时出错: {e}")
        
        logger.info("✅ 索引管理器资源已释放")
        
    except Exception as e:
        logger.warning(f"⚠️  关闭索引管理器时出错: {e}")
        # 即使出错，也要尽可能清理引用
        try:
            index_manager.chroma_client = None
            index_manager.chroma_collection = None
            index_manager.vector_store = None
            index_manager.storage_context = None
            index_manager._index = None
        except Exception:
            pass
