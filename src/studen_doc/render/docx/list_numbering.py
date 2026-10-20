"""
Списки Word: определения нумерации по стилю, экземпляры для каждого списка документа
и тексты маркеров для статического (старого) формата.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import assert_never

from docx.document import Document as DocxDocument

from studen_doc.ir import ListMarker, RListItem
from studen_doc.ooxml.numbering import LevelSpec, add_abstract_num, add_list_instance
from studen_doc.style import ReportStyle

#: Сколько уровней вложенности описано в определении списка.
LEVELS = 4

#: Буквенная нумерация Word (``russianLower``) совпадает с ГОСТ только на первых семи буквах: а б в г д е ж.
#: Дальше Word ставит "з", "о", "ч", "ы", которых ГОСТ 7.32 для перечислений не допускает.
WORD_LETTERS_MATCH_GOST = 7

#: Буквы для перечислений по ГОСТ 7.32: без ё, з, й, о, ч, ъ, ы, ь.
GOST_LETTERS = "абвгдежиклмнпрстуфхцшщэюя"

#: Неразрывный пробел между маркером и текстом пункта в статическом формате.
NBSP = "\u00a0"

#: Маркеры буквенных списков.
LETTER_MARKERS: tuple[ListMarker, ...] = ("a)", "a.")


def uses_word_numbering(marker: ListMarker, items: Sequence[RListItem]) -> bool:
    """
    Настоящий список Word, если он не противоречит ГОСТ;
    иначе - статические маркеры с буквами по ГОСТ.
    """
    return not (marker in LETTER_MARKERS and len(items) > WORD_LETTERS_MATCH_GOST)


def marker_text(marker: ListMarker, index: int, level: int, bullet: str) -> str:
    """
    Маркер пункта в статическом формате (печатается в тексте пункта): тире, "1)", "1.", "a)", "a.".
    Буква печатается русской по ГОСТ; вложенные буквенные списки нумеруются цифрами.
    """
    effective = "1)" if level > 0 and marker in LETTER_MARKERS else marker
    match effective:
        case "bullet":
            label = bullet
        case "1)" | "1.":
            label = f"{index}{effective[1]}"
        case "a)" | "a.":
            label = f"{GOST_LETTERS[(index - 1) % len(GOST_LETTERS)]}{effective[1]}"
        case _:
            assert_never(effective)
    return label + NBSP


def _twips(cm: float) -> int:
    return round(cm / 2.54 * 1440)


def _levels(marker: ListMarker, style: ReportStyle) -> list[LevelSpec]:
    """
    Уровни списка: маркер стоит на абзацном отступе,
    строки-продолжения возвращаются к левому полю.
    """
    first, nested = _twips(style.text.first_indent_cm), _twips(style.lists.nested_indent_cm)

    def level(index: int, num_format: str, text: str, font: str | None = None) -> LevelSpec:
        return LevelSpec(num_format, text, left_twips=nested * index, first_line_twips=first, font=font)

    match marker:
        case "bullet":
            return [level(i, "bullet", style.lists.bullet, style.text.font_name) for i in range(LEVELS)]
        case "1)" | "1.":
            return [level(i, "decimal", f"%{i + 1}{marker[1]}") for i in range(LEVELS)]
        case "a)" | "a.":
            nested_levels = [level(i, "decimal", f"%{i + 1})") for i in range(1, LEVELS)]  # внутри букв - цифры
            return [level(0, "russianLower", f"%1{marker[1]}"), *nested_levels]
        case _:
            assert_never(marker)


class ListNumbering:
    """
    Создает в документе определения списков
    (по одному на вид маркера) и новый экземпляр на каждый список.
    """

    def __init__(self, doc: DocxDocument, style: ReportStyle) -> None:
        self._doc = doc
        self._style = style
        self._abstract_ids: dict[ListMarker, int] = {}

    def new_instance(self, marker: ListMarker) -> int:
        """
        ``numId`` нового списка: нумерация в нем начинается с 1 независимо от предыдущих списков.
        """
        if marker not in self._abstract_ids:
            self._abstract_ids[marker] = add_abstract_num(self._doc, _levels(marker, self._style))
        return add_list_instance(self._doc, self._abstract_ids[marker], levels=LEVELS)
