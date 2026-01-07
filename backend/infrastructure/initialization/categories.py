"""
初始化分类系统：定义模块分类和初始化顺序

主要功能：
- InitCategory：初始化分类枚举（基础/核心/可选）
- 分类显示名称映射
- 分类初始化顺序定义
"""

from enum import Enum
from typing import Dict, List


class InitCategory(Enum):
    """初始化分类枚举"""
    FOUNDATION = "foundation"  # 基础层：编码、配置、日志等基础设施
    CORE = "core"              # 核心层：Embedding、Chroma、IndexManager、LLM、RAGService、ChatManager
    OPTIONAL = "optional"       # 可选层：Phoenix、LlamaDebug、RAGAS等可观测性工具


# 分类显示名称映射
CATEGORY_DISPLAY_NAMES: Dict[str, str] = {
    "foundation": "基础层",
    "core": "核心层",
    "optional": "可选层",
}

# 分类初始化顺序（按顺序执行）
CATEGORY_INIT_ORDER: List[InitCategory] = [
    InitCategory.FOUNDATION,
    InitCategory.CORE,
    InitCategory.OPTIONAL,
]

# 分类图标映射
CATEGORY_ICONS: Dict[str, str] = {
    "foundation": "🏗️",
    "core": "💼",
    "optional": "📊",
}

