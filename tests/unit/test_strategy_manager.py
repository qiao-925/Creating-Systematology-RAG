"""
策略管理器单元测试
"""

import pytest
from unittest.mock import Mock, patch

from src.business.strategy_manager import (
    StrategyManager,
    StrategyVariant,
    StrategyType,
    get_strategy_manager,
    reset_strategy_manager,
)


class TestStrategyVariant:
    """StrategyVariant单元测试"""
    
    def test_init(self):
        """测试初始化"""
        variant = StrategyVariant(
            name="test_strategy",
            strategy_type=StrategyType.RETRIEVAL,
            config={"key": "value"},
            weight=1.0,
            enabled=True,
        )
        
        assert variant.name == "test_strategy"
        assert variant.strategy_type == StrategyType.RETRIEVAL
        assert variant.weight == 1.0
        assert variant.enabled is True
    
    def test_record_request(self):
        """测试记录请求"""
        variant = StrategyVariant(
            name="test",
            strategy_type=StrategyType.RETRIEVAL,
            config={},
        )
        
        variant.record_request(success=True, response_time=0.5)
        variant.record_request(success=False, response_time=0.3)
        
        assert variant.metrics["total_requests"] == 2
        assert variant.metrics["success_count"] == 1
        assert variant.metrics["error_count"] == 1
    
    def test_get_success_rate(self):
        """测试获取成功率"""
        variant = StrategyVariant(
            name="test",
            strategy_type=StrategyType.RETRIEVAL,
            config={},
        )
        
        # 无请求
        assert variant.get_success_rate() == 0.0
        
        # 记录请求
        variant.record_request(success=True, response_time=0.5)
        variant.record_request(success=True, response_time=0.6)
        variant.record_request(success=False, response_time=0.3)
        
        assert variant.get_success_rate() == pytest.approx(2/3, rel=0.1)


