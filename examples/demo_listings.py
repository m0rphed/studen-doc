"""
Листинги кода: как они выглядят по умолчанию, с номерами строк и с подсветкой синтаксиса (pygments).
"""

from pathlib import Path

from studen_doc import Listing, Md, P, Report, Subsection
from studen_doc.universities.suai import SUAI

CODE_DIR = Path(__file__).with_name("listings")


def read_code(name: str) -> str:
    """
    Текст листинга из файла в ``examples/listings``.
    """
    return (CODE_DIR / name).read_text(encoding="utf-8")


PYTHON = read_code("fit_regression.py")
SQL = read_code("scores_by_group.sql")
CPP = read_code("mean.cpp")
BASH = read_code("build_all.sh")
JSON = read_code("experiment.json")
LONG = read_code("evaluate_models.py")
TABS_AND_LONG_LINE = read_code("tabs_and_long_line.py")


def build_report() -> Report:
    report = Report(SUAI, title="Листинги")
    report.add_section(
        "Ход работы",
        P(
            Md(
                "Ниже показаны варианты оформления листингов. По умолчанию (листинг [](#lst:plain)) — чёрно-белая рамка "
                "моноширинным шрифтом: так принято в отчётах по ГОСТ. Номера строк и подсветка включаются для "
                "конкретного листинга ([](#lst:numbers), [](#lst:color)) либо для всего документа через стиль."
            )
        ),
        Subsection(
            "По умолчанию",
            Listing(PYTHON, caption="Python без подсветки и номеров строк", label="lst:plain", language="python"),
        ),
        Subsection(
            "Номера строк",
            Listing(
                PYTHON, caption="Те же строки, с номерами", label="lst:numbers", language="python", line_numbers=True
            ),
        ),
        Subsection(
            "Подсветка синтаксиса",
            Listing(PYTHON, caption="Python с подсветкой", label="lst:color", language="python", highlight=True),
            Listing(
                SQL, caption="SQL с подсветкой и номерами строк", language="sql", highlight=True, line_numbers=True
            ),
            Listing(CPP, caption="C++ с подсветкой", language="cpp", highlight=True),
            Listing(BASH, caption="Bash с подсветкой", language="bash", highlight=True),
            Listing(JSON, caption="JSON с подсветкой", language="json", highlight=True),
        ),
        Subsection(
            "Длинный листинг, табуляция и длинная строка",
            P(Md("Листинг [](#lst:long) не помещается на странице целиком — рамка продолжается на следующей.")),
            Listing(
                LONG,
                caption="Длинный листинг с подсветкой и номерами строк",
                label="lst:long",
                language="python",
                highlight=True,
                line_numbers=True,
            ),
            Listing(TABS_AND_LONG_LINE, caption="Табуляция и перенос длинной строки", language="python"),
            Listing("print('листинг без подписи и без номера')", language="python"),
        ),
    )
    return report


if __name__ == "__main__":
    print("saved", build_report().build_to_docx(Path(__file__).with_name("demo_listings.docx")))
