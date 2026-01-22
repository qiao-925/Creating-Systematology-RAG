"""
Hugging Face Inference API 实用工具

主要功能：
- TimeMonitor类：性能监控上下文管理器
"""

import time
import threading
from typing import Optional


class TimeMonitor:
    """时间监控器：后台定期打印耗时"""
    
    def __init__(
        self,
        logger_instance,
        message_template: str = "耗时 {elapsed} 秒",
        interval: float = 5.0
    ):
        """初始化时间监控器
        
        Args:
            logger_instance: logger 实例
            message_template: 日志消息模板，支持 {elapsed} 占位符
            interval: 打印间隔（秒），默认5.0秒
        """
        self.logger = logger_instance
        self.message_template = message_template
        self.interval = interval
        self.start_time: Optional[float] = None
        self.stop_event = threading.Event()
        self.thread: Optional[threading.Thread] = None
    
    def __enter__(self):
        """进入上下文，开始监控"""
        self.start_time = time.time()
        self.stop_event.clear()
        
        self.thread = threading.Thread(
            target=self._log_elapsed_time,
            daemon=True
        )
        self.thread.start()
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文，停止监控"""
        if self.thread and self.thread.is_alive():
            self.stop_event.set()
            self.thread.join(timeout=2.0)
        
        if self.start_time is not None:
            total_elapsed = time.time() - self.start_time
            if total_elapsed >= 1.0:
                final_message = self.message_template.format(elapsed=int(total_elapsed))
                self.logger.info(f"{final_message} (总计)")
            elif total_elapsed >= 0.5:
                final_message = self.message_template.format(elapsed=int(total_elapsed))
                self.logger.debug(f"{final_message} (总计)")
        
        return False
    
    def _log_elapsed_time(self):
        """后台线程函数，定期打印已花费时间"""
        last_logged_interval = -1
        
        while not self.stop_event.is_set():
            if self.start_time is None:
                break
            
            elapsed = time.time() - self.start_time
            current_interval = int(elapsed / self.interval)
            
            if current_interval > last_logged_interval and current_interval > 0:
                try:
                    elapsed_seconds = int(elapsed)
                    message = self.message_template.format(elapsed=elapsed_seconds)
                    if elapsed_seconds < 10:
                        self.logger.debug(message)
                    else:
                        self.logger.info(message)
                    last_logged_interval = current_interval
                except Exception:
                    pass
            
            self.stop_event.wait(timeout=self.interval)
