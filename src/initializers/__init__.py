"""组件初始化器模块

提供自动化的组件初始化和依赖管理功能。

使用方式：
    from initializers import InitializerRegistry
    from initializers import (
        StorageInitializer,
        LLMInitializer,
        EmbeddingInitializer,
        RetrievalInitializer,
        MemoryManagerInitializer,
        ToolsInitializer
    )

    # 创建注册表
    registry = InitializerRegistry()

    # 自动注册所有初始化器
    registry.auto_register([
        StorageInitializer,
        LLMInitializer,
        EmbeddingInitializer,
        RetrievalInitializer,
        MemoryManagerInitializer,
        ToolsInitializer
    ], config)

    # 自动初始化所有组件
    components = await registry.initialize_all(config)
"""

from .base import ComponentInitializer, InitializerRegistry
from .storage_initializer import StorageInitializer
from .llm_initializer import LLMInitializer
from .embedding_initializer import EmbeddingInitializer
from .retrieval_initializer import RetrievalInitializer
from .memory_manager_initializer import MemoryManagerInitializer
from .tools_initializer import ToolsInitializer

__all__ = [
    "ComponentInitializer",
    "InitializerRegistry",
    "StorageInitializer",
    "LLMInitializer",
    "EmbeddingInitializer",
    "RetrievalInitializer",
    "MemoryManagerInitializer",
    "ToolsInitializer",
]
