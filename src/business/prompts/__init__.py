"""
提示工程模块

提供Few-shot、CoT、AutoCoT等提示工程技术
"""

from .template_manager import PromptTemplateManager
from .few_shot import FewShotTemplate
from .cot import CoTTemplate
from .auto_cot import AutoCoTTemplate

__all__ = [
    'PromptTemplateManager',
    'FewShotTemplate',
    'CoTTemplate',
    'AutoCoTTemplate',
]
