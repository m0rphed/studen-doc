"""
Списки: настоящие списки Word (по умолчанию) либо старый формат с маркерами в тексте пунктов.
"""

from __future__ import annotations

from studen_doc.ir import ListMarker, RList, RListItem, RSources
from studen_doc.ooxml.numbering import attach_to_list
from studen_doc.ooxml.paragraph import set_format
from studen_doc.render.docx.context import Context
from studen_doc.render.docx.inline import add_inlines
from studen_doc.render.docx.list_numbering import LEVELS, marker_text, uses_word_numbering


def emit_list(ctx: Context, node: RList) -> None:
    """
    Настоящий список Word (по умолчанию) либо статические маркеры в тексте (``lists.word_numbering=False``).
    """
    if ctx.style.lists.word_numbering and uses_word_numbering(node.marker, node.items):
        _emit_word_list(ctx, node.items, ctx.lists.new_instance(node.marker), level=0)
    else:
        _emit_static_list(ctx, node.items, node.marker, level=0)


def emit_sources(ctx: Context, node: RSources) -> None:
    """
    Список использованных источников (ГОСТ 7.32, 6.16): нумерация арабскими цифрами с точкой, абзацный отступ.
    """
    emit_list(ctx, RList(tuple(RListItem(entry) for entry in node.entries), "1."))


def _emit_word_list(ctx: Context, items: tuple[RListItem, ...], num_id: int, level: int) -> None:
    """
    Настоящий список Word: маркеры и номера рисует Word, в Word список можно редактировать.
    """
    for item in items:
        par = ctx.add_paragraph("Normal")
        attach_to_list(par, num_id, min(level, LEVELS - 1))
        add_inlines(par, item.inlines, ctx)
        _emit_word_list(ctx, item.children, num_id, level + 1)


def _emit_static_list(ctx: Context, items: tuple[RListItem, ...], marker: ListMarker, level: int) -> None:
    """
    Старый формат: маркер - часть текста пункта, отступы заданы у абзаца напрямую.
    """
    text, lists = ctx.style.text, ctx.style.lists
    for index, item in enumerate(items, start=1):
        par = ctx.add_paragraph("Normal")
        set_format(
            par,
            first_indent_cm=text.first_indent_cm,
            left_indent_cm=lists.nested_indent_cm * level,
        )
        par.add_run(marker_text(marker, index, level, lists.bullet))
        add_inlines(par, item.inlines, ctx)
        _emit_static_list(ctx, item.children, marker, level + 1)
