"""
Стили документа: шрифт и язык по умолчанию.
"""

from __future__ import annotations

from docx.document import Document as DocxDocument
from docx.oxml.ns import qn

from studen_doc.ooxml.fonts import set_rfonts
from studen_doc.ooxml.settings import set_language


def set_document_defaults(doc: DocxDocument, *, font_name: str, language: str) -> None:
    """
    Шрифт и язык документа по умолчанию (``w:docDefaults``): без этого таблицы и поля берут тему Cambria/Calibri.
    """
    defaults = doc.styles.element.find(f"{qn('w:docDefaults')}/{qn('w:rPrDefault')}/{qn('w:rPr')}")
    if defaults is None:
        return
    set_rfonts(defaults, font_name)
    set_language(defaults, language)
