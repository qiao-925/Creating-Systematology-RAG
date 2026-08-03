"""
Template Registry Module

模板注册、加载和索引管理。
"""

import os
import yaml
from typing import Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class PerspectiveTemplate:
    """视角模板数据类"""
    id: str
    name: str
    ddc_class: str
    version: str
    data: Dict  # 完整的 YAML 数据
    file_path: str


class TemplateRegistry:
    """
    模板注册表
    
    功能：
    1. 加载所有预置模板
    2. 按 DDC 分类索引
    3. 模板缓存
    """
    
    def __init__(self, templates_dir: Optional[str] = None):
        if templates_dir is None:
            # 默认路径：backend/perspectives/templates/
            base_dir = Path(__file__).parent
            self.templates_dir = base_dir / "templates"
        else:
            self.templates_dir = Path(templates_dir)
        
        self._cache: Dict[str, PerspectiveTemplate] = {}
        self._ddc_index: Dict[str, List[str]] = {}  # DDC -> template_ids
        self._load_all_templates()
    
    def _load_all_templates(self):
        """加载所有模板文件"""
        if not self.templates_dir.exists():
            return
        
        for yaml_file in self.templates_dir.rglob("*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                if not data or 'id' not in data:
                    continue
                
                template = PerspectiveTemplate(
                    id=data['id'],
                    name=data.get('name', data['id']),
                    ddc_class=data.get('ddc_class', '000'),
                    version=data.get('version', '1.0.0'),
                    data=data,
                    file_path=str(yaml_file)
                )
                
                self._cache[template.id] = template
                
                # 建立 DDC 索引
                ddc = template.ddc_class
                if ddc not in self._ddc_index:
                    self._ddc_index[ddc] = []
                self._ddc_index[ddc].append(template.id)
                
            except Exception as e:
                print(f"Warning: Failed to load template {yaml_file}: {e}")
    
    def get_template(self, template_id: str) -> Optional[PerspectiveTemplate]:
        """获取指定模板"""
        return self._cache.get(template_id)
    
    def get_templates_by_ddc(self, ddc_class: str) -> List[PerspectiveTemplate]:
        """获取指定 DDC 分类的所有模板"""
        template_ids = self._ddc_index.get(ddc_class, [])
        return [self._cache[tid] for tid in template_ids if tid in self._cache]
    
    def get_all_templates(self) -> List[PerspectiveTemplate]:
        """获取所有模板"""
        return list(self._cache.values())
    
    def list_ddc_classes(self) -> List[str]:
        """列出所有可用的 DDC 分类"""
        return list(self._ddc_index.keys())
    
    def get_template_hierarchy(self, template_id: str) -> List[str]:
        """获取模板的继承层次"""
        hierarchy = []
        current_id = template_id
        
        while current_id:
            template = self._cache.get(current_id)
            if not template:
                break
            
            hierarchy.append(current_id)
            
            # 获取父模板
            inheritance = template.data.get('inheritance', {})
            current_id = inheritance.get('from', '').replace('.yaml', '').replace('/', '.')
            if current_id:
                current_id = current_id.split('.')[-1]  # 简化处理
        
        return list(reversed(hierarchy))
    
    def resolve_template(self, template_id: str) -> Dict:
        """
        解析模板（处理继承）
        
        返回完整的模板数据，包含所有继承字段
        """
        hierarchy = self.get_template_hierarchy(template_id)
        
        resolved = {}
        for tid in hierarchy:
            template = self._cache.get(tid)
            if template:
                # 深度合并
                resolved = self._deep_merge(resolved, template.data)
        
        return resolved
    
    @staticmethod
    def _deep_merge(base: Dict, override: Dict) -> Dict:
        """深度合并两个字典"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = TemplateRegistry._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def reload(self):
        """重新加载所有模板"""
        self._cache.clear()
        self._ddc_index.clear()
        self._load_all_templates()
