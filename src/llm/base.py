"""LLM Provider 抽象基类"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class LLMProvider(ABC):
    """LLM 聊天接口抽象基类"""

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> str:
        """
        聊天完成接口

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}, ...]
            temperature: 采样温度
            max_tokens: 最大生成 token 数
            **kwargs: 其他参数

        Returns:
            生成的文本
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """返回 Provider 名称"""
        pass


class EmbeddingProvider(ABC):
    """Embedding 接口抽象基类"""

    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """
        文本嵌入接口

        Args:
            text: 输入文本

        Returns:
            嵌入向量
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """返回 Provider 名称"""
        pass

    @abstractmethod
    def get_embedding_dim(self) -> int:
        """返回嵌入维度"""
        pass
