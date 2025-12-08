"""
维度检查模块：确保collection的embedding维度与当前模型匹配
"""

from typing import TYPE_CHECKING, Optional, Any

from src.infrastructure.logger import get_logger

if TYPE_CHECKING:
    from src.infrastructure.indexer.core.manager import IndexManager

logger = get_logger('indexer')


def ensure_collection_dimension_match(
    index_manager: "IndexManager",
    collection_count: Optional[int] = None,
    sample_data: Optional[Any] = None
) -> None:
    """确保collection的embedding维度与当前模型匹配
    
    Args:
        index_manager: 索引管理器实例
        collection_count: collection的向量数量（如果已获取，避免重复查询）
        sample_data: collection的样本数据（如果已获取，避免重复查询）
    
    如果collection已存在但维度不匹配，会抛出错误提示用户手动处理
    """
    try:
        # 检测模型维度
        model_dim = None
        dim_detection_methods = []
        
        # 方法1: 尝试从模型属性获取（最快速，无需计算）
        if hasattr(index_manager.embed_model, 'embed_dim'):
            model_dim = index_manager.embed_model.embed_dim
            dim_detection_methods.append("embed_dim属性")
        elif hasattr(index_manager.embed_model, '_model') and hasattr(index_manager.embed_model._model, 'config'):
            try:
                model_dim = getattr(index_manager.embed_model._model.config, 'hidden_size', None)
                if model_dim:
                    dim_detection_methods.append("模型config.hidden_size")
            except Exception as e:
                logger.debug(f"从模型config获取维度失败: {e}")
        
        # 方法2: 通过实际计算一个测试向量获取维度（最可靠，但需要计算）
        if model_dim is None:
            try:
                test_embedding = index_manager.embed_model.get_query_embedding("test")
                if hasattr(test_embedding, 'shape') and len(test_embedding.shape) > 0:
                    model_dim = int(test_embedding.shape[0])
                elif hasattr(test_embedding, '__len__'):
                    model_dim = int(len(test_embedding))
                else:
                    model_dim = int(test_embedding)
                dim_detection_methods.append("实际计算测试向量")
            except Exception as e:
                logger.warning(f"通过测试向量获取维度失败: {e}")
        
        if model_dim is not None:
            model_dim = int(model_dim)
        
        if model_dim is None:
            error_msg = "无法检测embedding模型维度，这可能导致维度不匹配错误"
            logger.error(f"{error_msg}, 尝试的方法: {dim_detection_methods}")
            raise ValueError(error_msg)
        
        logger.info(f"✅ 成功检测到embedding模型维度: {model_dim} (方法: {', '.join(dim_detection_methods)})")
        logger.info(f"📏 当前embedding模型维度: {model_dim}")
        
        # 直接使用已有的 chroma_collection，不重新获取
        chroma_collection = index_manager.chroma_collection
        
        # 如果未提供 collection_count，则查询（向后兼容）
        if collection_count is None:
            try:
                collection_count = chroma_collection.count()
            except Exception as e:
                logger.warning(f"获取collection数量失败: {e}")
                collection_count = 0
        
        collection_dim = None
        
        try:
            # 尝试从collection的metadata获取
            if chroma_collection.metadata and 'embedding_dimension' in chroma_collection.metadata:
                collection_dim = int(chroma_collection.metadata['embedding_dimension'])
                logger.info(f"从collection metadata获取维度: {collection_dim}")
            elif collection_count > 0:
                # 从实际数据获取维度
                # 如果已提供 sample_data，直接使用；否则查询
                sample = sample_data
                if sample is None:
                    try:
                        sample = chroma_collection.peek(limit=1)
                    except Exception as e:
                        logger.warning(f"获取collection样本数据失败: {e}")
                        sample = None
                
                if sample and 'embeddings' in sample:
                    embeddings_data = sample['embeddings']
                    if embeddings_data is not None:
                        try:
                            if isinstance(embeddings_data, list):
                                has_data = len(embeddings_data) > 0
                            elif hasattr(embeddings_data, '__len__'):
                                has_data = len(embeddings_data) > 0
                            else:
                                has_data = True
                        except (TypeError, ValueError):
                            has_data = False
                        
                        if has_data:
                            try:
                                if isinstance(embeddings_data, list) and len(embeddings_data) > 0:
                                    first_embedding = embeddings_data[0]
                                elif hasattr(embeddings_data, '__getitem__'):
                                    first_embedding = embeddings_data[0]
                                else:
                                    first_embedding = embeddings_data
                                
                                if hasattr(first_embedding, 'shape') and len(first_embedding.shape) > 0:
                                    collection_dim = int(first_embedding.shape[0])
                                elif hasattr(first_embedding, '__len__'):
                                    collection_dim = int(len(first_embedding))
                                else:
                                    collection_dim = int(first_embedding)
                                
                                if collection_dim is not None:
                                    logger.info(f"从collection实际数据获取维度: {collection_dim}")
                            except (TypeError, ValueError, IndexError) as dim_error:
                                logger.warning(f"无法从embedding数据获取维度: {dim_error}")
                                collection_dim = None
        except Exception as e:
            logger.warning(f"获取collection维度失败: {e}")
        
        # 如果collection为空，直接使用
        if collection_count == 0:
            logger.info(f"✅ Collection为空，可以使用: {index_manager.collection_name}")
        # 如果无法获取维度，抛出错误
        elif collection_dim is None:
            error_msg = (
                f"⚠️  Collection '{index_manager.collection_name}' 有数据但无法检测维度。"
                f"当前模型维度: {model_dim}。"
                f"请手动清理collection或检查数据完整性。"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        # 如果维度不匹配，直接报错
        elif int(model_dim) != int(collection_dim):
            error_msg = (
                f"⚠️  Embedding维度不匹配！"
                f"Collection '{index_manager.collection_name}' 维度: {collection_dim}, "
                f"当前模型维度: {model_dim}。"
                f"请手动清理collection或切换匹配的embedding模型。"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        else:
            # 维度匹配，使用现有collection
            logger.info(f"✅ Collection维度检查通过: {model_dim}维")
                
    except ValueError:
        raise
    except Exception as e:
        error_msg = f"维度检测过程出错: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e
