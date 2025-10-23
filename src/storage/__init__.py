"""存储后端模块"""
from .base import StorageBackend
from .backends.json_backend import JSONStorageBackend


class StorageFactory:
    """存储后端工厂"""

    _backends = {
        "json": JSONStorageBackend,
    }

    @classmethod
    def create(cls, config: dict) -> StorageBackend:
        """
        创建存储后端实例

        Args:
            config: 配置字典，包含 'backend' 键和对应配置

        Returns:
            StorageBackend 实例
        """
        backend_name = config.get("backend", "json")

        if backend_name not in cls._backends:
            raise ValueError(
                f"Unknown storage backend: {backend_name}. "
                f"Available backends: {list(cls._backends.keys())}"
            )

        backend_class = cls._backends[backend_name]
        return backend_class(config)

    @classmethod
    def register_backend(cls, name: str, backend_class: type):
        """注册新的存储后端（插件机制）"""
        cls._backends[name] = backend_class


__all__ = [
    "StorageBackend",
    "JSONStorageBackend",
    "StorageFactory",
]
