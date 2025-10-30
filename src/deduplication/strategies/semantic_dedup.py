"""
Semantic Deduplication Strategy

Detects semantically similar memories using embedding similarity.
"""

from typing import List, Optional, Dict, Any
import numpy as np
from ..base import DeduplicationStrategy, DeduplicationResult
from ...utils.similarity import cosine_similarity
import logging

logger = logging.getLogger(__name__)


class SemanticDeduplicationStrategy(DeduplicationStrategy):
    """
    Semantic deduplication using embedding cosine similarity.

    Use case: Find memories that describe similar experiences,
    even if the exact wording is different.
    """

    @property
    def name(self) -> str:
        return "semantic"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.threshold = config.get("semantic", {}).get("threshold", 0.90)
        self.top_k = config.get("semantic", {}).get("top_k_check", 1)

    async def check_duplicate(
        self,
        memory: Dict[str, Any],
        embedding: Optional[np.ndarray] = None,
        storage_backend: Any = None,
        agent_id: Optional[str] = None
    ) -> DeduplicationResult:
        """
        Check if semantically similar memories exist for this agent.

        Args:
            memory: Memory dict
            embedding: Pre-computed embedding of memory query (REQUIRED)
            storage_backend: Storage backend
            agent_id: Agent ID for isolation (CRITICAL)
        """
        if embedding is None:
            logger.warning("No embedding provided for semantic dedup check")
            return DeduplicationResult(
                is_duplicate=False,
                reason="No embedding provided"
            )

        if not storage_backend:
            logger.warning("No storage_backend provided")
            return DeduplicationResult(is_duplicate=False)

        # Retrieve similar memories within agent_id scope
        try:
            # Use existing retrieval mechanism with agent_id filter
            from ...retrieval.factory import RetrievalFactory

            # Get retrieval strategy from storage
            retrieval_strategy = storage_backend.retrieval_strategy
            if not retrieval_strategy:
                logger.warning("No retrieval strategy available")
                return DeduplicationResult(is_duplicate=False)

            # Retrieve top-k similar memories
            # Note: query text is not used by retrieval (only embedding),
            # but required by interface
            query_text = memory.get("query", "")
            similar_results = await retrieval_strategy.retrieve(
                query=query_text,
                query_embedding=embedding,
                top_k=self.top_k,
                agent_id=agent_id,  # CRITICAL: Only search within this agent
                storage_backend=storage_backend
            )

            # Check if any exceed threshold
            for mem_id, score in similar_results:
                if score >= self.threshold:
                    existing_mem = await storage_backend.get_memory(mem_id)
                    logger.info(
                        f"Found semantically similar memory: {mem_id} "
                        f"(score={score:.3f}, threshold={self.threshold}) "
                        f"for agent_id={agent_id}"
                    )
                    return DeduplicationResult(
                        is_duplicate=True,
                        duplicate_of=mem_id,
                        similarity_score=score,
                        reason=f"Semantically similar to existing memory (score={score:.3f})",
                        metadata={
                            "existing_title": existing_mem.get("title", ""),
                            "threshold": self.threshold
                        }
                    )

            return DeduplicationResult(
                is_duplicate=False,
                reason=f"No similar memories above threshold {self.threshold}"
            )

        except Exception as e:
            logger.error(f"Error in semantic dedup check: {e}", exc_info=True)
            return DeduplicationResult(
                is_duplicate=False,
                reason=f"Error during check: {str(e)}"
            )

    async def find_duplicate_groups(
        self,
        storage_backend: Any,
        agent_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[List[str]]:
        """
        Find clusters of semantically similar memories within agent_id scope.

        Uses a greedy clustering approach:
        1. For each memory, find all memories above similarity threshold
        2. Group connected memories together
        """
        if not storage_backend:
            return []

        # Get all memories for this agent
        all_memories = await storage_backend.get_all_memories(agent_id=agent_id)
        all_embeddings = await storage_backend.get_embeddings(
            [m["memory_id"] for m in all_memories]
        )

        if len(all_memories) < 2:
            return []

        # Build similarity matrix
        n = len(all_memories)
        visited = set()
        groups = []

        for i in range(n):
            mem_id_i = all_memories[i]["memory_id"]

            if mem_id_i in visited:
                continue

            # Start a new group
            current_group = [mem_id_i]
            visited.add(mem_id_i)

            emb_i = all_embeddings.get(mem_id_i)
            if emb_i is None:
                continue

            # Find all similar memories
            for j in range(i + 1, n):
                mem_id_j = all_memories[j]["memory_id"]

                if mem_id_j in visited:
                    continue

                emb_j = all_embeddings.get(mem_id_j)
                if emb_j is None:
                    continue

                similarity = cosine_similarity(emb_i, emb_j)

                if similarity >= self.threshold:
                    current_group.append(mem_id_j)
                    visited.add(mem_id_j)

            # Only keep groups with 2+ members
            if len(current_group) >= 2:
                groups.append(current_group)

        if limit:
            groups = groups[:limit]

        logger.info(
            f"Found {len(groups)} semantic duplicate groups for agent_id={agent_id}"
        )

        return groups
