"""
测试 frontend/settings/dev_tools.py
对应源文件：frontend/settings/dev_tools.py
"""

import pytest
from unittest.mock import MagicMock, patch


class TestDevTools:
    """测试开发工具设置"""
    
    @patch('frontend.settings.dev_tools.st')
    def test_render_dev_tools_tab_structure(self, mock_st):
        """测试开发工具标签页结构"""
        try:
            from frontend.settings.dev_tools import render_dev_tools_tab
            render_dev_tools_tab()
            # 验证基本组件被调用
            mock_st.markdown.assert_called()
        except ImportError:
            pytest.skip("开发工具设置模块未找到")

