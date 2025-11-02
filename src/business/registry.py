"""
模块注册中心

管理模块元数据，提供工厂函数创建实例
支持版本管理和配置驱动
"""

from typing import Dict, List, Optional, Any, Callable, Type
from dataclasses import dataclass, field, asdict
import importlib
import yaml
from pathlib import Path

from src.business.protocols import (
    PipelineModule,
    ModuleType,
    ModuleMetadata,
)
from src.logger import setup_logger

logger = setup_logger('module_registry')


@dataclass
class ModuleRegistration:
    """模块注册信息"""
    metadata: ModuleMetadata
    factory: Callable
    module_class: Optional[Type] = None
    config_schema: Dict[str, Any] = field(default_factory=dict)
    
    def create_instance(self, config: Optional[Dict[str, Any]] = None) -> PipelineModule:
        """创建模块实例
        
        Args:
            config: 模块配置
            
        Returns:
            PipelineModule实例
        """
        if config is None:
            config = {}
        
        # 合并默认配置
        merged_config = {**self.config_schema.get("defaults", {}), **config}
        
        # 调用工厂函数或类构造函数
        if self.factory:
            return self.factory(**merged_config)
        elif self.module_class:
            return self.module_class(**merged_config)
        else:
            raise ValueError(f"模块 {self.metadata.name} 没有有效的工厂函数或类")


