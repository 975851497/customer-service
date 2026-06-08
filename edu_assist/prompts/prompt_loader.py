"""提示词加载器。"""

from __future__ import annotations

from pathlib import Path

from jinja2 import Template

_PROMPTS_DIR = Path(__file__).resolve().parent / "jinja2"


def load_prompt(file_name: str) -> Template:
    """从 prompts/jinja2/ 目录加载 .jinja2 模板文件。"""
    file_path = _PROMPTS_DIR / file_name
    with open(file_path, "r", encoding="utf-8") as f:
        return Template(f.read())
