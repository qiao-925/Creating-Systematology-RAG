"""
初始化引导模块：在应用启动时执行初始化检查

主要功能：
- check_initialization_on_startup()：在应用启动时检查所有模块的初始化状态
- 生成初始化报告并记录日志
"""

from src.infrastructure.initialization.manager import InitializationManager
from src.infrastructure.initialization.registry import register_all_modules
from src.infrastructure.logger import get_logger

logger = get_logger('initialization_bootstrap')


def check_initialization_on_startup() -> InitializationManager:
    """在应用启动时检查所有模块的初始化状态
    
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
