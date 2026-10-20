"""
Список использованных источников по ГОСТ 7.32 (6.16) и ссылки на источники [1] в тексте.

Две сборки:

* ``build_report`` - Markdown со ссылками ``[@ключ]`` и библиографией из ``markdown/references.bib``: записи оформляет
  pandoc (стиль ГОСТ Р 7.0.5-2008), номера идут в порядке первой ссылки;
* ``build_manual_report`` - то же без файла библиографии: записи написаны вручную, а ссылки заданы узлами ``Cite``.
"""

from pathlib import Path

import studen_doc.universities  # noqa: F401 - регистрирует стиль suai из sources.md
from studen_doc import Citation, Cite, Md, P, Report, Source, Sources
from studen_doc.universities.suai import SUAI

HERE = Path(__file__).parent


def build_report() -> Report:
    return Report.from_markdown(HERE / "markdown" / "sources.md")


def build_manual_report() -> Report:
    report = Report(SUAI, title="Обзор источников вручную", author="О. Н. Молодец")
    report.add_toc()
    report.add_section(
        "Введение",
        P("Сравнение статистических критериев начато с Z-теста ", Cite("ztest"), "."),
        P(
            "Подробнее о проверке гипотез - в методических материалах ",
            Cite(Citation("hse", "с. 4"), "zharinov"),
            " и в учебном пособии ",
            Cite("vainshtein"),
            ".",
        ),
        P(Md("Те же ссылки можно писать в `Md`: [@vainshtein; @ztest]. Первый источник в списке - по первой ссылке.")),
    )
    report.add_section(
        "Список использованных источников",
        Sources(
            [
                Source("zharinov", "Жаринов О. О. Методические материалы к практической работе №5. ГУАП, 2026. 13 с."),
                Source("ztest", "Z-тест. Материал из Википедии. URL: https://ru.wikipedia.org/wiki/Z-тест (дата обращения: 15.07.2026)."),
                Source("hse", "Проверка статистических гипотез. URL: http://math-info.hse.ru/f/hypo-test.pdf (дата обращения: 15.07.2026)."),
                Source("vainshtein", Md("Вайнштейн И. И. и др. *Теория вероятностей и математическая статистика*: лабораторный практикум. Красноярск: СФУ, 2012.")),
                "Запись без ключа: на нее нельзя сослаться, но она есть в списке.",
            ]
        ),
    )
    return report


if __name__ == "__main__":
    print("saved", build_report().build_to_docx(HERE / "demo_sources.docx"))
    print("saved", build_manual_report().build_to_docx(HERE / "demo_sources_manual.docx"))
