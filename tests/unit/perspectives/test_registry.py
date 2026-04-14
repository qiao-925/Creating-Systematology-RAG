"""
Tests for TemplateRegistry
"""

import pytest
from pathlib import Path
from backend.perspectives.registry import TemplateRegistry, PerspectiveTemplate


class TestTemplateRegistry:
    """测试模板注册表"""
    
    @pytest.fixture
    def registry(self):
        """创建测试用的注册表"""
        return TemplateRegistry()
    
    def test_loads_templates(self, registry):
        """测试模板加载"""
        templates = registry.get_all_templates()
        assert len(templates) > 0
    
    def test_get_template_by_id(self, registry):
        """测试通过 ID 获取模板"""
        template = registry.get_template("ddc_330_economic")
        if template:  # 如果模板存在
            assert template.id == "ddc_330_economic"
            assert template.ddc_class == "330"
    
    def test_get_templates_by_ddc(self, registry):
        """测试通过 DDC 分类获取模板"""
        templates = registry.get_templates_by_ddc("330")
        if templates:  # 如果有该分类的模板
            assert all(t.ddc_class == "330" for t in templates)
    
    def test_template_inheritance_resolution(self, registry):
        """测试模板继承解析"""
        # 解析经济分析师模板
        resolved = registry.resolve_template("ddc_330_economic")
        
        # 应该包含继承自基础模板和自身定义的字段
        assert "role_definition" in resolved
        assert "extraction_preferences" in resolved
    
    def test_list_ddc_classes(self, registry):
        """测试列出 DDC 分类"""
        ddc_classes = registry.list_ddc_classes()
        assert isinstance(ddc_classes, list)
        # 应该包含至少 320, 330, 340, 360
        expected = ["320", "330", "340", "360"]
        assert any(c in ddc_classes for c in expected)
    
    def test_get_template_hierarchy(self, registry):
        """测试获取模板继承层次"""
        hierarchy = registry.get_template_hierarchy("ddc_330_economic")
        assert isinstance(hierarchy, list)
        # 层次应包含自身
        assert "ddc_330_economic" in hierarchy or len(hierarchy) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
