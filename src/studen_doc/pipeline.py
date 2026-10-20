"""
Конвейер сборки: модель -> IR -> файл.

Склеивает слои, которые друг о друге не знают: нумерацию (``resolve``), разбор строк ``Md``
(``frontends``) и запись в Word (``render.docx``). ``Report.resolve`` и ``Report.build_to_docx`` - короткие
обертки над функциями отсюда.
"""

from __future__ import annotations

from pathlib import Path

from studen_doc.bibliography import PandocCiteproc
from studen_doc.equations import MathConverter
from studen_doc.frontends.markdown import parse_inline_markdown
from studen_doc.ir import ResolvedReport
from studen_doc.model.bibliography import SourceFormatter
from studen_doc.model.inline import InlineParser
from studen_doc.model.report import Report
from studen_doc.render.docx import DocxRenderer
from studen_doc.resolve import resolve_report


def resolve(
    report: Report,
    *,
    inline_parser: InlineParser | None = None,
    source_formatter: SourceFormatter | None = None,
) -> ResolvedReport:
    """
    Проход нумерации и ссылок: модель -> промежуточное представление (не зависит от формата).

    Строки ``Md`` разбирает ``inline_parser``; по умолчанию - pandoc, один вызов на весь документ. Записи
    библиографии оформляет ``source_formatter``; по умолчанию - pandoc citeproc по ``report.bibliography``.
    """
    if source_formatter is None and report.bibliography is not None:
        source_formatter = PandocCiteproc(report.bibliography)
    return resolve_report(
        report,
        inline_parser if inline_parser is not None else parse_inline_markdown,
        source_formatter,
    )


def build_docx(
    report: Report,
    path: str | Path,
    *,
    math: MathConverter | None = None,
    inline_parser: InlineParser | None = None,
    source_formatter: SourceFormatter | None = None,
) -> Path:
    """
    Собирает .docx. ``math`` - свой конвертер формул (по умолчанию pandoc), ``inline_parser`` - свой разбор ``Md``,
    ``source_formatter`` - свое оформление записей библиографии.
    """
    resolved = resolve(report, inline_parser=inline_parser, source_formatter=source_formatter)
    return DocxRenderer(math).render(resolved, Path(path))
