"""
Генератор ``src/studen_doc/style/changes.py``: TypedDict-ы с правками стилей для ``ReportStyle.evolve``.

Файл строится рефлексией по dataclass-ам стиля (``dataclasses.fields``, ``typing.get_type_hints``,
``typing.get_origin`` и ``get_args``) и собирается как синтаксическое дерево модулем ``ast`` - без текстовых
шаблонов, в которые подставляются имена. Запуск: ``uv run python tools/generate_style_changes.py``.
Тест ``tests/test_style_changes.py`` следит, чтобы файл не отставал от dataclass-ов.
"""

from __future__ import annotations

import ast
import dataclasses
import types
import typing
from collections import defaultdict
from pathlib import Path
from typing import Any

import studen_doc.style
import studen_doc.style.components as components
import studen_doc.style.headings as headings
import studen_doc.types as shared_types
from studen_doc.style.evolve import Evolvable
from studen_doc.style.report_style import ReportStyle

TARGET = Path(studen_doc.style.__file__).with_name("changes.py")
FIRST_PARTY = "studen_doc"
SUFFIX = "Changes"


def is_style(tp: object) -> bool:
    """
    Класс стиля - dataclass, который поддерживает ``evolve``.
    """
    return isinstance(tp, type) and dataclasses.is_dataclass(tp) and issubclass(tp, Evolvable)


def init_fields(cls: type) -> list[dataclasses.Field[Any]]:
    return [field for field in dataclasses.fields(cls) if field.init]


def style_classes(root: type) -> list[type]:
    """
    Классы стиля, достижимые из ``root`` через поля-стили; зависимости идут раньше зависимых.
    """
    ordered: list[type] = []

    def visit(cls: type) -> None:
        if cls in ordered:
            return
        hints = typing.get_type_hints(cls)
        for field in init_fields(cls):
            if is_style(hints[field.name]):
                visit(hints[field.name])
        ordered.append(cls)

    visit(root)
    return ordered


def literal_aliases() -> dict[object, tuple[str, str]]:
    """
    Именованные Literal-типы пакета (``Align``, ``NumberScope``...): значение -> (модуль, имя).
    """
    found: dict[object, tuple[str, str]] = {}
    for module in (shared_types, components, headings):
        for name, value in vars(module).items():
            if typing.get_origin(value) is typing.Literal and not name.startswith("_"):
                found.setdefault(value, (module.__name__, name))
    return found


class Annotator:
    """
    Превращает объект типа в выражение ``ast`` и запоминает, какие имена нужно импортировать.
    """

    def __init__(self) -> None:
        self.imports: defaultdict[str, set[str]] = defaultdict(set)
        self._aliases = literal_aliases()

    def use(self, module: str, name: str) -> ast.Name:
        if module != "builtins":
            self.imports[module].add(name)
        return ast.Name(id=name, ctx=ast.Load())

    def annotation(self, tp: Any, *, top_level: bool = True) -> ast.expr:
        """
        ``top_level=True`` - тип самого поля: вложенный стиль можно задать словарем правок или готовым объектом.
        """
        if tp is None or tp is type(None):
            return ast.Constant(value=None)
        if tp is Ellipsis:
            return ast.Constant(value=Ellipsis)
        if is_style(tp):
            plain = self.use(tp.__module__, tp.__name__)
            if not top_level:
                return plain
            return _union([ast.Name(id=changes_name(tp), ctx=ast.Load()), plain])
        if tp in self._aliases:
            module, name = self._aliases[tp]
            return self.use(module, name)
        origin = typing.get_origin(tp)
        arguments = typing.get_args(tp)
        if origin is typing.Literal:
            values = ast.Tuple(elts=[ast.Constant(value=value) for value in arguments], ctx=ast.Load())
            return ast.Subscript(value=self.use("typing", "Literal"), slice=values, ctx=ast.Load())
        if origin in (typing.Union, types.UnionType):
            return _union([self.annotation(argument, top_level=top_level) for argument in arguments])
        if origin is not None:
            parameters = [self.annotation(argument, top_level=False) for argument in arguments]
            subscript = parameters[0] if len(parameters) == 1 else ast.Tuple(elts=parameters, ctx=ast.Load())
            return ast.Subscript(
                value=self.use(origin.__module__, origin.__name__), slice=subscript, ctx=ast.Load()
            )
        if isinstance(tp, type):
            return self.use(tp.__module__, tp.__name__)
        raise TypeError(f"Не знаю, как записать тип {tp!r}")

    def import_nodes(self) -> list[ast.ImportFrom]:
        """
        ``from модуль import имена``: стандартная библиотека, затем пакет; внутри групп - по алфавиту.
        """
        modules = sorted(self.imports, key=lambda module: (module.startswith(FIRST_PARTY), module))
        return [
            ast.ImportFrom(
                module=module,
                names=[ast.alias(name=name) for name in sorted(self.imports[module])],
                level=0,
            )
            for module in modules
        ]


def _union(members: list[ast.expr]) -> ast.expr:
    result = members[0]
    for member in members[1:]:
        result = ast.BinOp(left=result, op=ast.BitOr(), right=member)
    return result


def changes_name(cls: type) -> str:
    return f"{cls.__name__}{SUFFIX}"


def own_docstring(cls: type) -> str | None:
    """
    Docstring, написанный автором класса: dataclass подставляет в ``__doc__`` сигнатуру, ее пропускаем.
    """
    doc = cls.__dict__.get("__doc__")
    if not doc or doc.startswith(f"{cls.__name__}("):
        return None
    return " ".join(doc.split())


def changes_class(cls: type, annotator: Annotator) -> ast.ClassDef:
    hints = typing.get_type_hints(cls)
    summary = f"Правки ``{cls.__name__}`` для ``evolve``."
    if any(is_style(hints[field.name]) for field in init_fields(cls)):
        summary += " Вложенный стиль - словарем правок или готовым объектом."
    own = own_docstring(cls)
    body: list[ast.stmt] = [ast.Expr(value=ast.Constant(value=f"{summary} {own}" if own else summary))]
    for field in init_fields(cls):
        body.append(
            ast.AnnAssign(
                target=ast.Name(id=field.name, ctx=ast.Store()),
                annotation=annotator.annotation(hints[field.name]),
                value=None,
                simple=1,
            )
        )
    return ast.ClassDef(
        name=changes_name(cls),
        bases=[annotator.use("typing", "TypedDict")],
        keywords=[ast.keyword(arg="total", value=ast.Constant(value=False))],
        body=body,
        decorator_list=[],
        type_params=[],
    )


def build_module() -> ast.Module:
    annotator = Annotator()
    classes = [changes_class(cls, annotator) for cls in style_classes(ReportStyle)]
    docstring = (
        "Сгенерировано tools/generate_style_changes.py по dataclass-ам стиля: не править вручную. "
        "TypedDict-ы описывают аргументы ReportStyle.evolve."
    )
    module = ast.Module(
        body=[
            ast.Expr(value=ast.Constant(value=docstring)),
            ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0),
            *annotator.import_nodes(),
            *classes,
        ],
        type_ignores=[],
    )
    return ast.fix_missing_locations(module)


def render() -> str:
    return ast.unparse(build_module()) + "\n"


def main() -> None:
    TARGET.write_text(render(), encoding="utf-8")
    print("written", TARGET)


if __name__ == "__main__":
    main()
