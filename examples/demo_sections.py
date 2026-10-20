"""
Нумерация «в пределах раздела» (1.1, 1.2), приложение с буквенной нумерацией и свой стиль через evolve.
"""

from pathlib import Path

from studen_doc import Figure, Formula, Md, P, Report, Subsection, Table
from studen_doc.universities.suai import SUAI

SHOTS = Path(__file__).parent / "images"

#: Свой стиль — «правки поверх пресета», вложенные поля задаются словарями.
STYLE = SUAI.evolve(
    numbering={"scope": "section"},
    page_numbers={"align": "right"},
)


def build_report() -> Report:
    report = Report(STYLE)
    report.add_section(
        "Ход работы",
        P(
            Md(
                "Формулы ([](#eq:a)), ([](#eq:b)) и ([](#eq:c)) набраны одним вызовом pandoc; "
                "рисунок [](#fig:x), таблица [](#tab:x)."
            )
        ),
        Subsection(
            "Формулы",
            Formula(r"R^2 = 1-\frac{\sum_{i=1}^{n}(y_i-\hat y_i)^2}{\sum_{i=1}^{n}(y_i-\bar y)^2}", label="eq:a"),
            Formula(r"\hat\beta=(X^{T}X)^{-1}X^{T}y", label="eq:b"),
            Formula(r"\mathrm{RMSE}=\sqrt{\frac{1}{n}\sum_{i=1}^{n}(y_i-\hat y_i)^2}", label="eq:c"),
            Formula(r"\begin{pmatrix} a & b \\ c & d \end{pmatrix}\begin{pmatrix} x \\ y \end{pmatrix}"),
        ),
        Subsection(
            "Номера по разделам",
            Figure(SHOTS / "10-poly-a.png", "Нумерация «1.1»", label="fig:x", width_cm=11),
            Table(["A", "B"], [["1", "2"]], caption="Нумерация «1.1»", label="tab:x"),
        ),
    )
    report.add_section(
        "Рисунки", Figure(SHOTS / "10-poly-a.png", "Рисунок в приложении", width_cm=8), rule="Приложение"
    )
    return report


if __name__ == "__main__":
    print("saved", build_report().build_to_docx(Path(__file__).with_name("demo_sections.docx")))
