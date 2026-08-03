"""
初始化相关 Fixtures

提供初始化模块测试相关的 fixtures。
"""

import pytest
from unittest.mock import Mock, MagicMock
from backend.infrastructure.initialization.manager import InitializationManager, InitStatus
from backend.infrastructure.initialization.categories import InitCategory


@pytest.fixture
def mock_initialization_manager():
    """Mock 初始化管理器"""
    manager = Mock(spec=InitializationManager)
    manager.modules = {}
    manager.check_functions = {}
    manager.init_functions = {}
    manager.instances = {}
    manager.execute_all.return_value = {}
    manager.check_all.return_value = {}
    manager.generate_report.return_value = "Mock报告"
    manager.get_status_summary.return_value = {
        "total": 0,
        "success": 0,
        "failed": 0,
        "skipped": 0,
        "pending": 0,
        "required_failed": [],
        "all_required_ready": True
    }
    return manager


@pytest.fixture
def empty_initialization_manager():
    """空的初始化管理器（真实实例）"""
    return InitializationManager()


@pytest.fixture
def mock_init_functions():
    """Mock 初始化函数字典"""
    return {
        "config": lambda: Mock(name="config_instance"),
        "logger": lambda: Mock(name="logger_instance"),
        "embedding": lambda: Mock(name="embedding_instance"),
        "chroma": lambda: Mock(name="chroma_instance"),
        "index_manager": lambda: Mock(name="index_manager_instance")
    }


@pytest.fixture
def mock_check_functions():
    """Mock 检查函数字典"""
    return {
        "config": lambda: True,
        "logger": lambda: True,
        "embedding": lambda: True,
        "chroma": lambda: True,
        "index_manager": lambda: True
    }


@pytest.fixture
def sample_module_statuses():
    """样例模块状态"""
    return {
        "config": {
            "name": "config",
            "category": InitCategory.FOUNDATION.value,
            "status": InitStatus.SUCCESS,
            "is_required": True
        },
        "logger": {
            "name": "logger",
            "category": InitCategory.FOUNDATION.value,
            "status": InitStatus.SUCCESS,
            "is_required": True,
            "dependencies": ["config"]
        },
        "embedding": {
            "name": "embedding",
            "category": InitCategory.CORE.value,
            "status": InitStatus.SUCCESS,
            "is_required": False,
            "dependencies": ["config", "logger"]
        }
    }
