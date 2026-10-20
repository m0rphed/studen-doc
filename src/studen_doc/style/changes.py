"""Сгенерировано tools/generate_style_changes.py по dataclass-ам стиля: не править вручную. TypedDict-ы описывают аргументы ReportStyle.evolve."""
from __future__ import annotations
from collections.abc import Mapping
from typing import Literal, TypedDict
from studen_doc.style.components import CaptionStyle, CellPadding, FigureStyle, FormulaStyle, ListStyle, ListingStyle, NumberScope, NumberingStyle, PageNumberStyle, PageStyle, TableStyle, TextStyle
from studen_doc.style.headings import HeadingStyle, HeadingsStyle, SectionRule
from studen_doc.types import Align, BoxAlign

class PageStyleChanges(TypedDict, total=False):
    """Правки ``PageStyle`` для ``evolve``."""
    width_mm: float
    height_mm: float
    margin_left_mm: float
    margin_right_mm: float
    margin_top_mm: float
    margin_bottom_mm: float
    footer_distance_mm: float

class PageNumberStyleChanges(TypedDict, total=False):
    """Правки ``PageNumberStyle`` для ``evolve``."""
    align: Literal['left', 'center', 'right', 'none']
    show_on_title_page: bool

class TextStyleChanges(TypedDict, total=False):
    """Правки ``TextStyle`` для ``evolve``."""
    font_name: str
    size_pt: float
    mono_font_name: str
    mono_size_pt: float
    line_spacing: float
    first_indent_cm: float
    align: Align
    language: str
    color: str

class HeadingStyleChanges(TypedDict, total=False):
    """Правки ``HeadingStyle`` для ``evolve``. Оформление заголовка одного уровня."""
    size_pt: float
    bold: bool
    italic: bool
    caps: bool
    align: Align
    first_indent_cm: float
    before_pt: float
    after_pt: float
    line_spacing: float
    keep_with_next: bool
    page_break_before: bool

class SectionRuleChanges(TypedDict, total=False):
    """Правки ``SectionRule`` для ``evolve``. Как оформляется раздел с данным именем (Введение, Ход работы, ...)."""
    numbered: bool
    structural: bool
    page_break_before: bool | None
    appendix: bool

class HeadingsStyleChanges(TypedDict, total=False):
    """Правки ``HeadingsStyle`` для ``evolve``. Вложенный стиль - словарем правок или готовым объектом."""
    structural: HeadingStyleChanges | HeadingStyle
    level1: HeadingStyleChanges | HeadingStyle
    level2: HeadingStyleChanges | HeadingStyle
    level3: HeadingStyleChanges | HeadingStyle
    number_separator: str
    appendix_word: str
    appendix_gap_pt: float
    rules: Mapping[str, SectionRule]
    default_rule: SectionRuleChanges | SectionRule

class CaptionStyleChanges(TypedDict, total=False):
    """Правки ``CaptionStyle`` для ``evolve``. Подпись «<label> N — текст»."""
    label: str
    dash: str
    align: Align
    size_pt: float
    line_spacing: float
    before_pt: float
    after_pt: float
    keep_with_next: bool

class FigureStyleChanges(TypedDict, total=False):
    """Правки ``FigureStyle`` для ``evolve``. Вложенный стиль - словарем правок или готовым объектом."""
    caption: CaptionStyleChanges | CaptionStyle
    width_fraction: float
    max_height_cm: float
    gap_pt: float

class CellPaddingChanges(TypedDict, total=False):
    """Правки ``CellPadding`` для ``evolve``. Поля внутри ячеек таблицы, в двадцатых долях пункта (twips)."""
    top: int
    bottom: int
    left: int
    right: int

class TableStyleChanges(TypedDict, total=False):
    """Правки ``TableStyle`` для ``evolve``. Вложенный стиль - словарем правок или готовым объектом."""
    caption: CaptionStyleChanges | CaptionStyle
    cell_padding: CellPaddingChanges | CellPadding
    font_size_pt: float
    line_spacing: float
    align: BoxAlign
    header_bold: bool
    header_align: Align
    header_fill: str | None
    body_align: Align
    numeric_align: Align
    border_sz: int
    gap_after_pt: float

class ListingStyleChanges(TypedDict, total=False):
    """Правки ``ListingStyle`` для ``evolve``. Вложенный стиль - словарем правок или готовым объектом."""
    caption: CaptionStyleChanges | CaptionStyle
    font_size_pt: float
    box: bool
    border_sz: int
    border_color: str
    border_padding_pt: int
    fill: str | None
    line_numbers: bool
    line_number_color: str
    highlight: bool
    pygments_style: str
    gap_after_pt: float
    keep_together_lines: int
    edge_lines: int

class FormulaStyleChanges(TypedDict, total=False):
    """Правки ``FormulaStyle`` для ``evolve``."""
    label: str
    number_format: str
    gap_pt: float
    number_width_cm: float
    legend_word: str
    legend_dash: str

class ListStyleChanges(TypedDict, total=False):
    """Правки ``ListStyle`` для ``evolve``."""
    bullet: str
    nested_indent_cm: float
    word_numbering: bool

class NumberingStyleChanges(TypedDict, total=False):
    """Правки ``NumberingStyle`` для ``evolve``. Рисунок 3 (``continuous``) или Рисунок 2.3 (``section``)."""
    scope: NumberScope

class ReportStyleChanges(TypedDict, total=False):
    """Правки ``ReportStyle`` для ``evolve``. Вложенный стиль - словарем правок или готовым объектом. Оформление отчёта. Пресеты - готовые экземпляры (``GOST_732``, ``SUAI``); правки - ``evolve``: MY_STYLE = SUAI.evolve(table={"border_sz": 8}, text={"size_pt": 12}, figure={"caption": {"dash": "-"}})"""
    page: PageStyleChanges | PageStyle
    page_numbers: PageNumberStyleChanges | PageNumberStyle
    text: TextStyleChanges | TextStyle
    headings: HeadingsStyleChanges | HeadingsStyle
    figure: FigureStyleChanges | FigureStyle
    table: TableStyleChanges | TableStyle
    listing: ListingStyleChanges | ListingStyle
    formula: FormulaStyleChanges | FormulaStyle
    lists: ListStyleChanges | ListStyle
    numbering: NumberingStyleChanges | NumberingStyle
    toc_title: str
    toc_placeholder: str
