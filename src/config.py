import json
import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

class LLMConfig(BaseModel):
    provider: str = "openai"
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 4096

class GitConfig(BaseModel):
    auto_commit: bool = True
    author_name: str = "Novel Assistant"
    author_email: str = "assistant@local"

class WritingConfig(BaseModel):
    max_retries_per_chapter: int = 3
    auto_check_consistency_every_n_chapters: int = 10

class Config(BaseModel):
    llm: LLMConfig = Field(default_factory=LLMConfig)
    git: GitConfig = Field(default_factory=GitConfig)
    writing: WritingConfig = Field(default_factory=WritingConfig)
    config_path: Optional[Path] = Field(default=None, exclude=True)

    def save(self):
        if self.config_path is None:
            raise ValueError("config_path not set")
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.model_dump(exclude={"config_path"}), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: Path) -> "Config":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        config = cls(**data, config_path=path)
        env_key = os.environ.get("NOVEL_ASSISTANT_API_KEY")
        if env_key:
            config.llm.api_key = env_key
        return config

    @classmethod
    def init_config(cls, path: Path) -> "Config":
        if path.exists():
            return cls.load(path)
        config = cls(config_path=path)
        config.save()
        return config

    @classmethod
    def get_default_path(cls) -> Path:
        return Path.home() / ".novel_assistant" / "config.json"
