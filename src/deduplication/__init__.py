"""
Deduplication module initialization

Registers all built-in deduplication strategies.
"""

from .base import DeduplicationStrategy, DeduplicationResult
from .factory import DeduplicationFactory
from .strategies.semantic_dedup import SemanticDeduplicationStrategy

# Register built-in strategies
DeduplicationFactory.register("semantic", SemanticDeduplicationStrategy)

__all__ = [
    "DeduplicationStrategy",
    "DeduplicationResult",
    "DeduplicationFactory",
    "SemanticDeduplicationStrategy",
]
