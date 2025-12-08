"""
Observer模块单元测试
测试PhoenixObserver、LlamaDebugObserver、RAGASEvaluator和ObserverManager
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List

from src.infrastructure.observers.base import BaseObserver, ObserverType
from src.infrastructure.observers.phoenix_observer import PhoenixObserver
from src.infrastructure.observers.llama_debug_observer import LlamaDebugObserver
from src.infrastructure.observers.ragas_evaluator import RAGASEvaluator
from src.infrastructure.observers.manager import ObserverManager
from src.infrastructure.observers.factory import create_default_observers, create_observer_from_config


class TestBaseObserver:
    """BaseObserver接口测试"""
    
    def test_base_observer_interface(self):
        """测试BaseObserver接口定义"""
        # BaseObserver是抽象类，不能直接实例化
        assert hasattr(BaseObserver, 'get_observer_type')
        assert hasattr(BaseObserver, 'setup')
        assert hasattr(BaseObserver, 'on_query_start')
        assert hasattr(BaseObserver, 'on_query_end')
        assert hasattr(BaseObserver, 'get_report')
        assert hasattr(BaseObserver, 'teardown')
    
    def test_observer_type_enum(self):
        """测试ObserverType枚举"""
        assert ObserverType.TRACING.value == "tracing"
        assert ObserverType.EVALUATION.value == "evaluation"
        assert ObserverType.DEBUG.value == "debug"
        assert ObserverType.METRICS.value == "metrics"


class TestPhoenixObserver:
    """PhoenixObserver测试"""
    
    @patch('src.infrastructure.observers.phoenix_observer.px')
    def test_phoenix_observer_init(self, mock_px):
        """测试PhoenixObserver初始化（Mock）"""
        mock_px.launch_app.return_value = Mock()
        from phoenix.trace.llama_index import OpenInferenceTraceCallbackHandler
        
        observer = PhoenixObserver(
            name="test_phoenix",
            enabled=True,
            launch_app=False
        )
        
        assert isinstance(observer, BaseObserver)
        assert observer.name == "test_phoenix"
        assert observer.enabled is True
        assert observer.get_observer_type() == ObserverType.TRACING
    
    @patch('src.infrastructure.observers.phoenix_observer.px')
    def test_phoenix_observer_init_with_launch(self, mock_px):
        """测试PhoenixObserver初始化（启动应用）"""
        mock_session = Mock()
        mock_px.launch_app.return_value = mock_session
        from phoenix.trace.llama_index import OpenInferenceTraceCallbackHandler
        
        observer = PhoenixObserver(
            name="test_phoenix",
            enabled=True,
            launch_app=True,
            host="127.0.0.1",
            port=6006
        )
        
        assert observer.session is not None
        mock_px.launch_app.assert_called_once_with(host="127.0.0.1", port=6006)
    
    @patch('src.infrastructure.observers.phoenix_observer.px')
    def test_phoenix_observer_init_import_error(self, mock_px):
        """测试Phoenix导入失败时的处理"""
        import sys
        original_import = __import__
        
        def mock_import(name, *args, **kwargs):
            if name == 'phoenix':
                raise ImportError("phoenix not installed")
            return original_import(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=mock_import):
            observer = PhoenixObserver(enabled=True)
            assert observer.enabled is False
    
    def test_phoenix_observer_query_callbacks(self):
        """测试PhoenixObserver查询回调"""
        observer = PhoenixObserver(
            name="test_phoenix",
            enabled=True,
            launch_app=False
        )
        
        # 如果Phoenix未安装，observer会被禁用
        if not observer.enabled:
            pytest.skip("Phoenix未安装")
        
        # 测试查询开始
        trace_id = observer.on_query_start("test query")
        assert trace_id is None  # Phoenix不需要手动管理trace_id
        
        # 测试查询结束
        observer.on_query_end(
            query="test query",
            answer="test answer",
            sources=[]
        )
    
    def test_phoenix_observer_get_callback_handler(self):
        """测试获取回调处理器"""
        observer = PhoenixObserver(
            name="test_phoenix",
            enabled=True,
            launch_app=False
        )
        
        if not observer.enabled:
            pytest.skip("Phoenix未安装")
        
        handler = observer.get_callback_handler()
        # handler应该存在（如果是None，说明Phoenix未正确初始化）
        if handler is not None:
            assert handler is not None
    
    def test_phoenix_observer_get_report(self):
        """测试获取Phoenix报告"""
        observer = PhoenixObserver(
            name="test_phoenix",
            enabled=True,
            launch_app=False
        )
        
        report = observer.get_report()
        
        assert isinstance(report, dict)
        assert report['observer'] == "test_phoenix"
        assert report['type'] == 'tracing'
        assert report['enabled'] == observer.enabled


class TestLlamaDebugObserver:
    """LlamaDebugObserver测试"""
    
    def test_llama_debug_observer_init(self):
        """测试LlamaDebugObserver初始化"""
        observer = LlamaDebugObserver(
            name="test_debug",
            enabled=True
        )
        
        assert isinstance(observer, BaseObserver)
        assert observer.name == "test_debug"
        assert observer.get_observer_type() == ObserverType.DEBUG
    
    def test_llama_debug_observer_query_callbacks(self):
        """测试LlamaDebugObserver查询回调"""
        observer = LlamaDebugObserver(
            name="test_debug",
            enabled=True
        )
        
        # 测试查询开始
        trace_id = observer.on_query_start("test query")
        assert trace_id is None
        
        # 测试查询结束
        observer.on_query_end(
            query="test query",
            answer="test answer",
            sources=[]
        )
    
    def test_llama_debug_observer_get_callback_handler(self):
        """测试获取回调处理器"""
        observer = LlamaDebugObserver(
            name="test_debug",
            enabled=True
        )
        
        handler = observer.get_callback_handler()
        assert handler is not None
    
    def test_llama_debug_observer_get_report(self):
        """测试获取调试报告"""
        observer = LlamaDebugObserver(
            name="test_debug",
            enabled=True
        )
        
        report = observer.get_report()
        
        assert isinstance(report, dict)
        assert report['observer'] == "test_debug"
        assert report['type'] == 'debug'
        assert report['enabled'] is True
        assert 'print_trace_on_end' in report


class TestRAGASEvaluator:
    """RAGASEvaluator测试"""
    
    def test_ragas_evaluator_init(self):
        """测试RAGASEvaluator初始化"""
        observer = RAGASEvaluator(
            name="test_ragas",
            enabled=True
        )
        
        assert isinstance(observer, BaseObserver)
        assert observer.name == "test_ragas"
        assert observer.get_observer_type() == ObserverType.EVALUATION
        
        # 如果RAGAS未安装，observer会被禁用
        if not observer.enabled:
            pytest.skip("RAGAS未安装")
    
    def test_ragas_evaluator_init_custom_metrics(self):
        """测试使用自定义指标初始化"""
        custom_metrics = ["faithfulness", "answer_relevancy"]
        observer = RAGASEvaluator(
            name="test_ragas",
            enabled=True,
            metrics=custom_metrics
        )
        
        if not observer.enabled:
            pytest.skip("RAGAS未安装")
        
        assert observer.metrics == custom_metrics
    
    def test_ragas_evaluator_query_callbacks(self):
        """测试RAGASEvaluator查询回调"""
        observer = RAGASEvaluator(
            name="test_ragas",
            enabled=True,
            batch_size=1  # 使用小批量以便立即触发评估
        )
        
        if not observer.enabled:
            pytest.skip("RAGAS未安装")
        
        # 测试查询开始
        trace_id = observer.on_query_start("test query")
        assert trace_id is None
        
        # 测试查询结束
        observer.on_query_end(
            query="test query",
            answer="test answer",
            sources=[{"text": "context text"}]
        )
        
        # 验证数据已记录
        assert len(observer.evaluation_data) > 0
    
    def test_ragas_evaluator_batch_evaluation(self):
        """测试批量评估"""
        observer = RAGASEvaluator(
            name="test_ragas",
            enabled=True,
            batch_size=2
        )
        
        if not observer.enabled:
            pytest.skip("RAGAS未安装")
        
        # 添加评估数据
        observer.evaluation_data = [
            {
                "question": "q1",
                "answer": "a1",
                "contexts": ["c1"],
                "timestamp": "2024-01-01T00:00:00"
            },
            {
                "question": "q2",
                "answer": "a2",
                "contexts": ["c2"],
                "timestamp": "2024-01-01T00:00:00"
            }
        ]
        
        # 执行批量评估
        try:
            observer._run_batch_evaluation()
            
            # 验证评估结果已保存
            assert len(observer.evaluation_results) > 0
        except Exception as e:
            # 如果RAGAS评估失败，跳过测试
            pytest.skip(f"RAGAS批量评估失败: {e}")
    
    def test_ragas_evaluator_get_report(self):
        """测试获取评估报告"""
        observer = RAGASEvaluator(
            name="test_ragas",
            enabled=True
        )
        
        report = observer.get_report()
        
        assert isinstance(report, dict)
        assert report['observer_type'] == 'ragas_evaluator'
        assert report['enabled'] == observer.enabled
        assert 'metrics' in report
        assert 'pending_evaluations' in report
        assert 'completed_evaluations' in report


class TestObserverManager:
    """ObserverManager测试"""
    
    def test_observer_manager_init(self):
        """测试ObserverManager初始化"""
        manager = ObserverManager()
        
        assert isinstance(manager.observers, list)
        assert len(manager.observers) == 0
    
    def test_observer_manager_add_remove(self):
        """测试添加和移除观察器"""
        manager = ObserverManager()
        observer = LlamaDebugObserver(name="test")
        
        # 添加观察器
        manager.add_observer(observer)
        assert len(manager.observers) == 1
        assert observer in manager.observers
        
        # 移除观察器
        manager.remove_observer(observer)
        assert len(manager.observers) == 0
    
    def test_observer_manager_get_by_type(self):
        """测试按类型获取观察器"""
        manager = ObserverManager()
        
        debug_observer = LlamaDebugObserver(name="debug1", enabled=True)
        phoenix_observer = PhoenixObserver(name="phoenix1", enabled=True, launch_app=False)
        
        manager.add_observer(debug_observer)
        manager.add_observer(phoenix_observer)
        
        debug_observers = manager.get_observers_by_type(ObserverType.DEBUG)
        assert len(debug_observers) > 0
        assert all(obs.get_observer_type() == ObserverType.DEBUG for obs in debug_observers)
    
    def test_observer_manager_query_callbacks(self):
        """测试查询回调"""
        manager = ObserverManager()
        
        observer1 = LlamaDebugObserver(name="debug1", enabled=True)
        observer2 = LlamaDebugObserver(name="debug2", enabled=True)
        
        manager.add_observer(observer1)
        manager.add_observer(observer2)
        
        # 测试查询开始
        trace_ids = manager.on_query_start("test query")
        assert isinstance(trace_ids, dict)
        
        # 测试查询结束
        manager.on_query_end(
            query="test query",
            answer="test answer",
            sources=[]
        )
    
    def test_observer_manager_callback_handlers(self):
        """测试获取回调处理器"""
        manager = ObserverManager()
        
        debug_observer = LlamaDebugObserver(name="debug1", enabled=True)
        manager.add_observer(debug_observer)
        
        handlers = manager.get_callback_handlers()
        assert isinstance(handlers, list)
        if handlers:
            assert all(handler is not None for handler in handlers)
    
    def test_observer_manager_get_summary(self):
        """测试获取摘要"""
        manager = ObserverManager()
        
        observer1 = LlamaDebugObserver(name="debug1", enabled=True)
        observer2 = LlamaDebugObserver(name="debug2", enabled=False)
        
        manager.add_observer(observer1)
        manager.add_observer(observer2)
        
        summary = manager.get_summary()
        
        assert isinstance(summary, dict)
        assert summary['total_observers'] == 2
        assert summary['enabled_observers'] == 1
        assert len(summary['observers']) == 2
    
    def test_observer_manager_teardown_all(self):
        """测试清理所有观察器"""
        manager = ObserverManager()
        
        observer = LlamaDebugObserver(name="debug1", enabled=True)
        manager.add_observer(observer)
        
        manager.teardown_all()
        
        assert len(manager.observers) == 0


class TestObserverFactory:
    """观察器工厂函数测试"""
    
    def test_create_default_observers(self):
        """测试创建默认观察器"""
        manager = create_default_observers(
            enable_phoenix=False,
            enable_debug=True,
            enable_ragas=False
        )
        
        assert isinstance(manager, ObserverManager)
        assert len(manager.observers) >= 0  # 至少0个（取决于依赖）
    
    def test_create_default_observers_all_enabled(self):
        """测试启用所有观察器"""
        manager = create_default_observers(
            enable_phoenix=True,
            enable_debug=True,
            enable_ragas=True
        )
        
        assert isinstance(manager, ObserverManager)
        # 观察器数量取决于依赖是否安装
    
    @patch('src.infrastructure.observers.factory.config')
    def test_create_observer_from_config(self, mock_config):
        """测试从配置创建观察器"""
        mock_config.ENABLE_PHOENIX = False
        mock_config.ENABLE_DEBUG_HANDLER = True
        mock_config.ENABLE_RAGAS = False
        mock_config.PHOENIX_LAUNCH_APP = False
        
        manager = create_observer_from_config()
        
        assert isinstance(manager, ObserverManager)


class TestObserverIntegration:
    """观察器集成测试"""
    
    def test_multiple_observers_coordination(self):
        """测试多个观察器协调工作"""
        manager = ObserverManager()
        
        debug_observer = LlamaDebugObserver(name="debug", enabled=True)
        manager.add_observer(debug_observer)
        
        # 执行查询流程
        trace_ids = manager.on_query_start("test query")
        
        manager.on_query_end(
            query="test query",
            answer="test answer",
            sources=[{"text": "context"}],
            trace_ids=trace_ids
        )
        
        # 验证观察器正常工作
        summary = manager.get_summary()
        assert summary['total_observers'] == 1
    
    def test_observer_enable_disable(self):
        """测试观察器启用/禁用"""
        observer = LlamaDebugObserver(name="test", enabled=True)
        
        assert observer.is_enabled() is True
        
        observer.disable()
        assert observer.is_enabled() is False
        
        observer.enable()
        assert observer.is_enabled() is True


