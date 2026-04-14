"""
Tests for TemplateEvaluator
"""

import pytest
from backend.perspectives.evaluator import (
    TemplateEvaluator, 
    EvaluationReport,
    CounterfactualResult,
    AdvancementResult
)


class TestTemplateEvaluator:
    """测试模板评估器"""
    
    @pytest.fixture
    def evaluator(self):
        """创建测试用的评估器"""
        return TemplateEvaluator()
    
    def test_evaluate_returns_report(self, evaluator):
        """测试评估返回报告"""
        report = evaluator.evaluate("ddc_330_economic")
        
        assert isinstance(report, EvaluationReport)
        assert report.template_id == "ddc_330_economic"
    
    def test_counterfactual_evaluation(self, evaluator):
        """测试反事实评估"""
        result = evaluator.evaluate_counterfactual("ddc_330_economic")
        
        assert isinstance(result, CounterfactualResult)
        # 注意：当前是占位实现，实际值可能不准确
        assert result.test_count >= 0
    
    def test_advancement_evaluation(self, evaluator):
        """测试 Action Advancement 评估"""
        result = evaluator.evaluate_advancement("ddc_330_economic")
        
        assert isinstance(result, AdvancementResult)
        assert 0.0 <= result.advancement_rate <= 1.0
        assert result.test_count >= 0
    
    def test_evaluation_thresholds(self, evaluator):
        """测试评估阈值"""
        # 阈值常量
        assert evaluator.CF_MEAN_THRESHOLD == 10.0
        assert evaluator.CF_MIN_THRESHOLD == 0.0
        assert evaluator.AA_RATE_THRESHOLD == 0.7
    
    def test_get_evaluation_summary(self, evaluator):
        """测试获取评估摘要"""
        report = evaluator.evaluate("ddc_330_economic")
        summary = evaluator.get_evaluation_summary(report)
        
        assert "template_id" in summary
        assert "counterfactual" in summary
        assert "action_advancement" in summary
        assert "overall_pass" in summary
        assert "can_deploy" in summary
    
    def test_overall_pass_logic(self, evaluator):
        """测试整体通过逻辑"""
        # 只有当两项评估都通过时才整体通过
        # 注意：占位实现的结果可能不符合此逻辑
        report = evaluator.evaluate("ddc_330_economic")
        
        # overall_pass 应该是两项评估 passed 的 AND
        expected_pass = (report.counterfactual.passed and 
                        report.action_advancement.passed)
        assert report.overall_pass == expected_pass
        assert report.can_deploy == report.overall_pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
