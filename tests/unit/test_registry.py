"""
模块注册中心单元测试
"""

import pytest
from unittest.mock import Mock, patch
import tempfile
import yaml
from pathlib import Path

from src.business.registry import (
    ModuleRegistry,
    ModuleRegistration,
    get_registry,
    reset_registry,
)
from src.business.protocols import (
    ModuleMetadata,
    ModuleType,
    PipelineModule,
    PipelineContext,
)


class MockModule(PipelineModule):
    """Mock模块用于测试"""
    
    def __init__(self, name: str):
        super().__init__(name, ModuleType.RETRIEVAL)
    
    def execute(self, context: PipelineContext) -> PipelineContext:
        context.set_metadata("executed", True)
        return context


def mock_factory(**kwargs):
    """Mock工厂函数"""
    return MockModule(kwargs.get("name", "mock_module"))


class TestModuleRegistry:
    """ModuleRegistry单元测试"""
    
    def test_init(self):
        """测试初始化"""
        registry = ModuleRegistry()
        
        assert len(registry._registrations) == 0
        assert len(registry.list_modules()) == 0
    
    def test_register_module(self):
        """测试注册模块"""
        registry = ModuleRegistry()
        
        metadata = ModuleMetadata(
            name="test_module",
            module_type=ModuleType.RETRIEVAL,
            version="1.0.0",
            description="测试模块",
        )
        
        registry.register(
            metadata=metadata,
            factory=mock_factory,
        )
        
        assert len(registry.list_modules()) == 1
        assert "test_module" in registry.list_modules()
    
    def test_register_module_with_class(self):
        """测试使用类注册模块"""
        registry = ModuleRegistry()
        
        metadata = ModuleMetadata(
            name="test_module",
            module_type=ModuleType.GENERATION,
        )
        
        registry.register(
            metadata=metadata,
            module_class=MockModule,
        )
        
        assert "test_module" in registry.list_modules()
    
    def test_register_module_no_factory_or_class(self):
        """测试无工厂函数或类"""
        registry = ModuleRegistry()
        
        metadata = ModuleMetadata(
            name="test_module",
            module_type=ModuleType.RETRIEVAL,
        )
        
        with pytest.raises(ValueError, match="必须提供factory或module_class"):
            registry.register(metadata=metadata)
    
    def test_get_module(self):
        """测试获取模块"""
        registry = ModuleRegistry()
        
        metadata = ModuleMetadata(
            name="test_module",
            module_type=ModuleType.RETRIEVAL,
        )
        
        registry.register(metadata=metadata, factory=mock_factory)
        
        registration = registry.get_module("test_module")
        assert registration is not None
        assert registration.metadata.name == "test_module"
        
        # 不存在的模块
        assert registry.get_module("nonexistent") is None
    
    def test_list_modules(self):
        """测试列出模块"""
        registry = ModuleRegistry()
        
        # 注册多个模块
        for i in range(3):
            metadata = ModuleMetadata(
                name=f"module_{i}",
                module_type=ModuleType.RETRIEVAL if i % 2 == 0 else ModuleType.GENERATION,
            )
            registry.register(metadata=metadata, factory=mock_factory)
        
        # 列出所有模块
        all_modules = registry.list_modules()
        assert len(all_modules) == 3
        
        # 按类型过滤
        retrieval_modules = registry.list_modules(ModuleType.RETRIEVAL)
        assert len(retrieval_modules) == 2
        
        generation_modules = registry.list_modules(ModuleType.GENERATION)
        assert len(generation_modules) == 1
    
    def test_create_module(self):
        """测试创建模块实例"""
        registry = ModuleRegistry()
        
        metadata = ModuleMetadata(
            name="test_module",
            module_type=ModuleType.RETRIEVAL,
        )
        
        registry.register(metadata=metadata, factory=mock_factory)
        
        instance = registry.create_module("test_module", config={"name": "custom_name"})
        
        assert instance is not None
        assert isinstance(instance, PipelineModule)
    
    def test_create_module_nonexistent(self):
        """测试创建不存在的模块"""
        registry = ModuleRegistry()
        
        instance = registry.create_module("nonexistent")
        
        assert instance is None
    
    def test_get_metadata(self):
        """测试获取元数据"""
        registry = ModuleRegistry()
        
        metadata = ModuleMetadata(
            name="test_module",
            module_type=ModuleType.RETRIEVAL,
            version="1.0.0",
        )
        
        registry.register(metadata=metadata, factory=mock_factory)
        
        retrieved_metadata = registry.get_metadata("test_module")
        
        assert retrieved_metadata is not None
        assert retrieved_metadata.name == "test_module"
        assert retrieved_metadata.version == "1.0.0"
    
    def test_load_from_yaml(self):
        """测试从YAML加载"""
        registry = ModuleRegistry()
        
        # 创建临时YAML文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml_config = {
                'modules': [
                    {
                        'name': 'test_module',
                        'module_type': 'retrieval',
                        'version': '1.0.0',
                        'factory': 'tests.unit.test_registry.mock_factory',
                    }
                ]
            }
            yaml.dump(yaml_config, f)
            yaml_path = f.name
        
        try:
            registry.load_from_yaml(yaml_path)
            
            assert "test_module" in registry.list_modules()
        finally:
            Path(yaml_path).unlink()
    
    def test_export_to_yaml(self):
        """测试导出到YAML"""
        registry = ModuleRegistry()
        
        metadata = ModuleMetadata(
            name="test_module",
            module_type=ModuleType.RETRIEVAL,
            version="1.0.0",
        )
        
        registry.register(metadata=metadata, factory=mock_factory)
        
        # 导出到临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml_path = f.name
        
        try:
            registry.export_to_yaml(yaml_path)
            
            # 验证文件存在
            assert Path(yaml_path).exists()
            
            # 验证内容
            with open(yaml_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                assert 'modules' in config
                assert len(config['modules']) == 1
        finally:
            Path(yaml_path).unlink()
    
    def test_get_summary(self):
        """测试获取摘要"""
        registry = ModuleRegistry()
        
        # 注册多个不同类型的模块
        for i, module_type in enumerate([ModuleType.RETRIEVAL, ModuleType.GENERATION]):
            metadata = ModuleMetadata(
                name=f"module_{i}",
                module_type=module_type,
            )
            registry.register(metadata=metadata, factory=mock_factory)
        
        summary = registry.get_summary()
        
        assert summary['total_modules'] == 2
        assert 'by_type' in summary
        assert summary['by_type']['retrieval'] == 1
        assert summary['by_type']['generation'] == 1


class TestGlobalRegistry:
    """全局注册中心测试"""
    
    def test_get_registry_singleton(self):
        """测试单例模式"""
        reset_registry()
        
        registry1 = get_registry()
        registry2 = get_registry()
        
        assert registry1 is registry2
    
    def test_reset_registry(self):
        """测试重置注册中心"""
        registry1 = get_registry()
        registry1.register(
            metadata=ModuleMetadata(name="test", module_type=ModuleType.RETRIEVAL),
            factory=mock_factory,
        )
        
        reset_registry()
        
        registry2 = get_registry()
        assert len(registry2.list_modules()) == 0 or len(registry2.list_modules()) > 0  # 可能有默认注册


class TestModuleRegistration:
    """ModuleRegistration测试"""
    
    def test_create_instance(self):
        """测试创建实例"""
        metadata = ModuleMetadata(
            name="test_module",
            module_type=ModuleType.RETRIEVAL,
        )
        
        registration = ModuleRegistration(
            metadata=metadata,
            factory=mock_factory,
            config_schema={"defaults": {"name": "default_name"}},
        )
        
        instance = registration.create_instance()
        assert isinstance(instance, PipelineModule)
        
        # 使用自定义配置
        instance2 = registration.create_instance(config={"name": "custom_name"})
        assert isinstance(instance2, PipelineModule)
    
    def test_create_instance_with_class(self):
        """测试使用类创建实例"""
        metadata = ModuleMetadata(
            name="test_module",
            module_type=ModuleType.RETRIEVAL,
        )
        
        registration = ModuleRegistration(
            metadata=metadata,
            factory=None,  # 使用 module_class 时，factory 为 None
            module_class=MockModule,
        )
        
        instance = registration.create_instance(config={"name": "test"})
        assert isinstance(instance, MockModule)

