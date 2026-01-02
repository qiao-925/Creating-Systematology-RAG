"""
测试 frontend/settings/main.py
对应源文件：frontend/settings/main.py

注意：render_settings_page() 函数已删除，设置功能已迁移到弹窗实现
此测试文件保留用于未来可能的设置模块测试
"""

import pytest


class TestSettingsMain:
    """测试设置模块主文件"""
    
    def test_settings_module_imports(self):
        """测试设置模块可以正常导入"""
        from frontend.settings.main import (
            render_data_source_tab,
            render_dev_tools_tab,
            render_system_status_tab,
        )
        # 验证函数可以导入
        assert callable(render_data_source_tab)
        assert callable(render_dev_tools_tab)
        assert callable(render_system_status_tab)

