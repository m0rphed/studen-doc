"""
Время сборки растет линейно с размером документа.

Раньше заполнение таблицы через ``Table.cell()`` и ``Paragraph.style = имя`` в python-docx давало квадратичное
время: таблица на 5000 строк собиралась дольше двух минут. Тест сравнивает время сборки на размерах в четыре раза
разных: при линейном росте отношение около 4, при квадратичном - около 16. Порог взят с запасом, чтобы случайные
колебания машины его не задевали.
"""

import time
from pathlib import Path

import pytest

from studen_doc import Bullets, P, Report, Table
from studen_doc.style import GOST_732

SMALL, LARGE = 300, 1200
#: Отношение времени на большом размере к малому: линейный рост - около 4, квадратичный - около 16.
MAX_RATIO = 9


def table(rows: int) -> list:
    return [Table(["Номер", "Значение", "Подпись"], [[i, i / 7, f"строка {i}"] for i in range(rows)], caption="Данные")]


def paragraphs(count: int) -> list:
    return [P(f"Абзац номер {i} с текстом.") for i in range(count)]


def bullets(count: int) -> list:
    return [Bullets([f"пункт {i}" for i in range(count)])]


def build_seconds(make, size: int, path: Path) -> float:
    """
    Лучшее из двух времен сборки: так случайная задержка не портит замер.
    """
    report = Report(GOST_732).add_section("Раздел", *make(size))
    times = []
    for _ in range(2):
        start = time.perf_counter()
        report.build_to_docx(path)
        times.append(time.perf_counter() - start)
    return min(times)


@pytest.mark.parametrize("make", [table, paragraphs, bullets], ids=["table", "paragraphs", "bullets"])
def test_build_time_grows_linearly(make, tmp_path):
    small = build_seconds(make, SMALL, tmp_path / "small.docx")
    large = build_seconds(make, LARGE, tmp_path / "large.docx")
    assert large < MAX_RATIO * small, f"{make.__name__}: {SMALL} -> {small:.2f} с, {LARGE} -> {large:.2f} с"
