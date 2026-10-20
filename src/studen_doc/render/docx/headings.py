"""
Заголовки разделов, приложений и оглавление.
"""

from __future__ import annotations

from docx.text.paragraph import Paragraph

from studen_doc.ir import RAppendixHeading, RHeading, RToc
from studen_doc.ooxml.fields import add_field
from studen_doc.ooxml.fonts import apply_font
from studen_doc.ooxml.paragraph import set_format
from studen_doc.render.docx.context import Context
from studen_doc.render.docx.paragraphs import emit_page_break
from studen_doc.style import HeadingStyle


def _heading_paragraph(
    ctx: Context,
    text: str,
    heading: HeadingStyle,
    *,
    word_style: str,
    page_break: bool | None,
) -> Paragraph:
    """
    Абзац заголовка по стилю заголовка. ``word_style`` - имя стиля Word: от него зависит,
    попадет ли абзац в оглавление (заголовки Heading N попадают, Normal - нет).
    """
    par = ctx.add_paragraph(word_style)
    set_format(
        par,
        align=heading.align,
        first_indent_cm=heading.first_indent_cm,
        line_spacing=heading.line_spacing,
        before_pt=heading.before_pt,
        after_pt=heading.after_pt,
        keep_next=heading.keep_with_next,
        page_break_before=page_break,
    )
    apply_font(
        par.add_run(text),
        name=ctx.style.text.font_name,
        size_pt=heading.size_pt,
        bold=heading.bold,
        italic=heading.italic,
    )
    return par


def emit_heading(ctx: Context, node: RHeading) -> None:
    headings = ctx.style.headings
    heading = headings.structural if node.structural else headings.for_level(node.level)
    text = node.title.upper() if heading.caps else node.title
    if node.number:
        text = f"{node.number}{headings.number_separator}{text}"
    page_break = heading.page_break_before if node.page_break is None else node.page_break
    _heading_paragraph(ctx, text, heading, word_style=f"Heading {min(node.level, 3)}", page_break=page_break)


def emit_appendix_heading(ctx: Context, node: RAppendixHeading) -> None:
    """
    Заголовок приложения по центру: строка «ПРИЛОЖЕНИЕ А», затем (необязательно) статус и название.
    """
    headings = ctx.style.headings
    structural = headings.structural
    gap = headings.appendix_gap_pt
    par = ctx.add_paragraph("Heading 1")
    set_format(
        par,
        align="center",
        first_indent_cm=0,
        before_pt=structural.before_pt,
        after_pt=gap,
        page_break_before=True if node.page_break is None else node.page_break,
    )
    apply_font(par.add_run(f"{headings.appendix_word} {node.letter}"), bold=structural.bold, caps=False)
    if node.status:
        status = ctx.doc.add_paragraph()
        set_format(status, align="center", first_indent_cm=0, after_pt=gap, keep_next=True)
        status.add_run(f"({node.status})")
    if node.title:
        title = ctx.doc.add_paragraph()
        set_format(
            title,
            align="center",
            first_indent_cm=0,
            after_pt=structural.after_pt,
            keep_next=True,
        )
        apply_font(title.add_run(node.title), bold=structural.bold)


def emit_toc(ctx: Context, node: RToc) -> None:
    structural = ctx.style.headings.structural
    title = node.title.upper() if structural.caps else node.title
    _heading_paragraph(ctx, title, structural, word_style="Normal", page_break=None)
    field_par = ctx.doc.add_paragraph()
    set_format(field_par, align="left", first_indent_cm=0)
    add_field(field_par, f'TOC \\o "1-{node.levels}" \\h \\z \\u', ctx.style.toc_placeholder)
    if node.page_break_after:
        emit_page_break(ctx)
