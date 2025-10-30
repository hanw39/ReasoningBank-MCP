"""retrieve_memory 工具 - 检索相关记忆"""
from typing import Dict, List
from datetime import datetime, timezone
import numpy as np


class RetrieveMemoryTool:
    """检索记忆工具"""

    def __init__(self, config, storage_backend, embedding_provider, retrieval_strategy):
        """
        初始化检索工具

        Args:
            config: 配置对象
            storage_backend: 存储后端实例
            embedding_provider: 嵌入 Provider 实例
            retrieval_strategy: 检索策略实例
        """
        self.config = config
        self.storage = storage_backend
        self.embedding = embedding_provider
        self.retrieval = retrieval_strategy

    async def execute(self, query: str, top_k: int = None, agent_id: str = None) -> Dict:
        """
        执行记忆检索

        Args:
            query: 任务查询
            top_k: 检索数量，默认使用配置中的值
            agent_id: Agent ID，用于多租户隔离

        Returns:
            检索结果字典
        """
        # 使用配置的默认值
        if top_k is None:
            top_k = self.config.get("retrieval", "default_top_k", default=1)

        # 限制最大值
        max_top_k = self.config.get("retrieval", "max_top_k", default=10)
        top_k = min(top_k, max_top_k)

        # 获取最小分数阈值
        min_score_threshold = self.config.get("retrieval", "min_score_threshold", default=0.85)

        try:
            # 1. 对查询进行嵌入
            query_embedding = await self.embedding.embed(query)
            query_vec = np.array(query_embedding)

            # 2. 使用策略检索
            top_k_results = await self.retrieval.retrieve(
                query=query,
                query_embedding=query_vec,
                storage_backend=self.storage,
                top_k=top_k,
                agent_id=agent_id
            )

            if not top_k_results:
                return {
                    "status": "no_memories",
                    "message": "记忆库为空或没有找到相关记忆",
                    "query": query,
                    "memories": [],
                    "formatted_prompt": ""
                }

            # 3. 获取完整记忆内容并更新统计（过滤低分记忆）
            retrieved_memories = []
            current_time = datetime.now(timezone.utc).isoformat()
            filtered_count = 0  # 记录被过滤的数量

            for memory_id, score in top_k_results:
                # 过滤低于阈值的记忆
                if score < min_score_threshold:
                    filtered_count += 1
                    continue

                memory = await self.storage.get_memory_by_id(memory_id)
                if memory:
                    # 更新检索统计
                    await self.storage.update_retrieval_stats(memory_id, current_time)

                    # 添加到结果
                    retrieved_memories.append({
                        "memory_id": memory_id,
                        "score": float(score),
                        "title": memory["title"],
                        "content": memory["content"],
                        "success": memory.get("success", True),
                        "tags": memory.get("tags", []),
                        "description": memory.get("description", "")
                    })

            # 如果所有记忆都被过滤了
            if not retrieved_memories:
                return {
                    "status": "no_memories",
                    "message": f"没有找到相关度高于 {min_score_threshold} 的记忆（过滤了 {filtered_count} 条低相关度记忆）",
                    "query": query,
                    "min_score_threshold": min_score_threshold,
                    "filtered_count": filtered_count,
                    "memories": [],
                    "formatted_prompt": ""
                }

            # 4. 格式化为 LLM 提示
            formatted_prompt = self._format_for_prompt(retrieved_memories)

            return {
                "status": "success",
                "query": query,
                "retrieval_strategy": self.retrieval.get_name(),
                "top_k": top_k,
                "min_score_threshold": min_score_threshold,
                "filtered_count": filtered_count,
                "memories": retrieved_memories,
                "formatted_prompt": formatted_prompt
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"检索失败: {str(e)}",
                "query": query,
                "memories": [],
                "formatted_prompt": ""
            }

    def _format_for_prompt(self, memories: List[Dict]) -> str:
        """格式化为可直接用于 LLM 提示的文本"""
        if not memories:
            return ""

        from ..prompts.formatters import format_memory_for_prompt
        return format_memory_for_prompt(memories)
