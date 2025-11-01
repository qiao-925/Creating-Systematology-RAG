# 可观测性纳入模块化 RAG - 设计方案

> **任务来源**: TRACKER.md 任务6 - RAG 评估体系构建  
> **创建时间**: 2025-11-01  
> **文档类型**: 设计方案

---

## 📋 背景与目标

### 当前模块化架构

我们已经建立了完整的可插拔架构：

```
✅ Embedding 层（可插拔）
✅ Retriever 层（可插拔）
✅ Postprocessor 层（可插拔）
✅ Reranker 模块（可插拔）
```

### 问题

**可观测性实现分散**：
- ❌ Phoenix 集成在单个文件中
- ❌ LlamaDebugHandler 散落在多处
- ❌ Trace 信息收集不统一
- ❌ 无法灵活切换不同的可观测性工具
- ❌ 难以扩展新的评估工具（RAGAS、deep EVAL）

### 目标

**统一的可观测性架构**：
```
⭐ BaseObserver（抽象基类）
    ├─ PhoenixObserver（已集成）
    ├─ RAGASEvaluator（待集成）
    ├─ LlamaDebugObserver（现有）
    └─ CustomObserver（扩展点）
```

**核心价值**：
1. ✅ 统一接口，配置驱动
2. ✅ 可插拔，灵活切换
3. ✅ 易于扩展，添加新工具
4. ✅ 解耦设计，不侵入核心逻辑
5. ✅ 支持多观察器同时工作

---

## 🏗️ 架构设计

### 完整的模块化 RAG 架构（含可观测性）

```
┌─────────────────────────────────────────────────────────┐
│         模块化 RAG 架构（完整版 v2.0）                   │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  [1] Embedding 层 ✅                                     │
│      └─ BaseEmbedding → Local / API                     │
│           ↓                                              │
│  [2] Retriever 层 ✅                                     │
│      └─ Vector / BM25 / Hybrid                          │
│           ↓                                              │
│  [3] Postprocessor 层 ✅                                 │
│      ├─ SimilarityFilter                                │
│      └─ Reranker（可插拔）                               │
│           ↓                                              │
│  [4] Query Engine ✅                                     │
│      └─ ModularQueryEngine                              │
│           ↓                                              │
│  [5] Observer 层（新增）✨                               │
│      ├─ BaseObserver（抽象）                            │
│      ├─ PhoenixObserver（追踪可视化）                   │
│      ├─ RAGASEvaluator（评估指标）                      │
│      ├─ LlamaDebugObserver（调试日志）                  │
│      └─ MetricsCollector（性能指标）                    │
│           ↓                                              │
│  [6] ObserverManager（协调器）✨                         │
│      └─ 统一管理多个观察器                               │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 详细设计

### 1. 抽象基类

**新文件**: `src/observers/base.py`

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from enum import Enum

class ObserverType(Enum):
    """观察器类型"""
    TRACING = "tracing"          # 追踪（Phoenix）
    EVALUATION = "evaluation"    # 评估（RAGAS）
    DEBUG = "debug"              # 调试（LlamaDebug）
    METRICS = "metrics"          # 指标收集


class BaseObserver(ABC):
    """可观测性观察器基类
    
    所有观察器实现都应继承此类，实现统一接口
    """
    
    def __init__(self, name: str, enabled: bool = True):
        """初始化观察器
        
        Args:
            name: 观察器名称
            enabled: 是否启用
        """
        self.name = name
        self.enabled = enabled
    
    @abstractmethod
    def get_observer_type(self) -> ObserverType:
        """获取观察器类型"""
        pass
    
    @abstractmethod
    def setup(self) -> None:
        """设置观察器（初始化）"""
        pass
    
    @abstractmethod
    def on_query_start(self, query: str, **kwargs) -> Optional[str]:
        """查询开始时回调
        
        Args:
            query: 查询文本
            **kwargs: 其他参数
            
        Returns:
            追踪ID（如果支持）
        """
        pass
    
    @abstractmethod
    def on_query_end(
        self,
        query: str,
        answer: str,
        sources: List[Dict],
        trace_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """查询结束时回调
        
        Args:
            query: 查询文本
            answer: 回答
            sources: 引用来源
            trace_id: 追踪ID
            **kwargs: 其他参数（如耗时、token数等）
        """
        pass
    
    def on_retrieval(self, query: str, nodes: List[Any], **kwargs) -> None:
        """检索完成时回调（可选）"""
        pass
    
    def on_rerank(self, query: str, nodes: List[Any], **kwargs) -> None:
        """重排序完成时回调（可选）"""
        pass
    
    def on_generation(self, query: str, answer: str, **kwargs) -> None:
        """生成完成时回调（可选）"""
        pass
    
    @abstractmethod
    def get_report(self) -> Dict[str, Any]:
        """获取观察报告
        
        Returns:
            观察报告字典
        """
        pass
    
    @abstractmethod
    def teardown(self) -> None:
        """清理资源"""
        pass
    
    def is_enabled(self) -> bool:
        """检查观察器是否启用"""
        return self.enabled
    
    def enable(self) -> None:
        """启用观察器"""
        self.enabled = True
    
    def disable(self) -> None:
        """禁用观察器"""
        self.enabled = False
    
    def __repr__(self) -> str:
        status = "enabled" if self.enabled else "disabled"
        return f"{self.__class__.__name__}(name={self.name}, {status})"
```

