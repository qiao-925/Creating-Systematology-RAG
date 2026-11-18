"""
RAG引擎格式化模块 - Prompt模板加载器

主要功能：
- get_template()：获取模板（从文件加载）
- reload_templates()：运行时重新加载模板

模板文件位置：prompts/rag/chat.txt
"""

from pathlib import Path
from typing import Optional

from backend.infrastructure.logger import get_logger

logger = get_logger('rag_engine.templates')

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent

# 模板文件路径
CHAT_TEMPLATE_PATH = PROJECT_ROOT / "prompts" / "rag" / "chat.txt"

# 模板缓存
_template_cache: Optional[str] = None

# 默认模板（文件加载失败时的后备）
_DEFAULT_TEMPLATE = """你是一位系统科学领域的资深学者，兼具严谨的学术素养和活泼的表达风格。

【知识库参考】
{context_str}

【核心原则】
1. **客观为本**：基于知识库内容，坦诚说明边界
2. **启发优先**：挖掘"为什么"，点燃思考火花
3. **批判视角**：指出理论局限和争议点

请用中文回答。"""


def get_template(template_type: str = 'chat') -> str:
    """获取模板
    
    优先从文件加载，失败时使用默认模板。
    
    Args:
        template_type: 模板类型（目前仅支持 'chat'）
            
    Returns:
        str: 模板内容
    """
    global _template_cache
    
    # 检查缓存
    if _template_cache is not None:
        return _template_cache
    
    # 尝试从文件加载
    try:
        if CHAT_TEMPLATE_PATH.exists():
            content = CHAT_TEMPLATE_PATH.read_text(encoding='utf-8')
            _template_cache = content
            logger.debug("模板加载成功", path=str(CHAT_TEMPLATE_PATH))
            return content
        else:
            logger.warning(f"模板文件不存在: {CHAT_TEMPLATE_PATH}")
    except Exception as e:
        logger.error(f"模板加载失败", error=str(e))
    
    # 使用默认模板
    logger.info("使用默认模板")
    return _DEFAULT_TEMPLATE


def reload_templates() -> None:
    """重新加载模板（清除缓存）
    
    用于运行时热更新模板，无需重启应用。
    """
    global _template_cache
    _template_cache = None
    logger.info("模板缓存已清除，下次访问将重新加载")
