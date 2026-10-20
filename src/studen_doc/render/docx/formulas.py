"""
Выключные формулы: формула по центру, номер у правого края, пояснения «где ...» под формулой.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from docx.enum.table import WD_ALIGN_VERTICAL

from studen_doc.ir import Number, RFormula
from studen_doc.ooxml.fields import add_seq_number
from studen_doc.ooxml.math import append_display_math
from studen_doc.ooxml.paragraph import COMPACT, gap_paragraph, set_format
from studen_doc.ooxml.table_format import add_table
from studen_doc.render.docx.context import Context
from studen_doc.render.docx.inline import add_inlines, add_math

if TYPE_CHECKING:
    from lxml import etree


def emit_formula(ctx: Context, node: RFormula) -> None:
    style = ctx.style.formula
    omath = ctx.math[node.latex]
    gap_paragraph(ctx.doc, style.gap_pt)
    if node.number is None:
        par = ctx.doc.add_paragraph()
        set_format(par, base=COMPACT, align="center")
        append_display_math(par, omath)
    else:
        _numbered_formula(ctx, omath, node.number)
    gap_paragraph(ctx.doc, style.gap_pt)
    _legend(ctx, node)


def _numbered_formula(ctx: Context, omath: etree._Element, number: Number) -> None:
    """
    Формула по центру и номер у правого края - двухячеечная таблица без границ.
    """
    style = ctx.style.formula
    table = add_table(
        ctx.doc,
        rows=1,
        columns=2,
        widths_cm=[ctx.text_width_cm - style.number_width_cm, style.number_width_cm],
        align="center",
    )
    formula_cell, number_cell = table.cell(0, 0), table.cell(0, 1)
    for cell in (formula_cell, number_cell):
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    left = formula_cell.paragraphs[0]
    set_format(left, base=COMPACT, align="center")
    append_display_math(left, omath)
    right = number_cell.paragraphs[0]
    set_format(right, base=COMPACT, align="right")
    prefix, _, suffix = style.number_format.partition("{n}")
    if prefix:
        right.add_run(prefix)
    add_seq_number(
        right,
        seq_name=style.label,
        display=number.display,
        bookmark_name=number.bookmark,
        use_seq=number.use_seq,
    )
    if suffix:
        right.add_run(suffix)


def _legend(ctx: Context, node: RFormula) -> None:
    """
    Экспликация под формулой по ГОСТ: "где y - факт; n - размер выборки.".
    """
    style = ctx.style.formula
    for index, (symbol, description) in enumerate(node.where):
        par = ctx.add_paragraph("Normal")
        set_format(par, first_indent_cm=0)
        if index == 0:
            par.add_run(f"{style.legend_word} ")
        add_math(par, symbol, ctx)
        par.add_run(f" {style.legend_dash} ")
        add_inlines(par, description, ctx)
        par.add_run(";" if index < len(node.where) - 1 else ".")
