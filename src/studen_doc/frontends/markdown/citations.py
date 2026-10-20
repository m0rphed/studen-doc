"""
Ссылки на источники в тексте Markdown: ``[@ключ]``, ``[@a; @b]``, ``[@a, с. 5]``.

Диалект ``commonmark_x`` не знает ссылок pandoc, поэтому они остаются в тексте обычными строками
(``Str "[@a;"``, ``Space``, ``Str "@b]"``). Здесь они находятся в склеенном тексте и превращаются в ``Citation``.
Синтаксис - подмножество pandoc: ключи через ``;``, у каждого необязательное место в источнике после запятой;
текст перед ``@`` (``[см. @a]``) не поддерживается.

Скобки, в которых есть ``@ключ``, но которые не разобрались (опечатка, лишний текст, незакрытая скобка), -
ошибка ``MarkdownError`` с самим фрагментом: тихо оставить такую запись обычным текстом значило бы выпустить
отчет с ``[@ключ]`` вместо номера. Чтобы показать ``[@ключ]`` буквально, пишите его кодом: `` `[@ключ]` ``.
"""

from __future__ import annotations

import re
from collections.abc import Iterator

from studen_doc.errors import MarkdownError
from studen_doc.model.inline import Citation

#: Ключ как у pandoc: буква, цифра или ``_`` (в том числе кириллические), внутри допустимы еще ``:.#$%&+?<>~/-``.
_KEY = r"\w(?:[\w:.#$%&+?<>~/-]*\w)?"

#: Что похоже на ссылку: ``@`` не после буквы или цифры (так отличается ``me@example.com``) и сразу за ним ключ.
_CITATION_MARK = r"(?<!\w)@\w"

_BRACKETS = re.compile(r"\[([^\[\]]*)\]")
_ITEM = re.compile(rf"@(?P<key>{_KEY})(?:\s*,\s*(?P<locator>\S.*))?")
_LOOKS_LIKE_CITATION = re.compile(_CITATION_MARK)
_OPEN_BRACKET = re.compile(rf"\[[^\[\]]*{_CITATION_MARK}")

#: Сколько символов фрагмента показывать в сообщении об ошибке.
_CONTEXT = 60


def split_citations(text: str) -> Iterator[str | tuple[Citation, ...]]:
    """
    Текст по частям: обычные строки и ссылки на источники (кортеж ``Citation``) в порядке следования.

    Скобки с ``@ключ``, которые не удалось разобрать, и незакрытая скобка со ссылкой - ``MarkdownError``.
    """
    end = 0
    for match in _BRACKETS.finditer(text):
        if not _LOOKS_LIKE_CITATION.search(match[1]):
            continue
        citations = _parse(match[1])
        if citations is None:
            raise MarkdownError(f"Не удалось разобрать ссылку на источник {match[0]!r}: {_EXPECTED}")
        if match.start() > end:
            yield _plain(text[end : match.start()])
        yield citations
        end = match.end()
    if end < len(text):
        yield _plain(text[end:])


def _plain(text: str) -> str:
    """
    Обычный текст между ссылками; в нем не должно остаться начатой, но не закрытой ссылки.
    """
    if unclosed := _OPEN_BRACKET.search(text):
        raise MarkdownError(f"Не закрыта скобка в ссылке на источник: {text[unclosed.start() :][:_CONTEXT]!r}")
    return text


_EXPECTED = (
    "ожидалось [@ключ], [@ключ1; @ключ2] или [@ключ, с. 5] (текст перед @ не поддерживается); "
    "чтобы показать запись как есть, оформите ее кодом"
)


def _parse(content: str) -> tuple[Citation, ...] | None:
    """
    Содержимое скобок как ссылки; ``None``, если оно не подходит под синтаксис ссылок.
    """
    citations: list[Citation] = []
    for part in content.split(";"):
        item = _ITEM.fullmatch(part.strip())
        if item is None:
            return None
        citations.append(Citation(item["key"], item["locator"]))
    return tuple(citations)
