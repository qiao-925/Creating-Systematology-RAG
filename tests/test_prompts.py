"""
提示工程模块测试
"""

import pytest
from unittest.mock import Mock

from src.business.prompts import (
    PromptTemplateManager,
    FewShotTemplate,
    CoTTemplate,
    AutoCoTTemplate,
)
from src.business.prompts.few_shot import Example
from src.business.protocols import PipelineContext


class TestPromptTemplateManager:
    """测试PromptTemplateManager"""
    
    def test_manager_creation(self):
        """测试创建管理器"""
        manager = PromptTemplateManager()
        assert len(manager) > 0  # 有默认模板
        assert "basic_rag" in manager
    
    def test_register_and_get_template(self):
        """测试注册和获取模板"""
        manager = PromptTemplateManager()
        
        manager.register_template("test", "问题：{question}")
        assert "test" in manager
        assert manager.get_template("test") == "问题：{question}"
    
    def test_render_template(self):
        """测试渲染模板"""
        manager = PromptTemplateManager()
        manager.register_template("test", "问题：{question}，答案：{answer}")
        
        rendered = manager.render("test", question="测试", answer="成功")
        assert "测试" in rendered
        assert "成功" in rendered
    
    def test_render_missing_template(self):
        """测试渲染不存在的模板"""
        manager = PromptTemplateManager()
        
        with pytest.raises(KeyError):
            manager.render("nonexistent", question="test")
    
    def test_list_templates(self):
        """测试列出模板"""
        manager = PromptTemplateManager()
        templates = manager.list_templates()
        
        assert isinstance(templates, list)
        assert len(templates) > 0


class TestFewShotTemplate:
    """测试FewShotTemplate"""
    
    def test_example_creation(self):
        """测试创建示例"""
        example = Example(
            question="什么是AI？",
            context="人工智能是...",
            answer="人工智能是模拟人类智能的技术"
        )
        
        assert example.question == "什么是AI？"
        prompt = example.to_prompt()
        assert "示例" in prompt
        assert "什么是AI" in prompt
    
    def test_few_shot_creation(self):
        """测试创建Few-shot模板"""
        examples = [
            Example("Q1", "C1", "A1"),
            Example("Q2", "C2", "A2"),
        ]
        
        few_shot = FewShotTemplate(examples=examples, num_examples=2)
        assert len(few_shot.examples) == 2
        assert few_shot.num_examples == 2
    
    def test_few_shot_build_prompt(self):
        """测试构建提示"""
        few_shot = FewShotTemplate(num_examples=1)
        
        # Mock文档
        docs = [Mock(text="测试文档内容")]
        
        prompt = few_shot.build_prompt("测试问题", docs)
        
        assert "示例" in prompt
        assert "测试问题" in prompt
        assert "测试文档内容" in prompt
    
    def test_few_shot_execute(self):
        """测试执行Few-shot"""
        few_shot = FewShotTemplate()
        
        context = PipelineContext(query="测试问题")
        context.retrieved_docs = [Mock(text="文档1")]
        
        context = few_shot.execute(context)
        
        assert context.prompt is not None
        assert len(context.prompt) > 0
        assert context.get_metadata('prompt_type') == 'few_shot'


class TestCoTTemplate:
    """测试CoTTemplate"""
    
    def test_cot_creation(self):
        """测试创建CoT模板"""
        cot = CoTTemplate(reasoning_style="step_by_step")
        assert cot.reasoning_style == "step_by_step"
    
    def test_cot_build_prompt(self):
        """测试构建CoT提示"""
        cot = CoTTemplate(reasoning_style="step_by_step")
        
        docs = [Mock(text="参考文档内容")]
        prompt = cot.build_prompt("测试问题", docs)
        
        assert "一步步思考" in prompt
        assert "测试问题" in prompt
    
    def test_cot_execute(self):
        """测试执行CoT"""
        cot = CoTTemplate()
        
        context = PipelineContext(query="复杂问题")
        context.retrieved_docs = [Mock(text="文档")]
        
        context = cot.execute(context)
        
        assert context.prompt is not None
        assert context.get_metadata('prompt_type') == 'cot'
    
    def test_cot_different_styles(self):
        """测试不同推理风格"""
        styles = ["step_by_step", "analytical"]
        
        for style in styles:
            cot = CoTTemplate(reasoning_style=style)
            docs = [Mock(text="文档")]
            prompt = cot.build_prompt("问题", docs)
            assert len(prompt) > 0


class TestAutoCoTTemplate:
    """测试AutoCoTTemplate"""
    
    def test_auto_cot_creation(self):
        """测试创建Auto-CoT模板"""
        auto_cot = AutoCoTTemplate(max_steps=5)
        assert auto_cot.max_steps == 5
        assert auto_cot.auto_generate_steps is True
    
    def test_analyze_question_type(self):
        """测试问题类型分析"""
        auto_cot = AutoCoTTemplate()
        
        assert auto_cot._analyze_question_type("什么是系统思维？") == "definition"
        assert auto_cot._analyze_question_type("为什么需要系统思维？") == "explanation"
        assert auto_cot._analyze_question_type("如何应用系统思维？") == "application"
        assert auto_cot._analyze_question_type("分析系统思维的特点") == "analysis"
    
    def test_generate_reasoning_steps(self):
        """测试生成推理步骤"""
        auto_cot = AutoCoTTemplate()
        
        steps = auto_cot._generate_reasoning_steps("什么是AI？", "definition")
        assert isinstance(steps, list)
        assert len(steps) > 0
        assert all(isinstance(step, str) for step in steps)
    
    def test_auto_cot_build_prompt(self):
        """测试构建Auto-CoT提示"""
        auto_cot = AutoCoTTemplate(max_steps=3)
        
        docs = [Mock(text="文档内容")]
        prompt = auto_cot.build_prompt("如何解决问题？", docs)
        
        assert "推理框架" in prompt
        assert "如何解决问题" in prompt
    
    def test_auto_cot_execute(self):
        """测试执行Auto-CoT"""
        auto_cot = AutoCoTTemplate()
        
        context = PipelineContext(query="复杂分析问题")
        context.retrieved_docs = [Mock(text="文档")]
        
        context = auto_cot.execute(context)
        
        assert context.prompt is not None
        assert context.get_metadata('prompt_type') == 'auto_cot'
        assert 'question_type' in context.metadata


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
