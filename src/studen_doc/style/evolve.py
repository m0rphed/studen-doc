"""
Неизменяемое обновление вложенных dataclass-стилей: ``style.evolve(table={"border_sz": 8})``.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields, is_dataclass, replace
from typing import Any, Self


def evolve_dataclass[T](obj: T, **changes: Any) -> T:
    """
    Возвращает копию ``obj`` с изменениями.

    * значение-словарь для поля-dataclass обновляет это поле рекурсивно, а не заменяет целиком;
    * значение-словарь для поля-словаря (например, ``rules``) *дополняет* существующее;
    * неизвестное имя поля — ``TypeError`` с перечнем допустимых.
    """
    names = {f.name for f in fields(obj)}  # type: ignore[arg-type]
    unknown = set(changes) - names
    if unknown:
        raise TypeError(f"{type(obj).__name__}: неизвестные поля {sorted(unknown)}; допустимые: {sorted(names)}")
    resolved: dict[str, Any] = {}
    for name, value in changes.items():
        current = getattr(obj, name)
        if isinstance(value, Mapping) and is_dataclass(current) and not isinstance(current, type):
            resolved[name] = evolve_dataclass(current, **value)
        elif isinstance(value, Mapping) and isinstance(current, Mapping):
            resolved[name] = {**current, **value}
        else:
            resolved[name] = value
    return replace(obj, **resolved)  # type: ignore[type-var]


class Evolvable:
    """Примесь: добавляет ``.evolve(**changes)`` frozen-dataclass-ам."""
    __slots__ = ()

    def evolve(self, **changes: Any) -> Self:
        return evolve_dataclass(self, **changes)
