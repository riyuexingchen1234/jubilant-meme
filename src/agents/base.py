import json
import re
from typing import Any, Dict, Optional
from src.llm.base import BaseLLMClient
from src.utils.prompt_loader import get_prompt_loader

class BaseAgent:
    def __init__(self, llm_client: BaseLLMClient, prompt_template_path: str, temperature: float = None, max_tokens: int = None):
        self.llm = llm_client
        self.prompt_path = prompt_template_path
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.loader = get_prompt_loader()

    def system_prompt(self, **kwargs) -> str:
        return self.loader.render(self.prompt_path, **kwargs)

    def call_llm(self, system_prompt: str, user_message: str, temperature: float = None, max_tokens: int = None) -> str:
        from src.llm.base import LLMResponse
        resp = self.llm.chat(
            messages=[{"role": "user", "content": user_message}],
            system_prompt=system_prompt,
            temperature=temperature if temperature is not None else self.temperature,
            max_tokens=max_tokens if max_tokens is not None else self.max_tokens,
        )
        return resp.content

    def parse_response(self, content: str) -> Dict[str, Any]:
        if not content or not content.strip():
            return {"raw": ""}
        content = content.strip()
        json_block = re.search(r"```json\s*\n(.*?)```", content, re.DOTALL)
        if json_block:
            try:
                return json.loads(json_block.group(1).strip())
            except json.JSONDecodeError:
                pass
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        brace_start = content.find("{")
        brace_end = content.rfind("}")
        if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
            try:
                return json.loads(content[brace_start:brace_end+1])
            except json.JSONDecodeError:
                pass
        return {"raw": content}

    def run(self, user_message: str = "", **kwargs) -> Dict[str, Any]:
        sp = self.system_prompt(**kwargs)
        content = self.call_llm(sp, user_message or "请按要求执行任务。")
        return self.parse_response(content)
