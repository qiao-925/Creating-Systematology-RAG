"""
RAG引擎检索模块 - 文件级别检索策略：实现文件级别的检索功能

实现文件级别的检索功能：
- FilesViaContentRetriever: 宽泛主题查询（文件级别语义检索）
- FilesViaMetadataRetriever: 文件名查询（文件级别元数据检索）
"""

from typing import List, Dict, Optional, Set, Union
from collections import defaultdict

from llama_index.core.schema import NodeWithScore, QueryBundle

from backend.infrastructure.indexer import IndexManager
from backend.infrastructure.logger import get_logger

logger = get_logger('rag_engine.retrieval')


def group_nodes_by_file(nodes: List[NodeWithScore]) -> Dict[str, List[NodeWithScore]]:
    """按文件路径分组节点
    
    Args:
        nodes: 节点列表
        
    Returns:
        文件路径到节点列表的映射字典
    """
    file_groups = defaultdict(list)
    
    for node in nodes:
        file_path = node.node.metadata.get('file_path', '')
        if file_path:
            file_groups[file_path].append(node)
        else:
            # 如果没有 file_path，使用 'unknown' 作为键
            file_groups['unknown'].append(node)
    
    return dict(file_groups)


def calculate_file_score(file_chunks: List[NodeWithScore], top_k_chunks: int = 3) -> float:
    """计算文件的相关性分数
    
    使用文件 top_k 个最相关 chunks 的平均分数作为文件分数
    
    Args:
        file_chunks: 文件的所有 chunks（已按分数排序）
        top_k_chunks: 用于计算文件分数的 top_k chunks 数量
        
    Returns:
        文件的相关性分数（0-1）
    """
    if not file_chunks:
        return 0.0
    
    # 选择 top_k 个最相关的 chunks
    top_chunks = file_chunks[:top_k_chunks]
    
    # 计算平均分数
    scores = [node.score for node in top_chunks if node.score is not None]
    if not scores:
        return 0.0
    
    avg_score = sum(scores) / len(scores)
    return min(avg_score, 1.0)  # 确保分数在 0-1 范围内


def aggregate_file_chunks(
    file_groups: Dict[str, List[NodeWithScore]],
    top_k_files: int = 5,
    top_k_per_file: int = 3
) -> List[NodeWithScore]:
    """聚合文件 chunks，选择 top_k 文件，每个文件保留 top_k 个 chunks
    
    Args:
        file_groups: 文件路径到节点列表的映射
        top_k_files: 保留的文件数量
        top_k_per_file: 每个文件保留的 chunks 数量
        
    Returns:
        聚合后的节点列表（已去重）
    """
    # 计算每个文件的分数
    file_scores = {}
    for file_path, chunks in file_groups.items():
        # chunks 应该已经按分数排序
        sorted_chunks = sorted(chunks, key=lambda x: x.score or 0.0, reverse=True)
        file_scores[file_path] = calculate_file_score(sorted_chunks, top_k_chunks=top_k_per_file)
    
    # 按文件分数排序，选择 top_k 个文件
    sorted_files = sorted(file_scores.items(), key=lambda x: x[1], reverse=True)[:top_k_files]
    
    # 从每个文件中选择 top_k 个 chunks
    aggregated_nodes = []
    seen_nodes = set()  # 用于去重（基于节点ID或文本内容）
    
    for file_path, _ in sorted_files:
        chunks = file_groups[file_path]
        # chunks 应该已经按分数排序
        sorted_chunks = sorted(chunks, key=lambda x: x.score or 0.0, reverse=True)
        
        for chunk in sorted_chunks[:top_k_per_file]:
            # 简单的去重：基于节点文本的前100个字符
            node_key = chunk.node.text[:100] if chunk.node.text else str(id(chunk.node))
            if node_key not in seen_nodes:
                seen_nodes.add(node_key)
                aggregated_nodes.append(chunk)
    
    return aggregated_nodes


