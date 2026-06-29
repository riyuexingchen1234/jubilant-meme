# 个人创作助手 MVP 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现核心创作链路——作者风格六层蒸馏 → 基于规则创作小说（人物不OOC、伏笔不遗忘、无明显AI味）→ 多Agent审稿 → 自动维护小说圣经状态 → 总编助理沟通层 → 手动热点素材导入与匹配

**Architecture:** Python编排内核 + 多Agent协作（每个Agent独立Prompt）+ Markdown/JSON共享状态层（小说圣经）+ 版本控制。Prompt是核心创作逻辑，Python代码负责编排、文件IO和状态管理。

**Tech Stack:** Python 3.10+, openai SDK, pydantic v2, jinja2, gitpython, chardet, python-frontmatter, pytest

**测试策略说明：** 本系统大部分核心逻辑在Prompt中，Prompt效果无法用单元测试验证，需实际调LLM测试；Python编排层（数据模型、文件IO、状态读写、工具函数）必须写单元测试覆盖。

---

## 前置说明：目录结构确认

实现中创建的文件严格遵循设计文档，以下是所有需要创建的源文件列表：

```
src/
├── __init__.py
├── config.py
├── main.py
├── llm/
│   ├── __init__.py
│   ├── base.py
│   └── openai_client.py
├── utils/
│   ├── __init__.py
│   ├── git.py
│   ├── text_clean.py
│   └── prompt_loader.py
├── bible/
│   ├── __init__.py
│   ├── models.py
│   ├── reader.py
│   └── writer.py
├── agents/
│   ├── __init__.py
│   ├── base.py
│   ├── editor_assistant.py
│   ├── distillation/
│   │   ├── __init__.py
│   │   ├── preprocessor.py
│   │   ├── statistician.py
│   │   ├── literature_analyst.py
│   │   ├── antipattern_detector.py
│   │   └── validator.py
│   └── writing/
│       ├── __init__.py
│       ├── hotspot_collector.py
│       ├── material_matcher.py
│       ├── outline_writer.py
│       ├── writer.py
│       ├── style_reviewer.py
│       ├── logic_reviewer.py
│       ├── rationality_reviewer.py
│       ├── review_aggregator.py
│       └── state_updater.py
└── workflows/
    ├── __init__.py
    ├── distill.py
    └── daily_update.py
prompts/  (所有Agent的System Prompt)
tests/    (单元测试)
imports/  (用户导入素材目录，运行时创建)
novels/   (小说数据目录，运行时创建)
```

---

## Task 1: 项目初始化与依赖配置

**Files:**
- Create: `pyproject.toml`
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `src/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: 创建 .gitignore**

```
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
*.egg-info/
dist/
build/
.env
.novel_assistant/
imports/
novels/
*.log
```

- [ ] **Step 2: 创建 requirements.txt**

```
openai>=1.0.0
pydantic>=2.0.0
jinja2>=3.1.0
gitpython>=3.1.0
chardet>=5.0.0
python-frontmatter>=1.0.0
pytest>=7.0.0
pytest-asyncio>=0.21.0
```

- [ ] **Step 3: 创建 pyproject.toml**

```toml
[project]
name = "novel-assistant"
version = "0.1.0"
description = "AI-powered multi-agent novel writing assistant with author style distillation"
requires-python = ">=3.10"
dependencies = [
    "openai>=1.0.0",
    "pydantic>=2.0.0",
    "jinja2>=3.1.0",
    "gitpython>=3.1.0",
    "chardet>=5.0.0",
    "python-frontmatter>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
]

[project.scripts]
novel-assistant = "src.main:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

- [ ] **Step 4: 创建空 __init__.py 文件**

创建以下空文件：
- `src/__init__.py`
- `tests/__init__.py`

- [ ] **Step 5: 安装依赖**

Run:
```bash
cd /workspace && pip install -e ".[dev]"
```
Expected: 依赖安装成功，无报错。

- [ ] **Step 6: Commit**

```bash
cd /workspace && git init && git add -A && git commit -m "chore: initialize project structure and dependencies"
```

---

## Task 2: 配置管理模块

**Files:**
- Create: `src/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: 写配置测试**

Create `tests/test_config.py`:
```python
import json
import os
import tempfile
from pathlib import Path
import pytest

