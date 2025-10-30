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
    async def get_all_memories(self, agent_id: str = None) -> List[Dict]:
        """
        获取所有记忆

        Args:
            agent_id: Agent ID，用于过滤。None 表示获取所有记忆

        Returns:
            记忆项列表
        """
        pass

    @abstractmethod
    async def get_all_embeddings(self, agent_id: str = None) -> Dict[str, np.ndarray]:
        """
        获取所有嵌入向量

        Args:
            agent_id: Agent ID，用于过滤。None 表示获取所有嵌入

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

    @abstractmethod
    async def save_memories(self, memories: List[Dict], embeddings: Dict[str, np.ndarray]):
        """
        批量保存记忆（用于合并后保存）

        Args:
            memories: 记忆项列表
            embeddings: {memory_id: embedding_vector} 字典
        """
        pass

    @abstractmethod
    async def get_memory(self, memory_id: str) -> Optional[Dict]:
        """
        获取单个记忆（别名，与 get_memory_by_id 相同）

        Args:
            memory_id: 记忆 ID

        Returns:
            记忆项字典，不存在返回 None
        """
        pass

    @abstractmethod
    async def get_embeddings(self, memory_ids: List[str]) -> Dict[str, np.ndarray]:
        """
        获取指定记忆的嵌入向量

        Args:
            memory_ids: 记忆 ID 列表

        Returns:
            {memory_id: embedding_vector} 字典
        """
        pass

    @abstractmethod
    async def archive_memories(self, memories: List[Dict]):
        """
        归档记忆到 archived_memories.json

        Args:
            memories: 要归档的记忆项列表（包含 archived=True 等字段）
        """
        pass

    @abstractmethod
    async def get_archived_memory(self, memory_id: str) -> Optional[Dict]:
        """
        获取已归档的记忆

        Args:
            memory_id: 记忆 ID

        Returns:
            归档的记忆项，不存在返回 None
        """
        pass

    @abstractmethod
    async def delete_memories(self, memory_ids: List[str], agent_id: Optional[str] = None):
        """
        删除记忆

        Args:
            memory_ids: 要删除的记忆 ID 列表
            agent_id: Agent ID，用于安全验证（只能删除该 agent 的记忆）
        """
        pass
