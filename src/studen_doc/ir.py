"""
Промежуточное представление (IR): отчёт после нумерации и разбора ссылок.

IR не зависит от формата вывода: DOCX-рендерер (и любой будущий — typst, LaTeX) получает плоскую
последовательность узлов, где уже есть номера, закладки, разобранный инлайн-текст и вычисленные
значения «по умолчанию». Рендерерам не нужно ничего считать — только рисовать.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

from studen_doc.model.blocks import ImageSource
from studen_doc.model.inline import Inline
from studen_doc.model.report import TitlePage
from studen_doc.style import ReportStyle
from studen_doc.types import Align

NumberKind = Literal["figure", "table", "listing", "formula"]
ListMarker = Literal["bullet", "1)", "1.", "a)", "a."]
Inlines = tuple[Inline, ...]


@dataclass(frozen=True, slots=True)
class Number:
    """
    Номер подписываемого элемента и закладка, на которую ссылаются поля REF.
    """

    kind: NumberKind
    display: str  # «3», «2.3», «А.1»
    bookmark: str
    use_seq: bool  # True -> номер можно оформить полем SEQ (сквозная нумерация)


@dataclass(frozen=True, slots=True)
class RHeading:
    level: int  # 1 — раздел, 2 — подраздел, ...
    title: str
    number: str | None  # «1», «1.2.3» либо None у структурных элементов
    structural: bool
    page_break: bool | None  # None -> по умолчанию заголовка


@dataclass(frozen=True, slots=True)
class RAppendixHeading:
    letter: str
    title: str | None
    status: str | None
    page_break: bool | None


@dataclass(frozen=True, slots=True)
class RParagraph:
    inlines: Inlines
    align: Align | None
    indent: bool
    keep_with_next: bool


@dataclass(frozen=True, slots=True)
class RFigure:
    source: ImageSource
    caption: Inlines
    number: Number
    width_cm: float | None


@dataclass(frozen=True, slots=True)
class RCell:
    inlines: Inlines
    numeric: bool


@dataclass(frozen=True, slots=True)
class RTable:
    header: tuple[Inlines, ...]
    rows: tuple[tuple[RCell, ...], ...]
    caption: Inlines | None
    number: Number | None
    col_widths_cm: tuple[float, ...] | None
    align: tuple[Align | None, ...] | None
    font_size_pt: float | None


@dataclass(frozen=True, slots=True)
class RListing:
    code: str
    caption: Inlines | None
    number: Number | None
    language: str | None
    line_numbers: bool  # уже с учётом стиля
    highlight: bool


@dataclass(frozen=True, slots=True)
class RFormula:
    latex: str
    number: Number | None
    where: tuple[tuple[str, Inlines], ...]


@dataclass(frozen=True, slots=True)
class RListItem:
    inlines: Inlines
    children: tuple[RListItem, ...] = ()


@dataclass(frozen=True, slots=True)
class RList:
    items: tuple[RListItem, ...]
    marker: ListMarker


@dataclass(frozen=True, slots=True)
class RSources:
    """
    Список использованных источников: готовые записи в порядке номеров (номер ставит рендерер списком ``1.``).
    """

    entries: tuple[Inlines, ...]


@dataclass(frozen=True, slots=True)
class RPageBreak:
    pass


@dataclass(frozen=True, slots=True)
class RToc:
    title: str
    levels: int
    page_break_after: bool


RNode = (
    RHeading
    | RAppendixHeading
    | RParagraph
    | RFigure
    | RTable
    | RListing
    | RFormula
    | RList
    | RSources
    | RPageBreak
    | RToc
)


@dataclass(frozen=True, slots=True)
class ResolvedReport:
    style: ReportStyle
    nodes: tuple[RNode, ...]
    labels: Mapping[str, Number]
    title_page: TitlePage | None = None
    title: str | None = None
    author: str | None = None
    #: Все формулы LaTeX документа без повторов, в порядке появления (их переводят в OMML одним вызовом).
    formulas: tuple[str, ...] = ()

    @property
    def has_toc(self) -> bool:
        return any(isinstance(node, RToc) for node in self.nodes)
