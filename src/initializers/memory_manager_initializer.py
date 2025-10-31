"""记忆管理器初始化器"""

import logging
from typing import Any, Dict
from .base import ComponentInitializer
from ..services import MemoryManager
from ..deduplication import DeduplicationFactory
from ..merge import MergeFactory

logger = logging.getLogger("reasoning-bank-mcp")


class MemoryManagerInitializer(ComponentInitializer):
    """记忆管理器初始化器"""

    @property
    def name(self) -> str:
        return "memory_manager"

    @property
    def dependencies(self):
        return ["storage", "llm", "embedding"]  # 依赖这三个组件

    @property
    def enabled(self) -> bool:
        """根据配置判断是否启用"""
        return self.config.get("memory_manager", "enabled", default=True)

    async def initialize(self, context: Dict[str, Any]) -> Any:
        """初始化记忆管理器"""
        # 获取依赖组件
        storage = self._get_component(context, "storage")
        llm = self._get_component(context, "llm")
        embedding = self._get_component(context, "embedding")

        # 创建去重策略（传递 Config 对象）
        dedup_strategy = DeduplicationFactory.create(self.config)

        # 创建合并策略（传递 Config 对象）
        merge_strategy = MergeFactory.create(self.config)

        # 创建记忆管理器
        memory_manager = MemoryManager(
            storage_backend=storage,
            dedup_strategy=dedup_strategy,
            merge_strategy=merge_strategy,
            embedding_provider=embedding,
            llm_provider=llm,
            config=self.config.all
        )

        logger.info(f"  - 去重策略: {dedup_strategy.name}")
        logger.info(f"  - 合并策略: {merge_strategy.name}")

        return memory_manager
