"""
Что подставляется в Markdown из Python: блоки на место ``::: insert`` и значения на место ``[]{var=...}``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from studen_doc.errors import MarkdownError
from studen_doc.model.blocks import Block
from studen_doc.numfmt import format_value


@dataclass(frozen=True, slots=True)
class Substitutions:
    """
    ``inserts`` - блок или список блоков по имени (вместо ``::: insert``); ``variables`` - значения по имени
    (вместо ``[]{var=...}``); ``decimal`` - десятичный разделитель в подставленных числах.
    """

    inserts: Mapping[str, Block | Sequence[Block]] = field(default_factory=dict)
    variables: Mapping[str, Any] = field(default_factory=dict)
    decimal: str = ","

    def insert(self, name: str) -> list[Block]:
        """
        Блоки для ``::: {.insert name=...}``.
        """
        if name not in self.inserts:
            raise MarkdownError(f"::: insert: блок {name!r} не передан (переданы: {sorted(self.inserts)})")
        chosen = self.inserts[name]
        return list(chosen) if isinstance(chosen, Sequence) else [chosen]

    def variable(self, name: str, spec: str = "") -> str:
        """
        Текст для ``[]{var=name format=spec}``: значение, отформатированное как ``format(value, spec)``.
        """
        if name not in self.variables:
            raise MarkdownError(f"Переменная {name!r} не передана (переданы: {sorted(self.variables)})")
        return format_value(self.variables[name], spec, decimal=self.decimal)
