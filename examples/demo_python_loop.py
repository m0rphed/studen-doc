"""
Чистый Python DSL: отчет по нескольким наборам данных собирается циклом, Markdown-файлов нет.

Сильные стороны такого подхода - всё, что генерируется: подраздел, рисунок, таблица и формула на каждый
набор данных, метки (``fig:alpha``, ``tbl:beta``) из f-строк, выводы по условию (значим ли наклон), сводная
таблица и ранжирование. Данные - polars и numpy, статистика - scipy, рисунки - matplotlib.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from scipy import stats

from studen_doc import (
    Bullets,
    Formula,
    ListItem,
    Md,
    Numbered,
    P,
    Report,
    Subsection,
    figure_from_matplotlib,
    format_value,
    listing_from_callable,
    table_from,
)
from studen_doc.universities.suai import SUAI, TitlePageSUAI

plt.switch_backend("Agg")

HERE = Path(__file__).parent
SAMPLES = 60
ALPHA = 0.05

#: Набор -> (свободный член, наклон, шум): истинные параметры, по которым генерируются данные.
DATASETS = {
    "alpha": (1.0, 2.0, 1.5),
    "beta": (4.0, -0.8, 2.0),
    "gamma": (2.0, 0.05, 3.0),
}
NAMES = {"alpha": "Альфа", "beta": "Бета", "gamma": "Гамма"}


def make_frame(seed: int, intercept: float, slope: float, noise: float) -> pl.DataFrame:
    """
    Синтетический набор: отклик линейно зависит от x плюс гауссов шум.
    """
    rng = np.random.default_rng(seed)
    x = rng.uniform(0, 10, SAMPLES)
    return pl.DataFrame({"x": x, "y": intercept + slope * x + rng.normal(0, noise, SAMPLES)})


def tex(value: float, spec: str = ".2f") -> str:
    """
    Число для формулы LaTeX: десятичная запятая в фигурных скобках, чтобы после нее не было пробела.
    """
    return format_value(value, spec).replace(",", "{,}")


def p_text(p: float) -> str:
    """
    p-значение для текста: очень малые значения не округляются до нуля.
    """
    return "< 0,0001" if p < 1e-4 else format_value(p, ".4f")


def scatter_with_fit(frame: pl.DataFrame, fit, title: str):
    figure, axes = plt.subplots(figsize=(5.5, 3.4))
    axes.scatter(frame["x"], frame["y"], s=14, alpha=0.7)
    line = np.array([frame["x"].min(), frame["x"].max()])
    axes.plot(line, fit.intercept + fit.slope * line, "r-", linewidth=1.5)
    axes.set(xlabel="x", ylabel="y", title=title)
    figure.tight_layout()
    return figure


def dataset_section(key: str, seed: int) -> tuple[Subsection, dict]:
    frame = make_frame(seed, *DATASETS[key])
    fit = stats.linregress(frame["x"].to_numpy(), frame["y"].to_numpy())
    sign = "+" if fit.intercept >= 0 else "-"
    significant = fit.pvalue < ALPHA
    figure = scatter_with_fit(frame, fit, f"Набор {NAMES[key]}")
    section = Subsection(
        f"Набор «{NAMES[key]}»",
        P(
            Md(
                f"Набор **{NAMES[key]}** содержит {frame.height} наблюдений; выборочный коэффициент корреляции "
                f"$r$ = {format_value(fit.rvalue, '.3f')}. Описательная статистика приведена в таблице "
                f"[](#tbl:{key}), диаграмма рассеяния с прямой регрессии — на рисунке [](#fig:{key})."
            )
        ),
        table_from(
            frame.describe().rename({"statistic": "Показатель"}),
            caption=f"Описательная статистика набора «{NAMES[key]}»",
            label=f"tbl:{key}",
            float_format=".2f",
            col_widths_cm=[5, 4, 4],
        ),
        figure_from_matplotlib(figure, f"Диаграмма рассеяния: набор «{NAMES[key]}»", label=f"fig:{key}", width_cm=12),
        P(Md(f"Прямая регрессии задается формулой [](#eq:{key}).")),
        Formula(
            rf"y = {tex(fit.intercept)} {sign} {tex(abs(fit.slope))}\,x",
            label=f"eq:{key}",
            where={"x": "независимая переменная", "y": "прогнозируемый отклик"},
        ),
        Bullets(
            [
                f"наклон: {format_value(fit.slope, '.3f')} ± {format_value(fit.stderr, '.3f')}",
                f"p-значение наклона: {p_text(fit.pvalue)}",
                "наклон статистически значим" if significant else "наклон статистически не значим",
            ]
        ),
    )
    plt.close(figure)
    summary = {
        "Набор": NAMES[key],
        "n": frame.height,
        "Наклон": fit.slope,
        "r": fit.rvalue,
        "p": fit.pvalue,
        "Значим": "да" if significant else "нет",
    }
    return section, summary


def build_report() -> Report:
    sections, summaries = zip(*(dataset_section(key, seed) for seed, key in enumerate(DATASETS)), strict=True)
    summary = pl.DataFrame(summaries)
    ranking = summary.sort(pl.col("r").abs(), descending=True)

    report = Report(SUAI, title="Линейная регрессия на нескольких наборах", author="О. Н. Молодец")
    report.add_title_page(
        TitlePageSUAI(
            student_name="О. Н. Молодец",
            group="4318",
            year=2026,
            subject="ИНТЕЛЛЕКТУАЛЬНЫЕ ИНФОРМАЦИОННЫЕ СИСТЕМЫ",
            teacher_name="Иванов М. М.",
            teacher_position="Ассистент",
            work_number=5,
            work_title="ЛИНЕЙНАЯ РЕГРЕССИЯ НА НЕСКОЛЬКИХ НАБОРАХ ДАННЫХ",
        )
    )
    report.add_toc()
    report.add_section(
        "Цель работы",
        P(Md(f"Оценить линейную зависимость $y$ от $x$ на {len(DATASETS)} наборах данных и сравнить силу связи.")),
    )
    report.add_section(
        "Ход работы",
        P(Md("Для каждого набора построены описательная статистика, диаграмма рассеяния и прямая регрессии.")),
        *sections,
        Subsection(
            "Сводка",
            P(Md("Результаты по всем наборам собраны в таблице [](#tbl:summary).")),
            table_from(
                summary,
                caption="Сводка по наборам данных",
                label="tbl:summary",
                float_format={
                    "Наклон": ".3f",
                    "r": ".3f",
                    "p": p_text,
                },
            ),
            P("Наборы по убыванию силы связи (модуля коэффициента корреляции):"),
            Numbered(
                [
                    ListItem(
                        f"{row['Набор']}: r = {format_value(row['r'], '.3f')}",
                        [f"наклон {format_value(row['Наклон'], '.3f')}", f"значим: {row['Значим']}"],
                    )
                    for row in ranking.iter_rows(named=True)
                ],
                marker="a)",
            ),
        ),
    )
    report.add_section(
        "Вывод",
        P(
            Md(
                f"Сильнее всего связь выражена в наборе **{ranking['Набор'][0]}** "
                f"($r$ = {format_value(ranking['r'][0], '.3f')}), слабее всего — в наборе **{ranking['Набор'][-1]}**."
            )
        ),
    )
    report.add_section(
        "Исходный код",
        P("Функция генерации данных:"),
        listing_from_callable(make_frame, "Генерация синтетического набора", label="lst:make"),
        rule="Приложение",
        status="справочное",
    )
    return report


if __name__ == "__main__":
    print("saved", build_report().build_to_docx(HERE / "demo_python_loop.docx"))
