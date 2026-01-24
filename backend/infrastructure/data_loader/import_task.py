"""
后台导入任务：封装 GitHub 导入流程，支持后台执行和进度查询

主要功能：
- ImportTask: 后台导入任务类
- 支持启动、取消、进度查询
- 线程安全的状态管理

使用方式：
1. task = ImportTask.start(owner, repo, branch, index_manager, github_sync_manager)
2. while not task.is_complete:
       progress = task.get_progress()
       render_progress(progress)
       time.sleep(1)
3. result = task.get_result()
"""

import threading
import traceback
from typing import Optional, Dict, Any, TYPE_CHECKING

from backend.infrastructure.logger import get_logger
from backend.infrastructure.data_loader.progress import ImportProgressManager, ImportStage
from backend.infrastructure.data_loader.github_preflight import check_repository

if TYPE_CHECKING:
    from backend.infrastructure.indexer.service import IndexService
    from backend.infrastructure.data_loader.github_sync.manager import GitHubSyncManager

logger = get_logger('import_task')


class ImportTask:
    """后台导入任务
    
    封装 GitHub 导入的完整流程，在后台线程执行，
    支持实时进度查询和取消操作。
    """
    
    def __init__(
        self,
        owner: str,
        repo: str,
        branch: str,
        index_manager: "IndexService",
        github_sync_manager: "GitHubSyncManager"
    ):
        """初始化导入任务（不直接调用，使用 start() 类方法）
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            branch: 分支名称
            index_manager: 索引管理器
            github_sync_manager: GitHub 同步管理器
        """
        self.owner = owner
        self.repo = repo
        self.branch = branch
        self.index_manager = index_manager
        self.github_sync_manager = github_sync_manager
        
        # 进度管理器
        self.progress_manager = ImportProgressManager(owner, repo, branch)
        
        # 任务状态
        self._thread: Optional[threading.Thread] = None
        self._result: Optional[Dict[str, Any]] = None
        self._error: Optional[str] = None
        self._documents_count: int = 0
    
    @classmethod
    def start(
        cls,
        owner: str,
        repo: str,
        branch: str,
        index_manager: "IndexService",
        github_sync_manager: "GitHubSyncManager"
    ) -> "ImportTask":
        """启动导入任务
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            branch: 分支名称
            index_manager: 索引管理器
            github_sync_manager: GitHub 同步管理器
            
        Returns:
            ImportTask 实例
        """
        task = cls(owner, repo, branch, index_manager, github_sync_manager)
        task._thread = threading.Thread(target=task._run, daemon=True)
        task._thread.start()
        logger.info(f"[ImportTask] 启动导入任务: {owner}/{repo}@{branch}")
        return task
    
    @property
    def is_complete(self) -> bool:
        """任务是否完成（成功、失败或取消）"""
        return self.progress_manager.is_complete
    
    @property
    def is_success(self) -> bool:
        """任务是否成功"""
        return self.progress_manager.current_stage == ImportStage.COMPLETE
    
    @property
    def error_message(self) -> Optional[str]:
        """错误消息"""
        return self._error
    
    @property
    def documents_count(self) -> int:
        """导入的文档数量"""
        return self._documents_count
    
    def get_progress(self) -> Dict[str, Any]:
        """获取当前进度
        
        Returns:
            进度字典，包含阶段、进度、日志等信息
        """
        return self.progress_manager.to_dict()
    
    def cancel(self):
        """请求取消任务"""
        self.progress_manager.request_cancel()
        logger.info(f"[ImportTask] 收到取消请求: {self.owner}/{self.repo}")
    
    def _run(self):
        """后台线程执行的导入流程"""
        pm = self.progress_manager
        
        try:
            # 阶段 1: 仓库预检
            pm.start_stage(ImportStage.PREFLIGHT)
            
            preflight_result = check_repository(self.owner, self.repo)
            
            if not preflight_result.success:
                pm.fail_import(f"预检失败: {preflight_result.error_message}")
                self._error = preflight_result.error_message
                return
            
            pm.log_success(f"预检通过 (大小: {preflight_result.size_mb:.1f}MB)")
            pm.complete_stage(ImportStage.PREFLIGHT)
            
            # 检查取消
            if pm.check_cancelled():
                return
            
            # 阶段 2: 克隆/同步仓库
            pm.start_stage(ImportStage.GIT_CLONE)
            
            from backend.infrastructure.data_loader import sync_github_repository
            
            documents, changes, commit_sha = sync_github_repository(
                owner=self.owner,
                repo=self.repo,
                branch=self.branch,
                github_sync_manager=self.github_sync_manager,
                show_progress=False
            )
            
            if commit_sha:
                pm.log_success(f"仓库同步完成 (Commit: {commit_sha[:8]})")
            pm.complete_stage(ImportStage.GIT_CLONE)
            
            # 检查取消
            if pm.check_cancelled():
                return
            
            if not documents:
                pm.fail_import("未能加载任何文件")
                self._error = "未能加载任何文件"
                return
            
            self._documents_count = len(documents)
            pm.log_info(f"加载了 {self._documents_count} 个文档")
            
            # 阶段 3: 构建索引（最耗时，支持进度回调）
            pm.start_stage(ImportStage.VECTORIZE, total=100)  # 假设 100%
            
            def progress_callback(current: int, total: int):
                """索引构建进度回调"""
                percent = int(current / total * 100) if total > 0 else 0
                pm.update_progress(percent, f"向量化: {current}/{total} 节点")
            
            index, vector_ids_map = self.index_manager.build_index(
                documents,
                show_progress=False,
                github_sync_manager=self.github_sync_manager,
                progress_callback=progress_callback
            )
            
            pm.complete_stage(ImportStage.VECTORIZE)
            
            # 检查取消
            if pm.check_cancelled():
                return
            
            # 阶段 4: 保存状态
            pm.log_info("保存同步状态...")
            
            self.github_sync_manager.update_repository_sync_state(
                owner=self.owner,
                repo=self.repo,
                branch=self.branch,
                documents=documents,
                vector_ids_map=vector_ids_map,
                commit_sha=commit_sha
            )
            
            # 完成
            pm.complete_import(f"成功导入 {self._documents_count} 个文档")
            
            self._result = {
                "success": True,
                "documents_count": self._documents_count,
                "commit_sha": commit_sha,
            }
            
            logger.info(f"[ImportTask] 导入完成: {self.owner}/{self.repo}, {self._documents_count} 个文档")
            
        except Exception as e:
            error_msg = str(e)[:200]
            pm.fail_import(error_msg)
            self._error = error_msg
            logger.error(f"[ImportTask] 导入失败: {error_msg}")
            logger.debug(f"[ImportTask] 详细错误:\n{traceback.format_exc()}")
