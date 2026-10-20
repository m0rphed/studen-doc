"""
Контракт рендер-реализации: любой формат вывода (docx, typst, ...) принимает IR и пишет файл.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from studen_doc.ir import ResolvedReport


class Renderer(Protocol):
    """
    Рендерер формата.
    Получает уже пронумерованный отчёт (со стилем внутри) и путь результата.
    """

    def render(self, report: ResolvedReport, path: Path) -> Path: ...
