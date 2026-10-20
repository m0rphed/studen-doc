"""
Подпись под рисунком, над таблицей и над листингом: «<Метка> N - текст».
"""

from __future__ import annotations

from studen_doc.ir import Inlines, Number
from studen_doc.ooxml.fields import add_seq_number
from studen_doc.render.docx.context import Context
from studen_doc.render.docx.inline import add_inlines
from studen_doc.style import CaptionStyle


def emit_caption(ctx: Context, style_name: str, caption: CaptionStyle, number: Number, text: Inlines | None) -> None:
    """
    Абзац подписи: номер - поле SEQ (или обычный текст) внутри закладки, на которую ссылаются поля REF.
    ``style_name`` - стиль абзаца Word для этого вида подписей.
    """
    par = ctx.add_paragraph(style_name)
    par.add_run(f"{caption.label} ")
    add_seq_number(
        par,
        seq_name=caption.label,
        display=number.display,
        bookmark_name=number.bookmark,
        use_seq=number.use_seq,
    )
    if text:
        par.add_run(f" {caption.dash} ")
        add_inlines(par, text, ctx)
