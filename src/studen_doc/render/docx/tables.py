"""
Таблицы: подпись сверху, шапка с повтором на страницах, строки без разрывов, числа по стилю.
"""

from __future__ import annotations

from docx.enum.table import WD_ALIGN_VERTICAL
from docx.table import Table, _Cell, _Row

from studen_doc.ir import Inlines, RTable
from studen_doc.model.inline import Text
from studen_doc.ooxml.cell_template import CellCopier, is_plain_text
from studen_doc.ooxml.paragraph import gap_paragraph, set_format, set_style_id
from studen_doc.ooxml.table_format import (
    add_table,
    forbid_row_split,
    repeat_header,
    set_cell_margins,
    set_table_borders,
    shade_cell,
    table_cells,
)
from studen_doc.render.docx import names
from studen_doc.render.docx.captions import emit_caption
from studen_doc.render.docx.context import Context
from studen_doc.render.docx.inline import add_inlines
from studen_doc.style import TableStyle
from studen_doc.types import Align


def emit_table(ctx: Context, node: RTable) -> None:
    style = ctx.style.table
    if node.caption is not None and node.number is not None:
        emit_caption(ctx, names.TABLE_CAPTION, style.caption, node.number, node.caption)
    table = _create(ctx, node, style)
    rows = list(table.rows)
    cells = table_cells(table)
    text_style_id = ctx.doc.styles[names.TABLE_TEXT].style_id
    painter = CellPainter(ctx, text_style_id, node.font_size_pt)
    _fill_header(painter, rows[0], cells[0], node, style)
    _fill_body(painter, rows[1:], cells[1:], node, style)
    gap_paragraph(ctx.doc, style.gap_after_pt)


def _create(ctx: Context, node: RTable, style: TableStyle) -> Table:
    columns = len(node.header)
    table = add_table(
        ctx.doc,
        rows=1 + len(node.rows),
        columns=columns,
        widths_cm=node.col_widths_cm or [ctx.text_width_cm / columns] * columns,
        align=style.align,
        style="Table Grid",
    )
    padding = style.cell_padding
    set_cell_margins(table, top=padding.top, bottom=padding.bottom, left=padding.left, right=padding.right)
    set_table_borders(table, size=style.border_sz)
    return table


def _fill_header(painter: CellPainter, row: _Row, cells: list[_Cell], node: RTable, style: TableStyle) -> None:
    for cell, inlines in zip(cells, node.header, strict=True):
        painter.paint(cell, inlines, style.header_align, bold=style.header_bold)
        if style.header_fill:
            shade_cell(cell, style.header_fill)
    repeat_header(row)


def _fill_body(
    painter: CellPainter, rows: list[_Row], cells: list[list[_Cell]], node: RTable, style: TableStyle
) -> None:
    for row, row_cells, data in zip(rows, cells, node.rows, strict=True):
        forbid_row_split(row)
        for column, (cell, value) in enumerate(zip(row_cells, data, strict=True)):
            align = _cell_align(node.align, column, value.numeric, style)
            painter.paint(cell, value.inlines, align)


def _cell_align(column_aligns: tuple[Align | None, ...] | None, column: int, numeric: bool, style: TableStyle) -> Align:
    """
    Выравнивание ячейки: заданное для столбца, иначе по стилю (числа и текст выравниваются по-разному).
    """
    if column_aligns is not None and (own := column_aligns[column]) is not None:
        return own
    return style.numeric_align if numeric else style.body_align


class CellPainter:
    """
    Оформляет ячейки одной таблицы. Ячейка с обычным текстом (один узел ``Text``, без табуляций и переводов строк) -
    самый частый случай: такие ячейки одного вида копируются с первой (см. ``ooxml.cell_template``), а сложное
    содержимое (ссылки, формулы, переносы) оформляется напрямую.
    """

    def __init__(self, ctx: Context, text_style_id: str, size_pt: float | None) -> None:
        self._ctx = ctx
        self._text_style_id = text_style_id
        self._size_pt = size_pt
        self._copier = CellCopier()

    def paint(self, cell: _Cell, inlines: Inlines, align: Align, *, bold: bool = False) -> None:
        def build() -> None:
            self._build(cell, inlines, align, bold)

        match inlines:
            case (Text(text=text, bold=text_bold, italic=italic, script=script),) if is_plain_text(text):
                self._copier.fill(cell, (align, bold, text_bold, italic, script), text, build)
            case _:
                build()

    def _build(self, cell: _Cell, inlines: Inlines, align: Align, bold: bool) -> None:
        par = cell.paragraphs[0]
        set_style_id(par, self._text_style_id)
        set_format(par, align=align)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        add_inlines(par, inlines, self._ctx, bold=bold, size_pt=self._size_pt)
