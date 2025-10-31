"""LLM Provider 初始化器"""

from typing import Any, Dict
from .base import ComponentInitializer
from ..llm import LLMFactory


class LLMInitializer(ComponentInitializer):
    """LLM Provider 初始化器"""

    @property
    def name(self) -> str:
        return "llm"

    @property
    def dependencies(self):
        return []  # 无依赖

    async def initialize(self, context: Dict[str, Any]) -> Any:
        """初始化 LLM Provider"""
        llm_config = self.config.get_llm_config()
        return LLMFactory.create(llm_config)
