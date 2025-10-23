"""检索策略工厂"""
from typing import Dict
from .base import RetrievalStrategy
from .strategies import CosineRetrievalStrategy, HybridRetrievalStrategy


class RetrievalFactory:
    """检索策略工厂"""

    _strategies = {
        "cosine": CosineRetrievalStrategy,
        "hybrid": HybridRetrievalStrategy,
    }

    @classmethod
    def create(cls, strategy_name: str, config: Dict = None) -> RetrievalStrategy:
        """
        创建检索策略实例

        Args:
            strategy_name: 策略名称 ("cosine" | "hybrid")
            config: 策略配置参数

        Returns:
            RetrievalStrategy 实例
        """
        if strategy_name not in cls._strategies:
            raise ValueError(
                f"Unknown retrieval strategy: {strategy_name}. "
                f"Available strategies: {list(cls._strategies.keys())}"
            )

        strategy_class = cls._strategies[strategy_name]

        # 根据策略类型传递配置
        if strategy_name == "hybrid":
            return strategy_class(config)
        else:
            return strategy_class()

    @classmethod
    def register_strategy(cls, name: str, strategy_class: type):
        """
        注册新的检索策略（插件机制）

        Args:
            name: 策略名称
            strategy_class: 策略类
        """
        cls._strategies[name] = strategy_class

    @classmethod
    def list_strategies(cls) -> list:
        """返回所有可用的策略名称"""
        return list(cls._strategies.keys())
