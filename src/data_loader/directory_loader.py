"""
目录加载器模块
从本地目录加载文档
"""

from pathlib import Path
from typing import List, Optional

from llama_index.core import SimpleDirectoryReader
from llama_index.core.schema import Document as LlamaDocument

from src.data_source import LocalFileSource
from src.data_loader.processor import DocumentProcessor, safe_print
from src.data_loader.source_loader import load_documents_from_source, NEW_ARCHITECTURE_AVAILABLE
from src.logger import setup_logger

logger = setup_logger('data_loader')


def load_documents_from_directory(directory_path: str | Path, 
                                 recursive: bool = True,
                                 clean: bool = True,
                                 required_exts: Optional[List[str]] = None) -> List[LlamaDocument]:
    """从目录加载所有文档（使用官方 SimpleDirectoryReader）
    
    Args:
        directory_path: 目录路径
        recursive: 是否递归加载
        clean: 是否清理文本
        required_exts: 文件扩展名列表（默认：[".md", ".markdown"]）
        
    Returns:
        Document对象列表
    """
    # 使用新架构（如果可用）
    if NEW_ARCHITECTURE_AVAILABLE:
        try:
            source = LocalFileSource(
                directory_path=directory_path,
                recursive=recursive,
                required_exts=required_exts
            )
            documents = load_documents_from_source(source, clean=clean, show_progress=True)
            
            # 为 Markdown 文件提取标题（保持原有行为）
            for doc in documents:
                file_name = doc.metadata.get('file_name', '')
                if any(file_name.endswith(ext) for ext in ['.md', '.markdown']):
                    title = DocumentProcessor.extract_title_from_markdown(doc.text)
                    if not title:
                        title = Path(file_name).stem if file_name else "未命名"
                    doc.metadata.update({
                        "title": title,
                        "source_type": doc.metadata.get("source_type", "markdown"),
                    })
            
            return documents
        except Exception as e:
            logger.warning(f"新架构加载失败，回退到旧实现: {e}")
    
    # 回退到旧实现
    directory_path = Path(directory_path)
    required_exts = required_exts or [".md", ".markdown"]
    
    # 验证目录
    if not directory_path.exists() or not directory_path.is_dir():
        safe_print(f"❌ 目录不存在或不是有效目录: {directory_path}")
        logger.error(f"目录不存在: {directory_path}")
        return []
    
    try:
        logger.info(f"开始加载目录: {directory_path}, 递归: {recursive}")
        
        # 使用 SimpleDirectoryReader 加载文档
        reader = SimpleDirectoryReader(
            input_dir=str(directory_path),
            recursive=recursive,
            required_exts=required_exts,
            filename_as_id=True,
            errors='ignore',
        )
        
        documents = reader.load_data()
        
        if not documents:
            safe_print(f"⚠️  未找到任何文档（支持格式：{', '.join(required_exts)}）")
            logger.warning(f"目录为空: {directory_path}")
            return []
        
        # 增强元数据
        for doc in documents:
            file_path = doc.metadata.get('file_path', '')
            file_name = doc.metadata.get('file_name', '')
            
            # 为 Markdown 文件提取标题
            if any(file_name.endswith(ext) for ext in ['.md', '.markdown']):
                title = DocumentProcessor.extract_title_from_markdown(doc.text)
                if not title:
                    title = Path(file_name).stem if file_name else "未命名"
                
                doc.metadata.update({
                    "title": title,
                    "source_type": "markdown",
                })
            
            # 确保基础元数据存在
            if not doc.metadata.get('file_path'):
                doc.metadata['file_path'] = file_path
            if not doc.metadata.get('file_name'):
                doc.metadata['file_name'] = file_name
            
            safe_print(f"✅ 已加载: {file_name}")
        
        safe_print(f"\n📚 总共加载了 {len(documents)} 个文档")
        logger.info(f"成功加载 {len(documents)} 个文档")
        
        # 可选的文本清理
        if clean:
            processor = DocumentProcessor()
            cleaned_documents = []
            for doc in documents:
                cleaned_text = processor.clean_text(doc.text)
                cleaned_doc = LlamaDocument(
                    text=cleaned_text,
                    metadata=doc.metadata,
                    id_=doc.id_
                )
                cleaned_documents.append(cleaned_doc)
            return cleaned_documents
        
        return documents
        
    except Exception as e:
        safe_print(f"❌ 加载目录失败: {e}")
        logger.error(f"加载目录失败 {directory_path}: {e}")
        return []

