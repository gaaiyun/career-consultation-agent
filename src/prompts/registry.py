from __future__ import annotations

from pathlib import Path

from src.config.settings import Settings


class PromptRegistry:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def get_prompt(self, name: str) -> str:
        path = self.settings.prompts_dir / f"{name}.md"
        if not path.exists():
            raise FileNotFoundError(f"Prompt not found: {path}")
        return path.read_text(encoding="utf-8")

    def render_prompt(self, name: str, variables: dict[str, str]) -> str:
        prompt = self.get_prompt(name)
        for key, value in variables.items():
            prompt = prompt.replace(f"{{{{ {key} }}}}", value)
        return prompt
