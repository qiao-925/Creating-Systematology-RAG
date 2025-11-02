"""
策略管理器

管理不同的检索策略，支持运行时切换和A/B测试
"""

from typing import Dict, List, Optional, Any
from enum import Enum
import random
import time

from src.logger import setup_logger
from src.config import config

logger = setup_logger('strategy_manager')


class StrategyType(Enum):
    """策略类型"""
    RETRIEVAL = "retrieval"
    RERANKING = "reranking"
    GENERATION = "generation"


class StrategyVariant:
    """策略变体"""
    
    def __init__(
        self,
        name: str,
        strategy_type: StrategyType,
        config: Dict[str, Any],
        weight: float = 1.0,
        enabled: bool = True,
    ):
        """初始化策略变体
        
        Args:
            name: 变体名称
            strategy_type: 策略类型
            config: 策略配置
            weight: 权重（用于A/B测试）
            enabled: 是否启用
        """
        self.name = name
        self.strategy_type = strategy_type
        self.config = config
        self.weight = weight
        self.enabled = enabled
        self.metrics: Dict[str, Any] = {
            "total_requests": 0,
            "success_count": 0,
            "error_count": 0,
            "avg_response_time": 0.0,
        }
    
    def record_request(self, success: bool, response_time: float):
        """记录请求指标"""
        self.metrics["total_requests"] += 1
        if success:
            self.metrics["success_count"] += 1
        else:
            self.metrics["error_count"] += 1
        
        # 更新平均响应时间
        total = self.metrics["total_requests"]
        current_avg = self.metrics["avg_response_time"]
        self.metrics["avg_response_time"] = (
            (current_avg * (total - 1) + response_time) / total
        )
    
    def get_success_rate(self) -> float:
        """获取成功率"""
        total = self.metrics["total_requests"]
        if total == 0:
            return 0.0
        return self.metrics["success_count"] / total
    
    def __repr__(self) -> str:
        return f"StrategyVariant(name={self.name}, type={self.strategy_type.value}, weight={self.weight})"


