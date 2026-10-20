"""
Отчет целиком из файла Markdown: содержимое, стиль и титульный лист заданы в ``markdown/report.md``.

Стиль и титульный лист можно переопределить аргументами, например
``Report.from_markdown(path, style=SUAI.evolve(...), title_page=TitlePageSUAI(...))``.
"""

from pathlib import Path

import studen_doc.universities  # noqa: F401 - регистрирует стиль и титульный лист suai из report.md
from studen_doc import Report

HERE = Path(__file__).parent


def build_report() -> Report:
    return Report.from_markdown(HERE / "markdown" / "report.md")


if __name__ == "__main__":
    print("saved", build_report().build_to_docx(HERE / "demo_markdown.docx"))
