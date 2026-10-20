"""
Фабрика оформления по ГОСТ 7.32: частые настройки одним вызовом, производные значения считаются в одном месте.
"""

from __future__ import annotations

from studen_doc.style.changes import CaptionStyleChanges, PageStyleChanges, ReportStyleChanges, TextStyleChanges
from studen_doc.style.report_style import ReportStyle


def gost_732(
    *,
    font_name: str | None = None,
    font_size_pt: float | None = None,
    mono_font_name: str | None = None,
    line_spacing: float | None = None,
    first_indent_cm: float | None = None,
    margins_mm: tuple[float, float, float, float] | None = None,
) -> ReportStyle:
    """
    Оформление по ГОСТ 7.32-2017; незаданные параметры остаются значениями по умолчанию.

    ``font_size_pt`` задает размер основного текста и подписей (рисунков, таблиц, листингов).
    ``margins_mm`` - поля (слева, справа, сверху, снизу).
    Результат - обычный ``ReportStyle``, дальше его можно уточнять через ``evolve``.
    """
    changes: ReportStyleChanges = {}
    text: TextStyleChanges = {}
    if font_name is not None:
        text["font_name"] = font_name
    if font_size_pt is not None:
        text["size_pt"] = font_size_pt
    if mono_font_name is not None:
        text["mono_font_name"] = mono_font_name
    if line_spacing is not None:
        text["line_spacing"] = line_spacing
    if first_indent_cm is not None:
        text["first_indent_cm"] = first_indent_cm
    if text:
        changes["text"] = text
    if font_size_pt is not None:
        caption: CaptionStyleChanges = {"size_pt": font_size_pt}
        changes["figure"] = {"caption": caption}
        changes["table"] = {"caption": caption}
        changes["listing"] = {"caption": caption}
    if margins_mm is not None:
        left, right, top, bottom = margins_mm
        page: PageStyleChanges = {
            "margin_left_mm": left,
            "margin_right_mm": right,
            "margin_top_mm": top,
            "margin_bottom_mm": bottom,
        }
        changes["page"] = page
    return ReportStyle().evolve(**changes)