---

### 2. Phoenix 观察器

**新文件**: `src/observers/phoenix_observer.py`

```python
from typing import Any, Dict, List, Optional
import phoenix as px
from phoenix.trace.llama_index import OpenInferenceTraceCallbackHandler

from src.observers.base import BaseObserver, ObserverType
from src.config import config
from src.logger import setup_logger

logger = setup_logger('phoenix_observer')


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
            if self.launch_app:
                # 启动 Phoenix Web 应用
                self.session = px.launch_app(host=self.host, port=self.port)
                logger.info(f"✅ Phoenix Web 应用已启动: http://{self.host}:{self.port}")
            else:
                logger.info("ℹ️  Phoenix Web 应用未启动（launch_app=False）")
            
            # 创建回调处理器
            self.callback_handler = OpenInferenceTraceCallbackHandler()
            logger.info("✅ Phoenix 追踪回调处理器已创建")
            
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


class LegacyPhoenixObserver(PhoenixObserver):
    """兼容旧代码的 Phoenix 观察器
    
    兼容现有的 phoenix_utils.py 实现
    """
    
    def setup(self) -> None:
        """使用现有的 setup_phoenix() 函数"""
        try:
            from src.phoenix_utils import setup_phoenix
            
            logger.info("📊 使用现有 Phoenix 集成")
            setup_phoenix(launch_app=self.launch_app)
            
            # 创建回调处理器
            self.callback_handler = OpenInferenceTraceCallbackHandler()
            logger.info("✅ Phoenix（兼容模式）初始化完成")
            
        except Exception as e:
            logger.error(f"❌ Phoenix 初始化失败: {e}")
            self.enabled = False
```

---

### 3. RAGAS 评估器

**新文件**: `src/observers/ragas_evaluator.py`

