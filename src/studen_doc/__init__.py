"""
studen_doc — декларативная генерация отчётов .docx по ГОСТ 7.32-2017 и вузовским стилям.

Слои: ``frontends`` (Markdown -> модель) и Python-описание дают ``model`` (что в отчёте); ``style`` - как
оформить; ``resolve`` расставляет номера и ссылки, результат - ``ir``; ``render`` записывает IR в формат
(``ooxml`` - примитивы Word). ``pipeline`` соединяет слои.

``import studen_doc`` не загружает python-docx: он нужен только при сборке .docx. Готовые стили вузов
(``universities``) подключаются явно: ``import studen_doc.universities`` регистрирует стиль и титульный
лист ``suai``, после чего ``style: suai`` в Markdown находит их по имени.
"""

from studen_doc.equations import MathConverter, PandocConverter
from studen_doc.errors import (
    BibliographyError,
    MarkdownError,
    MathConversionError,
    PandocError,
    ReportError,
    ResolveError,
)
from studen_doc.integrations import (
    figure_from_matplotlib,
    listing_from_callable,
    listing_from_file,
    table_from,
)
from studen_doc.model import (
    B,
    Bibliography,
    Bullets,
    Citation,
    Cite,
    Code,
    Figure,
    Formula,
    I,
    LineBreak,
    Listing,
    ListItem,
    Math,
    Md,
    Numbered,
    P,
    PageBreak,
    Ref,
    Report,
    Source,
    Sources,
    Subsection,
    Table,
    Text,
    TitlePage,
)
from studen_doc.model.report import register_title_page
from studen_doc.numfmt import format_value
from studen_doc.style import GOST_732, HeadingStyle, ReportStyle, SectionRule, register_style

__all__ = [
    "GOST_732",
    "B",
    "Bibliography",
    "BibliographyError",
    "Bullets",
    "Citation",
    "Cite",
    "Code",
    "Figure",
    "Formula",
    "HeadingStyle",
    "I",
    "LineBreak",
    "ListItem",
    "Listing",
    "MarkdownError",
    "Math",
    "MathConversionError",
    "MathConverter",
    "Md",
    "Numbered",
    "P",
    "PageBreak",
    "PandocConverter",
    "PandocError",
    "Ref",
    "Report",
    "ReportError",
    "ReportStyle",
    "ResolveError",
    "SectionRule",
    "Source",
    "Sources",
    "Subsection",
    "Table",
    "Text",
    "TitlePage",
    "figure_from_matplotlib",
    "format_value",
    "listing_from_callable",
    "listing_from_file",
    "register_style",
    "register_title_page",
    "table_from",
]
__version__ = "0.1.0"
