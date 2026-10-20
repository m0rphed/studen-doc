"""
Формулы OMML внутри абзаца.
"""

from __future__ import annotations

from copy import deepcopy

from docx.text.paragraph import Paragraph
from lxml import etree

from studen_doc.ooxml.elements import element, paragraph_xml


def append_math(par: Paragraph, omath: etree._Element) -> None:
    """
    Строчная формула (``m:oMath``) в конце абзаца. Вставляется копия: один и тот же элемент нельзя
    поместить в документ дважды, а формула может встречаться много раз.
    """
    paragraph_xml(par).append(deepcopy(omath))


def append_display_math(par: Paragraph, omath: etree._Element) -> None:
    """
    Выключная формула (``m:oMathPara``) в конце абзаца: отдельной строкой по центру, как в Word.
    """
    paragraph_xml(par).append(element("m:oMathPara", None, deepcopy(omath)))
