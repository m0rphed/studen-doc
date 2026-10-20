"""
Фронтенды: чтение исходных форматов (Markdown) в модель отчета.
"""

from studen_doc.frontends.markdown import (
    PANDOC_FORMAT,
    MarkdownError,
    ParsedDocument,
    load_report,
    parse_inline_markdown,
    parse_markdown,
    parse_markdown_text,
)

__all__ = [
    "PANDOC_FORMAT",
    "MarkdownError",
    "ParsedDocument",
    "load_report",
    "parse_inline_markdown",
    "parse_markdown",
    "parse_markdown_text",
]
