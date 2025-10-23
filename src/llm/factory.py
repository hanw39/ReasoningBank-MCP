"""LLM 和 Embedding Provider 工厂"""
from typing import Dict
from .base import LLMProvider, EmbeddingProvider
from .providers import (
    DashScopeLLMProvider,
    DashScopeEmbeddingProvider,
    OpenAILLMProvider,
    OpenAIEmbeddingProvider,
    AnthropicLLMProvider,
)


class LLMFactory:
    """LLM Provider 工厂"""

    _providers = {
        "dashscope": DashScopeLLMProvider,
        "openai": OpenAILLMProvider,
        "anthropic": AnthropicLLMProvider,
    }

    @classmethod
    def create(cls, config: Dict) -> LLMProvider:
        """
        创建 LLM Provider 实例

        Args:
            config: 配置字典，包含 'provider' 键和对应配置

        Returns:
            LLMProvider 实例
        """
        provider_name = config.get("provider")
        if provider_name not in cls._providers:
            raise ValueError(f"Unknown LLM provider: {provider_name}")

        provider_class = cls._providers[provider_name]
        return provider_class(config)

    @classmethod
    def register_provider(cls, name: str, provider_class: type):
        """注册新的 LLM Provider（插件机制）"""
        cls._providers[name] = provider_class


class EmbeddingFactory:
    """Embedding Provider 工厂"""

    _providers = {
        "dashscope": DashScopeEmbeddingProvider,
        "openai": OpenAIEmbeddingProvider,
    }

    @classmethod
    def create(cls, config: Dict) -> EmbeddingProvider:
        """
        创建 Embedding Provider 实例

        Args:
            config: 配置字典，包含 'provider' 键和对应配置

        Returns:
            EmbeddingProvider 实例
        """
        provider_name = config.get("provider")
        if provider_name not in cls._providers:
            raise ValueError(f"Unknown embedding provider: {provider_name}")

        provider_class = cls._providers[provider_name]
        return provider_class(config)

    @classmethod
    def register_provider(cls, name: str, provider_class: type):
        """注册新的 Embedding Provider（插件机制）"""
        cls._providers[name] = provider_class
