"""
LaTeX -> OMML (формулы Word): контракт конвертера и реализация на pandoc.
"""

from studen_doc.equations.base import MathConversionError, MathConverter
from studen_doc.equations.pandoc import PandocConverter, find_pandoc

__all__ = ["MathConversionError", "MathConverter", "PandocConverter", "find_pandoc"]
