"""
Инлайн-узлы (текст внутри абзаца, подписи, ячейки).

Модель - набор неизменяемых узлов: их собирают вручную, ``P("см. ", Ref("fig:a"), " и ", B("важно"))``.
Обычная строка - всегда буквальный текст, без разметки. Разметка Markdown включается явно: ``Md("см. *важно*")``;
такие строки разбирает pandoc, все сразу одним вызовом на документ (см. ``Report.resolve``).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Literal, TypeGuard

#: Надстрочный и подстрочный текст.
type Script = Literal["sup", "sub"]


@dataclass(frozen=True, slots=True)
class Text:
    text: str
    bold: bool = False
    italic: bool = False
    script: Script | None = None


@dataclass(frozen=True, slots=True)
class Code:
    """
    Моноширинный фрагмент (имена переменных, файлов).
    """

    text: str
    bold: bool = False
    italic: bool = False


@dataclass(frozen=True, slots=True)
class Math:
    """
    Формула LaTeX в строке текста.
    """

    latex: str


@dataclass(frozen=True, slots=True)
class Ref:
    """
    Ссылка на номер рисунка, таблицы, листинга или формулы по строковой метке (``label="fig:x"``).
    В Python ссылку на блок можно взять и напрямую: ``figure.ref`` (см. ``BlockRef``).
    """

    label: str
    bold: bool = False
    italic: bool = False


@dataclass(frozen=True, slots=True)
class Citation:
    """
    Один источник в ссылке: ключ записи и, если нужно, место в источнике (``"с. 5"``).
    """

    key: str
    locator: str | None = None


@dataclass(frozen=True, slots=True, init=False)
class Cite:
    """
    Ссылка на источник из списка использованных источников; по ГОСТ 7.32 (6.9.1) это номер записи в квадратных
    скобках: ``Cite("ivanov2020")`` -> ``[1]``, ``Cite("a", "b")`` -> ``[1, 2]``,
    ``Cite(Citation("a", "с. 5"))`` -> ``[1, с. 5]``.

    Номера выдаются в порядке первой ссылки в тексте; в Markdown та же ссылка записывается ``[@ivanov2020]``.
    """

    citations: tuple[Citation, ...]
    bold: bool
    italic: bool

    def __init__(self, *citations: str | Citation, bold: bool = False, italic: bool = False) -> None:
        if not citations:
            raise ValueError("Cite без ключей: укажите хотя бы один источник")
        entries = tuple(Citation(item) if isinstance(item, str) else item for item in citations)
        object.__setattr__(self, "citations", entries)
        object.__setattr__(self, "bold", bold)
        object.__setattr__(self, "italic", italic)


@dataclass(frozen=True, slots=True)
class LineBreak:
    """Перенос строки внутри абзаца."""


@dataclass(frozen=True, slots=True)
class Md:
    """
    Строка с инлайн-разметкой Markdown (один абзац): ``Md("см. [](#fig:a) и **важно** при $R^2 > 0.8$")``.

    Разбирает pandoc (диалект как у ``Report.from_markdown``): **жирный**, *курсив*, `код`, ``$формула$``,
    ``^надстрочный^``, ``~подстрочный~``, ``[](#метка)`` - ссылка на номер, ``\\`` и перевод строки - перенос строки.
    """

    source: str


@dataclass(frozen=True, slots=True, eq=False)
class BlockRef:
    """
    Ссылка на номер самого блока: ``figure.ref`` у рисунка, таблицы, листинга и формулы. Метка не нужна:
    блок находится по объекту. Сравнивается по тождеству блока, а не по значению.

    Блок должен быть в отчете ровно один раз и иметь номер (у таблицы и листинга - подпись, у формулы - номер).
    """

    target: object
    bold: bool = False
    italic: bool = False


Inline = Text | Code | Math | Ref | LineBreak
#: Узлы текста до разбора отчета: при ``Report.resolve`` ``BlockRef`` становится ``Ref``, ``Cite`` - текстом ``[1]``.
type ModelInline = Inline | BlockRef | Cite
#: Всё, что принимают блоки вместо текста: строка (буквально), узел, ``Md`` либо последовательность из них.
type RichText = str | ModelInline | Md | Sequence[RichText]
#: Разбор строк с разметкой: все строки документа сразу -> узлы для каждой.
type InlineParser = Callable[[Sequence[str]], Mapping[str, tuple[ModelInline, ...]]]
type _Markup = Callable[[str], tuple[ModelInline, ...]]


def B(text: str) -> Text:
    """
    Жирный текст.
    """
    return Text(text, bold=True)


def I(text: str) -> Text:  # noqa: E743 - короткое имя параллельно B осознанно
    """
    Курсив.
    """
    return Text(text, italic=True)


def merge_text(nodes: Iterable[ModelInline]) -> tuple[ModelInline, ...]:
    """
    Склеивает соседние Text с одинаковым начертанием (после разбора разметки их остаётся несколько).
    """
    merged: list[ModelInline] = []
    for node in nodes:
        previous = merged[-1] if merged else None
        if isinstance(previous, Text) and isinstance(node, Text) and _look(previous) == _look(node):
            merged[-1] = replace(previous, text=previous.text + node.text)
        else:
            merged.append(node)
    return tuple(merged)


def _look(node: Text) -> tuple[bool, bool, Script | None]:
    return node.bold, node.italic, node.script


def plain_text(nodes: Iterable[ModelInline]) -> str:
    """
    Текст узлов без оформления: формулы дают LaTeX, ссылки и переносы строк - ничего.
    """
    return "".join(
        node.latex if isinstance(node, Math) else node.text for node in nodes if isinstance(node, Text | Code | Math)
    )


def is_rich_text(value: object) -> TypeGuard[RichText]:
    """
    Значение уже допустимый ``RichText`` (строка, узел, ``Md``, последовательность), а не, например, число.
    """
    return isinstance(value, Text | Code | Math | Ref | LineBreak | BlockRef | Cite | Md | Sequence)


def as_inlines(value: RichText, markup: _Markup) -> tuple[ModelInline, ...]:
    """
    Приводит любое допустимое «богатое» значение к кортежу узлов; ``markup`` разбирает ``Md``.
    """
    match value:
        case str():
            return (Text(value),) if value else ()
        case Md(source=source):
            return markup(source)
        case Text() | Code() | Math() | Ref() | LineBreak() | BlockRef() | Cite():
            return (value,)
        case _:
            return tuple(node for part in value for node in as_inlines(part, markup))
