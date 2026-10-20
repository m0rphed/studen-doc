"""
Чтение AST pandoc: запуск процесса, проверка версии формата и обертки над узлами.

AST приходит как JSON: узел - словарь ``{"t": тип, "c": содержимое}``. Разбирают его ``match``-выражения
в модулях ``inlines``, ``blocks`` и ``tables``.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from studen_doc.errors import MarkdownError
from studen_doc.frontends.markdown.options import Options
from studen_doc.pandoc import run_pandoc

#: Диалект Markdown: CommonMark плюс расширения pandoc (список: ``pandoc --list-extensions=commonmark_x``).
PANDOC_FORMAT = "commonmark_x+implicit_figures"

#: Минимальная версия формата AST pandoc (pandoc-api-version): с нее устроены ``Figure`` и ``Table``.
MIN_API_VERSION = (1, 23)

#: Блоки с текстом абзаца: обычный абзац и "голый" абзац внутри пункта списка или ячейки.
TEXT_BLOCKS = ("Para", "Plain")

type Node = dict[str, Any]


@dataclass(frozen=True, slots=True)
class Attr:
    """
    Атрибуты блока или фрагмента: ``{#идентификатор .класс ключ=значение}``.
    """

    ident: str
    classes: tuple[str, ...]
    options: Options

    @classmethod
    def parse(cls, raw: Sequence[Any]) -> Attr:
        """
        Из формата pandoc: ``[идентификатор, [классы], [[ключ, значение], ...]]``.
        """
        ident, classes, pairs = raw
        return cls(ident, tuple(classes), Options(dict(pairs)))

    @property
    def label(self) -> str | None:
        """
        Идентификатор как метка для ссылок (``None``, если не задан).
        """
        return self.ident or None


def read_ast(text: str, *, command: Sequence[str] | None, timeout_s: float) -> Node:
    """
    Разбирает Markdown процессом pandoc и возвращает корень AST (``meta`` и ``blocks``).
    """
    result = run_pandoc(("-f", PANDOC_FORMAT, "-t", "json"), text.encode("utf-8"), command=command, timeout_s=timeout_s)
    ast = json.loads(result.stdout)
    version = tuple(ast["pandoc-api-version"][:2])
    if version < MIN_API_VERSION:
        raise MarkdownError(f"Версия AST pandoc {version} старше поддерживаемой {MIN_API_VERSION}: обновите pandoc")
    return ast


def is_text_block(node: Node) -> bool:
    return node["t"] in TEXT_BLOCKS


def first_text(blocks: Sequence[Node]) -> Sequence[Node]:
    """
    Инлайны первого абзаца из списка блоков (подпись рисунка, описание в определении); пусто, если абзацев нет.
    """
    return next((block["c"] for block in blocks if is_text_block(block)), ())
