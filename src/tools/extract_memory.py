"""extract_memory 工具 - 提取记忆（支持异步）"""
import json
import uuid
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timezone


class ExtractMemoryTool:
    """记忆提取工具"""

    def __init__(self, config, storage_backend, llm_provider, embedding_provider, memory_manager=None):
        """
        初始化提取工具

        Args:
            config: 配置对象
            storage_backend: 存储后端实例
            llm_provider: LLM Provider 实例
            embedding_provider: 嵌入 Provider 实例
            memory_manager: 记忆管理器实例（可选，用于去重和合并）
        """
        self.config = config
        self.storage = storage_backend
        self.llm = llm_provider
        self.embedding = embedding_provider
        self.memory_manager = memory_manager

        # 提取配置
        extraction_config = config.get("extraction", default={})
        self.max_memories = extraction_config.get("max_memories_per_trajectory", 3)
        self.judge_temp = extraction_config.get("judge_temperature", 0.0)
        self.extract_temp = extraction_config.get("extract_temperature", 1.0)
        self.async_by_default = extraction_config.get("async_by_default", True)

    async def execute(
        self,
        trajectory: List[Dict],
        query: str,
        success_signal: Optional[bool] = None,
        async_mode: bool = None,
        agent_id: str = None
    ) -> Dict:
        """
        执行记忆提取

        Args:
            trajectory: 轨迹步骤列表
            query: 任务查询
            success_signal: 成功/失败标记，None 时自动判断
            async_mode: 是否异步处理，None 时使用配置默认值
            agent_id: Agent ID，用于多租户隔离

        Returns:
            提取结果字典
        """
        # 确定是否异步
        if async_mode is None:
            async_mode = self.async_by_default

        # 生成任务 ID
        task_id = f"extract_{uuid.uuid4().hex[:8]}"

        if async_mode:
            # 异步模式：立即返回，后台处理
            asyncio.create_task(
                self._extract_async(task_id, trajectory, query, success_signal, agent_id)
            )
            return {
                "status": "processing",
                "message": "记忆提取任务已提交，正在后台处理",
                "task_id": task_id,
                "async_mode": True
            }
        else:
            # 同步模式：等待处理完成
            result = await self._extract_sync(trajectory, query, success_signal, agent_id)
            return {
                **result,
                "task_id": task_id,
                "async_mode": False
            }

    async def _extract_sync(
        self,
        trajectory: List[Dict],
        query: str,
        success_signal: Optional[bool],
        agent_id: str = None
    ) -> Dict:
        """同步提取记忆"""
        try:
            # 1. 判断成功/失败（如果未提供）
            if success_signal is None:
                success_signal = await self._judge_trajectory(trajectory, query)

            # 2. 格式化轨迹
            from ..prompts.formatters import format_trajectory
            trajectory_text = format_trajectory(trajectory)

            # 3. 提取记忆项
            from ..prompts.templates import get_extract_prompt
            extract_prompt = get_extract_prompt(query, trajectory_text, success_signal)

            response = await self.llm.chat(
                messages=[{"role": "user", "content": extract_prompt}],
                temperature=self.extract_temp
            )

            # 4. 解析 LLM 响应
            memories = self._parse_llm_response(response)

            # 限制数量
            memories = memories[:self.max_memories]

            # 5. 构建记忆项和嵌入
            new_memories = []
            embeddings_dict = {}
            current_time = datetime.now(timezone.utc).isoformat()

            for mem_data in memories:
                memory_id = f"mem_{uuid.uuid4().hex}"

                # 构建完整记忆项
                memory = {
                    "memory_id": memory_id,
                    "agent_id": agent_id,
                    "timestamp": current_time,
                    "success": success_signal,
                    "title": mem_data["title"],
                    "description": mem_data["description"],
                    "content": mem_data["content"],
                    "query": query,
                    "retrieval_count": 0,
                    "last_retrieved": None,
                    "tags": self._extract_tags(mem_data, query),
                    "metadata": {
                        "extraction_model": self.llm.get_provider_name(),
                        "embedding_model": self.embedding.get_provider_name()
                    }
                }

                # 计算嵌入：对记忆内容进行向量化，而不是查询
                memory_text = f"{mem_data['title']}  {mem_data['description']} {mem_data['content']}"
                embedding = await self.embedding.embed(memory_text)

                new_memories.append(memory)
                embeddings_dict[memory_id] = embedding

            # 6. 通过 MemoryManager 处理（去重和合并检测）
            memories_to_save = new_memories
            management_result = None

            if self.memory_manager:
                try:
                    management_result = await self.memory_manager.on_memory_created(
                        new_memories=new_memories,
                        embeddings=embeddings_dict,
                        agent_id=agent_id
                    )

                    # 使用去重后的记忆列表
                    if management_result.success:
                        memories_to_save = management_result.metadata.get("unique_memories", new_memories)

                except Exception as e:
                    # MemoryManager 失败不影响主流程
                    import logging
                    logging.warning(f"MemoryManager 处理失败: {e}", exc_info=True)

            # 7. 保存记忆到存储
            saved_memories = []
            for memory in memories_to_save:
                memory_id = memory["memory_id"]
                embedding = embeddings_dict[memory_id]

                await self.storage.add_memory(memory, embedding)

                saved_memories.append({
                    "memory_id": memory_id,
                    "title": memory["title"],
                    "description": memory["description"]
                })

            # 8. 构建返回结果
            result = {
                "status": "completed",
                "success": success_signal,
                "extracted_count": len(saved_memories),
                "memories": saved_memories
            }

            # 添加管理信息
            if management_result:
                result["management"] = {
                    "duplicates_skipped": management_result.duplicates_found,
                    "merges_triggered": management_result.merged_count,
                    "message": management_result.message
                }

            return result

        except Exception as e:
            return {
                "status": "error",
                "message": f"提取失败: {str(e)}",
                "success": None,
                "extracted_count": 0,
                "memories": []
            }

    async def _extract_async(
        self,
        task_id: str,
        trajectory: List[Dict],
        query: str,
        success_signal: Optional[bool],
        agent_id: str = None
    ):
        """异步提取记忆（后台任务）"""
        # 直接调用同步提取逻辑
        await self._extract_sync(trajectory, query, success_signal, agent_id)
        # 注意：异步模式下，结果不返回给调用者，只记录到日志或存储

    async def _judge_trajectory(self, trajectory: List[Dict], query: str) -> bool:
        """判断轨迹是否成功"""
        try:
            from ..prompts.formatters import format_trajectory
            from ..prompts.templates import get_judge_prompt

            trajectory_text = format_trajectory(trajectory)
            # todo 轨迹分段，A task may involve success and failure..
            judge_prompt = get_judge_prompt(query, trajectory_text)

            response = await self.llm.chat(
                messages=[{"role": "user", "content": judge_prompt}],
                temperature=self.judge_temp
            )

            # 解析判断结果
            result = self._parse_json_response(response)
            return result.get("result", "failure") == "success"

        except Exception:
            # 判断失败时，默认为失败轨迹
            return False

    def _parse_llm_response(self, response: str) -> List[Dict]:
        """解析 LLM 返回的记忆项"""
        try:
            # 尝试提取 JSON
            data = self._parse_json_response(response)

            if "memories" in data:
                return data["memories"]
            else:
                return []

        except Exception:
            return []

    def _parse_json_response(self, response: str) -> Dict:
        """从响应中提取 JSON"""
        # 移除可能的 markdown 代码块标记
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]

        response = response.strip()
        return json.loads(response)

    def _extract_tags(self, memory_data: Dict, query: str) -> List[str]:
        """从记忆内容中提取标签"""
        # 简单的标签提取逻辑
        tags = []

        # 基于成功/失败
        # （在调用处已经有 success 信息）

        # 可以添加更复杂的标签提取逻辑
        return tags
