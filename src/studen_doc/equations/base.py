"""
Контракт конвертера формул: LaTeX -> OMML (формулы Word).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Protocol

from studen_doc.errors import MathConversionError

if TYPE_CHECKING:  # lxml нужен только конвертеру: пакет не должен тянуть его при импорте
    from lxml import etree

__all__ = ["MathConversionError", "MathConverter"]


class MathConverter(Protocol):
    """
    Превращает набор формул LaTeX в элементы ``m:oMath``.

    Контракт: один вызов — все формулы документа (конвертер сам решает, как их обработать за один раз);
    ключи результата — исходные строки; ошибка в любой формуле — ``MathConversionError`` с её текстом.
    Подмена в тестах и подключение другого движка — любым объектом с таким методом.
    """

    def convert(self, formulas: Sequence[str]) -> Mapping[str, etree._Element]: ...
