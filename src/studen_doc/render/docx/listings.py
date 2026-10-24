"""
Листинги кода: каждая строка - абзац моноширинным шрифтом, подряд идущие абзацы с рамкой Word рисует как один блок.
"""

from __future__ import annotations

from docx.text.paragraph import Paragraph

from studen_doc.ir import RListing
from studen_doc.model.blocks import CodeRun
from studen_doc.ooxml.fonts import apply_font, enabled
from studen_doc.ooxml.paragraph import BOX_SIDES, box_paragraph, gap_paragraph, set_format
from studen_doc.render.docx import names
from studen_doc.render.docx.captions import emit_caption
from studen_doc.render.docx.context import Context
from studen_doc.render.docx.highlight import Span, highlight_lines
from studen_doc.style import ListingStyle

#: Ширина табуляции в листинге: табуляция заменяется пробелами, чтобы отступы не зависели от настроек Word.
TAB_WIDTH = 4


def emit_listing(ctx: Context, node: RListing) -> None:
    style = ctx.style.listing
    if node.caption is not None and node.number is not None:
        emit_caption(ctx, names.LISTING_CAPTION, style.caption, node.number, node.caption)
    if node.runs is not None:
        _emit_styled_lines(ctx, node)
        gap_paragraph(ctx.doc, style.gap_after_pt)
        return
    code = node.code.expandtabs(TAB_WIDTH).strip("\n")
    lines = code.split("\n")
    highlighted = None
    if node.highlight and node.language:
        highlighted = highlight_lines(code, node.language, style.pygments_style)
    digits = len(str(len(lines)))
    for index, line in enumerate(lines, start=1):
        par = ctx.add_paragraph(names.CODE)
        _frame(par, style)
        if _keeps_with_next(index, len(lines), style):
            set_format(par, keep_next=True)
        if node.line_numbers:
            apply_font(par.add_run(f"{index:>{digits}}  "), color=style.line_number_color)
        _add_code(par, line, highlighted[index - 1] if highlighted is not None else None)
    gap_paragraph(ctx.doc, style.gap_after_pt)


def _emit_styled_lines(ctx: Context, node: RListing) -> None:
    """
    Строки листинга с готовыми фрагментами: текст не нормализуется (пустые строки в начале и в конце, пробелы
    и выравнивание остаются как есть), подсветка по языку не применяется.
    """
    style = ctx.style.listing
    lines = node.runs or ()
    digits = len(str(len(lines)))
    for index, line in enumerate(lines, start=1):
        par = ctx.add_paragraph(names.CODE)
        _frame(par, style)
        if _keeps_with_next(index, len(lines), style):
            set_format(par, keep_next=True)
        if node.line_numbers:
            apply_font(par.add_run(f"{index:>{digits}}  "), color=style.line_number_color)
        for run in line:
            _add_run(par, run)


def _add_run(par: Paragraph, run: CodeRun) -> None:
    apply_font(
        par.add_run(run.text),
        color=run.color,
        shade=run.background,
        bold=enabled(run.bold),
        italic=enabled(run.italic),
        underline=enabled(run.underline),
        strike=enabled(run.strike),
    )


def _keeps_with_next(index: int, count: int, style: ListingStyle) -> bool:
    """
    Строка 1..count не отрывается от следующей: короткий листинг не разрывается совсем, у длинного на каждой
    странице остается не меньше ``edge_lines`` строк в начале и в конце (без одиноких строк).
    """
    if index == count:
        return False
    if count <= style.keep_together_lines:
        return True
    return index < style.edge_lines or index >= count - style.edge_lines + 1


def _frame(par: Paragraph, style: ListingStyle) -> None:
    """
    Рамка и заливка строки листинга по стилю (рамка, только заливка или ничего).
    """
    if style.box or style.fill:
        box_paragraph(
            par,
            border_sz=style.border_sz,
            color=style.border_color,
            space_pt=style.border_padding_pt,
            fill=style.fill,
            sides=BOX_SIDES if style.box else (),
        )


def _add_code(par: Paragraph, line: str, spans: list[Span] | None) -> None:
    """
    Текст строки: одним запуском либо цветными фрагментами подсветки синтаксиса.
    """
    if spans is None:
        par.add_run(line)
        return
    for span in spans:
        apply_font(
            par.add_run(span.text),
            color=span.color,
            bold=enabled(span.bold),
            italic=enabled(span.italic),
        )