class FilesViaContentRetriever:
    """文件级别内容检索器（宽泛主题查询）
    
    实现文件级别的语义检索：
    1. 使用向量索引检索所有相关 chunks
    2. 按文件路径分组
    3. 选择 top_k 个最相关的文件
    4. 从每个文件中选择 top_k 个最相关的 chunks
    """
    
    def __init__(
        self,
        index_manager: IndexManager,
        top_k_files: int = 5,
        top_k_per_file: int = 3,
        similarity_top_k: int = 50,
    ):
        """初始化文件级别内容检索器
        
        Args:
            index_manager: 索引管理器
            top_k_files: 保留的文件数量
            top_k_per_file: 每个文件保留的 chunks 数量
            similarity_top_k: 初始检索的 chunks 数量（用于文件筛选）
        """
        self.index_manager = index_manager
        self.top_k_files = top_k_files
        self.top_k_per_file = top_k_per_file
        self.similarity_top_k = similarity_top_k
        
        logger.info(
            f"文件级别内容检索器初始化: "
            f"top_k_files={top_k_files}, "
            f"top_k_per_file={top_k_per_file}, "
            f"similarity_top_k={similarity_top_k}"
        )
    
    def retrieve(
        self, 
        query: Union[str, QueryBundle], 
        top_k: Optional[int] = None
    ) -> List[NodeWithScore]:
        """执行文件级别内容检索
        
        Args:
            query: 查询文本或 QueryBundle
            top_k: 返回的节点数量（如果提供，会覆盖 top_k_files * top_k_per_file）
            
        Returns:
            检索到的节点列表（按文件分组和分数排序）
        """
        # 提取查询字符串
        if isinstance(query, QueryBundle):
            query_str = query.query_str
        else:
            query_str = query
        
        if not query_str or not query_str.strip():
            logger.warning("查询为空，返回空结果")
            return []
        
        try:
            # Step 1: 使用向量索引检索所有相关 chunks
            index = self.index_manager.get_index()
            retriever = index.as_retriever(similarity_top_k=self.similarity_top_k)
            
            # 支持字符串和 QueryBundle
            if isinstance(query, str):
                query_bundle = QueryBundle(query_str=query)
            else:
                query_bundle = query
            
            all_nodes = retriever.retrieve(query_bundle)
            
            if not all_nodes:
                logger.info(f"未找到相关结果: {query_str[:50]}")
                return []
            
            logger.debug(
                f"文件级别内容检索: "
                f"查询={query_str[:50]}..., "
                f"初始检索结果数={len(all_nodes)}"
            )
            
            # Step 2: 按文件路径分组
            file_groups = group_nodes_by_file(all_nodes)
            
            logger.debug(
                f"文件分组完成: "
                f"文件数={len(file_groups)}, "
                f"总chunks数={sum(len(chunks) for chunks in file_groups.values())}"
            )
            
            # Step 3: 聚合文件 chunks（选择 top_k 文件，每个文件保留 top_k chunks）
            # 如果提供了 top_k，调整参数
            if top_k is not None:
                # 估算每个文件应该保留的 chunks 数量
                estimated_chunks_per_file = max(1, top_k // self.top_k_files)
                final_nodes = aggregate_file_chunks(
                    file_groups,
                    top_k_files=self.top_k_files,
                    top_k_per_file=estimated_chunks_per_file
                )
                # 最终限制到 top_k
                final_nodes = final_nodes[:top_k]
            else:
                final_nodes = aggregate_file_chunks(
                    file_groups,
                    top_k_files=self.top_k_files,
                    top_k_per_file=self.top_k_per_file
                )
            
            logger.info(
                f"文件级别内容检索完成: "
                f"查询={query_str[:50]}..., "
                f"文件数={len(file_groups)}, "
                f"最终结果数={len(final_nodes)}"
            )
            
            return final_nodes
            
        except Exception as e:
            logger.error(f"文件级别内容检索失败: {e}", exc_info=True)
            return []


class FilesViaMetadataRetriever:
    """文件级别元数据检索器（文件名查询）
    
    实现文件级别的元数据检索：
    1. 从查询中提取文件名关键词
    2. 使用元数据匹配找到文件
    3. 从匹配文件中检索所有相关 chunks
    """
    
    def __init__(
        self,
        index_manager: IndexManager,
        top_k_per_file: int = 5,
        similarity_top_k: int = 20,
    ):
        """初始化文件级别元数据检索器
        
        Args:
            index_manager: 索引管理器
            top_k_per_file: 每个文件保留的 chunks 数量
            similarity_top_k: 从每个文件中检索的 chunks 数量
        """
        self.index_manager = index_manager
        self.top_k_per_file = top_k_per_file
        self.similarity_top_k = similarity_top_k
        
        logger.info(
            f"文件级别元数据检索器初始化: "
            f"top_k_per_file={top_k_per_file}, "
            f"similarity_top_k={similarity_top_k}"
        )
    
    def _extract_file_keywords(self, query: str) -> List[str]:
        """从查询中提取文件名关键词
        
        Args:
            query: 查询文本
            
        Returns:
            文件名关键词列表
        """
        import re
        
        keywords = []
        
        # 匹配文件扩展名（.md, .pdf, .txt 等）
        ext_pattern = r'\.([a-z]+)'
        extensions = re.findall(ext_pattern, query.lower())
        keywords.extend(extensions)
        
        # 匹配 "xxx文件"、"xxx文档" 格式
        file_patterns = [
            r'([^，。！？\s]+)(?:文件|文档)',
            r'([^，。！？\s]+)\.(?:md|pdf|txt|py|docx)',
        ]
        for pattern in file_patterns:
            matches = re.findall(pattern, query)
            keywords.extend(matches)
        
        # 如果没有匹配到文件相关关键词，尝试提取可能的文件名
        if not keywords:
            # 提取查询中的主要词汇（去除停用词）
            words = re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]+', query)
            # 过滤掉常见的停用词
            stop_words = {'的', '是', '什么', '如何', '文件', '文档', '内容', '说', '讲'}
            keywords = [w for w in words if w not in stop_words and len(w) >= 2]
        
        # 去重并返回
        unique_keywords = list(set(keywords))
        logger.debug(f"提取的文件名关键词: {unique_keywords}")
        
        return unique_keywords
    
    def _match_files_by_metadata(
        self,
        keywords: List[str],
        fuzzy_match: bool = True
    ) -> List[str]:
        """通过元数据匹配找到文件
        
        Args:
            keywords: 文件名关键词列表
            fuzzy_match: 是否启用模糊匹配（部分匹配）
            
        Returns:
            匹配的文件路径列表
        """
        if not keywords:
            return []
        
        matched_files = []
        
        try:
            # 获取 Chroma collection
            chroma_collection = self.index_manager.chroma_collection
            
            # 如果启用模糊匹配，需要查询所有数据然后过滤
            if fuzzy_match:
                # 获取所有数据的元数据
                all_data = chroma_collection.get()
                metadatas = all_data.get('metadatas', [])
                ids = all_data.get('ids', [])
                
                # 匹配文件路径或文件名
                for idx, metadata in enumerate(metadatas):
                    if not metadata:
                        continue
                    
                    file_path = metadata.get('file_path', '')
                    file_name = metadata.get('file_name', '')
                    
                    # 检查是否匹配任何关键词
                    for keyword in keywords:
                        if keyword.lower() in file_path.lower() or keyword.lower() in (file_name or '').lower():
                            if file_path and file_path not in matched_files:
                                matched_files.append(file_path)
                            break
            
            else:
                # 精确匹配：使用 ChromaDB 的 where 查询
                # 注意：ChromaDB 的 where 查询不支持模糊匹配，只能精确匹配
                for keyword in keywords:
                    try:
                        # 尝试匹配 file_path
                        results = chroma_collection.get(
                            where={"file_path": keyword}
                        )
                        if results and results.get('ids'):
                            # 从结果中提取唯一的 file_path
                            metadatas = results.get('metadatas', [])
                            for metadata in metadatas:
                                if metadata and metadata.get('file_path'):
                                    file_path = metadata['file_path']
                                    if file_path not in matched_files:
                                        matched_files.append(file_path)
                    except Exception as e:
                        logger.debug(f"精确匹配失败 [{keyword}]: {e}")
                        continue
            
            logger.debug(
                f"元数据匹配完成: "
                f"关键词={keywords}, "
                f"匹配文件数={len(matched_files)}"
            )
            
            return matched_files
            
        except Exception as e:
            logger.error(f"元数据匹配失败: {e}", exc_info=True)
            return []
    
    def _retrieve_file_chunks(
        self,
        query: str,
        file_path: str,
        top_k: int
    ) -> List[NodeWithScore]:
        """从指定文件中检索相关 chunks
        
        Args:
            query: 查询文本
            file_path: 文件路径
            top_k: 返回的 chunks 数量
            
        Returns:
            检索到的节点列表
        """
        try:
            # 获取该文件的所有向量ID
            vector_ids = self.index_manager._get_vector_ids_by_metadata(file_path)
            
            if not vector_ids:
                logger.debug(f"文件没有向量ID: {file_path}")
                return []
            
            # 使用向量索引检索这些 chunks
            index = self.index_manager.get_index()
            
            # 创建查询
            if isinstance(query, str):
                query_bundle = QueryBundle(query_str=query)
            else:
                query_bundle = query
            
            # 使用向量索引检索，但需要过滤只返回指定文件的 chunks
            # 由于 LlamaIndex 的检索器不支持直接过滤向量ID，我们需要：
            # 1. 先检索更多结果
            # 2. 过滤出属于该文件的 chunks
            retriever = index.as_retriever(similarity_top_k=top_k * 2)  # 检索更多，然后过滤
            all_nodes = retriever.retrieve(query_bundle)
            
            # 过滤出属于该文件的 chunks
            file_nodes = []
            for node in all_nodes:
                node_file_path = node.node.metadata.get('file_path', '')
                if node_file_path == file_path:
                    file_nodes.append(node)
            
            # 按分数排序并返回 top_k
            file_nodes = sorted(file_nodes, key=lambda x: x.score or 0.0, reverse=True)[:top_k]
            
            return file_nodes
            
        except Exception as e:
            logger.error(f"检索文件chunks失败 [{file_path}]: {e}", exc_info=True)
            return []
    
    def retrieve(
        self, 
        query: Union[str, QueryBundle], 
        top_k: Optional[int] = None
    ) -> List[NodeWithScore]:
        """执行文件级别元数据检索
        
        Args:
            query: 查询文本或 QueryBundle
            top_k: 返回的节点数量（如果提供，会覆盖 top_k_per_file * 文件数）
            
        Returns:
            检索到的节点列表
        """
        # 提取查询字符串
        if isinstance(query, QueryBundle):
            query_str = query.query_str
        else:
            query_str = query
        
        if not query_str or not query_str.strip():
            logger.warning("查询为空，返回空结果")
            return []
        
        try:
            # Step 1: 从查询中提取文件名关键词
            keywords = self._extract_file_keywords(query_str)
            
            if not keywords:
                logger.info(f"未提取到文件名关键词: {query_str[:50]}")
                return []
            
            # Step 2: 通过元数据匹配找到文件
            matched_files = self._match_files_by_metadata(keywords, fuzzy_match=True)
            
            if not matched_files:
                logger.info(
                    f"未找到匹配的文件: "
                    f"查询={query_str[:50]}..., "
                    f"关键词={keywords}"
                )
                return []
            
            logger.debug(
                f"文件级别元数据检索: "
                f"查询={query_str[:50]}..., "
                f"匹配文件数={len(matched_files)}, "
                f"文件列表={matched_files[:5]}"
            )
            
            # Step 3: 从每个匹配文件中检索 chunks
            all_nodes = []
            for file_path in matched_files:
                # 如果提供了 top_k，平均分配给每个文件
                if top_k is not None:
                    chunks_per_file = max(1, top_k // len(matched_files))
                else:
                    chunks_per_file = self.top_k_per_file
                
                file_chunks = self._retrieve_file_chunks(query_str, file_path, chunks_per_file)
                all_nodes.extend(file_chunks)
            
            # 按分数排序
            all_nodes = sorted(all_nodes, key=lambda x: x.score or 0.0, reverse=True)
            
            # 如果提供了 top_k，限制结果数量
            if top_k is not None:
                all_nodes = all_nodes[:top_k]
            
            logger.info(
                f"文件级别元数据检索完成: "
                f"查询={query_str[:50]}..., "
                f"匹配文件数={len(matched_files)}, "
                f"最终结果数={len(all_nodes)}"
            )
            
            return all_nodes
            
        except Exception as e:
            logger.error(f"文件级别元数据检索失败: {e}", exc_info=True)
            return []