class ModuleRegistry:
    """模块注册中心
    
    管理所有模块的元数据，提供工厂函数创建实例
    """
    
    def __init__(self):
        """初始化模块注册中心"""
        self._registrations: Dict[str, ModuleRegistration] = {}
        self._by_type: Dict[ModuleType, List[str]] = {
            module_type: [] for module_type in ModuleType
        }
        
        logger.info("模块注册中心初始化")
    
    def register(
        self,
        metadata: ModuleMetadata,
        factory: Optional[Callable] = None,
        module_class: Optional[Type] = None,
        config_schema: Optional[Dict[str, Any]] = None,
    ):
        """注册模块
        
        Args:
            metadata: 模块元数据
            factory: 工厂函数（优先使用）
            module_class: 模块类（factory为None时使用）
            config_schema: 配置模式
        """
        if not factory and not module_class:
            raise ValueError("必须提供factory或module_class")
        
        registration = ModuleRegistration(
            metadata=metadata,
            factory=factory,
            module_class=module_class,
            config_schema=config_schema or {},
        )
        
        self._registrations[metadata.name] = registration
        self._by_type[metadata.module_type].append(metadata.name)
        
        logger.info(
            f"注册模块: {metadata.name} "
            f"(type={metadata.module_type.value}, version={metadata.version})"
        )
    
    def get_module(self, name: str) -> Optional[ModuleRegistration]:
        """获取模块注册信息"""
        return self._registrations.get(name)
    
    def list_modules(self, module_type: Optional[ModuleType] = None) -> List[str]:
        """列出模块名称
        
        Args:
            module_type: 模块类型过滤（可选）
            
        Returns:
            模块名称列表
        """
        if module_type:
            return self._by_type.get(module_type, []).copy()
        else:
            return list(self._registrations.keys())
    
    def create_module(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> Optional[PipelineModule]:
        """创建模块实例
        
        Args:
            name: 模块名称
            config: 模块配置
            
        Returns:
            PipelineModule实例，如果模块不存在则返回None
        """
        registration = self._registrations.get(name)
        if not registration:
            logger.warning(f"模块不存在: {name}")
            return None
        
        try:
            instance = registration.create_instance(config)
            logger.info(f"创建模块实例: {name}")
            return instance
        except Exception as e:
            logger.error(f"创建模块实例失败: {name}, error={e}", exc_info=True)
            return None
    
    def get_metadata(self, name: str) -> Optional[ModuleMetadata]:
        """获取模块元数据"""
        registration = self._registrations.get(name)
        return registration.metadata if registration else None
    
    def load_from_yaml(self, yaml_path: str):
        """从YAML文件加载模块配置
        
        Args:
            yaml_path: YAML配置文件路径
        """
        yaml_file = Path(yaml_path)
        if not yaml_file.exists():
            logger.warning(f"YAML配置文件不存在: {yaml_path}")
            return
        
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if not config or 'modules' not in config:
                logger.warning(f"YAML配置文件格式错误: {yaml_path}")
                return
            
            for module_config in config['modules']:
                try:
                    self._register_from_config(module_config)
                except Exception as e:
                    logger.error(f"注册模块失败: {module_config.get('name', 'unknown')}, error={e}")
            
            logger.info(f"从YAML加载模块配置: {len(config['modules'])} 个模块")
            
        except Exception as e:
            logger.error(f"加载YAML配置失败: {e}", exc_info=True)
    
    def _register_from_config(self, module_config: Dict[str, Any]):
        """从配置字典注册模块"""
        # 解析元数据
        metadata = ModuleMetadata(
            name=module_config['name'],
            module_type=ModuleType(module_config['module_type']),
            version=module_config.get('version', '1.0.0'),
            description=module_config.get('description', ''),
            author=module_config.get('author', ''),
            dependencies=module_config.get('dependencies', []),
            config_schema=module_config.get('config_schema', {}),
        )
        
        # 解析工厂函数或类
        factory = None
        module_class = None
        
        if 'factory' in module_config:
            # 从字符串路径导入工厂函数
            factory_path = module_config['factory']
            module_path, func_name = factory_path.rsplit('.', 1)
            module = importlib.import_module(module_path)
            factory = getattr(module, func_name)
        elif 'class' in module_config:
            # 从字符串路径导入类
            class_path = module_config['class']
            module_path, class_name = class_path.rsplit('.', 1)
            module = importlib.import_module(module_path)
            module_class = getattr(module, class_name)
        
        # 注册模块
        self.register(
            metadata=metadata,
            factory=factory,
            module_class=module_class,
            config_schema=module_config.get('config_schema', {}),
        )
    
    def export_to_yaml(self, yaml_path: str):
        """导出模块配置到YAML文件
        
        Args:
            yaml_path: YAML文件路径
        """
        config = {
            'modules': []
        }
        
        for name, registration in self._registrations.items():
            module_config = {
                'name': registration.metadata.name,
                'module_type': registration.metadata.module_type.value,
                'version': registration.metadata.version,
                'description': registration.metadata.description,
                'author': registration.metadata.author,
                'dependencies': registration.metadata.dependencies,
                'config_schema': registration.config_schema,
            }
            
            # 添加工厂函数或类路径
            if registration.factory:
                module_config['factory'] = f"{registration.factory.__module__}.{registration.factory.__name__}"
            elif registration.module_class:
                module_config['class'] = f"{registration.module_class.__module__}.{registration.module_class.__name__}"
            
            config['modules'].append(module_config)
        
        try:
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True, sort_keys=False)
            
            logger.info(f"导出模块配置到YAML: {yaml_path}, {len(config['modules'])} 个模块")
        except Exception as e:
            logger.error(f"导出YAML配置失败: {e}", exc_info=True)
    
    def get_summary(self) -> Dict[str, Any]:
        """获取注册中心摘要"""
        return {
            'total_modules': len(self._registrations),
            'by_type': {
                module_type.value: len(names)
                for module_type, names in self._by_type.items()
                if names
            },
            'modules': [
                {
                    'name': reg.metadata.name,
                    'type': reg.metadata.module_type.value,
                    'version': reg.metadata.version,
                }
                for reg in self._registrations.values()
            ]
        }


# 全局注册中心实例
_global_registry: Optional[ModuleRegistry] = None


def get_registry() -> ModuleRegistry:
    """获取全局模块注册中心"""
    global _global_registry
    if _global_registry is None:
        _global_registry = ModuleRegistry()
    return _global_registry


def reset_registry():
    """重置全局注册中心（主要用于测试）"""
    global _global_registry
    _global_registry = None

