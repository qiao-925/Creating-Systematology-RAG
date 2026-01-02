"""
测试 frontend/settings/data_source.py
对应源文件：frontend/settings/data_source.py
"""

import pytest
from unittest.mock import MagicMock, patch


class TestDataSource:
    """测试数据源设置"""
    
    @patch('frontend.settings.data_source.st')
    @patch('frontend.settings.data_source.DataImportService')
    @patch('frontend.settings.data_source.load_index')
    def test_render_data_source_tab_structure(self, mock_load_index, mock_data_service, mock_st):
        """测试数据源标签页结构"""
        try:
            from frontend.settings.data_source import render_data_source_tab
            mock_st.columns.return_value = [MagicMock(), MagicMock()]
            mock_st.text_input.return_value = ""
            mock_st.button.return_value = False
            render_data_source_tab()
            # 验证基本组件被调用
            mock_st.markdown.assert_called()
        except ImportError:
            pytest.skip("数据源设置模块未找到")

