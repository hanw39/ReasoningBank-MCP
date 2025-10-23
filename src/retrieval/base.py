"""检索策略抽象基类"""
from abc import ABC, abstractmethod
from typing import List, Tuple, Dict
import numpy as np


class RetrievalStrategy(ABC):
    """检索策略抽象基类"""

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        query_embedding: np.ndarray,
        storage_backend: 'StorageBackend',
        top_k: int = 1,
        **kwargs
    ) -> List[Tuple[str, float]]:
        """
        检索相关记忆

        Args:
            query: 查询文本
            query_embedding: 查询的嵌入向量
            storage_backend: 存储后端实例
            top_k: 返回的记忆数量
            **kwargs: 其他参数

        Returns:
            [(memory_id, score), ...] 按分数降序排列
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """返回策略名称"""
        pass
