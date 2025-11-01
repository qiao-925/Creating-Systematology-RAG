"""
流水线执行器

负责编排和执行能力模块，实现模块化的RAG流程
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime
import time

from src.business.protocols import (
    PipelineModule,
    PipelineContext,
    ModuleType,
    ModuleList,
)
from src.logger import setup_logger

logger = setup_logger('pipeline_executor')


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    context: PipelineContext
    execution_time: float
    modules_executed: List[str]
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "execution_time": self.execution_time,
            "modules_executed": self.modules_executed,
            "errors": self.errors,
            "has_errors": len(self.errors) > 0,
        }


@dataclass
class Pipeline:
    """流水线定义
    
    包含模块列表和执行配置
    """
    name: str
    modules: ModuleList
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


class PipelineExecutor:
    """流水线执行器
    
    负责按顺序执行流水线中的各个模块
    支持事件钩子、错误处理、性能监控
    
    Examples:
        >>> executor = PipelineExecutor()
        >>> pipeline = Pipeline(name="rag", modules=[retrieval, generation])
        >>> context = PipelineContext(query="问题")
        >>> result = executor.execute(pipeline, context)
        >>> print(result.context.formatted_answer)
    """
    
    def __init__(
        self,
        enable_hooks: bool = True,
        stop_on_error: bool = False,
        max_execution_time: Optional[float] = None,
    ):
        """初始化执行器
        
        Args:
            enable_hooks: 是否启用事件钩子
            stop_on_error: 遇到错误是否停止（False继续执行）
            max_execution_time: 最大执行时间（秒），超时则中止
        """
        self.enable_hooks = enable_hooks
        self.stop_on_error = stop_on_error
        self.max_execution_time = max_execution_time
        
        # 事件钩子
        self._pre_pipeline_hooks: List[Callable] = []
        self._post_pipeline_hooks: List[Callable] = []
        self._pre_module_hooks: List[Callable] = []
        self._post_module_hooks: List[Callable] = []
        self._error_hooks: List[Callable] = []
        
        logger.info(f"PipelineExecutor初始化: hooks={enable_hooks}, stop_on_error={stop_on_error}")
    
    def execute(
        self,
        pipeline: Pipeline,
        context: PipelineContext,
    ) -> ExecutionResult:
        """执行流水线
        
        Args:
            pipeline: 流水线定义
            context: 初始上下文
            
        Returns:
            ExecutionResult: 执行结果
        """
        start_time = time.time()
        modules_executed = []
        
        logger.info(f"开始执行流水线: {pipeline.name}, modules={len(pipeline.modules)}")
        
        # 执行前钩子
        if self.enable_hooks:
            self._trigger_pre_pipeline_hooks(pipeline, context)
        
        try:
            # 按顺序执行模块
            for i, module in enumerate(pipeline.modules):
                # 检查超时
                if self.max_execution_time:
                    elapsed = time.time() - start_time
                    if elapsed > self.max_execution_time:
                        error_msg = f"流水线执行超时: {elapsed:.2f}s > {self.max_execution_time}s"
                        logger.error(error_msg)
                        context.set_error(error_msg)
                        break
                
                # 执行模块
                try:
                    logger.debug(f"执行模块 [{i+1}/{len(pipeline.modules)}]: {module.name}")
                    
                    # 执行前钩子
                    if self.enable_hooks:
                        self._trigger_pre_module_hooks(module, context)
                    
                    # 检查是否应该执行
                    should_execute = module.pre_execute(context)
                    if not should_execute:
                        logger.info(f"跳过模块: {module.name}")
                        continue
                    
                    # 执行模块
                    context = module.execute(context)
                    modules_executed.append(module.name)
                    
                    # 执行后钩子
                    module.post_execute(context)
                    if self.enable_hooks:
                        self._trigger_post_module_hooks(module, context)
                    
                except Exception as e:
                    logger.error(f"模块执行失败: {module.name}, error={e}", exc_info=True)
                    
                    # 调用模块错误处理
                    module.on_error(context, e)
                    
                    # 调用全局错误钩子
                    if self.enable_hooks:
                        self._trigger_error_hooks(module, context, e)
                    
                    # 根据配置决定是否继续
                    if self.stop_on_error:
                        logger.error("遇到错误，停止执行")
                        break
            
            # 执行后钩子
            if self.enable_hooks:
                self._trigger_post_pipeline_hooks(pipeline, context)
            
            execution_time = time.time() - start_time
            success = not context.has_errors()
            
            result = ExecutionResult(
                success=success,
                context=context,
                execution_time=execution_time,
                modules_executed=modules_executed,
                errors=context.errors,
            )
            
            logger.info(
                f"流水线执行完成: success={success}, time={execution_time:.3f}s, "
                f"modules={len(modules_executed)}/{len(pipeline.modules)}"
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"流水线执行异常: {e}", exc_info=True)
            context.set_error(f"Pipeline execution failed: {str(e)}")
            
            return ExecutionResult(
                success=False,
                context=context,
                execution_time=execution_time,
                modules_executed=modules_executed,
                errors=context.errors,
            )
    
    # === 钩子管理 ===
    
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
    
    def _trigger_pre_pipeline_hooks(self, pipeline: Pipeline, context: PipelineContext):
        """触发流水线执行前钩子"""
        for hook in self._pre_pipeline_hooks:
            try:
                hook(pipeline, context)
            except Exception as e:
                logger.warning(f"Pre-pipeline hook失败: {e}")
    
    def _trigger_post_pipeline_hooks(self, pipeline: Pipeline, context: PipelineContext):
        """触发流水线执行后钩子"""
        for hook in self._post_pipeline_hooks:
            try:
                hook(pipeline, context)
            except Exception as e:
                logger.warning(f"Post-pipeline hook失败: {e}")
    
    def _trigger_pre_module_hooks(self, module: PipelineModule, context: PipelineContext):
        """触发模块执行前钩子"""
        for hook in self._pre_module_hooks:
            try:
                hook(module, context)
            except Exception as e:
                logger.warning(f"Pre-module hook失败: {e}")
    
    def _trigger_post_module_hooks(self, module: PipelineModule, context: PipelineContext):
        """触发模块执行后钩子"""
        for hook in self._post_module_hooks:
            try:
                hook(module, context)
            except Exception as e:
                logger.warning(f"Post-module hook失败: {e}")
    
    def _trigger_error_hooks(self, module: PipelineModule, context: PipelineContext, error: Exception):
        """触发错误钩子"""
        for hook in self._error_hooks:
            try:
                hook(module, context, error)
            except Exception as e:
                logger.warning(f"Error hook失败: {e}")


# 便捷函数

def create_simple_rag_pipeline(
    retrieval_module: PipelineModule,
    generation_module: PipelineModule,
    formatting_module: Optional[PipelineModule] = None,
    name: str = "simple_rag",
) -> Pipeline:
    """创建简单RAG流水线
    
    Args:
        retrieval_module: 检索模块
        generation_module: 生成模块
        formatting_module: 格式化模块（可选）
        name: 流水线名称
        
    Returns:
        Pipeline: 流水线对象
    """
    modules = [retrieval_module, generation_module]
    if formatting_module:
        modules.append(formatting_module)
    
    return Pipeline(
        name=name,
        modules=modules,
        description="简单RAG流水线: 检索 → 生成 → 格式化",
    )


def create_advanced_rag_pipeline(
    retrieval_module: PipelineModule,
    reranking_module: PipelineModule,
    prompt_module: PipelineModule,
    generation_module: PipelineModule,
    formatting_module: PipelineModule,
    name: str = "advanced_rag",
) -> Pipeline:
    """创建高级RAG流水线
    
    Args:
        retrieval_module: 检索模块
        reranking_module: 重排序模块
        prompt_module: 提示工程模块
        generation_module: 生成模块
        formatting_module: 格式化模块
        name: 流水线名称
        
    Returns:
        Pipeline: 流水线对象
    """
    return Pipeline(
        name=name,
        modules=[
            retrieval_module,
            reranking_module,
            prompt_module,
            generation_module,
            formatting_module,
        ],
        description="高级RAG流水线: 检索 → 重排序 → 提示工程 → 生成 → 格式化",
    )
