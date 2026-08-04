"""
导入进度管理器：管理 GitHub 导入流程的进度状态和取消机制

主要功能：
- ImportStage: 导入阶段枚举
- ImportProgressManager: 进度管理器，追踪阶段、进度、日志
- 支持阶段性取消点

执行流程：
1. 创建进度管理器
2. 各阶段开始/结束时调用更新方法
3. 在安全点检查取消标志
4. 收集日志供前端展示
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Callable
import threading

from backend.infrastructure.logger import get_logger

logger = get_logger('import_progress')


class ImportStage(Enum):
    """导入阶段枚举"""
    IDLE = ("idle", "空闲", False)
    PREFLIGHT = ("preflight", "仓库预检", False)
    GIT_CLONE = ("git_clone", "克隆仓库", False)  # 不可量化
    FILE_WALK = ("file_walk", "扫描文件", False)  # 不可量化（总数未知）
    DOC_PARSE = ("doc_parse", "解析文档", True)   # 可量化
    VECTORIZE = ("vectorize", "生成向量", True)   # 可量化
    COMPLETE = ("complete", "完成", False)
    FAILED = ("failed", "失败", False)
    CANCELLED = ("cancelled", "已取消", False)
    
    def __init__(self, stage_id: str, display_name: str, quantifiable: bool):
        self.stage_id = stage_id
        self.display_name = display_name
        self.quantifiable = quantifiable  # 是否可量化进度


@dataclass
class LogEntry:
    """日志条目"""
    timestamp: datetime
    level: str  # info, success, warning, error
    message: str
    
    def format(self) -> str:
        """格式化日志条目"""
        time_str = self.timestamp.strftime("%H:%M:%S")
        icon_map = {
            "info": "🔄",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌"
        }
        icon = icon_map.get(self.level, "📝")
        return f"{time_str} {icon} {self.message}"


@dataclass
class StageProgress:
    """阶段进度"""
    stage: ImportStage
    current: int = 0
    total: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @property
    def progress_ratio(self) -> float:
        """进度比例 (0.0 - 1.0)"""
        if not self.stage.quantifiable or self.total == 0:
            return 0.0
        return min(self.current / self.total, 1.0)
    
    @property
    def progress_percent(self) -> int:
        """进度百分比 (0 - 100)"""
        return int(self.progress_ratio * 100)
    
    @property
    def elapsed_seconds(self) -> float:
        """已耗时（秒）"""
        if not self.start_time:
            return 0.0
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()


class ImportProgressManager:
    """导入进度管理器
    
    管理导入流程的进度状态、日志收集和取消机制。
    线程安全，可在多线程环境中使用。
    """
    
    # 阶段顺序（用于计算总进度）
    STAGE_ORDER = [
        ImportStage.PREFLIGHT,
        ImportStage.GIT_CLONE,
        ImportStage.FILE_WALK,
        ImportStage.DOC_PARSE,
        ImportStage.VECTORIZE,
        ImportStage.COMPLETE
    ]
    
    def __init__(self, owner: str, repo: str, branch: str = "main"):
        """初始化进度管理器
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            branch: 分支名称
        """
        self.owner = owner
        self.repo = repo
        self.branch = branch
        
        self._lock = threading.Lock()
        self._cancelled = False
        self._current_stage = ImportStage.IDLE
        self._stage_progress: dict[ImportStage, StageProgress] = {}
        self._logs: List[LogEntry] = []
        self._error_message: Optional[str] = None
        self._on_update_callbacks: List[Callable] = []
        
        # 初始化各阶段进度
        for stage in self.STAGE_ORDER:
            self._stage_progress[stage] = StageProgress(stage=stage)
    
    @property
    def repository_name(self) -> str:
        """仓库全名"""
        return f"{self.owner}/{self.repo}@{self.branch}"
    
    @property
    def current_stage(self) -> ImportStage:
        """当前阶段"""
        with self._lock:
            return self._current_stage
    
    @property
    def is_cancelled(self) -> bool:
        """是否已取消"""
        with self._lock:
            return self._cancelled
    
    @property
    def is_complete(self) -> bool:
        """是否已完成"""
        with self._lock:
            return self._current_stage in (
                ImportStage.COMPLETE,
                ImportStage.FAILED,
                ImportStage.CANCELLED
            )
    
    @property
    def logs(self) -> List[LogEntry]:
        """获取日志列表的副本"""
        with self._lock:
            return list(self._logs)
    
    @property
    def formatted_logs(self) -> List[str]:
        """获取格式化的日志列表"""
        return [log.format() for log in self.logs]
    
    @property
    def current_stage_index(self) -> int:
        """当前阶段索引 (1-based)"""
        try:
            return self.STAGE_ORDER.index(self._current_stage) + 1
        except ValueError:
            return 0
    
    @property
    def total_stages(self) -> int:
        """总阶段数（不含 COMPLETE）"""
        return len(self.STAGE_ORDER) - 1  # 排除 COMPLETE
    
    def get_stage_progress(self, stage: ImportStage) -> StageProgress:
        """获取指定阶段的进度"""
        with self._lock:
            return self._stage_progress.get(stage, StageProgress(stage=stage))
    
    def get_current_progress(self) -> StageProgress:
        """获取当前阶段的进度"""
        return self.get_stage_progress(self._current_stage)
    
    # === 阶段控制方法 ===
    
    def start_stage(self, stage: ImportStage, total: int = 0):
        """开始一个阶段
        
        Args:
            stage: 阶段
            total: 总数（可量化阶段需要）
        """
        with self._lock:
            self._current_stage = stage
            progress = self._stage_progress[stage]
            progress.start_time = datetime.now()
            progress.total = total
            progress.current = 0
        
        self._add_log("info", f"开始: {stage.display_name}")
        logger.info(f"[进度] 开始阶段: {stage.display_name}")
        self._notify_update()
    
    def update_progress(self, current: int, message: Optional[str] = None):
        """更新当前阶段进度
        
        Args:
            current: 当前进度
            message: 可选的日志消息
        """
        with self._lock:
            stage = self._current_stage
            if stage in self._stage_progress:
                self._stage_progress[stage].current = current
        
        if message:
            self._add_log("info", message)
        
        self._notify_update()
    
    def complete_stage(self, stage: ImportStage, message: Optional[str] = None):
        """完成一个阶段
        
        Args:
            stage: 阶段
            message: 可选的完成消息
        """
        with self._lock:
            if stage in self._stage_progress:
                progress = self._stage_progress[stage]
                progress.end_time = datetime.now()
                if progress.total > 0:
                    progress.current = progress.total
        
        log_msg = message or f"完成: {stage.display_name}"
        self._add_log("success", log_msg)
        logger.info(f"[进度] 阶段完成: {stage.display_name}")
        self._notify_update()
    
    def complete_import(self, message: str = "导入完成"):
        """标记导入完成"""
        with self._lock:
            self._current_stage = ImportStage.COMPLETE
        self._add_log("success", message)
        logger.info(f"[进度] 导入完成: {self.repository_name}")
        self._notify_update()
    
    def fail_import(self, error_message: str):
        """标记导入失败"""
        with self._lock:
            self._current_stage = ImportStage.FAILED
            self._error_message = error_message
        self._add_log("error", error_message)
        logger.error(f"[进度] 导入失败: {error_message}")
        self._notify_update()
    
    # === 取消机制 ===
    
    def request_cancel(self):
        """请求取消导入"""
        with self._lock:
            self._cancelled = True
        self._add_log("warning", "用户请求取消")
        logger.info(f"[进度] 收到取消请求: {self.repository_name}")
    
    def check_cancelled(self) -> bool:
        """检查是否已取消（安全点调用）
        
        Returns:
            是否已取消
        """
        if self.is_cancelled:
            with self._lock:
                if self._current_stage not in (ImportStage.CANCELLED, ImportStage.FAILED):
                    self._current_stage = ImportStage.CANCELLED
            self._add_log("warning", "导入已取消")
            logger.info(f"[进度] 导入已取消: {self.repository_name}")
            self._notify_update()
            return True
        return False
    
    # === 日志方法 ===
    
    def log_info(self, message: str):
        """记录信息日志"""
        self._add_log("info", message)
    
    def log_success(self, message: str):
        """记录成功日志"""
        self._add_log("success", message)
    
    def log_warning(self, message: str):
        """记录警告日志"""
        self._add_log("warning", message)
    
    def log_error(self, message: str):
        """记录错误日志"""
        self._add_log("error", message)
    
    def _add_log(self, level: str, message: str):
        """添加日志条目"""
        entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            message=message
        )
        with self._lock:
            self._logs.append(entry)
            # 限制日志数量，避免内存过大
            if len(self._logs) > 100:
                self._logs = self._logs[-100:]
    
    # === 回调机制 ===
    
    def on_update(self, callback: Callable):
        """注册更新回调
        
        Args:
            callback: 回调函数，无参数
        """
        self._on_update_callbacks.append(callback)
    
    def _notify_update(self):
        """通知所有回调"""
        for callback in self._on_update_callbacks:
            try:
                callback()
            except Exception as e:
                logger.warning(f"[进度] 回调执行失败: {e}")
    
    # === 序列化方法（用于前端展示）===
    
    def to_dict(self) -> dict:
        """转换为字典（用于前端）"""
        current_progress = self.get_current_progress()
        
        return {
            "repository": self.repository_name,
            "current_stage": self._current_stage.stage_id,
            "current_stage_name": self._current_stage.display_name,
            "current_stage_index": self.current_stage_index,
            "total_stages": self.total_stages,
            "is_quantifiable": self._current_stage.quantifiable,
            "progress_current": current_progress.current,
            "progress_total": current_progress.total,
            "progress_percent": current_progress.progress_percent,
            "elapsed_seconds": current_progress.elapsed_seconds,
            "is_cancelled": self.is_cancelled,
            "is_complete": self.is_complete,
            "logs": self.formatted_logs,
            "error_message": self._error_message
        }
