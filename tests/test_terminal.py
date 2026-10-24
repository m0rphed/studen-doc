"""
Вывод терминала в отчете: цветной листинг и скриншот (пакет termsnap, extra ``terminal``).
"""

import io
import sys

import pytest
from docx import Document

pytest.importorskip("termsnap")
pytest.importorskip("PIL")

import termsnap
from PIL import Image

from studen_doc import Figure, Listing, Report, figure_from_terminal, listing_from_terminal
from studen_doc.universities.suai import SUAI

#: Вывод программы: красный жирный, обычный, черный на зеленом фоне.
COLORED = "esc = chr(27); print(esc + '[1;31mred' + esc + '[0m plain ' + esc + '[42;30mgreen' + esc + '[0m')"
LIGHT_RED = "cd3131"


def python(code: str) -> list[str]:
    return [sys.executable, "-c", code]


@pytest.fixture(scope="module")
def has_monospace_font() -> None:
    from termsnap.errors import FontNotFound
    from termsnap.png import resolve

    try:
        resolve()
    except FontNotFound as error:
        pytest.skip(f"в системе нет подходящего моноширинного шрифта: {error.problems}")


def build(tmp_path, *blocks):
    report = Report(SUAI, title="Тест")
    report.add_section("Ход работы", *blocks)
    return Document(str(report.build_to_docx(tmp_path / "report.docx")))


# --- листинг ---


def test_colored_output_becomes_text_runs_with_the_theme_colours():
    listing = listing_from_terminal(python(COLORED), "Вывод")
    assert listing.code == "red plain green"
    assert listing.runs is not None
    (line,) = listing.runs
    red, plain, green = (run for run in line if run.text.strip())
    assert (red.text, red.color, red.bold, red.background) == ("red", LIGHT_RED, True, None)
    assert (plain.text.strip(), plain.color, plain.background, plain.bold) == ("plain", None, None, False)
    assert (green.color, green.background) == ("000000", "00bc00")


def test_theme_can_be_given_as_a_name_a_mapping_or_an_object():
    by_name = listing_from_terminal(python(COLORED), theme="dark")
    assert (
        by_name.runs[0][0].color == "cd3131"
    )  # красный DARK (у LIGHT он совпадает по значению, проверяем другой цвет)
    by_mapping = listing_from_terminal(python(COLORED), theme={"base": "light", "ansi": {"red": "#ff0000"}})
    assert by_mapping.runs[0][0].color == "ff0000"
    custom = termsnap.LIGHT.derive(ansi={"red": (1, 2, 3)})
    by_object = listing_from_terminal(python(COLORED), theme=custom)
    assert by_object.runs[0][0].color == "010203"
    green_background = listing_from_terminal(python(COLORED), theme={"ansi": {"green": "#112233"}})
    assert green_background.runs[0][-1].background == "112233"


def test_unknown_theme_name_is_an_error():
    with pytest.raises(ValueError, match="solarized"):
        listing_from_terminal(python(COLORED), theme="solarized")


def test_dim_text_is_blended_with_the_background_and_inverse_swaps_colours():
    esc = "esc = chr(27); print(esc + '[2mdim' + esc + '[0m ' + esc + '[7minv' + esc + '[0m')"
    listing = listing_from_terminal(python(esc))
    dim, _space, inverse = listing.runs[0]
    assert dim.color == "858585"  # 60% текста (333333) и 40% белого фона
    assert (inverse.color, inverse.background) == ("ffffff", "333333")


def test_empty_output_is_one_empty_line():
    listing = listing_from_terminal(python("pass"))
    assert listing.code == ""
    assert listing.runs == ((),)


def test_ready_capture_is_used_as_it_is_and_run_options_cannot_be_mixed_with_it():
    capture = termsnap.run(python(COLORED))
    assert listing_from_terminal(capture).code == "red plain green"
    with pytest.raises(TypeError, match="timeout"):
        listing_from_terminal(capture, timeout=5)


def test_listing_command_runs_in_a_terminal_narrow_enough_for_the_page():
    code = "import os; print(os.environ['COLUMNS'])"
    assert listing_from_terminal(python(code)).code == "64"
    assert listing_from_terminal(python(code), columns=100).code == "100"
    assert listing_from_terminal(python(code), columns=40).code == "40"


def test_a_command_must_be_a_list_not_a_string():
    with pytest.raises(TypeError, match="список"):
        listing_from_terminal("python app.py")  # pyright: ignore[reportArgumentType]


def test_run_options_reach_termsnap():
    with pytest.raises(termsnap.RunTimeout):
        listing_from_terminal(python("import time; time.sleep(30)"), timeout=0.5)


def test_interactive_program_can_be_driven_through_the_pty_backend():
    pytest.importorskip("pyte")
    if sys.platform == "win32":
        pytest.importorskip("winpty")
    listing = listing_from_terminal(
        python("print(input().upper())"),
        backend=termsnap.PtyBackend(),
        input=("hello",),
    )
    assert listing.code.split("\n") == ["hello", "HELLO"]


