# studen-doc

Осторожно: IT'S 70% AI-SLOP

> **Studen'** (СтуденЬ): холодный заливной суп.
> documentation (*otchetiki*) as code

Библиотека Python для оформления отчетов `.docx` по **ГОСТ 7.32-2017** и в соотв.
со принятыми стилями вузов (пока что только СПбГУАП).
Содержимое описывается кодом или Markdown, а нумерация, ссылки,
формулы и список источников собираются автоматически - так, чтобы
в Word все было "живым": поля, нумерованные списки, формулы, которые можно править.

## Что можно делать (фитчи)

- Оформление ориентированное на ГОСТ 7.32-2017: заголовки, приложения со статусом,
подписи "Рисунок 1 - ...", оглавление.
  Стиль - неизменяемые данные, свой получается через `SUAI.evolve(...)`; вуз добавляется регистрацией и описанием отдельного стиля.
- Два способа писать: Python (блоки) и Markdown (CommonMark + pandoc), их можно комбинировать.
- Формулы LaTeX превращаются в нативные формулы Word (OMML); номера и ссылки - настоящие поля SEQ и REF.
- Таблицы из pandas, polars, numpy и обычных данных; рисунки matplotlib; листинги с подсветкой синтаксиса.
- Список использованных источников: ссылки `[1]` в тексте, записи из BibTeX, CSL JSON и других файлов pandoc
  по стилю CSL, который проверен на примерах самого ГОСТ 7.32.

## Установка

```bash
pip install git+https://github.com/m0rphed/studen-doc
uv add git+https://github.com/m0rphed/studen-doc
```

Требуется Python 3.12+; pandoc приходит вместе с пакетом (`pypandoc-binary`). Подсветка листингов:
`pip install "studen-doc[highlight]"`.

## Пример

```python
import studen_doc.universities  # noqa: F401 - регистрирует стиль и титульный лист ГУАП
from studen_doc import Formula, Listing, P, Report, Source, Sources, Subsection, table_from
from studen_doc.universities.suai import SUAI, TitlePageSUAI

table = table_from(
    {"Модель": ["Линейная", "Лес"], "R2": [0.725, 0.881]},
    caption="Метрики моделей", label="tbl:r2", float_format=".3f",
)
formula = Formula(
    r"R^2 = 1 - rac{SS_{res}}{SS_{tot}}", label="eq:r2",
    where={"SS_{res}": "сумма квадратов остатков", "SS_{tot}": "полная сумма квадратов"},
)

report = Report(SUAI, title="ЛР4", author="О. Н. Молодец")
report.add_title_page(TitlePageSUAI(
    student_name="О. Н. Молодец", group="9000", year=3026, subject="ИНТЕЛЛЕКТУАЛЬНЫЕ ИНФОРМАЦИОННЫЕ СИСТЕМЫ",
    teacher_name="Иванов A. I.", teacher_position="Ассистент", work_number=4, work_title="СРАВНЕНИЕ МОДЕЛЕЙ",
))
report.add_toc()
report.add_section("Цель работы", P.md("Сравнить модели по метрике $R^2$ [@sklearn]."))
report.add_section(
    "Ход работы",
    Subsection(
        "Метрики",
        P("Метрика задана формулой ", formula.ref, ", результаты - в таблице ", table.ref, "."),
        formula,
        table,
        Listing("model.fit(X, y)", caption="Обучение модели", language="python"),
    ),
)
report.add_section("Список использованных источников", Sources([
    Source("sklearn", "Pedregosa F. et al. Scikit-learn: machine learning in Python // JMLR. - 2011. - Vol. 12."),
]))
report.build_to_docx("report.docx")
```

Markdown с метаданными (`style: suai`, `bibliography: refs.bib`) читается так же: `Report.from_markdown("report.md")`.
Готовые примеры - в папке [`examples/`](examples/).

[-> читать подробнее](docs/usage.md)

## WHY

Потому что!
> 1. Многие вещи просто неудобно делать сначала в python, а потом вручную в docx вставлять.
> 2. К сожалению, многие вузы требуют оформлять в MS Word отчёты. MS Word - проприетарный редактор (интересно, а откуда у всех берётся лицензия? неужели...)

## Why So Sloppy?

Студенты не пишут отчёты вручную.
> В лучшем случае: их *иногда* читают. Если бы мы предположили, что > 50% студенческих работ оформляют ai инструментами (оптимистичная оценка... - скорее всего уже около 80%) - то получается что каждый ai агент/модель постоянно перерасходует 10-20% токенов на то, чтобы собрать .docx в соотвествии с неуклюжим промптингом студента и попыткой попасть в ГОСТ - если бы люди/ai просто использовали plain-text форматы - всё было бы проще... И, МОЖЕТ БЫТЬ, у людей оставалось бы время / желание почитать содержание той ерунды которая в итоге окажется в конечном .docx.

Автоматизация через подход "otchetiki-as-code" (documentation as code) в этой задаче сам напрашивается. Этот мини-проект не подразумевает обязательное использование совместно с ai инструментами, но он скорее всего поможет собирать отчёты в коде быстрее и эффективнее (ai пмощник тоже будет рад).

_ _ _

[ai в обучении, MIT](https://aiandeducation.mit.edu/report/)
