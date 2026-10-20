import pytest
from docx import Document

from helpers import instructions, png
from studen_doc import Figure, Formula, Listing, Md, P, Report, Table
from studen_doc.errors import ResolveError
from studen_doc.ir import RParagraph
from studen_doc.model.inline import BlockRef, Ref, Text
from studen_doc.universities.suai import SUAI


def paragraph_inlines(resolved):
    return [node.inlines for node in resolved.nodes if isinstance(node, RParagraph)]


def test_ref_property_returns_block_ref_to_the_same_object():
    figure = Figure(png(), "Схема")
    assert isinstance(figure.ref, BlockRef) and figure.ref.target is figure
    assert Table(["a"], []).ref.target is not None and Listing("x").ref and Formula("x").ref


def test_block_ref_resolves_to_the_blocks_number_without_labels(tmp_path):
    figure = Figure(png(), "Схема")
    table = Table(["a"], [["1"]], caption="Итоги")
    listing = Listing("x = 1", "Код")
    formula = Formula("E=mc^2", numbered=True)
    report = Report(SUAI)
    report.add_section(
        "Ход работы",
        P("Рис. ", figure.ref, ", табл. ", table.ref, ", лист. ", listing.ref, ", ф. ", formula.ref, "."),
        figure,
        table,
        listing,
        formula,
    )
    resolved = report.resolve()
    (inlines,) = paragraph_inlines(resolved)
    numbers = [resolved.labels[node.label].display for node in inlines if isinstance(node, Ref)]
    assert numbers == ["1", "1", "1", "1"]
    assert [label for label in resolved.labels if not label.startswith("\0")] == []  # публичных меток нет

    doc = Document(str(report.build_to_docx(tmp_path / "r.docx")))
    assert sum(text.startswith("REF ") for text in instructions(doc)) == 4


def test_forward_reference_and_mixing_with_string_labels():
    later = Figure(png(), "потом")
    labeled = Figure(png(), "с меткой", label="fig:named")
    report = Report(SUAI)
    report.add_section("Ход работы", P("Вперед: ", later.ref, " и ", Ref("fig:named"), "."), labeled, later)
    resolved = report.resolve()
    (inlines,) = paragraph_inlines(resolved)
    displays = [resolved.labels[node.label].display for node in inlines if isinstance(node, Ref)]
    assert displays == ["2", "1"]
    assert "fig:named" in resolved.labels


def test_block_ref_survives_md_two_pass_resolve():
    figure = Figure(png(), "Схема")
    report = Report(SUAI)
    report.add_section("Ход работы", P(Md("Смотри *рисунок* "), figure.ref), figure)
    parsed = {"Смотри *рисунок* ": (Text("Смотри рисунок "),)}  # любой разбор: оба прохода видят один объект блока
    resolved = report.resolve(inline_parser=lambda sources: parsed)
    (inlines,) = paragraph_inlines(resolved)
    assert inlines[0] == Text("Смотри рисунок ") and resolved.labels[inlines[1].label].display == "1"


def test_block_ref_to_unknown_or_unnumbered_block_is_an_error():
    outside = Figure(png(), "нигде")
    unnumbered = Table(["a"], [["1"]])  # без подписи номера нет
    report = Report(SUAI)
    report.add_section("Ход работы", P(outside.ref), unnumbered)
    with pytest.raises(ResolveError, match="Figure, которого нет в отчете"):
        report.resolve()

    report = Report(SUAI)
    report.add_section("Ход работы", P(unnumbered.ref), unnumbered)
    with pytest.raises(ResolveError, match="Table, которого нет в отчете или у которого нет номера"):
        report.resolve()


def test_same_block_object_twice_is_an_error_only_when_referenced():
    figure = Figure(png(), "Схема")
    report = Report(SUAI)
    report.add_section("Ход работы", figure, figure)
    assert len(report.resolve().nodes) == 3  # без ref дубликат допустим, как раньше

    report = Report(SUAI)
    report.add_section("Ход работы", P(figure.ref), figure, figure)
    with pytest.raises(ResolveError, match="неоднозначен"):
        report.resolve()


def test_unknown_string_label_message_does_not_list_internal_labels():
    figure = Figure(png(), "Схема")
    report = Report(SUAI)
    report.add_section("Ход работы", P(figure.ref, Ref("fig:нет")), figure)
    with pytest.raises(ResolveError) as error:
        report.resolve()
    assert "fig:нет" in str(error.value) and "block" not in str(error.value)
