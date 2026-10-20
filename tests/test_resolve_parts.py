"""
Части резолвера по отдельности: счетчики разделов и блоков, реестр меток и ссылок.
"""

import pytest

from helpers import png
from studen_doc import Figure, Formula, Listing, P, Ref, ResolveError, Table
from studen_doc.model.inline import BlockRef
from studen_doc.resolve.counters import NumberAllocator, SectionContext, SectionNumbering
from studen_doc.resolve.labels import LabelRegistry
from studen_doc.resolve.resolver import _NUMERIC_CELL


# ------------------------------------------------------------------------------------- разделы
def test_numbered_sections_count_up_and_unnumbered_ones_have_no_number():
    sections = SectionNumbering()
    assert sections.open(appendix=False, numbered=False) == SectionContext(None, appendix=False)
    assert sections.open(appendix=False, numbered=True).number == "1"
    assert sections.open(appendix=False, numbered=True).number == "2"


def test_appendices_get_letters_and_run_out_of_gost_letters():
    sections = SectionNumbering()
    assert [sections.open(appendix=True, numbered=False).number for _ in range(3)] == ["А", "Б", "В"]
    with pytest.raises(ResolveError, match="Слишком много приложений"):
        for _ in range(30):
            sections.open(appendix=True, numbered=False)


def test_subsections_are_numbered_by_depth_and_reset_inside_a_new_section():
    sections = SectionNumbering()
    second = sections.open(appendix=False, numbered=True)
    assert [sections.subsection(second, depth) for depth in (1, 1, 2, 2, 3, 1, 2)] == [
        "1.1",
        "1.2",
        "1.2.1",
        "1.2.2",
        "1.2.2.1",
        "1.3",
        "1.3.1",
    ]
    third = sections.open(appendix=False, numbered=True)
    assert sections.subsection(third, 1) == "2.1"
    assert sections.subsection(SectionContext(None, appendix=False), 1) is None


# ------------------------------------------------------------------------------------- номера блоков
def test_continuous_numbers_are_counted_per_kind_with_unique_bookmarks():
    numbers = NumberAllocator("continuous")
    section = SectionContext("1", appendix=False)
    figure1, figure2, table1 = (numbers.next(kind, section) for kind in ("figure", "figure", "table"))
    assert (figure1.display, figure2.display, table1.display) == ("1", "2", "1")
    assert all(number.use_seq for number in (figure1, figure2, table1))
    assert len({figure1.bookmark, figure2.bookmark, table1.bookmark}) == 3
    assert figure1.bookmark.startswith("_Ref_fig_") and table1.bookmark.startswith("_Ref_tab_")


def test_section_scope_restarts_numbers_in_every_section_and_disables_seq_fields():
    numbers = NumberAllocator("section")
    first, second = SectionContext("1", appendix=False), SectionContext("2", appendix=False)
    assert [numbers.next("figure", first).display for _ in range(2)] == ["1.1", "1.2"]
    numbers.start_section()
    number = numbers.next("figure", second)
    assert (number.display, number.use_seq) == ("2.1", False)


def test_unnumbered_section_keeps_continuous_numbering_even_in_section_scope():
    numbers = NumberAllocator("section")
    assert numbers.next("table", SectionContext(None, appendix=False)).display == "1"


def test_appendix_numbers_follow_the_letter_in_any_scope():
    numbers = NumberAllocator("continuous")
    appendix = SectionContext("А", appendix=True)
    assert [numbers.next("listing", appendix).display for _ in range(2)] == ["А.1", "А.2"]
    assert numbers.next("listing", appendix).use_seq is False


# --------------------------------------------------------------------------------------- метки
def _number(allocator, kind="figure"):
    return allocator.next(kind, SectionContext("1", appendix=False))


def test_registry_keeps_author_labels_and_hides_unreferenced_blocks():
    allocator, registry = NumberAllocator("continuous"), LabelRegistry()
    labeled, plain = Figure(png(), "а", label="fig:a"), Figure(png(), "б")
    first, second = _number(allocator), _number(allocator)
    registry.register(labeled, first)
    registry.register(plain, second)
    assert registry.labels() == {"fig:a": first}


def test_registry_resolves_block_references_through_internal_labels():
    allocator, registry = NumberAllocator("continuous"), LabelRegistry()
    table = Table(["a"], [["1"]], caption="т")
    number = _number(allocator, "table")
    registry.register(table, number)
    ref = registry.reference_block(BlockRef(table, bold=True))
    assert isinstance(ref, Ref) and ref.bold and ref.label.startswith("\0")
    assert registry.labels() == {ref.label: number}
    registry.check()


def test_registry_rejects_duplicate_labels_unknown_refs_and_broken_block_refs():
    allocator, registry = NumberAllocator("continuous"), LabelRegistry()
    registry.register(Figure(png(), "а", label="x"), _number(allocator))
    with pytest.raises(ResolveError, match="уже используется"):
        registry.register(Figure(png(), "б", label="x"), _number(allocator))

    registry.use(Ref("fig:нет"))
    with pytest.raises(ResolveError, match=r"неизвестные метки: \['fig:нет'\]; известные: \['x'\]"):
        registry.check()

    fresh = LabelRegistry()
    fresh.reference_block(BlockRef(Listing("x", "Код")))
    with pytest.raises(ResolveError, match="Listing, которого нет в отчете"):
        fresh.check()

    shared = Formula("a", numbered=True)
    twice = LabelRegistry()
    twice.register(shared, _number(allocator, "formula"))
    twice.register(shared, _number(allocator, "formula"))
    twice.check()  # без ссылки дубликат допустим
    twice.reference_block(BlockRef(shared))
    with pytest.raises(ResolveError, match="неоднозначен"):
        twice.check()


def test_resolved_report_collects_formulas_once_in_order_of_appearance():
    from studen_doc import Math, Report
    from studen_doc.universities.suai import SUAI

    report = Report(SUAI)
    report.add_section("Введение", P(Math("b"), Math("a")), Formula("c", where=[("a", "x"), ("d", "y")]), P(Math("b")))
    assert report.resolve().formulas == ("b", "a", "c", "d")


@pytest.mark.parametrize("text", ["1", "-2,5", "+3.14", "−7", "1 000,5", "1 000", "1e-5", "45 %", "25%"])
def test_numbers_are_aligned_as_numbers(text):
    assert _NUMERIC_CELL.match(text)


@pytest.mark.parametrize("text", ["", "-", "1.2.3", "12-34", "2024-05-01", "1 2 3", "a1", "1a", "%", "10 20"])
def test_identifiers_dates_and_words_are_not_numbers(text):
    assert not _NUMERIC_CELL.match(text)
