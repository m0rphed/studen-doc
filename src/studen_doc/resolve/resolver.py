"""
Обход модели отчета: блоки -> узлы IR с номерами, закладками и разобранным текстом.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator, Sequence
from typing import assert_never

from studen_doc.errors import BibliographyError, ResolveError
from studen_doc.ir import (
    Inlines,
    Number,
    NumberKind,
    RAppendixHeading,
    RCell,
    ResolvedReport,
    RFigure,
    RFormula,
    RHeading,
    RList,
    RListing,
    RListItem,
    RNode,
    RPageBreak,
    RParagraph,
    RSources,
    RTable,
    RToc,
)
from studen_doc.model.bibliography import SourceFormatter
from studen_doc.model.blocks import (
    Block,
    Bullets,
    Figure,
    Formula,
    ListEntry,
    Listing,
    ListItem,
    Numbered,
    P,
    PageBreak,
    Source,
    Sources,
    Subsection,
    Table,
    normalize_marker,
)
from studen_doc.model.inline import (
    BlockRef,
    Cite,
    Inline,
    InlineParser,
    Math,
    ModelInline,
    Ref,
    RichText,
    Text,
    as_inlines,
    is_rich_text,
    plain_text,
)
from studen_doc.model.report import Report, Section, Toc
from studen_doc.resolve.counters import NumberAllocator, SectionContext, SectionNumbering
from studen_doc.resolve.labels import Labeled, LabelRegistry
from studen_doc.resolve.sources import SourceRegistry
from studen_doc.style import ReportStyle

#: Ячейка таблицы с числом: ее выравнивают как число (``1``, ``-2,5``, ``1 000,5``, ``1e-5``, ``45 %``).
#: Номера и даты (``1.2.3``, ``12-34``, ``2024-05-01``) числами не считаются; выравнивание столбца можно
#: задать явно через ``Table(align=...)``.
_NUMERIC_CELL = re.compile(r"^[+\-\u2212]?\d+(?:[ \u00a0]\d{3})*(?:[.,]\d+)?(?:[eE][+\-\u2212]?\d+)?(?:[ \u00a0]?%)?$")

type Markup = Callable[[str], tuple[ModelInline, ...]]


def resolve_report(
    report: Report,
    inline_parser: InlineParser | None = None,
    source_formatter: SourceFormatter | None = None,
) -> ResolvedReport:
    """
    Модель -> IR. Строки ``Md`` разбираются одним вызовом ``inline_parser``: первый проход их только
    собирает, второй - подставляет разобранные узлы. Без ``Md`` проход один и ``inline_parser`` не нужен.

    Описания источников из библиографии оформляет ``source_formatter`` (один вызов на документ); без записей,
    которых нет в ``Sources(entries=...)``, он не нужен.
    """
    pending: list[str] = []

    def collect(source: str) -> tuple[ModelInline, ...]:
        pending.append(source)
        return (Text(source),)

    resolver, nodes = _run(report, collect)
    if pending:
        if inline_parser is None:
            raise ResolveError("В отчете есть Md, но не задан inline_parser: используйте Report.resolve()")
        resolver, nodes = _run(report, inline_parser(pending).__getitem__)
    resolver.labels.check()  # после разбора Md: ссылки внутри них тоже проверяются
    return ResolvedReport(
        style=report.style,
        nodes=_with_sources(resolver.sources, nodes, source_formatter),
        labels=resolver.labels.labels(),
        title_page=report.title_page,
        title=report.title,
        author=report.author,
        formulas=resolver.formulas,
    )


def _with_sources(
    registry: SourceRegistry,
    nodes: tuple[RNode, ...],
    source_formatter: SourceFormatter | None,
) -> tuple[RNode, ...]:
    """
    Подставляет в список источников готовые записи: их порядок известен только после прохода по всему тексту.
    """
    if not registry.has_list:
        if registry.has_citations:
            raise BibliographyError("В тексте есть ссылки на источники, а списка нет: добавьте блок Sources")
        return nodes
    keys = registry.requested_keys()
    if keys and source_formatter is None:
        raise BibliographyError(
            f"Источники {keys} не записаны вручную, а библиографии нет: задайте Report.bibliography "
            "(в Markdown - bibliography: в метаданных)"
        )
    formatted = source_formatter(keys) if keys and source_formatter is not None else {}
    entries = registry.entries(formatted)
    return tuple(RSources(entries) if isinstance(node, RSources) else node for node in nodes)


def _run(report: Report, markup: Markup) -> tuple[Resolver, tuple[RNode, ...]]:
    resolver = Resolver(report.style, markup)
    return resolver, tuple(resolver.items(report.items))


class Resolver:
    """
    Один проход по отчету: накапливает счетчики, метки и формулы, а наружу отдает неизменяемые узлы IR.
    """

    def __init__(self, style: ReportStyle, markup: Markup) -> None:
        self._style = style
        self._markup = markup
        self._sections = SectionNumbering()
        self._numbers = NumberAllocator(style.numbering.scope)
        self._formulas: dict[str, None] = {}  # LaTeX без повторов в порядке появления (упорядоченное множество)
        self.labels = LabelRegistry()
        self.sources = SourceRegistry()

    @property
    def formulas(self) -> tuple[str, ...]:
        """
        Все формулы LaTeX документа без повторов, в порядке появления: выключные, пояснения «где...» и строчные.
        """
        return tuple(self._formulas)

    # ---------------------------------------------------------------------------- верхний уровень
    def items(self, items: Sequence[Section | Toc]) -> Iterator[RNode]:
        for item in items:
            match item:
                case Toc(title=title, levels=levels, page_break_after=page_break):
                    yield RToc(title or self._style.toc_title, levels, page_break)
                case Section():
                    yield from self._section(item)

    def _section(self, section: Section) -> Iterator[RNode]:
        rule_name = section.rule_name
        rule = self._style.headings.rule_for(rule_name)
        context = self._sections.open(appendix=rule.appendix, numbered=rule.numbered)
        self._numbers.start_section()
        if rule.appendix:
            assert context.number is not None
            own_title = None if section.title == rule_name else section.title
            yield RAppendixHeading(context.number, own_title, section.status, rule.page_break_before)
        else:
            yield RHeading(1, section.title, context.number, rule.structural, rule.page_break_before)
        yield from self._blocks(section.content, context, depth=1)

    # ------------------------------------------------------------------------------------- блоки
    def _blocks(self, blocks: tuple[Block, ...], section: SectionContext, depth: int) -> Iterator[RNode]:
        for block in blocks:
            match block:
                case P(parts=parts, align=align, indent=indent, keep_with_next=keep):
                    yield RParagraph(self._inlines(parts), align, indent, keep)
                case Subsection(title=title, content=content):
                    yield RHeading(depth + 1, title, self._sections.subsection(section, depth), False, None)
                    yield from self._blocks(content, section, depth + 1)
                case Figure():
                    yield self._figure(block, section)
                case Table():
                    yield self._table(block, section)
                case Listing():
                    yield self._listing(block, section)
                case Formula():
                    yield self._formula(block, section)
                case Bullets(items=items):
                    yield RList(self._list_items(items), "bullet")
                case Numbered(items=items, marker=marker):
                    yield RList(self._list_items(items), normalize_marker(marker))
                case Sources():
                    yield self._sources(block)
                case PageBreak():
                    yield RPageBreak()
                case _:
                    assert_never(block)

    def _sources(self, block: Sources) -> RSources:
        """
        Место списка источников: записи вручную запоминаются, а сам список заполняется после прохода по отчету.
        """
        self.sources.open_list()
        for entry in block.entries:
            match entry:
                case Source(key=key, text=text):
                    self.sources.add_manual(self._inlines(text), key)
                case _:
                    self.sources.add_manual(self._inlines(entry))
        self.sources.add_nocite(block.nocite)
        return RSources(())

    def _figure(self, block: Figure, section: SectionContext) -> RFigure:
        number = self._number(block, "figure", section)
        return RFigure(block.source, self._inlines(block.caption), number, block.width_cm)

    def _table(self, block: Table, section: SectionContext) -> RTable:
        number = self._number(block, "table", section) if block.caption is not None else None
        caption = self._optional_inlines(block.caption)
        header = tuple(self._inlines(cell) for cell in block.header)
        rows = tuple(tuple(self._cell(value) for value in row) for row in block.rows)
        return RTable(
            header,
            rows,
            caption,
            number,
            tuple(block.col_widths_cm) if block.col_widths_cm is not None else None,
            tuple(block.align) if block.align is not None else None,
            block.font_size_pt,
        )

    def _cell(self, value: object) -> RCell:
        """
        Ячейка: узлы, ``Md`` и их последовательности берутся как есть, остальное (строка, число) - буквальный текст.
        """
        inlines = self._inlines(value if is_rich_text(value) else str(value))
        return RCell(inlines, numeric=bool(_NUMERIC_CELL.match(plain_text(inlines))))

    def _listing(self, block: Listing, section: SectionContext) -> RListing:
        style = self._style.listing
        number = self._number(block, "listing", section) if block.caption is not None else None
        caption = self._optional_inlines(block.caption)
        return RListing(
            block.code,
            caption,
            number,
            block.language,
            line_numbers=style.line_numbers if block.line_numbers is None else block.line_numbers,
            highlight=style.highlight if block.highlight is None else block.highlight,
        )

    def _formula(self, block: Formula, section: SectionContext) -> RFormula:
        numbered = bool(block.label) if block.numbered is None else block.numbered
        number = self._number(block, "formula", section) if numbered else None
        self._formulas[block.latex] = None
        self._formulas.update(dict.fromkeys(symbol for symbol, _ in block.legend))
        where = tuple((symbol, self._inlines(text)) for symbol, text in block.legend)
        return RFormula(block.latex, number, where)

    def _list_items(self, entries: Sequence[ListEntry]) -> tuple[RListItem, ...]:
        return tuple(self._list_item(entry) for entry in entries)

    def _list_item(self, entry: ListEntry) -> RListItem:
        match entry:
            case ListItem(text=text, children=children):
                return RListItem(self._inlines(text), self._list_items(children))
            case _:
                return RListItem(self._inlines(entry))

    # --------------------------------------------------------------------------- номера и текст
    def _number(self, block: Labeled, kind: NumberKind, section: SectionContext) -> Number:
        number = self._numbers.next(kind, section)
        self.labels.register(block, number)
        return number

    def _optional_inlines(self, value: RichText | None) -> Inlines | None:
        return None if value is None else self._inlines(value)

    def _inlines(self, value: RichText) -> Inlines:
        """
        Текст в инлайны IR: ``Md`` разобран, ссылки на блоки заменены ссылками по метке; заодно запоминаются
        использованные метки и формулы.
        """
        nodes: list[Inline] = []
        for node in as_inlines(value, self._markup):
            match node:
                case BlockRef():
                    nodes.append(self.labels.reference_block(node))
                case Cite(citations=citations, bold=bold, italic=italic):
                    nodes.append(Text(self.sources.cite(citations), bold, italic))
                case Ref():
                    self.labels.use(node)
                    nodes.append(node)
                case Math(latex=latex):
                    self._formulas[latex] = None
                    nodes.append(node)
                case _:
                    nodes.append(node)
        return tuple(nodes)
