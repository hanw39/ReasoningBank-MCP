"""
Voting-based Merge Strategy

Selects the "best" memory from a group and removes the rest.
Does not create a new merged memory, just chooses a representative.
"""

from typing import List, Dict, Any, Optional
from ..base import MergeStrategy
import logging

logger = logging.getLogger(__name__)


class VotingMergeStrategy(MergeStrategy):
    """
    Voting merge: Select best memory, remove others.

    Selection criteria (in priority order):
    1. Highest retrieval_count (most used)
    2. Success=true preferred over false
    3. Most recent timestamp
    """

    @property
    def name(self) -> str:
        return "voting"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.min_group_size = config.get("voting", {}).get("min_group_size", 2)

    async def should_merge(
        self,
        memories: List[Dict[str, Any]],
        agent_id: Optional[str] = None
    ) -> bool:
        """
        Check if group meets minimum size requirement.
        Also validates all memories belong to the same agent.
        """
        if len(memories) < self.min_group_size:
            return False

        # Validate all memories have same agent_id
        if agent_id:
            for mem in memories:
                if mem.get("agent_id") != agent_id:
                    logger.warning(
                        f"Memory {mem.get('memory_id')} has different agent_id: "
                        f"{mem.get('agent_id')} != {agent_id}"
                    )
                    return False

        return True

    async def merge(
        self,
        memories: List[Dict[str, Any]],
        agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Select the "best" memory from the group.

        Returns the selected memory with added merge metadata.
        """
        if not memories:
            raise ValueError("Cannot merge empty memory list")

        # Validate agent_id consistency
        if agent_id:
            for mem in memories:
                if mem.get("agent_id") != agent_id:
                    raise ValueError(
                        f"Memory {mem.get('memory_id')} belongs to different agent"
                    )

        # Sort by: retrieval_count (desc), success (desc), timestamp (desc)
        # todo 是否不公平，对于新经验
        def sort_key(mem):
            return (
                mem.get("retrieval_count", 0),  # Higher is better
                1 if mem.get("success", False) else 0,  # Success preferred
                mem.get("timestamp", "")  # More recent preferred
            )

        sorted_memories = sorted(memories, key=sort_key, reverse=True)
        best_memory = sorted_memories[0]

        logger.info(
            f"Selected best memory: {best_memory.get('memory_id')} "
            f"from group of {len(memories)} (agent_id={agent_id})"
        )

        # Return the best memory with merge metadata
        merged_from = [ m["memory_id"] for m in memories if m["memory_id"] != best_memory["memory_id"] ]

        return {
            **best_memory,
            "is_merged": True,
            "merged_from": merged_from,
            "merge_metadata": {
                "merge_strategy": self.name,
                "original_count": len(memories),
                "selection_reason": "highest_usage",
                "abstraction_level": 0  # Same level, just selected best
            }
        }