```python
from typing import Any, Dict, List, Optional
from datetime import datetime

from src.observers.base import BaseObserver, ObserverType
from src.config import config
from src.logger import setup_logger

logger = setup_logger('ragas_evaluator')


class RAGASEvaluator(BaseObserver):
    """RAGAS 评估观察器
    
    提供多维度的 RAG 评估指标：
    - Faithfulness（忠实度）
    - Answer Relevancy（答案相关性）
    - Context Precision（上下文精确度）
    - Context Recall（上下文召回率）
    - Context Relevancy（上下文相关性）
    - Answer Similarity（答案相似度）
    """
    
    def __init__(
        self,
        name: str = "ragas",
        enabled: bool = True,
        metrics: Optional[List[str]] = None,
        batch_size: int = 10,
    ):
        """初始化 RAGAS 评估器
        
        Args:
            name: 观察器名称
            enabled: 是否启用
            metrics: 要计算的指标列表（None表示全部）
            batch_size: 批量评估大小
        """
        super().__init__(name, enabled)
        self.metrics = metrics or [
            "faithfulness",
            "answer_relevancy",
            "context_precision",
            "context_recall",
        ]
        self.batch_size = batch_size
        
        # 存储评估数据
        self.evaluation_data = []
        
        if self.enabled:
            self.setup()
    
    def get_observer_type(self) -> ObserverType:
        return ObserverType.EVALUATION
    
    def setup(self) -> None:
        """设置 RAGAS"""
        logger.info("📈 初始化 RAGAS 评估器")
        
        try:
            # 尝试导入 RAGAS
            import ragas
            logger.info(f"✅ RAGAS 版本: {ragas.__version__}")
            logger.info(f"   评估指标: {', '.join(self.metrics)}")
            
        except ImportError:
            logger.warning("⚠️  RAGAS 未安装，请运行: uv add ragas")
            logger.info("   评估器将以收集模式运行（不计算指标）")
            self.enabled = False
    
    def on_query_start(self, query: str, **kwargs) -> Optional[str]:
        """查询开始时回调"""
        if not self.enabled:
            return None
        
        # RAGAS 不需要在查询开始时做什么
        return None
    
    def on_query_end(
        self,
        query: str,
        answer: str,
        sources: List[Dict],
        trace_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """查询结束时回调 - 收集评估数据"""
        # 收集数据（无论是否启用）
        contexts = [source.get('text', '') for source in sources]
        
        evaluation_item = {
            "question": query,
            "answer": answer,
            "contexts": contexts,
            "ground_truth": kwargs.get("ground_truth"),  # 如果有标注答案
            "timestamp": datetime.now().isoformat(),
            "trace_id": trace_id,
        }
        
        self.evaluation_data.append(evaluation_item)
        logger.debug(f"📊 收集评估数据: {len(self.evaluation_data)} 条")
        
        # 如果达到批量大小，可以触发评估
        if len(self.evaluation_data) >= self.batch_size:
            logger.info(f"💡 提示: 已收集 {len(self.evaluation_data)} 条数据，可以运行评估")
    
    def evaluate(self, ground_truths: Optional[List[str]] = None) -> Dict[str, Any]:
        """运行 RAGAS 评估
        
        Args:
            ground_truths: 标注答案列表（可选）
            
        Returns:
            评估结果字典
        """
        if not self.enabled:
            logger.warning("⚠️  RAGAS 未启用，无法评估")
            return {}
        
        if not self.evaluation_data:
            logger.warning("⚠️  没有评估数据")
            return {}
        
        try:
            from ragas import evaluate
            from ragas.metrics import (
                faithfulness,
                answer_relevancy,
                context_precision,
                context_recall,
            )
            from datasets import Dataset
            
            logger.info(f"📊 开始 RAGAS 评估: {len(self.evaluation_data)} 条数据")
            
            # 准备数据集
            dataset_dict = {
                "question": [item["question"] for item in self.evaluation_data],
                "answer": [item["answer"] for item in self.evaluation_data],
                "contexts": [item["contexts"] for item in self.evaluation_data],
            }
            
            # 如果有标注答案
            if ground_truths:
                dataset_dict["ground_truth"] = ground_truths
            
            dataset = Dataset.from_dict(dataset_dict)
            
            # 选择评估指标
            metrics_map = {
                "faithfulness": faithfulness,
                "answer_relevancy": answer_relevancy,
                "context_precision": context_precision,
                "context_recall": context_recall,
            }
            
            selected_metrics = [
                metrics_map[m] for m in self.metrics if m in metrics_map
            ]
            
            # 运行评估
            result = evaluate(dataset, metrics=selected_metrics)
            
            logger.info("✅ RAGAS 评估完成")
            logger.info(f"   结果: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ RAGAS 评估失败: {e}")
            return {}
    
    def get_report(self) -> Dict[str, Any]:
        """获取评估报告"""
        return {
            "observer": self.name,
            "type": self.get_observer_type().value,
            "enabled": self.enabled,
            "metrics": self.metrics,
            "data_collected": len(self.evaluation_data),
            "batch_size": self.batch_size,
        }
    
    def clear_data(self) -> None:
        """清除评估数据"""
        logger.info(f"🧹 清除 {len(self.evaluation_data)} 条评估数据")
        self.evaluation_data = []
    
    def teardown(self) -> None:
        """清理资源"""
        self.clear_data()
```

