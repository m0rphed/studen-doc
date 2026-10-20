"""
Структура документа: плоский поток заголовков и блоков -> разделы с вложенными подразделами.

В Markdown заголовки идут подряд (``#``, ``##``, ``###``), а в модели подраздел вложен в раздел:
``Section("Ход работы", (..., Subsection("Подраздел", ...)))``.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from studen_doc.errors import MarkdownError
from studen_doc.frontends.markdown.options import Options
from studen_doc.model.blocks import Block, Subsection
from studen_doc.model.report import Section, Toc

#: Ключ правил оформления для приложений (см. ``HeadingsStyle.rules``).
APPENDIX_SECTION = "Приложение"

#: Класс заголовка, который превращает раздел в приложение: ``# Название {.appendix status=справочное}``.
APPENDIX_CLASS = "appendix"


@dataclass(frozen=True, slots=True)
class Heading:
    """
    Заголовок в потоке блоков, до свертки в разделы.
    """

    level: int
    title: str
    classes: tuple[str, ...]
    options: Options


#: Элемент потока блоков документа: обычный блок, заголовок или оглавление.
type Item = Block | Heading | Toc


def build_sections(items: Sequence[Item]) -> tuple[Section | Toc, ...]:
    """
    Разделы верхнего уровня и оглавления между ними. Оглавление и заголовки первого уровня разделяют
    разделы; текст до первого заголовка - ошибка.
    """
    result: list[Section | Toc] = []
    position = 0
    while position < len(items):
        item = items[position]
        match item:
            case Toc():
                result.append(item)
                position += 1
            case Heading(level=1):
                content, position = _fold(items, position + 1, level=1)
                result.append(_section(item, content))
            case Heading(title=title):
                raise MarkdownError(f"Документ должен начинаться с заголовка первого уровня: {title!r}")
            case _:
                raise MarkdownError("Текст до первого заголовка первого уровня: поместите его в раздел")
    return tuple(result)


def _section(heading: Heading, content: tuple[Block, ...]) -> Section:
    """
    Раздел из заголовка: правило оформления - из ``{rule=...}``, у приложения (``.appendix``) - «Приложение».
    """
    rule = heading.options.text("rule")
    if rule is None and APPENDIX_CLASS in heading.classes:
        rule = APPENDIX_SECTION
    return Section(heading.title, content, rule=rule, status=heading.options.text("status"))


def _fold(items: Sequence[Item], start: int, level: int) -> tuple[tuple[Block, ...], int]:
    """
    Содержимое раздела или подраздела: заголовки глубже ``level`` складываются во вложенные ``Subsection``.
    Возвращает блоки и позицию первого элемента, который уже не относится к этому уровню.
    """
    blocks: list[Block] = []
    position = start
    while position < len(items):
        item = items[position]
        match item:
            case Toc() if level == 1:
                break  # оглавление между разделами верхнего уровня
            case Toc():
                raise MarkdownError("Оглавление допустимо только между разделами верхнего уровня")
            case Heading(level=deeper) if deeper <= level:
                break
            case Heading(level=deeper, title=title):
                content, position = _fold(items, position + 1, deeper)
                blocks.append(Subsection(title, *content))
            case _:
                blocks.append(item)
                position += 1
    return tuple(blocks), position
