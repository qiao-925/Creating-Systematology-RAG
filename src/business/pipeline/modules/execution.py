"""
Pipeline执行器 - 执行核心模块
Pipeline执行核心逻辑
"""

from typing import List, Optional
from dataclasses import dataclass

from src.business.protocols import PipelineModule, PipelineContext, Pipeline
from src.logger import setup_logger

logger = setup_logger('pipeline_executor')


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    context: PipelineContext
    execution_time: float = 0.0
    modules_executed: List[str] = None
    errors: List[str] = None
    
    def __post_init__(self):
        if self.modules_executed is None:
            self.modules_executed = []
        if self.errors is None:
            self.errors = []


class PipelineExecutorCore:
    """Pipeline执行核心"""
    
    def __init__(
        self,
        stop_on_error: bool = False,
        max_execution_time: Optional[float] = None,
    ):
        """初始化执行核心"""
        self.stop_on_error = stop_on_error
        self.max_execution_time = max_execution_time
    
    def execute(
        self,
        pipeline: Pipeline,
        context: PipelineContext,
        hook_manager,
    ) -> ExecutionResult:
        """执行流水线核心逻辑"""
        import time
        start_time = time.time()
        modules_executed = []
        
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
                hook_manager.trigger_pre_module_hooks(module, context)
                
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
                hook_manager.trigger_post_module_hooks(module, context)
                
            except Exception as e:
                logger.error(f"模块执行失败: {module.name}, error={e}", exc_info=True)
                
                # 调用模块错误处理
                module.on_error(context, e)
                
                # 调用全局错误钩子
                hook_manager.trigger_error_hooks(module, context, e)
                
                # 根据配置决定是否继续
                if self.stop_on_error:
                    logger.error("遇到错误，停止执行")
                    break
        
        execution_time = time.time() - start_time
        success = not context.has_errors()
        
        return ExecutionResult(
            success=success,
            context=context,
            execution_time=execution_time,
            modules_executed=modules_executed,
            errors=context.errors,
        )

