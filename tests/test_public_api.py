"""
Публичный API: заголовок раздела отдельно от правила оформления, именованные параметры блоков,
нормализация маркеров списков, переименованные реестры и подстановки.
"""

import pytest

from studen_doc import Report
from studen_doc.frontends import MarkdownError, parse_markdown_text
from studen_doc.model.blocks import Formula, Numbered, P, Table, normalize_marker
from studen_doc.model.inline import Md
from studen_doc.model.report import Section, Toc
from studen_doc.pandoc import find_pandoc
from studen_doc.style import GOST_732, register_style, style_named, style_names

needs_pandoc = pytest.mark.skipif(find_pandoc() is None, reason="pandoc не найден")


def test_section_title_comes_first_and_rule_defaults_to_the_title():
    assert Section("Введение", ()).rule_name == "Введение"
    assert Section("Исходный код", (), rule="Приложение").rule_name == "Приложение"
    report = Report(GOST_732).add_section("Описание данных", P("x"), rule="Основная часть", status="справочное")
    (section,) = report.items
    assert (section.title, section.rule, section.status) == ("Описание данных", "Основная часть", "справочное")


@needs_pandoc
def test_markdown_heading_rule_option_sets_the_rule():
    (section,) = parse_markdown_text('# Описание данных {rule="Основная часть"}\n\nтекст\n').items
    assert (section.title, section.rule_name) == ("Описание данных", "Основная часть")


def test_toc_options_are_keyword_only():
    assert Toc("Содержание", levels=2).levels == 2
    with pytest.raises(TypeError):
        Toc(None, 2)  # type: ignore[misc]
    with pytest.raises(TypeError):
        Report(GOST_732).add_toc(None, 2)  # type: ignore[misc]


def test_block_options_are_keyword_only():
    with pytest.raises(TypeError):
        Table(["a"], [["1"]], "подпись")  # type: ignore[misc]
    with pytest.raises(TypeError):
        Formula("a=b", "eq:a")  # type: ignore[misc]
    with pytest.raises(TypeError):
        Numbered(["x"], "1)")  # type: ignore[misc]


def test_formula_where_accepts_dict_and_pairs_alike():
    as_dict = Formula("a=b", where={"a": "первое", "b": Md("второе")})
    as_pairs = Formula("a=b", where=[("a", "первое"), ("b", Md("второе"))])
    assert as_dict.legend == as_pairs.legend == (("a", "первое"), ("b", Md("второе")))
    assert as_dict == as_pairs


def test_paragraph_md_shortcut():
    assert P.md("*курсив*") == P(Md("*курсив*"))
    assert P.md("текст", keep_with_next=True).keep_with_next is True


@pytest.mark.parametrize("marker", ["1)", "1.", "a)", "a."])
def test_latin_markers_are_kept(marker):
    assert normalize_marker(marker) == marker
    assert Numbered(["x"], marker=marker).marker == marker


@pytest.mark.parametrize(("cyrillic", "latin"), [("а)", "a)"), ("а.", "a.")])
def test_cyrillic_markers_are_normalized_to_latin(cyrillic, latin):
    assert Numbered(["x"], marker=cyrillic).marker == latin


@pytest.mark.parametrize("marker", ["a )", " 1)", "1 .", "b)", "1", "a)x", "б)", "-", "1-", ""])
def test_other_markers_are_rejected_at_construction(marker):
    with pytest.raises(ValueError, match="Маркер списка"):
        Numbered(["x"], marker=marker)


def test_style_registry_names(temporary_style):
    style = temporary_style("api-test-style", GOST_732)
    assert style_named("api-test-style") is style
    assert "api-test-style" in style_names()
    with pytest.raises(ValueError, match="уже зарегистрирован"):
        register_style("api-test-style", style)


@needs_pandoc
def test_inserts_and_variables_feed_markdown():
    table = Table(["a"], [["1"]], caption="Из Python", label="tbl:py")
    text = '# Раздел\n\n::: {.insert name=t}\n:::\n\nR2 = []{var=r2 format=".2f"}\n'
    (section,) = parse_markdown_text(text, inserts={"t": table}, variables={"r2": 0.873}).items
    assert section.content[0] is table
    assert "0,87" in repr(section.content[1])
    with pytest.raises(MarkdownError, match="не передан"):
        parse_markdown_text(text, variables={"r2": 1})


@pytest.mark.skipif(find_pandoc() is None, reason="pandoc не найден")
def test_from_markdown_returns_the_class_it_was_called_on(tmp_path):
    class MyReport(Report):
        pass

    path = tmp_path / "r.md"
    path.write_text("# Раздел\n\nТекст.\n", encoding="utf-8")
    report = MyReport.from_markdown(path, style=GOST_732)
    assert type(report) is MyReport and [item.title for item in report.items] == ["Раздел"]
