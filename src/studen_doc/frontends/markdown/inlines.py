"""
Инлайн-узлы pandoc (текст внутри абзаца, подписи, ячейки) -> инлайны модели.

Вложенное оформление pandoc (``Strong[Emph[Str]]``) разворачивается в плоские узлы ``Text`` с флагами
``bold``, ``italic``, ``script``: так их рисует рендерер, по одному запуску Word на узел.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass, replace
from functools import partial

from studen_doc.errors import MarkdownError
from studen_doc.frontends.markdown.citations import split_citations
from studen_doc.frontends.markdown.pandoc_ast import Attr, Node
from studen_doc.frontends.markdown.substitutions import Substitutions
from studen_doc.model.inline import (
    Cite,
    Code,
    LineBreak,
    Math,
    ModelInline,
    Ref,
    Script,
    Text,
    merge_text,
    plain_text,
)

_QUOTES = {"DoubleQuote": ("«", "»"), "SingleQuote": ("„", "“")}


@dataclass(frozen=True, slots=True)
class _Look:
    """
    Начертание, накопленное при обходе вложенных узлов оформления.
    """

    bold: bool = False
    italic: bool = False
    script: Script | None = None

    def text(self, value: str) -> Text:
        return Text(value, self.bold, self.italic, self.script)


def _keep(look: _Look) -> _Look:
    return look


#: Узлы оформления: как они меняют начертание вложенного текста. Оформление без аналога в отчете
#: (зачеркнутый, подчеркнутый, капитель) пропускается: остается просто текст.
_STYLES: dict[str, Callable[[_Look], _Look]] = {
    "Emph": partial(replace, italic=True),
    "Strong": partial(replace, bold=True),
    "Superscript": partial(replace, script="sup"),
    "Subscript": partial(replace, script="sub"),
    "Strikeout": _keep,
    "Underline": _keep,
    "SmallCaps": _keep,
}


class InlineConverter:
    """
    Превращает инлайн-узлы pandoc в инлайны модели; подставляет значения ``[]{var=...}``.
    """

    def __init__(self, substitutions: Substitutions | None = None) -> None:
        self._substitutions = substitutions or Substitutions()

    def convert(self, nodes: Sequence[Node]) -> tuple[ModelInline, ...]:
        """
        Инлайны модели; соседний текст с одинаковым начертанием склеивается в один узел.
        """
        return merge_text(self._walk(nodes, _Look()))

    def plain(self, nodes: Sequence[Node]) -> str:
        """
        Текст без оформления (заголовки, значения метаданных).
        """
        return plain_text(self.convert(nodes))

    def _walk(self, nodes: Sequence[Node], look: _Look) -> Iterator[ModelInline]:
        """
        Узлы подряд: слова и пробелы склеиваются в текст (в нем ищутся ``[@ссылки]``), остальное обходится по типу.
        """
        words: list[str] = []
        for node in nodes:
            match node:
                case {"t": "Str", "c": text}:
                    words.append(text)
                case {"t": "Space" | "SoftBreak"}:
                    words.append(" ")
                case _:
                    yield from self._text(words, look)
                    words = []
                    yield from self._node(node, look)
        yield from self._text(words, look)

    @staticmethod
    def _text(words: list[str], look: _Look) -> Iterator[ModelInline]:
        for part in split_citations("".join(words)):
            if isinstance(part, str):
                yield look.text(part)
            else:
                yield Cite(*part, bold=look.bold, italic=look.italic)

    def _node(self, node: Node, look: _Look) -> Iterator[ModelInline]:
        match node:
            case {"t": "LineBreak"}:
                yield LineBreak()
            case {"t": kind, "c": children} if kind in _STYLES:
                yield from self._walk(children, _STYLES[kind](look))
            case {"t": "Span", "c": [attr, children]}:
                yield from self._span(Attr.parse(attr), children, look)
            case {"t": "Code", "c": [_attr, text]}:
                yield Code(text, look.bold, look.italic)
            case {"t": "Math", "c": [_kind, latex]}:
                yield Math(latex.strip())
            case {"t": "Quoted", "c": [{"t": quote}, children]}:
                opening, closing = _QUOTES[quote]
                yield look.text(opening)
                yield from self._walk(children, look)
                yield look.text(closing)
            case {"t": "Link", "c": [_attr, children, [url, _title]]}:
                yield from self._link(children, url, look)
            case {"t": "Image"}:
                raise MarkdownError("Картинка допустима только отдельным абзацем")
            case {"t": kind}:
                raise MarkdownError(f"Элемент {kind} пока не поддерживается")

    def _span(self, attr: Attr, children: Sequence[Node], look: _Look) -> Iterator[ModelInline]:
        """
        ``[]{var=имя format=".3f"}`` - значение из Python; любой другой фрагмент прозрачен.
        """
        name = attr.options.text("var")
        if name is None:
            yield from self._walk(children, look)
        else:
            yield look.text(self._substitutions.variable(name, attr.options.text("format") or ""))

    def _link(self, children: Sequence[Node], url: str, look: _Look) -> Iterator[ModelInline]:
        """
        Ссылка на метку (``#fig:x``) становится номером; внешняя - текстом, за которым в скобках стоит адрес.
        """
        if url.startswith("#"):
            yield Ref(url[1:], look.bold, look.italic)
            return
        text = tuple(self._walk(children, look))
        yield from text
        if plain_text(text) != url:
            yield look.text(f" ({url})")
