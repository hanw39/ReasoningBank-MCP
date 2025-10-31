"""存储后端初始化器"""

from typing import Any, Dict
from .base import ComponentInitializer
from ..storage import StorageFactory


class StorageInitializer(ComponentInitializer):
    """存储后端初始化器"""

    @property
    def name(self) -> str:
        return "storage"

    @property
    def dependencies(self):
        return []  # 无依赖

    async def initialize(self, context: Dict[str, Any]) -> Any:
        """初始化存储后端"""
        storage_config = self.config.get_storage_config()
        return StorageFactory.create(storage_config)
