"""Satu file = satu agent. Persona ada di smart_library/prompts/<nama>.md."""

from importlib import resources


def load_prompt(name: str) -> str:
    return resources.files("smart_library.prompts").joinpath(f"{name}.md").read_text(encoding="utf-8")
