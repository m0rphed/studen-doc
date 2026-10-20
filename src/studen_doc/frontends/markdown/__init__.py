"""
Фронтенд Markdown: текст .md -> разделы и блоки модели отчета.

Разбор делает pandoc (формат ``PANDOC_FORMAT``: CommonMark и явный список расширений), здесь только обход
его AST и превращение узлов в модель. Устройство пакета:

* ``pandoc_ast`` - запуск pandoc, проверка версии, ``Attr`` (атрибуты блока) и общие помощники;
* ``options`` - типизированные значения атрибутов (``width=10cm``, ``highlight=true``);
* ``substitutions`` - блоки и значения из Python (``::: insert``, ``[]{var=...}``);
* ``inlines``, ``blocks``, ``tables`` - превращение узлов pandoc в инлайны, блоки и таблицы модели;
* ``structure`` - заголовки -> разделы и подразделы; ``meta`` - блок YAML; ``document`` - точки входа;
  ``report`` - отчет целиком из файлов.

Договоренности поверх Markdown:

    # Цель работы               раздел верхнего уровня; имя раздела - ключ правил оформления
    ## Подраздел                подразделы любой глубины
    # Название {.appendix status=обязательное}      приложение (буква ставится автоматически)
    # Описание данных {rule="Основная часть"}     заголовок свой, оформление - по правилу другого раздела

    ::: toc                      оглавление (необязательно: levels=3 title=...)
    :::
    ::: pagebreak                разрыв страницы
    :::
    ::: keep-with-next           абзацы внутри не отрываются от следующего блока (вопрос перед ответом)
    :::

    ![Подпись](x.png){#fig:x width=10cm}          рисунок: id - метка, width - cm, mm, in или pt
    $$ a = b $$ {#eq:a}                           формула; с id нумеруется
    ::: where                                     пояснения к формуле над ним: определения "символ: описание"
    $y$
    :   фактическое значение
    :::
    ``` {#lst:a .python .numberLines caption="Подпись" highlight=true}     листинг (file=путь вместо текста)
    ```
    ::: {.table #tbl:x widths="6,2" font-size=12}  таблица с подписью (абзац внутри), меткой и размерами
    Подпись

    | A | B |
    |---|---|
    | 1 | 2 |
    :::
    [](#fig:x)                                    ссылка на номер по метке

Смешивание с Python (аргументы ``inserts`` и ``variables`` у ``parse_markdown`` и ``Report.from_markdown``):

    ::: {.insert name=metrics}                    сюда подставится блок или список блоков inserts["metrics"]
    :::
    R^2 = []{var=r2 format=".3f"}                 сюда подставится variables["r2"], отформатированное как в format()

Блок метаданных YAML в начале файла (все ключи необязательны):

    ---
    title: ЛР4. Регрессия         свойства документа
    author: О. Н. Молодец
    style: suai                   имя стиля, зарегистрированного через register_style
    title_page:                   тип из register_title_page и поля этого титульного листа
      type: suai
      student_name: О. Н. Молодец
      group: "4318"
    ---
"""

from studen_doc.errors import MarkdownError
from studen_doc.frontends.markdown.document import (
    ParsedDocument,
    parse_inline_markdown,
    parse_markdown,
    parse_markdown_text,
)
from studen_doc.frontends.markdown.pandoc_ast import PANDOC_FORMAT
from studen_doc.frontends.markdown.report import load_report

__all__ = [
    "PANDOC_FORMAT",
    "MarkdownError",
    "ParsedDocument",
    "load_report",
    "parse_inline_markdown",
    "parse_markdown",
    "parse_markdown_text",
]
