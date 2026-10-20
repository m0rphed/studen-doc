"""
Подсветка синтаксиса листингов (pygments — необязательная зависимость).
"""

from __future__ import annotations

from typing import NamedTuple


class Span(NamedTuple):
    text: str
    color: str | None
    bold: bool
    italic: bool


def highlight_lines(
    code: str,
    language: str,
    pygments_style: str,
) -> list[list[Span]]:
    """
    Разбивает код на строки; каждая строка — список цветных фрагментов.
    """
    try:
        from pygments import lex
        from pygments.lexers import get_lexer_by_name
        from pygments.styles import get_style_by_name
    except ImportError as error:
        raise ImportError("Для подсветки листингов: pip install studen-doc[highlight]") from error
    style = get_style_by_name(pygments_style)
    lines: list[list[Span]] = [[]]
    for token_type, value in lex(code, get_lexer_by_name(language)):
        token_style = style.style_for_token(token_type)
        for index, part in enumerate(value.split("\n")):
            if index > 0:
                lines.append([])
            if part:
                lines[-1].append(
                    Span(part, token_style["color"] or None, bool(token_style["bold"]), bool(token_style["italic"]))
                )
    expected = len(code.split("\n"))
    lines.extend([] for _ in range(expected - len(lines)))
    return lines
