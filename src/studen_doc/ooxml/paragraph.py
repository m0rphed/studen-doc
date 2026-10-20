"""
Форматирование абзацев: отступы, интервалы, выравнивание, рамка и заливка, пустые «проставки».
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, replace
from typing import Any

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt
from docx.styles.style import ParagraphStyle
from docx.text.paragraph import Paragraph

from studen_doc.ooxml.elements import Container, element, paragraph_xml
from studen_doc.ooxml.schema import PPR_ORDER, insert_ordered
from studen_doc.types import Align

ALIGN: dict[Align, WD_ALIGN_PARAGRAPH] = {
    "left": WD_ALIGN_PARAGRAPH.LEFT,
    "center": WD_ALIGN_PARAGRAPH.CENTER,
    "right": WD_ALIGN_PARAGRAPH.RIGHT,
    "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
}

#: Стороны рамки в порядке, которого требует схема.
BOX_SIDES = ("top", "left", "bottom", "right")


@dataclass(frozen=True, slots=True, kw_only=True)
class ParagraphFormat:
    """
    Параметры абзаца; ``None`` — «не менять». Годится и для абзаца, и для стиля.
    """

    align: Align | None = None
    first_indent_cm: float | None = None
    left_indent_cm: float | None = None
    line_spacing: float | None = None
    before_pt: float | None = None
    after_pt: float | None = None
    keep_next: bool | None = None
    keep_lines: bool | None = None
    page_break_before: bool | None = None


# (поле ParagraphFormat, атрибут ParagraphFormat python-docx, преобразование значения)
_SETTERS: tuple[tuple[str, str, Callable[[Any], Any]], ...] = (
    ("align", "alignment", ALIGN.__getitem__),
    ("first_indent_cm", "first_line_indent", Cm),
    ("left_indent_cm", "left_indent", Cm),
    ("line_spacing", "line_spacing", float),
    ("before_pt", "space_before", Pt),
    ("after_pt", "space_after", Pt),
    ("keep_next", "keep_with_next", bool),
    ("keep_lines", "keep_together", bool),
    ("page_break_before", "page_break_before", bool),
)


def set_style_id(par: Paragraph, style_id: str | None) -> None:
    """
    Стиль абзаца по его id (``None`` - стиль по умолчанию). ``Paragraph.style = имя`` при каждом присваивании
    ищет стиль в документе и стиль по умолчанию для сравнения: в больших документах это главная статья расходов,
    поэтому id берут один раз заранее.
    """
    paragraph_xml(par).get_or_add_pPr().style = style_id


def apply_format(target: Paragraph | ParagraphStyle, fmt: ParagraphFormat) -> None:
    """
    Применяет формат к абзацу или к стилю абзаца.
    """
    paragraph_format = target.paragraph_format
    for field_name, attribute, convert in _SETTERS:
        value = getattr(fmt, field_name)
        if value is not None:
            setattr(paragraph_format, attribute, convert(value))


#: Абзац без абзацного отступа с одинарным интервалом: внутри ячеек, колонтитулов, на титульном листе.
COMPACT = ParagraphFormat(first_indent_cm=0, line_spacing=1.0)

#: То же, но без интервалов до и после абзаца.
COMPACT_TIGHT = ParagraphFormat(first_indent_cm=0, line_spacing=1.0, before_pt=0, after_pt=0)


def set_format(target: Paragraph | ParagraphStyle, *, base: ParagraphFormat | None = None, **fields: Any) -> None:
    """
    Короткая запись: ``set_format(par, align="center", after_pt=6)``.

    ``base`` - готовый формат (например, ``COMPACT``), поверх которого применяются ``fields``.
    """
    apply_format(target, replace(base, **fields) if base is not None else ParagraphFormat(**fields))


def box_paragraph(
    par: Paragraph,
    *,
    border_sz: int,
    color: str,
    space_pt: int,
    fill: str | None,
    sides: Iterable[str] = BOX_SIDES,
) -> None:
    """
    Рамка и заливка абзаца. Подряд идущие абзацы с одинаковой рамкой Word рисует как один блок.
    """
    drawn = set(sides)
    edges = [
        element(
            f"w:{side}",
            {"w:val": "single", "w:sz": border_sz, "w:space": space_pt, "w:color": color}
            if side in drawn
            else {"w:val": "nil"},
        )
        for side in BOX_SIDES
    ]
    properties = paragraph_xml(par).get_or_add_pPr()
    insert_ordered(properties, element("w:pBdr", None, *edges), PPR_ORDER)
    if fill:
        insert_ordered(properties, element("w:shd", {"w:val": "clear", "w:color": "auto", "w:fill": fill}), PPR_ORDER)


def anchor_to_page_bottom(par: Paragraph) -> None:
    """
    Прижимает абзац к нижнему полю страницы и центрирует по ширине текста (рамка ``w:framePr``):
    положение не зависит от того, сколько места заняло предыдущее содержимое.
    """
    frame = element(
        "w:framePr",
        {"w:wrap": "around", "w:vAnchor": "margin", "w:hAnchor": "margin", "w:xAlign": "center", "w:yAlign": "bottom"},
    )
    insert_ordered(paragraph_xml(par).get_or_add_pPr(), frame, PPR_ORDER)


def gap_paragraph(container: Container, height_pt: float) -> Paragraph:
    """
    Пустой абзац точной высоты (вместо «пустых строк»). ``container`` — документ или ячейка.
    """
    par = container.add_paragraph()
    set_format(par, first_indent_cm=0, before_pt=0, after_pt=0)
    par.paragraph_format.line_spacing = Pt(max(height_pt, 1))
    par.add_run("").font.size = Pt(1)
    return par
