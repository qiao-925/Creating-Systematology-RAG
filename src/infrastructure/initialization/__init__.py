"""
初始化管理模块：统一管理项目所有模块的初始化状态和日志记录

主要功能：
- InitializationManager：初始化管理器，统一记录所有模块的初始化状态
- initialize_app()：执行所有模块的初始化（推荐）
- check_initialization_on_startup()：检查所有模块的初始化状态（向后兼容）
- register_module()：注册需要初始化的模块
- execute_init()：执行模块初始化
- generate_report()：生成初始化报告

执行流程：
1. 注册所有需要初始化的模块
2. 在应用启动时统一执行初始化（按分类顺序：基础 -> 核心 -> 可选）
3. 记录每个模块的成功/失败/跳过状态
4. 生成详细的初始化报告

特性：
- 集中管理所有模块初始化
- 实际执行初始化（不仅是检查）
- 分类系统（基础/核心/可选）
- 依赖注入和实例存储
- 详细的日志记录
- 初始化状态统计
- 失败原因追踪
"""

from src.infrastructure.initialization.manager import InitializationManager, InitStatus, ModuleStatus
from src.infrastructure.initialization.bootstrap import (
    initialize_app,
    check_initialization_on_startup,
    InitResult
)
from src.infrastructure.initialization.categories import (
    InitCategory,
    CATEGORY_DISPLAY_NAMES,
    CATEGORY_ICONS,
    CATEGORY_INIT_ORDER
)

__all__ = [
    'InitializationManager',
    'InitStatus',
    'ModuleStatus',
    'initialize_app',
    'check_initialization_on_startup',
    'InitResult',
    'InitCategory',
    'CATEGORY_DISPLAY_NAMES',
    'CATEGORY_ICONS',
    'CATEGORY_INIT_ORDER',
]
