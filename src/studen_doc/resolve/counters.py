"""
Счетчики нумерации: разделы, приложения, подразделы, а также рисунки, таблицы, листинги и формулы.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from studen_doc.errors import ResolveError
from studen_doc.ir import Number, NumberKind
from studen_doc.style import APPENDIX_LETTERS, NumberScope

_BOOKMARK_PREFIX: dict[NumberKind, str] = {"figure": "fig", "table": "tab", "listing": "lst", "formula": "eq"}


@dataclass(frozen=True, slots=True)
class SectionContext:
    """
    Раздел верхнего уровня, внутри которого идет разбор.
    """

    number: str | None  # «2» или буква приложения; None у ненумерованных разделов
    appendix: bool


class SectionNumbering:
    """
    Номера разделов (``1``, ``2``), буквы приложений (``А``, ``Б``) и номера подразделов (``1.2.3``).
    """

    def __init__(self) -> None:
        self._sections = 0
        self._appendices = 0
        self._subsections: list[int] = []

    def open(self, *, appendix: bool, numbered: bool) -> SectionContext:
        """
        Начинает следующий раздел верхнего уровня: нумерация его подразделов идет заново.
        """
        self._subsections = []
        if appendix:
            if self._appendices >= len(APPENDIX_LETTERS):
                raise ResolveError("Слишком много приложений")
            letter = APPENDIX_LETTERS[self._appendices]
            self._appendices += 1
            return SectionContext(letter, appendix=True)
        if numbered:
            self._sections += 1
            return SectionContext(str(self._sections), appendix=False)
        return SectionContext(None, appendix=False)

    def subsection(self, section: SectionContext, depth: int) -> str | None:
        """
        Номер подраздела на глубине ``depth`` (1 - прямо в разделе: ``1.1``, 2 - глубже: ``1.1.1``);
        у ненумерованных разделов номеров нет.
        """
        if section.number is None:
            return None
        counters = self._subsections
        counters.extend([0] * (depth - len(counters)))
        counters[depth - 1] += 1
        del counters[depth:]
        return ".".join([section.number, *map(str, counters)])


class NumberAllocator:
    """
    Номера подписанных блоков: сквозные (``3``, поле SEQ) либо внутри раздела (``2.3``, ``А.1``).
    Внутри приложения нумерация всегда по приложению.
    """

    def __init__(self, scope: NumberScope) -> None:
        self._numbered_by_section = scope == "section"
        self._continuous: Counter[NumberKind] = Counter()
        self._in_section: Counter[NumberKind] = Counter()
        self._bookmarks = 0

    def start_section(self) -> None:
        """
        Счетчики внутри раздела начинаются заново.
        """
        self._in_section.clear()

    def next(self, kind: NumberKind, section: SectionContext) -> Number:
        """
        Следующий номер блока вида ``kind`` и имя закладки, на которую будут ссылаться поля REF.
        """
        if section.appendix or (self._numbered_by_section and section.number is not None):
            self._in_section[kind] += 1
            display, use_seq = f"{section.number}.{self._in_section[kind]}", False
        else:
            self._continuous[kind] += 1
            display, use_seq = str(self._continuous[kind]), True
        self._bookmarks += 1
        bookmark = f"_Ref_{_BOOKMARK_PREFIX[kind]}_{self._bookmarks:03d}"
        return Number(kind, display, bookmark, use_seq)
