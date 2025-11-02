"""
查询引擎工具函数模块
格式化引用来源等辅助函数
"""

from typing import List


def format_sources(sources: List[dict]) -> str:
    """格式化引用来源为可读文本
    
    Args:
        sources: 引用来源列表
        
    Returns:
        格式化的文本
    """
    if not sources:
        return "（无引用来源）"
    
    formatted = "\n\n📚 引用来源：\n"
    for source in sources:
        formatted += f"\n[{source['index']}] "
        
        # 添加文档信息
        metadata = source['metadata']
        if 'title' in metadata:
            formatted += f"{metadata['title']}"
        elif 'file_name' in metadata:
            formatted += f"{metadata['file_name']}"
        elif 'url' in metadata:
            formatted += f"{metadata['url']}"
        
        # 添加相似度分数
        if source['score'] is not None:
            formatted += f" (相似度: {source['score']:.2f})"
        
        # 完整显示文本内容
        formatted += f"\n   {source['text']}"
    
    return formatted


def create_query_engine(index_manager, with_citation: bool = True):
    """创建查询引擎（便捷函数）
    
    Args:
        index_manager: 索引管理器
        with_citation: 是否使用引用溯源
        
    Returns:
        QueryEngine或SimpleQueryEngine对象
    """
    if with_citation:
        from src.query.engine import QueryEngine
        return QueryEngine(index_manager)
    else:
        from src.query.simple import SimpleQueryEngine
        return SimpleQueryEngine(index_manager)

