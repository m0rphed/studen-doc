import dataclasses

import pytest

from helpers import png
from studen_doc import (
    Bullets,
    Figure,
    Formula,
    Listing,
    ListItem,
    Md,
    Numbered,
    P,
    Ref,
    Report,
    Subsection,
    Table,
)
from studen_doc.errors import ResolveError
from studen_doc.ir import (
    RAppendixHeading,
    RFigure,
    RFormula,
    RHeading,
    RList,
    RListing,
    RParagraph,
    RTable,
)
from studen_doc.universities.suai import SUAI


def numbers(resolved, kind):
    return [n.number.display for n in resolved.nodes if getattr(n, "number", None) and n.number.kind == kind]


def sample(style=SUAI) -> Report:
    report = Report(style)
    report.add_section("Цель работы", P("текст"))
    report.add_section(
        "Ход работы",
        Subsection("Первый", Figure(png(), "а", label="fig:a"), Subsection("Вложенный", P("x"))),
        Subsection("Второй", Figure(png(), "б", label="fig:b"), Table(["x"], [["1"]], caption="т", label="tab:t")),
    )
    report.add_section("Ход работы", Figure(png(), "в", label="fig:c"))
    report.add_section("Первое", Figure(png(), "г", label="fig:d"), rule="Приложение", status="справочное")
    report.add_section("Второе", Figure(png(), "д"), rule="Приложение")
    return report


def test_heading_numbers():
    headings = [(n.level, n.number, n.title) for n in sample().resolve().nodes if isinstance(n, RHeading)]
    assert headings == [
        (1, None, "Цель работы"),
        (1, "1", "Ход работы"), (2, "1.1", "Первый"), (3, "1.1.1", "Вложенный"), (2, "1.2", "Второй"),
        (1, "2", "Ход работы"),
    ]


def test_continuous_numbering_uses_seq_fields_except_in_appendices():
    resolved = sample().resolve()
    figures = [n.number for n in resolved.nodes if isinstance(n, RFigure)]
    assert [(f.display, f.use_seq) for f in figures] == [
        ("1", True), ("2", True), ("3", True), ("А.1", False), ("Б.1", False)]
    assert len({f.bookmark for f in figures}) == 5


def test_section_scope_numbering_is_static_and_restarts_per_section():
    resolved = sample(SUAI.evolve(numbering={"scope": "section"})).resolve()
    figures = [n.number for n in resolved.nodes if isinstance(n, RFigure)]
    assert [(f.display, f.use_seq) for f in figures] == [
        ("1.1", False), ("1.2", False), ("2.1", False), ("А.1", False), ("Б.1", False)]


def test_appendix_heading_keeps_title_only_when_it_differs():
    appendices = [n for n in sample().resolve().nodes if isinstance(n, RAppendixHeading)]
    assert [(a.letter, a.title, a.status) for a in appendices] == [("А", "Первое", "справочное"), ("Б", "Второе", None)]


def test_labels_map_to_numbers():
    resolved = sample().resolve()
    assert resolved.labels["fig:b"].display == "2"
    assert resolved.labels["tab:t"].kind == "table"


def test_unknown_reference_names_the_label():
    report = Report(SUAI)
    report.add_section("Вывод", P("см. ", Ref("fig:нет"), Md(" и [](#tab:тоже)")))
    with pytest.raises(ResolveError) as error:
        report.resolve()
    assert "fig:нет" in str(error.value) and "tab:тоже" in str(error.value)


def test_duplicate_label_is_rejected():
    report = Report(SUAI)
    report.add_section("Вывод", Figure(png(), "a", label="x"), Figure(png(), "b", label="x"))
    with pytest.raises(ResolveError, match="уже используется"):
        report.resolve()


def test_forward_references_are_allowed():
    report = Report(SUAI)
    report.add_section("Вывод", P(Md("раньше: [](#fig:later)")), Figure(png(), "потом", label="fig:later"))
    assert report.resolve().labels["fig:later"].display == "1"


def test_formula_is_numbered_only_with_label_or_flag():
    report = Report(SUAI)
    report.add_section("Вывод", Formula("a", label="eq:a"), Formula("b"), Formula("c", numbered=True),
                       Formula("d", label="eq:d", numbered=False))
    formulas = [n for n in report.resolve().nodes if isinstance(n, RFormula)]
    assert [f.number.display if f.number else None for f in formulas] == ["1", None, "2", None]


def test_table_and_listing_without_caption_take_no_number():
    report = Report(SUAI)
    report.add_section("Вывод", Table(["a"], [["1"]]), Listing("x"), Table(["a"], [["1"]], caption="с"))
    nodes = report.resolve().nodes
    assert next(n.number for n in nodes if isinstance(n, RTable)) is None
    assert [n.number.display for n in nodes if isinstance(n, RTable) and n.number] == ["1"]


def test_listing_flags_fall_back_to_style():
    style = SUAI.evolve(listing={"line_numbers": True, "highlight": False})
    report = Report(style)
    report.add_section("Вывод", Listing("x"), Listing("y", line_numbers=False, highlight=True))
    first, second = (n for n in report.resolve().nodes if isinstance(n, RListing))
    assert (first.line_numbers, first.highlight) == (True, False)
    assert (second.line_numbers, second.highlight) == (False, True)


def test_markdown_cells_are_parsed_and_numeric_cells_detected():
    report = Report(SUAI)
    report.add_section("Вывод", Table([Md("**A**"), "B"], [["1,5", "текст"], [2, Md("$x$")]]))
    table = next(n for n in report.resolve().nodes if isinstance(n, RTable))
    assert [c.numeric for c in table.rows[0]] == [True, False]
    assert [c.numeric for c in table.rows[1]] == [True, False]


def test_lists_become_nested_items():
    report = Report(SUAI)
    report.add_section("Вывод", Bullets(["а", ListItem("б", ["б1", "б2"])]), Numbered(["x"], marker="а)"))
    bullets, numbered = (n for n in report.resolve().nodes if isinstance(n, RList))
    assert bullets.marker == "bullet" and numbered.marker == "a)"
    assert [len(i.children) for i in bullets.items] == [0, 2]


def test_paragraph_block_becomes_a_resolved_paragraph():
    report = Report(SUAI)
    report.add_section("Вывод", P("строка"))
    assert isinstance(report.resolve().nodes[-1], RParagraph)


def test_resolved_report_is_immutable():
    resolved = sample().resolve()
    with pytest.raises(dataclasses.FrozenInstanceError):
        resolved.title = "x"  # type: ignore[misc]


def test_resolved_report_lists_unique_formulas_in_document_order():
    from studen_doc import Math

    report = Report(SUAI)
    report.add_section(
        "Вывод",
        P("до ", Math("a"), " и ", Math("b"), " и снова ", Math("a")),
        Formula("F", where=[("s", Md("пояснение $d$"))]),
        Table([Md("$h$")], [[Md("$c$")]]),
        Bullets([Md("$i$"), ListItem(Md("$j$"), [Md("$k$")])]),
    )
    assert report.resolve().formulas == ("a", "b", "F", "s", "d", "h", "c", "i", "j", "k")
