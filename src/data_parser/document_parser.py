"""
统一文档解析器
使用 SimpleDirectoryReader 解析所有支持的文件格式
"""

import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from llama_index.core import SimpleDirectoryReader
from llama_index.core.schema import Document as LlamaDocument
from src.logger import setup_logger

logger = setup_logger('document_parser')


class DocumentParser:
    """统一文档解析器
    
    使用 SimpleDirectoryReader 自动支持多种文件格式：
    - 文本文件：.md, .txt, .py, .js, .java, .cpp, .c, .h 等
    - PDF文件：.pdf
    - Word文档：.docx
    - 其他 SimpleDirectoryReader 支持的格式
    """
    
    def parse_files(
        self,
        file_paths: List[Path],
        metadata_map: Optional[Dict[Path, Dict[str, Any]]] = None,
        clean: bool = True
    ) -> List[LlamaDocument]:
        """解析文件列表，返回文档列表
        
        Args:
            file_paths: 文件路径列表
            metadata_map: 文件路径到元数据的映射（可选）
            clean: 是否清理文本（暂不使用，保留接口）
            
        Returns:
            文档列表
        """
        start_time = time.time()
        
        if not file_paths:
            logger.warning("文件路径列表为空")
            return []
        
        logger.info(f"开始解析 {len(file_paths)} 个文件")
        
        try:
            # 验证文件存在性
            valid_paths = []
            for file_path in file_paths:
                if not file_path.exists():
                    logger.warning(f"文件不存在，跳过: {file_path}")
                    continue
                if not file_path.is_file():
                    logger.warning(f"不是文件，跳过: {file_path}")
                    continue
                valid_paths.append(file_path)
            
            if not valid_paths:
                logger.warning("没有有效的文件路径")
                return []
            
            logger.info(f"有效文件数量: {len(valid_paths)}/{len(file_paths)}")
            
            # 优化：对于单个文件或少量文件，直接解析，避免读取整个目录
            documents = []
            
            # 如果文件数量很少（<=3）且在不同目录，逐个解析以提高性能
            if len(valid_paths) <= 3:
                unique_dirs = {p.parent for p in valid_paths}
                if len(unique_dirs) == len(valid_paths):
                    # 每个文件在不同目录，逐个解析
                    logger.debug("文件分散在不同目录，采用逐个解析模式")
                    for file_path in valid_paths:
                        parsed = self._parse_single_file(file_path, metadata_map)
                        documents.extend(parsed)
                    
                    elapsed = time.time() - start_time
                    logger.info(f"成功解析 {len(documents)}/{len(valid_paths)} 个文档 (耗时: {elapsed:.2f}s)")
                    return documents
            
            # 否则按目录分组批量处理
            # 按文件所在目录分组
            dir_files_map: Dict[Path, List[Path]] = {}
            for file_path in valid_paths:
                dir_path = file_path.resolve().parent  # 使用绝对路径规范化
                if dir_path not in dir_files_map:
                    dir_files_map[dir_path] = []
                dir_files_map[dir_path].append(file_path.resolve())
            
            logger.debug(f"文件分布在 {len(dir_files_map)} 个目录中")
            
            # 对每个目录使用 SimpleDirectoryReader
            unmatched_files: Set[Path] = set(valid_paths)
            
            for dir_path, files in dir_files_map.items():
                try:
                    dir_start_time = time.time()
                    logger.debug(f"解析目录: {dir_path} (包含 {len(files)} 个文件)")
                    
                    # 获取文件扩展名列表（用于过滤）
                    extensions = {f.suffix for f in files if f.suffix}
                    
                    # 使用 SimpleDirectoryReader 加载目录
                    reader = SimpleDirectoryReader(
                        input_dir=str(dir_path),
                        recursive=False,  # 不递归，因为我们已经有了文件列表
                        required_exts=list(extensions) if extensions else None,
                        filename_as_id=True,
                        errors='ignore'  # 忽略无法解析的文件
                    )
                    
                    dir_documents = reader.load_data()
                    logger.debug(f"SimpleDirectoryReader 返回 {len(dir_documents)} 个文档")
                    
                    # 构建规范化路径集合用于匹配
                    # 使用绝对路径和相对路径两种方式匹配
                    normalized_file_paths: Dict[Path, Path] = {}
                    file_names_to_paths: Dict[str, List[Path]] = {}
                    
                    for orig_path in files:
                        normalized_path = orig_path.resolve()
                        normalized_file_paths[normalized_path] = orig_path
                        
                        name = orig_path.name
                        if name not in file_names_to_paths:
                            file_names_to_paths[name] = []
                        file_names_to_paths[name].append(orig_path)
                    
                    # 只保留我们需要的文件
                    filtered_docs = []
                    matched_paths: Set[Path] = set()
                    
                    for doc in dir_documents:
                        doc_file_path_str = doc.metadata.get('file_path', '')
                        if not doc_file_path_str:
                            logger.debug("文档缺少 file_path 元数据，跳过")
                            continue
                        
                        # 规范化文档路径
                        doc_file_path = Path(doc_file_path_str)
                        if not doc_file_path.is_absolute():
                            # 如果是相对路径，转换为绝对路径
                            doc_file_path = (dir_path / doc_file_path).resolve()
                        else:
                            doc_file_path = doc_file_path.resolve()
                        
                        # 匹配逻辑：优先完整路径匹配，其次文件名匹配
                        matching_path = None
                        
                        # 方法1：直接路径匹配（最准确）
                        if doc_file_path in normalized_file_paths:
                            matching_path = normalized_file_paths[doc_file_path]
                            logger.debug(f"路径匹配成功: {doc_file_path} -> {matching_path}")
                        else:
                            # 方法2：文件名匹配（仅在唯一时使用）
                            file_name = doc_file_path.name
                            if file_name in file_names_to_paths:
                                candidates = file_names_to_paths[file_name]
                                if len(candidates) == 1:
                                    # 只有一个同名文件，可以安全匹配
                                    matching_path = candidates[0]
                                    logger.debug(f"文件名匹配成功: {file_name} -> {matching_path}")
                                elif len(candidates) > 1:
                                    # 多个同名文件，尝试更精确匹配
                                    # 检查相对路径是否匹配
                                    try:
                                        relative_doc_path = doc_file_path.relative_to(dir_path)
                                        for candidate in candidates:
                                            try:
                                                relative_candidate = candidate.relative_to(dir_path)
                                                if relative_doc_path == relative_candidate:
                                                    matching_path = candidate
                                                    logger.debug(f"相对路径匹配成功: {relative_doc_path}")
                                                    break
                                            except ValueError:
                                                continue
                                    except ValueError:
                                        logger.warning(f"无法确定相对路径，跳过同名文件匹配: {file_name} (有 {len(candidates)} 个候选)")
                        
                        if matching_path:
                            # 合并外部元数据
                            if metadata_map and matching_path in metadata_map:
                                doc.metadata.update(metadata_map[matching_path])
                                logger.debug(f"已合并元数据: {matching_path.name}")
                            
                            # 确保 source_type 存在
                            if 'source_type' not in doc.metadata:
                                doc.metadata['source_type'] = 'unknown'
                            
                            filtered_docs.append(doc)
                            matched_paths.add(matching_path)
                        else:
                            logger.debug(f"未找到匹配路径: {doc_file_path} (原始路径: {doc_file_path_str})")
                    
                    # 记录未匹配的文件
                    dir_unmatched = set(files) - matched_paths
                    if dir_unmatched:
                        logger.warning(f"目录 {dir_path} 中有 {len(dir_unmatched)} 个文件未匹配: {[str(p.name) for p in dir_unmatched]}")
                    unmatched_files -= matched_paths
                    
                    dir_elapsed = time.time() - dir_start_time
                    logger.info(f"目录 {dir_path.name} 解析完成: {len(filtered_docs)}/{len(files)} 个文件 (耗时: {dir_elapsed:.2f}s)")
                    
                    documents.extend(filtered_docs)
                    
                except Exception as e:
                    logger.error(f"解析目录失败 {dir_path}: {e}", exc_info=True)
                    continue
            
            # 如果有未匹配的文件，尝试逐个解析（回退方案）
            if unmatched_files:
                logger.warning(f"有 {len(unmatched_files)} 个文件未匹配，尝试逐个解析")
                for file_path in unmatched_files:
                    parsed = self._parse_single_file(file_path, metadata_map)
                    documents.extend(parsed)
            
            elapsed = time.time() - start_time
            avg_time = elapsed / len(valid_paths) if valid_paths else 0
            logger.info(f"解析完成: 成功解析 {len(documents)}/{len(valid_paths)} 个文档 (总耗时: {elapsed:.2f}s, 平均: {avg_time:.3f}s/文件)")
            
            return documents
            
        except Exception as e:
            logger.error(f"解析文件列表失败: {e}", exc_info=True)
            return []
    
    def _parse_single_file(
        self,
        file_path: Path,
        metadata_map: Optional[Dict[Path, Dict[str, Any]]] = None
    ) -> List[LlamaDocument]:
        """解析单个文件（优化性能的场景）
        
        Args:
            file_path: 文件路径
            metadata_map: 元数据映射
            
        Returns:
            文档列表
        """
        try:
            logger.debug(f"单独解析文件: {file_path}")
            
            reader = SimpleDirectoryReader(
                input_dir=str(file_path.parent),
                recursive=False,
                required_exts=[file_path.suffix] if file_path.suffix else None,
                filename_as_id=True,
                errors='ignore'
            )
            
            file_docs = reader.load_data()
            
            # 找到匹配的文件
            matching_docs = []
            file_path_resolved = file_path.resolve()
            
            for doc in file_docs:
                doc_path_str = doc.metadata.get('file_path', '')
                if not doc_path_str:
                    continue
                
                doc_path = Path(doc_path_str)
                if not doc_path.is_absolute():
                    doc_path = (file_path.parent / doc_path).resolve()
                else:
                    doc_path = doc_path.resolve()
                
                if doc_path == file_path_resolved or doc_path.name == file_path.name:
                    if metadata_map and file_path in metadata_map:
                        doc.metadata.update(metadata_map[file_path])
                    matching_docs.append(doc)
                    logger.debug(f"文件匹配成功: {file_path.name}")
                    break
            
            if not matching_docs:
                logger.warning(f"未能从 SimpleDirectoryReader 结果中找到文件: {file_path}")
            
            return matching_docs
                
        except Exception as e:
            logger.warning(f"解析文件失败 {file_path}: {e}", exc_info=True)
            return []

