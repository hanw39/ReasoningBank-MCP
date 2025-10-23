"""混合评分检索策略"""
from typing import List, Tuple, Dict
import numpy as np
from datetime import datetime, timezone
from ..base import RetrievalStrategy
from ...utils.similarity import cosine_similarity


class HybridRetrievalStrategy(RetrievalStrategy):
    """
    混合评分检索策略

    综合考虑多个因素：
    - 语义相似度（余弦相似度）
    - 记忆置信度（基于检索次数）
    - 成功/失败偏好
    - 时间衰减
    """

    def __init__(self, config: Dict = None):
        """
        初始化混合检索策略

        Args:
            config: 配置字典，包含权重和衰减参数
        """
        default_weights = {
            "semantic": 0.6,
            "confidence": 0.2,
            "success": 0.15,
            "recency": 0.05
        }

        if config:
            self.weights = config.get("weights", default_weights)
            self.time_decay_halflife = config.get("time_decay_halflife", 30)
        else:
            self.weights = default_weights
            self.time_decay_halflife = 30

    def _compute_time_decay(self, created_at: str) -> float:
        """
        计算时间衰减因子

        使用指数衰减: decay = exp(-λ * t)
        其中 λ = ln(2) / halflife

        Args:
            created_at: ISO 8601 时间戳

        Returns:
            衰减因子 [0, 1]，越新越接近 1
        """
        try:
            created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            current_time = datetime.now(timezone.utc)
            days_elapsed = (current_time - created_time).days

            # 指数衰减
            lambda_decay = np.log(2) / self.time_decay_halflife
            decay = np.exp(-lambda_decay * days_elapsed)

            return float(decay)
        except Exception:
            # 如果时间解析失败，返回默认值
            return 1.0

    def _compute_confidence_score(self, memory: Dict) -> float:
        """
        计算记忆置信度

        基于检索次数，使用对数缩放防止过度偏向高频记忆

        Args:
            memory: 记忆项字典

        Returns:
            置信度 [0.5, 1.0]
        """
        retrieval_count = memory.get("retrieval_count", 0)

        # 使用 tanh 进行平滑映射
        # confidence ∈ [0.5, 1.0]
        confidence = 0.5 + 0.5 * np.tanh(retrieval_count / 10)

        return float(confidence)

    async def retrieve(
        self,
        query: str,
        query_embedding: np.ndarray,
        storage_backend,
        top_k: int = 1,
        **kwargs
    ) -> List[Tuple[str, float]]:
        """
        使用混合评分检索记忆

        score = w1*semantic + w2*confidence + w3*success - w4*(1-recency)
        """
        # 获取所有记忆
        memory_embeddings = await storage_backend.get_all_embeddings()
        memories = await storage_backend.get_all_memories()

        if not memories or not memory_embeddings:
            return []

        # 创建 memory_id -> memory 的映射
        memory_map = {m["memory_id"]: m for m in memories}

        scores = []

        for memory in memories:
            memory_id = memory["memory_id"]

            # 确保嵌入存在
            if memory_id not in memory_embeddings:
                continue

            memory_vec = memory_embeddings[memory_id]

            # 1. 语义相似度
            semantic_sim = cosine_similarity(query_embedding, memory_vec)

            # 2. 置信度
            confidence = self._compute_confidence_score(memory)

            # 3. 成功/失败偏好
            success_bonus = 1.0 if memory.get("success", True) else -0.5

            # 4. 时间衰减
            time_decay = self._compute_time_decay(memory["timestamp"])

            # 混合评分
            final_score = (
                self.weights["semantic"] * semantic_sim
                + self.weights["confidence"] * confidence
                + self.weights["success"] * success_bonus
                - self.weights["recency"] * (1 - time_decay)  # 越新越好
            )

            scores.append((memory_id, float(final_score)))

        # 按分数降序排序
        scores.sort(key=lambda x: x[1], reverse=True)

        # 返回 Top-K
        return scores[:top_k]

    def get_name(self) -> str:
        return "hybrid"
