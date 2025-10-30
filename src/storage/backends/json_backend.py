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
        self.memories_path = Path(config.get("memories_path", "data/memories.json")).expanduser()
        self.embeddings_path = Path(config.get("embeddings_path", "data/embeddings.json")).expanduser()
        self.archived_path = Path(config.get("archived_path", "data/archived_memories.json")).expanduser()
        self._lock = Lock()

        # Store retrieval strategy reference (injected later)
        self.retrieval_strategy = None

        # 初始化文件
        self._initialize_files()

    def _initialize_files(self):
        """初始化 JSON 文件"""
        # 创建所有必要的目录
        self.memories_path.parent.mkdir(parents=True, exist_ok=True)
        self.embeddings_path.parent.mkdir(parents=True, exist_ok=True)
        self.archived_path.parent.mkdir(parents=True, exist_ok=True)

        # 初始化 memories 文件
        if not self.memories_path.exists():
            self._save_memories({
                "version": "1.0",
                "total_count": 0,
                "memories": []
            })

        # 初始化 embeddings 文件
        if not self.embeddings_path.exists():
            self._save_embeddings({
                "version": "1.0",
                "embedding_model": "unknown",
                "embedding_dim": 0,
                "embeddings": {}
            })

        # 注意：archived 文件是可选的，只在需要时创建（在 archive_memories 方法中）
        # 这里只确保父目录存在

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

    async def save_memories(self, memories: List[Dict], embeddings: Dict[str, np.ndarray]):
        """批量保存记忆（用于合并后保存）"""
        memories_data = self._load_memories()
        embeddings_data = self._load_embeddings()

        for mem in memories:
            # 添加记忆
            memories_data["memories"].append(mem)

            # 添加嵌入
            if mem["memory_id"] in embeddings:
                embedding_vector = embeddings[mem["memory_id"]]
                embeddings_data["embeddings"][mem["memory_id"]] = {
                    "query_text": mem.get("query", ""),
                    "vector": embedding_vector.tolist() if isinstance(embedding_vector, np.ndarray) else embedding_vector,
                    "created_at": mem.get("timestamp", datetime.now().isoformat())
                }

        # 更新元数据
        memories_data["total_count"] = len(memories_data["memories"])
        memories_data["last_updated"] = datetime.now().isoformat()
        embeddings_data["last_updated"] = datetime.now().isoformat()

        # 保存
        self._save_memories(memories_data)
        self._save_embeddings(embeddings_data)

    async def get_memory(self, memory_id: str) -> Optional[Dict]:
        """获取单个记忆（别名）"""
        return await self.get_memory_by_id(memory_id)

    async def get_embeddings(self, memory_ids: List[str]) -> Dict[str, np.ndarray]:
        """获取指定记忆的嵌入向量"""
        embeddings_data = self._load_embeddings()
        result = {}

        for mem_id in memory_ids:
            if mem_id in embeddings_data["embeddings"]:
                result[mem_id] = np.array(embeddings_data["embeddings"][mem_id]["vector"])

        return result

    async def archive_memories(self, memories: List[Dict]):
        """归档记忆到 archived_memories.json"""
        # 加载或创建归档文件
        if self.archived_path.exists():
            with self._lock:
                with open(self.archived_path, 'r', encoding='utf-8') as f:
                    archived_data = json.load(f)
        else:
            archived_data = {
                "version": "1.0",
                "description": "已归档的原始经验，不参与检索但可追溯",
                "memories": []
            }

        # 添加新归档
        archived_data["memories"].extend(memories)
        archived_data["last_updated"] = datetime.now().isoformat()

        # 保存
        with self._lock:
            with open(self.archived_path, 'w', encoding='utf-8') as f:
                json.dump(archived_data, f, ensure_ascii=False, indent=2)

    async def get_archived_memory(self, memory_id: str) -> Optional[Dict]:
        """获取已归档的记忆"""
        if not self.archived_path.exists():
            return None

        with self._lock:
            with open(self.archived_path, 'r', encoding='utf-8') as f:
                archived_data = json.load(f)

        for mem in archived_data.get("memories", []):
            if mem["memory_id"] == memory_id:
                return mem

        return None

    async def delete_memories(self, memory_ids: List[str], agent_id: Optional[str] = None):
        """删除记忆（带 agent_id 安全验证）"""
        memories_data = self._load_memories()
        embeddings_data = self._load_embeddings()

        # 过滤掉要删除的记忆
        deleted_count = 0
        new_memories = []

        for mem in memories_data["memories"]:
            should_delete = False

            if mem["memory_id"] in memory_ids:
                # 如果指定了 agent_id，验证权限
                if agent_id is None or mem.get("agent_id") == agent_id:
                    should_delete = True
                    deleted_count += 1

                    # 同时删除对应的 embedding
                    if mem["memory_id"] in embeddings_data["embeddings"]:
                        del embeddings_data["embeddings"][mem["memory_id"]]

            if not should_delete:
                new_memories.append(mem)

        # 更新数据
        memories_data["memories"] = new_memories
        memories_data["total_count"] = len(new_memories)
        memories_data["last_updated"] = datetime.now().isoformat()
        embeddings_data["last_updated"] = datetime.now().isoformat()

        # 保存
        self._save_memories(memories_data)
        self._save_embeddings(embeddings_data)

        return deleted_count

