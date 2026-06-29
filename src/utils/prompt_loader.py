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
            raise FileNotFoundError(f"Prompt not found: {full_path}")
        post = frontmatter.load(str(full_path))
        template = self.env.from_string(post.content)
        return template.render(**kwargs).strip()

    def load_with_metadata(self, template_path: str, **kwargs: Any) -> Dict[str, Any]:
        full_path = self.prompts_dir / f"{template_path}.md"
        if not full_path.exists():
            raise FileNotFoundError(f"Prompt not found: {full_path}")
        post = frontmatter.load(str(full_path))
        template = self.env.from_string(post.content)
        rendered = template.render(**kwargs).strip()
        return {"content": rendered, "metadata": dict(post.metadata)}

_prompt_loader: Optional[PromptLoader] = None

def get_prompt_loader() -> PromptLoader:
    global _prompt_loader
    if _prompt_loader is None:
        prompts_dir = Path(__file__).parent.parent.parent / "prompts"
        _prompt_loader = PromptLoader(prompts_dir)
    return _prompt_loader

def load_prompt(template_path: str, **kwargs: Any) -> str:
    return get_prompt_loader().render(template_path, **kwargs)
