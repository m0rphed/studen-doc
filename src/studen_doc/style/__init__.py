"""
Описание оформления отчёта: тематические стили, композиция ReportStyle и пресеты.
"""

from studen_doc.style.components import (
    CaptionStyle,
    CellPadding,
    FigureStyle,
    FormulaStyle,
    ListingStyle,
    ListStyle,
    NumberingStyle,
    NumberScope,
    PageNumberStyle,
    PageStyle,
    TableStyle,
    TextStyle,
)
from studen_doc.style.evolve import evolve_dataclass
from studen_doc.style.headings import (
    APPENDIX_LETTERS,
    GOST_732_SECTIONS,
    HeadingsStyle,
    HeadingStyle,
    SectionRule,
)
from studen_doc.style.presets import gost_732
from studen_doc.style.registry import register_style, style_named, style_names, unregister_style
from studen_doc.style.report_style import ReportStyle

#: ГОСТ 7.32-2017: значения по умолчанию всех тематических стилей.
GOST_732 = register_style("gost_732", gost_732())

__all__ = [
    "APPENDIX_LETTERS",
    "GOST_732",
    "GOST_732_SECTIONS",
    "CaptionStyle",
    "CellPadding",
    "FigureStyle",
    "FormulaStyle",
    "HeadingStyle",
    "HeadingsStyle",
    "ListStyle",
    "ListingStyle",
    "NumberScope",
    "NumberingStyle",
    "PageNumberStyle",
    "PageStyle",
    "ReportStyle",
    "SectionRule",
    "TableStyle",
    "TextStyle",
    "evolve_dataclass",
    "gost_732",
    "register_style",
    "style_named",
    "style_names",
    "unregister_style",
]