---

### 4. LlamaDebug 观察器

**新文件**: `src/observers/llama_debug_observer.py`

```python
from typing import Any, Dict, List, Optional
from llama_index.core.callbacks import LlamaDebugHandler

from src.observers.base import BaseObserver, ObserverType
from src.logger import setup_logger

logger = setup_logger('llama_debug_observer')


class LlamaDebugObserver(BaseObserver):
    """LlamaDebug 观察器
    
    提供 LlamaIndex 内置的调试日志功能
    """
    
    def __init__(
        self,
        name: str = "llama_debug",
        enabled: bool = True,
        print_trace_on_end: bool = True,
    ):
        """初始化 LlamaDebug 观察器
        
        Args:
            name: 观察器名称
            enabled: 是否启用
            print_trace_on_end: 是否在结束时打印追踪信息
        """
        super().__init__(name, enabled)
        self.print_trace_on_end = print_trace_on_end
        self.handler = None
        
        if self.enabled:
            self.setup()
    
    def get_observer_type(self) -> ObserverType:
        return ObserverType.DEBUG
    
    def setup(self) -> None:
        """设置 LlamaDebug"""
        logger.info("🐛 初始化 LlamaDebug 观察器")
        
        self.handler = LlamaDebugHandler(
            print_trace_on_end=self.print_trace_on_end
        )
        
        logger.info("✅ LlamaDebug 观察器初始化完成")
    
    def on_query_start(self, query: str, **kwargs) -> Optional[str]:
        """查询开始时回调"""
        # LlamaDebugHandler 自动处理
        return None
    
    def on_query_end(
        self,
        query: str,
        answer: str,
        sources: List[Dict],
        trace_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """查询结束时回调"""
        # LlamaDebugHandler 自动处理
        pass
    
    def get_callback_handler(self):
        """获取 LlamaIndex 兼容的回调处理器"""
        return self.handler
    
    def get_event_pairs(self):
        """获取事件对"""
        if self.handler:
            return self.handler.get_event_pairs()
        return []
    
    def get_report(self) -> Dict[str, Any]:
        """获取调试报告"""
        report = {
            "observer": self.name,
            "type": self.get_observer_type().value,
            "enabled": self.enabled,
            "print_trace_on_end": self.print_trace_on_end,
        }
        
        if self.handler:
            event_pairs = self.get_event_pairs()
            report["events_count"] = len(event_pairs)
        
        return report
    
    def teardown(self) -> None:
        """清理资源"""
        logger.info("🧹 清理 LlamaDebug 资源")
```

---

### 5. 观察器管理器

**新文件**: `src/observers/manager.py`

