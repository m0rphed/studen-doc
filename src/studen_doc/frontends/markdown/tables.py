"""
Таблицы pandoc -> ``Table`` модели.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from studen_doc.errors import MarkdownError
from studen_doc.frontends.markdown.inlines import InlineConverter
from studen_doc.frontends.markdown.options import Options
from studen_doc.frontends.markdown.pandoc_ast import Attr, Node, is_text_block
from studen_doc.model.blocks import Table
from studen_doc.model.inline import ModelInline
from studen_doc.types import Align

#: Выравнивание столбца в pipe-таблице (``:--``, ``:-:``, ``--:``); без двоеточий выравнивание по стилю.
_COLUMN_ALIGN: dict[str, Align] = {"AlignLeft": "left", "AlignCenter": "center", "AlignRight": "right"}

type Cells = tuple[tuple[ModelInline, ...], ...]


class TableConverter:
    """
    Pipe-таблицы Markdown: просто таблица либо ``::: {.table #tbl:x}`` с подписью, меткой и размерами.
    """

    def __init__(self, inlines: InlineConverter) -> None:
        self._inlines = inlines

    def bare(self, parts: Sequence[Any]) -> Table:
        """
        Таблица без обертки: без подписи и метки, не нумеруется.
        """
        return self._table(parts, caption=(), label=None, options=Options())

    def captioned(self, attr: Attr, content: Sequence[Node]) -> Table:
        """
        Содержимое ``::: {.table #tbl:x widths="6,2" font-size=12}``: одна таблица и не больше одного абзаца-подписи
        (до таблицы или после нее).
        """
        tables = [block["c"] for block in content if block["t"] == "Table"]
        captions = [block["c"] for block in content if is_text_block(block)]
        if len(tables) != 1 or len(captions) > 1 or len(tables) + len(captions) != len(content):
            raise MarkdownError("Блок ::: table состоит из одной таблицы и не более чем одного абзаца-подписи")
        caption = self._inlines.convert(captions[0]) if captions else ()
        return self._table(tables[0], caption=caption, label=attr.label, options=attr.options)

    def _table(
        self,
        parts: Sequence[Any],
        *,
        caption: tuple[ModelInline, ...],
        label: str | None,
        options: Options,
    ) -> Table:
        _attr, _caption, columns, head, bodies, foot = parts
        if foot[1]:
            raise MarkdownError("Подвал таблицы (foot) не поддерживается")
        if len(head[1]) != 1:
            raise MarkdownError("У таблицы должна быть ровно одна строка заголовка")
        header = self._row(head[1][0])
        rows: list[Cells] = []
        for _body_attr, row_head_columns, intermediate_head, body_rows in bodies:
            if row_head_columns or intermediate_head:
                raise MarkdownError("Заголовочные столбцы и промежуточные заголовки таблицы не поддерживаются")
            rows.extend(self._row(row) for row in body_rows)
        aligns: tuple[Align | None, ...] = tuple(_COLUMN_ALIGN.get(spec[0]["t"]) for spec in columns)
        return Table(
            header,
            rows,
            caption=caption or None,
            label=label,
            col_widths_cm=options.lengths_cm("widths", count=len(header)),
            align=aligns if any(aligns) else None,
            font_size_pt=options.number("font-size"),
        )

    def _row(self, row: Sequence[Any]) -> Cells:
        _attr, cells = row
        return tuple(self._cell(cell) for cell in cells)

    def _cell(self, cell: Sequence[Any]) -> tuple[ModelInline, ...]:
        _attr, _align, row_span, col_span, blocks = cell
        if row_span != 1 or col_span != 1:
            raise MarkdownError("Объединенные ячейки таблицы не поддерживаются")
        if not blocks:
            return ()
        if len(blocks) > 1 or not is_text_block(blocks[0]):
            raise MarkdownError("В ячейке таблицы допустим один абзац текста")
        return self._inlines.convert(blocks[0]["c"])
