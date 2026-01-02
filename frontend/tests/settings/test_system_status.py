"""
测试 frontend/settings/system_status.py
对应源文件：frontend/settings/system_status.py
"""

import pytest
from unittest.mock import MagicMock, patch


class TestSystemStatus:
    """测试系统状态设置"""
    
    @patch('frontend.settings.system_status.st')
    @patch('frontend.settings.system_status.display_model_status')
    def test_render_system_status_tab_structure(self, mock_display_model, mock_st):
        """测试系统状态标签页结构"""
        try:
            from frontend.settings.system_status import render_system_status_tab
            # 根据实际代码，st.columns(3) 返回3个列，st.columns([1, 2]) 返回2个列
            def columns_side_effect(*args, **kwargs):
                if len(args) > 0 and args[0] == 3:
                    return [MagicMock(), MagicMock(), MagicMock()]
                elif len(args) > 0 and isinstance(args[0], list) and len(args[0]) == 2:
                    return [MagicMock(), MagicMock()]
                return [MagicMock(), MagicMock()]
            mock_st.columns.side_effect = columns_side_effect
            mock_st.button.return_value = False
            render_system_status_tab()
            # 验证基本组件被调用
            mock_st.markdown.assert_called()
        except ImportError:
            pytest.skip("系统状态设置模块未找到")