class StrategyManager:
    """策略管理器
    
    管理不同的策略变体，支持：
    - 策略切换
    - A/B测试
    - 性能监控
    """
    
    def __init__(self):
        """初始化策略管理器"""
        self._strategies: Dict[StrategyType, List[StrategyVariant]] = {
            strategy_type: []
            for strategy_type in StrategyType
        }
        self._default_strategies: Dict[StrategyType, str] = {}
        self._ab_test_enabled: Dict[StrategyType, bool] = {
            strategy_type: False
            for strategy_type in StrategyType
        }
        
        logger.info("策略管理器初始化")
    
    def register_strategy(
        self,
        name: str,
        strategy_type: StrategyType,
        config: Dict[str, Any],
        weight: float = 1.0,
        is_default: bool = False,
    ):
        """注册策略变体
        
        Args:
            name: 策略名称
            strategy_type: 策略类型
            config: 策略配置
            weight: 权重（用于A/B测试）
            is_default: 是否设为默认策略
        """
        variant = StrategyVariant(
            name=name,
            strategy_type=strategy_type,
            config=config,
            weight=weight,
        )
        
        self._strategies[strategy_type].append(variant)
        
        if is_default or not self._default_strategies.get(strategy_type):
            self._default_strategies[strategy_type] = name
        
        logger.info(
            f"注册策略: {name} (type={strategy_type.value}, weight={weight})"
        )
    
    def get_strategy(
        self,
        strategy_type: StrategyType,
        variant_name: Optional[str] = None,
        enable_ab_test: bool = False,
    ) -> Optional[StrategyVariant]:
        """获取策略变体
        
        Args:
            strategy_type: 策略类型
            variant_name: 变体名称（可选，默认使用默认策略或A/B测试）
            enable_ab_test: 是否启用A/B测试
            
        Returns:
            StrategyVariant实例
        """
        variants = self._strategies.get(strategy_type, [])
        if not variants:
            logger.warning(f"未找到策略: {strategy_type.value}")
            return None
        
        # 过滤启用的变体
        enabled_variants = [v for v in variants if v.enabled]
        if not enabled_variants:
            logger.warning(f"未找到启用的策略: {strategy_type.value}")
            return None
        
        # 如果指定了变体名称，直接返回
        if variant_name:
            for variant in enabled_variants:
                if variant.name == variant_name:
                    return variant
            logger.warning(f"未找到策略变体: {variant_name}")
            return None
        
        # A/B测试：按权重随机选择
        if enable_ab_test and self._ab_test_enabled.get(strategy_type, False):
            return self._select_by_weight(enabled_variants)
        
        # 默认策略
        default_name = self._default_strategies.get(strategy_type)
        if default_name:
            for variant in enabled_variants:
                if variant.name == default_name:
                    return variant
        
        # 如果没有默认策略，返回第一个启用的变体
        return enabled_variants[0]
    
    def _select_by_weight(self, variants: List[StrategyVariant]) -> StrategyVariant:
        """按权重随机选择策略变体（用于A/B测试）"""
        if not variants:
            return None
        
        # 计算总权重
        total_weight = sum(v.weight for v in variants)
        if total_weight == 0:
            return variants[0]
        
        # 随机选择
        rand = random.random() * total_weight
        cumulative = 0.0
        
        for variant in variants:
            cumulative += variant.weight
            if rand <= cumulative:
                return variant
        
        return variants[-1]
    
    def enable_ab_test(self, strategy_type: StrategyType, enabled: bool = True):
        """启用/禁用A/B测试"""
        self._ab_test_enabled[strategy_type] = enabled
        logger.info(f"A/B测试 {'启用' if enabled else '禁用'}: {strategy_type.value}")
    
    def set_default_strategy(self, strategy_type: StrategyType, variant_name: str):
        """设置默认策略"""
        variants = self._strategies.get(strategy_type, [])
        for variant in variants:
            if variant.name == variant_name:
                self._default_strategies[strategy_type] = variant_name
                logger.info(f"设置默认策略: {strategy_type.value} -> {variant_name}")
                return
        
        logger.warning(f"未找到策略变体: {variant_name}")
    
    def record_strategy_metrics(
        self,
        strategy_type: StrategyType,
        variant_name: str,
        success: bool,
        response_time: float,
    ):
        """记录策略指标"""
        variant = self.get_strategy(strategy_type, variant_name)
        if variant:
            variant.record_request(success, response_time)
    
    def get_strategy_metrics(
        self,
        strategy_type: Optional[StrategyType] = None,
        variant_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取策略指标
        
        Args:
            strategy_type: 策略类型（可选）
            variant_name: 变体名称（可选）
            
        Returns:
            指标字典
        """
        if strategy_type and variant_name:
            # 获取特定变体的指标
            variant = self.get_strategy(strategy_type, variant_name)
            if variant:
                return {
                    "variant": variant.name,
                    "type": strategy_type.value,
                    "metrics": variant.metrics.copy(),
                    "success_rate": variant.get_success_rate(),
                }
        elif strategy_type:
            # 获取该类型所有变体的指标
            variants = self._strategies.get(strategy_type, [])
            return {
                "type": strategy_type.value,
                "variants": [
                    {
                        "name": v.name,
                        "metrics": v.metrics.copy(),
                        "success_rate": v.get_success_rate(),
                    }
                    for v in variants
                ]
            }
        else:
            # 获取所有策略的指标
            return {
                "all_strategies": {
                    strategy_type.value: self.get_strategy_metrics(strategy_type)
                    for strategy_type in StrategyType
                    if self._strategies.get(strategy_type)
                }
            }
        
        return {}
    
    def list_strategies(self, strategy_type: Optional[StrategyType] = None) -> List[str]:
        """列出策略名称"""
        if strategy_type:
            return [v.name for v in self._strategies.get(strategy_type, [])]
        else:
            all_names = []
            for variants in self._strategies.values():
                all_names.extend([v.name for v in variants])
            return all_names
    
    def disable_strategy(self, strategy_type: StrategyType, variant_name: str):
        """禁用策略变体"""
        variants = self._strategies.get(strategy_type, [])
        for variant in variants:
            if variant.name == variant_name:
                variant.enabled = False
                logger.info(f"禁用策略: {variant_name}")
                return
        
        logger.warning(f"未找到策略变体: {variant_name}")
    
    def enable_strategy(self, strategy_type: StrategyType, variant_name: str):
        """启用策略变体"""
        variants = self._strategies.get(strategy_type, [])
        for variant in variants:
            if variant.name == variant_name:
                variant.enabled = True
                logger.info(f"启用策略: {variant_name}")
                return
        
        logger.warning(f"未找到策略变体: {variant_name}")


# 全局策略管理器实例
_global_strategy_manager: Optional[StrategyManager] = None


def get_strategy_manager() -> StrategyManager:
    """获取全局策略管理器"""
    global _global_strategy_manager
    if _global_strategy_manager is None:
        _global_strategy_manager = StrategyManager()
        _init_default_strategies(_global_strategy_manager)
    return _global_strategy_manager


def reset_strategy_manager():
    """重置全局策略管理器（用于测试）"""
    global _global_strategy_manager
    _global_strategy_manager = None
    logger.info("策略管理器已重置")


def _init_default_strategies(manager: StrategyManager):
    """初始化默认策略"""
    # 注册默认检索策略
    manager.register_strategy(
        name="vector",
        strategy_type=StrategyType.RETRIEVAL,
        config={"retrieval_strategy": "vector"},
        is_default=True,
    )
    
    manager.register_strategy(
        name="multi",
        strategy_type=StrategyType.RETRIEVAL,
        config={"retrieval_strategy": "multi"},
        weight=0.5,
    )
    
    # 注册默认重排序策略
    manager.register_strategy(
        name="sentence_transformer",
        strategy_type=StrategyType.RERANKING,
        config={"reranker_type": "sentence-transformer"},
        is_default=True,
    )
    
    manager.register_strategy(
        name="bge",
        strategy_type=StrategyType.RERANKING,
        config={"reranker_type": "bge"},
        weight=0.5,
    )
    
    logger.info("默认策略初始化完成")

