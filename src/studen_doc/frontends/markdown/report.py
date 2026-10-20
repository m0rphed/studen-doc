"""
Отчет целиком из одного или нескольких файлов Markdown.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, TypedDict, Unpack, overload

from studen_doc.errors import MarkdownError
from studen_doc.frontends.markdown.document import ParsedDocument, parse_markdown
from studen_doc.frontends.markdown.meta import REGISTRY_HINT
from studen_doc.model.bibliography import Bibliography
from studen_doc.model.blocks import Block
from studen_doc.model.report import Report, TitlePage
from studen_doc.style import ReportStyle, style_named, style_names


class ReportOptions(TypedDict, total=False):
    """
    Необязательные аргументы ``load_report`` (и ``Report.from_markdown``); смысл - в ``Report.from_markdown``.
    """

    style: ReportStyle | None
    title_page: TitlePage | None
    title: str | None
    author: str | None
    bibliography: Bibliography | None
    inserts: Mapping[str, Block | Sequence[Block]] | None
    variables: Mapping[str, Any] | None
    decimal: str
    command: Sequence[str] | None


@overload
def load_report(*sources: str | Path, **options: Unpack[ReportOptions]) -> Report: ...
@overload
def load_report[R: Report](*sources: str | Path, report_class: type[R], **options: Unpack[ReportOptions]) -> R: ...
def load_report(
    *sources: str | Path,
    report_class: type[Report] = Report,
    **options: Unpack[ReportOptions],
) -> Report:
    """
    Отчет из файлов Markdown (содержимое файлов идет подряд). Подробности - в ``Report.from_markdown``;
    ``report_class`` - какой класс отчета создать (по умолчанию ``Report``, можно свой подкласс).
    """
    if not sources:
        raise ValueError("Нужен хотя бы один файл Markdown")
    documents = [
        parse_markdown(
            source,
            inserts=options.get("inserts"),
            variables=options.get("variables"),
            decimal=options.get("decimal", ","),
            command=options.get("command"),
        )
        for source in sources
    ]
    style = options.get("style")
    return report_class(
        style if style is not None else _style_from_metadata(documents),
        title=options.get("title") or _first_set(documents, "title"),
        author=options.get("author") or _first_set(documents, "author"),
        title_page=options.get("title_page") or _first_set(documents, "title_page"),
        bibliography=options.get("bibliography") or _first_set(documents, "bibliography"),
        items=[item for document in documents for item in document.items],
    )


def _first_set(documents: Sequence[ParsedDocument], field: str) -> Any:
    """
    Значение поля из первого документа, где оно задано.
    """
    return next((value for document in documents if (value := getattr(document, field))), None)


def _style_from_metadata(documents: Sequence[ParsedDocument]) -> ReportStyle:
    name = _first_set(documents, "style_name")
    if name is None:
        raise MarkdownError("Стиль не задан: передайте style=... или напишите style: suai в метаданных")
    try:
        return style_named(name)
    except KeyError:
        raise MarkdownError(f"Неизвестный стиль {name!r}; известны {style_names()}. {REGISTRY_HINT}") from None
