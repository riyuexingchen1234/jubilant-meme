from typing import Any, Dict, List, Optional
from openai import OpenAI
from src.config import LLMConfig
from src.llm.base import BaseLLMClient, LLMResponse

class OpenAIClient(BaseLLMClient):
    def __init__(self, config: LLMConfig):
        self.config = config
        kwargs = {"api_key": config.api_key}
        if config.base_url:
            kwargs["base_url"] = config.base_url
        self.client = OpenAI(**kwargs)

    def chat(self, messages: List[Dict[str, str]], temperature: Optional[float] = None,
             max_tokens: Optional[int] = None, system_prompt: Optional[str] = None, **kwargs) -> LLMResponse:
        final_messages = []
        if system_prompt:
            final_messages.append({"role": "system", "content": system_prompt})
        final_messages.extend(messages)
        params = {
            "model": self.config.model,
            "messages": final_messages,
            "temperature": temperature if temperature is not None else self.config.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.config.max_tokens,
            **kwargs,
        }
        response = self.client.chat.completions.create(**params)
        choice = response.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            },
            finish_reason=choice.finish_reason or "stop",
            raw_response=response,
        )
