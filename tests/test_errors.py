import pytest

import studen_doc
from studen_doc import (
    MarkdownError,
    MathConversionError,
    P,
    PandocError,
    Ref,
    Report,
    ReportError,
    ResolveError,
)
from studen_doc.frontends import parse_markdown_text
from studen_doc.pandoc import run_pandoc
from studen_doc.universities.suai import SUAI


def test_every_library_error_is_a_report_error():
    for error in (ResolveError, MarkdownError, MathConversionError, PandocError):
        assert issubclass(error, ReportError)
    assert not issubclass(ReportError, (ValueError, KeyError, RuntimeError))  # ловится только как ReportError


def test_public_names_are_the_same_classes_as_in_the_errors_module():
    from studen_doc import errors

    for name in ("ReportError", "ResolveError", "MarkdownError", "MathConversionError", "PandocError"):
        assert getattr(studen_doc, name) is getattr(errors, name)


def test_resolve_error_message_is_plain_text_not_a_quoted_key_error():
    report = Report(SUAI)
    report.add_section("Вывод", P(Ref("fig:нет")))
    with pytest.raises(ReportError) as error:
        report.resolve()
    assert isinstance(error.value, ResolveError)
    assert str(error.value).startswith("Ссылки на неизвестные метки")  # KeyError показал бы текст в кавычках


def test_markdown_problem_is_caught_as_report_error():
    with pytest.raises(ReportError):
        parse_markdown_text("текст до первого заголовка\n")


def test_missing_pandoc_executable_is_a_pandoc_error(tmp_path):
    with pytest.raises(PandocError, match="Не удалось запустить"):
        run_pandoc(["--version"], b"", command=[str(tmp_path / "нет-такого-pandoc")])


def test_argument_misuse_stays_a_builtin_error():
    with pytest.raises(ValueError, match="хотя бы один"):
        Report.from_markdown(style=SUAI)
    with pytest.raises(TypeError, match="допустимые"):
        SUAI.evolve(tabel={})  # type: ignore[call-arg]
