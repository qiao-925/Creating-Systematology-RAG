"""
提示模板管理器

负责管理和渲染各种提示模板
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import json

from src.logger import setup_logger

logger = setup_logger('prompt_template_manager')


class PromptTemplateManager:
    """提示模板管理器
    
    管理RAG系统中的各种提示模板，支持模板注册、渲染和持久化
    
    Examples:
        >>> manager = PromptTemplateManager()
        >>> manager.register_template("rag_query", "基于以下文档回答问题：\\n{context}\\n\\n问题：{question}")
        >>> prompt = manager.render("rag_query", context="...", question="...")
    """
    
    def __init__(self, template_dir: Optional[Path] = None):
        """初始化模板管理器
        
        Args:
            template_dir: 模板文件目录（可选）
        """
        self.templates: Dict[str, str] = {}
        self.template_dir = template_dir
        
        # 注册默认模板
        self._register_default_templates()
        
        # 从文件加载模板（如果提供）
        if template_dir and template_dir.exists():
            self._load_templates_from_dir(template_dir)
        
        logger.info(f"PromptTemplateManager初始化: templates={len(self.templates)}")
    
    def _register_default_templates(self):
        """注册默认模板"""
        # 基础RAG查询模板
        self.templates["basic_rag"] = """基于以下参考文档，回答用户的问题。

参考文档：
{context}

用户问题：{question}

请提供详细、准确的答案："""
        
        # Markdown格式RAG模板
        self.templates["rag_markdown"] = """## 参考文档

{context}

---

## 用户问题

{question}

---

## 答案

请基于参考文档提供详细答案："""
        
        # 引用型RAG模板
        self.templates["rag_with_citation"] = """你是一个严谨的AI助手，回答问题时必须引用来源。

参考文档：
{context}

问题：{question}

要求：
1. 基于参考文档回答问题
2. 在答案中标注引用来源 [1], [2] 等
3. 如果文档中没有相关信息，请明确说明

答案："""
        
        logger.info(f"注册默认模板: {len(self.templates)}个")
    
    def register_template(self, name: str, template: str):
        """注册模板
        
        Args:
            name: 模板名称
            template: 模板字符串（支持{变量}占位符）
        """
        self.templates[name] = template
        logger.info(f"注册模板: {name}")
    
    def get_template(self, name: str) -> Optional[str]:
        """获取模板
        
        Args:
            name: 模板名称
            
        Returns:
            Optional[str]: 模板字符串，不存在返回None
        """
        return self.templates.get(name)
    
    def render(self, name: str, **kwargs) -> str:
        """渲染模板
        
        Args:
            name: 模板名称
            **kwargs: 模板变量
            
        Returns:
            str: 渲染后的提示词
            
        Raises:
            KeyError: 模板不存在
            KeyError: 缺少必需的模板变量
        """
        template = self.templates.get(name)
        if not template:
            raise KeyError(f"模板不存在: {name}")
        
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.error(f"渲染模板失败，缺少变量: {e}")
            raise
    
    def list_templates(self) -> List[str]:
        """列出所有模板名称
        
        Returns:
            List[str]: 模板名称列表
        """
        return list(self.templates.keys())
    
    def save_template(self, name: str, file_path: Path):
        """保存模板到文件
        
        Args:
            name: 模板名称
            file_path: 文件路径
        """
        template = self.get_template(name)
        if not template:
            raise KeyError(f"模板不存在: {name}")
        
        file_path.write_text(template, encoding='utf-8')
        logger.info(f"保存模板: {name} -> {file_path}")
    
    def load_template(self, name: str, file_path: Path):
        """从文件加载模板
        
        Args:
            name: 模板名称
            file_path: 文件路径
        """
        template = file_path.read_text(encoding='utf-8')
        self.register_template(name, template)
        logger.info(f"加载模板: {file_path} -> {name}")
    
    def _load_templates_from_dir(self, template_dir: Path):
        """从目录加载所有模板"""
        for file_path in template_dir.glob("*.txt"):
            name = file_path.stem
            self.load_template(name, file_path)
        
        logger.info(f"从目录加载模板: {template_dir}, 数量={len(list(template_dir.glob('*.txt')))}")
    
    def export_templates(self, output_path: Path):
        """导出所有模板到JSON文件
        
        Args:
            output_path: 输出文件路径
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.templates, f, ensure_ascii=False, indent=2)
        
        logger.info(f"导出模板: {len(self.templates)}个 -> {output_path}")
    
    def import_templates(self, input_path: Path):
        """从JSON文件导入模板
        
        Args:
            input_path: 输入文件路径
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            templates = json.load(f)
        
        for name, template in templates.items():
            self.register_template(name, template)
        
        logger.info(f"导入模板: {len(templates)}个 <- {input_path}")
    
    def __len__(self) -> int:
        """模板数量"""
        return len(self.templates)
    
    def __contains__(self, name: str) -> bool:
        """检查模板是否存在"""
        return name in self.templates
    
    def __repr__(self) -> str:
        return f"PromptTemplateManager(templates={len(self.templates)})"


# 全局单例（可选）
_global_manager: Optional[PromptTemplateManager] = None


def get_global_template_manager() -> PromptTemplateManager:
    """获取全局模板管理器（单例）
    
    Returns:
        PromptTemplateManager: 全局管理器实例
    """
    global _global_manager
    if _global_manager is None:
        _global_manager = PromptTemplateManager()
    return _global_manager
