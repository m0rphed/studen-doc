"""
Вывод терминала: цветной листинг или рисунок-скриншот. Нужен пакет termsnap: ``pip install studen-doc[terminal]``.

Источник - готовый результат запуска (``termsnap.Capture``) либо команда, которую нужно выполнить:

    listing_from_terminal(["python", "train.py"], "Вывод обучения")
    figure_from_terminal(["python", "train.py"], "Окно терминала", theme="dark")

Тема (``theme``) - любой способ ее задать в termsnap: ``Theme``, имя (``"light"``) или словарь
(``{"base": "light", "ansi": {"red": "#c0392b"}}``), поэтому ее можно держать в конфигурации и передавать как есть.
Остальные именованные параметры уходят в ``termsnap.run`` (``backend``, ``timeout``, ``columns``, ``input``,
``snapshot``, ...): так запускаются и интерактивные программы (IPython, htop).
"""

from __future__ import annotations

import io
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from studen_doc.model.blocks import CodeRun, Figure, Listing
from studen_doc.model.inline import RichText

if TYPE_CHECKING:
    from termsnap import Capture, Rgb, Span, Theme, ThemeSpec
    from termsnap.png import FontSpec

#: Доля цвета текста в тусклом тексте, остальное - цвет фона (так же рисует PNG-рендерер termsnap).
DIM_SHARE = 0.6

#: Ширина терминала для листинга, если команда запускается здесь: строка листинга шрифтом 12 pt на странице А4
#: с полями ГУАП вмещает около 64 символов, а терминал по умолчанию шире (100) и дал бы переносы.
LISTING_COLUMNS = 64

_MISSING = "Для вывода терминала нужен пакет termsnap: pip install studen-doc[terminal]"


def _termsnap() -> Any:
    """
    Модуль termsnap; без него ``ImportError`` с подсказкой, что установить.
    """
    try:
        import termsnap
    except ImportError as error:
        raise ImportError(_MISSING) from error
    return termsnap


def _capture(source: Capture | Sequence[str], run_options: dict[str, Any]) -> Capture:
    """
    Результат запуска: готовый ``Capture`` берется как есть, команда выполняется с параметрами ``run_options``.
    """
    termsnap = _termsnap()
    if isinstance(source, str):
        raise TypeError('команда - это список аргументов, например ["python", "app.py"], а не строка')
    if isinstance(source, Sequence):
        return termsnap.run(source, **run_options)
    if run_options:
        raise TypeError(f"параметры запуска ({', '.join(sorted(run_options))}) нельзя задать вместе с готовым Capture")
    return source


def _hex(color: Rgb) -> str:
    return color.hex.removeprefix("#")


def _dimmed(foreground: Rgb, background: Rgb) -> Rgb:
    """
    Цвет тусклого текста: смесь цвета текста с фоном.
    """
    termsnap = _termsnap()

    def channel(front: int, back: int) -> int:
        return round(front * DIM_SHARE + back * (1 - DIM_SHARE))

    return termsnap.Rgb(
        channel(foreground.red, background.red),
        channel(foreground.green, background.green),
        channel(foreground.blue, background.blue),
    )


def _run(span: Span, theme: Theme) -> CodeRun:
    """
    Фрагмент листинга из фрагмента вывода терминала. Цвета по умолчанию остаются «как у остального текста»
    (``None``): листинг сам решает, каким цветом по умолчанию писать текст на своем фоне.
    """
    style = span.style
    foreground, background = theme.colors_of(style)
    if style.dim:
        foreground = _dimmed(foreground, background)
    explicit_foreground = style.fg is not None or style.inverse or style.dim
    explicit_background = style.bg is not None or style.inverse
    return CodeRun(
        span.text,
        color=_hex(foreground) if explicit_foreground else None,
        background=_hex(background) if explicit_background else None,
        bold=style.bold,
        italic=style.italic,
        underline=style.underline,
        strike=style.strike,
    )


