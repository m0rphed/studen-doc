import dataclasses
import typing

import generate_style_changes as generator
import pytest

from studen_doc.style import GOST_732, ReportStyle, changes
from studen_doc.universities.suai import SUAI


def test_generated_file_is_up_to_date():
    """
    Если тест упал, dataclass-ы стиля изменились: ``uv run python tools/generate_style_changes.py``.
    """
    assert generator.TARGET.read_text(encoding="utf-8") == generator.render()


def test_every_style_class_has_a_typed_dict_with_exactly_its_fields():
    classes = generator.style_classes(ReportStyle)
    assert ReportStyle in classes and len(classes) >= 10
    for cls in classes:
        typed_dict = getattr(changes, generator.changes_name(cls))
        names = {field.name for field in dataclasses.fields(cls) if field.init}
        assert set(typing.get_type_hints(typed_dict)) == names
        assert typed_dict.__total__ is False


def test_nested_style_fields_accept_partial_dict_or_instance():
    hints = typing.get_type_hints(changes.ReportStyleChanges)
    assert set(typing.get_args(hints["table"])) == {changes.TableStyleChanges, type(GOST_732.table)}
    assert hints["toc_title"] is str
    mapping = typing.get_type_hints(changes.HeadingsStyleChanges)["rules"]
    assert typing.get_origin(mapping).__name__ == "Mapping"  # значения заменяют записи целиком, не словарем правок


def test_evolve_still_validates_at_runtime_and_keeps_nested_semantics():
    custom = SUAI.evolve(table={"border_sz": 8, "cell_padding": {"left": 100}}, toc_title="Оглавление")
    assert (custom.table.border_sz, custom.table.cell_padding.left, custom.toc_title) == (8, 100, "Оглавление")
    assert custom.table.cell_padding.right == SUAI.table.cell_padding.right
    with pytest.raises(TypeError, match="допустимые"):
        SUAI.evolve(tabel={})  # type: ignore[call-arg]
