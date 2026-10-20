"""
Что загружается при импорте: проверка в свежем процессе, потому что в процессе pytest все уже импортировано.
"""

import os
import subprocess
import sys

import pytest


def python(code: str, *args: object) -> subprocess.CompletedProcess[str]:
    """
    Запускает ``code`` в новом интерпретаторе; обмен в UTF-8 независимо от кодировки консоли.
    """
    environment = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
    return subprocess.run(
        [sys.executable, "-c", code, *map(str, args)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=environment,
        check=False,
    )


@pytest.mark.parametrize(
    "module",
    [
        "studen_doc",
        "studen_doc.model",
        "studen_doc.style",
        "studen_doc.resolve",
        "studen_doc.frontends",
        "studen_doc.errors",
    ],
)
def test_importing_the_core_does_not_load_docx_lxml_or_universities(module):
    result = python(
        f"import sys, {module}\n"
        "heavy = ('docx', 'lxml', 'studen_doc.universities', 'studen_doc.render')\n"
        "print([m for m in heavy if m in sys.modules])"
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "[]", f"{module} загрузил лишнее: {result.stdout.strip()}"


def test_the_pipeline_is_where_python_docx_gets_loaded():
    result = python("import sys, studen_doc.pipeline; print('docx' in sys.modules)")
    assert result.stdout.strip() == "True", result.stderr


BUILD_FROM_MARKDOWN = (
    "import sys\n"
    "from pathlib import Path\n"
    "from studen_doc import Report, MarkdownError\n"
    "{extra}"
    "try:\n"
    "    report = Report.from_markdown(Path(sys.argv[1]))\n"
    "    print('OK', report.items[0].title)\n"
    "except MarkdownError as error:\n"
    "    print('ERROR', error)\n"
)


def test_a_university_style_needs_an_explicit_import(tmp_path):
    path = tmp_path / "r.md"
    path.write_text("---\nstyle: suai\n---\n\n# Введение\n\nТекст.\n", encoding="utf-8")

    without = python(BUILD_FROM_MARKDOWN.format(extra=""), path)
    assert without.stdout.startswith("ERROR Неизвестный стиль 'suai'; известны ['gost_732']"), without.stdout
    assert "import studen_doc.universities" in without.stdout  # ошибка говорит, что делать

    explicit = python(BUILD_FROM_MARKDOWN.format(extra="import studen_doc.universities\n"), path)
    assert explicit.stdout.strip() == "OK Введение", explicit.stdout + explicit.stderr


def test_unknown_title_page_type_gets_the_same_hint(tmp_path):
    path = tmp_path / "r.md"
    path.write_text("---\nstyle: gost_732\ntitle_page:\n  type: suai\n---\n\n# Введение\n", encoding="utf-8")
    result = python(BUILD_FROM_MARKDOWN.format(extra=""), path)
    assert "title_page.type = 'suai'" in result.stdout, result.stdout + result.stderr
    assert "import studen_doc.universities" in result.stdout
