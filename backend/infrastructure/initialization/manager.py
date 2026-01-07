"""
初始化管理器：统一管理项目所有模块的初始化状态和日志记录

主要功能：
- InitializationManager：初始化管理器类
- register_module()：注册需要初始化的模块
- check_initialization()：检查模块初始化状态
- generate_report()：生成初始化报告
"""

from typing import Dict, List, Optional, Callable, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import traceback

from backend.infrastructure.logger import get_logger
from backend.infrastructure.initialization.categories import (
    InitCategory,
    CATEGORY_DISPLAY_NAMES,
    CATEGORY_ICONS,
    CATEGORY_INIT_ORDER
)

logger = get_logger('initialization')


class InitStatus(Enum):
    """初始化状态枚举"""
    PENDING = "pending"  # 待初始化
    SUCCESS = "success"  # 初始化成功
    FAILED = "failed"    # 初始化失败
    SKIPPED = "skipped"  # 跳过初始化（可选模块）


@dataclass
class ModuleStatus:
    """模块初始化状态"""
    name: str
    category: str  # 分类：infrastructure/business/ui/observability
    status: InitStatus = InitStatus.PENDING
    error: Optional[str] = None
    error_traceback: Optional[str] = None
    init_time: Optional[float] = None  # 初始化耗时（秒）
    dependencies: List[str] = field(default_factory=list)  # 依赖的其他模块
    is_required: bool = True  # 是否为必需模块
    description: Optional[str] = None  # 模块描述