```python
from typing import Any, Dict, List, Optional
from src.observers.base import BaseObserver, ObserverType
from src.logger import setup_logger

logger = setup_logger('observer_manager')


class ObserverManager:
    """观察器管理器
    
    统一管理多个观察器，协调它们的工作
    """
    
    def __init__(self):
        """初始化观察器管理器"""
        self.observers: List[BaseObserver] = []
        logger.info("📊 初始化观察器管理器")
    
    def add_observer(self, observer: BaseObserver) -> None:
        """添加观察器
        
        Args:
            observer: 观察器实例
        """
        self.observers.append(observer)
        logger.info(f"➕ 添加观察器: {observer}")
    
    def remove_observer(self, observer: BaseObserver) -> None:
        """移除观察器"""
        if observer in self.observers:
            self.observers.remove(observer)
            logger.info(f"➖ 移除观察器: {observer}")
    
    def get_observers_by_type(self, observer_type: ObserverType) -> List[BaseObserver]:
        """按类型获取观察器"""
        return [
            obs for obs in self.observers
            if obs.get_observer_type() == observer_type and obs.is_enabled()
        ]
    
    def on_query_start(self, query: str, **kwargs) -> Dict[str, Optional[str]]:
        """通知所有观察器：查询开始
        
        Returns:
            观察器名称到追踪ID的映射
        """
        trace_ids = {}
        
        for observer in self.observers:
            if observer.is_enabled():
                try:
                    trace_id = observer.on_query_start(query, **kwargs)
                    if trace_id:
                        trace_ids[observer.name] = trace_id
                except Exception as e:
                    logger.error(f"❌ 观察器 {observer.name} 处理失败: {e}")
        
        return trace_ids
    
    def on_query_end(
        self,
        query: str,
        answer: str,
        sources: List[Dict],
        trace_ids: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> None:
        """通知所有观察器：查询结束"""
        for observer in self.observers:
            if observer.is_enabled():
                try:
                    trace_id = trace_ids.get(observer.name) if trace_ids else None
                    observer.on_query_end(
                        query, answer, sources, trace_id, **kwargs
                    )
                except Exception as e:
                    logger.error(f"❌ 观察器 {observer.name} 处理失败: {e}")
    
    def on_retrieval(self, query: str, nodes: List[Any], **kwargs) -> None:
        """通知所有观察器：检索完成"""
        for observer in self.observers:
            if observer.is_enabled():
                try:
                    observer.on_retrieval(query, nodes, **kwargs)
                except Exception as e:
                    logger.error(f"❌ 观察器 {observer.name} 处理失败: {e}")
    
    def get_callback_handlers(self) -> List[Any]:
        """获取所有观察器的回调处理器（用于LlamaIndex）
        
        Returns:
            回调处理器列表
        """
        handlers = []
        
        for observer in self.observers:
            if observer.is_enabled() and hasattr(observer, 'get_callback_handler'):
                handler = observer.get_callback_handler()
                if handler:
                    handlers.append(handler)
        
        return handlers
    
    def get_summary(self) -> Dict[str, Any]:
        """获取所有观察器的摘要"""
        return {
            "total_observers": len(self.observers),
            "enabled_observers": len([obs for obs in self.observers if obs.is_enabled()]),
            "observers": [obs.get_report() for obs in self.observers],
        }
    
    def teardown_all(self) -> None:
        """清理所有观察器"""
        logger.info("🧹 清理所有观察器")
        
        for observer in self.observers:
            try:
                observer.teardown()
            except Exception as e:
                logger.error(f"❌ 观察器 {observer.name} 清理失败: {e}")
        
        self.observers.clear()
```

---

### 6. 工厂函数

**新文件**: `src/observers/factory.py`

```python
from typing import List, Optional
from src.observers.base import BaseObserver
from src.observers.phoenix_observer import PhoenixObserver, LegacyPhoenixObserver
from src.observers.ragas_evaluator import RAGASEvaluator
from src.observers.llama_debug_observer import LlamaDebugObserver
from src.observers.manager import ObserverManager
from src.config import config
from src.logger import setup_logger

logger = setup_logger('observer_factory')


def create_default_observers(
    enable_phoenix: bool = True,
    enable_ragas: bool = False,
    enable_debug: bool = False,
    **kwargs
) -> ObserverManager:
    """创建默认的观察器管理器
    
    Args:
        enable_phoenix: 是否启用 Phoenix
        enable_ragas: 是否启用 RAGAS
        enable_debug: 是否启用 LlamaDebug
        **kwargs: 其他参数
        
    Returns:
        配置好的 ObserverManager
    """
    manager = ObserverManager()
    
    # Phoenix 观察器
    if enable_phoenix:
        phoenix = LegacyPhoenixObserver(
            enabled=True,
            launch_app=kwargs.get('launch_phoenix_app', False),
        )
        manager.add_observer(phoenix)
        logger.info("✅ 已添加 Phoenix 观察器")
    
    # RAGAS 评估器
    if enable_ragas:
        ragas = RAGASEvaluator(
            enabled=True,
            batch_size=kwargs.get('ragas_batch_size', 10),
        )
        manager.add_observer(ragas)
        logger.info("✅ 已添加 RAGAS 评估器")
    
    # LlamaDebug 观察器
    if enable_debug:
        debug = LlamaDebugObserver(
            enabled=True,
            print_trace_on_end=kwargs.get('print_trace', True),
        )
        manager.add_observer(debug)
        logger.info("✅ 已添加 LlamaDebug 观察器")
    
    logger.info(f"📊 观察器管理器已创建: {len(manager.observers)} 个观察器")
    
    return manager


def create_observer_from_config() -> ObserverManager:
    """从配置创建观察器管理器
    
    读取配置文件中的观察器配置
    """
    enable_phoenix = getattr(config, 'ENABLE_PHOENIX', True)
    enable_ragas = getattr(config, 'ENABLE_RAGAS', False)
    enable_debug = getattr(config, 'ENABLE_DEBUG_HANDLER', False)
    
    return create_default_observers(
        enable_phoenix=enable_phoenix,
        enable_ragas=enable_ragas,
        enable_debug=enable_debug,
    )
```