from src.config import Config, LLMConfig, GitConfig, WritingConfig


def test_default_config_creation():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        config = Config(config_path=config_path)
        assert config.llm.provider == "openai"
        assert config.llm.model == "gpt-4o"
        assert config.llm.temperature == 0.7
        assert config.git.auto_commit is True
        assert config.writing.max_retries_per_chapter == 3


def test_config_save_and_load():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        config = Config(config_path=config_path)
        config.llm.api_key = "test-key-123"
        config.llm.model = "gpt-4"
        config.save()
        assert config_path.exists()
        loaded = Config.load(config_path)
        assert loaded.llm.api_key == "test-key-123"
        assert loaded.llm.model == "gpt-4"


def test_config_init_creates_template_when_missing():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        assert not config_path.exists()
        Config.init_config(config_path)
        assert config_path.exists()
        with open(config_path) as f:
            data = json.load(f)
        assert "llm" in data
        assert "git" in data
        assert "writing" in data


def test_config_env_var_override():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        Config.init_config(config_path)
        os.environ["NOVEL_ASSISTANT_API_KEY"] = "env-key-456"
        try:
            config = Config.load(config_path)
            assert config.llm.api_key == "env-key-456"
        finally:
            del os.environ["NOVEL_ASSISTANT_API_KEY"]
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd /workspace && pytest tests/test_config.py -v`
Expected: FAIL (ImportError: cannot import name 'Config')

- [ ] **Step 3: 实现配置模块**

Create `src/config.py`:
```python
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
        env_base_url = os.environ.get("NOVEL_ASSISTANT_BASE_URL")
        if env_base_url:
            config.llm.base_url = env_base_url
        env_model = os.environ.get("NOVEL_ASSISTANT_MODEL")
        if env_model:
            config.llm.model = env_model
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
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd /workspace && pytest tests/test_config.py -v`
Expected: 4 tests passed.

- [ ] **Step 5: Commit**

```bash
cd /workspace && git add src/config.py tests/test_config.py && git commit -m "feat: add configuration management with env var support"
```

---

## Task 3: Prompt加载与模板渲染工具

**Files:**
- Create: `src/utils/__init__.py`
- Create: `src/utils/prompt_loader.py`
- Create: `tests/test_prompt_loader.py`
- Create: `prompts/` 目录结构和基础Agent Prompt

- [ ] **Step 1: 写Prompt加载器测试**

Create `tests/test_prompt_loader.py`:
```python
import tempfile
from pathlib import Path

from src.utils.prompt_loader import PromptLoader, load_prompt


def test_prompt_loader_loads_markdown():
    with tempfile.TemporaryDirectory() as tmpdir:
        prompts_dir = Path(tmpdir) / "prompts"
        prompts_dir.mkdir()
        test_prompt = prompts_dir / "test.md"
        test_prompt.write_text("# Test Prompt\n\nHello {{ name }}!", encoding="utf-8")
        loader = PromptLoader(prompts_dir)
        result = loader.render("test", name="World")
        assert "Hello World!" in result
        assert "Test Prompt" not in result


def test_load_prompt_helper_with_frontmatter():
    with tempfile.TemporaryDirectory() as tmpdir:
        prompts_dir = Path(tmpdir) / "prompts"
        prompts_dir.mkdir()
        subdir = prompts_dir / "sub"
        subdir.mkdir()
        test_prompt = subdir / "demo.md"
        test_prompt.write_text(
            "---\nmodel: gpt-4o\ntemperature: 0.5\n---\nYou are a {{ role }}.",
            encoding="utf-8"
        )
        loader = PromptLoader(prompts_dir)
        result = loader.render("sub/demo", role="writer")
        assert "You are a writer." in result
        assert "model:" not in result


def test_prompt_not_found_raises():
    with tempfile.TemporaryDirectory() as tmpdir:
        prompts_dir = Path(tmpdir) / "prompts"
        prompts_dir.mkdir()
        loader = PromptLoader(prompts_dir)
        try:
            loader.render("nonexistent")
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError:
            pass
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd /workspace && pytest tests/test_prompt_loader.py -v`
Expected: FAIL

- [ ] **Step 3: 实现Prompt加载器**

Create `src/utils/__init__.py` (空文件)

Create `src/utils/prompt_loader.py`:
```python
from pathlib import Path
from typing import Any, Dict, Optional

