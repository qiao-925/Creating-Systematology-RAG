"""
初始化模块单元测试
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from backend.infrastructure.initialization.bootstrap import (
    initialize_app,
    check_initialization_on_startup,
    InitResult
)
from backend.infrastructure.initialization.manager import (
    InitializationManager,
    InitStatus,
    ModuleStatus
)
from backend.infrastructure.initialization.registry import register_all_modules
from backend.infrastructure.initialization.categories import InitCategory


@pytest.mark.fast
class TestBootstrap:
    """Bootstrap 模块测试"""
    
    def test_initialize_app_success(self, mocker):
        """测试成功初始化所有模块"""
        # Mock InitializationManager
        mock_manager = Mock(spec=InitializationManager)
        mock_manager.instances = {}
        mock_manager.execute_all.return_value = {
            "config": True,
            "logger": True,
            "embedding": True
        }
        mock_manager.generate_report.return_value = "测试报告"
        mock_manager.get_status_summary.return_value = {
            "total": 3,
            "success": 3,
            "failed": 0,
            "skipped": 0,
            "pending": 0,
            "required_failed": [],
            "all_required_ready": True
        }
        
        mocker.patch(
            'backend.infrastructure.initialization.bootstrap.InitializationManager',
            return_value=mock_manager
        )
        mocker.patch(
            'backend.infrastructure.initialization.bootstrap.register_all_modules'
        )
        
        result = initialize_app()
        
        assert isinstance(result, InitResult)
        assert result.all_required_ready is True
        assert len(result.failed_modules) == 0
        assert mock_manager.execute_all.called
    
    def test_initialize_app_with_categories(self, mocker):
        """测试按分类初始化"""
        mock_manager = Mock(spec=InitializationManager)
        mock_manager.instances = {}
        mock_manager.execute_all.return_value = {"config": True}
        mock_manager.generate_report.return_value = "测试报告"
        mock_manager.get_status_summary.return_value = {
            "total": 1,
            "success": 1,
            "failed": 0,
            "skipped": 0,
            "pending": 0,
            "required_failed": [],
            "all_required_ready": True
        }
        
        mocker.patch(
            'backend.infrastructure.initialization.bootstrap.InitializationManager',
            return_value=mock_manager
        )
        mocker.patch(
            'backend.infrastructure.initialization.bootstrap.register_all_modules'
        )
        
        result = initialize_app(categories=[InitCategory.FOUNDATION])
        
        assert result.all_required_ready is True
        # 验证按分类调用
        mock_manager.execute_all.assert_called_once_with(
            categories=[InitCategory.FOUNDATION]
        )
    
    def test_initialize_app_required_failed(self, mocker):
        """测试必需模块失败的情况"""
        mock_manager = Mock(spec=InitializationManager)
        mock_manager.instances = {}
        mock_manager.execute_all.return_value = {
            "config": True,
            "logger": False  # 必需模块失败
        }
        mock_manager.generate_report.return_value = "测试报告"
        mock_manager.get_status_summary.return_value = {
            "total": 2,
            "success": 1,
            "failed": 1,
            "skipped": 0,
            "pending": 0,
            "required_failed": ["logger"],
            "all_required_ready": False
        }
        
        mocker.patch(
            'backend.infrastructure.initialization.bootstrap.InitializationManager',
            return_value=mock_manager
        )
        mocker.patch(
            'backend.infrastructure.initialization.bootstrap.register_all_modules'
        )
        
        result = initialize_app()
        
        assert result.all_required_ready is False
        assert "logger" in result.failed_modules
    
    def test_initialize_app_show_progress(self, mocker):
        """测试显示进度参数"""
        mock_manager = Mock(spec=InitializationManager)
        mock_manager.instances = {}
        mock_manager.execute_all.return_value = {"config": True}
        mock_manager.generate_report.return_value = "测试报告"
        mock_manager.get_status_summary.return_value = {
            "total": 1,
            "success": 1,
            "failed": 0,
            "skipped": 0,
            "pending": 0,
            "required_failed": [],
            "all_required_ready": True
        }
        
        mocker.patch(
            'backend.infrastructure.initialization.bootstrap.InitializationManager',
            return_value=mock_manager
        )
        mocker.patch(
            'backend.infrastructure.initialization.bootstrap.register_all_modules'
        )
        
        result = initialize_app(show_progress=True)
        
        assert result.all_required_ready is True
    
    def test_check_initialization_on_startup(self, mocker):
        """测试向后兼容的检查函数"""
        mock_manager = Mock(spec=InitializationManager)
        mock_manager.check_all.return_value = {"config": True, "logger": True}
        mock_manager.generate_report.return_value = "测试报告"
        mock_manager.get_status_summary.return_value = {
            "total": 2,
            "success": 2,
            "failed": 0,
            "skipped": 0,
            "pending": 0,
            "required_failed": [],
            "all_required_ready": True
        }
        
        mocker.patch(
            'backend.infrastructure.initialization.bootstrap.InitializationManager',
            return_value=mock_manager
        )
        mocker.patch(
            'backend.infrastructure.initialization.bootstrap.register_all_modules'
        )
        
        manager = check_initialization_on_startup()
        
        assert manager == mock_manager
        assert mock_manager.check_all.called
    
    def test_init_result_structure(self, mocker):
        """测试 InitResult 数据结构"""
        mock_manager = Mock(spec=InitializationManager)
        mock_manager.instances = {"config": Mock(), "logger": Mock()}
        mock_manager.execute_all.return_value = {"config": True, "logger": True}
        mock_manager.generate_report.return_value = "测试报告"
        mock_manager.get_status_summary.return_value = {
            "total": 2,
            "success": 2,
            "failed": 0,
            "skipped": 0,
            "pending": 0,
            "required_failed": [],
            "all_required_ready": True
        }
        
        mocker.patch(
            'backend.infrastructure.initialization.bootstrap.InitializationManager',
            return_value=mock_manager
        )
        mocker.patch(
            'backend.infrastructure.initialization.bootstrap.register_all_modules'
        )
        
        result = initialize_app()
        
        assert hasattr(result, 'all_required_ready')
        assert hasattr(result, 'manager')
        assert hasattr(result, 'instances')
        assert hasattr(result, 'failed_modules')
        assert hasattr(result, 'summary')
        assert isinstance(result.instances, dict)


@pytest.mark.fast
class TestInitializationManager:
    """InitializationManager 测试"""
    
    def test_manager_initialization(self):
        """测试管理器初始化"""
        manager = InitializationManager()
        
        assert manager.modules == {}
        assert manager.check_functions == {}
        assert manager.init_functions == {}
        assert manager.instances == {}
    
    def test_register_module(self):
        """测试模块注册"""
        manager = InitializationManager()
        
        def check_func():
            return True
        
        manager.register_module(
            name="test_module",
            category=InitCategory.FOUNDATION.value,
            check_func=check_func,
            is_required=True
        )
        
        assert "test_module" in manager.modules
        assert "test_module" in manager.check_functions
        assert manager.modules["test_module"].name == "test_module"
        assert manager.modules["test_module"].category == InitCategory.FOUNDATION.value
    
    def test_register_module_with_dependencies(self):
        """测试带依赖的模块注册"""
        manager = InitializationManager()
        
        # 先注册依赖模块
        manager.register_module(
            name="dep_module",
            category=InitCategory.FOUNDATION.value,
            check_func=lambda: True
        )
        
        # 注册依赖 dep_module 的模块
        manager.register_module(
            name="test_module",
            category=InitCategory.CORE.value,
            check_func=lambda: True,
            dependencies=["dep_module"]
        )
        
        assert "test_module" in manager.modules
        assert "dep_module" in manager.modules["test_module"].dependencies
    
    def test_check_initialization_success(self):
        """测试检查初始化成功"""
        manager = InitializationManager()
        
        manager.register_module(
            name="test_module",
            category=InitCategory.FOUNDATION.value,
            check_func=lambda: True
        )
        
        result = manager.check_initialization("test_module")
        
        assert result is True
        assert manager.modules["test_module"].status == InitStatus.SUCCESS
    
    def test_check_initialization_failed(self):
        """测试检查初始化失败"""
        manager = InitializationManager()
        
        manager.register_module(
            name="test_module",
            category=InitCategory.FOUNDATION.value,
            check_func=lambda: False
        )
        
        result = manager.check_initialization("test_module")
        
        assert result is False
        assert manager.modules["test_module"].status == InitStatus.FAILED
    
    def test_check_initialization_dependency_failed(self):
        """测试依赖失败的情况"""
        manager = InitializationManager()
        
        # 注册依赖模块（失败）
        manager.register_module(
            name="dep_module",
            category=InitCategory.FOUNDATION.value,
            check_func=lambda: False,
            is_required=True
        )
        
        # 注册依赖 dep_module 的模块
        manager.register_module(
            name="test_module",
            category=InitCategory.CORE.value,
            check_func=lambda: True,
            dependencies=["dep_module"],
            is_required=True
        )
        
        # 先检查依赖模块
        manager.check_initialization("dep_module")
        
        # 检查 test_module（应该因为依赖失败而失败）
        result = manager.check_initialization("test_module")
        
        assert result is False
        assert manager.modules["test_module"].status == InitStatus.FAILED
    
    def test_execute_init_success(self):
        """测试执行初始化成功"""
        manager = InitializationManager()
        
        mock_instance = Mock()
        
        manager.register_module(
            name="test_module",
            category=InitCategory.FOUNDATION.value,
            init_func=lambda: mock_instance
        )
        
        result = manager.execute_init("test_module")
        
        assert result is True
        assert manager.modules["test_module"].status == InitStatus.SUCCESS
        assert "test_module" in manager.instances
        assert manager.instances["test_module"] == mock_instance
    
    def test_execute_init_failed(self):
        """测试执行初始化失败"""
        manager = InitializationManager()
        
        def failing_init():
            raise ValueError("初始化失败")
        
        manager.register_module(
            name="test_module",
            category=InitCategory.FOUNDATION.value,
            init_func=failing_init
        )
        
        result = manager.execute_init("test_module")
        
        assert result is False
        assert manager.modules["test_module"].status == InitStatus.FAILED
        assert manager.modules["test_module"].error is not None
    
    def test_execute_by_category(self):
        """测试按分类执行"""
        manager = InitializationManager()
        
        # 注册不同分类的模块
        manager.register_module(
            name="foundation_module",
            category=InitCategory.FOUNDATION.value,
            init_func=lambda: Mock()
        )
        
        manager.register_module(
            name="core_module",
            category=InitCategory.CORE.value,
            init_func=lambda: Mock()
        )
        
        results = manager.execute_by_category(InitCategory.FOUNDATION)
        
        assert "foundation_module" in results
        assert "core_module" not in results
    
    def test_execute_all(self):
        """测试执行所有模块"""
        manager = InitializationManager()
        
        manager.register_module(
            name="module1",
            category=InitCategory.FOUNDATION.value,
            init_func=lambda: Mock()
        )
        
        manager.register_module(
            name="module2",
            category=InitCategory.CORE.value,
            init_func=lambda: Mock()
        )
        
        results = manager.execute_all()
        
        assert "module1" in results
        assert "module2" in results
    
    def test_topological_sort(self):
        """测试依赖拓扑排序"""
        manager = InitializationManager()
        
        # 注册模块（有依赖关系）
        manager.register_module(
            name="module_a",
            category=InitCategory.FOUNDATION.value,
            check_func=lambda: True
        )
        
        manager.register_module(
            name="module_b",
            category=InitCategory.CORE.value,
            check_func=lambda: True,
            dependencies=["module_a"]
        )
        
        manager.register_module(
            name="module_c",
            category=InitCategory.CORE.value,
            check_func=lambda: True,
            dependencies=["module_b"]
        )
        
        sorted_modules = manager._topological_sort()
        
        # 验证依赖顺序：module_a 应该在 module_b 之前，module_b 应该在 module_c 之前
        assert sorted_modules.index("module_a") < sorted_modules.index("module_b")
        assert sorted_modules.index("module_b") < sorted_modules.index("module_c")
    
    def test_generate_report(self):
        """测试生成报告"""
        manager = InitializationManager()
        
        manager.register_module(
            name="test_module",
            category=InitCategory.FOUNDATION.value,
            check_func=lambda: True
        )
        
        manager.check_initialization("test_module")
        report = manager.generate_report()
        
        assert isinstance(report, str)
        assert "test_module" in report
        assert "初始化状态报告" in report or "项目初始化状态报告" in report
    
    def test_get_status_summary(self):
        """测试获取状态摘要"""
        manager = InitializationManager()
        
        manager.register_module(
            name="success_module",
            category=InitCategory.FOUNDATION.value,
            check_func=lambda: True
        )
        
        manager.register_module(
            name="failed_module",
            category=InitCategory.FOUNDATION.value,
            check_func=lambda: False,
            is_required=True
        )
        
        manager.check_initialization("success_module")
        manager.check_initialization("failed_module")
        
        summary = manager.get_status_summary()
        
        assert summary["total"] == 2
        assert summary["success"] == 1
        assert summary["failed"] == 1
        assert "failed_module" in summary["required_failed"]
        assert summary["all_required_ready"] is False


@pytest.mark.fast
class TestRegistry:
    """Registry 模块测试"""
    
    def test_register_all_modules(self):
        """测试注册所有模块"""
        manager = InitializationManager()
        
        register_all_modules(manager)
        
        # 验证至少注册了一些模块
        assert len(manager.modules) > 0
    
    def test_module_dependencies(self):
        """测试模块依赖关系"""
        manager = InitializationManager()
        
        register_all_modules(manager)
        
        # 检查某些模块是否有依赖
        for module_name, module_status in manager.modules.items():
            if module_status.dependencies:
                # 验证依赖的模块都已注册
                for dep in module_status.dependencies:
                    assert dep in manager.modules, f"模块 {module_name} 的依赖 {dep} 未注册"
    
    def test_required_vs_optional_modules(self):
        """测试必需和可选模块标记"""
        manager = InitializationManager()
        
        register_all_modules(manager)
        
        # 验证至少有一些必需模块和一些可选模块
        required_modules = [m for m in manager.modules.values() if m.is_required]
        optional_modules = [m for m in manager.modules.values() if not m.is_required]
        
        assert len(required_modules) > 0, "应该有至少一个必需模块"
        # 可选模块可能为0，所以不强制检查
