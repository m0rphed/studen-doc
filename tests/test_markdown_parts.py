"""
Части фронтенда Markdown по отдельности: атрибуты, подстановки, структура, метаданные (pandoc не нужен).
"""

import pytest

from studen_doc import MarkdownError, P, Table
from studen_doc.frontends.markdown.meta import _coerce
from studen_doc.frontends.markdown.options import Options, parse_flag, parse_length_cm
from studen_doc.frontends.markdown.pandoc_ast import Attr, first_text, is_text_block
from studen_doc.frontends.markdown.structure import Heading, build_sections
from studen_doc.frontends.markdown.substitutions import Substitutions
from studen_doc.model import Section, Subsection, Toc


# ---------------------------------------------------------------------------------------- атрибуты
def test_attr_parses_pandoc_triplet_and_exposes_label():
    attr = Attr.parse(["fig:x", ["python", "numberLines"], [["width", "10cm"], ["caption", "Подпись"]]])
    assert attr.ident == "fig:x" and attr.label == "fig:x"
    assert attr.classes == ("python", "numberLines")
    assert attr.options.text("caption") == "Подпись"
    assert Attr.parse(["", [], []]).label is None


@pytest.mark.parametrize(
    ("text", "centimetres"),
    [("10cm", 10.0), ("100mm", 10.0), ("2in", 5.08), ("72pt", 2.54), ("7", 7.0), (" 3.5 cm ", 3.5)],
)
def test_lengths_are_converted_to_centimetres(text, centimetres):
    assert parse_length_cm(text) == pytest.approx(centimetres)


@pytest.mark.parametrize("text", ["50%", "cm", "10 km", "", "1,5"])
def test_bad_lengths_are_rejected(text):
    with pytest.raises(ValueError):
        parse_length_cm(text)


@pytest.mark.parametrize(("text", "flag"), [("true", True), ("yes", True), ("1", True), ("false", False), ("0", False)])
def test_flags(text, flag):
    assert parse_flag(text) is flag
    with pytest.raises(ValueError):
        parse_flag("maybe")


def test_options_getters_convert_types_and_return_defaults_for_missing_names():
    options = Options({"levels": "2", "font-size": "11.5", "highlight": "no", "width": "5cm", "widths": "3,5.5"})
    assert options.integer("levels", 3) == 2 and options.integer("other", 3) == 3
    assert options.number("font-size") == 11.5 and options.number("other") is None
    assert options.flag("highlight") is False and options.flag("other") is None
    assert options.length_cm("width") == 5.0 and options.length_cm("other") is None
    assert options.lengths_cm("widths", count=2) == (3.0, 5.5) and options.lengths_cm("other", count=2) is None
    assert options.text("levels") == "2" and options.text("other", "x") == "x"


@pytest.mark.parametrize(
    ("call", "message"),
    [
        (lambda o: o.integer("v", 1), r"v='abc': ожидалось целое число"),
        (lambda o: o.number("v"), r"v='abc': ожидалось число"),
        (lambda o: o.flag("v"), r"v='abc': ожидалось true или false"),
        (lambda o: o.length_cm("v"), r"v='abc': ожидались число и единица"),
        (lambda o: o.lengths_cm("v", count=2), r"v='abc': ожидался список из 2 длин"),
    ],
)
def test_options_errors_name_the_attribute_and_its_value(call, message):
    with pytest.raises(MarkdownError, match=message):
        call(Options({"v": "abc"}))


def test_lengths_must_match_the_requested_count():
    with pytest.raises(MarkdownError, match="список из 3 длин"):
        Options({"w": "1,2"}).lengths_cm("w", count=3)


# ------------------------------------------------------------------------------------- помощники AST
def test_text_blocks_and_first_text():
    para, plain, table = {"t": "Para", "c": ["a"]}, {"t": "Plain", "c": ["b"]}, {"t": "Table", "c": []}
    assert is_text_block(para) and is_text_block(plain) and not is_text_block(table)
    assert first_text([table, plain, para]) == ["b"] and first_text([table]) == ()


# ------------------------------------------------------------------------------------- подстановки
def test_substitutions_return_blocks_and_formatted_values():
    table = Table(["a"], [["1"]])
    substitutions = Substitutions({"one": table, "many": [P("x"), P("y")]}, {"r2": 0.8812, "n": 5}, decimal=",")
    assert substitutions.insert("one") == [table]
    assert substitutions.insert("many") == [P("x"), P("y")]
    assert substitutions.variable("r2", ".2f") == "0,88" and substitutions.variable("n") == "5"
    assert Substitutions(variables={"r2": 0.5}, decimal=".").variable("r2", ".1f") == "0.5"


