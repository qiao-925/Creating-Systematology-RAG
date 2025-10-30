"""
缓存管理器模块
负责管理GitHub导入和向量化流程的步骤级缓存
"""

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.logger import setup_logger

logger = setup_logger('cache_manager')


class CacheManager:
    """缓存管理器
    
    管理步骤级缓存状态，支持断点续传和缓存复用
    """
    
    # 步骤名称常量
    STEP_CLONE = "step_clone"
    STEP_PARSE = "step_parse"
    STEP_VECTORIZE = "step_vectorize"
    
    # 步骤状态常量
    STATUS_COMPLETED = "completed"
    STATUS_PENDING = "pending"
    STATUS_FAILED = "failed"
    
    def __init__(self, cache_state_path: Path):
        """初始化缓存管理器
        
        Args:
            cache_state_path: 缓存状态文件路径
        """
        self.cache_state_path = cache_state_path
        self.cache_state_path.parent.mkdir(parents=True, exist_ok=True)
        self._cache_data: Dict = self._load_cache_state()
        
    def _load_cache_state(self) -> Dict:
        """加载缓存状态文件
        
        Returns:
            缓存状态字典
        """
        if not self.cache_state_path.exists():
            logger.info(f"缓存状态文件不存在，创建新文件: {self.cache_state_path}")
            return {
                "version": "1.0",
                "tasks": {}
            }
        
        try:
            with open(self.cache_state_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.debug(f"加载缓存状态文件成功: {len(data.get('tasks', {}))} 个任务")
            return data
        except Exception as e:
            logger.error(f"加载缓存状态文件失败: {e}")
            logger.warning("将创建新的缓存状态文件")
            return {
                "version": "1.0",
                "tasks": {}
            }
    
    def _save_cache_state(self):
        """保存缓存状态到文件（使用原子操作）"""
        try:
            # 使用临时文件+原子操作确保写入安全
            temp_file = self.cache_state_path.with_suffix('.tmp')
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache_data, f, indent=2, ensure_ascii=False)
            
            # 原子替换
            temp_file.replace(self.cache_state_path)
            logger.debug(f"缓存状态文件已保存: {self.cache_state_path}")
        except Exception as e:
            logger.error(f"保存缓存状态文件失败: {e}")
            raise
    
    @staticmethod
    def compute_hash(data: str) -> str:
        """计算字符串的MD5哈希值
        
        Args:
            data: 输入字符串
            
        Returns:
            MD5哈希值（十六进制字符串）
        """
        return hashlib.md5(data.encode('utf-8')).hexdigest()
    
    def get_task_id(
        self,
        owner: str,
        repo: str,
        branch: str,
        filter_directories: Optional[List[str]] = None,
        filter_file_extensions: Optional[List[str]] = None
    ) -> str:
        """生成任务ID
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            branch: 分支名称
            filter_directories: 目录过滤器（可选）
            filter_file_extensions: 文件扩展名过滤器（可选）
            
        Returns:
            任务ID字符串
        """
        # 构建参数字符串用于哈希
        params = {
            "owner": owner,
            "repo": repo,
            "branch": branch,
            "filter_directories": sorted(filter_directories) if filter_directories else [],
            "filter_file_extensions": sorted(filter_file_extensions) if filter_file_extensions else []
        }
        
        params_str = json.dumps(params, sort_keys=True, ensure_ascii=False)
        params_hash = self.compute_hash(params_str)[:8]  # 使用前8位哈希
        
        # 生成任务ID: owner_repo_branch_hash
        task_id = f"{owner}_{repo}_{branch}_{params_hash}"
        
        logger.debug(f"生成任务ID: {task_id}")
        return task_id
    
    def get_task_key(self, owner: str, repo: str, branch: str) -> str:
        """获取任务键（用于显示）
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            branch: 分支名称
            
        Returns:
            任务键字符串（格式: owner/repo@branch）
        """
        return f"{owner}/{repo}@{branch}"
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """获取任务缓存信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务缓存信息字典，如果不存在返回None
        """
        return self._cache_data.get("tasks", {}).get(task_id)
    
    def init_task(
        self,
        task_id: str,
        task_key: str
    ):
        """初始化任务（如果不存在）
        
        Args:
            task_id: 任务ID
            task_key: 任务键（用于显示）
        """
        if task_id not in self._cache_data["tasks"]:
            self._cache_data["tasks"][task_id] = {
                "task_key": task_key,
                "created_at": datetime.now().isoformat(),
                self.STEP_CLONE: {"status": self.STATUS_PENDING},
                self.STEP_PARSE: {"status": self.STATUS_PENDING},
                self.STEP_VECTORIZE: {"status": self.STATUS_PENDING}
            }
            logger.debug(f"初始化任务: {task_id}")
    
    def check_step_cache(
        self,
        task_id: str,
        step_name: str,
        input_hash: Optional[str] = None
    ) -> bool:
        """检查步骤缓存是否有效
        
        Args:
            task_id: 任务ID
            step_name: 步骤名称
            input_hash: 输入参数哈希（用于验证缓存有效性）
            
        Returns:
            缓存是否有效
        """
        task = self.get_task(task_id)
        if not task:
            logger.debug(f"任务不存在: {task_id}")
            return False
        
        step_info = task.get(step_name)
        if not step_info:
            logger.debug(f"步骤信息不存在: {task_id}/{step_name}")
            return False
        
        # 检查步骤状态
        status = step_info.get("status")
        if status != self.STATUS_COMPLETED:
            logger.debug(f"步骤未完成: {task_id}/{step_name} (status: {status})")
            return False
        
        # 如果提供了输入哈希，验证是否匹配
        if input_hash:
            cached_hash = step_info.get("hash")
            if cached_hash != input_hash:
                logger.debug(f"输入哈希不匹配: {task_id}/{step_name} (cached: {cached_hash}, current: {input_hash})")
                return False
        
        logger.debug(f"缓存有效: {task_id}/{step_name}")
        return True
    
    def mark_step_completed(
        self,
        task_id: str,
        step_name: str,
        input_hash: Optional[str] = None,
        **step_data
    ):
        """标记步骤完成
        
        Args:
            task_id: 任务ID
            step_name: 步骤名称
            input_hash: 输入参数哈希（可选）
            **step_data: 步骤相关的其他数据（如输出路径、统计信息等）
        """
        task = self.get_task(task_id)
        if not task:
            logger.warning(f"任务不存在，无法标记步骤完成: {task_id}")
            return
        
        step_info = {
            "status": self.STATUS_COMPLETED,
            "timestamp": datetime.now().isoformat(),
            **step_data
        }
        
        if input_hash:
            step_info["hash"] = input_hash
        
        task[step_name] = step_info
        self._save_cache_state()
        
        logger.info(f"标记步骤完成: {task_id}/{step_name}")
    
    def mark_step_failed(
        self,
        task_id: str,
        step_name: str,
        error_message: Optional[str] = None
    ):
        """标记步骤失败
        
        Args:
            task_id: 任务ID
            step_name: 步骤名称
            error_message: 错误消息（可选）
        """
        task = self.get_task(task_id)
        if not task:
            logger.warning(f"任务不存在，无法标记步骤失败: {task_id}")
            return
        
        step_info = {
            "status": self.STATUS_FAILED,
            "timestamp": datetime.now().isoformat()
        }
        
        if error_message:
            step_info["error"] = error_message
        
        task[step_name] = step_info
        self._save_cache_state()
        
        logger.warning(f"标记步骤失败: {task_id}/{step_name} ({error_message})")
    
    def get_step_data(self, task_id: str, step_name: str) -> Optional[Dict]:
        """获取步骤数据
        
        Args:
            task_id: 任务ID
            step_name: 步骤名称
            
        Returns:
            步骤数据字典，如果不存在返回None
        """
        task = self.get_task(task_id)
        if not task:
            return None
        
        return task.get(step_name)
    
    def invalidate_task(self, task_id: str):
        """使任务缓存失效（删除任务记录）
        
        Args:
            task_id: 任务ID
        """
        if task_id in self._cache_data["tasks"]:
            del self._cache_data["tasks"][task_id]
            self._save_cache_state()
            logger.info(f"已使任务缓存失效: {task_id}")
    
    def clear_all_cache(self):
        """清除所有缓存"""
        self._cache_data["tasks"] = {}
        self._save_cache_state()
        logger.info("已清除所有缓存")
    
    def list_tasks(self) -> List[Dict]:
        """列出所有任务
        
        Returns:
            任务列表（包含任务ID和基本信息）
        """
        tasks = []
        for task_id, task_data in self._cache_data.get("tasks", {}).items():
            tasks.append({
                "task_id": task_id,
                "task_key": task_data.get("task_key", ""),
                "created_at": task_data.get("created_at", ""),
                "steps": {
                    self.STEP_CLONE: task_data.get(self.STEP_CLONE, {}).get("status", self.STATUS_PENDING),
                    self.STEP_PARSE: task_data.get(self.STEP_PARSE, {}).get("status", self.STATUS_PENDING),
                    self.STEP_VECTORIZE: task_data.get(self.STEP_VECTORIZE, {}).get("status", self.STATUS_PENDING)
                }
            })
        return tasks


