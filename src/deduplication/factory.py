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
    def create(cls, config: Dict[str, Any]) -> DeduplicationStrategy:
        """
        Create a deduplication strategy instance based on config.

        Args:
            config: Configuration dict with "deduplication.strategy" key

        Returns:
            DeduplicationStrategy instance

        Raises:
            ValueError: If strategy name is not registered
        """
        # Extract deduplication config
        # todo 风格不统一
        dedup_config = config.get("memory_manager", {}).get("deduplication", {})
        strategy_name = dedup_config.get("strategy", "semantic")

        if strategy_name not in cls._strategies:
            raise ValueError(
                f"Unknown deduplication strategy: {strategy_name}. "
                f"Available: {list(cls._strategies.keys())}"
            )

        strategy_class = cls._strategies[strategy_name]

        return strategy_class(dedup_config)

    @classmethod
    def list_strategies(cls) -> list:
        """Return list of registered strategy names"""
        return list(cls._strategies.keys())
