"""
网页加载器模块
从URL列表加载网页文档
"""

from typing import List

from llama_index.core.schema import Document as LlamaDocument

try:
    from llama_index.readers.web import SimpleWebPageReader
except ImportError:
    SimpleWebPageReader = None

from src.data_source import WebSource
from src.data_loader.processor import DocumentProcessor, safe_print
from src.data_loader.source_loader import load_documents_from_source, NEW_ARCHITECTURE_AVAILABLE
from src.logger import setup_logger

logger = setup_logger('data_loader')


def load_documents_from_urls(urls: List[str], 
                            clean: bool = True) -> List[LlamaDocument]:
    """从URL列表加载文档（使用官方 SimpleWebPageReader）
    
    Args:
        urls: URL列表
        clean: 是否清理文本
        
    Returns:
        Document对象列表
    """
    if SimpleWebPageReader is None:
        safe_print("❌ 缺少依赖：llama-index-readers-web")
        safe_print("   安装：pip install llama-index-readers-web")
        logger.error("SimpleWebPageReader 未安装")
        return []
    
    # 使用新架构（如果可用）
    if NEW_ARCHITECTURE_AVAILABLE:
        try:
            source = WebSource(urls=urls)
            documents = load_documents_from_source(source, clean=clean, show_progress=True)
            
            # 清理临时文件
            source.cleanup()
            
            return documents
        except Exception as e:
            logger.warning(f"新架构加载失败，回退到旧实现: {e}")
    
    # 回退到旧实现
    if not urls:
        safe_print("⚠️  URL 列表为空")
        return []
    
    try:
        logger.info(f"开始加载 {len(urls)} 个网页")
        
        # 使用 SimpleWebPageReader 加载网页
        reader = SimpleWebPageReader(html_to_text=True)
        documents = reader.load_data(urls)
        
        if not documents:
            safe_print("⚠️  未成功加载任何网页")
            logger.warning("没有成功加载任何网页")
            return []
        
        # 增强元数据
        for i, doc in enumerate(documents):
            url = urls[i] if i < len(urls) else "unknown"
            
            doc.metadata.update({
                "source_type": "web",
                "url": url,
            })
            
            safe_print(f"✅ 已加载: {url}")
        
        safe_print(f"\n🌐 总共加载了 {len(documents)} 个网页")
        logger.info(f"成功加载 {len(documents)} 个网页")
        
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
        safe_print(f"❌ 加载网页失败: {e}")
        logger.error(f"加载网页失败: {e}")
        return []

