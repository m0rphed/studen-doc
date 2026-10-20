import dataclasses

import pytest

from studen_doc.style import GOST_732, HeadingStyle, ReportStyle, SectionRule
from studen_doc.universities.suai import SUAI


def test_styles_are_immutable():
    with pytest.raises(dataclasses.FrozenInstanceError):
        GOST_732.text.size_pt = 10  # type: ignore[misc]


def test_evolve_updates_nested_fields_without_touching_original():
    custom = SUAI.evolve(table={"border_sz": 8}, text={"size_pt": 12},
                         figure={"caption": {"dash": "–"}})
    assert custom.table.border_sz == 8
    assert custom.text.size_pt == 12
    assert custom.figure.caption.dash == "–"
    assert custom.figure.caption.label == "Рисунок"            # соседние поля сохранены
    assert SUAI.table.border_sz == 4 and SUAI.figure.caption.dash == "—"


def test_evolve_rejects_unknown_fields_with_hint():
    with pytest.raises(TypeError, match="допустимые"):
        GOST_732.evolve(tabel={"border_sz": 8})
    with pytest.raises(TypeError, match="border_size"):
        GOST_732.evolve(table={"border_size": 8})


def test_evolve_merges_rules_instead_of_replacing():
    custom = GOST_732.evolve(headings={"rules": {"Анализ": SectionRule(numbered=True, structural=False)}})
    assert custom.headings.rule_for("Анализ").numbered
    assert custom.headings.rule_for("Введение") == SectionRule()   # старые правила на месте


def test_evolve_replaces_value_objects_wholesale():
    heading = HeadingStyle(align="center", caps=True)
    assert GOST_732.evolve(headings={"level1": heading}).headings.level1 is heading


def test_presets_differ_only_where_declared():
    assert SUAI.headings.structural.align == "left" and GOST_732.headings.structural.align == "center"
    assert SUAI.headings.rule_for("Ход работы").numbered
    assert GOST_732.headings.rule_for("Ход работы") == GOST_732.headings.default_rule
    assert dataclasses.replace(SUAI, headings=GOST_732.headings) == GOST_732.evolve(toc_title=SUAI.toc_title)


def test_text_width_is_derived_from_page():
    assert GOST_732.page.text_width_cm == pytest.approx(16.5)
    assert isinstance(GOST_732, ReportStyle)


def test_section_name_hint_covers_every_known_rule():
    from typing import get_args

    from studen_doc.style.headings import GOST_732_SECTIONS, SectionName

    literal = next(arg for arg in get_args(SectionName.__value__) if arg is not str)
    hinted = set(get_args(literal))
    assert set(GOST_732_SECTIONS) <= hinted
    assert set(SUAI.headings.rules) <= hinted
