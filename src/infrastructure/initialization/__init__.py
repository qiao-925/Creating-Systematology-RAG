"""
初始化管理模块：统一管理项目所有模块的初始化状态和日志记录

主要功能：
- InitializationManager：初始化管理器，统一记录所有模块的初始化状态
- register_module()：注册需要初始化的模块
- check_initialization()：检查模块初始化状态
- generate_report()：生成初始化报告

执行流程：
1. 注册所有需要初始化的模块
2. 在应用启动时统一检查初始化状态
3. 记录每个模块的成功/失败/跳过状态
4. 生成详细的初始化报告

特性：
- 集中管理所有模块初始化
- 详细的日志记录
- 初始化状态统计
- 失败原因追踪
"""

from src.infrastructure.initialization.manager import InitializationManager
from src.infrastructure.initialization.bootstrap import check_initialization_on_startup

__all__ = ['InitializationManager', 'check_initialization_on_startup']