---

### 7. 配置更新

**文件**: `src/config.py`

```python
# ===== 可观测性配置（新增）=====

# Phoenix 配置
ENABLE_PHOENIX = os.getenv("ENABLE_PHOENIX", "true").lower() == "true"
PHOENIX_LAUNCH_APP = os.getenv("PHOENIX_LAUNCH_APP", "false").lower() == "true"
PHOENIX_HOST = os.getenv("PHOENIX_HOST", "0.0.0.0")
PHOENIX_PORT = int(os.getenv("PHOENIX_PORT", "6006"))

# RAGAS 配置
ENABLE_RAGAS = os.getenv("ENABLE_RAGAS", "false").lower() == "true"
RAGAS_BATCH_SIZE = int(os.getenv("RAGAS_BATCH_SIZE", "10"))

# LlamaDebug 配置
ENABLE_DEBUG_HANDLER = os.getenv("ENABLE_DEBUG_HANDLER", "false").lower() == "true"
DEBUG_PRINT_TRACE = os.getenv("DEBUG_PRINT_TRACE", "true").lower() == "true"
```

---

### 8. ModularQueryEngine 集成

**文件**: `src/modular_query_engine.py`

**修改内容**：

```python
from src.observers.manager import ObserverManager
from src.observers.factory import create_observer_from_config

class ModularQueryEngine:
    def __init__(
        self,
        index_manager: IndexManager,
        # ... 现有参数 ...
        observer_manager: Optional[ObserverManager] = None,  # 新增
    ):
        # ...
        
        # 观察器管理器
        if observer_manager is not None:
            self.observer_manager = observer_manager
        else:
            # 从配置创建
            self.observer_manager = create_observer_from_config()
        
        logger.info(f"✅ 观察器: {self.observer_manager.get_summary()}")
        
        # 获取所有回调处理器
        callback_handlers = self.observer_manager.get_callback_handlers()
        
        # 设置全局回调（传递给 LlamaIndex）
        if callback_handlers:
            from llama_index.core import Settings
            Settings.callback_manager = CallbackManager(callback_handlers)
    
    def query(
        self, 
        question: str, 
        collect_trace: bool = False
    ) -> Tuple[str, List[dict], Optional[Dict[str, Any]]]:
        """执行查询"""
        
        # 通知观察器：查询开始
        trace_ids = self.observer_manager.on_query_start(question)
        
        try:
            # 执行查询（现有逻辑）
            response = self.query_engine.query(question)
            answer = str(response)
            sources = self._extract_sources(response)
            
            # 通知观察器：查询结束
            self.observer_manager.on_query_end(
                question,
                answer,
                sources,
                trace_ids,
            )
            
            return answer, sources, trace_info
            
        except Exception as e:
            logger.error(f"❌ 查询失败: {e}")
            raise
```

---

## 💡 使用示例

### 示例1：默认配置

```python
from src.modular_query_engine import ModularQueryEngine

# 默认启用 Phoenix
query_engine = ModularQueryEngine(index_manager)

# 查询（自动追踪）
answer, sources, _ = query_engine.query("问题")
```

### 示例2：启用 RAGAS 评估

```python
from src.observers.factory import create_default_observers

# 创建观察器管理器
observer_manager = create_default_observers(
    enable_phoenix=True,
    enable_ragas=True,  # 启用 RAGAS
)

# 创建 QueryEngine
query_engine = ModularQueryEngine(
    index_manager,
    observer_manager=observer_manager,
)

# 查询（自动收集评估数据）
for question in questions:
    answer, sources, _ = query_engine.query(question)

# 运行评估
ragas_evaluator = observer_manager.get_observers_by_type(ObserverType.EVALUATION)[0]
result = ragas_evaluator.evaluate()
print(result)
```

