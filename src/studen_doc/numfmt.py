"""
Форматирование чисел для текста отчета: спецификация формата, десятичный разделитель и знак минус.
"""

from __future__ import annotations

import re
from typing import Any

#: Типографский знак минус (U+2212): в тексте отрицательные числа пишутся им, а не дефисом.
MINUS = "\u2212"

#: Число целиком: знак, цифры, дробная часть, порядок, необязательный процент. Дефис в такой записи - только знак.
_NUMBER = re.compile(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?%?")


def format_value(value: Any, spec: str = "", *, decimal: str = ",", minus: str = MINUS) -> str:
    """
    Значение как текст: ``format(value, spec)`` (или ``str``); в числе точка заменяется на ``decimal``, а дефис
    знака - на ``minus`` (по умолчанию типографский минус).

    ``format_value(-0.8812, ".3f")`` дает ``0,881`` с минусом U+2212 впереди; строки, не похожие на число, не меняются.
    Обычный дефис в знаке оставляет ``minus="-"``.
    """
    text = format(value, spec) if spec else str(value)
    if _NUMBER.fullmatch(text):
        if minus != "-":
            text = text.replace("-", minus)
        if decimal != ".":
            text = text.replace(".", decimal)
    return text
