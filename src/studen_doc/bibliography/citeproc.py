"""
Оформление записей библиографии процессом pandoc (``--citeproc``): все записи документа - одним запуском.
"""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from studen_doc.errors import BibliographyError
from studen_doc.frontends.markdown.inlines import InlineConverter
from studen_doc.frontends.markdown.pandoc_ast import Node
from studen_doc.model.bibliography import ALL_SOURCES, Bibliography
from studen_doc.model.inline import Code, Inline, LineBreak, Math, ModelInline, Ref, Text
from studen_doc.pandoc import run_pandoc

#: Стили из пакета: описания по примерам ГОСТ 7.32-2017 (по умолчанию) и ГОСТ Р 7.0.5-2008.
STYLE_GOST_732 = Path(__file__).with_name("gost-7-32-numeric.csl")
STYLE_GOST_R_705 = Path(__file__).with_name("gost-r-7-0-5-2008-numeric.csl")
DEFAULT_CSL = STYLE_GOST_732

#: Что pandoc кладет в атрибуты блока записи: идентификатор ``ref-<ключ>`` и классы частей записи.
_ENTRY_PREFIX = "ref-"
_NUMBER_CLASS = "csl-left-margin"
_TEXT_CLASS = "csl-right-inline"


@dataclass(slots=True)
class PandocCiteproc:
    """
    ``SourceFormatter`` через pandoc: ключи -> текст записи по стилю CSL, без номера (номер ставит список отчета).

    ``command`` - команда запуска pandoc (по умолчанию ищется автоматически). Результаты запоминаются:
    одинаковый набор ключей повторно не оформляется.
    """

    bibliography: Bibliography
    command: Sequence[str] | None = None
    timeout_s: float = 120.0
    _cache: dict[tuple[str, ...], dict[str, tuple[Inline, ...]]] = field(default_factory=dict, init=False, repr=False)

    def __call__(self, keys: Sequence[str]) -> Mapping[str, tuple[Inline, ...]]:
        request = tuple(dict.fromkeys(keys))
        if request not in self._cache:
            self._cache[request] = self._format(request)
        return self._cache[request]

    def _format(self, keys: tuple[str, ...]) -> dict[str, tuple[Inline, ...]]:
        for path in self._paths():
            if not path.is_file():
                raise BibliographyError(f"Файл библиографии или стиля не найден: {path}")
        result = run_pandoc(self._arguments(), _source(keys), command=self.command, timeout_s=self.timeout_s)
        ast = json.loads(result.stdout)
        converter = InlineConverter()
        return {key: _plain(converter.convert(_entry_text(entry))) for key, entry in _entries(ast["blocks"])}

    def _paths(self) -> list[Path]:
        return [*self.bibliography.files, self._csl()]

    def _csl(self) -> Path:
        return self.bibliography.csl if self.bibliography.csl is not None else DEFAULT_CSL

    def _arguments(self) -> list[str]:
        files = [argument for path in self.bibliography.files for argument in ("--bibliography", str(path))]
        return ["-f", "markdown", "-t", "json", "--citeproc", "--csl", str(self._csl()), *files]


def _plain(nodes: Sequence[ModelInline]) -> tuple[Inline, ...]:
    """
    Узлы записи без ссылок на источники: в описании источника ``[@ключ]`` ничего не значит.
    """
    return tuple(node for node in nodes if isinstance(node, Text | Code | Math | Ref | LineBreak))


def _source(keys: Sequence[str]) -> bytes:
    """
    Документ из одних метаданных: ``nocite`` заставляет pandoc оформить записи, хотя ссылок в тексте нет.
    """
    cited = ", ".join(f"@{key}" for key in keys if key != ALL_SOURCES)
    if ALL_SOURCES in keys:
        cited = f"{cited}, @*" if cited else "@*"
    return f"---\nnocite: {json.dumps(cited)}\n---\n".encode()


def _entries(blocks: Sequence[Node]) -> Iterator[tuple[str, Node]]:
    """
    Записи из блока ``references`` в конце документа: ключ и абзац записи.
    """
    for block in blocks:
        match block:
            case {"t": "Div", "c": [[_, classes, _], children]} if "references" in classes:
                for child in children:
                    match child:
                        case {"t": "Div", "c": [[ident, _, _], [paragraph, *_]]} if ident.startswith(_ENTRY_PREFIX):
                            yield ident.removeprefix(_ENTRY_PREFIX), paragraph


def _entry_text(paragraph: Node) -> Sequence[Node]:
    """
    Текст записи без номера: у нумерованного стиля номер лежит в ``csl-left-margin``, текст - в ``csl-right-inline``.
    """
    for node in paragraph["c"]:
        match node:
            case {"t": "Span", "c": [[_, classes, _], inlines]} if _TEXT_CLASS in classes:
                return inlines
    return [
        node
        for node in paragraph["c"]
        if not (node["t"] == "Span" and _NUMBER_CLASS in node["c"][0][1])
    ]
