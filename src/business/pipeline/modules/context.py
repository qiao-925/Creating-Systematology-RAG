"""
Pipeline执行器 - 上下文管理模块
执行上下文管理
"""

from typing import Dict, Any, Optional

from src.logger import setup_logger

logger = setup_logger('pipeline_executor')


class ExecutionContext:
    """执行上下文"""
    
    def __init__(self):
        """初始化执行上下文"""
        self._inputs: Dict[str, Any] = {}
        self._step_results: Dict[str, Any] = {}
    
    def reset(self):
        """重置上下文"""
        self._inputs.clear()
        self._step_results.clear()
    
    def set_input(self, key: str, value: Any):
        """设置输入值"""
        self._inputs[key] = value
    
    def get_input(self, key: str) -> Optional[Any]:
        """获取输入值"""
        return self._inputs.get(key)
    
    def set_step_result(self, step_name: str, result: Any):
        """设置步骤结果"""
        self._step_results[step_name] = result
    
    def get_step_result(self, step_name: str) -> Optional[Any]:
        """获取步骤结果"""
        return self._step_results.get(step_name)
    
    def get_results(self) -> Dict[str, Any]:
        """获取所有结果"""
        return {
            'inputs': self._inputs.copy(),
            'step_results': self._step_results.copy()
        }

