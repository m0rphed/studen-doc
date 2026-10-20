"""
Инлайн-узлы -> запуски (runs), формулы и поля внутри абзаца Word.
"""

from __future__ import annotations

from typing import assert_never

from docx.text.paragraph import Paragraph

from studen_doc.ir import Inlines
from studen_doc.model.inline import Code, LineBreak, Math, Ref, Text
from studen_doc.ooxml.fields import FieldRunProps, add_field
from studen_doc.ooxml.fonts import apply_font, enabled
from studen_doc.ooxml.math import append_math
from studen_doc.render.docx.context import Context


def add_inlines(
    par: Paragraph,
    inlines: Inlines,
    ctx: Context,
    *,
    bold: bool = False,
    italic: bool = False,
    size_pt: float | None = None,
) -> None:
    """
    Добавляет узлы в абзац. ``bold``/``italic``/``size_pt`` — базовое оформление (например, заголовок таблицы).
    """
    for node in inlines:
        match node:
            case Text():
                _add_text(par, node, bold, italic, size_pt)
            case Code():
                _add_code(par, node, ctx, bold, italic, size_pt)
            case Math(latex=latex):
                add_math(par, latex, ctx)
            case Ref():
                _add_reference(par, node, ctx, bold, italic)
            case LineBreak():
                par.add_run().add_break()
            case _:
                assert_never(node)


def add_math(par: Paragraph, latex: str, ctx: Context) -> None:
    append_math(par, ctx.math[latex])


def _add_text(par: Paragraph, node: Text, bold: bool, italic: bool, size_pt: float | None) -> None:
    apply_font(
        par.add_run(node.text),
        size_pt=size_pt,
        bold=enabled(node.bold or bold),
        italic=enabled(node.italic or italic),
        script=node.script,
    )


def _add_code(par: Paragraph, node: Code, ctx: Context, bold: bool, italic: bool, size_pt: float | None) -> None:
    """
    Моноширинный фрагмент; размер задан стилем, пока не переопределен (например, в ячейке таблицы).
    """
    text = ctx.style.text
    apply_font(
        par.add_run(node.text),
        name=text.mono_font_name,
        size_pt=text.mono_size_pt if size_pt is None else size_pt,
        bold=enabled(node.bold or bold),
        italic=enabled(node.italic or italic),
    )


def _add_reference(par: Paragraph, node: Ref, ctx: Context, bold: bool, italic: bool) -> None:
    """
    Ссылка на номер: поле REF на закладку подписи.
    """
    number = ctx.labels[node.label]
    flags = FieldRunProps(bold=node.bold or bold, italic=node.italic or italic)
    add_field(par, f"REF {number.bookmark} \\h", number.display, flags)
