"""
Листинги из исходного кода: функции и классы Python, файлы.
"""

from __future__ import annotations

import inspect
import textwrap
from collections.abc import Callable
from pathlib import Path
from typing import Any

from studen_doc.model.blocks import Listing
from studen_doc.model.inline import RichText

#: Язык подсветки по расширению файла.
_LANGUAGES = {
    ".py": "python",
    ".sql": "sql",
    ".sh": "bash",
    ".json": "json",
    ".cpp": "cpp",
    ".c": "c",
    ".h": "c",
    ".java": "java",
    ".js": "javascript",
    ".ts": "typescript",
    ".cs": "csharp",
    ".go": "go",
    ".rs": "rust",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".md": "markdown",
    ".html": "html",
    ".css": "css",
}


def listing_from_callable(
    obj: Callable[..., Any] | type,
    caption: RichText | None = None,
    *,
    label: str | None = None,
    line_numbers: bool | None = None,
    highlight: bool | None = None,
) -> Listing:
    """
    Листинг с исходным кодом функции или класса Python (``inspect.getsource``): код в отчете всегда настоящий.
    """
    code = textwrap.dedent(inspect.getsource(obj))
    return Listing(code, caption, label=label, language="python", line_numbers=line_numbers, highlight=highlight)


def listing_from_file(
    path: str | Path,
    caption: RichText | None = None,
    *,
    lines: tuple[int, int] | None = None,
    language: str | None = None,
    label: str | None = None,
    line_numbers: bool | None = None,
    highlight: bool | None = None,
) -> Listing:
    """
    Листинг из файла с кодом; ``lines=(5, 20)`` - только строки с 5 по 20 включительно (нумерация с 1).
    Язык по умолчанию определяется по расширению файла.
    """
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if lines is not None:
        first, last = lines
        text = "\n".join(text.splitlines()[first - 1 : last])
    return Listing(
        text,
        caption,
        label=label,
        language=language or _LANGUAGES.get(path.suffix.lower()),
        line_numbers=line_numbers,
        highlight=highlight,
    )
