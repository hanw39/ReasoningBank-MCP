"""存储后端抽象基类"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import numpy as np


class StorageBackend(ABC):
    """存储后端抽���接口"""

    @abstractmethod
    async def add_memory(self, memory: Dict, embedding: List[float]):
        """
        添加记忆

        Args:
            memory: 记忆项字典
            embedding: 嵌入向量
        """
        pass

    @abstractmethod
    async def get_memory_by_id(self, memory_id: str) -> Optional[Dict]:
        """
        获取单个记忆

        Args:
            memory_id: 记忆 ID

        Returns:
            记忆项字典，不存在返回 None
        """
        pass

    @abstractmethod
    async def get_all_memories(self) -> List[Dict]:
        """
        获取所有记忆

        Returns:
            记忆项列表
        """
        pass

    @abstractmethod
    async def get_all_embeddings(self) -> Dict[str, np.ndarray]:
        """
        获取所有嵌入向量

        Returns:
            {memory_id: embedding_vector} 字典
        """
        pass

    @abstractmethod
    async def update_retrieval_stats(self, memory_id: str, timestamp: str):
        """
        更新检索统计

        Args:
            memory_id: 记忆 ID
            timestamp: 检索时间戳
        """
        pass

    @abstractmethod
    async def get_stats(self) -> Dict:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        pass
