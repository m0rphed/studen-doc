"""
Поля Word (SEQ, REF, PAGE, TOC) и закладки.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Literal, TypedDict

from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph
from lxml import etree

from studen_doc.ooxml.elements import element, paragraph_xml


class FieldRunProps(TypedDict, total=False):
    """
    Начертание результата поля.
    """

    bold: bool
    italic: bool


def _field_char(kind: Literal["begin", "separate", "end"]) -> etree._Element:
    return element("w:r", None, element("w:fldChar", {"w:fldCharType": kind}))


def add_field(par: Paragraph, instruction: str, cached: str, props: FieldRunProps | None = None) -> None:
    """
    Сложное поле: начало, инструкция, разделитель, результат, конец. ``cached`` - результат, который Word
    показывает до обновления поля.
    """
    result_children = [element("w:t", {"xml:space": "preserve"}, text=cached)]
    if props is not None:  # начертание результата: полужирный и курсив, в порядке ``b``, ``i`` по схеме
        flags = [element("w:b")] if props.get("bold") else []
        flags += [element("w:i")] if props.get("italic") else []
        result_children.insert(0, element("w:rPr", None, *flags))
    instruction_run = element("w:r", None, element("w:instrText", {"xml:space": "preserve"}, text=f" {instruction} "))
    paragraph_xml(par).extend(
        [
            _field_char("begin"),
            instruction_run,
            _field_char("separate"),
            element("w:r", None, *result_children),
            _field_char("end"),
        ]
    )


def _next_bookmark_id(par: Paragraph) -> int:
    root = paragraph_xml(par).getroottree().getroot()
    ids = (int(el.get(qn("w:id"), "0")) for el in root.iter(qn("w:bookmarkStart")))
    return max(ids, default=0) + 1


@contextmanager
def bookmark(par: Paragraph, name: str) -> Iterator[None]:
    """
    Всё, что добавлено в абзац внутри ``with``, оказывается внутри закладки ``name``.
    """
    bookmark_id = _next_bookmark_id(par)
    paragraph = paragraph_xml(par)
    paragraph.append(element("w:bookmarkStart", {"w:id": bookmark_id, "w:name": name}))
    try:
        yield
    finally:
        paragraph.append(element("w:bookmarkEnd", {"w:id": bookmark_id}))


def add_seq_number(par: Paragraph, *, seq_name: str, display: str, bookmark_name: str, use_seq: bool) -> None:
    """
    Номер подписи внутри закладки (на нее ссылаются поля REF): поле SEQ при сквозной нумерации
    либо обычный текст (нумерация по разделам, приложения).
    """
    with bookmark(par, bookmark_name):
        if use_seq:
            add_field(par, f"SEQ {seq_name} \\* ARABIC", display)
        else:
            par.add_run(display)
