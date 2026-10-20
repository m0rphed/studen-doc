"""
Метаданные документа (блок YAML в начале файла): заголовок, автор, стиль и титульный лист.

    ---
    title: ЛР4. Регрессия
    author: О. Н. Молодец
    style: suai
    title_page:
      type: suai
      student_name: О. Н. Молодец
      group: "4318"
    bibliography: refs.bib        # файлы библиографии (список или один) и стиль CSL, пути - от папки файла
    csl: gost.csl
    ---
"""

from __future__ import annotations

import dataclasses
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, get_args, get_type_hints

from studen_doc.errors import MarkdownError
from studen_doc.frontends.markdown.inlines import InlineConverter
from studen_doc.frontends.markdown.pandoc_ast import Node
from studen_doc.model.bibliography import Bibliography
from studen_doc.model.report import TitlePage, title_page_named, title_page_names

#: Подсказка к ошибке «неизвестное имя»: стили и титульные листы вузов регистрируются при импорте их модуля.
REGISTRY_HINT = "Стили и титульные листы вузов подключаются импортом, например: import studen_doc.universities"

_INTEGER = re.compile(r"-?\d+")
_DECIMAL = re.compile(r"-?\d+(?:\.\d+)?")


@dataclass(frozen=True, slots=True)
class Metadata:
    title: str | None = None
    author: str | None = None
    style_name: str | None = None  # имя зарегистрированного стиля (``register_style``)
    title_page: TitlePage | None = None
    bibliography: Bibliography | None = None


def read_metadata(meta: Node, inlines: InlineConverter, base_dir: Path) -> Metadata:
    """
    Метаданные из ``meta`` корня AST; все ключи необязательны. Пути к файлам библиографии и стилю CSL
    отсчитываются от ``base_dir`` - папки документа.
    """
    return Metadata(
        title=_text(meta.get("title"), inlines),
        author=_text(meta.get("author"), inlines),
        style_name=_text(meta.get("style"), inlines),
        title_page=_title_page(meta.get("title_page"), inlines),
        bibliography=_bibliography(meta, inlines, base_dir),
    )


def _text(value: Node | None, inlines: InlineConverter) -> str | None:
    """
    Значение как простой текст; список (несколько авторов) склеивается через запятую.
    """
    match value:
        case {"t": "MetaInlines", "c": nodes}:
            return inlines.plain(nodes)
        case {"t": "MetaString", "c": text}:
            return text
        case {"t": "MetaList", "c": entries}:
            return ", ".join(part for entry in entries if (part := _text(entry, inlines)))
        case _:
            return None


def _bibliography(meta: Node, inlines: InlineConverter, base_dir: Path) -> Bibliography | None:
    """
    ``bibliography: refs.bib`` (или список файлов) и ``csl: стиль.csl``; без файлов библиографии - ``None``.
    """
    names = _texts(meta.get("bibliography"), inlines)
    if not names:
        return None
    csl = _text(meta.get("csl"), inlines)
    return Bibliography([base_dir / name for name in names], base_dir / csl if csl else None)


def _texts(value: Node | None, inlines: InlineConverter) -> list[str]:
    """
    Значение как список строк: один элемент или ``MetaList``.
    """
    match value:
        case {"t": "MetaList", "c": entries}:
            return [text for entry in entries if (text := _text(entry, inlines))]
        case None:
            return []
        case _:
            return [text] if (text := _text(value, inlines)) else []


def _title_page(node: Node | None, inlines: InlineConverter) -> TitlePage | None:
    """
    ``title_page: {type: suai, ...}``: класс титульного листа по ``type``, остальные ключи - его поля.
    """
    if node is None:
        return None
    if node["t"] != "MetaMap":
        raise MarkdownError("title_page в метаданных должен быть словарем: type и поля титульного листа")
    values = {name: _field_value(value, inlines) for name, value in node["c"].items()}
    kind = values.pop("type", None)
    if not isinstance(kind, str) or kind not in title_page_names():
        raise MarkdownError(f"title_page.type = {kind!r}: известны {title_page_names()}. {REGISTRY_HINT}")
    return _build(kind, title_page_named(kind), values)


def _field_value(node: Node, inlines: InlineConverter) -> str | bool:
    match node:
        case {"t": "MetaBool", "c": flag}:
            return flag
        case {"t": "MetaString" | "MetaInlines"}:
            return _text(node, inlines) or ""
        case _:
            raise MarkdownError("В полях титульного листа допустимы строки, числа и true/false")


def _build(kind: str, cls: type[TitlePage], values: dict[str, str | bool]) -> TitlePage:
    """
    Создает титульный лист из значений метаданных, приводя строки к типам полей (``int``, ``float``, ``bool``).
    """
    if not dataclasses.is_dataclass(cls):
        raise TypeError(f"Титульный лист {cls.__name__} должен быть dataclass")
    names = {field.name for field in dataclasses.fields(cls) if field.init}
    unknown = sorted(values.keys() - names)
    if unknown:
        raise MarkdownError(f"title_page {kind}: неизвестные поля {unknown}; допустимы {sorted(names)}")
    hints = get_type_hints(cls)
    converted: dict[str, Any] = {}
    for name, value in values.items():
        try:
            converted[name] = _coerce(value, hints[name])
        except ValueError:
            expected = hints[name]
            raise MarkdownError(f"title_page {kind}: поле {name} = {value!r} не подходит к типу {expected}") from None
    try:
        return cls(**converted)
    except TypeError as error:  # например, не заданы обязательные поля
        raise MarkdownError(f"title_page {kind}: {error}") from error


def _coerce(value: str | bool, hint: Any) -> Any:
    """
    Приводит значение метаданных к типу поля: ``int``, ``float``, ``bool``, ``str`` или их объединению.
    """
    accepted = get_args(hint) or (hint,)
    match value:
        case bool() if bool in accepted:
            return value
        case str() if int in accepted and _INTEGER.fullmatch(value):
            return int(value)
        case str() if float in accepted and _DECIMAL.fullmatch(value):
            return float(value)
        case "true" | "false" if bool in accepted:
            return value == "true"
        case str() if str in accepted:
            return value
    raise ValueError(value)