def listing_from_terminal(
    source: Capture | Sequence[str],
    caption: RichText | None = None,
    *,
    theme: ThemeSpec = "light",
    label: str | None = None,
    line_numbers: bool | None = None,
    **run_options: Any,
) -> Listing:
    """
    Листинг с выводом терминала: текст остается текстом (его можно выделить и найти), цвета и начертание
    сохраняются фрагментами. Подпись - «Листинг N», как у любого листинга.

    Цвета берутся из темы, поэтому нужна тема, подходящая к фону листинга: по умолчанию светлая (``"light"``),
    чтобы цветной текст читался на белом. Для темного вида в документе лучше рисунок (``figure_from_terminal``).
    Цвет текста по умолчанию в листинге не задается, он остается как у остальных листингов документа.

    Если задана команда, она запускается в терминале шириной ``LISTING_COLUMNS`` (64) колонки, чтобы строки не
    переносились на странице; другая ширина задается параметром ``columns``.

    Если вывод длиннее экрана, по умолчанию сохраняются и строки, ушедшие вверх; ``capture_visible_only=True``
    оставляет только видимый экран (для программ, которые рисуют окно целиком).

    Параметры запуска уходят в ``termsnap.run``. Переменные окружения добавляются через
    ``extra_env={"ИМЯ": "значение"}`` (остальное окружение процесса остается); ``env`` - окружение целиком, оно
    заменяет текущее, и без системных переменных (``PATH``, ``SYSTEMROOT`` в Windows) программа может не запуститься.
    """
    termsnap = _termsnap()
    if not isinstance(source, str) and isinstance(source, Sequence):
        run_options.setdefault("columns", LISTING_COLUMNS)
    capture = _capture(source, run_options)
    palette = termsnap.get_theme(theme)
    lines = [tuple(_run(span, palette) for span in line.spans) for line in capture.lines]
    return Listing.styled(lines or [()], caption, label=label, line_numbers=line_numbers)


def figure_from_terminal(
    source: Capture | Sequence[str],
    caption: RichText,
    *,
    theme: ThemeSpec = "dark",
    fonts: FontSpec | None = None,
    font_size: float = 14,
    scale: int = 2,
    padding: int = 16,
    line_spacing: float = 1.25,
    label: str | None = None,
    width_cm: float | None = None,
    **run_options: Any,
) -> Figure:
    """
    Скриншот терминала: рисунок PNG в памяти (файлов на диске нет) с подписью «Рисунок N».

    ``theme``, ``fonts``, ``font_size``, ``scale``, ``padding`` и ``line_spacing`` - параметры
    рисования termsnap (см. ``termsnap.png.render_png``): тему можно задать именем, словарем или ``Theme``, шрифт -
    именем семейства или списком предпочтительных, ``padding`` - поля в пикселях (можно уменьшить или обнулить).
    Эмодзи и редкие символы рисуются запасными шрифтами автоматически. Остальные параметры (в том числе
    ``columns`` и ``rows`` - размер терминала) уходят в ``termsnap.run``. Переменные окружения добавляются через
    ``extra_env={"ИМЯ": "значение"}`` (остальное окружение процесса остается); ``env`` - окружение целиком, оно
    заменяет текущее, и без системных переменных (``PATH``, ``SYSTEMROOT`` в Windows) программа может не запуститься.
    ``capture_visible_only=True`` оставляет на рисунке только видимый экран, без строк, ушедших вверх при
    прокрутке (так выглядит скриншот окна).
    """
    _termsnap()
    try:
        from termsnap.png import render_png
    except ImportError as error:
        raise ImportError("Для скриншотов нужен Pillow: pip install studen-doc[terminal]") from error
    capture = _capture(source, run_options)
    options: dict[str, Any] = {
        "theme": theme,
        "font_size": font_size,
        "scale": scale,
        "padding": padding,
        "line_spacing": line_spacing,
    }
    if fonts is not None:
        options["fonts"] = fonts
    image = io.BytesIO(render_png(capture.lines, **options))
    return Figure(image, caption, label=label, width_cm=width_cm)
