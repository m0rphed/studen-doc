"""
Рисунки: картинка по центру и подпись под ней.
"""

from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

from docx.image.image import Image as DocxImage
from docx.shared import Cm

from studen_doc.ir import RFigure
from studen_doc.model.blocks import ImageSource
from studen_doc.render.docx import names
from studen_doc.render.docx.captions import emit_caption
from studen_doc.render.docx.context import Context


def emit_figure(ctx: Context, node: RFigure) -> None:
    style = ctx.style.figure
    wanted = node.width_cm if node.width_cm is not None else ctx.text_width_cm * style.width_fraction
    par = ctx.add_paragraph(names.FIGURE)
    source = _image_argument(node.source)
    width = _fit_width(source, min(wanted, ctx.text_width_cm), style.max_height_cm)
    par.add_run().add_picture(source, width=Cm(width))
    emit_caption(ctx, names.FIGURE_CAPTION, style.caption, node.number, node.caption)


def _image_argument(source: ImageSource) -> str | BinaryIO:
    """
    python-docx принимает путь строкой или файловый объект.
    """
    return str(source) if isinstance(source, str | Path) else source


def _fit_width(source: str | BinaryIO, width_cm: float, max_height_cm: float) -> float:
    """
    Уменьшает ширину, если картинка при такой ширине выше допустимого.
    """
    if not isinstance(source, str):
        source.seek(0)  # поток мог быть прочитан раньше (повторная сборка отчета)
    image = DocxImage.from_file(source)
    if not isinstance(source, str):
        source.seek(0)  # поток нужен python-docx с начала
    height = width_cm * image.px_height / image.px_width
    return width_cm * min(1.0, max_height_cm / height)
