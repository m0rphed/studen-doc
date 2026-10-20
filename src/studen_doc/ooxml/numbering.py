"""
Настоящие списки Word: определения нумерации (numbering.xml) и привязка абзацев к спискам.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from docx.document import Document as DocxDocument
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph
from lxml import etree

from studen_doc.ooxml.elements import element, paragraph_xml
from studen_doc.ooxml.schema import NUM_PR_ORDER, PPR_ORDER, ensure_child


@dataclass(frozen=True, slots=True)
class LevelSpec:
    """
    Один уровень многоуровневого списка.
    """

    num_format: str  # decimal | bullet | russianLower | ...
    text: str  # шаблон маркера: «%1)», «%2.», либо сам знак для bullet
    left_twips: int  # отступ абзаца слева (куда возвращаются строки-продолжения)
    first_line_twips: int  # отступ первой строки (где стоит маркер)
    font: str | None = None  # гарнитура знака маркера (для bullet)


def _level_element(index: int, level: LevelSpec) -> etree._Element:
    """
    ``w:lvl``: дети идут в порядке схемы - начало, формат, разделитель, текст маркера, выравнивание, отступы, шрифт.
    """
    children = [
        element("w:start", {"w:val": 1}),
        element("w:numFmt", {"w:val": level.num_format}),
        element("w:suff", {"w:val": "space"}),
        element("w:lvlText", {"w:val": level.text}),
        element("w:lvlJc", {"w:val": "left"}),
        element(
            "w:pPr",
            None,
            element("w:ind", {"w:left": level.left_twips, "w:firstLine": level.first_line_twips}),
        ),
    ]
    if level.font:
        fonts = {"w:ascii": level.font, "w:hAnsi": level.font, "w:cs": level.font, "w:hint": "default"}
        children.append(element("w:rPr", None, element("w:rFonts", fonts)))
    return element("w:lvl", {"w:ilvl": index}, *children)


def add_abstract_num(doc: DocxDocument, levels: Sequence[LevelSpec]) -> int:
    """
    Добавляет определение многоуровневого списка и возвращает его abstractNumId.
    """
    numbering = doc.part.numbering_part.element
    existing = (int(el.get(qn("w:abstractNumId"), "0")) for el in numbering.findall(qn("w:abstractNum")))
    abstract_id = max(existing, default=-1) + 1
    definition = element(
        "w:abstractNum",
        {"w:abstractNumId": abstract_id},
        element("w:multiLevelType", {"w:val": "multilevel"}),
        *(_level_element(index, level) for index, level in enumerate(levels)),
    )
    first_instance = numbering.find(qn("w:num"))
    if first_instance is None:
        numbering.append(definition)
    else:
        first_instance.addprevious(definition)  # по схеме все abstractNum идут до первого num
    return abstract_id


def add_list_instance(doc: DocxDocument, abstract_id: int, *, levels: int) -> int:
    """
    Новый экземпляр списка (numId) с нумерацией, начинающейся с 1 на каждом из ``levels`` уровней.
    """
    numbering = doc.part.numbering_part.element
    existing = (int(el.get(qn("w:numId"), "0")) for el in numbering.findall(qn("w:num")))
    num_id = max(existing, default=0) + 1
    overrides = [
        element("w:lvlOverride", {"w:ilvl": level}, element("w:startOverride", {"w:val": 1}))
        for level in range(levels)
    ]
    instance = element("w:num", {"w:numId": num_id}, element("w:abstractNumId", {"w:val": abstract_id}), *overrides)
    numbering.append(instance)
    return num_id


def attach_to_list(par: Paragraph, num_id: int, level: int) -> None:
    """
    Делает абзац пунктом списка ``num_id`` на уровне ``level`` (0 — верхний).
    """
    membership = ensure_child(paragraph_xml(par).get_or_add_pPr(), "w:numPr", PPR_ORDER)
    ensure_child(membership, "w:ilvl", NUM_PR_ORDER).set(qn("w:val"), str(level))
    ensure_child(membership, "w:numId", NUM_PR_ORDER).set(qn("w:val"), str(num_id))
