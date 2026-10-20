"""Правила слоёв: ядро (модель, стиль, нумерация, IR) не знает о python-docx и о рендерерах.

Именно это делает возможным второй формат вывода (typst, LaTeX): он читает тот же IR.
"""
import ast
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src" / "studen_doc"

CORE = ["model", "style", "resolve", "ir.py", "types.py", "errors.py", "numfmt.py"]
FORBIDDEN_IN_CORE = (
    "docx",
    "lxml",
    "studen_doc.render",
    "studen_doc.ooxml",
    "studen_doc.equations",
    "studen_doc.bibliography",
    "studen_doc.frontends",
    "studen_doc.universities",
    "studen_doc.pipeline",
)
#: Единственные места ядра, которым нужен верхний слой: короткие обертки ``Report.resolve`` и аналоги.
ALLOWED_LAZY = {"model/report.py": {"studen_doc.frontends.markdown", "studen_doc.pipeline"}}

FRONTEND_FORBIDDEN = (
    "docx",
    "lxml",
    "studen_doc.render",
    "studen_doc.ooxml",
    "studen_doc.universities",
)

#: Слой render работает с Word только через ooxml: сырого XML (``docx.oxml``, lxml) в нем быть не должно.
RENDER_FORBIDDEN = ("docx.oxml", "lxml")


def imported_modules(path: Path) -> set[str]:
    """
    Все импортируемые модули файла, включая вложенные в функции; импорты под ``if TYPE_CHECKING`` не считаются.
    """
    found: set[str] = set()

    def visit(node: ast.AST) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.If) and ast.unparse(child.test) == "TYPE_CHECKING":
                continue
            if isinstance(child, ast.Import):
                found.update(alias.name for alias in child.names)
            elif isinstance(child, ast.ImportFrom) and child.module and not child.level:
                found.add(child.module)
            visit(child)

    visit(ast.parse(path.read_text(encoding="utf-8")))
    return found


def source_files(entries: list[str]) -> list[Path]:
    files: list[Path] = []
    for entry in entries:
        target = SRC / entry
        files.extend(sorted(target.rglob("*.py")) if target.is_dir() else [target])
    return files


@pytest.mark.parametrize("path", source_files(CORE), ids=lambda p: str(p.relative_to(SRC)))
def test_core_depends_neither_on_docx_stack_nor_on_upper_layers(path):
    allowed = ALLOWED_LAZY.get(path.relative_to(SRC).as_posix(), set())
    bad = {m for m in imported_modules(path) if m.startswith(FORBIDDEN_IN_CORE) and m not in allowed}
    assert not bad, f"{path.name}: ядро не должно импортировать {sorted(bad)}"


@pytest.mark.parametrize("path", source_files(["render"]), ids=lambda p: str(p.relative_to(SRC)))
def test_render_layer_does_not_touch_raw_xml(path):
    bad = {m for m in imported_modules(path) if m.startswith(RENDER_FORBIDDEN)}
    assert not bad, f"{path.name}: рендерер должен работать через ooxml, а не с {sorted(bad)}"


@pytest.mark.parametrize("path", source_files(["bibliography"]), ids=lambda p: str(p.relative_to(SRC)))
def test_bibliography_layer_knows_neither_docx_nor_renderers(path):
    bad = {m for m in imported_modules(path) if m.startswith((*FRONTEND_FORBIDDEN, "studen_doc.pipeline"))}
    assert not bad, f"{path.name}: оформление источников не должно импортировать {sorted(bad)}"


@pytest.mark.parametrize("path", source_files(["frontends"]), ids=lambda p: str(p.relative_to(SRC)))
def test_frontends_do_not_know_about_renderers_or_universities(path):
    bad = {m for m in imported_modules(path) if m.startswith(FRONTEND_FORBIDDEN)}
    assert not bad, f"{path.name}: фронтенд не должен импортировать {sorted(bad)}"


def test_all_imports_are_absolute():
    relative = [str(p.relative_to(SRC)) for p in SRC.rglob("*.py")
                if any(isinstance(n, ast.ImportFrom) and n.level for n in ast.walk(ast.parse(p.read_text("utf-8"))))]
    assert not relative, f"относительные импорты в {relative}"


PRIVATE_DOCX_ATTRIBUTES = {"_p", "_r", "_tc", "_tbl", "_tr", "_element", "_numbering", "_body"}


def test_private_python_docx_attributes_are_read_only_in_ooxml_elements():
    """
    Приватные атрибуты python-docx (``par._p``, ``cell._tc``...) читает только ``ooxml/elements.py``:
    при смене версии python-docx править придется одно место.
    """
    offenders = []
    for path in SRC.rglob("*.py"):
        if path == SRC / "ooxml" / "elements.py":
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            is_private = isinstance(node, ast.Attribute) and node.attr in PRIVATE_DOCX_ATTRIBUTES
            if is_private and not (isinstance(node.value, ast.Name) and node.value.id == "self"):  # type: ignore[union-attr]
                offenders.append(f"{path.relative_to(SRC)}:{node.lineno}")  # type: ignore[union-attr]
    assert not offenders, f"приватные атрибуты python-docx вне ooxml/elements.py: {offenders}"


def test_package_root_does_not_import_heavy_layers():
    """
    ``import studen_doc`` остается легким: ни python-docx, ни рендерера, ни вузов (они подключаются явно).
    """
    heavy = ("docx", "studen_doc.render", "studen_doc.ooxml", "studen_doc.universities")
    bad = {m for m in imported_modules(SRC / "__init__.py") if m.startswith(heavy)}
    assert not bad, f"корень пакета не должен импортировать {sorted(bad)}"
