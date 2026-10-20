"""
Настройка документа Word по стилю: страница, шрифты по умолчанию, именованные стили, колонтитул.
"""

from __future__ import annotations

from typing import cast

from docx.document import Document as DocxDocument
from docx.enum.style import WD_STYLE_TYPE
from docx.shared import Mm
from docx.styles.style import ParagraphStyle

from studen_doc.ir import ResolvedReport
from studen_doc.ooxml.fields import add_field
from studen_doc.ooxml.fonts import apply_font
from studen_doc.ooxml.paragraph import COMPACT_TIGHT, ParagraphFormat, apply_format, set_format
from studen_doc.ooxml.settings import set_compat_mode_15
from studen_doc.ooxml.styles import set_document_defaults
from studen_doc.render.docx import names
from studen_doc.style import CaptionStyle, ReportStyle


def _paragraph_style(doc: DocxDocument, name: str) -> ParagraphStyle:
    """
    Стиль абзаца по имени: существующий или новый (python-docx типизирует оба как BaseStyle).
    """
    try:
        return cast(ParagraphStyle, doc.styles[name])
    except KeyError:
        return cast(ParagraphStyle, doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH))


def setup_document(doc: DocxDocument, report: ResolvedReport) -> None:
    style = report.style
    _setup_page(doc, style)
    set_compat_mode_15(doc)
    _setup_defaults(doc, style)
    _setup_builtin_styles(doc, style)
    _setup_custom_styles(doc, style)
    if report.title:
        doc.core_properties.title = report.title
    if report.author:
        doc.core_properties.author = report.author


def setup_footer(doc: DocxDocument, report: ResolvedReport) -> None:
    numbers = report.style.page_numbers
    if numbers.align == "none":
        return
    section = doc.sections[0]
    section.different_first_page_header_footer = report.title_page is not None and not numbers.show_on_title_page
    par = section.footer.paragraphs[0]
    set_format(par, base=COMPACT_TIGHT, align=numbers.align)
    add_field(par, "PAGE", "1")


def _setup_page(doc: DocxDocument, style: ReportStyle) -> None:
    page = style.page
    section = doc.sections[0]
    section.page_width, section.page_height = Mm(page.width_mm), Mm(page.height_mm)
    section.left_margin, section.right_margin = Mm(page.margin_left_mm), Mm(page.margin_right_mm)
    section.top_margin, section.bottom_margin = Mm(page.margin_top_mm), Mm(page.margin_bottom_mm)
    section.footer_distance = Mm(page.footer_distance_mm)


def _setup_defaults(doc: DocxDocument, style: ReportStyle) -> None:
    """
    Шрифт и язык документа по умолчанию — чтобы таблицы и поля не брали тему Cambria/Calibri.
    """
    set_document_defaults(doc, font_name=style.text.font_name, language=style.text.language)


def _setup_builtin_styles(doc: DocxDocument, style: ReportStyle) -> None:
    text, headings = style.text, style.headings
    normal = _paragraph_style(doc, "Normal")
    apply_font(normal, name=text.font_name, size_pt=text.size_pt, color=text.color)
    apply_format(
        normal,
        ParagraphFormat(
            align=text.align,
            first_indent_cm=text.first_indent_cm,
            line_spacing=text.line_spacing,
            before_pt=0,
            after_pt=0,
        ),
    )
    normal.paragraph_format.widow_control = True

    for level in (1, 2, 3):
        heading = headings.for_level(level)
        word_style = _paragraph_style(doc, f"Heading {level}")
        apply_font(
            word_style,
            name=text.font_name,
            size_pt=heading.size_pt,
            bold=heading.bold,
            italic=heading.italic,
            caps=heading.caps,
            color=text.color,
        )
        apply_format(
            word_style,
            ParagraphFormat(
                align=heading.align,
                first_indent_cm=heading.first_indent_cm,
                left_indent_cm=0,
                line_spacing=heading.line_spacing,
                before_pt=heading.before_pt,
                after_pt=heading.after_pt,
                keep_next=heading.keep_with_next,
            ),
        )


def _setup_custom_styles(doc: DocxDocument, style: ReportStyle) -> None:
    text = style.text
    normal = _paragraph_style(doc, "Normal")

    def define(name: str, *, font: str, size_pt: float, fmt: ParagraphFormat) -> None:
        word_style = _paragraph_style(doc, name)
        word_style.base_style = normal
        apply_font(word_style, name=font, size_pt=size_pt, color=text.color)
        apply_format(word_style, fmt)

    def caption(name: str, cap: CaptionStyle) -> None:
        define(
            name,
            font=text.font_name,
            size_pt=cap.size_pt,
            fmt=ParagraphFormat(
                align=cap.align,
                first_indent_cm=0,
                line_spacing=cap.line_spacing,
                before_pt=cap.before_pt,
                after_pt=cap.after_pt,
                keep_next=cap.keep_with_next,
            ),
        )

    define(
        names.FIGURE,
        font=text.font_name,
        size_pt=text.size_pt,
        fmt=ParagraphFormat(
            align="center",
            first_indent_cm=0,
            line_spacing=1.0,
            before_pt=style.figure.gap_pt,
            after_pt=style.figure.gap_pt,
            keep_next=True,
        ),
    )
    caption(names.FIGURE_CAPTION, style.figure.caption)
    caption(names.TABLE_CAPTION, style.table.caption)
    caption(names.LISTING_CAPTION, style.listing.caption)
    define(
        names.TABLE_TEXT,
        font=text.font_name,
        size_pt=style.table.font_size_pt,
        fmt=ParagraphFormat(
            align="left",
            first_indent_cm=0,
            line_spacing=style.table.line_spacing,
            before_pt=0,
            after_pt=0,
        ),
    )
    define(
        names.CODE,
        font=text.mono_font_name,
        size_pt=style.listing.font_size_pt,
        fmt=ParagraphFormat(
            align="left",
            first_indent_cm=0,
            left_indent_cm=0,
            line_spacing=1.0,
            before_pt=0,
            after_pt=0,
        ),
    )