class TestStrategyManager:
    """StrategyManager单元测试"""
    
    def test_init(self):
        """测试初始化"""
        manager = StrategyManager()
        
        assert len(manager.list_strategies()) == 0
    
    def test_register_strategy(self):
        """测试注册策略"""
        manager = StrategyManager()
        
        manager.register_strategy(
            name="test_strategy",
            strategy_type=StrategyType.RETRIEVAL,
            config={"key": "value"},
            weight=1.0,
            is_default=True,
        )
        
        assert "test_strategy" in manager.list_strategies()
        assert manager._default_strategies[StrategyType.RETRIEVAL] == "test_strategy"
    
    def test_get_strategy_default(self):
        """测试获取默认策略"""
        manager = StrategyManager()
        
        manager.register_strategy(
            name="default_strategy",
            strategy_type=StrategyType.RETRIEVAL,
            config={},
            is_default=True,
        )
        
        manager.register_strategy(
            name="other_strategy",
            strategy_type=StrategyType.RETRIEVAL,
            config={},
        )
        
        strategy = manager.get_strategy(StrategyType.RETRIEVAL)
        
        assert strategy is not None
        assert strategy.name == "default_strategy"
    
    def test_get_strategy_by_name(self):
        """测试按名称获取策略"""
        manager = StrategyManager()
        
        manager.register_strategy(
            name="test_strategy",
            strategy_type=StrategyType.RETRIEVAL,
            config={},
        )
        
        strategy = manager.get_strategy(
            StrategyType.RETRIEVAL,
            variant_name="test_strategy",
        )
        
        assert strategy is not None
        assert strategy.name == "test_strategy"
    
    def test_get_strategy_nonexistent(self):
        """测试获取不存在的策略"""
        manager = StrategyManager()
        
        strategy = manager.get_strategy(StrategyType.RETRIEVAL)
        
        assert strategy is None
    
    def test_ab_test_selection(self):
        """测试A/B测试选择"""
        manager = StrategyManager()
        
        manager.register_strategy(
            name="strategy1",
            strategy_type=StrategyType.RETRIEVAL,
            config={},
            weight=1.0,
        )
        
        manager.register_strategy(
            name="strategy2",
            strategy_type=StrategyType.RETRIEVAL,
            config={},
            weight=0.5,
        )
        
        manager.enable_ab_test(StrategyType.RETRIEVAL, enabled=True)
        
        # 多次选择应该能选到不同策略（由于随机性）
        strategies_selected = set()
        for _ in range(20):
            strategy = manager.get_strategy(
                StrategyType.RETRIEVAL,
                enable_ab_test=True,
            )
            if strategy:
                strategies_selected.add(strategy.name)
        
        # 应该选到至少一个策略
        assert len(strategies_selected) > 0
    
    def test_set_default_strategy(self):
        """测试设置默认策略"""
        manager = StrategyManager()
        
        manager.register_strategy(
            name="strategy1",
            strategy_type=StrategyType.RETRIEVAL,
            config={},
            is_default=True,
        )
        
        manager.register_strategy(
            name="strategy2",
            strategy_type=StrategyType.RETRIEVAL,
            config={},
        )
        
        manager.set_default_strategy(StrategyType.RETRIEVAL, "strategy2")
        
        strategy = manager.get_strategy(StrategyType.RETRIEVAL)
        assert strategy.name == "strategy2"
    
    def test_record_strategy_metrics(self):
        """测试记录策略指标"""
        manager = StrategyManager()
        
        manager.register_strategy(
            name="test_strategy",
            strategy_type=StrategyType.RETRIEVAL,
            config={},
        )
        
        manager.record_strategy_metrics(
            StrategyType.RETRIEVAL,
            "test_strategy",
            success=True,
            response_time=0.5,
        )
        
        metrics = manager.get_strategy_metrics(
            StrategyType.RETRIEVAL,
            variant_name="test_strategy",
        )
        
        assert metrics["metrics"]["total_requests"] == 1
        assert metrics["metrics"]["success_count"] == 1
    
    def test_get_strategy_metrics(self):
        """测试获取策略指标"""
        manager = StrategyManager()
        
        manager.register_strategy(
            name="strategy1",
            strategy_type=StrategyType.RETRIEVAL,
            config={},
        )
        
        manager.register_strategy(
            name="strategy2",
            strategy_type=StrategyType.RETRIEVAL,
            config={},
        )
        
        # 记录指标
        manager.record_strategy_metrics(
            StrategyType.RETRIEVAL,
            "strategy1",
            success=True,
            response_time=0.5,
        )
        
        # 获取单个变体指标
        metrics = manager.get_strategy_metrics(
            StrategyType.RETRIEVAL,
            variant_name="strategy1",
        )
        
        assert "variant" in metrics
        assert metrics["variant"] == "strategy1"
        
        # 获取类型所有变体指标
        all_metrics = manager.get_strategy_metrics(StrategyType.RETRIEVAL)
        
        assert "variants" in all_metrics
        assert len(all_metrics["variants"]) == 2
    
    def test_disable_enable_strategy(self):
        """测试禁用和启用策略"""
        manager = StrategyManager()
        
        manager.register_strategy(
            name="test_strategy",
            strategy_type=StrategyType.RETRIEVAL,
            config={},
        )
        
        # 禁用
        manager.disable_strategy(StrategyType.RETRIEVAL, "test_strategy")
        
        strategy = manager.get_strategy(StrategyType.RETRIEVAL)
        assert strategy is None or strategy.enabled is False
        
        # 启用
        manager.enable_strategy(StrategyType.RETRIEVAL, "test_strategy")
        
        strategy = manager.get_strategy(StrategyType.RETRIEVAL)
        assert strategy is not None
        assert strategy.enabled is True


class TestGlobalStrategyManager:
    """全局策略管理器测试"""
    
    def test_get_strategy_manager_singleton(self):
        """测试单例模式"""
        manager1 = get_strategy_manager()
        manager2 = get_strategy_manager()
        
        assert manager1 is manager2
    
    def test_default_strategies_init(self):
        """测试默认策略初始化"""
        manager = get_strategy_manager()
        
        # 应该已经有默认策略
        strategies = manager.list_strategies()
        assert len(strategies) > 0

