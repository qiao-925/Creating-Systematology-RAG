"""
索引维度检查和匹配模块
确保collection的embedding维度与当前模型匹配
"""

from src.logger import setup_logger

logger = setup_logger('indexer')


def ensure_collection_dimension_match(index_manager):
    """确保collection的embedding维度与当前模型匹配
    
    如果collection已存在但维度不匹配，会自动删除并重新创建
    """
    try:
        # 检测模型维度
        # 不同embedding模型有不同的向量维度（如384、768、1024等）
        # 维度不匹配会导致向量检索失败，必须在初始化阶段检测
        model_dim = None
        dim_detection_methods = []
        
        # 方法1: 尝试从模型属性获取（最快速，无需计算）
        # 优先使用模型自带的维度信息，避免不必要的计算开销
        if hasattr(index_manager.embed_model, 'embed_dim'):
            model_dim = index_manager.embed_model.embed_dim
            dim_detection_methods.append("embed_dim属性")
        elif hasattr(index_manager.embed_model, '_model') and hasattr(index_manager.embed_model._model, 'config'):
            # HuggingFace模型的config中通常包含hidden_size（即embedding维度）
            try:
                model_dim = getattr(index_manager.embed_model._model.config, 'hidden_size', None)
                if model_dim:
                    dim_detection_methods.append("模型config.hidden_size")
            except Exception as e:
                logger.debug(f"从模型config获取维度失败: {e}")
        
        # 方法2: 通过实际计算一个测试向量获取维度（最可靠，但需要计算）
        # 当模型属性不可用时，实际计算是最可靠的方法，确保获取真实维度
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
        
        # 尝试获取现有collection
        try:
            existing_collection = index_manager.chroma_client.get_collection(name=index_manager.collection_name)
            collection_dim = None
            collection_count = existing_collection.count()
            
            try:
                # 尝试从collection的metadata获取
                if existing_collection.metadata and 'embedding_dimension' in existing_collection.metadata:
                    collection_dim = int(existing_collection.metadata['embedding_dimension'])
                    logger.info(f"从collection metadata获取维度: {collection_dim}")
                elif collection_count > 0:
                    # 从实际数据获取维度
                    sample = existing_collection.peek(limit=1)
                    if sample and 'embeddings' in sample and sample['embeddings']:
                        embeddings_data = sample['embeddings']
                        if isinstance(embeddings_data, list) and len(embeddings_data) > 0:
                            first_embedding = embeddings_data[0]
                        else:
                            first_embedding = embeddings_data[0] if hasattr(embeddings_data, '__getitem__') else embeddings_data
                        
                        try:
                            if hasattr(first_embedding, 'shape') and len(first_embedding.shape) > 0:
                                collection_dim = int(first_embedding.shape[0])
                            elif hasattr(first_embedding, '__len__'):
                                collection_dim = int(len(first_embedding))
                            else:
                                collection_dim = int(first_embedding)
                        except (TypeError, ValueError) as dim_error:
                            logger.warning(f"无法从embedding数据获取维度: {dim_error}")
                            collection_dim = None
                        
                        if collection_dim is not None:
                            logger.info(f"从collection实际数据获取维度: {collection_dim}")
            except Exception as e:
                logger.warning(f"获取collection维度失败: {e}")
            
            # 如果collection为空，直接使用
            # 空collection没有维度约束，可以接受任何维度的向量
            if collection_count == 0:
                index_manager.chroma_collection = existing_collection
                logger.info(f"✅ Collection为空，可以使用: {index_manager.collection_name}")
            # 如果无法获取维度，采用保守策略：删除并重建
            # 无法检测维度时无法保证一致性，宁可丢失数据也要保证系统可用性
            # 这是防御性编程：避免后续操作因维度不匹配而失败
            elif collection_dim is None:
                logger.warning(f"⚠️  Collection有数据但无法检测维度，采用保守策略删除并重建")
                logger.info(f"   当前模型维度: {model_dim}")
                logger.info(f"🔄 自动删除旧collection并重新创建...")
                
                index_manager.chroma_client.delete_collection(name=index_manager.collection_name)
                logger.warning(f"因无法检测维度，已删除collection: {index_manager.collection_name}")
                
                index_manager.chroma_collection = index_manager.chroma_client.get_or_create_collection(
                    name=index_manager.collection_name
                )
                logger.warning(f"✅ 已重新创建collection: {index_manager.collection_name}")
                logger.warning(f"⚠️  **重要**: Collection已重新创建，原有数据已被清除")
            # 如果维度不匹配，删除并重建
            elif int(model_dim) != int(collection_dim):
                logger.warning(f"⚠️  检测到embedding维度不匹配:")
                logger.info(f"   Collection维度: {collection_dim}")
                logger.info(f"   当前模型维度: {model_dim}")
                logger.info(f"🔄 自动删除旧collection并重新创建...")
                
                index_manager.chroma_client.delete_collection(name=index_manager.collection_name)
                logger.info(f"已删除维度不匹配的collection: {index_manager.collection_name}")
                
                index_manager.chroma_collection = index_manager.chroma_client.get_or_create_collection(
                    name=index_manager.collection_name
                )
                logger.warning(f"✅ 已重新创建collection: {index_manager.collection_name} (维度: {model_dim})")
                logger.warning(f"⚠️  **重要**: Collection已重新创建，原有数据已被清除")
            else:
                # 维度匹配，使用现有collection
                index_manager.chroma_collection = existing_collection
                logger.info(f"✅ Collection维度检查通过: {model_dim}维")
                
        except Exception as e:
            # Collection不存在，创建新的
            if "does not exist" in str(e) or "not found" in str(e).lower():
                index_manager.chroma_collection = index_manager.chroma_client.get_or_create_collection(
                    name=index_manager.collection_name
                )
                logger.info(f"✅ 创建新collection: {index_manager.collection_name} (维度: {model_dim})")
            else:
                logger.error(f"获取collection时出错: {e}")
                raise
                
    except Exception as e:
        # 如果检测过程出错，尝试删除旧collection并重建
        # 检测失败可能意味着collection处于不一致状态，保守策略是重建
        # 内层try-except处理删除失败（collection可能不存在），外层处理重建失败
        logger.error(f"维度检测过程出错: {e}")
        logger.info("采用保守策略：删除旧collection并重建")
        
        try:
            # 嵌套try-except：删除失败不应该阻止重建尝试
            # collection可能已被删除或不存在，此时应该继续尝试创建
            try:
                index_manager.chroma_client.delete_collection(name=index_manager.collection_name)
                logger.info(f"🔄 已删除可能不兼容的collection: {index_manager.collection_name}")
            except:
                pass
            
            index_manager.chroma_collection = index_manager.chroma_client.get_or_create_collection(
                name=index_manager.collection_name
            )
            logger.info(f"✅ 已重新创建collection: {index_manager.collection_name}")
        except Exception as fallback_error:
            logger.error(f"回退创建collection也失败: {fallback_error}")
            raise

