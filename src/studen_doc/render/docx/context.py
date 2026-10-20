"""
Общий контекст отрисовки одного документа.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from docx.document import Document as DocxDocument
from docx.enum.style import WD_STYLE_TYPE
from docx.text.paragraph import Paragraph

from studen_doc.ir import Number
from studen_doc.ooxml.paragraph import set_style_id
from studen_doc.render.docx.list_numbering import ListNumbering
from studen_doc.style import ReportStyle

if TYPE_CHECKING:
    from lxml import etree


@dataclass(frozen=True, slots=True)
class Context:
    doc: DocxDocument
    style: ReportStyle
    labels: Mapping[str, Number]
    math: Mapping[str, etree._Element]  # LaTeX -> OMML, уже сконвертированные одним вызовом
    lists: ListNumbering                # определения и экземпляры списков Word
    _style_ids: dict[str, str | None] = field(default_factory=dict, init=False, repr=False)

    @property
    def text_width_cm(self) -> float:
        return self.style.page.text_width_cm

    def add_paragraph(self, style: str) -> Paragraph:
        """
        Абзац в конце документа со стилем по имени. Python-docx при каждом ``add_paragraph(style=имя)`` ищет стиль
        в документе (и стиль по умолчанию для сравнения) - несколько миллисекунд на абзац, поэтому идентификатор
        стиля находится один раз.
        """
        paragraph = self.doc.add_paragraph()
        set_style_id(paragraph, self._paragraph_style_id(style))
        return paragraph

    def _paragraph_style_id(self, name: str) -> str | None:
        """
        Идентификатор стиля абзаца; у стиля по умолчанию ``None``: Word применяет его сам, и в абзаце его не пишут.
        """
        if name not in self._style_ids:
            styles = self.doc.styles
            style_id = styles[name].style_id
            default = styles.default(WD_STYLE_TYPE.PARAGRAPH)
            self._style_ids[name] = None if default is not None and style_id == default.style_id else style_id
        return self._style_ids[name]
