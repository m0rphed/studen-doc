"""
Точки входа фронтенда: файл или текст Markdown -> разделы модели, а также разбор отдельных строк ``Md``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from studen_doc.errors import MarkdownError
from studen_doc.frontends.markdown.blocks import BlockConverter
from studen_doc.frontends.markdown.inlines import InlineConverter
from studen_doc.frontends.markdown.meta import read_metadata
from studen_doc.frontends.markdown.pandoc_ast import TEXT_BLOCKS, read_ast
from studen_doc.frontends.markdown.structure import build_sections
from studen_doc.frontends.markdown.substitutions import Substitutions
from studen_doc.model.bibliography import Bibliography
from studen_doc.model.blocks import Block
from studen_doc.model.inline import ModelInline
from studen_doc.model.report import Section, TitlePage, Toc
from studen_doc.numfmt import MINUS


@dataclass(frozen=True, slots=True)
class ParsedDocument:
    items: tuple[Section | Toc, ...]
    title: str | None = None
    author: str | None = None
    title_page: TitlePage | None = None
    style_name: str | None = None  # имя зарегистрированного стиля (``register_style``)
    bibliography: Bibliography | None = None


def parse_markdown(
    path: str | Path,
    *,
    inserts: Mapping[str, Block | Sequence[Block]] | None = None,
    variables: Mapping[str, Any] | None = None,
    decimal: str = ",",
    minus: str = MINUS,
    command: Sequence[str] | None = None,
    timeout_s: float = 120.0,
) -> ParsedDocument:
    """
    Читает файл .md; пути к картинкам и ``file=`` у листингов отсчитываются от папки файла.

    ``inserts`` - блоки, подставляемые вместо ``::: {.insert name=...}``; ``variables`` - значения для
    ``[]{var=имя format=".3f"}``; ``decimal`` - десятичный разделитель, ``minus`` - знак минус в подставленных числах.
    """
    path = Path(path)
    return parse_markdown_text(
        path.read_text(encoding="utf-8"),
        base_dir=path.parent,
        inserts=inserts,
        variables=variables,
        decimal=decimal,
        minus=minus,
        command=command,
        timeout_s=timeout_s,
    )


def parse_markdown_text(
    text: str,
    *,
    base_dir: str | Path | None = None,
    inserts: Mapping[str, Block | Sequence[Block]] | None = None,
    variables: Mapping[str, Any] | None = None,
    decimal: str = ",",
    minus: str = MINUS,
    command: Sequence[str] | None = None,
    timeout_s: float = 120.0,
) -> ParsedDocument:
    """
    Разбирает текст Markdown. ``base_dir`` - от чего отсчитывать относительные пути (по умолчанию текущая папка);
    ``inserts``, ``variables``, ``decimal`` и ``minus`` - как у ``parse_markdown``.
    """
    ast = read_ast(text, command=command, timeout_s=timeout_s)
    substitutions = Substitutions(inserts or {}, variables or {}, decimal, minus)
    inlines = InlineConverter(substitutions)
    resolved_base = Path(base_dir) if base_dir is not None else Path.cwd()
    converter = BlockConverter(resolved_base, inlines, substitutions)
    metadata = read_metadata(ast.get("meta", {}), inlines, resolved_base)
    return ParsedDocument(
        build_sections(converter.convert(ast["blocks"])),
        title=metadata.title,
        author=metadata.author,
        title_page=metadata.title_page,
        style_name=metadata.style_name,
        bibliography=metadata.bibliography,
    )


def parse_inline_markdown(
    sources: Sequence[str],
    *,
    command: Sequence[str] | None = None,
    timeout_s: float = 120.0,
) -> dict[str, tuple[ModelInline, ...]]:
    """
    Строки с инлайн-разметкой (``Md``) -> узлы; все строки - одним вызовом pandoc (одинаковые разбираются раз).
    Каждая строка должна быть одним абзацем обычного текста.
    """
    unique = list(dict.fromkeys(sources))
    for source in unique:
        if not source.strip() or "\n\n" in source.strip():
            raise MarkdownError(f"Md принимает один непустой абзац, получено: {source[:60]!r}")
    ast = read_ast("\n\n".join(source.strip() for source in unique), command=command, timeout_s=timeout_s)
    paragraphs = ast["blocks"]
    if len(paragraphs) != len(unique) or any(block["t"] not in TEXT_BLOCKS for block in paragraphs):
        raise MarkdownError("Md принимает обычный текст абзаца: без заголовков, списков, цитат и таблиц")
    inlines = InlineConverter()
    return {source: inlines.convert(block["c"]) for source, block in zip(unique, paragraphs, strict=True)}
