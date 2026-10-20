"""
Полное описание оформления отчёта - композиция неизменяемых тематических стилей.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self, Unpack

from studen_doc.style.components import (
    FigureStyle,
    FormulaStyle,
    ListingStyle,
    ListStyle,
    NumberingStyle,
    PageNumberStyle,
    PageStyle,
    TableStyle,
    TextStyle,
)
from studen_doc.style.evolve import Evolvable, evolve_dataclass
from studen_doc.style.headings import HeadingsStyle

if TYPE_CHECKING:
    from studen_doc.style.changes import ReportStyleChanges


@dataclass(frozen=True, slots=True, kw_only=True)
class ReportStyle(Evolvable):
    """
    Оформление отчёта. Пресеты - готовые экземпляры (``GOST_732``, ``SUAI``); правки - ``evolve``:

        MY_STYLE = SUAI.evolve(table={"border_sz": 8}, text={"size_pt": 12}, figure={"caption": {"dash": "-"}})
    """

    page: PageStyle = PageStyle()
    page_numbers: PageNumberStyle = PageNumberStyle()
    text: TextStyle = TextStyle()
    headings: HeadingsStyle = HeadingsStyle()
    figure: FigureStyle = FigureStyle()
    table: TableStyle = TableStyle()
    listing: ListingStyle = ListingStyle()
    formula: FormulaStyle = FormulaStyle()
    lists: ListStyle = ListStyle()
    numbering: NumberingStyle = NumberingStyle()
    toc_title: str = "Содержание"
    toc_placeholder: str = "Оглавление обновится при открытии: нажмите «Да» (или F9 в Word)."

    def evolve(self, **changes: Unpack[ReportStyleChanges]) -> Self:
        """
        Копия стиля с правками: `style.evolve(table={"border_sz": 8})`. Допустимые имена и типы значений -
        в `ReportStyleChanges` (сгенерирован из полей стиля, IDE подсказывает его ключи).
        """
        return evolve_dataclass(self, **changes)
