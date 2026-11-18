"""
Chroma客户端管理器：全局单例，复用CloudClient连接

主要功能：
- ChromaClientManager类：管理Chroma CloudClient的全局单例
- get_client()：获取或创建CloudClient实例
- get_collection()：获取或创建Collection实例

特性：
- 延迟初始化：首次使用时连接
- 全局复用：避免重复创建连接
- 线程安全：使用锁保护
"""

import threading
from typing import Optional

import chromadb
from chromadb.api.models.Collection import Collection

from backend.infrastructure.config import config
from backend.infrastructure.logger import get_logger

logger = get_logger('chroma_client')


class ChromaClientManager:
    """Chroma CloudClient 全局单例管理器
    
    复用连接，减少握手延迟。首次调用时初始化连接。
    """
    
    _lock = threading.Lock()
    _client: Optional[chromadb.CloudClient] = None
    _collections: dict[str, Collection] = {}
    
    @classmethod
    def get_client(cls) -> chromadb.CloudClient:
        """获取全局 CloudClient 实例
        
        Returns:
            chromadb.CloudClient: 全局单例客户端
            
        Raises:
            ValueError: 配置不完整
            Exception: 连接失败
        """
        if cls._client is not None:
            return cls._client
        
        with cls._lock:
            # 双重检查锁定
            if cls._client is not None:
                return cls._client
            
            logger.info("🗄️  初始化 Chroma Cloud 客户端（全局单例）")
            
            # 验证配置
            if not config.CHROMA_CLOUD_API_KEY or not config.CHROMA_CLOUD_DATABASE:
                raise ValueError(
                    "Chroma Cloud 配置不完整，请设置以下环境变量：\n"
                    "- CHROMA_CLOUD_API_KEY\n"
                    "- CHROMA_CLOUD_DATABASE"
                )
            
            tenant = config.CHROMA_CLOUD_TENANT
            if not tenant or tenant == "your_chroma_cloud_tenant_here":
                logger.warning("⚠️  CHROMA_CLOUD_TENANT 未设置或为模板值，将尝试自动检测...")
                tenant = None
            
            try:
                if tenant:
                    cls._client = chromadb.CloudClient(
                        api_key=config.CHROMA_CLOUD_API_KEY,
                        tenant=tenant,
                        database=config.CHROMA_CLOUD_DATABASE
                    )
                else:
                    cls._client = chromadb.CloudClient(
                        api_key=config.CHROMA_CLOUD_API_KEY,
                        database=config.CHROMA_CLOUD_DATABASE
                    )
                
                logger.info("✅ Chroma Cloud 客户端初始化成功（全局单例）")
                return cls._client
                
            except chromadb.errors.ChromaAuthError as e:
                error_msg = str(e)
                if "does not match" in error_msg and "from the server" in error_msg:
                    import re
                    tenant_match = re.search(r'does not match ([a-f0-9\-]+) from the server', error_msg)
                    if tenant_match:
                        correct_tenant = tenant_match.group(1)
                        logger.error(f"❌ Chroma Cloud Tenant 配置错误")
                        logger.error(f"   当前配置: {config.CHROMA_CLOUD_TENANT}")
                        logger.error(f"   服务器返回的正确 Tenant: {correct_tenant}")
                        raise ValueError(
                            f"Chroma Cloud Tenant 配置不匹配！\n"
                            f"当前配置: {config.CHROMA_CLOUD_TENANT}\n"
                            f"服务器返回的正确 Tenant: {correct_tenant}\n\n"
                            f"请在 .env 文件中更新配置：\n"
                            f"CHROMA_CLOUD_TENANT={correct_tenant}"
                        )
                raise
            except Exception as e:
                logger.error(f"❌ Chroma Cloud 客户端初始化失败: {e}")
                raise
    
    @classmethod
    def get_collection(cls, collection_name: str) -> Collection:
        """获取或创建 Collection 实例
        
        Args:
            collection_name: Collection 名称
            
        Returns:
            Collection: Chroma Collection 实例
        """
        # 检查缓存
        if collection_name in cls._collections:
            return cls._collections[collection_name]
        
        with cls._lock:
            # 双重检查
            if collection_name in cls._collections:
                return cls._collections[collection_name]
            
            client = cls.get_client()
            
            try:
                collection = client.get_or_create_collection(
                    name=collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
                cls._collections[collection_name] = collection
                logger.info(f"✅ 获取/创建 Collection: {collection_name}")
                return collection
                
            except Exception as e:
                logger.error(f"❌ 创建 Collection 失败: {e}")
                raise
    
    @classmethod
    def reset(cls) -> None:
        """重置客户端（用于测试或重新连接）"""
        with cls._lock:
            cls._client = None
            cls._collections.clear()
            logger.info("🔄 Chroma 客户端已重置")
    
    @classmethod
    def is_initialized(cls) -> bool:
        """检查客户端是否已初始化"""
        return cls._client is not None


# 便捷函数
def get_chroma_client() -> chromadb.CloudClient:
    """获取全局 Chroma 客户端"""
    return ChromaClientManager.get_client()


def get_chroma_collection(collection_name: str) -> Collection:
    """获取 Chroma Collection"""
    return ChromaClientManager.get_collection(collection_name)
