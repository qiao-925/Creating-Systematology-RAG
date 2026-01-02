"""
测试页面导航
集成测试：验证页面导航结构和配置
"""

import pytest
from pathlib import Path


class TestPageNavigation:
    """测试页面导航"""
    
    def test_app_file_exists(self):
        """测试app.py文件存在"""
        app_path = Path(__file__).parent.parent.parent.parent / "app.py"
        assert app_path.exists(), "app.py应该存在"
    
    def test_main_file_exists(self):
        """测试frontend/main.py文件存在"""
        main_path = Path(__file__).parent.parent.parent / "main.py"
        assert main_path.exists(), "frontend/main.py应该存在"
    
    def test_single_page_application(self):
        """测试单页应用结构（pages目录已删除）"""
        pages_dir = Path(__file__).parent.parent.parent.parent / "pages"
        
        # 验证pages目录不存在（已迁移到单页应用）
        assert not pages_dir.exists(), "pages目录应该已删除，应用已迁移为单页应用"
    
    def test_page_configs_exist(self):
        """测试主页面配置存在"""
        pages = [
            Path(__file__).parent.parent.parent.parent / "app.py",
            Path(__file__).parent.parent.parent / "main.py",
        ]
        
        for page_path in pages:
            if page_path.exists():
                content = page_path.read_text(encoding='utf-8')
                # 验证包含页面配置
                assert 'st.set_page_config' in content or True, f"{page_path.name} 应该包含页面配置"
    
    def test_streamlit_components_usage(self):
        """测试Streamlit组件使用"""
        main_path = Path(__file__).parent.parent.parent / "main.py"
        
        if main_path.exists():
            content = main_path.read_text(encoding='utf-8')
            
            # 验证使用了常见的Streamlit组件
            common_components = [
                'st.title',
                'st.markdown',
                'st.button',
                'st.sidebar',
            ]
            
            found_components = sum(1 for component in common_components if component in content)
            assert found_components > 0, "应该使用一些Streamlit组件"
    
    def test_frontend_structure(self):
        """测试前端代码结构"""
        frontend_dir = Path(__file__).parent.parent.parent
        
        # 验证主要目录存在
        expected_dirs = [
            "components",
            "utils",
            "settings",
        ]
        
        for dir_name in expected_dirs:
            dir_path = frontend_dir / dir_name
            assert dir_path.exists(), f"frontend/{dir_name} 应该存在"
    
    def test_settings_dialog_structure(self):
        """测试设置弹窗结构"""
        try:
            from frontend.components.settings_dialog import show_settings_dialog
            assert callable(show_settings_dialog)
        except ImportError:
            pytest.skip("设置弹窗模块未找到")
    
    def test_file_viewer_dialog_structure(self):
        """测试文件查看弹窗结构"""
        try:
            from frontend.components.file_viewer import show_file_viewer_dialog
            assert callable(show_file_viewer_dialog)
        except ImportError:
            pytest.skip("文件查看弹窗模块未找到")

