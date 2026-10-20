"""
Библиография: откуда брать описания источников и как их оформлять. Только данные и контракты: сам разбор
файлов и оформление записей - в ``studen_doc.bibliography``.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from studen_doc.model.inline import Inline

#: Ключ ``nocite``, который означает «все записи библиографии».
ALL_SOURCES = "*"


@dataclass(frozen=True, slots=True, init=False)
class Bibliography:
    """
    Файлы с описаниями источников (BibTeX, BibLaTeX, CSL JSON или YAML - как принимает pandoc) и стиль оформления
    записей CSL. Без ``csl`` берется стиль по ГОСТ 7.32-2017 из пакета.

    ``Bibliography("refs.bib")``, ``Bibliography(["a.bib", "b.json"], csl="my-style.csl")``.
    """

    files: tuple[Path, ...]
    csl: Path | None

    def __init__(self, files: str | Path | Sequence[str | Path], csl: str | Path | None = None) -> None:
        paths = (files,) if isinstance(files, str | Path) else tuple(files)
        if not paths:
            raise ValueError("Bibliography без файлов: укажите хотя бы один файл с описаниями источников")
        object.__setattr__(self, "files", tuple(Path(path) for path in paths))
        object.__setattr__(self, "csl", Path(csl) if csl is not None else None)


#: Оформитель записей: ключи (и ``"*"`` - все записи) -> готовый текст записи по каждому ключу в том порядке,
#: в каком записи лежат в библиографии. Записи, которых нет в библиографии, в результате отсутствуют.
type SourceFormatter = Callable[[Sequence[str]], Mapping[str, tuple[Inline, ...]]]