class InitializationManager:
    """初始化管理器：统一管理项目所有模块的初始化状态"""
    
    def __init__(self):
        """初始化管理器"""
        self.modules: Dict[str, ModuleStatus] = {}
        self.check_functions: Dict[str, Callable[[], bool]] = {}
        self.init_functions: Dict[str, Callable[[], Any]] = {}  # 初始化函数字典
        self.instances: Dict[str, Any] = {}  # 存储初始化后的实例
        self.init_time = datetime.now()
        logger.info("初始化管理器已创建")
    
    def register_module(
        self,
        name: str,
        category: str,
        check_func: Optional[Callable[[], bool]] = None,
        init_func: Optional[Callable[[], Any]] = None,
        dependencies: Optional[List[str]] = None,
        is_required: bool = True,
        description: Optional[str] = None
    ) -> None:
        """注册需要初始化的模块
        
        Args:
            name: 模块名称
            category: 模块分类（foundation/core/optional）
            check_func: 检查函数，返回True表示初始化成功
            init_func: 初始化函数，返回初始化后的实例（可选）
            dependencies: 依赖的其他模块名称列表
            is_required: 是否为必需模块
            description: 模块描述
        """
        if name in self.modules:
            logger.warning(f"模块 {name} 已注册，将覆盖之前的注册")
        
        self.modules[name] = ModuleStatus(
            name=name,
            category=category,
            dependencies=dependencies or [],
            is_required=is_required,
            description=description
        )
        
        if check_func:
            self.check_functions[name] = check_func
        
        if init_func:
            self.init_functions[name] = init_func
        
        logger.debug(f"注册模块: {name} (分类: {category}, 必需: {is_required})")
    
    def check_initialization(self, module_name: str) -> bool:
        """检查模块初始化状态
        
        Args:
            module_name: 模块名称
            
        Returns:
            bool: True表示初始化成功，False表示失败或未初始化
        """
        if module_name not in self.modules:
            logger.warning(f"模块 {module_name} 未注册")
            return False
        
        module = self.modules[module_name]
        
        # 检查依赖
        for dep in module.dependencies:
            if dep not in self.modules:
                logger.warning(f"模块 {module_name} 的依赖 {dep} 未注册")
                continue
            
            dep_status = self.modules[dep]
            if dep_status.status != InitStatus.SUCCESS:
                logger.warning(f"模块 {module_name} 的依赖 {dep} 未成功初始化")
                if module.is_required:
                    module.status = InitStatus.FAILED
                    module.error = f"依赖模块 {dep} 未成功初始化"
                    return False
        
        # 执行检查函数
        if module_name in self.check_functions:
            start_time = datetime.now()
            try:
                result = self.check_functions[module_name]()
                elapsed = (datetime.now() - start_time).total_seconds()
                
                if result:
                    module.status = InitStatus.SUCCESS
                    module.init_time = elapsed
                    logger.info(f"✅ 模块 {module_name} 初始化成功 (耗时: {elapsed:.2f}s)")
                else:
                    module.status = InitStatus.FAILED
                    module.error = "检查函数返回False"
                    module.init_time = elapsed
                    logger.error(f"❌ 模块 {module_name} 初始化失败")
            except Exception as e:
                elapsed = (datetime.now() - start_time).total_seconds()
                module.status = InitStatus.FAILED
                module.error = str(e)
                module.error_traceback = traceback.format_exc()
                module.init_time = elapsed
                logger.error(f"❌ 模块 {module_name} 初始化失败: {e}", exc_info=True)
                return False
        else:
            # 没有检查函数，标记为跳过
            module.status = InitStatus.SKIPPED
            logger.debug(f"⏭️  模块 {module_name} 跳过初始化检查（无检查函数）")
        
        return module.status == InitStatus.SUCCESS
    
    def execute_init(self, module_name: str) -> bool:
        """执行模块初始化
        
        Args:
            module_name: 模块名称
            
        Returns:
            bool: True表示初始化成功，False表示失败
        """
        if module_name not in self.modules:
            logger.warning(f"模块 {module_name} 未注册")
            return False
        
        module = self.modules[module_name]
        
        # 如果已经成功初始化，直接返回
        if module.status == InitStatus.SUCCESS and module_name in self.instances:
            logger.debug(f"模块 {module_name} 已初始化，跳过")
            return True
        
        # 检查依赖
        for dep in module.dependencies:
            if dep not in self.modules:
                logger.warning(f"模块 {module_name} 的依赖 {dep} 未注册")
                continue
            
            dep_status = self.modules[dep]
            if dep_status.status != InitStatus.SUCCESS:
                error_msg = f"依赖模块 {dep} 未成功初始化"
                logger.warning(f"模块 {module_name}: {error_msg}")
                if module.is_required:
                    module.status = InitStatus.FAILED
                    module.error = error_msg
                    return False
                else:
                    # 可选模块的依赖失败，标记为跳过
                    module.status = InitStatus.SKIPPED
                    module.error = error_msg
                    return False
        
        # 执行初始化函数
        if module_name in self.init_functions:
            start_time = datetime.now()
            try:
                init_func = self.init_functions[module_name]
                instance = init_func()
                elapsed = (datetime.now() - start_time).total_seconds()
                
                # 存储实例
                if instance is not None:
                    self.instances[module_name] = instance
                
                module.status = InitStatus.SUCCESS
                module.init_time = elapsed
                logger.info(f"✅ 模块 {module_name} 初始化成功 (耗时: {elapsed:.2f}s)")
                return True
            except Exception as e:
                elapsed = (datetime.now() - start_time).total_seconds()
                module.status = InitStatus.FAILED
                module.error = str(e)
                module.error_traceback = traceback.format_exc()
                module.init_time = elapsed
                logger.error(f"❌ 模块 {module_name} 初始化失败: {e}", exc_info=True)
                return False
        else:
            # 没有初始化函数，尝试使用检查函数
            if module_name in self.check_functions:
                return self.check_initialization(module_name)
            else:
                # 既没有初始化函数也没有检查函数，标记为跳过
                module.status = InitStatus.SKIPPED
                logger.debug(f"⏭️  模块 {module_name} 跳过初始化（无初始化函数）")
                return False
    
    def execute_by_category(self, category: InitCategory) -> Dict[str, bool]:
        """按分类执行初始化
        
        Args:
            category: 分类枚举
            
        Returns:
            Dict[str, bool]: 模块名称到初始化状态的映射
        """
        results = {}
        
        # 获取该分类下的所有模块
        category_modules = [
            name for name, module in self.modules.items()
            if module.category == category.value
        ]
        
        # 按依赖顺序排序
        sorted_modules = self._topological_sort()
        category_modules = [m for m in sorted_modules if m in category_modules]
        
        logger.info(f"开始初始化 {category.value} 分类的 {len(category_modules)} 个模块...")
        
        for module_name in category_modules:
            results[module_name] = self.execute_init(module_name)
            
            # 如果必需模块失败，停止初始化
            module = self.modules[module_name]
            if module.is_required and module.status == InitStatus.FAILED:
                logger.error(f"必需模块 {module_name} 初始化失败，停止 {category.value} 分类的初始化")
                break
        
        return results
    
    def execute_all(
        self,
        categories: Optional[List[InitCategory]] = None
    ) -> Dict[str, bool]:
        """执行所有或指定分类的初始化
        
        Args:
            categories: 要初始化的分类列表，None表示所有分类
            
        Returns:
            Dict[str, bool]: 模块名称到初始化状态的映射
        """
        results = {}
        
        # 确定要初始化的分类
        if categories is None:
            categories = CATEGORY_INIT_ORDER
        
        logger.info(f"开始执行初始化，分类顺序: {[c.value for c in categories]}")
        
        # 按分类顺序执行
        for category in categories:
            category_results = self.execute_by_category(category)
            results.update(category_results)
            
            # 检查是否有必需模块失败
            failed_required = [
                name for name, success in category_results.items()
                if not success and self.modules[name].is_required
            ]
            
            if failed_required:
                logger.error(f"分类 {category.value} 中有 {len(failed_required)} 个必需模块失败: {failed_required}")
                # 继续执行其他分类，但记录错误
        
        return results
    
    def check_all(self) -> Dict[str, bool]:
        """检查所有模块的初始化状态
        
        Returns:
            Dict[str, bool]: 模块名称到初始化状态的映射
        """
        results = {}
        
        # 按依赖顺序排序（简单的拓扑排序）
        sorted_modules = self._topological_sort()
        
        logger.info(f"开始检查 {len(sorted_modules)} 个模块的初始化状态...")
        
        for module_name in sorted_modules:
            results[module_name] = self.check_initialization(module_name)
        
        return results
    
    def _topological_sort(self) -> List[str]:
        """拓扑排序：按依赖关系排序模块
        
        Returns:
            List[str]: 排序后的模块名称列表
        """
        # 简单的拓扑排序实现
        visited = set()
        result = []
        
        def visit(name: str):
            if name in visited:
                return
            visited.add(name)
            
            module = self.modules[name]
            for dep in module.dependencies:
                if dep in self.modules:
                    visit(dep)
            
            result.append(name)
        
        for module_name in self.modules:
            if module_name not in visited:
                visit(module_name)
        
        return result
    
    def generate_report(self) -> str:
        """生成初始化报告
        
        Returns:
            str: 格式化的初始化报告
        """
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("📊 项目初始化状态报告")
        report_lines.append("=" * 80)
        report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # 按分类统计
        by_category: Dict[str, List[ModuleStatus]] = {}
        for module in self.modules.values():
            if module.category not in by_category:
                by_category[module.category] = []
            by_category[module.category].append(module)
        
        # 统计信息
        total = len(self.modules)
        success = sum(1 for m in self.modules.values() if m.status == InitStatus.SUCCESS)
        failed = sum(1 for m in self.modules.values() if m.status == InitStatus.FAILED)
        skipped = sum(1 for m in self.modules.values() if m.status == InitStatus.SKIPPED)
        pending = sum(1 for m in self.modules.values() if m.status == InitStatus.PENDING)
        
        report_lines.append("📈 总体统计:")
        report_lines.append(f"  总模块数: {total}")
        report_lines.append(f"  ✅ 成功: {success}")
        report_lines.append(f"  ❌ 失败: {failed}")
        report_lines.append(f"  ⏭️  跳过: {skipped}")
        report_lines.append(f"  ⏳ 待检查: {pending}")
        report_lines.append("")
        
        # 按分类详细报告（使用新的分类系统）
        for category in CATEGORY_INIT_ORDER:
            category_value = category.value
            if category_value not in by_category:
                continue
            
            modules = by_category[category_value]
            category_display = CATEGORY_DISPLAY_NAMES.get(category_value, category_value)
            category_icon = CATEGORY_ICONS.get(category_value, "📦")
            report_lines.append(f"{category_icon} {category_display} ({len(modules)} 个模块):")
            
            for module in sorted(modules, key=lambda m: m.name):
                status_icon = {
                    InitStatus.SUCCESS: "✅",
                    InitStatus.FAILED: "❌",
                    InitStatus.SKIPPED: "⏭️ ",
                    InitStatus.PENDING: "⏳"
                }.get(module.status, "❓")
                
                required_mark = "【必需】" if module.is_required else "【可选】"
                time_info = f" ({module.init_time:.2f}s)" if module.init_time else ""
                
                report_lines.append(f"  {status_icon} {module.name} {required_mark}{time_info}")
                
                if module.description:
                    report_lines.append(f"     描述: {module.description}")
                
                if module.dependencies:
                    report_lines.append(f"     依赖: {', '.join(module.dependencies)}")
                
                if module.status == InitStatus.FAILED and module.error:
                    report_lines.append(f"     错误: {module.error}")
                    if module.error_traceback:
                        # 只显示错误堆栈的前几行
                        trace_lines = module.error_traceback.split('\n')[:3]
                        report_lines.append(f"     堆栈: {' | '.join(trace_lines)}")
            
            report_lines.append("")
        
        # 失败模块汇总
        failed_modules = [m for m in self.modules.values() if m.status == InitStatus.FAILED]
        if failed_modules:
            report_lines.append("⚠️  失败模块详情:")
            for module in failed_modules:
                report_lines.append(f"  ❌ {module.name}: {module.error}")
            report_lines.append("")
        
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)
    
    def get_status_summary(self) -> Dict[str, Any]:
        """获取初始化状态摘要
        
        Returns:
            Dict[str, Any]: 状态摘要字典
        """
        total = len(self.modules)
        success = sum(1 for m in self.modules.values() if m.status == InitStatus.SUCCESS)
        failed = sum(1 for m in self.modules.values() if m.status == InitStatus.FAILED)
        skipped = sum(1 for m in self.modules.values() if m.status == InitStatus.SKIPPED)
        pending = sum(1 for m in self.modules.values() if m.status == InitStatus.PENDING)
        
        required_failed = [
            m.name for m in self.modules.values()
            if m.status == InitStatus.FAILED and m.is_required
        ]
        
        return {
            "total": total,
            "success": success,
            "failed": failed,
            "skipped": skipped,
            "pending": pending,
            "required_failed": required_failed,
            "all_required_ready": len(required_failed) == 0
        }
