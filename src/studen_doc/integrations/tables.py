"""
Таблицы из pandas, polars, numpy и обычных Python-структур.

Данные превращаются в ``Grid`` (названия столбцов и строки) адаптерами: по одному на источник. Адаптер
узнает «свои» данные по интерфейсу (утиная типизация), поэтому сами библиотеки импортировать не нужно.
"""

from __future__ import annotations

import numbers
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from studen_doc.model.blocks import Table
from studen_doc.model.inline import RichText
from studen_doc.numfmt import format_value
from studen_doc.types import Align

#: Формат чисел: строка для ``format()`` либо функция значение -> текст.
type NumberFormat = str | Callable[[float], str]


@dataclass(frozen=True, slots=True)
class Grid:
    """
    Данные таблицы в общем виде, до форматирования. ``columns`` - названия столбцов, если источник их знает.
    """

    rows: list[list[Any]]
    columns: list[str] | None = None


#: Адаптер: ``Grid`` из данных, которые он понимает, иначе ``None``.
type Adapter = Callable[[Any], Grid | None]


def _polars_frame(data: Any) -> Grid | None:
    if not (hasattr(data, "iter_rows") and hasattr(data, "columns")):
        return None
    return Grid([list(row) for row in data.iter_rows()], [str(name) for name in data.columns])


def _pandas_frame(data: Any) -> Grid | None:
    if not (hasattr(data, "itertuples") and hasattr(data, "columns")):
        return None
    rows = [list(row) for row in data.itertuples(index=False, name=None)]
    return Grid(rows, [str(name) for name in data.columns])


def _numpy_array(data: Any) -> Grid | None:
    if not (hasattr(data, "tolist") and hasattr(data, "ndim")):
        return None
    if data.ndim != 2:
        raise ValueError(f"Нужен двумерный массив, получен ndim={data.ndim}")
    rows = [list(row) for row in data.tolist()]
    return Grid(rows, [f"x{number}" for number in range(1, len(rows[0]) + 1)] if rows else [])


def _columns_mapping(data: Any) -> Grid | None:
    """
    ``{"столбец": [значения]}``.
    """
    if not isinstance(data, Mapping):
        return None
    return Grid([list(row) for row in zip(*data.values(), strict=True)], [str(name) for name in data])


def _records(data: Any) -> Grid | None:
    """
    ``[{"столбец": значение}, ...]``: названия столбцов - ключи первой записи.
    """
    if not (isinstance(data, Sequence) and data and isinstance(data[0], Mapping)):
        return None
    names = list(data[0])
    return Grid([[record[name] for name in names] for record in data], [str(name) for name in names])


def _rows(data: Any) -> Grid | None:
    """
    ``[[значения], ...]``: названия столбцов обязательно задаются через ``columns``.
    """
    if not isinstance(data, Sequence) or isinstance(data, str | bytes):
        return None
    return Grid([list(row) for row in data])


#: Адаптеры в порядке проверки: специфичные для библиотек раньше общих структур Python.
_ADAPTERS: tuple[Adapter, ...] = (_polars_frame, _pandas_frame, _numpy_array, _columns_mapping, _records, _rows)


def to_grid(data: Any, *, index: bool = False) -> Grid:
    """
    Табличные данные любого поддерживаемого вида в ``Grid``.
    """
    if hasattr(data, "to_frame"):  # pandas.Series и polars.Series ведут себя как таблица из одного столбца
        data = data.to_frame()
    if index and hasattr(data, "reset_index"):  # индекс pandas становится первым столбцом
        data = data.reset_index()
    for adapter in _ADAPTERS:
        if (grid := adapter(data)) is not None:
            return grid
    raise TypeError(f"Не знаю, как сделать таблицу из {type(data).__name__}")


def table_from(
    data: Any,
    *,
    columns: Sequence[str] | None = None,
    index: bool = False,
    caption: RichText | None = None,
    label: str | None = None,
    float_format: NumberFormat | Mapping[str, NumberFormat] = ".3f",
    decimal: str = ",",
    na: str = "",
    col_widths_cm: Sequence[float] | None = None,
    align: Sequence[Align | None] | None = None,
    font_size_pt: float | None = None,
) -> Table:
    """
    Блок ``Table`` из табличных данных:

    - pandas ``DataFrame`` и ``Series``, polars ``DataFrame`` и ``Series``;
    - массив numpy (двумерный; названия столбцов - в ``columns``, иначе ``x1``, ``x2``...);
    - словарь «столбец -> значения», список словарей, список строк (тогда ``columns`` обязателен).

    ``index=True`` добавляет индекс pandas первым столбцом. Вещественные числа форматирует ``float_format``
    (одна строка формата для всех, функция или словарь «имя столбца -> формат») с разделителем ``decimal``;
    целые не меняются; пропуски (None, NaN, pandas NA) заменяются на ``na``.
    """
    grid = to_grid(data, index=index)
    names = _column_names(grid, columns)
    formats = float_format if isinstance(float_format, Mapping) else dict.fromkeys(names, float_format)
    text_rows = [
        [_cell(value, formats.get(name, ".3f"), decimal, na) for name, value in zip(names, row, strict=True)]
        for row in grid.rows
    ]
    return Table(
        names,
        text_rows,
        caption=caption,
        label=label,
        col_widths_cm=col_widths_cm,
        align=align,
        font_size_pt=font_size_pt,
    )


def _column_names(grid: Grid, columns: Sequence[str] | None) -> list[str]:
    """
    Названия столбцов: заданные явно важнее тех, что знает источник; число значений в строках должно совпасть.
    """
    names = [str(name) for name in columns] if columns is not None else grid.columns
    if not names:
        raise ValueError("Не заданы названия столбцов: передайте columns=[...]")
    if any(len(row) != len(names) for row in grid.rows):
        raise ValueError(f"Число значений в строках не совпадает с числом столбцов ({len(names)})")
    return names


def _cell(value: Any, number_format: NumberFormat, decimal: str, na: str) -> str:
    if _is_missing(value):
        return na
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, numbers.Integral):
        return str(int(value))
    if isinstance(value, numbers.Real):
        number = float(value)
        if callable(number_format):
            return number_format(number)
        return format_value(number, number_format, decimal=decimal)
    return str(value)


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    try:
        return bool(value != value)  # NaN не равен самому себе
    except TypeError:  # pandas.NA: сравнение не приводится к bool
        return True