import frontmatter
from jinja2 import Environment, FileSystemLoader, select_autoescape


class PromptLoader:
    def __init__(self, prompts_dir: Path):
        self.prompts_dir = Path(prompts_dir)
        self.env = Environment(
            loader=FileSystemLoader(str(self.prompts_dir)),
            autoescape=select_autoescape([]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, template_path: str, **kwargs: Any) -> str:
        full_path = self.prompts_dir / f"{template_path}.md"
        if not full_path.exists():
            raise FileNotFoundError(f"Prompt template not found: {full_path}")
        post = frontmatter.load(str(full_path))
        template = self.env.from_string(post.content)
        return template.render(**kwargs).strip()

    def load_with_metadata(self, template_path: str, **kwargs: Any) -> Dict[str, Any]:
        full_path = self.prompts_dir / f"{template_path}.md"
        if not full_path.exists():
            raise FileNotFoundError(f"Prompt template not found: {full_path}")
        post = frontmatter.load(str(full_path))
        template = self.env.from_string(post.content)
        rendered = template.render(**kwargs).strip()
        return {
            "content": rendered,
            "metadata": dict(post.metadata),
        }


_prompt_loader: Optional[PromptLoader] = None


def get_prompt_loader() -> PromptLoader:
    global _prompt_loader
    if _prompt_loader is None:
        prompts_dir = Path(__file__).parent.parent.parent / "prompts"
        _prompt_loader = PromptLoader(prompts_dir)
    return _prompt_loader


def load_prompt(template_path: str, **kwargs: Any) -> str:
    return get_prompt_loader().render(template_path, **kwargs)
```

- [ ] **Step 4: 创建Prompts目录基础结构**

创建以下目录：
- `prompts/`
- `prompts/editor_assistant/`
- `prompts/distillation/`
- `prompts/writing/`
- `prompts/writing/reviewers/`

在每个目录下放一个 `.gitkeep` 空文件以保证git能跟踪空目录。

- [ ] **Step 5: 运行测试确认通过**

Run: `cd /workspace && pytest tests/test_prompt_loader.py -v`
Expected: 3 tests passed.

- [ ] **Step 6: Commit**

```bash
cd /workspace && git add src/utils/ tests/test_prompt_loader.py prompts/ && git commit -m "feat: add prompt loader with jinja2 templating and frontmatter support"
```

---

## Task 4: LLM客户端封装

**Files:**
- Create: `src/llm/__init__.py`
- Create: `src/llm/base.py`
- Create: `src/llm/openai_client.py`
- Create: `tests/test_llm.py`

- [ ] **Step 1: 写LLM客户端测试**

Create `tests/test_llm.py`:
```python
from unittest.mock import MagicMock, patch

from src.llm.base import BaseLLMClient, LLMResponse
from src.llm.openai_client import OpenAIClient
from src.config import LLMConfig


def test_llm_response_structure():
    resp = LLMResponse(
        content="Hello world",
        model="gpt-4o",
        usage={"prompt_tokens": 10, "completion_tokens": 5},
        finish_reason="stop",
    )
    assert resp.content == "Hello world"
    assert resp.usage["prompt_tokens"] == 10


@patch("src.llm.openai_client.OpenAI")
def test_openai_client_chat_basic(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Test response"
    mock_response.choices[0].finish_reason = "stop"
    mock_response.usage.prompt_tokens = 20
    mock_response.usage.completion_tokens = 10
    mock_response.model = "gpt-4o"
    mock_client.chat.completions.create.return_value = mock_response
    config = LLMConfig(api_key="test-key", model="gpt-4o")
    client = OpenAIClient(config)
    resp = client.chat([{"role": "user", "content": "Hi"}])
    assert resp.content == "Test response"
    assert resp.model == "gpt-4o"
    mock_client.chat.completions.create.assert_called_once()


@patch("src.llm.openai_client.OpenAI")
def test_openai_client_respects_temperature(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "ok"
    mock_response.choices[0].finish_reason = "stop"
    mock_response.usage.prompt_tokens = 5
    mock_response.usage.completion_tokens = 2
    mock_response.model = "gpt-4o"
    mock_client.chat.completions.create.return_value = mock_response
    config = LLMConfig(api_key="k", temperature=0.3, max_tokens=100)
    client = OpenAIClient(config)
    client.chat([{"role": "user", "content": "test"}])
    call_kwargs = mock_client.chat.completions.create.call_args[1]
    assert call_kwargs["temperature"] == 0.3
    assert call_kwargs["max_tokens"] == 100
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd /workspace && pytest tests/test_llm.py -v`
Expected: FAIL

- [ ] **Step 3: 实现LLM基类**

Create `src/llm/__init__.py` (空文件)

Create `src/llm/base.py`:
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class LLMResponse:
    content: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: str = "stop"
    raw_response: Any = None


class BaseLLMClient(ABC):
    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> LLMResponse:
        pass
```

- [ ] **Step 4: 实现OpenAI客户端**

Create `src/llm/openai_client.py`:
```python
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

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> LLMResponse:
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
```

- [ ] **Step 5: 运行测试确认通过**

Run: `cd /workspace && pytest tests/test_llm.py -v`
Expected: 3 tests passed.

- [ ] **Step 6: Commit**

```bash
cd /workspace && git add src/llm/ tests/test_llm.py && git commit -m "feat: add LLM client abstraction with OpenAI implementation"
```

---

## Task 5: 文本清洗工具

**Files:**
- Create: `src/utils/text_clean.py`
- Create: `tests/test_text_clean.py`

- [ ] **Step 1: 写文本清洗测试**

Create `tests/test_text_clean.py`:
```python
from src.utils.text_clean import clean_text, split_chapters, detect_encoding


def test_clean_text_removes_ads():
    text = "正文内容。\n更多精品小说请访问www.example.com\n正文继续。"
    cleaned = clean_text(text)
    assert "www.example.com" not in cleaned
    assert "正文内容" in cleaned


def test_clean_text_normalizes_newlines():
    text = "第一段\r\n\r\n\r\n第二段\n\n\n第三段"
    cleaned = clean_text(text)
    assert "\r" not in cleaned
    assert "\n\n\n" not in cleaned


def test_clean_text_removes_author_notes():
    text = "正文。\n作者有话说：今天更新晚了抱歉。\n下一章。"
    cleaned = clean_text(text)
    assert "作者有话说" not in cleaned
    assert "正文" in cleaned


def test_split_chapters_by_heading():
    text = "楔子\n\n内容0\n\n第一章 初入江湖\n\n内容1\n\n第二章 奇遇\n\n内容2\n\n第三章 高潮\n\n内容3"
    chapters = split_chapters(text)
    assert len(chapters) >= 3
    assert any("第一章" in c["title"] for c in chapters)
    assert any("第二章" in c["title"] for c in chapters)


def test_detect_encoding_utf8():
    import tempfile, os
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", encoding="utf-8", delete=False) as f:
        f.write("测试中文内容")
        path = f.name
    try:
        enc = detect_encoding(path)
        assert enc.lower().replace("-", "") in ("utf8", "utf_8", "ascii")
    finally:
        os.unlink(path)
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd /workspace && pytest tests/test_text_clean.py -v`
Expected: FAIL

- [ ] **Step 3: 实现文本清洗工具**

Create `src/utils/text_clean.py`:
```python
import re
from pathlib import Path
from typing import List, Dict, Any

import chardet


AD_PATTERNS = [
    r"www\.[a-zA-Z0-9\-]+\.[a-zA-Z]+",
    r"https?://[^\s]+",
    r"更多精[品彩]小说.*",
    r"手机用户.*访问.*",
    r"本书首发.*",
    r"最新章节.*阅读",
    r"章节列表.*",
]

AUTHOR_NOTE_PATTERNS = [
    r"作者有话说[：:].*",
    r"PS[：: ].*",
    r"ps[：: ].*",
    r"求收藏.*求推荐.*",
    r"求票票.*求花花.*",
    r"本章完.*",
    r"未完待续.*",
]

CHAPTER_PATTERN = re.compile(
    r"^(?:第[一二三四五六七八九十百千零\d]+[章节回卷集部篇]|楔子|序言|序章|引子|终章|尾声|后记)\s*.{0,30}$",
    re.MULTILINE,
)


def detect_encoding(file_path: str | Path) -> str:
    with open(file_path, "rb") as f:
        raw = f.read(1024 * 1024)
    result = chardet.detect(raw)
    encoding = result.get("encoding", "utf-8")
    if encoding is None:
        encoding = "utf-8"
    if encoding.lower() in ("gb2312", "gbk", "gb18030"):
        encoding = "gb18030"
    return encoding


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    for pattern in AD_PATTERNS:
        text = re.sub(pattern, "", text)
    for pattern in AUTHOR_NOTE_PATTERNS:
        text = re.sub(pattern, "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return text.strip()


def split_chapters(text: str) -> List[Dict[str, Any]]:
    matches = list(CHAPTER_PATTERN.finditer(text))
    chapters = []
    if not matches:
        chapters.append({
            "title": "正文",
            "content": text.strip(),
            "index": 0,
        })
        return chapters
    if matches[0].start() > 0:
        preamble = text[:matches[0].start()].strip()
        if preamble and len(preamble) > 100:
            chapters.append({
                "title": "楔子",
                "content": preamble,
                "index": 0,
            })
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        if content:
            chapters.append({
                "title": match.group(0).strip(),
                "content": content,
                "index": len(chapters),
            })
    return chapters


def load_and_clean_txt(file_path: str | Path) -> Dict[str, Any]:
    encoding = detect_encoding(file_path)
    with open(file_path, "r", encoding=encoding, errors="replace") as f:
        raw_text = f.read()
    cleaned = clean_text(raw_text)
    chapters = split_chapters(cleaned)
    return {
        "raw_text": raw_text,
        "cleaned_text": cleaned,
        "chapters": chapters,
        "total_chars": len(cleaned),
        "total_chapters": len(chapters),
        "encoding": encoding,
    }
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd /workspace && pytest tests/test_text_clean.py -v`
Expected: All tests passed.

- [ ] **Step 5: Commit**

```bash
cd /workspace && git add src/utils/text_clean.py tests/test_text_clean.py && git commit -m "feat: add text cleaning, chapter splitting, and encoding detection"
```

---

## Task 6: Git版本控制封装

**Files:**
- Create: `src/utils/git.py`
- Create: `tests/test_git.py`

- [ ] **Step 1: 写Git工具测试**

Create `tests/test_git.py`:
```python
import tempfile
from pathlib import Path

from src.utils.git import GitManager


def test_git_init_and_commit():
    with tempfile.TemporaryDirectory() as tmpdir:
        gm = GitManager(Path(tmpdir), author_name="Test", author_email="test@test.com")
        assert not gm.is_repo()
        gm.init()
        assert gm.is_repo()
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("hello", encoding="utf-8")
        gm.commit_all("test commit")
        log = gm.get_log(1)
        assert len(log) == 1
        assert "test commit" in log[0]["message"]


def test_git_rollback_to_commit():
    with tempfile.TemporaryDirectory() as tmpdir:
        gm = GitManager(Path(tmpdir), author_name="Test", author_email="test@test.com")
        gm.init()
        f1 = Path(tmpdir) / "a.txt"
        f1.write_text("version1", encoding="utf-8")
        gm.commit_all("first")
        first_hash = gm.get_log(1)[0]["hash"]
        f1.write_text("version2", encoding="utf-8")
        gm.commit_all("second")
        assert f1.read_text(encoding="utf-8") == "version2"
        gm.reset_to_commit(first_hash)
        assert f1.read_text(encoding="utf-8") == "version1"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd /workspace && pytest tests/test_git.py -v`
Expected: FAIL

- [ ] **Step 3: 实现Git工具**

Create `src/utils/git.py`:
```python
from pathlib import Path
from typing import Any, Dict, List, Optional

from git import GitCommandError, Repo


class GitManager:
    def __init__(self, repo_path: Path, author_name: str = "Novel Assistant", author_email: str = "assistant@local"):
        self.repo_path = Path(repo_path)
        self.author_name = author_name
        self.author_email = author_email

    def is_repo(self) -> bool:
        try:
            Repo(str(self.repo_path))
            return True
        except Exception:
            return False

    def init(self) -> None:
        if not self.is_repo():
            self.repo = Repo.init(str(self.repo_path))
            with self.repo.config_writer() as config:
                config.set_value("user", "name", self.author_name)
                config.set_value("user", "email", self.author_email)
        else:
            self.repo = Repo(str(self.repo_path))

    def _ensure_repo(self):
        if not hasattr(self, "repo"):
            self.init()

    def commit_all(self, message: str) -> Optional[str]:
        self._ensure_repo()
        self.repo.git.add(A=True)
        if not self.repo.is_dirty(untracked_files=True):
            return None
        commit = self.repo.index.commit(message)
        return str(commit.hexsha)

    def get_log(self, limit: int = 10) -> List[Dict[str, Any]]:
        self._ensure_repo()
        commits = []
        for i, commit in enumerate(self.repo.iter_commits(max_count=limit)):
            commits.append({
                "hash": str(commit.hexsha),
                "message": commit.message.strip(),
                "author": str(commit.author),
                "timestamp": commit.committed_datetime.isoformat(),
            })
        return commits

    def reset_to_commit(self, commit_hash: str, hard: bool = True) -> None:
        self._ensure_repo()
        if hard:
            self.repo.git.reset("--hard", commit_hash)
        else:
            self.repo.git.reset("--mixed", commit_hash)

    def get_current_commit_hash(self) -> str:
        self._ensure_repo()
        return str(self.repo.head.commit.hexsha)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd /workspace && pytest tests/test_git.py -v`
Expected: 2 tests passed.

- [ ] **Step 5: Commit**

```bash
cd /workspace && git add src/utils/git.py tests/test_git.py && git commit -m "feat: add git version control manager"
```

---

## Task 7: 圣经数据模型定义（Pydantic）

**Files:**
- Create: `src/bible/__init__.py`
- Create: `src/bible/models.py`
- Create: `tests/test_bible_models.py`

- [ ] **Step 1: 写数据模型测试**

Create `tests/test_bible_models.py`:
```python
import tempfile
from pathlib import Path
from src.bible.models import (
    Character, CharacterCard, Foreshadow, ForeshadowMap,
    HotspotMaterial, ChapterMeta, NovelMeta, Correction,
    ForeshadowStatus, ForeshadowType, MaterialStatus, NovelStatus,
)
from datetime import datetime


def test_character_card_defaults():
    card = CharacterCard(slug="protagonist", name="张三")
    assert card.ooc_redlines == []
    assert card.key_events == []
    assert card.slug == "protagonist"


def test_foreshadow_map_serialization():
    fm = ForeshadowMap()
    fm.add(Foreshadow(
        id="fs_001",
        content="主角捡到神秘玉佩",
        type=ForeshadowType.LIGHT,
        planted_chapter=3,
        status=ForeshadowStatus.PLANTED,
    ))
    data = fm.to_json()
    assert "fs_001" in data
    fm2 = ForeshadowMap.from_json(data)
    assert len(fm2.foreshadows) == 1
    assert fm2.foreshadows[0].content == "主角捡到神秘玉佩"


def test_novel_meta_defaults():
    meta = NovelMeta(novel_slug="test", title="测试小说")
    assert meta.status == NovelStatus.PLANNING
    assert meta.current_chapter == 0
    assert meta.config.chapter_word_count_target[0] == 3000


def test_correction_structure():
    c = Correction(
        scene="第三章女主撒娇",
        wrong="女主主动撒娇",
        correct="女主外冷内热不会主动撒娇",
        applied_scope="female_lead",
    )
    d = c.model_dump()
    assert "timestamp" in d
    assert d["wrong"] == "女主主动撒娇"


def test_hotspot_material_structure():
    hm = HotspotMaterial(
        id="hs_001",
        title="某地出现奇闻",
        category="社会",
        emotion_tags=["荒诞"],
        core_fact="某人遇到一件怪事",
        core_conflict="现实与常识的冲突",
        fictionable_score=7,
    )
    assert hm.status == MaterialStatus.UNUSED
    assert hm.used_in_chapter is None
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd /workspace && pytest tests/test_bible_models.py -v`
Expected: FAIL

- [ ] **Step 3: 实现数据模型**

Create `src/bible/__init__.py` (空文件)

Create `src/bible/models.py`:
```python
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class NovelStatus(str, Enum):
    PLANNING = "planning"
    WRITING = "writing"
    PAUSED = "paused"


class ForeshadowType(str, Enum):
    LIGHT = "light"
    HEAVY = "heavy"


class ForeshadowStatus(str, Enum):
    PLANTED = "planted"
    REVEALED = "revealed"
    ABANDONED = "abandoned"


class MaterialStatus(str, Enum):
    UNUSED = "unused"
    USED = "used"
    PLANTED_SEED = "planted_seed"


class ChapterWritingConfig(BaseModel):
    chapter_word_count_target: List[int] = Field(default_factory=lambda: [3000, 5000])
    hotspot_integration_ratio: float = 0.3
    auto_write_enabled: bool = False


class NovelMeta(BaseModel):
    novel_slug: str
    title: str
    author_style_source: List[str] = Field(default_factory=list)
    status: NovelStatus = NovelStatus.PLANNING
    current_chapter: int = 0
    novel_current_time: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    config: ChapterWritingConfig = Field(default_factory=ChapterWritingConfig)
    version: int = 1


class Character(BaseModel):
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None
    first_appearance_chapter: int = 0
    role: str = "supporting"


class KeyEvent(BaseModel):
    chapter: int
    event: str
    impact: str = ""


class CharacterCard(BaseModel):
    slug: str
    name: str
    basic_info: Character = Field(default_factory=lambda: Character(name=""))
    personality_traits: List[Dict[str, str]] = Field(default_factory=list)
    speech_patterns: Dict[str, Any] = Field(default_factory=dict)
    relationships: List[Dict[str, str]] = Field(default_factory=list)
    arc: Dict[str, Any] = Field(default_factory=dict)
    ooc_redlines: List[str] = Field(default_factory=list)
    key_events: List[KeyEvent] = Field(default_factory=list)


class Foreshadow(BaseModel):
    id: str
    content: str
    type: ForeshadowType = ForeshadowType.LIGHT
    planted_chapter: int
    planned_reveal_chapter: Optional[int] = None
    status: ForeshadowStatus = ForeshadowStatus.PLANTED
    related_material_id: Optional[str] = None
    notes: str = ""


class ForeshadowMap(BaseModel):
    foreshadows: List[Foreshadow] = Field(default_factory=list)

    def add(self, fs: Foreshadow):
        self.foreshadows.append(fs)

    def get_planted(self) -> List[Foreshadow]:
        return [f for f in self.foreshadows if f.status == ForeshadowStatus.PLANTED]

    def mark_revealed(self, fs_id: str, chapter: int):
        for f in self.foreshadows:
            if f.id == fs_id:
                f.status = ForeshadowStatus.REVEALED
                f.planned_reveal_chapter = chapter
                return

    def to_json(self) -> List[Dict[str, Any]]:
        return [f.model_dump() for f in self.foreshadows]

    @classmethod
    def from_json(cls, data: List[Dict[str, Any]]) -> "ForeshadowMap":
        return cls(foreshadows=[Foreshadow(**d) for d in data])


class HotspotMaterial(BaseModel):
    id: str
    title: str
    source: str = ""
    collected_at: datetime = Field(default_factory=datetime.now)
    category: str = "社会"
    emotion_tags: List[str] = Field(default_factory=list)
    core_fact: str = ""
    core_conflict: str = ""
    fictionable_points: List[str] = Field(default_factory=list)
    predicted_trends: List[str] = Field(default_factory=list)
    fictionable_score: int = 5
    related_characters: List[str] = Field(default_factory=list)
    status: MaterialStatus = MaterialStatus.UNUSED
    used_in_chapter: Optional[int] = None


class ChapterMeta(BaseModel):
    number: int
    title: str = ""
    word_count: int = 0
    summary: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    used_materials: List[str] = Field(default_factory=list)
    planted_foreshadows: List[str] = Field(default_factory=list)
    revealed_foreshadows: List[str] = Field(default_factory=list)


class Correction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: datetime = Field(default_factory=datetime.now)
    scene: str
    wrong: str
    correct: str
    applied_scope: str = "global"
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd /workspace && pytest tests/test_bible_models.py -v`
Expected: 5 tests passed.

- [ ] **Step 5: Commit**

```bash
cd /workspace && git add src/bible/models.py tests/test_bible_models.py && git commit -m "feat: add all pydantic data models for novel bible"
```

---

（后续任务继续实现圣经读写、Agent基类、各个Agent、工作流、Prompt、CLI入口——由于计划长度限制，将分多批次继续实现，此为前7个基础任务完成后的状态）
