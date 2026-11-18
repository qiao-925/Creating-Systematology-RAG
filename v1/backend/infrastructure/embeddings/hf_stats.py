"""
HuggingFace API 调用统计模块

主要功能：
- 全局和按任务维度的 API 调用统计
- 独立日志文件记录（仅任务完成时输出）
- 定时汇总输出（仅当有变化时）

日志输出时机：
- 任务完成时：输出该任务的完整统计
- 定期汇总（30秒）：仅当有新调用时输出

使用方式：
- 在查询入口设置任务 ID: set_current_task_id(session_id)
- 任务完成时调用: finish_task(session_id)
- 获取统计: get_stats(), get_task_stats(task_id)
"""

import logging
import threading
import contextvars
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional
from logging.handlers import RotatingFileHandler


# ============================================================
# 上下文变量：用于在调用链中传递任务 ID
# ============================================================

current_task_id: contextvars.ContextVar[str] = contextvars.ContextVar(
    'hf_task_id', default='global'
)


def set_current_task_id(task_id: str) -> contextvars.Token:
    """设置当前任务 ID"""
    return current_task_id.set(task_id or 'anonymous')


def get_current_task_id() -> str:
    """获取当前任务 ID"""
    return current_task_id.get()


# ============================================================
# 统计数据模型
# ============================================================

@dataclass
class HFAPIStats:
    """单个统计记录"""
    call_count: int = 0
    text_count: int = 0
    total_time: float = 0.0
    first_call_time: Optional[datetime] = None
    last_call_time: Optional[datetime] = None
    
    def record(self, text_count: int, elapsed_time: float) -> None:
        """记录一次调用"""
        now = datetime.now()
        self.call_count += 1
        self.text_count += text_count
        self.total_time += elapsed_time
        self.last_call_time = now
        if self.first_call_time is None:
            self.first_call_time = now
    
    def reset(self) -> None:
        """重置统计"""
        self.call_count = 0
        self.text_count = 0
        self.total_time = 0.0
        self.first_call_time = None
        self.last_call_time = None
    
    @property
    def avg_time_per_call(self) -> float:
        """平均每次调用耗时"""
        return self.total_time / self.call_count if self.call_count > 0 else 0.0
    
    @property
    def avg_time_per_text(self) -> float:
        """平均每个文本耗时"""
        return self.total_time / self.text_count if self.text_count > 0 else 0.0


# ============================================================
# 日志配置
# ============================================================

def _get_stats_logger() -> logging.Logger:
    """获取统计专用 logger"""
    logger = logging.getLogger('hf_api_stats')
    
    if not logger.handlers:
        project_root = Path(__file__).parent.parent.parent.parent
        log_dir = project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "hf_api_stats.log"
        
        handler = RotatingFileHandler(
            filename=str(log_file),
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8',
        )
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    
    return logger


# ============================================================
# 统计收集器（单例）
# ============================================================

