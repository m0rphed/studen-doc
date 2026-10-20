"""
Смешанный пример: проза и формулы лежат в Markdown, а расчеты, таблицы и рисунки приходят из Python.

В ``markdown/ml_report.md`` на местах ``::: {.insert name=...}`` стоят блоки, которые строит этот файл
(таблицы из pandas, рисунок matplotlib, листинг с настоящим кодом), а на местах ``[]{var=...}`` - числа
из scikit-learn и scipy. Названия моделей, p-значения и вывод про значимость в тексте всегда совпадают
с расчетом: поменяйте данные, и отчет пересоберется сам.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.datasets import load_diabetes
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from studen_doc import Bullets, Report, figure_from_matplotlib, listing_from_callable, table_from
from studen_doc.universities.suai import TitlePageSUAI

plt.switch_backend("Agg")  # рисунки только в память, без окон

HERE = Path(__file__).parent
TEST_SIZE = 0.3


def fit_and_score(models, X_train, y_train, X_test, y_test):
    """
    Обучает модели и возвращает таблицу метрик и предсказания на тестовой выборке.
    """
    scores, predictions = {}, {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        predicted = model.predict(X_test)
        predictions[name] = predicted
        scores[name] = {
            "MSE": mean_squared_error(y_test, predicted),
            "MAE": mean_absolute_error(y_test, predicted),
            "R2": r2_score(y_test, predicted),
        }
    return pd.DataFrame(scores).T.rename_axis("Модель"), predictions


def residuals_figure(y_test, predicted, name):
    """
    Предсказание против факта и гистограмма остатков для одной модели.
    """
    figure, (left, right) = plt.subplots(1, 2, figsize=(9, 3.6))
    left.scatter(y_test, predicted, s=14, alpha=0.7)
    limits = [min(y_test.min(), predicted.min()), max(y_test.max(), predicted.max())]
    left.plot(limits, limits, "r--", linewidth=1)
    left.set(xlabel="Факт", ylabel="Прогноз", title=name)
    right.hist(y_test - predicted, bins=20, color="0.6", edgecolor="black")
    right.set(xlabel="Остаток", ylabel="Число наблюдений", title="Распределение остатков")
    figure.tight_layout()
    return figure


def build_report() -> Report:
    data = load_diabetes(as_frame=True)
    X, y = data.data, data.target
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=TEST_SIZE, random_state=0)
    models = {
        "линейная регрессия": LinearRegression(),
        "гребневая регрессия": Ridge(alpha=1.0),
        "случайный лес": RandomForestRegressor(n_estimators=100, random_state=0),
    }
    metrics, predictions = fit_and_score(models, X_train, y_train, X_test, y_test)

    ranking = metrics.sort_values("R2", ascending=False)
    best, second = ranking.index[0], ranking.index[1]
    residuals = y_test.to_numpy() - predictions[best]
    shapiro_p = stats.shapiro(residuals).pvalue
    wilcoxon_p = stats.wilcoxon(
        np.abs(y_test.to_numpy() - predictions[best]), np.abs(y_test.to_numpy() - predictions[second])
    ).pvalue

    linear = models["линейная регрессия"]
    coefficients = pd.DataFrame({"Признак": X.columns, "Коэффициент": linear.coef_})
    coefficients = coefficients.sort_values("Коэффициент", key=abs, ascending=False)

    figure = residuals_figure(y_test, predictions[best], best)
    inserts = {
        "code": listing_from_callable(fit_and_score, "Обучение и оценка моделей", label="lst:fit"),
        "metrics": table_from(
            ranking,
            index=True,
            caption="Метрики моделей на тестовой выборке",
            label="tbl:metrics",
            float_format={"MSE": ".1f", "MAE": ".2f", "R2": ".3f"},
            col_widths_cm=[7, 3, 3, 3],
        ),
        "residuals": figure_from_matplotlib(figure, f"Предсказания и остатки: {best}", label="fig:resid", width_cm=15),
        "top_features": Bullets(
            [
                f"{row['Признак']}: {row['Коэффициент']:+.1f}".replace(".", ",")
                for _, row in coefficients.head(3).iterrows()
            ]
        ),
        "coefficients": table_from(
            coefficients,
            caption="Коэффициенты линейной регрессии",
            label="tbl:coef",
            float_format=".1f",
            col_widths_cm=[8, 5],
        ),
    }
    plt.close(figure)

    variables = {
        "n_total": len(X),
        "n_features": X.shape[1],
        "n_train": len(X_train),
        "n_test": len(X_test),
        "best": best,
        "first": best,
        "second": second,
        "best_r2": ranking.loc[best, "R2"],
        "best_mae": ranking.loc[best, "MAE"],
        "shapiro_p": shapiro_p,
        "normality": "согласуются с нормальным распределением" if shapiro_p >= 0.05 else "отличаются от нормальных",
        "wilcoxon_p": wilcoxon_p,
        "verdict": "различие между ними статистически значимо"
        if wilcoxon_p < 0.05
        else "различие между ними незначимо",
    }
    title_page = TitlePageSUAI(
        student_name="О. Н. Молодец",
        group="4318",
        year=2026,
        subject="ИНТЕЛЛЕКТУАЛЬНЫЕ ИНФОРМАЦИОННЫЕ СИСТЕМЫ",
        teacher_name="Иванов М. М.",
        teacher_position="Ассистент",
        work_number=4,
        work_title="СРАВНЕНИЕ МОДЕЛЕЙ РЕГРЕССИИ",
    )
    return Report.from_markdown(HERE / "markdown" / "ml_report.md", title_page=title_page, inserts=inserts, variables=variables)


if __name__ == "__main__":
    print("saved", build_report().build_to_docx(HERE / "demo_ml_mixed.docx"))
