"""Versioned prompt loading. Prompts are code (CLAUDE.md §17)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.ai.provider import PageInput

PROMPT_DIR = Path(__file__).parent / "prompts"


@lru_cache
def load_prompt(name: str) -> str:
    return (PROMPT_DIR / f"{name}.md").read_text(encoding="utf-8")


def render_pages(pages: list[PageInput]) -> str:
    return "\n\n".join(f"=== PAGE {p.page_number} ===\n{p.text}" for p in pages)


def render_extraction_prompt(pages: list[PageInput], schema: dict[str, Any]) -> tuple[str, str]:
    """Returns (system_prompt, user_prompt)."""
    template = load_prompt("extraction_v1")
    head, _, _ = template.partition("## Pages")
    system = head.replace("{{SCHEMA}}", json.dumps(schema, separators=(",", ":")))
    user = "## Pages\n" + render_pages(pages)
    return system, user
