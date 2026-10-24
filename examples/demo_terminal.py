"""
Вывод терминала в отчете: цветной листинг, скриншоты (своя тема, шрифт, поля), снимок программы, которая не
завершается, и сеанс IPython.

Нужен extra ``terminal`` (пакет termsnap). Один запуск программы переиспользуется для разных представлений: вывод
остается текстом в листинге (его можно выделить и найти) и рисуется скриншотом. Сеанс IPython берется через ``uvx``
(при первом запуске нужна сеть); без ``uvx`` или при ``STUDEN_DOC_DEMO_OFFLINE=1`` этот раздел пропускается.
"""

import os
import shutil
import sys
from pathlib import Path

import termsnap
from termsnap.png import DEFAULT_FAMILIES

from studen_doc import Md, P, Report, Subsection, figure_from_terminal, listing_from_terminal
from studen_doc.universities.suai import SUAI

HERE = Path(__file__).parent
PROGRAMS = HERE / "terminal"
PYTHON = sys.executable

#: Своя тема: все, что не названо, берется от ``base``. Такой словарь удобно хранить в конфигурации проекта.
NIGHT = {
    "base": "dark",
    "name": "night",
    "background": "#0b1020",
    "foreground": "#c8d3f5",
    "ansi": {"red": "#ff757f", "green": "#c3e88d", "yellow": "#ffc777", "blue": "#82aaff", "cyan": "#86e1fc"},
}

#: Свой шрифт: первое установленное семейство из списка; запасные (эмодзи, символы) подбираются сами.
FONTS = ("Cascadia Mono", "JetBrains Mono", *DEFAULT_FAMILIES)


def ipython_available() -> bool:
    return shutil.which("uvx") is not None and os.environ.get("STUDEN_DOC_DEMO_OFFLINE") != "1"


def ipython_session() -> termsnap.Capture:
    """
    Сеанс IPython: строки печатаются в псевдотерминале, стрелка вверх достает прошлую строку.
    """
    from termsnap import Key

    environment = {key: value for key, value in os.environ.items() if key != "VIRTUAL_ENV"}
    return termsnap.run(
        ["uvx", "--quiet", "ipython"],
        backend=termsnap.PtyBackend(),
        env=environment,
        timeout=180,
        columns=64,
        input=["squares = [n ** 2 for n in range(6)]", "squares", "1 / 0", "6 * 7", Key.UP, Key.ENTER, "exit"],
        prompt=r"In \[\d+\]:$",
    )


def build_report(*, ipython: bool | None = None) -> Report:
    report = Report(SUAI, title="Вывод терминала в отчете")
    log = termsnap.run([PYTHON, str(PROGRAMS / "train_log.py")], columns=64)

    text = listing_from_terminal(log, "Журнал обучения, цветной текст", label="lst:log")
    plain = figure_from_terminal(log, "Журнал обучения, окно терминала", label="fig:log")
    night = figure_from_terminal(
        log,
        "Тот же журнал: своя тема, шрифт и узкие поля",
        label="fig:night",
        theme=NIGHT,
        fonts=FONTS,
        font_size=13,
        padding=6,
    )
    report.add_section(
        "Вывод программы",
        P(
            "Результат запуска программы можно вставить в отчет двумя способами: текстом (листинг ",
            text.ref,
            ") и скриншотом (рисунок ",
            plain.ref,
            "). Текст остается текстом: его можно выделить, найти и скопировать, а цвета и начертание сохраняются.",
        ),
        Subsection("Цветной листинг", text),
        Subsection(
            "Скриншот",
            plain,
            P(
                "Тему, шрифт и поля можно переопределить при вызове (рисунок ",
                night.ref,
                "): тема задается словарем и достраивается от базовой, из шрифтов берется первое установленное, "
                "а эмодзи и редкие символы по-прежнему подбираются автоматически.",
            ),
            night,
        ),
    )

    monitor = figure_from_terminal(
        [PYTHON, str(PROGRAMS / "monitor.py")],
        "Снимок программы, которая сама не завершается",
        label="fig:monitor",
        backend=termsnap.PtyBackend(),
        snapshot=termsnap.Snapshot(after=1.2),
        columns=64,
        rows=10,
        timeout=60,
    )
    report.add_section(
        "Программа, которая не завершается",
        P(
            Md(
                "Мониторы вроде `htop` рисуют окно и работают, пока их не остановят. Момент снимка задается явно "
                "(здесь через 1,2 с после запуска), после него программа останавливается: рисунок [](#fig:monitor)."
            )
        ),
        monitor,
    )

    if ipython_available() if ipython is None else ipython:
        session = ipython_session()
        report.add_section(
            "Интерактивный сеанс",
            P(
                "Программе можно напечатать строки и клавиши. Сеанс IPython ниже получен автоматически: подсветка "
                "синтаксиса, приглашения и трассировка ошибки сохранились."
            ),
            figure_from_terminal(session, "Сеанс IPython, окно терминала", label="fig:ipython"),
            listing_from_terminal(session, "Тот же сеанс IPython, текстом", label="lst:ipython"),
        )
    return report


if __name__ == "__main__":
    print("saved", build_report().build_to_docx(Path(__file__).with_name("demo_terminal.docx")))
