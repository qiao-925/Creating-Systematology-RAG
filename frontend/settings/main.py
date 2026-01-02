"""
设置模块工具函数
此文件已不再使用，设置功能已迁移到弹窗实现（frontend/components/settings_dialog.py）
保留此文件仅用于导出设置标签页渲染函数，供弹窗使用
"""

from frontend.settings.data_source import render_data_source_tab
from frontend.settings.dev_tools import render_dev_tools_tab
from frontend.settings.system_status import render_system_status_tab

# 导出设置标签页渲染函数，供弹窗使用
__all__ = [
    'render_data_source_tab',
    'render_dev_tools_tab',
    'render_system_status_tab',
]
