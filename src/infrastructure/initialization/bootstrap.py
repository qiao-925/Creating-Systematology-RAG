"""
初始化引导模块：在应用启动时执行初始化

主要功能：
- initialize_app()：在应用启动时执行所有模块的初始化
- check_initialization_on_startup()：检查所有模块的初始化状态（向后兼容）
- 生成初始化报告并记录日志
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional

from src.infrastructure.initialization.manager import InitializationManager
from src.infrastructure.initialization.registry import register_all_modules
from src.infrastructure.initialization.categories import InitCategory
from src.infrastructure.logger import get_logger

logger = get_logger('initialization_bootstrap')


@dataclass
class InitResult:
    """初始化结果"""
    all_required_ready: bool
    manager: InitializationManager
    instances: Dict[str, Any]
    failed_modules: list[str]
    summary: Dict[str, Any]


def initialize_app(
    categories: Optional[list[InitCategory]] = None,
    show_progress: bool = False
) -> InitResult:
    """在应用启动时执行所有模块的初始化
    
    Args:
        categories: 要初始化的分类列表，None表示所有分类
        show_progress: 是否显示进度（Streamlit环境）
        
    Returns:
        InitResult: 初始化结果，包含管理器实例和初始化状态
    """
    logger.info("🚀 开始项目初始化...")
    
    # 创建初始化管理器
    manager = InitializationManager()
    
    # 注册所有模块
    register_all_modules(manager)
    
    # 执行初始化（按分类顺序）
    results = manager.execute_all(categories=categories)
    
    # 生成报告
    report = manager.generate_report()
    logger.info("\n" + report)
    
    # 获取状态摘要
    summary = manager.get_status_summary()
    
    # 检查是否有必需的模块失败
    failed_modules = summary['required_failed']
    all_required_ready = len(failed_modules) == 0
    
    if failed_modules:
        logger.error(f"⚠️  有 {len(failed_modules)} 个必需模块初始化失败: {', '.join(failed_modules)}")
    else:
        logger.info("✅ 所有必需模块初始化成功")
    
    # 记录统计信息
    logger.info(
        f"初始化统计: 总计={summary['total']}, "
        f"成功={summary['success']}, "
        f"失败={summary['failed']}, "
        f"跳过={summary['skipped']}, "
        f"待检查={summary['pending']}"
    )
    
    # 创建初始化结果
    init_result = InitResult(
        all_required_ready=all_required_ready,
        manager=manager,
        instances=manager.instances.copy(),
        failed_modules=failed_modules,
        summary=summary
    )
    
    return init_result


def check_initialization_on_startup() -> InitializationManager:
    """在应用启动时检查所有模块的初始化状态（向后兼容）
    
    Returns:
        InitializationManager: 初始化管理器实例
    """
    logger.info("🚀 开始项目初始化检查...")
    
    # 创建初始化管理器
    manager = InitializationManager()
    
    # 注册所有模块
    register_all_modules(manager)
    
    # 检查所有模块
    results = manager.check_all()
    
    # 生成报告
    report = manager.generate_report()
    logger.info("\n" + report)
    
    # 获取状态摘要
    summary = manager.get_status_summary()
    
    # 检查是否有必需的模块失败
    if summary['required_failed']:
        logger.error(f"⚠️  有 {len(summary['required_failed'])} 个必需模块初始化失败: {', '.join(summary['required_failed'])}")
    else:
        logger.info("✅ 所有必需模块初始化成功")
    
    # 记录统计信息
    logger.info(
        f"初始化统计: 总计={summary['total']}, "
        f"成功={summary['success']}, "
        f"失败={summary['failed']}, "
        f"跳过={summary['skipped']}, "
        f"待检查={summary['pending']}"
    )
    
    return manager
