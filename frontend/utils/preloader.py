"""
后台预加载器：异步初始化耗时模块，实现界面立即显示

核心功能：
- start_background_init()：启动后台初始化线程
- is_ready()：检查是否初始化完成
- get_services()：获取初始化完成的服务实例
- get_status()：获取当前初始化状态
"""

import threading
import time
from dataclasses import dataclass
from typing import Any, Optional, Tuple
from enum import Enum

from backend.infrastructure.logger import get_logger

logger = get_logger('frontend.preloader')


class PreloadStatus(Enum):
    """预加载状态"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PreloadResult:
    """预加载结果"""
    status: PreloadStatus
    init_result: Optional[Any] = None
    rag_service: Optional[Any] = None
    chat_manager: Optional[Any] = None
    error: Optional[str] = None
    duration: float = 0.0


class BackgroundPreloader:
    """后台预加载器（单例）"""
    
    _instance: Optional["BackgroundPreloader"] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._status = PreloadStatus.NOT_STARTED
        self._result: Optional[PreloadResult] = None
        self._thread: Optional[threading.Thread] = None
        self._start_time: float = 0.0
        # 详细进度跟踪
        self._current_stage: str = ""
        self._stage_details: list[str] = []
        self._completed_modules: list[str] = []
    
    def start(self) -> None:
        """启动后台初始化（如果尚未开始）"""
        with self._lock:
            if self._status != PreloadStatus.NOT_STARTED:
                return
            
            self._status = PreloadStatus.IN_PROGRESS
            self._start_time = time.perf_counter()
            self._thread = threading.Thread(target=self._do_init, daemon=True)
            self._thread.start()
            logger.info("🚀 后台预加载已启动")
    
    def _update_stage(self, stage: str, module_name: Optional[str] = None) -> None:
        """更新当前阶段"""
        self._current_stage = stage
        if module_name:
            self._stage_details.append(f"✅ {module_name}")
            if module_name not in self._completed_modules:
                self._completed_modules.append(module_name)
    
    def _do_init(self) -> None:
        """执行初始化（优化版：只初始化必需模块，延迟加载耗时组件）"""
        try:
            from backend.infrastructure.initialization.manager import InitializationManager
            from backend.infrastructure.initialization.registry import register_all_modules
            from backend.infrastructure.initialization.bootstrap import InitResult
            
            self._update_stage("创建初始化管理器")
            manager = InitializationManager()
            register_all_modules(manager)
            
            # 只初始化必需模块（跳过 embedding、index_manager 等耗时模块）
            for module_name in manager._topological_sort():
                module = manager.modules[module_name]
                display = module.description or module_name
                
                # 跳过非必需模块（延迟加载）
                if not module.is_required:
                    self._stage_details.append(f"⏭️ {display} (延迟加载)")
                    continue
                
                self._update_stage(f"初始化 {display}")
                success = manager.execute_init(module_name)
                
                if success:
                    self._update_stage(f"{display}", module_name)
                else:
                    self._fail(f"必需模块 {display} 初始化失败: {module.error}")
                    return
            
            # 创建轻量级服务（纯 LLM 模式，不依赖 index_manager）
            self._update_stage("创建轻量级服务")
            rag_service, chat_manager = self._create_lightweight_services(manager)
            
            if not rag_service or not chat_manager:
                self._fail("服务实例创建失败")
                return
            
            # 存储到 manager.instances 以便后续使用
            manager.instances['rag_service'] = rag_service
            manager.instances['chat_manager'] = chat_manager
            
            # 成功
            summary = manager.get_status_summary()
            init_result = InitResult(
                all_required_ready=summary['all_required_ready'],
                manager=manager, instances=manager.instances.copy(),
                failed_modules=summary['required_failed'], summary=summary
            )
            self._complete(init_result, rag_service, chat_manager)
            
        except Exception as e:
            self._fail(str(e))
            logger.error(f"❌ 后台预加载异常: {e}", exc_info=True)
    
    def _create_lightweight_services(self, manager) -> tuple:
        """创建轻量级服务（纯 LLM 模式，首次查询时延迟初始化 RAG）
        
        Returns:
            (rag_service, chat_manager)
        """
        from backend.infrastructure.config import config
        
        # 注意：后台线程中不要访问 st.session_state，避免大量警告日志
        # 使用默认配置即可，用户配置变更后会重建服务
        enable_debug = True  # 默认启用调试
        use_agentic_rag = False
        selected_model_id = config.get_default_llm_id()
        collection_name = config.CHROMA_COLLECTION_NAME
        
        # 创建 RAGService（延迟模式）
        logger.info("⏳ 开始创建 RAGService...")
        from backend.business.rag_api import RAGService
        
        rag_service = RAGService(
            collection_name=collection_name,
            enable_debug=enable_debug,
            enable_markdown_formatting=True,
            use_agentic_rag=use_agentic_rag,
            model_id=selected_model_id,
        )
        logger.info("✅ RAGService 创建完成")
        
        # 创建 ChatManager（纯 LLM 模式，无 index_manager）
        logger.info("⏳ 开始创建 ChatManager...")
        from backend.business.chat import ChatManager
        chat_manager = ChatManager(
            index_manager=None,  # 纯 LLM 模式
            enable_debug=enable_debug,
            enable_markdown_formatting=True,
            use_agentic_rag=use_agentic_rag,
            model_id=selected_model_id,
        )
        logger.info("✅ ChatManager 创建完成")
        
        logger.info("✅ 轻量级服务创建完成（延迟加载模式）")
        return rag_service, chat_manager
    
    def _fail(self, error: str) -> None:
        """标记初始化失败"""
        self._result = PreloadResult(
            status=PreloadStatus.FAILED, error=error,
            duration=time.perf_counter() - self._start_time
        )
        self._status = PreloadStatus.FAILED
        logger.error(f"❌ {error}")
    
    def _complete(self, init_result: Any, rag_service: Any, chat_manager: Any) -> None:
        """标记初始化完成"""
        duration = time.perf_counter() - self._start_time
        self._update_stage("初始化完成")
        self._result = PreloadResult(
            status=PreloadStatus.COMPLETED, init_result=init_result,
            rag_service=rag_service, chat_manager=chat_manager, duration=duration
        )
        self._status = PreloadStatus.COMPLETED
        logger.info(f"✅ 后台预加载完成（耗时: {duration:.2f}s）")
    
    def is_ready(self) -> bool:
        """检查是否初始化完成"""
        return self._status == PreloadStatus.COMPLETED
    
    def get_status(self) -> PreloadStatus:
        """获取当前状态"""
        return self._status
    
    def get_progress_message(self) -> str:
        """获取进度消息"""
        if self._status == PreloadStatus.NOT_STARTED:
            return "准备初始化..."
        if self._status == PreloadStatus.IN_PROGRESS:
            elapsed = time.perf_counter() - self._start_time
            return f"{self._current_stage or '启动中'}... ({elapsed:.1f}s)"
        if self._status == PreloadStatus.COMPLETED:
            return f"初始化完成 ({self._result.duration:.1f}s)"
        return f"初始化失败: {self._result.error if self._result else '未知错误'}"
    
    def get_detailed_progress(self) -> dict:
        """获取详细进度信息"""
        elapsed = time.perf_counter() - self._start_time if self._start_time > 0 else 0
        return {
            "status": self._status.value, "stage": self._current_stage, "elapsed": elapsed,
            "completed_modules": list(self._completed_modules),
            "module_count": len(self._completed_modules), "logs": list(self._stage_details),
        }
    
    def get_services(self) -> Optional[Tuple[Any, Any, Any]]:
        """获取服务实例 -> (init_result, rag_service, chat_manager) 或 None"""
        if self._status != PreloadStatus.COMPLETED or self._result is None:
            return None
        return (self._result.init_result, self._result.rag_service, self._result.chat_manager)
    
    def get_error(self) -> Optional[str]:
        """获取错误信息"""
        return self._result.error if self._result and self._result.error else None
    
    def reset(self) -> None:
        """重置预加载器（用于重试）"""
        with self._lock:
            self._status, self._result, self._thread = PreloadStatus.NOT_STARTED, None, None
            self._start_time, self._current_stage = 0.0, ""
            self._stage_details, self._completed_modules = [], []


# 全局预加载器实例
_preloader: Optional[BackgroundPreloader] = None

def get_preloader() -> BackgroundPreloader:
    """获取全局预加载器实例"""
    global _preloader
    if _preloader is None:
        _preloader = BackgroundPreloader()
    return _preloader

# 便捷函数
def start_background_init() -> None: get_preloader().start()
def is_services_ready() -> bool: return get_preloader().is_ready()
def get_services() -> Optional[Tuple[Any, Any, Any]]: return get_preloader().get_services()
def get_init_status() -> PreloadStatus: return get_preloader().get_status()
def get_progress_message() -> str: return get_preloader().get_progress_message()
def get_detailed_progress() -> dict: return get_preloader().get_detailed_progress()
