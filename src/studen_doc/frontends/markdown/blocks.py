"""
Блоки pandoc (абзацы, рисунки, листинги, списки, формулы, служебные ``:::``-блоки) -> блоки модели.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from studen_doc.errors import MarkdownError
from studen_doc.frontends.markdown.inlines import InlineConverter
from studen_doc.frontends.markdown.pandoc_ast import Attr, Node, first_text
from studen_doc.frontends.markdown.structure import Heading, Item
from studen_doc.frontends.markdown.substitutions import Substitutions
from studen_doc.frontends.markdown.tables import TableConverter
from studen_doc.model.blocks import (
    Block,
    Bullets,
    Figure,
    Formula,
    Listing,
    ListItem,
    Numbered,
    NumberedMarker,
    P,
    PageBreak,
    Source,
    Sources,
)
from studen_doc.model.inline import ModelInline, Text
from studen_doc.model.report import Toc

#: Классы блока кода, которые включают номера строк (первый - стандартный для pandoc).
_NUMBER_LINES = frozenset({"numberLines", "number-lines", "line-numbers"})

#: Служебные ``:::``-блоки, которые понимает фронтенд (для сообщения об ошибке).
_KNOWN_DIVS = "table, toc, pagebreak, insert, where, sources"

_WHITESPACE = ("Space", "SoftBreak")


class BlockConverter:
    """
    Превращает блоки pandoc в блоки модели. Относительные пути (картинки, ``file=``) отсчитываются от ``base_dir``.
    """

    def __init__(self, base_dir: Path, inlines: InlineConverter, substitutions: Substitutions) -> None:
        self._base_dir = base_dir
        self._inlines = inlines
        self._substitutions = substitutions
        self._tables = TableConverter(inlines)

    def convert(self, blocks: Sequence[Node]) -> list[Item]:
        """
        Поток элементов документа: блоки, заголовки (``Heading``) и оглавления (``Toc``).
        """
        items: list[Item] = []
        for block in blocks:
            match block:
                case {"t": "Header", "c": [level, attr, children]}:
                    parsed = Attr.parse(attr)
                    items.append(Heading(level, self._inlines.plain(children), parsed.classes, parsed.options))
                case {"t": "Para" | "Plain", "c": children}:
                    items.append(self._paragraph(children))
                case {"t": "Figure", "c": [attr, caption, content]}:
                    items.append(self._figure(Attr.parse(attr), caption[1], content))
                case {"t": "CodeBlock", "c": [attr, text]}:
                    items.append(self._listing(Attr.parse(attr), text))
                case {"t": "BulletList", "c": entries}:
                    items.append(Bullets(self._list_items(entries)))
                case {"t": "OrderedList", "c": [numbering, entries]}:
                    items.append(Numbered(self._list_items(entries), marker=_marker(numbering)))
                case {"t": "Table", "c": parts}:
                    items.append(self._tables.bare(parts))
                case {"t": "Div", "c": [attr, content]}:
                    self._div(Attr.parse(attr), content, items)
                case {"t": kind}:
                    raise MarkdownError(f"Блок {kind} пока не поддерживается")
        return items

    # --------------------------------------------------------------------------------- служебные блоки
    def _div(self, attr: Attr, content: Sequence[Node], items: list[Item]) -> None:
        match attr.classes:
            case ():
                items.extend(self.convert(content))  # div только с id: прозрачная обертка
            case ("table",):
                items.append(self._tables.captioned(attr, content))
            case ("toc",):
                items.append(Toc(attr.options.text("title"), levels=attr.options.integer("levels", 3)))
            case ("pagebreak",):
                items.append(PageBreak())
            case ("insert",):
                items.extend(self._substitutions.insert(self._insert_name(attr)))
            case ("where",):
                self._attach_legend(items, content)
            case ("sources",):
                items.append(self._sources(attr, content))
            case classes:
                raise MarkdownError(f"Неизвестный блок ::: {' '.join(classes)} (известны: {_KNOWN_DIVS})")

    def _sources(self, attr: Attr, content: Sequence[Node]) -> Sources:
        """
        ``::: sources``: список использованных источников. Пустой блок берет записи из библиографии
        (``bibliography:`` в метаданных); нумерованный список внутри - записи вручную, а ``[]{#ключ}`` в начале
        пункта дает ключ для ссылок ``[@ключ]``. ``nocite="a,b"`` (``nocite=*`` - все записи) добавляет в список
        источники, на которые нет ссылок.
        """
        entries: list[Source | tuple[ModelInline, ...]] = []
        for block in content:
            match block:
                case {"t": "OrderedList", "c": [_, list_entries]}:
                    entries.extend(self._source_entry(entry) for entry in list_entries)
                case _:
                    raise MarkdownError("Блок sources состоит из нумерованного списка источников (или пуст)")
        nocite = [key.strip() for key in (attr.options.text("nocite") or "").split(",") if key.strip()]
        return Sources(entries, nocite=nocite)

    def _source_entry(self, blocks: Sequence[Node]) -> Source | tuple[ModelInline, ...]:
        """
        Пункт списка источников; пустой span с идентификатором в начале (``[]{#ivanov2020}``) - ключ записи.
        """
        nodes = list(first_text(blocks))
        match nodes:
            case [{"t": "Span", "c": [[ident, _, _], []]}, *rest] if ident:
                while rest and rest[0]["t"] in _WHITESPACE:
                    rest.pop(0)
                return Source(ident, self._inlines.convert(rest))
            case _:
                return self._inlines.convert(nodes)

    @staticmethod
    def _insert_name(attr: Attr) -> str:
        name = attr.options.text("name")
        if name is None:
            raise MarkdownError("У ::: insert нет имени блока: ::: {.insert name=...}")
        return name

    def _attach_legend(self, items: list[Item], content: Sequence[Node]) -> None:
        """
        ``::: where``: пояснения к формуле, после которой он стоит.
        """
        if not items or not isinstance(items[-1], Formula):
            raise MarkdownError("Блок where должен стоять сразу после формулы")
        items[-1] = replace(items[-1], where=self._legend(content))

    def _legend(self, content: Sequence[Node]) -> tuple[tuple[str, tuple[ModelInline, ...]], ...]:
        """
        Список определений "символ: описание"; символом может быть формула ``$y$`` либо обычный текст.
        """
        pairs: list[tuple[str, tuple[ModelInline, ...]]] = []
        for block in content:
            match block:
                case {"t": "DefinitionList", "c": definitions}:
                    for term, descriptions in definitions:
                        symbol = self._inlines.plain(term).strip()
                        pairs.append((symbol, self._inlines.convert(first_text(descriptions[0]))))
                case _:
                    raise MarkdownError("Блок where состоит из определений: символ, затем строка с двоеточием")
        return tuple(pairs)

    # ------------------------------------------------------------------------- абзацы, формулы, рисунки
    def _paragraph(self, children: Sequence[Node]) -> Block:
        """
        Абзац; но абзац из одной выключной формулы - это ``Formula`` (с меткой, если за ней стоит ``{#id}``),
        а из одной картинки - рисунок без подписи.
        """
        significant = [node for node in children if not _is_blank([node])]
        match significant:
            case [{"t": "Math", "c": [{"t": "DisplayMath"}, latex]}]:
                return Formula(latex.strip())
            case [
                {"t": "Math", "c": [{"t": "DisplayMath"}, latex]},
                {"t": "Span", "c": [attr, inner]},
            ] if _is_blank(inner):
                if label := Attr.parse(attr).label:  # формула, за которой следует ``{#eq:id}``
                    return Formula(latex.strip(), label=label)
            case [{"t": "Image", "c": [attr, _alt, [url, _title]]}]:
                return self._image_figure(Attr.parse(attr), url, caption=(), label=None)
        return P(self._inlines.convert(children))

    def _figure(self, attr: Attr, caption: Sequence[Node], content: Sequence[Node]) -> Figure:
        images = [node for block in content for node in block.get("c", []) if node["t"] == "Image"]
        if len(images) != 1:
            raise MarkdownError("В подписанном рисунке должна быть ровно одна картинка")
        image_attr, _alt, (url, _title) = images[0]["c"]
        caption_inlines = self._inlines.convert(first_text(caption))
        return self._image_figure(Attr.parse(image_attr), url, caption=caption_inlines, label=attr.label)

    def _image_figure(self, image: Attr, url: str, *, caption: tuple[ModelInline, ...], label: str | None) -> Figure:
        width_cm = image.options.length_cm("width")
        return Figure(str(self._path(url)), caption, label=label, width_cm=width_cm)

    # --------------------------------------------------------------------------------------- листинги
    def _listing(self, attr: Attr, text: str) -> Listing:
        options = attr.options
        if (file := options.text("file")) is None:
            code = text
        elif text.strip():
            raise MarkdownError(f"У листинга с file={file} тело блока должно быть пустым")
        else:
            code = self._path(file).read_text(encoding="utf-8")
        caption = options.text("caption")
        return Listing(
            code,
            Text(caption) if caption else None,
            label=attr.label,
            language=next((name for name in attr.classes if name not in _NUMBER_LINES), None),
            line_numbers=True if _NUMBER_LINES.intersection(attr.classes) else None,
            highlight=options.flag("highlight"),
        )

    def _path(self, value: str) -> Path:
        path = Path(unquote(value))
        return path if path.is_absolute() else self._base_dir / path

    # ----------------------------------------------------------------------------------------- списки
    def _list_items(self, entries: Sequence[Sequence[Node]]) -> tuple[ListItem, ...]:
        """
        Пункт: первый абзац - текст, вложенные списки - подпункты (их маркеры не учитываются).
        """
        return tuple(self._list_item(entry) for entry in entries)

    def _list_item(self, entry: Sequence[Node]) -> ListItem:
        text: tuple[ModelInline, ...] | None = None
        children: list[ListItem] = []
        for block in entry:
            match block:
                case {"t": "Para" | "Plain", "c": inlines} if text is None:
                    text = self._inlines.convert(inlines)
                case {"t": "BulletList", "c": nested} | {"t": "OrderedList", "c": [_, nested]}:
                    children.extend(self._list_items(nested))
                case _:
                    raise MarkdownError("В пункте списка допустимы один абзац и вложенные списки")
        return ListItem(text or (), tuple(children))


def _is_blank(nodes: Sequence[Node]) -> bool:
    """
    Инлайны состоят только из пробелов и переносов строк.
    """
    return all(node["t"] in _WHITESPACE for node in nodes)


def _marker(numbering: Sequence[Any]) -> NumberedMarker:
    """
    Маркер нумерованного списка по виду нумерации pandoc: цифры или буквы, скобка или точка.
    """
    start, style, delimiter = numbering
    if start != 1:
        raise MarkdownError(f"Нумерованный список должен начинаться с 1 (начинается с {start})")
    period = delimiter["t"] in ("Period", "DefaultDelim")
    match style["t"]:
        case "DefaultStyle" | "Decimal":
            return "1." if period else "1)"
        case "LowerAlpha":  # a), b) в тексте печатаются русскими а), б) по ГОСТ 7.32
            return "a." if period else "a)"
        case other:
            raise MarkdownError(f"Вид нумерации списка {other} не поддерживается: есть цифры и строчные буквы")
