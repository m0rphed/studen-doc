"""
Построение и доступ к XML-элементам WordprocessingML.

Всё, что работает с lxml напрямую, живет в пакете ``ooxml``. Остальной код получает элементы из функций
этого модуля и не обращается к приватным атрибутам python-docx (``_p``, ``_tc``, ``_tbl``...).
"""

from __future__ import annotations

from collections.abc import Mapping

from docx.document import Document as DocxDocument
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.oxml.table import CT_Row, CT_Tbl, CT_Tc
from docx.oxml.text.paragraph import CT_P
from docx.oxml.text.run import CT_R
from docx.table import Table, _Cell, _Row
from docx.text.paragraph import Paragraph
from docx.text.run import Run
from lxml import etree

#: Всё, куда можно добавлять абзацы и таблицы: документ или ячейка таблицы.
type Container = DocxDocument | _Cell
#: Атрибуты элемента: имя с префиксом пространства имен (``"w:val"``) -> значение.
type Attributes = Mapping[str, str | int]


def element(
    tag: str,
    attrs: Attributes | None = None,
    *children: etree._Element,
    text: str | None = None,
) -> etree._Element:
    """
    Создает элемент вместе с атрибутами, вложенными элементами и текстом:

        element("w:top", {"w:val": "single", "w:sz": 4})
        element("w:rPr", None, element("w:b"), element("w:i"))
    """
    node = OxmlElement(tag)
    for name, value in (attrs or {}).items():
        node.set(qn(name), str(value))
    for child in children:
        node.append(child)
    if text is not None:
        node.text = text
    return node


# python-docx не дает общего публичного способа получить XML-элемент объекта: у каждого класса оно свое.
# Единственное место с приватным доступом - эти функции.
def paragraph_xml(paragraph: Paragraph) -> CT_P:
    return paragraph._p


def run_xml(run: Run) -> CT_R:
    return run._r


def table_xml(table: Table) -> CT_Tbl:
    return table._tbl


def row_xml(row: _Row) -> CT_Row:
    return row._tr


def cell_xml(cell: _Cell) -> CT_Tc:
    return cell._tc
