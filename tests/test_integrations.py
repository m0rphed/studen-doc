import math

import pytest

from studen_doc import (
    Figure,
    Listing,
    Report,
    Table,
    figure_from_matplotlib,
    listing_from_callable,
    listing_from_file,
    table_from,
)
from studen_doc.numfmt import format_value
from studen_doc.universities.suai import SUAI


# -------------------------------------------------------------------------------------- числа
@pytest.mark.parametrize(
    ("value", "spec", "decimal", "expected"),
    [
        (0.88123, ".3f", ",", "0,881"),
        (0.88123, ".3f", ".", "0.881"),
        (12, "", ",", "12"),
        (1.5e-05, "", ",", "1,5e-05"),
        ("a.b", "", ",", "a.b"),
        (1234.5, ".1f", ",", "1234,5"),
    ],
)
def test_format_value_uses_decimal_separator_only_for_fractions(value, spec, decimal, expected):
    assert format_value(value, spec, decimal=decimal) == expected


# ------------------------------------------------------------------------------------ таблицы
def test_table_from_dict_list_of_dicts_and_rows():
    expected_rows = [["a", "1", "0,500"], ["b", "2", "1,250"]]
    by_columns = table_from({"имя": ["a", "b"], "n": [1, 2], "x": [0.5, 1.25]})
    by_records = table_from(
        [{"имя": "a", "n": 1, "x": 0.5}, {"имя": "b", "n": 2, "x": 1.25}], caption="Подпись", label="tab:r"
    )
    by_rows = table_from([["a", 1, 0.5], ["b", 2, 1.25]], columns=["имя", "n", "x"])
    for table in (by_columns, by_records, by_rows):
        assert table.header == ["имя", "n", "x"]
        assert table.rows == expected_rows
    assert (by_records.caption, by_records.label) == ("Подпись", "tab:r")


def test_table_from_formats_missing_values_and_per_column_formats():
    table = table_from(
        {"k": ["a", "b"], "p": [0.12345, None], "q": [3.14159, math.nan]},
        float_format={"p": ".2f", "q": lambda value: f"~{value:.1f}"},
        na="-",
    )
    assert table.rows == [["a", "0,12", "~3.1"], ["b", "-", "-"]]


def test_table_from_validates_input():
    with pytest.raises(ValueError, match="columns"):
        table_from([[1, 2]])
    with pytest.raises(ValueError, match="не совпадает"):
        table_from([[1, 2, 3]], columns=["a", "b"])
    with pytest.raises(TypeError, match="int"):
        table_from(5)


def test_table_from_numpy_pandas_and_polars():
    numpy = pytest.importorskip("numpy")
    pandas = pytest.importorskip("pandas")
    polars = pytest.importorskip("polars")

    array = table_from(numpy.array([[1.0, 2], [3, 4.5]]), columns=["a", "b"], float_format=".1f")
    assert array.rows == [["1,0", "2,0"], ["3,0", "4,5"]]
    assert table_from(numpy.zeros((1, 2))).header == ["x1", "x2"]
    with pytest.raises(ValueError, match="двумерный"):
        table_from(numpy.zeros(3))

    frame = pandas.DataFrame({"модель": ["A", "B"], "r2": [0.9, float("nan")], "n": [10, 20]}, index=["i", "j"])
    assert table_from(frame).rows == [["A", "0,900", "10"], ["B", "", "20"]]
    assert table_from(frame, index=True).header == ["index", "модель", "r2", "n"]
    assert table_from(frame["r2"]).header == ["r2"]
    assert table_from(pandas.DataFrame({"a": pandas.array([1, None], dtype="Int64")})).rows == [["1"], [""]]

    polars_frame = polars.DataFrame({"модель": ["A", "B"], "r2": [0.9, None], "n": [10, 20]})
    assert table_from(polars_frame).rows == [["A", "0,900", "10"], ["B", "", "20"]]
    assert table_from(polars_frame["r2"]).header == ["r2"]


