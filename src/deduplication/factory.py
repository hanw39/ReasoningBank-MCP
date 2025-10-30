"""
Deduplication Strategy Factory

Provides plugin mechanism for registering and creating deduplication strategies.
"""

from typing import Dict, Type, Any
from .base import DeduplicationStrategy


class DeduplicationFactory:
    """Factory for creating deduplication strategy instances"""

    _strategies: Dict[str, Type[DeduplicationStrategy]] = {}

    @classmethod
    def register(cls, name: str, strategy_class: Type[DeduplicationStrategy]):
        """
        Register a deduplication strategy.

        Args:
            name: Strategy name (e.g., "hash", "semantic", "hybrid")
            strategy_class: Strategy class (must inherit from DeduplicationStrategy)
        """
        cls._strategies[name] = strategy_class

    @classmethod
    def create(cls, config: Any) -> DeduplicationStrategy:
        """
        Create a deduplication strategy instance based on config.

        Args:
            config: Config object with get() method

        Returns:
            DeduplicationStrategy instance

        Raises:
            ValueError: If strategy name is not registered
        """
        # 使用统一的配置访问方式
        strategy_name = config.get('memory_manager', 'deduplication', 'strategy', default='semantic')

        if strategy_name not in cls._strategies:
            raise ValueError(
                f"Unknown deduplication strategy: {strategy_name}. "
                f"Available: {list(cls._strategies.keys())}"
            )

        strategy_class = cls._strategies[strategy_name]

        # 获取去重配置
        dedup_config = config.get('memory_manager', 'deduplication', default={})

        return strategy_class(dedup_config)

    @classmethod
    def list_strategies(cls) -> list:
        """Return list of registered strategy names"""
        return list(cls._strategies.keys())
