"""
Шрифты: гарнитура для всех скриптов, размер, начертание, цвет - для запусков (run) и стилей.
"""

from __future__ import annotations

from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor
from docx.styles.style import CharacterStyle
from docx.text.run import Run
from lxml import etree

from studen_doc.ooxml.elements import element, run_xml
from studen_doc.ooxml.schema import STYLE_ORDER, ensure_child

_THEME_ATTRS = ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme")
_SCRIPT_ATTRS = ("ascii", "hAnsi", "eastAsia", "cs")


def set_rfonts(rpr: etree._Element, name: str) -> None:
    """
    Явно задает гарнитуру для всех скриптов (латиница, кириллица, восточные, сложные) и убирает привязку к темам.
    """
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = element("w:rFonts")
        rpr.insert(0, rfonts)
    for attribute in _THEME_ATTRS:
        if (key := qn(f"w:{attribute}")) in rfonts.attrib:
            del rfonts.attrib[key]
    for attribute in _SCRIPT_ATTRS:
        rfonts.set(qn(f"w:{attribute}"), name)


def enabled(flag: bool) -> bool | None:
    """
    Значение для ``bold`` и ``italic`` в ``apply_font``: ``True`` у включенного флага, иначе ``None``
    («не менять»): так в XML не появляется лишнее явное «не полужирный».
    """
    return True if flag else None


def _run_properties(target: Run | CharacterStyle) -> etree._Element:
    """
    ``w:rPr`` запуска или стиля (создается, если его еще нет).
    """
    if isinstance(target, Run):
        return run_xml(target).get_or_add_rPr()
    return ensure_child(target.element, "w:rPr", STYLE_ORDER)


def apply_font(
    target: Run | CharacterStyle,
    *,
    name: str | None = None,
    size_pt: float | None = None,
    bold: bool | None = None,
    italic: bool | None = None,
    underline: bool | None = None,
    caps: bool | None = None,
    color: str | None = None,
    script: str | None = None,
) -> None:
    """
    Применяет шрифт к запуску или к стилю; ``None`` - «не менять». ``script``: "sup" (надстрочный) или "sub".
    """
    font = target.font
    if script is not None:
        font.superscript = script == "sup"
        font.subscript = script == "sub"
    if name is not None:
        set_rfonts(_run_properties(target), name)
    if size_pt is not None:
        font.size = Pt(size_pt)
    if bold is not None:
        font.bold = bold
    if italic is not None:
        font.italic = italic
    if underline is not None:
        font.underline = underline
    if caps is not None:
        font.all_caps = caps
    if color is not None:
        font.color.rgb = RGBColor.from_string(color)
