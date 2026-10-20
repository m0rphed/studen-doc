"""
Списки: настоящие списки Word (маркеры и номера рисует Word),
вложенность, перезапуск нумерации.
"""

from pathlib import Path

from studen_doc import Bullets, ListItem, Numbered, P, Report, ReportStyle, Subsection
from studen_doc.universities.suai import SUAI

LONG_TEXT = (
    "пункт с длинным текстом, который не помещается в одну строку и переносится: строки-продолжения "
    "возвращаются к левому полю, а маркер стоит на абзацном отступе, как требует ГОСТ 7.32"
)


def build_report(style: ReportStyle = SUAI) -> Report:
    report = Report(style, title="Списки")
    report.add_section(
        "Ход работы",
        P("Списки оформляются настоящими средствами Word: после правки в Word номера пересчитываются сами."),
        Subsection(
            "Маркированный список (тире)",
            Bullets(
                [
                    "линейная регрессия;",
                    LONG_TEXT + ";",
                    ListItem("полиномиальная регрессия:", ["степень 2;", "степень 6."]),
                    "дерево решений.",
                ]
            ),
        ),
        Subsection(
            "Нумерованный список",
            Numbered(
                [
                    "подготовка данных;",
                    LONG_TEXT + ";",
                    ListItem("построение моделей:", ["обучение;", "оценка."]),
                    "сравнение.",
                ]
            ),
            P("Следующий список начинается с единицы заново:", keep_with_next=True),
            Numbered(["первый;", "второй;", "третий."], marker="1."),
        ),
        Subsection(
            "Буквенный список",
            P("До семи пунктов — настоящий список Word (а, б, в, ...); внутри — цифры."),
            Numbered(
                [
                    "исходные данные;",
                    ListItem("подготовка:", ["очистка;", "разбиение."]),
                    "модели;",
                    "метрики.",
                ],
                marker="a)",
            ),
            P(
                "Длиннее семи пунктов Word нумеровал бы «з», «о», «ч», «ы», которых ГОСТ не допускает, поэтому здесь "
                "буквы по ГОСТ (а, б, в, г, д, е, ж, и, к) записаны в текст пунктов:",
                keep_with_next=True,
            ),
            Numbered([f"пункт {i};" for i in range(1, 10)], marker="a)"),
        ),
    )
    return report


if __name__ == "__main__":
    here = Path(__file__)
    print("saved", build_report().build_to_docx(here.with_name("demo_lists.docx")))
    # Старый формат: маркер печатается в тексте пункта, отступы заданы у абзаца напрямую.
    static_style = SUAI.evolve(lists={"word_numbering": False})
    print("saved", build_report(static_style).build_to_docx(here.with_name("demo_lists_static.docx")))
