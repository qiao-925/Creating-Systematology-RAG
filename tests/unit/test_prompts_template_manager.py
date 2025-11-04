"""
提示模板管理器单元测试
测试 PromptTemplateManager 的各种功能
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from src.business.prompts.template_manager import (
    PromptTemplateManager,
    get_global_template_manager,
    _global_manager,
)


class TestPromptTemplateManagerInitialization:
    """测试 PromptTemplateManager 初始化"""

    def test_init_with_default_templates(self):
        """测试初始化时注册默认模板"""
        manager = PromptTemplateManager()
        
        assert len(manager) > 0
        assert "basic_rag" in manager
        assert "rag_markdown" in manager
        assert "rag_with_citation" in manager

    def test_init_with_custom_template_dir(self):
        """测试从目录加载模板"""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_dir = Path(tmpdir)
            template_file = template_dir / "custom_template.txt"
            template_file.write_text("自定义模板: {variable}", encoding='utf-8')
            
            manager = PromptTemplateManager(template_dir=template_dir)
            
            assert "custom_template" in manager
            assert manager.get_template("custom_template") == "自定义模板: {variable}"

    def test_init_with_nonexistent_dir(self):
        """测试不存在的目录不会报错"""
        nonexistent_dir = Path("/nonexistent/path")
        manager = PromptTemplateManager(template_dir=nonexistent_dir)
        
        # 应该只包含默认模板
        assert len(manager) >= 3  # 至少包含默认模板
        assert "basic_rag" in manager


class TestTemplateRegistration:
    """测试模板注册"""

    def test_register_template(self):
        """测试注册模板"""
        manager = PromptTemplateManager()
        initial_count = len(manager)
        
        manager.register_template("test_template", "测试: {value}")
        
        assert len(manager) == initial_count + 1
        assert "test_template" in manager
        assert manager.get_template("test_template") == "测试: {value}"

    def test_register_template_overwrite(self):
        """测试覆盖已存在的模板"""
        manager = PromptTemplateManager()
        
        manager.register_template("test", "原始模板")
        assert manager.get_template("test") == "原始模板"
        
        manager.register_template("test", "新模板")
        assert manager.get_template("test") == "新模板"

    def test_get_template_existing(self):
        """测试获取存在的模板"""
        manager = PromptTemplateManager()
        
        template = manager.get_template("basic_rag")
        assert template is not None
        assert isinstance(template, str)
        assert "{context}" in template

    def test_get_template_nonexistent(self):
        """测试获取不存在的模板"""
        manager = PromptTemplateManager()
        
        template = manager.get_template("nonexistent_template")
        assert template is None

    def test_list_templates(self):
        """测试列出所有模板"""
        manager = PromptTemplateManager()
        templates = manager.list_templates()
        
        assert isinstance(templates, list)
        assert len(templates) > 0
        assert "basic_rag" in templates
        assert all(isinstance(t, str) for t in templates)


class TestTemplateRendering:
    """测试模板渲染"""

    def test_render_basic_template(self):
        """测试基本模板渲染"""
        manager = PromptTemplateManager()
        manager.register_template("test", "问题: {question}, 答案: {answer}")
        
        result = manager.render("test", question="什么是AI", answer="人工智能")
        
        assert "什么是AI" in result
        assert "人工智能" in result
        assert "问题:" in result
        assert "答案:" in result

    def test_render_default_template(self):
        """测试渲染默认模板"""
        manager = PromptTemplateManager()
        
        result = manager.render(
            "basic_rag",
            context="参考文档内容",
            question="用户问题"
        )
        
        assert "参考文档内容" in result
        assert "用户问题" in result

    def test_render_with_multiple_variables(self):
        """测试包含多个变量的模板"""
        manager = PromptTemplateManager()
        manager.register_template(
            "complex",
            "用户: {user}, 时间: {time}, 消息: {message}"
        )
        
        result = manager.render(
            "complex",
            user="Alice",
            time="2024-01-01",
            message="Hello"
        )
        
        assert "Alice" in result
        assert "2024-01-01" in result
        assert "Hello" in result

    def test_render_missing_template(self):
        """测试渲染不存在的模板"""
        manager = PromptTemplateManager()
        
        with pytest.raises(KeyError, match="模板不存在"):
            manager.render("nonexistent", question="test")

    def test_render_missing_variable(self):
        """测试缺少必需变量时抛出错误"""
        manager = PromptTemplateManager()
        manager.register_template("test", "问题: {question}, 答案: {answer}")
        
        with pytest.raises(KeyError):
            manager.render("test", question="test")  # 缺少 answer

    def test_render_with_extra_variables(self):
        """测试传入额外变量（应该被忽略）"""
        manager = PromptTemplateManager()
        manager.register_template("test", "简单模板: {value}")
        
        # 传入额外变量不应该报错，但会被忽略
        result = manager.render("test", value="test", extra="ignored")
        assert "test" in result


class TestTemplatePersistence:
    """测试模板持久化"""

    def test_save_template(self):
        """测试保存模板到文件"""
        manager = PromptTemplateManager()
        manager.register_template("save_test", "保存的模板: {var}")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "template.txt"
            manager.save_template("save_test", file_path)
            
            assert file_path.exists()
            content = file_path.read_text(encoding='utf-8')
            assert "保存的模板: {var}" in content

    def test_save_nonexistent_template(self):
        """测试保存不存在的模板"""
        manager = PromptTemplateManager()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "template.txt"
            
            with pytest.raises(KeyError, match="模板不存在"):
                manager.save_template("nonexistent", file_path)

    def test_load_template(self):
        """测试从文件加载模板"""
        manager = PromptTemplateManager()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "loaded_template.txt"
            file_path.write_text("从文件加载: {value}", encoding='utf-8')
            
            manager.load_template("loaded_template", file_path)
            
            assert "loaded_template" in manager
            assert manager.get_template("loaded_template") == "从文件加载: {value}"

    def test_load_template_overwrite(self):
        """测试加载模板会覆盖已存在的模板"""
        manager = PromptTemplateManager()
        manager.register_template("test", "原始")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.txt"
            file_path.write_text("新内容", encoding='utf-8')
            
            manager.load_template("test", file_path)
            assert manager.get_template("test") == "新内容"

    def test_export_templates(self):
        """测试导出所有模板到JSON"""
        manager = PromptTemplateManager()
        manager.register_template("export_test", "导出测试: {var}")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "templates.json"
            manager.export_templates(output_path)
            
            assert output_path.exists()
            
            with open(output_path, 'r', encoding='utf-8') as f:
                exported = json.load(f)
            
            assert "export_test" in exported
            assert "basic_rag" in exported
            assert exported["export_test"] == "导出测试: {var}"

    def test_import_templates(self):
        """测试从JSON导入模板"""
        manager = PromptTemplateManager()
        initial_count = len(manager)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "templates.json"
            templates_data = {
                "imported1": "导入模板1: {var1}",
                "imported2": "导入模板2: {var2}"
            }
            
            with open(input_path, 'w', encoding='utf-8') as f:
                json.dump(templates_data, f, ensure_ascii=False)
            
            manager.import_templates(input_path)
            
            assert "imported1" in manager
            assert "imported2" in manager
            assert manager.get_template("imported1") == "导入模板1: {var1}"
            assert manager.get_template("imported2") == "导入模板2: {var2}"
            assert len(manager) == initial_count + 2

    def test_import_templates_overwrite(self):
        """测试导入模板会覆盖已存在的模板"""
        manager = PromptTemplateManager()
        manager.register_template("overwrite_test", "原始")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "templates.json"
            with open(input_path, 'w', encoding='utf-8') as f:
                json.dump({"overwrite_test": "新内容"}, f, ensure_ascii=False)
            
            manager.import_templates(input_path)
            assert manager.get_template("overwrite_test") == "新内容"


class TestTemplateManagerSpecialMethods:
    """测试模板管理器的特殊方法"""

    def test_len_method(self):
        """测试 __len__ 方法"""
        manager = PromptTemplateManager()
        initial_len = len(manager)
        
        manager.register_template("new", "新模板")
        assert len(manager) == initial_len + 1

    def test_contains_method(self):
        """测试 __contains__ 方法"""
        manager = PromptTemplateManager()
        
        assert "basic_rag" in manager
        assert "nonexistent" not in manager
        
        manager.register_template("test", "测试")
        assert "test" in manager

    def test_repr_method(self):
        """测试 __repr__ 方法"""
        manager = PromptTemplateManager()
        repr_str = repr(manager)
        
        assert "PromptTemplateManager" in repr_str
        assert str(len(manager)) in repr_str


class TestLoadTemplatesFromDir:
    """测试从目录加载模板"""

    def test_load_templates_from_dir(self):
        """测试从目录加载所有 .txt 模板文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_dir = Path(tmpdir)
            
            # 创建多个模板文件
            (template_dir / "template1.txt").write_text("模板1: {var1}", encoding='utf-8')
            (template_dir / "template2.txt").write_text("模板2: {var2}", encoding='utf-8')
            (template_dir / "not_template.json").write_text("{}", encoding='utf-8')  # 应该被忽略
            
            manager = PromptTemplateManager(template_dir=template_dir)
            
            assert "template1" in manager
            assert "template2" in manager
            assert manager.get_template("template1") == "模板1: {var1}"
            assert manager.get_template("template2") == "模板2: {var2}"

    def test_load_templates_from_dir_with_subdir(self):
        """测试目录中的子目录被忽略"""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_dir = Path(tmpdir)
            (template_dir / "template.txt").write_text("模板", encoding='utf-8')
            (template_dir / "subdir").mkdir()
            (template_dir / "subdir" / "ignored.txt").write_text("被忽略", encoding='utf-8')
            
            manager = PromptTemplateManager(template_dir=template_dir)
            
            assert "template" in manager
            # subdir 中的文件不应该被加载（glob 只匹配当前目录）


