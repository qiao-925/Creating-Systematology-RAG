"""
Pipeline执行器 - 核心执行模块
PipelineExecutor类实现
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable
import time

from src.business.protocols import (
    PipelineModule,
    PipelineContext,
    Pipeline,
    ModuleList,
)
from src.logger import setup_logger
from src.business.pipeline.modules.execution import PipelineExecutorCore, ExecutionResult
from src.business.pipeline.modules.hooks import HookManager

logger = setup_logger('pipeline_executor')


class PipelineExecutor:
    """流水线执行器"""
    
    def __init__(
        self,
        enable_hooks: bool = True,
        stop_on_error: bool = False,
        max_execution_time: Optional[float] = None,
    ):
        """初始化执行器"""
        self.enable_hooks = enable_hooks
        self.stop_on_error = stop_on_error
        self.max_execution_time = max_execution_time
        
        self.hook_manager = HookManager(enable_hooks)
        self.executor_core = PipelineExecutorCore(
            stop_on_error=stop_on_error,
            max_execution_time=max_execution_time
        )
        
        logger.info(f"PipelineExecutor初始化: hooks={enable_hooks}, stop_on_error={stop_on_error}")
    
    def execute(
        self,
        pipeline: Pipeline,
        context: PipelineContext,
    ) -> ExecutionResult:
        """执行流水线"""
        start_time = time.time()
        
        logger.info(f"开始执行流水线: {pipeline.name}, modules={len(pipeline.modules)}")
        
        # 执行前钩子
        if self.enable_hooks:
            self.hook_manager.trigger_pre_pipeline_hooks(pipeline, context)
        
        try:
            result = self.executor_core.execute(pipeline, context, self.hook_manager)
            
            execution_time = time.time() - start_time
            result.execution_time = execution_time
            
            # 执行后钩子
            if self.enable_hooks:
                self.hook_manager.trigger_post_pipeline_hooks(pipeline, context)
            
            logger.info(
                f"流水线执行完成: success={result.success}, time={execution_time:.3f}s, "
                f"modules={len(result.modules_executed)}/{len(pipeline.modules)}"
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
                modules_executed=[],
                errors=context.errors,
            )
    
    # === 钩子管理 ===
    
    def add_pre_pipeline_hook(self, hook: Callable):
        """添加流水线执行前钩子"""
        self.hook_manager.add_pre_pipeline_hook(hook)
    
    def add_post_pipeline_hook(self, hook: Callable):
        """添加流水线执行后钩子"""
        self.hook_manager.add_post_pipeline_hook(hook)
    
    def add_pre_module_hook(self, hook: Callable):
        """添加模块执行前钩子"""
        self.hook_manager.add_pre_module_hook(hook)
    
    def add_post_module_hook(self, hook: Callable):
        """添加模块执行后钩子"""
        self.hook_manager.add_post_module_hook(hook)
    
    def add_error_hook(self, hook: Callable):
        """添加错误钩子"""
        self.hook_manager.add_error_hook(hook)


# 便捷函数
def create_simple_rag_pipeline(
    retrieval_module: PipelineModule,
    generation_module: PipelineModule,
    formatting_module: Optional[PipelineModule] = None,
    name: str = "simple_rag",
) -> Pipeline:
    """创建简单RAG流水线"""
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
    """创建高级RAG流水线"""
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
