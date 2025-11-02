"""
Pipeline执行器 - 钩子管理模块
钩子管理逻辑
"""

from typing import List, Callable

from src.business.protocols import PipelineModule, PipelineContext, Pipeline
from src.logger import setup_logger

logger = setup_logger('pipeline_executor')


class HookManager:
    """钩子管理器"""
    
    def __init__(self, enable_hooks: bool = True):
        """初始化钩子管理器"""
        self.enable_hooks = enable_hooks
        
        self._pre_pipeline_hooks: List[Callable] = []
        self._post_pipeline_hooks: List[Callable] = []
        self._pre_module_hooks: List[Callable] = []
        self._post_module_hooks: List[Callable] = []
        self._error_hooks: List[Callable] = []
    
    def add_pre_pipeline_hook(self, hook: Callable):
        """添加流水线执行前钩子"""
        self._pre_pipeline_hooks.append(hook)
    
    def add_post_pipeline_hook(self, hook: Callable):
        """添加流水线执行后钩子"""
        self._post_pipeline_hooks.append(hook)
    
    def add_pre_module_hook(self, hook: Callable):
        """添加模块执行前钩子"""
        self._pre_module_hooks.append(hook)
    
    def add_post_module_hook(self, hook: Callable):
        """添加模块执行后钩子"""
        self._post_module_hooks.append(hook)
    
    def add_error_hook(self, hook: Callable):
        """添加错误钩子"""
        self._error_hooks.append(hook)
    
    def trigger_pre_pipeline_hooks(self, pipeline: Pipeline, context: PipelineContext):
        """触发流水线执行前钩子"""
        if not self.enable_hooks:
            return
        for hook in self._pre_pipeline_hooks:
            try:
                hook(pipeline, context)
            except Exception as e:
                logger.warning(f"Pre-pipeline hook失败: {e}")
    
    def trigger_post_pipeline_hooks(self, pipeline: Pipeline, context: PipelineContext):
        """触发流水线执行后钩子"""
        if not self.enable_hooks:
            return
        for hook in self._post_pipeline_hooks:
            try:
                hook(pipeline, context)
            except Exception as e:
                logger.warning(f"Post-pipeline hook失败: {e}")
    
    def trigger_pre_module_hooks(self, module: PipelineModule, context: PipelineContext):
        """触发模块执行前钩子"""
        if not self.enable_hooks:
            return
        for hook in self._pre_module_hooks:
            try:
                hook(module, context)
            except Exception as e:
                logger.warning(f"Pre-module hook失败: {e}")
    
    def trigger_post_module_hooks(self, module: PipelineModule, context: PipelineContext):
        """触发模块执行后钩子"""
        if not self.enable_hooks:
            return
        for hook in self._post_module_hooks:
            try:
                hook(module, context)
            except Exception as e:
                logger.warning(f"Post-module hook失败: {e}")
    
    def trigger_error_hooks(self, module: PipelineModule, context: PipelineContext, error: Exception):
        """触发错误钩子"""
        if not self.enable_hooks:
            return
        for hook in self._error_hooks:
            try:
                hook(module, context, error)
            except Exception as e:
                logger.warning(f"Error hook失败: {e}")

