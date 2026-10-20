"""
Быстрое заполнение однотипных ячеек.

Оформить ячейку через python-docx (стиль абзаца, выравнивание, шрифт, вертикальное выравнивание) - около
миллисекунды: каждая операция ищет место для нового элемента среди соседей. В таблице из тысяч строк почти все
ячейки отличаются только текстом, поэтому первую ячейку каждого вида оформляют обычным путем, а остальные
получают копию ее XML с подставленным текстом. Результат побайтово тот же.
"""

from __future__ import annotations

import copy
from collections.abc import Callable, Hashable
from dataclasses import dataclass

from docx.oxml.ns import qn
from docx.table import _Cell
from lxml import etree

from studen_doc.ooxml.elements import cell_xml

_XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"

#: Имена элементов с пространством имен: ``qn`` на каждую ячейку заметно тормозит, поэтому считаются один раз.
_PARAGRAPH = qn("w:p")
_RUN = qn("w:r")
_RUN_PROPERTIES = qn("w:rPr")
_TEXT = qn("w:t")
_CELL_PROPERTIES = qn("w:tcPr")
_CELL_WIDTH = qn("w:tcW")
_VERTICAL_ALIGNMENT = qn("w:vAlign")

#: Свойства ячейки до и после оформления: ширина (ее задает ``set_table_widths``) и вертикальное выравнивание.
_PLAIN_PROPERTIES = [_CELL_WIDTH]
_PAINTED_PROPERTIES = [_CELL_WIDTH, _VERTICAL_ALIGNMENT]


def is_plain_text(text: str) -> bool:
    """
    Текст без табуляций, переводов строк и других управляющих символов: python-docx превращает их в отдельные
    элементы (``w:tab``, ``w:br``), и копии шаблона с одним ``w:t`` уже не подойдут.
    """
    return all(char >= " " for char in text)


@dataclass(frozen=True, slots=True)
class _Template:
    paragraph: etree._Element  # абзац с одним запуском и одним w:t
    vertical_alignment: etree._Element


class CellCopier:
    """
    Заполняет ячейки с одним абзацем из одного запуска текста; ``key`` описывает оформление (выравнивание,
    шрифт, размер): ячейки с одинаковым ключом оформляются одинаково и отличаются только текстом.
    """

    def __init__(self) -> None:
        self._templates: dict[Hashable, _Template | None] = {}

    def fill(self, cell: _Cell, key: Hashable, text: str, build: Callable[[], None]) -> None:
        """
        Копирует шаблон ячейки с таким ключом; если его еще нет (или ячейка нестандартная), вызывает ``build`` -
        обычное оформление - и запоминает результат как шаблон.
        """
        tc = cell_xml(cell)
        template = self._templates.get(key)
        if template is not None and _tags(tc.find(_CELL_PROPERTIES)) == _PLAIN_PROPERTIES:
            _copy_into(tc, template, text)
            return
        build()
        if key not in self._templates:
            self._templates[key] = _capture(tc)


def _tags(properties: etree._Element | None) -> list[str]:
    return [] if properties is None else [child.tag for child in properties]


def _capture(tc: etree._Element) -> _Template | None:
    """
    Шаблон из оформленной ячейки; ``None``, если ячейка устроена сложнее, чем ожидается.
    """
    paragraphs = tc.findall(_PARAGRAPH)
    properties = tc.find(_CELL_PROPERTIES)
    if len(paragraphs) != 1 or _tags(properties) != _PAINTED_PROPERTIES or properties is None:
        return None
    (paragraph,) = paragraphs
    runs = paragraph.findall(_RUN)
    if len(runs) != 1 or len(runs[0].findall(_TEXT)) != 1:
        return None
    if [child.tag for child in runs[0] if child.tag not in (_RUN_PROPERTIES, _TEXT)]:
        return None
    vertical = properties.find(_VERTICAL_ALIGNMENT)
    if vertical is None:
        return None
    return _Template(copy.deepcopy(paragraph), copy.deepcopy(vertical))


def _copy_into(tc: etree._Element, template: _Template, text: str) -> None:
    paragraph = copy.deepcopy(template.paragraph)
    run_text = paragraph.find(f".//{_TEXT}")
    assert run_text is not None  # шаблон проверен в _capture
    run_text.text = text
    if text.strip() != text:
        run_text.set(_XML_SPACE, "preserve")
    elif _XML_SPACE in run_text.attrib:
        del run_text.attrib[_XML_SPACE]
    old = tc.find(_PARAGRAPH)
    assert old is not None
    tc.replace(old, paragraph)
    properties = tc.find(_CELL_PROPERTIES)
    assert properties is not None
    properties.append(copy.deepcopy(template.vertical_alignment))
