"""
Merge module initialization

Registers all built-in merge strategies.
"""

from .base import MergeStrategy, MergeResult
from .factory import MergeFactory
from .strategies.voting_merge import VotingMergeStrategy
from .strategies.llm_merge import LLMMergeStrategy

# Register built-in strategies
MergeFactory.register("voting", VotingMergeStrategy)
MergeFactory.register("llm", LLMMergeStrategy)

__all__ = [
    "MergeStrategy",
    "MergeResult",
    "MergeFactory",
    "VotingMergeStrategy",
    "LLMMergeStrategy",
]
