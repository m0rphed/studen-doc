"""
Титульные листы: диспетчеризация по типу.

Титульный лист — данные (подкласс ``TitlePage``, зарегистрированный под именем через
``register_title_page``). Для DOCX его вёрстку регистрирует тот, кто объявил класс данных (вуз, кафедра):

    @render_title.register
    def _(title: TitlePageSUAI, ctx: Context) -> None: ...

Для другого формата (typst, LaTeX) заводится аналогичная функция в его рендерере.
"""

from __future__ import annotations

from functools import singledispatch

from studen_doc.model.report import TitlePage
from studen_doc.render.docx.context import Context


@singledispatch
def render_title(title_page: TitlePage, ctx: Context) -> None:
    raise TypeError(
        f"Для {type(title_page).__name__} не зарегистрирована DOCX-вёрстка: "
        "используйте @render_title.register рядом с классом титульного листа"
    )
