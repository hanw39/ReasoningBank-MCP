"""
Deduplication Strategy Base Interface

Provides pluggable deduplication strategies for memory management.
All operations MUST respect agent_id isolation.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
import numpy as np


@dataclass
class DeduplicationResult:
    """Result of deduplication check"""
    is_duplicate: bool
    duplicate_of: Optional[str] = None  # memory_id of existing memory
    similarity_score: float = 0.0
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class DeduplicationStrategy(ABC):
    """
    Abstract base class for deduplication strategies.

    Key principle: All operations are scoped to a specific agent_id.
    Different agents should have isolated memory spaces.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize strategy with configuration.

        Args:
            config: Strategy-specific configuration dictionary
        """
        self.config = config

    @abstractmethod
    async def check_duplicate(
        self,
        memory: Dict[str, Any],
        embedding: Optional[np.ndarray] = None,
        storage_backend: Any = None,
        agent_id: Optional[str] = None
    ) -> DeduplicationResult:
        """
        Check if a memory is duplicate of existing memories within the same agent_id.

        Args:
            memory: Memory object to check (dict with keys: title, content, query, etc.)
            embedding: Optional pre-computed embedding vector
            storage_backend: Storage backend for querying existing memories
            agent_id: Agent ID for isolation (REQUIRED for multi-tenant safety)

        Returns:
            DeduplicationResult with is_duplicate flag and details
        """
        pass

    @abstractmethod
    async def find_duplicate_groups(
        self,
        storage_backend: Any,
        agent_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[List[str]]:
        """
        Find groups of duplicate memories within the same agent_id.

        Args:
            storage_backend: Storage backend for querying memories
            agent_id: Agent ID for isolation (only search within this agent's memories)
            limit: Maximum number of groups to return

        Returns:
            List of groups, where each group is a list of memory_ids that are duplicates
            Example: [["mem_1", "mem_2"], ["mem_3", "mem_4", "mem_5"]]
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return strategy name for logging and config"""
        pass
