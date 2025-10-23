"""DashScope (通义千问) Provider 实现"""
from typing import List, Dict
from openai import AsyncOpenAI
from ..base import LLMProvider, EmbeddingProvider


class DashScopeLLMProvider(LLMProvider):
    """DashScope LLM Provider（使用 OpenAI 兼容接口）"""

    def __init__(self, config: Dict):
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.model = config.get("chat_model", "qwen-plus")
        self.default_temperature = config.get("temperature", 0.7)
        self.default_max_tokens = config.get("max_tokens", 4096)

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = None,
        max_tokens: int = None,
        **kwargs
    ) -> str:
        """调用 DashScope Chat API"""
        temperature = temperature if temperature is not None else self.default_temperature
        max_tokens = max_tokens if max_tokens is not None else self.default_max_tokens

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

        return response.choices[0].message.content

    def get_provider_name(self) -> str:
        return f"dashscope:{self.model}"


class DashScopeEmbeddingProvider(EmbeddingProvider):
    """DashScope Embedding Provider"""

    def __init__(self, config: Dict):
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.model = config.get("model", "text-embedding-v3")

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

        # text-embedding-v3 是 1024 维
        self._embedding_dim = 1024

    async def embed(self, text: str) -> List[float]:
        """调用 DashScope Embedding API"""
        response = await self.client.embeddings.create(
            model=self.model,
            input=text
        )

        return response.data[0].embedding

    def get_provider_name(self) -> str:
        return f"dashscope:{self.model}"

    def get_embedding_dim(self) -> int:
        return self._embedding_dim
