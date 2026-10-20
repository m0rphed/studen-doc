"""
DOCX-рендерер: ``ResolvedReport`` -> файл .docx.
"""

from __future__ import annotations

from pathlib import Path
from typing import assert_never

from docx import Document
from docx.document import Document as DocxDocument

from studen_doc.equations import MathConverter, PandocConverter
from studen_doc.ir import (
    RAppendixHeading,
    ResolvedReport,
    RFigure,
    RFormula,
    RHeading,
    RList,
    RListing,
    RNode,
    RPageBreak,
    RParagraph,
    RSources,
    RTable,
    RToc,
)
from studen_doc.ooxml.settings import enable_update_fields
from studen_doc.render.docx import figures, formulas, headings, listings, lists, paragraphs, tables
from studen_doc.render.docx.context import Context
from studen_doc.render.docx.list_numbering import ListNumbering
from studen_doc.render.docx.setup import setup_document, setup_footer
from studen_doc.render.docx.title import render_title


class DocxRenderer:
    """
    Рисует IR средствами python-docx. Реализует протокол ``studen_doc.render.Renderer``.

    ``math`` — конвертер формул LaTeX -> OMML; по умолчанию pandoc. Все формулы документа
    конвертируются одним обращением к нему, до начала отрисовки.
    """

    def __init__(self, math: MathConverter | None = None) -> None:
        self.math: MathConverter = math if math is not None else PandocConverter()

    def build(self, report: ResolvedReport) -> DocxDocument:
        doc = Document()
        math = self.math.convert(report.formulas) if report.formulas else {}
        ctx = Context(doc, report.style, report.labels, math, ListNumbering(doc, report.style))
        setup_document(doc, report)
        if report.title_page is not None:
            render_title(report.title_page, ctx)
            paragraphs.emit_page_break(ctx)
        for node in report.nodes:
            self._emit(ctx, node)
        setup_footer(doc, report)
        if report.has_toc:
            enable_update_fields(doc)
        return doc

    def render(self, report: ResolvedReport, path: Path) -> Path:
        doc = self.build(report)
        path.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(path))
        return path

    @staticmethod
    def _emit(ctx: Context, node: RNode) -> None:
        match node:
            case RHeading():
                headings.emit_heading(ctx, node)
            case RAppendixHeading():
                headings.emit_appendix_heading(ctx, node)
            case RToc():
                headings.emit_toc(ctx, node)
            case RParagraph():
                paragraphs.emit_paragraph(ctx, node)
            case RPageBreak():
                paragraphs.emit_page_break(ctx)
            case RFigure():
                figures.emit_figure(ctx, node)
            case RTable():
                tables.emit_table(ctx, node)
            case RListing():
                listings.emit_listing(ctx, node)
            case RFormula():
                formulas.emit_formula(ctx, node)
            case RList():
                lists.emit_list(ctx, node)
            case RSources():
                lists.emit_sources(ctx, node)
            case _:
                assert_never(node)
