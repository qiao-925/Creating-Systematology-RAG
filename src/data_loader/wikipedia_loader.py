"""
Wikipedia加载器模块
从维基百科加载文档
"""

from typing import List, Optional
from llama_index.core.schema import Document as LlamaDocument

try:
    from llama_index.readers.wikipedia import WikipediaReader
except ImportError:
    WikipediaReader = None

from src.logger import setup_logger
from src.data_loader.processor import DocumentProcessor

logger = setup_logger('data_loader')


def load_documents_from_wikipedia(
    pages: List[str],
    lang: str = "en",
    auto_suggest: bool = True,
    clean: bool = True,
    show_progress: bool = True
) -> List[LlamaDocument]:
    """从维基百科加载文档
    
    Args:
        pages: 页面标题列表
        lang: 语言代码（en=英文, zh=中文等）
        auto_suggest: 是否自动建议正确的页面标题
        clean: 是否清理文本
        show_progress: 是否显示进度
        
    Returns:
        Document对象列表
    """
    if WikipediaReader is None:
        logger.error("WikipediaReader 未安装")
        return []
    
    if not pages:
        return []
    
    try:
        # 创建Wikipedia Reader
        reader = WikipediaReader()
        
        # 加载页面
        docs = reader.load_data(
            pages=pages,
            lang=lang,
            auto_suggest=auto_suggest
        )
        
        if not docs:
            logger.warning("未找到任何维基百科页面")
            return []
        
        # 转换文档格式
        llama_docs = []
        for doc in docs:
            # 增强元数据
            llama_doc = LlamaDocument(
                text=doc.text,
                metadata={
                    'source_type': 'wikipedia',
                    'language': lang,
                    'wikipedia_url': doc.metadata.get('url', ''),
                    'title': doc.metadata.get('title', ''),
                    **doc.metadata
                },
                id_=doc.id_
            )
            llama_docs.append(llama_doc)
        
        # 清理文本
        if clean:
            llama_docs = [DocumentProcessor.enrich_metadata(doc, {}) for doc in llama_docs]
        
        logger.info(f"成功加载 {len(llama_docs)} 个维基百科页面")
        return llama_docs
        
    except Exception as e:
        logger.error(f"加载维基百科失败: {e}")
        return []


