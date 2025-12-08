"""
Phoenix 观察器
提供实时追踪、向量空间可视化、性能分析等功能
"""

from typing import Any, Dict, List, Optional

from src.infrastructure.observers.base import BaseObserver, ObserverType
from src.infrastructure.config import config
from src.infrastructure.logger import get_logger

logger = get_logger('phoenix_observer')


class PhoenixObserver(BaseObserver):
    """Phoenix 可观测性观察器
    
    提供实时追踪、向量空间可视化、性能分析等功能
    """
    
    def __init__(
        self,
        name: str = "phoenix",
        enabled: bool = True,
        launch_app: bool = False,
        host: str = "0.0.0.0",
        port: int = 6006,
    ):
        """初始化 Phoenix 观察器
        
        Args:
            name: 观察器名称
            enabled: 是否启用
            launch_app: 是否启动 Phoenix Web 应用
            host: Web 应用地址
            port: Web 应用端口
        """
        super().__init__(name, enabled)
        self.launch_app = launch_app
        self.host = host
        self.port = port
        self.session = None
        self.callback_handler = None
        
        if self.enabled:
            self.setup()
    
    def get_observer_type(self) -> ObserverType:
        return ObserverType.TRACING
    
    def setup(self) -> None:
        """设置 Phoenix"""
        logger.info("📊 初始化 Phoenix 观察器")
        
        try:
            import phoenix as px
            from phoenix.trace.llama_index import OpenInferenceTraceCallbackHandler
            
            if self.launch_app:
                # 启动 Phoenix Web 应用
                self.session = px.launch_app(host=self.host, port=self.port)
                logger.info(f"✅ Phoenix Web 应用已启动: http://{self.host}:{self.port}")
            else:
                logger.info("ℹ️  Phoenix Web 应用未启动（launch_app=False）")
            
            # 创建回调处理器
            self.callback_handler = OpenInferenceTraceCallbackHandler()
            logger.info("✅ Phoenix 追踪回调处理器已创建")
            
        except ImportError as e:
            logger.warning(f"⚠️  Phoenix 未安装或导入失败: {e}")
            logger.info("   观察器将被禁用")
            self.enabled = False
        except Exception as e:
            logger.error(f"❌ Phoenix 初始化失败: {e}")
            self.enabled = False
    
    def on_query_start(self, query: str, **kwargs) -> Optional[str]:
        """查询开始时回调"""
        if not self.enabled:
            return None
        
        logger.debug(f"🔍 Phoenix 追踪查询: {query}")
        # Phoenix 通过 callback_handler 自动追踪
        return None  # Phoenix 不需要手动管理 trace_id
    
    def on_query_end(
        self,
        query: str,
        answer: str,
        sources: List[Dict],
        trace_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """查询结束时回调"""
        if not self.enabled:
            return
        
        logger.debug(f"✅ Phoenix 记录查询完成")
        # Phoenix 通过 callback_handler 自动记录
    
    def get_callback_handler(self):
        """获取 LlamaIndex 兼容的回调处理器"""
        return self.callback_handler
    
    def get_report(self) -> Dict[str, Any]:
        """获取 Phoenix 报告"""
        report = {
            "observer": self.name,
            "type": self.get_observer_type().value,
            "enabled": self.enabled,
        }
        
        if self.session:
            report["web_url"] = f"http://{self.host}:{self.port}"
        
        return report
    
    def teardown(self) -> None:
        """清理 Phoenix 资源"""
        logger.info("🧹 清理 Phoenix 资源")
        # Phoenix session 会自动清理

