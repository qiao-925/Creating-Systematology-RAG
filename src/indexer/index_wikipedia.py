"""
Wikipedia索引功能模块
提供预加载维基百科概念到索引的功能
"""

from typing import List
from src.logger import setup_logger

logger = setup_logger('indexer')


def preload_wikipedia_concepts(
    index_manager,
    concept_keywords: List[str],
    lang: str = "zh",
    show_progress: bool = True
) -> int:
    """预加载核心概念的维基百科内容到索引
    
    Args:
        index_manager: IndexManager实例
        concept_keywords: 概念关键词列表（维基百科页面标题）
        lang: 语言代码（zh=中文, en=英文）
        show_progress: 是否显示进度
        
    Returns:
        成功索引的页面数量
        
    Examples:
        >>> from src.indexer import IndexManager
        >>> index_manager = IndexManager()
        >>> index_manager.preload_wikipedia_concepts(
        ...     ["系统科学", "钱学森", "控制论"],
        ...     lang="zh"
        ... )
    """
    if not concept_keywords:
        logger.warning("⚠️  概念关键词列表为空")
        return 0
    
    try:
        from src.data_loader import load_documents_from_wikipedia
        
        logger.info(f"📖 预加载 {len(concept_keywords)} 个维基百科概念...")
        
        # 加载维基百科页面
        wiki_docs = load_documents_from_wikipedia(
            pages=concept_keywords,
            lang=lang,
            auto_suggest=True,
            clean=True,
            show_progress=show_progress
        )
        
        if not wiki_docs:
            logger.warning("⚠️  未找到任何维基百科内容")
            return 0
        
        # 构建索引
        index_manager.build_index(wiki_docs, show_progress=show_progress)
        
        logger.info(f"✅ 已索引 {len(wiki_docs)} 个维基百科页面")
        
        return len(wiki_docs)
        
    except ImportError as e:
        logger.error(f"❌ 导入Wikipedia加载器失败: {e}")
        logger.warning("⚠️  请确保已安装 llama-index-readers-wikipedia")
        return 0
    except Exception as e:
        logger.error(f"❌ 预加载维基百科概念失败: {e}", exc_info=True)
        return 0

