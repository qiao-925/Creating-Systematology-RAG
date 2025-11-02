"""
业务能力模块协议定义

定义流水线中各个能力模块的接口规范，确保模块间的互操作性
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class ModuleType(Enum):
    """模块类型枚举"""
    RETRIEVAL = "retrieval"          # 检索模块
    GENERATION = "generation"        # 生成模块
    FORMATTING = "formatting"        # 格式化模块
    RERANKING = "reranking"          # 重排序模块
    PROMPT = "prompt"                # 提示工程模块
    EVALUATION = "evaluation"        # 评估模块
    CUSTOM = "custom"                # 自定义模块


@dataclass
class PipelineContext:
    """流水线上下文
    
    在流水线执行过程中传递数据和状态
    """
    # 输入数据
    query: str = ""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # 中间结果
    retrieved_docs: List[Any] = field(default_factory=list)
    reranked_docs: List[Any] = field(default_factory=list)
    prompt: str = ""
    raw_answer: str = ""
    formatted_answer: str = ""
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 执行状态
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def set_error(self, error: str):
        """添加错误信息"""
        self.errors.append(error)
    
    def set_warning(self, warning: str):
        """添加警告信息"""
        self.warnings.append(warning)
    
    def has_errors(self) -> bool:
        """是否有错误"""
        return len(self.errors) > 0
    
    def get_metadata(self, key: str, default=None):
        """获取元数据"""
        return self.metadata.get(key, default)
    
    def set_metadata(self, key: str, value: Any):
        """设置元数据"""
        self.metadata[key] = value


class PipelineModule(ABC):
    """流水线模块基类
    
    所有能力模块都应继承此类并实现execute方法
    """
    
    def __init__(self, name: str, module_type: ModuleType, config: Optional[Dict[str, Any]] = None):
        """初始化模块
        
        Args:
            name: 模块名称
            module_type: 模块类型
            config: 模块配置
        """
        self.name = name
        self.module_type = module_type
        self.config = config or {}
        self.enabled = True
    
    @abstractmethod
    def execute(self, context: PipelineContext) -> PipelineContext:
        """执行模块逻辑
        
        Args:
            context: 流水线上下文
            
        Returns:
            PipelineContext: 更新后的上下文
        """
        pass
    
    def pre_execute(self, context: PipelineContext) -> bool:
        """执行前钩子
        
        Args:
            context: 流水线上下文
            
        Returns:
            bool: 是否继续执行（True继续，False跳过）
        """
        return self.enabled
    
    def post_execute(self, context: PipelineContext):
        """执行后钩子
        
        Args:
            context: 流水线上下文
        """
        pass
    
    def on_error(self, context: PipelineContext, error: Exception):
        """错误处理钩子
        
        Args:
            context: 流水线上下文
            error: 异常对象
        """
        context.set_error(f"[{self.name}] {str(error)}")
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, type={self.module_type.value})"


class RetrievalModule(PipelineModule):
    """检索模块接口
    
    负责从向量数据库检索相关文档
    """
    
    def __init__(self, name: str = "retrieval", config: Optional[Dict[str, Any]] = None):
        super().__init__(name, ModuleType.RETRIEVAL, config)
    
    @abstractmethod
    def retrieve(self, query: str, top_k: int = 5) -> List[Any]:
        """检索文档
        
        Args:
            query: 查询文本
            top_k: 返回文档数量
            
        Returns:
            List[Any]: 检索到的文档列表
        """
        pass


class RerankingModule(PipelineModule):
    """重排序模块接口
    
    负责对检索结果进行重新排序
    """
    
    def __init__(self, name: str = "reranking", config: Optional[Dict[str, Any]] = None):
        super().__init__(name, ModuleType.RERANKING, config)
    
    @abstractmethod
    def rerank(self, query: str, documents: List[Any]) -> List[Any]:
        """重排序文档
        
        Args:
            query: 查询文本
            documents: 文档列表
            
        Returns:
            List[Any]: 重排序后的文档列表
        """
        pass


class PromptModule(PipelineModule):
    """提示工程模块接口
    
    负责构造LLM提示词
    """
    
    def __init__(self, name: str = "prompt", config: Optional[Dict[str, Any]] = None):
        super().__init__(name, ModuleType.PROMPT, config)
    
    @abstractmethod
    def build_prompt(self, query: str, documents: List[Any]) -> str:
        """构造提示词
        
        Args:
            query: 用户查询
            documents: 参考文档
            
        Returns:
            str: 构造的提示词
        """
        pass


class GenerationModule(PipelineModule):
    """生成模块接口
    
    负责调用LLM生成答案
    """
    
    def __init__(self, name: str = "generation", config: Optional[Dict[str, Any]] = None):
        super().__init__(name, ModuleType.GENERATION, config)
    
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """生成答案
        
        Args:
            prompt: 提示词
            
        Returns:
            str: 生成的答案
        """
        pass


class FormattingModule(PipelineModule):
    """格式化模块接口
    
    负责格式化最终输出
    """
    
    def __init__(self, name: str = "formatting", config: Optional[Dict[str, Any]] = None):
        super().__init__(name, ModuleType.FORMATTING, config)
    
    @abstractmethod
    def format(self, answer: str, sources: List[Any]) -> str:
        """格式化输出
        
        Args:
            answer: 原始答案
            sources: 引用来源
            
        Returns:
            str: 格式化后的答案
        """
        pass


class EvaluationModule(PipelineModule):
    """评估模块接口
    
    负责评估RAG质量
    """
    
    def __init__(self, name: str = "evaluation", config: Optional[Dict[str, Any]] = None):
        super().__init__(name, ModuleType.EVALUATION, config)
    
    @abstractmethod
    def evaluate(self, query: str, answer: str, sources: List[Any]) -> Dict[str, Any]:
        """评估结果
        
        Args:
            query: 用户查询
            answer: 生成的答案
            sources: 引用来源
            
        Returns:
            Dict[str, Any]: 评估指标
        """
        pass


@dataclass
class ModuleMetadata:
    """模块元数据
    
    用于模块注册和管理
    """
    name: str
    module_type: ModuleType
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    dependencies: List[str] = field(default_factory=list)
    config_schema: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "module_type": self.module_type.value,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "dependencies": self.dependencies,
            "config_schema": self.config_schema,
        }


@dataclass
class Pipeline:
    """流水线定义"""
    name: str
    modules: List[PipelineModule]
    description: str = ""
    version: str = "1.0.0"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_module(self, module: PipelineModule):
        """添加模块"""
        self.modules.append(module)
    
    def remove_module(self, module_name: str):
        """移除模块"""
        self.modules = [m for m in self.modules if m.name != module_name]
    
    def get_module(self, module_name: str) -> Optional[PipelineModule]:
        """获取模块"""
        for module in self.modules:
            if module.name == module_name:
                return module
        return None
    
    def __len__(self) -> int:
        return len(self.modules)


# 便捷类型别名
ModuleList = List[PipelineModule]
ModuleConfig = Dict[str, Any]
