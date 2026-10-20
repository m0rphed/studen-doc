"""
Реестр именованных стилей: по имени стиль находится из метаданных Markdown (``style: suai``).
"""

from __future__ import annotations

from studen_doc.style.report_style import ReportStyle

_STYLES: dict[str, ReportStyle] = {}


def register_style(name: str, style: ReportStyle) -> ReportStyle:
    """
    Регистрирует стиль под именем (его можно писать как ``style: имя`` в метаданных Markdown)
    и возвращает его же, чтобы регистрировать прямо при создании:

        SUAI = register_style("suai", GOST_732.evolve(...))
    """
    if name in _STYLES:
        raise ValueError(f"Стиль {name!r} уже зарегистрирован")
    _STYLES[name] = style
    return style


def unregister_style(name: str) -> None:
    """
    Убирает стиль из реестра (для временных стилей: в тестах, плагинах); неизвестное имя - ``KeyError``.
    """
    del _STYLES[name]


def style_named(name: str) -> ReportStyle:
    """
    Стиль по имени; неизвестное имя - ``KeyError`` (допустимые имена - ``style_names()``).
    """
    return _STYLES[name]


def style_names() -> list[str]:
    return sorted(_STYLES)
