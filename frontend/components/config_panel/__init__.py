"""
配置面板模块 - 统一管理应用配置的 UI 组件

主要功能：
- AppConfig: 应用运行时配置数据类
- LLM_PRESETS: LLM 预设定义
- render_advanced_config(): 设置弹窗高级配置
"""

from frontend.components.config_panel.models import (
    AppConfig,
    LLM_PRESETS,
    get_preset_params,
)
from frontend.components.config_panel.panel import render_advanced_config

__all__ = [
    'AppConfig',
    'LLM_PRESETS',
    'get_preset_params',
    'render_advanced_config',
]