class HFAPIStatsCollector:
    """HF API 统计收集器
    
    日志策略：
    - 不记录每次调用明细（减少噪音）
    - 任务完成时输出该任务统计
    - 定期汇总仅当有新调用时输出
    """
    
    _instance: Optional['HFAPIStatsCollector'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'HFAPIStatsCollector':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        if self._initialized:
            return
        
        self._data_lock = threading.Lock()
        self._global_stats = HFAPIStats()
        self._task_stats: Dict[str, HFAPIStats] = {}
        self._active_tasks: set = set()
        self._logger = _get_stats_logger()
        
        # 定时器相关
        self._timer: Optional[threading.Timer] = None
        self._timer_interval = 30.0  # 30 秒（减少频率）
        self._timer_running = False
        
        # 用于检测是否有新调用
        self._last_logged_call_count = 0
        
        self._initialized = True
    
    def record(self, text_count: int, elapsed_time: float) -> None:
        """记录一次 API 调用（不输出明细日志）"""
        task_id = get_current_task_id()
        
        with self._data_lock:
            self._global_stats.record(text_count, elapsed_time)
            
            if task_id not in self._task_stats:
                self._task_stats[task_id] = HFAPIStats()
            self._task_stats[task_id].record(text_count, elapsed_time)
            
            if task_id != 'global':
                self._active_tasks.add(task_id)
                self._ensure_timer_running()
    
    def _ensure_timer_running(self) -> None:
        """确保定时器运行"""
        if not self._timer_running and self._active_tasks:
            self._start_timer()
    
    def _start_timer(self) -> None:
        """启动定时器"""
        if self._timer_running:
            return
        self._timer_running = True
        self._schedule_next_summary()
    
    def _schedule_next_summary(self) -> None:
        """调度下一次汇总"""
        if not self._timer_running:
            return
        self._timer = threading.Timer(self._timer_interval, self._periodic_summary)
        self._timer.daemon = True
        self._timer.start()
    
    def _periodic_summary(self) -> None:
        """定期汇总输出（仅当有新调用时）"""
        with self._data_lock:
            if not self._active_tasks:
                self._timer_running = False
                return
            
            # 只有当有新调用时才输出
            current_count = self._global_stats.call_count
            if current_count > self._last_logged_call_count:
                self._log_summary()
                self._last_logged_call_count = current_count
        
        if self._timer_running:
            self._schedule_next_summary()
    
    def _log_summary(self) -> None:
        """输出汇总日志（格式化表格）"""
        lines = [
            "",
            "┌─────────────────────────────────────────────────────────────┐",
            "│                  HF API 调用统计汇总                        │",
            "├─────────────────────────────────────────────────────────────┤",
        ]
        
        # 全局统计
        g = self._global_stats
        lines.append(
            f"│ 全局总计: {g.call_count:>4} 次调用 | {g.text_count:>6} 文本 | "
            f"{g.total_time:>7.1f}s | {g.avg_time_per_text:.2f}s/文本 │"
        )
        
        # 活跃任务统计
        if self._active_tasks:
            lines.append("├─────────────────────────────────────────────────────────────┤")
            lines.append("│ 活跃任务:                                                   │")
            for task_id in sorted(self._active_tasks):
                if task_id in self._task_stats:
                    s = self._task_stats[task_id]
                    task_display = task_id[:20] if len(task_id) > 20 else task_id
                    lines.append(
                        f"│   {task_display:<20} {s.call_count:>3}次 | {s.text_count:>5}文本 | {s.total_time:>6.1f}s │"
                    )
        
        lines.append("└─────────────────────────────────────────────────────────────┘")
        self._logger.info("\n".join(lines))
    
    def finish_task(self, task_id: str) -> Optional[HFAPIStats]:
        """标记任务完成，输出最终统计"""
        with self._data_lock:
            self._active_tasks.discard(task_id)
            
            if task_id in self._task_stats:
                stats = self._task_stats[task_id]
                if stats.call_count > 0:  # 只有有调用时才输出
                    self._log_task_complete(task_id, stats)
                
                return HFAPIStats(
                    call_count=stats.call_count,
                    text_count=stats.text_count,
                    total_time=stats.total_time,
                    first_call_time=stats.first_call_time,
                    last_call_time=stats.last_call_time,
                )
            
            if not self._active_tasks:
                self._timer_running = False
        
        return None
    
    def _log_task_complete(self, task_id: str, stats: HFAPIStats) -> None:
        """记录任务完成统计（格式化）"""
        duration_str = ""
        if stats.first_call_time and stats.last_call_time:
            delta = (stats.last_call_time - stats.first_call_time).total_seconds()
            duration_str = f" | 任务耗时: {delta:.1f}s"
        
        self._logger.info(
            f"\n══════════════════════════════════════════════════════════════\n"
            f"  任务完成: {task_id}\n"
            f"  ────────────────────────────────────────────────────────────\n"
            f"  API调用: {stats.call_count} 次 | 文本数: {stats.text_count}\n"
            f"  API耗时: {stats.total_time:.2f}s | 平均: {stats.avg_time_per_text:.3f}s/文本{duration_str}\n"
            f"══════════════════════════════════════════════════════════════"
        )
    
    def get_global_stats(self) -> HFAPIStats:
        """获取全局统计（副本）"""
        with self._data_lock:
            g = self._global_stats
            return HFAPIStats(
                call_count=g.call_count,
                text_count=g.text_count,
                total_time=g.total_time,
                first_call_time=g.first_call_time,
                last_call_time=g.last_call_time,
            )
    
    def get_task_stats(self, task_id: str) -> Optional[HFAPIStats]:
        """获取指定任务的统计（副本）"""
        with self._data_lock:
            if task_id in self._task_stats:
                s = self._task_stats[task_id]
                return HFAPIStats(
                    call_count=s.call_count,
                    text_count=s.text_count,
                    total_time=s.total_time,
                    first_call_time=s.first_call_time,
                    last_call_time=s.last_call_time,
                )
        return None
    
    def shutdown(self) -> None:
        """关闭收集器"""
        self._timer_running = False
        if self._timer:
            self._timer.cancel()
            self._timer = None


# ============================================================
# 便捷函数
# ============================================================

def get_collector() -> HFAPIStatsCollector:
    """获取统计收集器实例"""
    return HFAPIStatsCollector()


def record_api_call(text_count: int, elapsed_time: float) -> None:
    """记录一次 API 调用"""
    get_collector().record(text_count, elapsed_time)


def finish_task(task_id: str) -> Optional[HFAPIStats]:
    """标记任务完成"""
    return get_collector().finish_task(task_id)


def get_stats() -> HFAPIStats:
    """获取全局统计"""
    return get_collector().get_global_stats()


def get_task_stats(task_id: str) -> Optional[HFAPIStats]:
    """获取任务统计"""
    return get_collector().get_task_stats(task_id)
