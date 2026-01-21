"""
Prompt 加载器模块：从文件加载 Prompt 模板

主要功能：
- load_planning_prompt()：加载规划 Agent 的 Prompt
- 支持从文件加载，提供默认模板作为后备
- 支持运行时重新加载
"""

from pathlib import Path
from typing import Optional

from backend.infrastructure.logger import get_logger

logger = get_logger('rag_engine.agentic.prompts')

# 默认 Prompt 模板（作为后备）
DEFAULT_PLANNING_PROMPT = """你是一个智能检索规划助手。你的任务是：

1. 分析用户查询的特点和需求
2. 选择合适的检索工具：
   - vector_search: 适合概念理解、语义相似查询。使用向量相似度搜索，能够理解查询的语义含义，找到语义上最相关的文档片段。
   - hybrid_search: 适合需要平衡精度和召回的查询。结合向量检索和BM25关键词检索，既考虑语义相似度，也考虑关键词匹配，能够提供更全面的检索结果。
   - multi_search: 适合复杂查询、需要全面检索。同时使用多种检索策略（向量、BM25、Grep等），合并结果，能够提供最全面的检索覆盖。
3. 调用选定的工具获取答案

选择指导：
- 如果查询是概念性的、需要理解语义的，选择 vector_search
- 如果查询需要同时考虑语义和关键词匹配，选择 hybrid_search
- 如果查询很复杂、需要全面检索，选择 multi_search

请根据查询特点，智能选择最合适的工具。
"""


def load_planning_prompt(template_path: Optional[Path] = None) -> str:
    """加载规划 Agent 的 Prompt 模板
    
    Args:
        template_path: Prompt 模板文件路径（可选）
        
    Returns:
        Prompt 模板字符串
    """
    if template_path is None:
        # 使用集中管理的模板路径：prompts/agentic/planning.txt
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent.parent.parent.parent
        template_path = project_root / "prompts" / "agentic" / "planning.txt"
        
        # 向后兼容：如果新路径不存在，尝试旧路径
        if not template_path.exists():
            template_path = current_file.parent / "templates" / "planning.txt"
    
    # 尝试从文件加载
    if template_path.exists():
        try:
            prompt = template_path.read_text(encoding='utf-8')
            logger.info("从文件加载 Prompt 模板", path=str(template_path))
            return prompt.strip()
        except Exception as e:
            logger.warning(
                "加载 Prompt 模板文件失败，使用默认模板",
                path=str(template_path),
                error=str(e)
            )
            return DEFAULT_PLANNING_PROMPT
    else:
        logger.info(
            "Prompt 模板文件不存在，使用默认模板",
            path=str(template_path)
        )
        return DEFAULT_PLANNING_PROMPT


def reload_planning_prompt(template_path: Optional[Path] = None) -> str:
    """重新加载规划 Agent 的 Prompt 模板（运行时更新）
    
    Args:
        template_path: Prompt 模板文件路径（可选）
        
    Returns:
        Prompt 模板字符串
    """
    logger.info("重新加载 Prompt 模板", path=str(template_path) if template_path else "default")
    return load_planning_prompt(template_path)

