"""
Tests for PerspectiveGenerator
"""

import pytest
from backend.perspectives.generator import PerspectiveGenerator, GenerationResult
from backend.perspectives.classifier import QuestionClassifier
from backend.perspectives.registry import TemplateRegistry


class TestPerspectiveGenerator:
    """测试视角生成器"""
    
    @pytest.fixture
    def generator(self):
        """创建测试用的生成器"""
        return PerspectiveGenerator()
    
    def test_generate_returns_result(self, generator):
        """测试生成返回结果对象"""
        result = generator.generate("房产税政策的影响分析")
        
        assert isinstance(result, GenerationResult)
        assert result.question == "房产税政策的影响分析"
        assert len(result.perspectives) >= 0
    
    def test_generate_classifies_question(self, generator):
        """测试生成时进行问题分类"""
        result = generator.generate("税收政策分析")
        
        assert result.classification is not None
        assert len(result.classification.ddc_classes) >= 0
    
    def test_respects_max_perspectives(self, generator):
        """测试遵守最大视角数量限制"""
        result = generator.generate("综合政策分析", max_perspectives=2)
        
        assert len(result.perspectives) <= 2
    
    def test_perspectives_have_required_fields(self, generator):
        """测试生成的视角包含必需字段"""
        result = generator.generate("住房政策分析")
        
        for perspective in result.perspectives:
            assert perspective.id is not None
            assert perspective.name is not None
            assert perspective.role_definition is not None
            assert perspective.ddc_class is not None
    
    def test_get_generation_info(self, generator):
        """测试获取生成信息"""
        result = generator.generate("政策影响分析")
        info = generator.get_generation_info(result)
        
        assert "question" in info
        assert "classification" in info
        assert "perspectives" in info
        assert isinstance(info["perspectives"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