def test_capture_visible_only_reaches_the_terminal_and_by_default_nothing_scrolls_away():
    pytest.importorskip("pyte")
    if sys.platform == "win32":
        pytest.importorskip("winpty")
    code = "for n in range(1, 41): print('line', n)"
    options = {"backend": termsnap.PtyBackend(), "rows": 10}
    everything = listing_from_terminal(python(code), **options)
    visible = listing_from_terminal(python(code), capture_visible_only=True, **options)
    assert everything.code.split("\n") == [f"line {n}" for n in range(1, 41)]
    assert visible.code.split("\n") == [f"line {n}" for n in range(32, 41)]  # экран из 10 строк, последняя пустая


def test_listing_renders_to_docx_with_a_listing_caption_and_colours(tmp_path):
    doc = build(tmp_path, listing_from_terminal(python(COLORED), "Вывод программы", label="lst:out"))
    assert any(p.text.startswith("Листинг 1") and "Вывод программы" in p.text for p in doc.paragraphs)
    (paragraph,) = [p for p in doc.paragraphs if p.style.name == "Код"]
    assert paragraph.text == "red plain green"
    assert str(paragraph.runs[0].font.color.rgb).lower() == LIGHT_RED
    assert paragraph.runs[0].font.bold


def test_line_numbers_option_reaches_the_listing(tmp_path):
    doc = build(tmp_path, listing_from_terminal(python(COLORED), "Вывод", line_numbers=True))
    (paragraph,) = [p for p in doc.paragraphs if p.style.name == "Код"]
    assert paragraph.text == "1  red plain green"


# --- скриншот ---


def image_of(figure: Figure) -> Image.Image:
    assert isinstance(figure.source, io.BytesIO)
    return Image.open(io.BytesIO(figure.source.getvalue()))


def test_screenshot_is_a_png_figure_with_the_given_caption(has_monospace_font):
    figure = figure_from_terminal(python(COLORED), "Окно терминала", label="fig:term", width_cm=10)
    assert isinstance(figure, Figure)
    assert (figure.caption, figure.label, figure.width_cm) == ("Окно терминала", "fig:term", 10)
    image = image_of(figure)
    assert image.format == "PNG"
    assert image.width > 50
    assert image.getpixel((0, 0)) == (0x1E, 0x1E, 0x1E)  # по умолчанию темная тема


def test_theme_font_and_padding_are_passed_to_the_renderer(has_monospace_font):
    default = image_of(figure_from_terminal(python(COLORED), "Окно", scale=1))
    tight = image_of(figure_from_terminal(python(COLORED), "Окно", scale=1, padding=0))
    assert (default.width - tight.width, default.height - tight.height) == (32, 32)
    custom = image_of(figure_from_terminal(python(COLORED), "Окно", scale=1, theme={"background": "#010203"}))
    assert custom.getpixel((0, 0)) == (1, 2, 3)
    light = image_of(figure_from_terminal(python(COLORED), "Окно", scale=1, theme="light"))
    assert light.getpixel((0, 0)) == (255, 255, 255)


def test_font_can_be_chosen_and_a_missing_family_is_an_error(has_monospace_font):
    from termsnap.errors import FontNotFound
    from termsnap.png import resolve

    family = resolve().family
    chosen = image_of(figure_from_terminal(python(COLORED), "Окно", fonts=family, scale=1))
    default = image_of(figure_from_terminal(python(COLORED), "Окно", scale=1))
    assert chosen.size == default.size
    with pytest.raises(FontNotFound, match="Not A Real Font"):
        figure_from_terminal(python(COLORED), "Окно", fonts="Not A Real Font")


def test_screenshot_renders_to_docx_with_a_figure_caption(tmp_path, has_monospace_font):
    doc = build(tmp_path, figure_from_terminal(python(COLORED), "Окно терминала"))
    assert len(doc.inline_shapes) == 1
    assert any(p.text.startswith("Рисунок 1") and "Окно терминала" in p.text for p in doc.paragraphs)


def test_unsuitable_source_types_are_rejected_before_drawing():
    with pytest.raises(TypeError, match="список"):
        figure_from_terminal("python app.py", "Окно")  # pyright: ignore[reportArgumentType]


# --- без termsnap ---


def test_missing_termsnap_gives_an_installation_hint(monkeypatch):
    monkeypatch.setitem(sys.modules, "termsnap", None)
    with pytest.raises(ImportError, match=r"studen-doc\[terminal\]"):
        listing_from_terminal(python(COLORED))
    with pytest.raises(ImportError, match=r"studen-doc\[terminal\]"):
        figure_from_terminal(python(COLORED), "Окно")


def test_listing_type_is_the_ordinary_one():
    assert isinstance(listing_from_terminal(python(COLORED)), Listing)
