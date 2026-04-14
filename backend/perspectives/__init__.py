"""
CLDFlow Perspective Generation System

基于 DDC 分类法的动态视角生成模块。
"""

from .generator import PerspectiveGenerator
from .classifier import QuestionClassifier
from .registry import TemplateRegistry
from .evaluator import TemplateEvaluator

__all__ = [
    "PerspectiveGenerator",
    "QuestionClassifier", 
    "TemplateRegistry",
    "TemplateEvaluator",
]
