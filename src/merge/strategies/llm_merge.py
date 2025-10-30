"""
LLM-based Merge Strategy

Uses LLM to extract common patterns and create a generalized memory.
"""

from typing import List, Dict, Any, Optional
from ..base import MergeStrategy
import logging
import json

logger = logging.getLogger(__name__)


class LLMMergeStrategy(MergeStrategy):
    """
    LLM-driven merge: Extract common patterns from similar memories.

    Creates a new, more abstract memory that captures the essence
    of multiple specific experiences.
    """

    @property
    def name(self) -> str:
        return "llm"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.min_group_size = config.get("trigger", {}).get("min_similar_count", 3)
        self.llm_config = config.get("llm", {})
        self.temperature = self.llm_config.get("temperature", 0.7)
        self.llm_provider = None  # Will be injected by MemoryManager

    def set_llm_provider(self, llm_provider):
        """Inject LLM provider dependency"""
        self.llm_provider = llm_provider

    async def should_merge(
        self,
        memories: List[Dict[str, Any]],
        agent_id: Optional[str] = None
    ) -> bool:
        """
        Check if group meets criteria for LLM merge.

        Requirements:
        1. At least min_group_size memories
        2. All from same agent_id
        3. Majority should be successful experiences
        """
        if len(memories) < self.min_group_size:
            return False

        # Validate agent_id consistency
        if agent_id:
            for mem in memories:
                if mem.get("agent_id") != agent_id:
                    logger.warning(
                        f"Memory {mem.get('memory_id')} has different agent_id"
                    )
                    return False

        # Check success rate
        success_count = sum(1 for m in memories if m.get("success", False))
        success_rate = success_count / len(memories)

        # Only merge if majority are successful (avoid mixing success/failure)
        if success_rate < 0.6:
            logger.info(
                f"Success rate too low ({success_rate:.2f}) for merge, "
                f"agent_id={agent_id}"
            )
            return False

        return True

    async def merge(
        self,
        memories: List[Dict[str, Any]],
        agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Use LLM to extract common patterns and create generalized memory.

        Args:
            memories: List of similar memories (all from same agent_id)
            agent_id: Agent ID for validation

        Returns:
            New merged memory dict
        """
        if not self.llm_provider:
            raise RuntimeError("LLM provider not set. Call set_llm_provider() first.")

        if not memories:
            raise ValueError("Cannot merge empty memory list")

        # Validate agent_id
        if agent_id:
            for mem in memories:
                if mem.get("agent_id") != agent_id:
                    raise ValueError(
                        f"Memory {mem.get('memory_id')} belongs to different agent"
                    )

        # Build prompt for LLM
        prompt = self._build_merge_prompt(memories)

        # Call LLM
        try:
            response = await self.llm_provider.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature
            )

            # Parse JSON response
            merged_data = json.loads(response)

            # Validate response
            required_fields = ["title", "content", "description", "abstraction_level"]
            for field in required_fields:
                if field not in merged_data:
                    raise ValueError(f"LLM response missing required field: {field}")

            # Build merged memory
            merged_memory = {
                "title": merged_data["title"],
                "content": merged_data["content"],
                "description": merged_data["description"],
                "query": merged_data.get("query", "<通用场景>"),
                "success": True,  # Merged memories are positive learnings
                "agent_id": agent_id,
                "is_merged": True,
                "merged_from": [m["memory_id"] for m in memories],
                "merge_metadata": {
                    "merge_strategy": self.name,
                    "original_count": len(memories),
                    "abstraction_level": merged_data.get("abstraction_level", 1),
                    "llm_model": self.llm_config.get("model", "unknown")
                }
            }

            logger.info(
                f"LLM merge successful: {len(memories)} memories -> "
                f"'{merged_memory['title']}' (agent_id={agent_id})"
            )

            return merged_memory

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            raise
        except Exception as e:
            logger.error(f"Error during LLM merge: {e}", exc_info=True)
            raise

    def _build_merge_prompt(self, memories: List[Dict[str, Any]]) -> str:
        """Build prompt for LLM to merge memories"""

        # Format memories for LLM
        memories_text = ""
        for i, mem in enumerate(memories, 1):
            memories_text += f"\n### 经验 {i}\n"
            memories_text += f"**标题**: {mem.get('title', 'N/A')}\n"
            memories_text += f"**描述**: {mem.get('description', 'N/A')}\n"
            memories_text += f"**内容**: {mem.get('content', 'N/A')}\n"
            memories_text += f"**原始场景**: {mem.get('query', 'N/A')}\n"
        from ...prompts.templates import get_merge_prompt

        return get_merge_prompt(memories_text)
