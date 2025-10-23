"""工具函数 - 相似度计算"""
import numpy as np
from typing import List, Tuple, Dict


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    计算两个向量的余弦相似度

    Args:
        vec1: 向量1
        vec2: 向量2

    Returns:
        余弦相似度值 [-1, 1]
    """
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return float(dot_product / (norm1 * norm2))


def find_top_k_similar(
    query_embedding: List[float],
    memory_embeddings: Dict[str, np.ndarray],
    top_k: int = 1
) -> List[Tuple[str, float]]:
    """
    找到与查询最相似的 Top-K 记忆

    Args:
        query_embedding: 查询的嵌入向量
        memory_embeddings: 记忆嵌入字典 {memory_id: embedding}
        top_k: 返回的数量

    Returns:
        [(memory_id, similarity_score), ...] 按相似度降序排列
    """
    query_vec = np.array(query_embedding)

    similarities = []
    for memory_id, memory_vec in memory_embeddings.items():
        sim = cosine_similarity(query_vec, memory_vec)
        similarities.append((memory_id, sim))

    # 按相似度降序排序
    similarities.sort(key=lambda x: x[1], reverse=True)

    # 返回 Top-K
    return similarities[:top_k]
