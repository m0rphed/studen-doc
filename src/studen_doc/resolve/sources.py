"""
Список использованных источников: номера записей по порядку первой ссылки (ГОСТ 7.32, 6.16) и сборка списка.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence

from studen_doc.errors import BibliographyError, ResolveError
from studen_doc.ir import Inlines
from studen_doc.model.bibliography import ALL_SOURCES
from studen_doc.model.inline import Citation

#: Начало внутреннего ключа записи без ключа: автор такие ключи не пишет (в начале стоит нулевой символ).
_ANONYMOUS_PREFIX = "\0source:"

#: Сколько номеров подряд сворачивается в диапазон: [1, 2] остается, [1-3] сворачивается.
_MIN_RANGE = 3


class SourceRegistry:
    """
    Реестр одного прохода: какие источники процитированы и в каком порядке, какие записаны вручную.

    Номер записи в списке совпадает с номером в тексте ссылки (ГОСТ 7.32, 6.9.1), поэтому номера выдаются
    сразу при первой ссылке; источники без ссылок получают следующие номера при сборке списка.
    """

    def __init__(self) -> None:
        self._cited: dict[str, int] = {}
        self._manual: dict[str, Inlines] = {}
        self._nocite: list[str] = []
        self._list_count = 0

    @property
    def has_citations(self) -> bool:
        return bool(self._cited)

    @property
    def has_list(self) -> bool:
        return self._list_count > 0

    def cite(self, citations: Sequence[Citation]) -> str:
        """
        Текст ссылки в квадратных скобках: ``[1]``, ``[2, 3]``, ``[4, с. 5]``; подряд идущие номера (три и больше)
        сворачиваются в диапазон ``[1-3]``.
        """
        for citation in citations:
            self._cited.setdefault(citation.key, len(self._cited) + 1)
        return f"[{_join([(self._cited[citation.key], citation.locator) for citation in citations])}]"

    def open_list(self) -> None:
        """
        Начался список источников; в отчете он один.
        """
        self._list_count += 1
        if self._list_count > 1:
            raise ResolveError("В отчете несколько списков источников (Sources): нужен один")

    def add_manual(self, entry: Inlines, key: str | None = None) -> None:
        """
        Запись, написанная вручную; без ключа на нее нельзя сослаться, но в списке она есть.
        """
        if key is None:
            key = f"{_ANONYMOUS_PREFIX}{len(self._manual)}"
        elif key in self._manual:
            raise ResolveError(f"Источник {key!r} записан в списке дважды")
        self._manual[key] = entry

    def add_nocite(self, keys: Sequence[str]) -> None:
        self._nocite.extend(keys)

    def requested_keys(self) -> list[str]:
        """
        Ключи, описания которых нужно взять из библиографии: процитированные, не записанные вручную, и ``nocite``.
        """
        cited = [key for key in self._cited if key not in self._manual]
        return [*cited, *(key for key in self._nocite if key not in self._manual)]

    def entries(self, formatted: Mapping[str, Inlines]) -> tuple[Inlines, ...]:
        """
        Записи списка: сначала процитированные в порядке ссылок, затем остальные ручные и ``nocite``.
        """
        known = {**formatted, **self._manual}
        missing = [key for key in self._cited if key not in known]
        if missing:
            raise BibliographyError(
                f"Нет описания источников {missing}: добавьте их в библиографию "
                "(Bibliography, bibliography: в метаданных) или в Sources(entries=[Source(ключ, текст)])"
            )
        unknown = [key for key in self._nocite if key != ALL_SOURCES and key not in known]
        if unknown:
            raise BibliographyError(f"nocite: в библиографии нет источников {unknown}")
        order = [*self._cited, *self._manual, *formatted]
        return tuple(known[key] for key in dict.fromkeys(order))


def _join(items: list[tuple[int, str | None]]) -> str:
    """
    Номера через запятую; три и больше подряд сворачиваются в диапазон (``1-3``), а если у источника есть место
    (``с. 5``), оно пишется после номера и ссылки разделяются точкой с запятой.
    """
    separator = "; " if any(locator for _, locator in items) else ", "
    parts = [_run_text(run) for run in _runs(items)]
    return separator.join(parts)


def _runs(items: list[tuple[int, str | None]]) -> Iterator[list[tuple[int, str | None]]]:
    """
    Группы подряд идущих номеров без места в источнике; остальные ссылки идут по одной.
    """
    run: list[tuple[int, str | None]] = []
    for item in items:
        if run and item[1] is None and run[-1][1] is None and item[0] == run[-1][0] + 1:
            run.append(item)
            continue
        if run:
            yield run
        run = [item]
    if run:
        yield run


def _run_text(run: list[tuple[int, str | None]]) -> str:
    if len(run) >= _MIN_RANGE:
        return f"{run[0][0]}–{run[-1][0]}"
    return ", ".join(f"{number}, {locator}" if locator else str(number) for number, locator in run)
