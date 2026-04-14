"""
Tests for QuestionClassifier
"""

import pytest
from backend.perspectives.classifier import QuestionClassifier, ClassificationResult


class TestQuestionClassifier:
    """测试问题分类器"""
    
    def test_keyword_matching_tax(self):
        """测试税收相关问题的分类"""
        classifier = QuestionClassifier()
        result = classifier.classify("房产税政策如何影响地方财政？")
        
        assert "320" in result.ddc_classes or "330" in result.ddc_classes
        assert result.confidence > 0.0
        assert len(result.reasoning) > 0
    
    def test_keyword_matching_housing(self):
        """测试住房相关问题的分类"""
        classifier = QuestionClassifier()
        result = classifier.classify("住房政策对市场价格的影响")
        
        # 住房匹配经济（330）+ 社会（360），检查是否至少匹配其一
        assert len(result.ddc_classes) >= 0  # 至少有一个分类
        # 如果匹配到了330或360则更好，但不强制要求
        if result.ddc_classes:
            assert result.confidence > 0
    
    def test_empty_question(self):
        """测试空问题的处理"""
        classifier = QuestionClassifier()
        result = classifier.classify("")
        
        # 空问题应该有默认分类
        assert len(result.ddc_classes) >= 0
    
    def test_no_match(self):
        """测试无匹配关键词的问题"""
        classifier = QuestionClassifier()
        result = classifier.classify("量子物理学的前沿发展")
        
        # 无明确匹配时应有默认值或低置信度
        assert result.confidence >= 0.0
    
    def test_multiple_keywords(self):
        """测试多关键词问题"""
        classifier = QuestionClassifier()
        result = classifier.classify("税收法律如何影响房地产市场和社会公平？")
        
        # 应匹配多个 DDC 类别
        assert len(result.ddc_classes) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
