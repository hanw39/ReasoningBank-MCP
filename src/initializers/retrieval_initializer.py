"""检索策略初始化器"""

from typing import Any, Dict
from .base import ComponentInitializer
from ..retrieval import RetrievalFactory


class RetrievalInitializer(ComponentInitializer):
    """检索策略初始化器"""

    @property
    def name(self) -> str:
        return "retrieval"

    @property
    def dependencies(self):
        return ["storage"]  # 依赖 storage，因为需要注入到 storage 中

    async def initialize(self, context: Dict[str, Any]) -> Any:
        """初始化检索策略"""
        retrieval_config = self.config.get_retrieval_config()
        retrieval = RetrievalFactory.create(
            retrieval_config["strategy"],
            retrieval_config.get("strategy_config")
        )

        # 注入 retrieval_strategy 到 storage（用于语义去重）
        storage = self._get_component(context, "storage")
        if storage:
            storage.retrieval_strategy = retrieval

        return retrieval
