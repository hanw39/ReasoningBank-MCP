"""MCP 工具初始化器"""

from typing import Any, Dict
from .base import ComponentInitializer
from ..tools import RetrieveMemoryTool, ExtractMemoryTool


class ToolsInitializer(ComponentInitializer):
    """MCP 工具初始化器"""

    @property
    def name(self) -> str:
        return "tools"

    @property
    def dependencies(self):
        # tools 依赖所有其他组件
        return ["storage", "llm", "embedding", "retrieval", "memory_manager"]

    async def initialize(self, context: Dict[str, Any]) -> Any:
        """初始化 MCP 工具"""
        # 获取依赖组件
        storage = self._get_component(context, "storage")
        llm = self._get_component(context, "llm")
        embedding = self._get_component(context, "embedding")
        retrieval = self._get_component(context, "retrieval")
        memory_manager = self._get_component(context, "memory_manager")

        # 创建工具实例
        retrieve_tool = RetrieveMemoryTool(
            self.config,
            storage,
            embedding,
            retrieval
        )

        extract_tool = ExtractMemoryTool(
            self.config,
            storage,
            llm,
            embedding,
            memory_manager
        )

        return {
            "retrieve_tool": retrieve_tool,
            "extract_tool": extract_tool
        }
