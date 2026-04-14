"""
Question to DDC Classification Module

基于关键词和 LLM 辅助的问题分类器。
"""

from typing import List, Dict
from dataclasses import dataclass


@dataclass
class ClassificationResult:
    """分类结果"""
    ddc_classes: List[str]           # DDC 分类列表，如 ["320", "330"]
    confidence: float                  # 分类置信度
    reasoning: str                     # 分类理由


class QuestionClassifier:
    """
    问题分类器：将用户问题映射到 DDC 分类
    
    策略：
    1. 关键词匹配（快速、低成本）
    2. LLM 辅助分类（复杂问题）
    """
    
    # 关键词到 DDC 的映射
    KEYWORD_TO_DDC: Dict[str, List[str]] = {
        # 政治/政策相关
        "tax": ["320", "330"],              # 政治 + 经济
        "legislation": ["320", "340"],      # 政治 + 法律
        "government": ["320", "350"],       # 政治 + 公共管理
        "policy": ["320"],
        "regulation": ["320", "340"],
        "bureaucracy": ["350"],
        
        # 经济相关
        "housing": ["330", "360"],          # 经济 + 社会
        "market": ["330"],
        "price": ["330"],
        "inflation": ["330"],
        "supply": ["330"],
        "demand": ["330"],
        "budget": ["330", "350"],           # 经济 + 公共财政
        "cost": ["330"],
        "revenue": ["330"],
        "labor": ["330", "360"],            # 经济 + 社会
        
        # 法律相关
        "law": ["340"],
        "legal": ["340"],
        "compliance": ["340"],
        "litigation": ["340"],
        "enforcement": ["340"],
        
        # 社会相关
        "education": ["360", "370"],        # 社会 + 教育
        "healthcare": ["360", "610"],       # 社会 + 医学
        "poverty": ["360"],
        "inequality": ["360"],
        "community": ["360"],
        "equity": ["360"],
        "demographic": ["360"],
        "immigration": ["325", "360"],       # 移民 + 社会
        "discrimination": ["360"],
    }
    
    def __init__(self, use_llm: bool = False):
        self.use_llm = use_llm
    
    def classify(self, question: str) -> ClassificationResult:
        """
        分类问题到 DDC 类别
        
        Args:
            question: 用户输入的研究问题
            
        Returns:
            ClassificationResult 包含 DDC 分类列表
        """
        # 1. 关键词匹配
        ddc_scores = self._keyword_match(question.lower())
        
        # 2. 如果启用 LLM，进行辅助分类
        if self.use_llm and len(ddc_scores) < 2:
            ddc_scores = self._llm_classify(question, ddc_scores)
        
        # 3. 排序并选择前 3 个
        sorted_ddc = sorted(ddc_scores.items(), key=lambda x: x[1], reverse=True)
        selected = [ddc for ddc, score in sorted_ddc[:3] if score > 0.5]
        
        return ClassificationResult(
            ddc_classes=selected if selected else ["320"],  # 默认政治
            confidence=sorted_ddc[0][1] if sorted_ddc else 0.5,
            reasoning=self._generate_reasoning(selected, question)
        )
    
    def _keyword_match(self, question: str) -> Dict[str, float]:
        """基于关键词匹配计算 DDC 得分"""
        scores: Dict[str, float] = {}
        
        for keyword, ddc_list in self.KEYWORD_TO_DDC.items():
            if keyword in question:
                for ddc in ddc_list:
                    scores[ddc] = scores.get(ddc, 0) + 1.0
        
        # 归一化
        if scores:
            max_score = max(scores.values())
            scores = {k: min(v / max_score, 1.0) for k, v in scores.items()}
        
        return scores
    
    def _llm_classify(self, question: str, initial_scores: Dict[str, float]) -> Dict[str, float]:
        """LLM 辅助分类（预留接口）"""
        # Phase 2 实现
        return initial_scores
    
    def _generate_reasoning(self, ddc_classes: List[str], question: str) -> str:
        """生成分类理由"""
        if not ddc_classes:
            return "未匹配到明确分类，默认使用政治视角"
        
        ddc_names = {
            "320": "政治学/政策分析",
            "330": "经济学",
            "340": "法律/监管",
            "350": "公共管理",
            "360": "社会学/社会问题",
        }
        
        class_names = [ddc_names.get(c, c) for c in ddc_classes]
        return f"基于关键词匹配，问题涉及: {', '.join(class_names)}"
    
    def get_domain_keywords(self, ddc_class: str) -> List[str]:
        """获取指定 DDC 类的关键词"""
        keywords = []
        for kw, ddc_list in self.KEYWORD_TO_DDC.items():
            if ddc_class in ddc_list:
                keywords.append(kw)
        return keywords
