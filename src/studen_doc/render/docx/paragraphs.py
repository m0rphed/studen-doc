"""
Абзацы основного текста и разрыв страницы.
"""

from __future__ import annotations

from docx.enum.text import WD_BREAK

from studen_doc.ir import RParagraph
from studen_doc.ooxml.paragraph import COMPACT_TIGHT, set_format
from studen_doc.render.docx.context import Context
from studen_doc.render.docx.inline import add_inlines


def emit_paragraph(ctx: Context, node: RParagraph) -> None:
    par = ctx.add_paragraph("Normal")
    set_format(
        par,
        align=node.align,
        first_indent_cm=None if node.indent else 0,
        keep_next=True if node.keep_with_next else None,
    )
    add_inlines(par, node.inlines, ctx)


def emit_page_break(ctx: Context) -> None:
    """
    Принудительный разрыв страницы: отдельный абзац без интервалов.
    """
    par = ctx.doc.add_paragraph()
    set_format(par, base=COMPACT_TIGHT)
    par.add_run().add_break(WD_BREAK.PAGE)