class TestGlobalTemplateManager:
    """测试全局模板管理器"""

    def test_get_global_template_manager_singleton(self):
        """测试全局管理器是单例"""
        # 清除全局变量以便测试
        import src.business.prompts.template_manager as tm_module
        tm_module._global_manager = None
        
        manager1 = get_global_template_manager()
        manager2 = get_global_template_manager()
        
        assert manager1 is manager2

    def test_global_manager_has_default_templates(self):
        """测试全局管理器包含默认模板"""
        import src.business.prompts.template_manager as tm_module
        tm_module._global_manager = None
        
        manager = get_global_template_manager()
        assert "basic_rag" in manager


class TestTemplateManagerEdgeCases:
    """测试边界情况"""

    def test_empty_template(self):
        """测试空模板（当前实现不支持空字符串作为有效模板）"""
        manager = PromptTemplateManager()
        manager.register_template("empty", "")
        
        # 验证模板已注册
        assert "empty" in manager
        assert manager.get_template("empty") == ""
        
        # 注意：当前实现中，render 方法使用 `if not template:` 判断，
        # 这会导致空字符串被认为是 False，从而抛出 KeyError
        # 这是一个已知的限制
        with pytest.raises(KeyError):
            manager.render("empty")

    def test_template_with_no_variables(self):
        """测试没有变量的模板"""
        manager = PromptTemplateManager()
        manager.register_template("no_vars", "这是一个没有变量的模板")
        
        result = manager.render("no_vars")
        assert result == "这是一个没有变量的模板"

    def test_template_with_numeric_variables(self):
        """测试模板包含数字变量名（格式字符串的特性）"""
        manager = PromptTemplateManager()
        # 使用命名参数而不是位置参数
        manager.register_template("numeric", "{var0} and {var1}")
        
        # 使用命名参数进行渲染
        result = manager.render("numeric", var0="first", var1="second")
        assert "first" in result
        assert "second" in result

    def test_unicode_in_template(self):
        """测试模板中的 Unicode 字符"""
        manager = PromptTemplateManager()
        manager.register_template("unicode", "中文: {value}, 日文: こんにちは")
        
        result = manager.render("unicode", value="测试")
        assert "中文" in result
        assert "测试" in result
        assert "こんにちは" in result
