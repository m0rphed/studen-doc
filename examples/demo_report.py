"""
Демонстрация: отчёт ГУАП с формулами, рисунками, таблицами, листингом, списками и ссылками.
"""

from pathlib import Path

from studen_doc import (
    Bullets,
    Figure,
    Formula,
    Listing,
    ListItem,
    Md,
    Numbered,
    P,
    Report,
    ReportStyle,
    Subsection,
    Table,
)
from studen_doc.universities.suai import SUAI, TitlePageSUAI

THE_FILE: Path = Path(__file__)
SHOTS = THE_FILE.parent / "images"


def build_report(style: ReportStyle = SUAI) -> Report:
    title = TitlePageSUAI(
        student_name="О. Н. Молодец",
        group="4318",
        year=2026,
        subject="ИНТЕЛЛЕКТУАЛЬНЫЕ ИНФОРМАЦИОННЫЕ СИСТЕМЫ",
        teacher_name="Иванов М. М.",
        teacher_position="Ассистент",
        work_number=4,
        work_title="ЗАДАЧА РЕГРЕССИИ В ORANGE",
    )
    report = Report(style, title="ЛР4. Регрессия", author="О. Н. Молодец")
    report.add_title_page(title)
    report.add_toc()

    report.add_section(
        "Цель работы",
        P(Md("Изучить построение моделей регрессии и сравнить их по метрикам MSE, MAE и $R^2$ на тестовой выборке.")),
    )

    report.add_section(
        "Ход работы",
        P(
            Md(
                "Качество моделей оценивается по формулам ([](#eq:mse)) и ([](#eq:r2)); "
                "результаты сведены в таблицу [](#tab:res)."
            )
        ),
        Subsection(
            "Метрики качества",
            Formula(
                r"\mathrm{MSE}=\frac{1}{n}\sum_{i=1}^{n}\left(y_i-\hat y_i\right)^2",
                label="eq:mse",
                where={
                    "y_i": "фактическое значение",
                    r"\hat y_i": "прогноз модели",
                    "n": "размер выборки",
                },
            ),
            Formula(r"R^2 = 1-\frac{\sum_{i=1}^{n}(y_i-\hat y_i)^2}{\sum_{i=1}^{n}(y_i-\bar y)^2}", label="eq:r2"),
            Formula(r"\hat\beta=(X^{T}X)^{-1}X^{T}y"),
        ),
        Subsection(
            "Рабочий процесс",
            P(
                Md(
                    "Схема показана на рисунке [](#fig:wf); для оценки использован **Test and Score** "
                    "(режим *Test on test data*)."
                )
            ),
            Figure(SHOTS / "01a-workflow-all.png", "Рабочий процесс в Orange", label="fig:wf", width_cm=15),
            Subsection(
                "Результаты",
                Table(
                    ["Модель", "RMSE", "R²"],
                    [
                        ["Линейная", "4,714", "0,725"],
                        ["Случайный лес", "3,101", "0,881"],
                    ],
                    caption="Оценка моделей на тестовой выборке",
                    label="tab:res",
                    col_widths_cm=[8, 4, 4],
                ),
                P(Md("Код расчёта приведён в листинге [](#lst:fit).")),
                Listing(
                    "from sklearn.linear_model import LinearRegression\n\n"
                    "model = LinearRegression()\nmodel.fit(X_train, y_train)\nprint(model.score(X_test, y_test))",
                    caption="Обучение линейной регрессии",
                    label="lst:fit",
                    language="python",
                ),
                Bullets(["линейная регрессия;", "полиномиальная регрессия;", "дерево решений."]),
                Numbered(
                    [
                        "подготовка данных;",
                        ListItem(
                            "построение моделей:",
                            ["обучение;", "оценка;"],
                        ),
                        "сравнение.",
                    ],
                    marker="a)",
                ),
            ),
        ),
    )
    report.add_section("Вывод", P(Md("Лучшей оказалась модель случайного леса ($R^2 = 0{,}881$).")))
    report.add_section(
        "Исходные данные",
        P.md("Исходные данные приведены в файле `housing.tab`."),
        rule="Приложение",
        status="справочное",
    )
    return report


if __name__ == "__main__":
    print(
        "saved",
        build_report().build_to_docx(
            THE_FILE.with_name(
                "demo_report.docx"
            )
        )
    )
