"""
Заголовки и правила оформления разделов.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal

from studen_doc.style.evolve import Evolvable
from studen_doc.types import Align

# Буквы приложений по ГОСТ 7.32: без Ё, З, Й, О, Ч, Ь, Ы, Ъ.
APPENDIX_LETTERS = "АБВГДЕЖИКЛМНПРСТУФХЦШЩЭЮЯ"


@dataclass(frozen=True, slots=True, kw_only=True)
class HeadingStyle(Evolvable):
    """
    Оформление заголовка одного уровня.
    """

    size_pt: float = 14
    bold: bool = True
    italic: bool = False
    caps: bool = False              # ПРОПИСНЫМИ
    align: Align = "left"
    first_indent_cm: float = 1.25   # абзацный отступ
    before_pt: float = 12
    after_pt: float = 12
    line_spacing: float = 1.5
    keep_with_next: bool = True
    page_break_before: bool = False


@dataclass(frozen=True, slots=True, kw_only=True)
class SectionRule(Evolvable):
    """
    Как оформляется раздел с данным именем (Введение, Ход работы, ...).
    """

    numbered: bool = False                  # «1 Ход работы» против «Введение»
    structural: bool = True                 # структурный элемент: заголовок по HeadingsStyle.structural
    page_break_before: bool | None = None   # None -> брать значение по умолчанию заголовка
    appendix: bool = False                  # «ПРИЛОЖЕНИЕ А» + буквенная нумерация внутри


#: Структурные элементы по ГОСТ 7.32-2017.
GOST_732_SECTIONS: Mapping[str, SectionRule] = {
    "Реферат": SectionRule(),
    "Содержание": SectionRule(),
    "Термины и определения": SectionRule(),
    "Перечень сокращений и обозначений": SectionRule(),
    "Введение": SectionRule(),
    "Основная часть": SectionRule(numbered=True, structural=False),
    "Заключение": SectionRule(),
    "Список использованных источников": SectionRule(),
    "Ссылки на источники": SectionRule(),
    "Приложение": SectionRule(appendix=True),
}


#: Имя раздела: известные структурные элементы (ГОСТ 7.32 и лабораторные работы ГУАП) подсказывает IDE,
#: но подойдет и любая своя строка - раздел без правила оформляется по ``HeadingsStyle.default_rule``.
type SectionName = (
    Literal[
        "Реферат",
        "Содержание",
        "Термины и определения",
        "Перечень сокращений и обозначений",
        "Введение",
        "Основная часть",
        "Цель работы",
        "Ход работы",
        "Контрольные вопросы",
        "Вывод",
        "Заключение",
        "Список использованных источников",
        "Ссылки на источники",
        "Приложение",
    ]
    | str
)


#: Статус приложения, печатается в скобках под его номером. Подсказка IDE, но подойдет любая строка.
type AppendixStatus = Literal["обязательное", "справочное", "рекомендуемое"] | str


@dataclass(frozen=True, slots=True, kw_only=True)
class HeadingsStyle(Evolvable):
    structural: HeadingStyle = HeadingStyle(align="center", caps=True, first_indent_cm=0)
    level1: HeadingStyle = HeadingStyle()
    level2: HeadingStyle = HeadingStyle()
    level3: HeadingStyle = HeadingStyle()
    number_separator: str = " "
    appendix_word: str = "ПРИЛОЖЕНИЕ"
    appendix_gap_pt: float = 6.0 # интервал после «ПРИЛОЖЕНИЕ А» и после строки «(обязательное)»
    rules: Mapping[str, SectionRule] = field(default_factory=lambda: dict(GOST_732_SECTIONS))
    default_rule: SectionRule = SectionRule()

    def rule_for(self, section_name: str) -> SectionRule:
        return self.rules.get(section_name, self.default_rule)

    def for_level(self, level: int) -> HeadingStyle:
        """
        Заголовок подраздела: 1 — раздел, 2 — подраздел, 3 и глубже — пункт.
        """
        match level:
            case 1:
                return self.level1
            case 2:
                return self.level2
            case _:
                return self.level3
