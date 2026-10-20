"""
Атрибуты Markdown (``{width=10cm numberLines highlight=true}``) как типизированные значения.

Все ошибки разбора - ``MarkdownError`` с именем атрибута и его значением, чтобы в длинном документе
сразу было понятно, что поправить.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

from studen_doc.errors import MarkdownError

_LENGTH = re.compile(r"(\d+(?:\.\d+)?)\s*(cm|mm|in|pt)?")
_CM_PER_UNIT = {"cm": 1.0, "mm": 0.1, "in": 2.54, "pt": 2.54 / 72}
_FLAGS = {"true": True, "yes": True, "1": True, "false": False, "no": False, "0": False}


def parse_flag(text: str) -> bool:
    """
    ``true``, ``yes``, ``1`` и ``false``, ``no``, ``0``.
    """
    if text not in _FLAGS:
        raise ValueError(text)
    return _FLAGS[text]


def parse_length_cm(text: str) -> float:
    """
    Длина в сантиметрах: ``10cm``, ``100mm``, ``4in``, ``72pt``; число без единицы - сантиметры.
    """
    match = _LENGTH.fullmatch(text.strip())
    if match is None:
        raise ValueError(text)
    return float(match[1]) * _CM_PER_UNIT[match[2] or "cm"]


@dataclass(frozen=True, slots=True)
class Options:
    """
    Пары ``ключ=значение`` из атрибутов блока; значения читаются методами, которые сами приводят тип.
    """

    values: Mapping[str, str] = field(default_factory=dict)

    def text(self, name: str, default: str | None = None) -> str | None:
        return self.values.get(name, default)

    def integer(self, name: str, default: int) -> int:
        parsed = self._parse(name, int, "ожидалось целое число")
        return default if parsed is None else parsed

    def number(self, name: str) -> float | None:
        return self._parse(name, float, "ожидалось число")

    def flag(self, name: str) -> bool | None:
        return self._parse(name, parse_flag, "ожидалось true или false")

    def length_cm(self, name: str) -> float | None:
        return self._parse(name, parse_length_cm, "ожидались число и единица cm, mm, in или pt (например, 10cm)")

    def lengths_cm(self, name: str, *, count: int) -> tuple[float, ...] | None:
        """
        Список длин через запятую (``widths="3,5.5,2"``), ровно ``count`` штук.
        """

        def parse(text: str) -> tuple[float, ...]:
            lengths = tuple(parse_length_cm(part) for part in text.split(","))
            if len(lengths) != count:
                raise ValueError(text)
            return lengths

        return self._parse(name, parse, f"ожидался список из {count} длин через запятую (например, 3,5.5,2)")

    def _parse[T](self, name: str, parse: Callable[[str], T], expected: str) -> T | None:
        text = self.values.get(name)
        if text is None:
            return None
        try:
            return parse(text)
        except ValueError as error:
            raise MarkdownError(f"{name}={text!r}: {expected}") from error
