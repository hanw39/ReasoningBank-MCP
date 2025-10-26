"""余弦相似度检索策略（论文基线方法）"""
from typing import List, Tuple
import numpy as np
from ..base import RetrievalStrategy
from ...utils.similarity import cosine_similarity


class CosineRetrievalStrategy(RetrievalStrategy):
    """纯余弦相似度检索策略"""

    async def retrieve(
        self,
        query: str,
        query_embedding: np.ndarray,
        storage_backend,
        top_k: int = 1,
        agent_id: str = None,
        **kwargs
    ) -> List[Tuple[str, float]]:
        """
        使用余弦相似度检索记忆

        这是论文中使用的基线方法

        Args:
            agent_id: Agent ID，用于过滤记忆
        """
        # 获取所有记忆的嵌入（支持 agent_id 过滤）
        memory_embeddings = await storage_backend.get_all_embeddings(agent_id)

        if not memory_embeddings:
            return []

        # 计算相似度
        similarities = []
        for memory_id, memory_vec in memory_embeddings.items():
            score = cosine_similarity(query_embedding, memory_vec)
            similarities.append((memory_id, float(score)))

        # 按分数降序排序
        similarities.sort(key=lambda x: x[1], reverse=True)

        # 返回 Top-K
        return similarities[:top_k]

    def get_name(self) -> str:
        return "cosine"