### 示例3：自定义观察器组合

```python
from src.observers import (
    PhoenixObserver,
    RAGASEvaluator,
    LlamaDebugObserver,
    ObserverManager,
)

# 创建管理器
manager = ObserverManager()

# 添加 Phoenix（启动 Web 应用）
phoenix = PhoenixObserver(launch_app=True, port=6006)
manager.add_observer(phoenix)

# 添加 RAGAS
ragas = RAGASEvaluator(batch_size=20)
manager.add_observer(ragas)

# 添加 Debug
debug = LlamaDebugObserver()
manager.add_observer(debug)

# 创建 QueryEngine
query_engine = ModularQueryEngine(index_manager, observer_manager=manager)
```

### 示例4：环境变量配置

```bash
# .env
ENABLE_PHOENIX=true
PHOENIX_LAUNCH_APP=true
PHOENIX_PORT=6006

ENABLE_RAGAS=true
RAGAS_BATCH_SIZE=20

ENABLE_DEBUG_HANDLER=false
```

```python
# 自动读取配置
query_engine = ModularQueryEngine(index_manager)  # 自动创建观察器
```

---

## 📊 完整架构对比

### 实施前

```
❌ 分散的可观测性实现
    ├─ Phoenix 在 phoenix_utils.py
    ├─ LlamaDebug 散落在各处
    └─ Trace 信息手动收集

❌ 难以扩展
❌ 无法灵活切换
❌ 侵入核心逻辑
```

### 实施后

```
✅ 统一的可观测性架构
    ├─ BaseObserver（抽象）
    ├─ PhoenixObserver
    ├─ RAGASEvaluator
    ├─ LlamaDebugObserver
    └─ ObserverManager（协调）

✅ 可插拔
✅ 配置驱动
✅ 易于扩展
✅ 不侵入核心逻辑
```

---

## 🎯 实施计划

### 阶段1：核心框架（优先）

- [ ] 创建 `BaseObserver` 抽象基类
- [ ] 实现 `ObserverManager` 协调器
- [ ] 实现 `PhoenixObserver`（兼容现有）
- [ ] 实现 `LlamaDebugObserver`
- [ ] 工厂函数 `create_default_observers`
- [ ] 更新 `ModularQueryEngine` 集成

**工作量**：~4小时

### 阶段2：RAGAS 集成（推荐）

- [ ] 实现 `RAGASEvaluator`
- [ ] 安装 RAGAS 依赖
- [ ] 创建测试数据集
- [ ] 评估流程文档

**工作量**：~3小时

### 阶段3：完善与优化

- [ ] 添加更多观察器（Metrics、Custom）
- [ ] Web UI 集成
- [ ] 单元测试
- [ ] 文档完善

**工作量**：~3小时

---

## ❓ 需要您决策的问题

### 问题1：实施优先级？

**选项 A**：立即实施阶段1+2（核心框架 + RAGAS）⭐ 推荐  
**选项 B**：仅实施阶段1（核心框架）  
**选项 C**：仅更新设计文档

### 问题2：默认启用哪些观察器？

**选项 A**：仅 Phoenix（默认）  
**选项 B**：Phoenix + RAGAS ⭐ 推荐  
**选项 C**：全部启用

### 问题3：是否迁移现有代码？

**选项 A**：立即迁移（使用新的观察器架构）  
**选项 B**：新旧并存（渐进式迁移）⭐ 推荐  
**选项 C**：保留现有实现

---

## 📄 相关文档

- 📄 [可观测性调研报告](2025-10-31-8_RAG可观测性与评估体系_调研报告.md)
- 📄 [Phoenix 文档](https://docs.arize.com/phoenix)
- 📄 [RAGAS 文档](https://docs.ragas.io/)
- 📄 [LlamaIndex Observability](https://docs.llamaindex.ai/en/stable/module_guides/observability/)

---

**创建时间**: 2025-11-01  
**状态**: ⏸️ 待决策  
**下一步**: 等待决策后开始实施

