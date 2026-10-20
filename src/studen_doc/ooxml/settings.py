"""
Настройки документа: поля при открытии, режим совместимости, язык.
"""

from __future__ import annotations

from docx.document import Document as DocxDocument
from docx.oxml.ns import qn
from lxml import etree

from studen_doc.ooxml.elements import element
from studen_doc.ooxml.schema import SETTINGS_ORDER, ensure_child

_WORD_URI = "http://schemas.microsoft.com/office/word"
_COMPATIBILITY_MODE_WORD_2013 = "15"


def enable_update_fields(doc: DocxDocument) -> None:
    """
    Word предложит обновить поля (оглавление, номера страниц) при открытии.
    """
    updater = ensure_child(doc.settings.element, "w:updateFields", SETTINGS_ORDER)
    updater.set(qn("w:val"), "true")


def set_compat_mode_15(doc: DocxDocument) -> None:
    """
    Без этого Word показывает «режим совместимости» (15 - формат Word 2013 и новее).
    """
    compat = ensure_child(doc.settings.element, "w:compat", SETTINGS_ORDER)
    for setting in compat.findall(qn("w:compatSetting")):
        if setting.get(qn("w:name")) == "compatibilityMode":
            setting.set(qn("w:val"), _COMPATIBILITY_MODE_WORD_2013)
            return
    compat.append(
        element(
            "w:compatSetting",
            {"w:name": "compatibilityMode", "w:uri": _WORD_URI, "w:val": _COMPATIBILITY_MODE_WORD_2013},
        )
    )


def set_language(rpr: etree._Element, language: str) -> None:
    """
    Язык текста (проверка орфографии) для свойств запуска ``w:rPr``: обычный, восточный и справа налево.
    """
    lang = rpr.find(qn("w:lang"))
    if lang is None:
        lang = element("w:lang")
        rpr.append(lang)
    for attribute in ("val", "eastAsia", "bidi"):
        lang.set(qn(f"w:{attribute}"), language)
