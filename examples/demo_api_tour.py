"""
Обзор API на одном отчете: то, чего нет в других демо.

* свой стиль через ``gost_732(...)`` и ``evolve`` (моноширинный шрифт листингов - Cascadia Code);
* ссылки на блоки без меток (``table.ref``, ``figure.ref``) и по строковой метке (``Ref``);
* узлы текста ``Math``, ``Code``, ``LineBreak`` и ``P.md``;
* таблица из массива numpy с выравниванием столбцов, размером шрифта и форматом чисел;
* листинг из файла, разрыв страницы, перечисление с кириллической буквой;
* раздел со своим заголовком и правилом оформления основной части.
"""

from pathlib import Path

import matplotlib
import numpy as np

import studen_doc.universities  # noqa: F401 - регистрирует стиль suai
from studen_doc import (
    B,
    Code,
    Formula,
    I,
    LineBreak,
    Math,
    Numbered,
    P,
    PageBreak,
    Ref,
    Report,
    Subsection,
    figure_from_matplotlib,
    listing_from_file,
    table_from,
)
from studen_doc.style import style_named

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).parent

#: Стиль вуза с другим моноширинным шрифтом: нужен шрифт Cascadia Code на компьютере читателя.
STYLE = style_named("suai").evolve(text={"mono_font_name": "Cascadia Code"})


def build_report() -> Report:
    rng = np.random.default_rng(7)
    table = table_from(
        rng.normal(size=(5, 3)),
        columns=["Параметр", "Оценка", "Ошибка"],
        caption="Оценки параметров",
        label="tbl:params",
        float_format=".2f",
        align=["left", "right", "right"],
        font_size_pt=11,
        col_widths_cm=[5, 4, 4],
    )
    figure = figure_from_matplotlib(_plot(rng), "Выборка из стандартного нормального распределения")
    listing = listing_from_file(
        HERE / "listings" / "fit_regression.py",
        "Подгонка модели регрессии",
        label="lst:fit",
        highlight=True,
        line_numbers=True,
    )

    report = Report(STYLE, title="Обзор API", author="О. Н. Молодец")
    report.add_toc()
    report.add_section(
        "Введение",
        P(
            "Формула ",
            Math(r"y = \beta_0 + \beta_1 x"),
            " оценивается функцией ",
            Code("fit"),
            ": ",
            B("жирным"),
            " и ",
            I("курсивом"),
            ".",
            LineBreak(),
            "Перенос строки внутри абзаца.",
        ),
        P.md("Тот же текст через `P.md`: $y = \\beta_0$, **жирный**, *курсив*."),
    )
    report.add_section(
        "Описание данных",
        P(
            "Оценки приведены в таблице ",
            table.ref,
            ", выборка показана на рисунке ",
            figure.ref,
            ", расчет - в листинге ",
            Ref("lst:fit"),
            ".",
        ),
        table,
        figure,
        Subsection(
            "Расчет",
            P("Остатки модели ", Math(r"e_i = y_i - \hat y_i"), " вычисляются по формуле (", Ref("eq:resid"), ")", "."),
            Formula(r"e_i = y_i - \hat y_i", label="eq:resid", where={"y_i": "наблюдение", r"\hat y_i": "прогноз"}),
            listing,
        ),
        PageBreak(),
        P("После разрыва страницы идет перечисление русскими буквами:"),
        Numbered(["подготовка данных;", "подгонка модели;", "проверка остатков."], marker="а)"),
        rule="Основная часть",
    )
    return report


def _plot(rng: np.random.Generator) -> plt.Figure:
    figure, axes = plt.subplots(figsize=(5, 3))
    axes.hist(rng.normal(size=300), bins=20, color="#4477aa")
    axes.set(xlabel="Значение", ylabel="Число наблюдений")
    return figure


if __name__ == "__main__":
    print("saved", build_report().build_to_docx(HERE / "demo_api_tour.docx"))