def test_substitution_errors_list_what_was_passed():
    substitutions = Substitutions({"a": P("x")}, {"v": 1})
    with pytest.raises(MarkdownError, match=r"'b' не передан \(переданы: \['a'\]\)"):
        substitutions.insert("b")
    with pytest.raises(MarkdownError, match=r"'w' не передана \(переданы: \['v'\]\)"):
        substitutions.variable("w")


# ------------------------------------------------------------------------------------------ структура
def heading(level: int, title: str, *classes: str, **options: str) -> Heading:
    return Heading(level, title, classes, Options(options))


def test_build_sections_folds_headings_into_nested_subsections():
    items = [
        heading(1, "Ход работы"),
        P("а"),
        heading(2, "Один"),
        P("б"),
        heading(3, "Глубже"),
        P("в"),
        heading(2, "Два"),
    ]
    (section,) = build_sections(items)
    assert section == Section(
        "Ход работы",
        (P("а"), Subsection("Один", P("б"), Subsection("Глубже", P("в"))), Subsection("Два")),
    )


def test_appendix_class_makes_an_appendix_section_with_kind():
    (section,) = build_sections([heading(1, "Исходный код", "appendix", status="справочное"), P("т")])
    assert (section.rule_name, section.title, section.status) == ("Приложение", "Исходный код", "справочное")


def test_toc_is_allowed_between_sections_only():
    items = [Toc(None, levels=2), heading(1, "А"), P("т"), Toc(), heading(1, "Б")]
    assert [type(item).__name__ for item in build_sections(items)] == ["Toc", "Section", "Toc", "Section"]
    with pytest.raises(MarkdownError, match="Оглавление"):
        build_sections([heading(1, "А"), heading(2, "Под"), Toc()])


@pytest.mark.parametrize(
    ("items", "message"),
    [([P("т")], "до первого заголовка"), ([heading(2, "Под")], "первого уровня")],
)
def test_build_sections_requires_a_level_one_heading_first(items, message):
    with pytest.raises(MarkdownError, match=message):
        build_sections(items)


# ------------------------------------------------------------------------- приведение типов метаданных
@pytest.mark.parametrize(
    ("value", "hint", "expected"),
    [
        ("2026", int, 2026),
        ("4", int | str | None, 4),
        ("4а", int | str | None, "4а"),
        ("1.5", float, 1.5),
        ("true", bool, True),
        (False, bool, False),
        ("4318", str, "4318"),
    ],
)
def test_metadata_values_are_coerced_to_field_types(value, hint, expected):
    result = _coerce(value, hint)
    assert result == expected and type(result) is type(expected)


@pytest.mark.parametrize(("value", "hint"), [("abc", int), ("1.5", int), ("maybe", bool), (True, str)])
def test_metadata_values_of_wrong_type_are_rejected(value, hint):
    with pytest.raises(ValueError):
        _coerce(value, hint)


# --------------------------------------------------------------- таблицы, которых нет в нашем диалекте
def _cell(blocks=(), row_span=1, col_span=1):
    return [["", [], []], {"t": "AlignDefault"}, row_span, col_span, list(blocks)]


def _text(text):
    return {"t": "Plain", "c": [{"t": "Str", "c": text}]}


def _table(*, head_rows=1, foot_rows=0, cell=None, body_head_columns=0):
    """
    AST таблицы pandoc с одной колонкой; параметры включают конструкции, которые CommonMark-таблицы не создают.
    """
    cell = cell if cell is not None else _cell([_text("a")])
    row = [["", [], []], [cell]]
    return [
        ["", [], []],
        [None, []],
        [[{"t": "AlignDefault"}, {"t": "ColWidthDefault"}]],
        [["", [], []], [row] * head_rows],
        [[["", [], []], body_head_columns, [], [row]]],
        [["", [], []], [row] * foot_rows],
    ]


@pytest.mark.parametrize(
    ("parts", "message"),
    [
        (_table(foot_rows=1), "Подвал таблицы"),
        (_table(head_rows=0), "ровно одна строка заголовка"),
        (_table(head_rows=2), "ровно одна строка заголовка"),
        (_table(body_head_columns=1), "Заголовочные столбцы"),
        (_table(cell=_cell([_text("a")], row_span=2)), "Объединенные ячейки"),
        (_table(cell=_cell([_text("a"), _text("b")])), "один абзац текста"),
    ],
)
def test_table_constructs_outside_the_dialect_are_rejected(parts, message):
    from studen_doc.frontends.markdown.inlines import InlineConverter
    from studen_doc.frontends.markdown.tables import TableConverter

    with pytest.raises(MarkdownError, match=message):
        TableConverter(InlineConverter()).bare(parts)


def test_empty_cell_and_valid_handmade_table_are_converted():
    from studen_doc.frontends.markdown.inlines import InlineConverter
    from studen_doc.frontends.markdown.tables import TableConverter

    table = TableConverter(InlineConverter()).bare(_table(cell=_cell([])))
    assert table.header == ((),) and table.rows == [((),)]