# ------------------------------------------------------------------------------------ рисунки
def test_figure_from_matplotlib_gives_png_in_memory_and_can_be_built_twice(tmp_path):
    pyplot = pytest.importorskip("matplotlib.pyplot")
    figure, axes = pyplot.subplots(figsize=(3, 2))
    axes.plot([1, 2, 3], [1, 4, 9])
    block = figure_from_matplotlib(axes, "Квадраты", label="fig:sq", width_cm=8)
    pyplot.close(figure)
    assert isinstance(block, Figure) and block.label == "fig:sq" and block.width_cm == 8
    assert block.source.read(8) == b"\x89PNG\r\n\x1a\n"  # type: ignore[union-attr]

    report = Report(SUAI)
    report.add_section("Ход работы", block)
    for name in ("a.docx", "b.docx"):  # поток перематывается: отчет можно собрать повторно
        report.build_to_docx(tmp_path / name)
    from docx import Document

    assert len(Document(str(tmp_path / "b.docx")).inline_shapes) == 1


# ------------------------------------------------------------------------------------ листинги
def sample_function(x):
    """
    Пример.
    """
    return x * 2


def test_listing_from_callable_dedents_source():
    listing = listing_from_callable(sample_function, "Функция", label="lst:f")
    assert isinstance(listing, Listing)
    assert listing.code.startswith("def sample_function(x):")
    assert listing.language == "python" and listing.label == "lst:f"


def test_listing_from_file_slices_lines_and_guesses_language(tmp_path):
    path = tmp_path / "q.sql"
    path.write_text("a\nb\nc\nd\n", encoding="utf-8")
    assert listing_from_file(path, lines=(2, 3)).code == "b\nc"
    assert listing_from_file(path).language == "sql"
    assert listing_from_file(path, language="text").language == "text"
    assert listing_from_file(path).code == "a\nb\nc\nd\n"


def test_table_from_result_is_a_normal_table():
    assert isinstance(table_from({"a": [1]}), Table)


# ------------------------------------------------------------- адаптеры без настоящих библиотек
class FakePolars:
    columns = ("a", "b")

    def iter_rows(self):
        return iter([(1, 2.5), (3, None)])


class FakePandas:
    columns = ("x", "y")

    def __init__(self, with_index=False):
        self.with_index = with_index

    def reset_index(self):
        return FakePandas(with_index=True)

    def itertuples(self, index, name):
        assert index is False and name is None
        return iter([("i", 1, 2)] if self.with_index else [(1, 2)])


class FakeSeries:
    def to_frame(self):
        return FakePolars()


class FakeArray:
    ndim = 2

    def tolist(self):
        return [[1, 2, 3]]


def test_adapters_recognise_sources_by_interface_without_importing_their_libraries():
    from studen_doc.integrations.tables import to_grid

    assert to_grid(FakePolars()).columns == ["a", "b"]
    assert to_grid(FakePandas()).rows == [[1, 2]]
    assert to_grid(FakeSeries()).columns == ["a", "b"]  # Series -> таблица из одного столбца через to_frame
    assert to_grid(FakeArray()).columns == ["x1", "x2", "x3"]


def test_pandas_index_is_added_only_on_request():
    from studen_doc.integrations.tables import to_grid

    assert to_grid(FakePandas(), index=False).columns == ["x", "y"]
    assert to_grid(FakePandas(), index=True).rows == [["i", 1, 2]]


def test_records_take_columns_from_the_first_record_and_missing_keys_fail():
    from studen_doc.integrations.tables import to_grid

    grid = to_grid([{"a": 1, "b": 2}, {"a": 3, "b": 4}])
    assert (grid.columns, grid.rows) == (["a", "b"], [[1, 2], [3, 4]])
    with pytest.raises(KeyError):
        to_grid([{"a": 1, "b": 2}, {"a": 3}])


@pytest.mark.parametrize("data", ["строка", b"bytes", 3.5, None, object()])
def test_things_that_are_not_tables_are_rejected(data):
    from studen_doc.integrations.tables import to_grid

    with pytest.raises(TypeError, match="Не знаю, как сделать таблицу"):
        to_grid(data)


def test_empty_rows_still_need_column_names():
    assert table_from([], columns=["a"]).rows == []
    with pytest.raises(ValueError, match="columns"):
        table_from([])
