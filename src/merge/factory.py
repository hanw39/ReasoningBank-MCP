"""
Merge Strategy Factory

Provides plugin mechanism for registering and creating merge strategies.
"""

from typing import Dict, Type, Any
from .base import MergeStrategy


class MergeFactory:
    """Factory for creating merge strategy instances"""

    _strategies: Dict[str, Type[MergeStrategy]] = {}

    @classmethod
    def register(cls, name: str, strategy_class: Type[MergeStrategy]):
        """
        Register a merge strategy.

        Args:
            name: Strategy name (e.g., "llm", "voting", "template")
            strategy_class: Strategy class (must inherit from MergeStrategy)
        """
        cls._strategies[name] = strategy_class

    @classmethod
    def create(cls, config: Any) -> MergeStrategy:
        """
        Create a merge strategy instance based on config.

        Args:
            config: Config object with get() method

        Returns:
            MergeStrategy instance

        Raises:
            ValueError: If strategy name is not registered
        """
        # 使用统一的配置访问方式
        strategy_name = config.get('memory_manager', 'merge', 'strategy', default='voting')

        if strategy_name not in cls._strategies:
            raise ValueError(
                f"Unknown merge strategy: {strategy_name}. "
                f"Available: {list(cls._strategies.keys())}"
            )

        strategy_class = cls._strategies[strategy_name]

        # 获取合并配置
        merge_config = config.get('memory_manager', 'merge', default={})

        return strategy_class(merge_config)

    @classmethod
    def list_strategies(cls) -> list:
        """Return list of registered strategy names"""
        return list(cls._strategies.keys())
