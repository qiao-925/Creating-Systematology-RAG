"""
Perspective Generator Module

动态视角生成器主逻辑。
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from .classifier import QuestionClassifier, ClassificationResult
from .registry import TemplateRegistry, PerspectiveTemplate


@dataclass
class Perspective:
    """生成的视角定义"""
    id: str
    name: str
    role_definition: Dict
    extraction_preferences: Dict
    search_strategy: Dict
    ddc_class: str
    template_source: str  # 基于哪个模板


@dataclass
class GenerationResult:
    """生成结果"""
    perspectives: List[Perspective]
    classification: ClassificationResult
    question: str


class PerspectiveGenerator:
    """
    视角生成器
    
    核心流程：
    1. 问题分类 → DDC
    2. DDC → 模板选择
    3. 模板细化 → 具体视角
    """
    
    def __init__(
        self,
        classifier: Optional[QuestionClassifier] = None,
        registry: Optional[TemplateRegistry] = None
    ):
        self.classifier = classifier or QuestionClassifier()
        self.registry = registry or TemplateRegistry()
    
    def generate(self, question: str, max_perspectives: int = 4) -> GenerationResult:
        """
        根据问题生成视角列表
        
        Args:
            question: 研究问题
            max_perspectives: 最大视角数量（硬限制）
            
        Returns:
            GenerationResult 包含视角列表和分类信息
        """
        # 1. 问题分类
        classification = self.classifier.classify(question)
        
        # 2. 根据 DDC 选择模板
        templates = self._select_templates(classification.ddc_classes)
        
        # 3. 限制数量
        templates = templates[:max_perspectives]
        
        # 4. 生成具体视角
        perspectives = []
        for template in templates:
            perspective = self._refine_template(template, question)
            perspectives.append(perspective)
        
        return GenerationResult(
            perspectives=perspectives,
            classification=classification,
            question=question
        )
    
    def _select_templates(self, ddc_classes: List[str]) -> List[PerspectiveTemplate]:
        """根据 DDC 分类选择模板"""
        selected = []
        seen_ids = set()
        
        for ddc in ddc_classes:
            templates = self.registry.get_templates_by_ddc(ddc)
            for template in templates:
                if template.id not in seen_ids:
                    selected.append(template)
                    seen_ids.add(template.id)
        
        return selected
    
    def _refine_template(self, template: PerspectiveTemplate, question: str) -> Perspective:
        """
        细化模板，生成具体视角
        
        策略：解析继承链，合并所有字段
        """
        # 解析完整模板（处理继承）
        full_data = self.registry.resolve_template(template.id)
        
        # 提取关键字段
        role_def = full_data.get('role_definition', {})
        extraction = full_data.get('extraction_preferences', {})
        search = full_data.get('search_strategy', {})
        
        return Perspective(
            id=f"{template.id}_{hash(question) % 10000}",  # 实例 ID
            name=role_def.get('title', template.name),
            role_definition=role_def,
            extraction_preferences=extraction,
            search_strategy=search,
            ddc_class=template.ddc_class,
            template_source=template.id
        )
    
    def get_generation_info(self, result: GenerationResult) -> Dict:
        """获取生成信息的摘要"""
        return {
            "question": result.question,
            "classification": {
                "ddc_classes": result.classification.ddc_classes,
                "confidence": result.classification.confidence,
                "reasoning": result.classification.reasoning
            },
            "perspectives": [
                {
                    "id": p.id,
                    "name": p.name,
                    "ddc_class": p.ddc_class,
                    "template": p.template_source
                }
                for p in result.perspectives
            ]
        }
