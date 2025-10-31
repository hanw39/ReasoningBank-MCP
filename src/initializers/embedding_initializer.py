"""Embedding Provider 初始化器"""

from typing import Any, Dict
from .base import ComponentInitializer
from ..llm import EmbeddingFactory


class EmbeddingInitializer(ComponentInitializer):
    """Embedding Provider 初始化器"""

    @property
    def name(self) -> str:
        return "embedding"

    @property
    def dependencies(self):
        return []  # 无依赖

    async def initialize(self, context: Dict[str, Any]) -> Any:
        """初始化 Embedding Provider"""
        embedding_config = self.config.get_embedding_config()
        return EmbeddingFactory.create(embedding_config)
