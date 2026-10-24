"""
Мост между Python-данными и блоками отчета: таблицы из pandas, polars и numpy, рисунки matplotlib, листинги кода.

Ни одна из этих библиотек не нужна пакету: функции работают с объектами по их интерфейсу (утиная типизация),
поэтому импортировать matplotlib, pandas, polars или numpy здесь не требуется.

* ``tables`` - ``table_from`` и адаптеры источников данных;
* ``figures`` - ``figure_from_matplotlib``;
* ``listings`` - ``listing_from_callable`` и ``listing_from_file``;
* ``terminal`` - ``listing_from_terminal`` и ``figure_from_terminal`` (нужен ``studen-doc[terminal]``).
"""

from studen_doc.integrations.figures import figure_from_matplotlib
from studen_doc.integrations.listings import listing_from_callable, listing_from_file
from studen_doc.integrations.tables import table_from
from studen_doc.integrations.terminal import figure_from_terminal, listing_from_terminal

__all__ = [
    "figure_from_matplotlib",
    "figure_from_terminal",
    "listing_from_callable",
    "listing_from_file",
    "listing_from_terminal",
    "table_from",
]
