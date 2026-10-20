"""
Форматирование чисел для текста отчета: спецификация формата и десятичный разделитель.
"""

from __future__ import annotations

import re
from typing import Any

_DECIMAL_NUMBER = re.compile(r"[-+]?\d+\.\d+(?:[eE][-+]?\d+)?")


def format_value(value: Any, spec: str = "", *, decimal: str = ",") -> str:
    """
    Значение как текст: ``format(value, spec)`` (или ``str``), в десятичной дроби точка заменяется на ``decimal``.

    ``format_value(0.8812, ".3f")`` -> ``"0,881"``; строки и целые числа не меняются.
    """
    text = format(value, spec) if spec else str(value)
    if decimal != "." and _DECIMAL_NUMBER.fullmatch(text):
        text = text.replace(".", decimal)
    return text
