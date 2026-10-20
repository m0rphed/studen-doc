"""
Блоки содержимого отчёта — неизменяемые данные без знания о стиле и формате вывода.

Любой текст внутри блоков — :data:`RichText`: строка (буквально), ``Md("...")`` с разметкой Markdown
или узлы ``Text``/``Math``/``Ref``...

Обязательное у каждого блока (содержимое, подпись) передается позиционно, настройки - только по имени:
``Table(header, rows, caption="Итоги", label="tab:r")``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import KW_ONLY, dataclass
from pathlib import Path
from typing import BinaryIO, Literal, Self

from studen_doc.model.inline import BlockRef, Md, RichText
from studen_doc.types import Align

ImageSource = str | Path | BinaryIO

#: Маркеры нумерованных списков в канонической записи: цифры (``1)``, ``1.``) или буквы (``a)``, ``a.``).
#: Буквы печатаются русскими по ГОСТ 7.32 (а, б, в...), а в записи - латинская ``a``, как в Markdown.
type NumberedMarker = Literal["1)", "1.", "a)", "a."]

#: Допустимые записи маркера: канонические и те же с кириллической «а» (``"а)"``, ``"а."``).
type MarkerSpelling = NumberedMarker | Literal["а)", "а."]

_MARKER_SPELLINGS: dict[str, NumberedMarker] = {
    "1)": "1)",
    "1.": "1.",
    "a)": "a)",
    "a.": "a.",
    "а)": "a)",  # кириллическая «а» выглядит как латинская, поэтому принимается как та же буква
    "а.": "a.",
}


def normalize_marker(marker: str) -> NumberedMarker:
    """
    Каноническая запись маркера списка; любая другая строка (с пробелами, другими символами) - ``ValueError``.
    """
    try:
        return _MARKER_SPELLINGS[marker]
    except KeyError:
        raise ValueError(
            f"Маркер списка {marker!r} не поддерживается: допустимы 1), 1., a), a. "
            "(буква латинская или кириллическая, без пробелов и других символов)"
        ) from None


@dataclass(frozen=True, slots=True)
class ListItem:
    """
    Пункт списка с подпунктами любой глубины.
    """

    text: RichText
    children: Sequence[ListEntry] = ()


#: Пункт списка: текст (``RichText``) либо ``ListItem`` с подпунктами.
ListEntry = RichText | ListItem


@dataclass(frozen=True, slots=True, init=False)
class P:
    """
    Абзац основного текста: ``P("текст ", Ref("fig:a"), " ещё текст")``.
    """

    parts: tuple[RichText, ...]
    align: Align | None
    indent: bool
    keep_with_next: bool

    def __init__(
        self,
        *parts: RichText,
        align: Align | None = None,
        indent: bool = True,
        keep_with_next: bool = False,
    ) -> None:
        object.__setattr__(self, "parts", parts)
        object.__setattr__(self, "align", align)
        object.__setattr__(self, "indent", indent)
        object.__setattr__(self, "keep_with_next", keep_with_next)

    @classmethod
    def md(
        cls,
        source: str,
        *,
        align: Align | None = None,
        indent: bool = True,
        keep_with_next: bool = False,
    ) -> Self:
        """
        Абзац из текста с разметкой Markdown: ``P.md("см. [](#fig:a) и **важно**")`` - то же, что ``P(Md("..."))``.
        """
        return cls(Md(source), align=align, indent=indent, keep_with_next=keep_with_next)


@dataclass(frozen=True, slots=True)
class Figure:
    """
    Рисунок с подписью «Рисунок N — ...».
    """

    source: ImageSource
    caption: RichText
    _: KW_ONLY
    label: str | None = None
    width_cm: float | None = None

    @property
    def ref(self) -> BlockRef:
        """
        Ссылка на номер этого блока для текста: ``P("см. ", block.ref)``.
        """
        return BlockRef(self)


@dataclass(frozen=True, slots=True)
class Table:
    """
    Таблица; подпись «Таблица N — ...» над ней, если задан caption.
    """

    header: Sequence[RichText]
    rows: Sequence[Sequence[object]]
    _: KW_ONLY
    caption: RichText | None = None
    label: str | None = None
    col_widths_cm: Sequence[float] | None = None
    align: Sequence[Align | None] | None = None  # выравнивание по столбцам; None у столбца - по стилю
    font_size_pt: float | None = None

    @property
    def ref(self) -> BlockRef:
        """
        Ссылка на номер этого блока для текста: ``P("см. ", block.ref)``.
        """
        return BlockRef(self)


@dataclass(frozen=True, slots=True)
class Listing:
    """
    Листинг кода; подпись «Листинг N — ...» над ним, если задан caption.
    """

    code: str
    caption: RichText | None = None
    _: KW_ONLY
    label: str | None = None
    language: str | None = None  # для подсветки синтаксиса
    line_numbers: bool | None = None  # None -> как в стиле
    highlight: bool | None = None  # None -> как в стиле

    @property
    def ref(self) -> BlockRef:
        """
        Ссылка на номер этого блока для текста: ``P("см. ", block.ref)``.
        """
        return BlockRef(self)


#: Пояснения под формулой: словарь «символ -> описание» либо список пар.
type Legend = Mapping[str, RichText] | Sequence[tuple[str, RichText]]


@dataclass(frozen=True, slots=True)
class Formula:
    """
    Выключная формула LaTeX; нумеруется справа «(N)», если есть label (или numbered=True).

    ``where`` - пояснения под формулой («где y - факт; n - размер выборки.»):
    ``where={"y": "факт", "n": "размер выборки"}``; хранится всегда как кортеж пар.
    """

    latex: str
    _: KW_ONLY
    label: str | None = None
    numbered: bool | None = None  # None -> нумеровать, если есть label
    where: Legend = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "where", self.legend)  # единая форма: равенство не зависит от способа записи

    @property
    def legend(self) -> tuple[tuple[str, RichText], ...]:
        """
        Пояснения парами «символ - описание» в порядке записи.
        """
        pairs = self.where.items() if isinstance(self.where, Mapping) else self.where
        return tuple((symbol, text) for symbol, text in pairs)

    @property
    def ref(self) -> BlockRef:
        """
        Ссылка на номер этой формулы для текста: ``P("см. формулу ", formula.ref)``.
        """
        return BlockRef(self)


@dataclass(frozen=True, slots=True)
class Bullets:
    """
    Маркированный список (по ГОСТ маркер — тире).
    """

    items: Sequence[ListEntry]


@dataclass(frozen=True, slots=True)
class Numbered:
    """
    Нумерованный список: ``marker`` - ``"1)"``, ``"1."``, ``"a)"`` или ``"a."`` (буква печатается русской по ГОСТ,
    записывать можно латинской или кириллической). Вложенность - через ``ListItem(текст, [подпункты])``.
    """

    items: Sequence[ListEntry]
    _: KW_ONLY
    marker: MarkerSpelling = "1)"

    def __post_init__(self) -> None:
        object.__setattr__(self, "marker", normalize_marker(self.marker))  # ошибка сразу, а не при сборке


@dataclass(frozen=True, slots=True)
class Source:
    """
    Источник, записанный вручную: ``Source("ivanov2020", "Иванов И. И. Основы ... - М., 2020.")``. По ``key`` на него
    можно сослаться из текста: ``Cite("ivanov2020")``.
    """

    key: str
    text: RichText


@dataclass(frozen=True, slots=True)
class Sources:
    """
    Список использованных источников по ГОСТ 7.32 (6.16): нумерованный список «1.» с абзацным отступом.

    В списке источники, на которые есть ссылки, в порядке первой ссылки, затем остальные. Записи берутся из
    ``entries`` (вручную: просто текст или ``Source`` с ключом) и из библиографии отчета (``Report.bibliography``):
    по ссылкам ``Cite``/``[@ключ]`` и по ``nocite`` - ключам записей, которые нужны в списке без ссылок
    (``"*"`` - все записи библиографии).
    """

    entries: Sequence[Source | RichText] = ()
    _: KW_ONLY
    nocite: Sequence[str] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "entries", tuple(self.entries))  # единая форма: равенство не зависит от записи
        object.__setattr__(self, "nocite", tuple(self.nocite))


@dataclass(frozen=True, slots=True)
class PageBreak:
    """
    Принудительный разрыв страницы.
    """


@dataclass(frozen=True, slots=True, init=False)
class Subsection:
    """
    Подраздел; уровень заголовка определяется вложенностью Subsection друг в друга.
    """

    title: str
    content: tuple[Block, ...]

    def __init__(self, title: str, *content: Block) -> None:
        object.__setattr__(self, "title", title)
        object.__setattr__(self, "content", content)


Block = P | Figure | Table | Listing | Formula | Bullets | Numbered | Sources | PageBreak | Subsection
