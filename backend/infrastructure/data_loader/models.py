"""
数据导入模型：数据类和辅助类

主要功能：
- ImportResult：导入结果数据类
- ProgressReporter：进度反馈器
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any

from llama_index.core.schema import Document as LlamaDocument

from backend.infrastructure.logger import get_logger
from backend.infrastructure.data_loader.processor import safe_print

logger = get_logger('data_loader_service')


@dataclass
class ImportResult:
    """导入结果"""
    documents: List[LlamaDocument]
    success: bool
    stats: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class ProgressReporter:
    """进度反馈器"""
    
    def __init__(self, show_progress: bool = True):
        """初始化进度反馈器
        
        Args:
            show_progress: 是否显示进度
        """
        self.show_progress = show_progress
    
    def report_stage(self, stage: str, message: str):
        """报告阶段信息
        
        Args:
            stage: 阶段名称
            message: 消息内容
        """
        if self.show_progress:
            safe_print(f"{stage} {message}")
        logger.info(f"[{stage}] {message}")
    
    def report_progress(self, current: int, total: int, message: str = ""):
        """报告进度
        
        Args:
            current: 当前进度
            total: 总数
            message: 附加消息
        """
        if self.show_progress:
            progress_msg = f"进度: {current}/{total}"
            if message:
                progress_msg += f" - {message}"
            safe_print(progress_msg)
        logger.debug(f"进度: {current}/{total} {message}")
    
    def report_success(self, message: str):
        """报告成功
        
        Args:
            message: 成功消息
        """
        if self.show_progress:
            safe_print(f"✅ {message}")
        logger.info(f"成功: {message}")
    
    def report_error(self, message: str):
        """报告错误
        
        Args:
            message: 错误消息
        """
        if self.show_progress:
            safe_print(f"❌ {message}")
        logger.error(f"错误: {message}")
    
    def report_warning(self, message: str):
        """报告警告
        
        Args:
            message: 警告消息
        """
        if self.show_progress:
            safe_print(f"⚠️  {message}")
        logger.warning(f"警告: {message}")
    
    def print_if_enabled(self, message: str):
        """如果启用进度显示则打印消息（简化版）
        
        Args:
            message: 消息内容
        """
        if self.show_progress:
            safe_print(message)
