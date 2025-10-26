"""JSON 存储后端实现"""
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import numpy as np
from threading import Lock

from ..base import StorageBackend


class JSONStorageBackend(StorageBackend):
    """JSON 文件存储后端"""

    def __init__(self, config: Dict):
        self.memories_path = Path(config.get("memories_path", "data/memories.json"))
        self.embeddings_path = Path(config.get("embeddings_path", "data/embeddings.json"))
        self._lock = Lock()

        # 初始化文件
        self._initialize_files()

    def _initialize_files(self):
        """初始化 JSON 文件"""
        self.memories_path.parent.mkdir(parents=True, exist_ok=True)
        self.embeddings_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.memories_path.exists():
            self._save_memories({
                "version": "1.0",
                "total_count": 0,
                "memories": []
            })

        if not self.embeddings_path.exists():
            self._save_embeddings({
                "version": "1.0",
                "embedding_model": "unknown",
                "embedding_dim": 0,
                "embeddings": {}
            })

    def _load_memories(self) -> Dict:
        """加载记忆数据"""
        with self._lock:
            with open(self.memories_path, 'r', encoding='utf-8') as f:
                return json.load(f)

    def _save_memories(self, data: Dict):
        """保存记忆数据"""
        with self._lock:
            with open(self.memories_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_embeddings(self) -> Dict:
        """加载嵌入数据"""
        with self._lock:
            with open(self.embeddings_path, 'r', encoding='utf-8') as f:
                return json.load(f)

    def _save_embeddings(self, data: Dict):
        """保存嵌入数据"""
        with self._lock:
            with open(self.embeddings_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    async def add_memory(self, memory: Dict, embedding: List[float]):
        """添加新记忆"""
        # 添加到 memories.json
        memories_data = self._load_memories()
        memories_data["memories"].append(memory)
        memories_data["total_count"] = len(memories_data["memories"])
        memories_data["last_updated"] = memory["timestamp"]
        self._save_memories(memories_data)

        # 添加到 embeddings.json
        embeddings_data = self._load_embeddings()
        embeddings_data["embeddings"][memory["memory_id"]] = {
            "query_text": memory["query"],
            "vector": embedding,
            "created_at": memory["timestamp"]
        }
        embeddings_data["last_updated"] = memory["timestamp"]
        self._save_embeddings(embeddings_data)

    async def get_memory_by_id(self, memory_id: str) -> Optional[Dict]:
        """根据 ID 获取记忆"""
        memories_data = self._load_memories()
        for mem in memories_data["memories"]:
            if mem["memory_id"] == memory_id:
                return mem
        return None

    async def get_all_memories(self, agent_id: str = None) -> List[Dict]:
        """
        获取所有记忆

        Args:
            agent_id: Agent ID，用于过滤。None 表示获取所有记忆
        """
        memories_data = self._load_memories()
        all_memories = memories_data["memories"]

        # 如果指定了 agent_id，只返回匹配的记忆
        if agent_id is not None:
            return [m for m in all_memories if m.get("agent_id") == agent_id]

        # 否则返回所有记忆
        return all_memories

    async def get_all_embeddings(self, agent_id: str = None) -> Dict[str, np.ndarray]:
        """
        获取所有嵌入向量

        Args:
            agent_id: Agent ID，用于过滤。None 表示获取所有嵌入
        """
        embeddings_data = self._load_embeddings()

        if agent_id is None:
            # 返回所有
            return {
                mem_id: np.array(data["vector"])
                for mem_id, data in embeddings_data["embeddings"].items()
            }

        # 需要先获取记忆列表，找出属于该 agent 的 memory_id
        memories = await self.get_all_memories(agent_id)
        memory_ids = {m["memory_id"] for m in memories}

        return {
            mem_id: np.array(data["vector"])
            for mem_id, data in embeddings_data["embeddings"].items()
            if mem_id in memory_ids
        }

    async def update_retrieval_stats(self, memory_id: str, timestamp: str):
        """更新检索统计"""
        memories_data = self._load_memories()
        for mem in memories_data["memories"]:
            if mem["memory_id"] == memory_id:
                mem["retrieval_count"] = mem.get("retrieval_count", 0) + 1
                mem["last_retrieved"] = timestamp
                break
        self._save_memories(memories_data)

    async def get_stats(self) -> Dict:
        """获取统计信息"""
        memories_data = self._load_memories()
        memories = memories_data["memories"]

        success_count = sum(1 for m in memories if m.get("success", True))
        failure_count = len(memories) - success_count

        return {
            "total_count": len(memories),
            "success_count": success_count,
            "failure_count": failure_count,
            "last_updated": memories_data.get("last_updated")
        }
