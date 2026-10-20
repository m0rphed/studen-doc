"""
Шаблон лабораторной в Markdown + расчет в Python: подгонка кривой scipy, числа и формула подставляются в текст.

Файл ``markdown/curve_fit.md`` читается как обычный документ, а вместо ``::: {.insert ...}`` попадают блоки
из расчета: таблица из массива numpy, таблица параметров (pandas), формула с найденными коэффициентами и
рисунок. Листинг ядра подгонки подключен прямо из файла (``file=../listings/curve_fit_core.py``).
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import curve_fit

from studen_doc import Formula, Report, figure_from_matplotlib, format_value, table_from
from studen_doc.universities.suai import TitlePageSUAI

plt.switch_backend("Agg")

HERE = Path(__file__).parent
TRUE_PARAMS = (3.0, 1.2, 0.4)  # амплитуда, скорость затухания, фон
MEASUREMENTS = 25


def model(x, a, k, c):
    return a * np.exp(-k * x) + c


def tex(value: float, spec: str = ".2f") -> str:
    """
    Число для формулы LaTeX: десятичная запятая в фигурных скобках.
    """
    return format_value(value, spec).replace(",", "{,}")


def build_report() -> Report:
    rng = np.random.default_rng(7)
    x = np.linspace(0, 5, MEASUREMENTS)
    y = model(x, *TRUE_PARAMS) + rng.normal(0, 0.08, x.size)

    params, covariance = curve_fit(model, x, y, p0=(1.0, 1.0, 0.0))
    errors = np.sqrt(np.diag(covariance))
    a, k, c = params
    fitted = model(x, *params)
    residuals = y - fitted
    r2 = 1 - (residuals**2).sum() / ((y - y.mean()) ** 2).sum()
    shapiro_p = stats.shapiro(residuals).pvalue
    half_life = np.log(2) / k
    half_life_err = half_life * errors[1] / k  # относительная погрешность та же, что у k

    figure, (top, bottom) = plt.subplots(2, 1, figsize=(6.5, 5), sharex=True, height_ratios=[3, 1])
    top.plot(x, y, "o", label="измерения")
    top.plot(x, fitted, "r-", label="подгонка")
    top.set(ylabel="y")
    top.legend()
    bottom.bar(x, residuals, width=0.12, color="0.5")
    bottom.axhline(0, color="black", linewidth=0.8)
    bottom.set(xlabel="x, с", ylabel="остаток")
    figure.tight_layout()

    inserts = {
        "data_table": table_from(
            np.column_stack([x, y, fitted])[:8],
            columns=["x, с", "y", "y подгонки"],
            caption="Первые восемь измерений и значения модели",
            label="tbl:data",
            float_format=".3f",
        ),
        "params_table": table_from(
            pd.DataFrame(
                {
                    "Параметр": ["a (амплитуда)", "k (затухание)", "c (фон)"],
                    "Значение": params,
                    "Ошибка": errors,
                    "Истинное": TRUE_PARAMS,
                }
            ),
            caption="Параметры модели",
            label="tbl:params",
            float_format=".3f",
            col_widths_cm=[6, 3.5, 3.5, 3.5],
        ),
        "fit_formula": Formula(
            rf"y(x) = {tex(a)}\,e^{{-{tex(k)}\,x}} + {tex(c)}",
            label="eq:fit",
            where={"x": "время, с", "y": "измеряемая величина"},
        ),
        "fit_plot": figure_from_matplotlib(
            figure, "Данные, подобранная кривая и остатки", label="fig:fit", width_cm=13
        ),
    }
    plt.close(figure)

    variables = {
        "n": x.size,
        "x_min": x.min(),
        "x_max": x.max(),
        "r2": r2,
        "rmse": np.sqrt((residuals**2).mean()),
        "shapiro_p": shapiro_p,
        "normality": "согласуются с нормальным распределением" if shapiro_p >= 0.05 else "отличаются от нормальных",
        "half_life": half_life,
        "half_life_err": half_life_err,
    }
    title_page = TitlePageSUAI(
        student_name="О. Н. Молодец",
        group="4318",
        year=2026,
        subject="ИНТЕЛЛЕКТУАЛЬНЫЕ ИНФОРМАЦИОННЫЕ СИСТЕМЫ",
        teacher_name="Иванов М. М.",
        teacher_position="Ассистент",
        work_number=6,
        work_title="ПОДГОНКА ЭКСПОНЕНЦИАЛЬНОЙ ЗАВИСИМОСТИ",
    )
    return Report.from_markdown(HERE / "markdown" / "curve_fit.md", title_page=title_page, inserts=inserts, variables=variables)


if __name__ == "__main__":
    print("saved", build_report().build_to_docx(HERE / "demo_curve_fit.docx"))
