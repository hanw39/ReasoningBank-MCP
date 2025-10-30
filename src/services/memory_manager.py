"""
Memory Manager Service

Core service for managing memory deduplication, merging, and cleanup.
All operations respect agent_id isolation.
"""

from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
from dataclasses import dataclass, field
import asyncio
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class MemoryManagementResult:
    """Result of memory management operations"""
    success: bool
    action: str  # "saved", "skipped_duplicate", "merged", "error"
    memory_ids: List[str] = field(default_factory=list)
    duplicates_found: int = 0
    merged_count: int = 0
    message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class MemoryManager:
    """
    Memory Manager: Orchestrates deduplication, merging, and cleanup.

    Core responsibilities:
    1. Real-time deduplication on memory creation
    2. Trigger merging when similar memories accumulate
    3. Archive original memories after merge
    4. All operations are agent_id scoped
    """

    def __init__(
        self,
        storage_backend,
        dedup_strategy,
        merge_strategy,
        embedding_provider,
        llm_provider,
        config: Dict[str, Any]
    ):
        """
        Initialize MemoryManager.

        Args:
            storage_backend: Storage backend instance
            dedup_strategy: Deduplication strategy instance
            merge_strategy: Merge strategy instance
            embedding_provider: Embedding provider for new memories
            llm_provider: LLM provider for merge operations
            config: Configuration dict
        """
        self.storage = storage_backend
        self.dedup_strategy = dedup_strategy
        self.merge_strategy = merge_strategy
        self.embedding_provider = embedding_provider
        self.llm_provider = llm_provider
        self.config = config

        # Inject LLM provider into merge strategy if needed
        if hasattr(merge_strategy, 'set_llm_provider'):
            merge_strategy.set_llm_provider(llm_provider)

        # Configuration
        self.manager_config = config.get("memory_manager", {})
        self.dedup_on_extraction = self.manager_config.get("deduplication", {}).get("on_extraction", True)
        self.merge_auto_execute = self.manager_config.get("merge", {}).get("auto_execute", True)
        self.merge_min_similar = self.manager_config.get("merge", {}).get("trigger", {}).get("min_similar_count", 3)
        self.merge_threshold = self.manager_config.get("merge", {}).get("trigger", {}).get("similarity_threshold", 0.85)

        logger.info(
            f"MemoryManager initialized: "
            f"dedup={self.dedup_on_extraction}, "
            f"auto_merge={self.merge_auto_execute}"
        )

    async def on_memory_created(
        self,
        new_memories: List[Dict[str, Any]],
        embeddings: Dict[str, Any],
        agent_id: Optional[str] = None
    ) -> MemoryManagementResult:
        """
        Hook called after memories are extracted but before saving.

        Process:
        1. Check for duplicates (agent_id scoped)
        2. Filter out duplicates
        3. Check if merge should be triggered (agent_id scoped)
        4. Return filtered memories and merge status

        Args:
            new_memories: List of newly extracted memories
            embeddings: Dict mapping memory_id to embedding vector
            agent_id: Agent ID (CRITICAL for isolation)

        Returns:
            MemoryManagementResult with filtered memories and actions taken
        """
        logger.info(
            f"MemoryManager.on_memory_created: {len(new_memories)} new memories "
            f"for agent_id={agent_id}"
        )

        unique_memories = []
        duplicate_count = 0
        merge_triggered = []

        # Step 1: Deduplication check
        if self.dedup_on_extraction:
            for mem in new_memories:
                embedding = embeddings.get(mem["memory_id"])

                dedup_result = await self.dedup_strategy.check_duplicate(
                    memory=mem,
                    embedding=embedding,
                    storage_backend=self.storage,
                    agent_id=agent_id  # CRITICAL: Only check within this agent
                )

                if dedup_result.is_duplicate:
                    logger.info(
                        f"Skipping duplicate memory: {mem.get('title', 'N/A')} "
                        f"(similar to {dedup_result.duplicate_of}, agent_id={agent_id})"
                    )
                    duplicate_count += 1
                else:
                    unique_memories.append(mem)
        else:
            unique_memories = new_memories

        # Step 2: Check if merge should be triggered
        if self.merge_auto_execute and unique_memories:
            for mem in unique_memories:
                try:
                    merge_check = await self._check_merge_opportunity(
                        memory=mem,
                        embedding=embeddings.get(mem["memory_id"]),
                        agent_id=agent_id
                    )

                    if merge_check:
                        merge_triggered.append(merge_check)
                except Exception as e:
                    logger.error(f"Error checking merge opportunity: {e}", exc_info=True)

        return MemoryManagementResult(
            success=True,
            action="processed",
            memory_ids=[m["memory_id"] for m in unique_memories],
            duplicates_found=duplicate_count,
            merged_count=len(merge_triggered),
            message=f"Processed {len(unique_memories)} unique memories, "
                    f"skipped {duplicate_count} duplicates, "
                    f"triggered {len(merge_triggered)} merges",
            metadata={
                "unique_memories": unique_memories,
                "merge_tasks": merge_triggered
            }
        )

    async def _check_merge_opportunity(
        self,
        memory: Dict[str, Any],
        embedding: Any,
        agent_id: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Check if new memory creates a merge opportunity.

        Logic:
        1. Find similar memories (agent_id scoped)
        2. If similar_count >= threshold, trigger merge
        3. Execute merge in background

        Returns:
            Merge task info if triggered, None otherwise
        """
        if not embedding:
            return None

        # Retrieve similar memories within agent_id scope
        try:
            retrieval_strategy = self.storage.retrieval_strategy
            if not retrieval_strategy:
                return None

            # Retrieve similar memories within agent_id scope
            query_text = memory.get("query", "")
            similar_results = await retrieval_strategy.retrieve(
                query=query_text,
                query_embedding=embedding,
                top_k=10,  # Check top 10
                agent_id=agent_id,  # CRITICAL: Only search within this agent
                storage_backend=self.storage
            )

            # Filter by threshold
            similar_ids = [
                mem_id for mem_id, score in similar_results
                if score >= self.merge_threshold
            ]

            if len(similar_ids) >= self.merge_min_similar:
                logger.info(
                    f"Merge opportunity detected: {len(similar_ids)} similar memories "
                    f"for agent_id={agent_id}"
                )

                # Fetch full memory objects
                similar_memories = []
                for mem_id in similar_ids:
                    mem = await self.storage.get_memory(mem_id)
                    if mem:
                        similar_memories.append(mem)

                # Add the new memory to the group
                similar_memories.append(memory)

                # Check if should merge
                should_merge = await self.merge_strategy.should_merge(
                    similar_memories,
                    agent_id=agent_id
                )

                if should_merge:
                    # Execute merge in background
                    asyncio.create_task(
                        self._execute_merge(similar_memories, agent_id)
                    )

                    return {
                        "group_size": len(similar_memories),
                        "memory_ids": [m["memory_id"] for m in similar_memories]
                    }

        except Exception as e:
            logger.error(f"Error in merge opportunity check: {e}", exc_info=True)

        return None

    async def _execute_merge(
        self,
        memories: List[Dict[str, Any]],
        agent_id: Optional[str]
    ):
        """
        Execute merge operation in background.

        Steps:
        1. Call merge strategy to create merged memory
        2. Generate embedding for merged memory
        3. Save merged memory
        4. Archive original memories
        5. Delete original memories from active storage
        """
        try:
            logger.info(
                f"Executing merge: {len(memories)} memories for agent_id={agent_id}"
            )

            # Step 1: Merge
            merged_data = await self.merge_strategy.merge(memories, agent_id=agent_id)

            # Step 2: Generate memory_id and timestamp
            merged_memory = {
                **merged_data,
                "memory_id": f"mem_merged_{uuid4().hex[:16]}",
                "timestamp": datetime.now().isoformat(),
                "retrieval_count": 0,
                "last_retrieved": None
            }

            # Step 3: Generate embedding
            query_text = merged_memory.get("query", merged_memory.get("description", ""))
            embedding = await self.embedding_provider.embed(query_text)

            # Step 4: Save merged memory
            await self.storage.save_memories(
                [merged_memory],
                {merged_memory["memory_id"]: embedding}
            )

            logger.info(
                f"Merged memory saved: {merged_memory['memory_id']} "
                f"(agent_id={agent_id})"
            )

            # Step 5: Archive originals
            await self._archive_memories(
                memories,
                merged_into=merged_memory["memory_id"],
                agent_id=agent_id
            )

            logger.info(
                f"Merge completed: {len(memories)} memories -> "
                f"{merged_memory['memory_id']} (agent_id={agent_id})"
            )

        except Exception as e:
            logger.error(
                f"Error executing merge for agent_id={agent_id}: {e}",
                exc_info=True
            )

    async def _archive_memories(
        self,
        memories: List[Dict[str, Any]],
        merged_into: str,
        agent_id: Optional[str]
    ):
        """
        Archive original memories after merge.

        Args:
            memories: Original memories to archive
            merged_into: ID of merged memory
            agent_id: Agent ID for validation
        """
        archived_data = []

        for mem in memories:
            # Validate agent_id
            if agent_id and mem.get("agent_id") != agent_id:
                logger.warning(
                    f"Skipping archive: memory {mem['memory_id']} has different agent_id"
                )
                continue

            archived_mem = {
                **mem,
                "archived": True,
                "archived_at": datetime.now().isoformat(),
                "archived_reason": "merged",
                "merged_into": merged_into,
                "original_retrieval_count": mem.get("retrieval_count", 0)
            }
            archived_data.append(archived_mem)

        if archived_data:
            # Archive to storage
            await self.storage.archive_memories(archived_data)

            # Delete from active storage
            memory_ids = [m["memory_id"] for m in archived_data]
            await self.storage.delete_memories(memory_ids, agent_id=agent_id)

            logger.info(
                f"Archived {len(archived_data)} memories for agent_id={agent_id}"
            )

    async def cleanup_duplicates(
        self,
        agent_id: Optional[str] = None,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Find and remove duplicate memories (agent_id scoped).

        Args:
            agent_id: Only cleanup within this agent's memories (None = all agents)
            dry_run: If True, only report what would be deleted

        Returns:
            Cleanup report dict
        """
        logger.info(
            f"Running duplicate cleanup for agent_id={agent_id}, dry_run={dry_run}"
        )

        duplicate_groups = await self.dedup_strategy.find_duplicate_groups(
            storage_backend=self.storage,
            agent_id=agent_id
        )

        to_delete = []
        to_keep = []

        for group in duplicate_groups:
            # Keep the first one (arbitrary choice), delete rest
            to_keep.append(group[0])
            to_delete.extend(group[1:])

        if not dry_run and to_delete:
            await self.storage.delete_memories(to_delete, agent_id=agent_id)

        return {
            "agent_id": agent_id,
            "duplicate_groups": len(duplicate_groups),
            "memories_to_delete": len(to_delete),
            "memories_to_keep": len(to_keep),
            "dry_run": dry_run,
            "deleted_ids": [] if dry_run else to_delete
        }
