"""
Отпечаток структуры .docx для «золотых» тестов: стили, тексты, поля, форматирование абзацев.
"""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

M = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"


def _pt(length) -> float | None:
    return None if length is None else round(length.pt, 2)


def _paragraph(par: Paragraph) -> dict:
    fmt = par.paragraph_format
    el = par._p
    return {
        "style": par.style.name,
        "text": par.text,
        "align": None if par.alignment is None else int(par.alignment),
        "first": _pt(fmt.first_line_indent),
        "left": _pt(fmt.left_indent),
        "before": _pt(fmt.space_before),
        "after": _pt(fmt.space_after),
        "keep_next": fmt.keep_with_next,
        "page_break_before": fmt.page_break_before,
        "fields": [i.text.strip().split(" ")[0] for i in el.iter(qn("w:instrText"))],
        "math": len(list(el.iter(M + "oMath"))),
        "images": len(list(el.iter(qn("w:drawing")))),
        "bookmarks": len(list(el.iter(qn("w:bookmarkStart")))),
        "breaks": len([b for b in el.iter(qn("w:br")) if b.get(qn("w:type")) == "page"]),
    }


def fingerprint(path: str | Path) -> dict:
    doc = Document(str(path))
    body: list[dict] = []
    for child in doc.element.body.iterchildren():
        if child.tag == qn("w:p"):
            body.append(_paragraph(Paragraph(child, doc)))
        elif child.tag == qn("w:tbl"):
            table = Table(child, doc)
            body.append(
                {
                    "table": [len(table.rows), len(table.columns)],
                    "cells": [[c.text for c in row.cells] for row in table.rows],
                    "math": len(list(child.iter(M + "oMath"))),
                }
            )
    sec = doc.sections[0]
    return {
        "body": body,
        "page": [
            round(sec.page_width.mm),
            round(sec.page_height.mm),
            round(sec.left_margin.mm),
            round(sec.right_margin.mm),
            round(sec.top_margin.mm),
            round(sec.bottom_margin.mm),
        ],
        "different_first_page": sec.different_first_page_header_footer,
        "footer": [_paragraph(p) for p in sec.footer.paragraphs],
        "update_fields": doc.settings.element.find(qn("w:updateFields")) is not None,
        "normal": [doc.styles["Normal"].font.name, _pt(doc.styles["Normal"].font.size)],
    }
