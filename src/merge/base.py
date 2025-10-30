"""
Merge Strategy Base Interface

Provides pluggable merge strategies for combining similar memories.
All operations MUST respect agent_id isolation.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class MergeResult:
    """Result of a merge operation"""
    success: bool
    merged_memory_id: Optional[str] = None
    merged_from: List[str] = field(default_factory=list)
    abstraction_level: int = 1  # 0=specific case, 1=pattern, 2=principle
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class MergeStrategy(ABC):
    """
    Abstract base class for merge strategies.

    Different strategies can implement different merge algorithms:
    - LLM-based (extract common patterns)
    - Template-based (rule-based merging)
    - Voting-based (keep best, remove rest)
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize strategy with configuration.

        Args:
            config: Strategy-specific configuration
        """
        self.config = config

    @abstractmethod
    async def should_merge(
        self,
        memories: List[Dict[str, Any]],
        agent_id: Optional[str] = None
    ) -> bool:
        """
        Determine if a group of memories should be merged.

        Args:
            memories: List of memory dicts to evaluate
            agent_id: Agent ID (all memories must belong to same agent)

        Returns:
            True if memories should be merged, False otherwise
        """
        pass

    @abstractmethod
    async def merge(
        self,
        memories: List[Dict[str, Any]],
        agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Merge multiple memories into a single, more general memory.

        Args:
            memories: List of memory dicts to merge (all from same agent_id)
            agent_id: Agent ID for validation

        Returns:
            New merged memory dict with keys:
                - title: str
                - content: str
                - description: str
                - query: str (generalized)
                - abstraction_level: int
                - merged_from: List[str] (memory_ids)
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return strategy name for logging and config"""
        pass
