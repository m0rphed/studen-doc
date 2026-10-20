"""
Тематические неизменяемые описания оформления: страница, текст, подписи, рисунки, таблицы...

Правило: ``None`` в поле означает «значения нет» (например, нет заливки), а не «возьми из другого места» —
все размеры и интервалы здесь конкретные числа.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from studen_doc.style.evolve import Evolvable
from studen_doc.types import Align, BoxAlign

NumberScope = Literal["continuous", "section"]


@dataclass(frozen=True, slots=True, kw_only=True)
class PageStyle(Evolvable):
    width_mm: float = 210
    height_mm: float = 297
    margin_left_mm: float = 30
    margin_right_mm: float = 15
    margin_top_mm: float = 20
    margin_bottom_mm: float = 20
    footer_distance_mm: float = 10

    @property
    def text_width_cm(self) -> float:
        return (self.width_mm - self.margin_left_mm - self.margin_right_mm) / 10


@dataclass(frozen=True, slots=True, kw_only=True)
class PageNumberStyle(Evolvable):
    align: Literal["left", "center", "right", "none"] = "center"
    show_on_title_page: bool = False


@dataclass(frozen=True, slots=True, kw_only=True)
class TextStyle(Evolvable):
    font_name: str = "Times New Roman"
    size_pt: float = 14
    mono_font_name: str = "Courier New"
    mono_size_pt: float = 12
    line_spacing: float = 1.5
    first_indent_cm: float = 1.25
    align: Align = "justify"
    language: str = "ru-RU"
    color: str = "000000"  # цвет текста (hex RGB)


@dataclass(frozen=True, slots=True, kw_only=True)
class CaptionStyle(Evolvable):
    """
    Подпись «<label> N — текст».
    """

    label: str
    dash: str = "—"  # «—» (тире) или «–» (среднее тире)
    align: Align = "left"
    size_pt: float = 14
    line_spacing: float = 1.0
    before_pt: float = 0
    after_pt: float = 0
    keep_with_next: bool = False


@dataclass(frozen=True, slots=True, kw_only=True)
class FigureStyle(Evolvable):
    caption: CaptionStyle = CaptionStyle(label="Рисунок", align="center", after_pt=6)
    width_fraction: float = 1.0  # ширина по умолчанию — доля ширины текста
    max_height_cm: float = 19.0
    gap_pt: float = 6.0  # отступы вокруг картинки


@dataclass(frozen=True, slots=True, kw_only=True)
class CellPadding(Evolvable):
    """
    Поля внутри ячеек таблицы, в двадцатых долях пункта (twips).
    """

    top: int = 20
    bottom: int = 20
    left: int = 80
    right: int = 80


@dataclass(frozen=True, slots=True, kw_only=True)
class TableStyle(Evolvable):
    caption: CaptionStyle = CaptionStyle(label="Таблица", before_pt=6, after_pt=4, keep_with_next=True)
    cell_padding: CellPadding = CellPadding()
    font_size_pt: float = 12
    line_spacing: float = 1.0
    align: BoxAlign = "center"
    header_bold: bool = True
    header_align: Align = "center"
    header_fill: str | None = None  # None -> без заливки
    body_align: Align = "left"
    numeric_align: Align = "center"
    border_sz: int = 4  # в восьмых долях пункта
    gap_after_pt: float = 10.0


@dataclass(frozen=True, slots=True, kw_only=True)
class ListingStyle(Evolvable):
    caption: CaptionStyle = CaptionStyle(
        label="Листинг",
        before_pt=6,
        after_pt=4,
        keep_with_next=True,
    )
    font_size_pt: float = 12
    box: bool = True
    border_sz: int = 4  # толщина рамки, в восьмых долях пункта
    border_color: str = "808080"
    border_padding_pt: int = 2  # расстояние от текста до рамки
    fill: str | None = None  # например "F5F5F5"; None -> без заливки
    line_numbers: bool = False
    line_number_color: str = "808080"
    highlight: bool = False  # цветная подсветка (нужен pygments)
    pygments_style: str = "default"
    gap_after_pt: float = 10.0
    keep_together_lines: int = 15  # листинг не длиннее целиком остается на одной странице
    edge_lines: int = 2  # сколько строк минимум остается на странице при разрыве листинга сверху и снизу


@dataclass(frozen=True, slots=True, kw_only=True)
class FormulaStyle(Evolvable):
    label: str = "Формула"  # имя последовательности SEQ в полях Word
    number_format: str = "({n})"
    gap_pt: float = 6.0
    number_width_cm: float = 1.5
    legend_word: str = "где"  # слово перед расшифровкой обозначений под формулой
    legend_dash: str = "—"  # знак между обозначением и пояснением


@dataclass(frozen=True, slots=True, kw_only=True)
class ListStyle(Evolvable):
    bullet: str = "–"
    nested_indent_cm: float = 1.25
    #: True — настоящие списки Word (маркеры рисует Word, список редактируется); False — старый формат:
    #: маркер печатается в тексте пункта. Буквенные списки длиннее 7 пунктов в режиме True тоже статические.
    word_numbering: bool = True


@dataclass(frozen=True, slots=True, kw_only=True)
class NumberingStyle(Evolvable):
    """Рисунок 3 (``continuous``) или Рисунок 2.3 (``section``)."""

    scope: NumberScope = "continuous"
