"""Anthropic (Claude) Provider 实现"""
from typing import List, Dict
try:
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from ..base import LLMProvider


class AnthropicLLMProvider(LLMProvider):
    """Anthropic Claude LLM Provider"""

    def __init__(self, config: Dict):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "Anthropic provider requires 'anthropic' package. "
                "Install it with: pip install anthropic"
            )

        self.api_key = config.get("api_key")
        self.model = config.get("chat_model", "claude-3-5-sonnet-20241022")
        self.default_temperature = config.get("temperature", 0.7)
        self.default_max_tokens = config.get("max_tokens", 4096)

        self.client = AsyncAnthropic(api_key=self.api_key)

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = None,
        max_tokens: int = None,
        **kwargs
    ) -> str:
        """调用 Anthropic Chat API"""
        temperature = temperature if temperature is not None else self.default_temperature
        max_tokens = max_tokens if max_tokens is not None else self.default_max_tokens

        # Anthropic API 需要分离 system 和 messages
        system_message = None
        user_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                user_messages.append(msg)

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_message,
            messages=user_messages,
            **kwargs
        )

        return response.content[0].text

    def get_provider_name(self) -> str:
        return f"anthropic:{self.model}"
