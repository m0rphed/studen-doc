import subprocess
import sys
from pathlib import Path

import pytest

from helpers import M
from studen_doc.equations import MathConversionError, MathConverter, PandocConverter, find_pandoc

FAKE = str(Path(__file__).with_name("fake_pandoc.py"))


@pytest.fixture
def fake(tmp_path, monkeypatch):
    """Конвертер с подставным pandoc + журнал его запусков (по строке на запуск)."""
    log = tmp_path / "calls.log"
    monkeypatch.setenv("FAKE_PANDOC_LOG", str(log))

    def calls() -> list[str]:
        return log.read_text(encoding="utf-8").splitlines() if log.exists() else []

    return PandocConverter(command=[sys.executable, FAKE]), calls


def text_of(element) -> str:
    return "".join(element.itertext())


# ------------------------------------------------------------------ один вызов на набор формул
def test_all_formulas_go_to_a_single_process(fake):
    converter, calls = fake
    result = converter.convert(["x^2", r"\frac{a}{b}", "y"])
    assert len(calls()) == 1
    assert {k: text_of(v) for k, v in result.items()} == {"x^2": "x^2", r"\frac{a}{b}": r"\frac{a}{b}", "y": "y"}


def test_duplicates_and_cached_formulas_are_not_sent_again(fake):
    converter, calls = fake
    converter.convert(["a", "b", "a"])
    assert len(calls()) == 1 and calls()[0].count("$") == 4          # «a» и «b» по одному разу
    converter.convert(["a", "b"])
    assert len(calls()) == 1                                          # всё из кэша — процесс не запускался
    converter.convert(["b", "c"])
    assert len(calls()) == 2 and calls()[1] == "$c$"                  # доконвертирована только новая


def test_multiline_formula_stays_one_paragraph(fake):
    converter, calls = fake
    converter.convert(["a\n\nb"])
    assert calls() == ["$a  b$"]


def test_returned_elements_are_fresh_for_every_call(fake):
    converter, _ = fake
    first = converter.convert(["x"])["x"]
    first.clear()
    assert text_of(converter.convert(["x"])["x"]) == "x"


# ------------------------------------------------------------------------------------- ошибки
def test_empty_formula_fails_before_starting_a_process(fake):
    converter, calls = fake
    with pytest.raises(MathConversionError, match="Пустая"):
        converter.convert(["x", "  "])
    assert calls() == []


def test_nonzero_exit_code_is_reported(fake, monkeypatch):
    monkeypatch.setenv("FAKE_PANDOC_MODE", "fail")
    with pytest.raises(MathConversionError, match=r"кодом 3.*boom"):
        fake[0].convert(["x"])


def test_formula_pandoc_could_not_parse_is_named(fake, monkeypatch):
    monkeypatch.setenv("FAKE_PANDOC_MODE", "unparsed")
    with pytest.raises(MathConversionError) as error:
        fake[0].convert(["good", r"\BAD{", "fine"])
    assert r"\BAD{" in str(error.value) and "good" not in str(error.value)


def test_paragraph_count_mismatch_is_detected(fake, monkeypatch):
    monkeypatch.setenv("FAKE_PANDOC_MODE", "short")
    with pytest.raises(MathConversionError, match="абзацев"):
        fake[0].convert(["a", "b"])


def test_missing_executable_gives_clear_error(tmp_path):
    converter = PandocConverter(command=[str(tmp_path / "нет-такого-pandoc")])
    with pytest.raises(MathConversionError, match="Не удалось запустить"):
        converter.convert(["x"])


# ---------------------------------------------------------- вызов процесса: кроссплатформенность
def test_process_is_started_without_shell_with_argument_list_and_bytes(monkeypatch):
    seen: dict = {}
    real_run = subprocess.run

    def spy(args, **kwargs):
        seen.update(args=args, kwargs=kwargs)
        return real_run(args, **kwargs)

    monkeypatch.setattr(subprocess, "run", spy)
    PandocConverter(command=[sys.executable, FAKE]).convert(["é^2"])
    assert isinstance(seen["args"], list) and all(isinstance(a, str) for a in seen["args"])
    assert not seen["kwargs"].get("shell")                           # без оболочки: нет проблем с кавычками cmd/sh
    assert isinstance(seen["kwargs"]["input"], bytes)                # обмен байтами UTF-8, не кодировкой консоли
    assert seen["kwargs"]["input"].decode("utf-8") == "$é^2$"
    assert seen["kwargs"]["timeout"] > 0


def test_find_pandoc_prefers_explicit_variable(monkeypatch):
    monkeypatch.setenv("PANDOC", "/custom/pandoc")
    assert find_pandoc() == "/custom/pandoc"


def test_converter_without_pandoc_explains_how_to_fix(monkeypatch):
    monkeypatch.setattr("studen_doc.pandoc.find_pandoc", lambda: None)
    with pytest.raises(MathConversionError, match="pypandoc-binary"):
        PandocConverter().convert(["x"])


def test_any_object_with_convert_satisfies_the_protocol():
    class Stub:
        def convert(self, formulas):
            return dict.fromkeys(formulas)

    converter: MathConverter = Stub()
    assert converter.convert(["x"]) == {"x": None}


# ---------------------------------------------------------------- настоящий pandoc (если найден)
real = pytest.mark.skipif(find_pandoc() is None, reason="pandoc не найден")


@real
@pytest.mark.parametrize("latex", [
    r"\frac{a}{b}",
    r"\sqrt{x^2+1}",
    r"\hat\beta=(X^{T}X)^{-1}X^{T}y",
    r"\begin{pmatrix}a&b\\c&d\end{pmatrix}",
    r"f(x)=\begin{cases} x^2, & x\ge 0 \\ -x, & x<0 \end{cases}",
])
def test_real_pandoc_returns_omath(latex):
    assert PandocConverter().convert([latex])[latex].tag == M + "oMath"


@real
def test_real_pandoc_keeps_sum_body_inside_nary():
    formula = r"\sum_{i=1}^{n}(x_i-\bar x)^2"
    omml = PandocConverter().convert([formula])[formula]
    body = next(omml.iter(M + "nary")).find(M + "e")
    assert body is not None and len(body) > 0


@real
def test_real_pandoc_names_unparseable_formulas():
    with pytest.raises(MathConversionError, match=r"\\badcommand"):
        PandocConverter().convert([r"x^2", r"\badcommand{z}"])
